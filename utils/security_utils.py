"""
utils/security_utils.py — ExamHelp AI Security Utilities v1.0
=================================================================
FIX-11.1: API key masking in logs and UI
FIX-11.2: Input sanitization (XSS, prompt injection, length limits)
FIX-11.3: Centralized error logger with structured output
FIX-11.4: Rate-limit decorator for UI functions
"""
from __future__ import annotations

import hashlib
import html
import logging
import re
import sys
import time
import threading
from typing import Any, Callable, Optional

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("examhelp")


# ── FIX-11.1: API Key Masking ─────────────────────────────────────────────────
def mask_api_key(key: str) -> str:
    """
    FIX-11.1: Mask an API key for safe display in logs/UI.
    Shows first 4 + last 4 characters, middle replaced with *****.
    """
    if not key or len(key) < 10:
        return "***masked***"
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


def log_api_call(model: str, key: str, tokens_in: int = 0, tokens_out: int = 0) -> None:
    """FIX-11.1: Log API call with masked key. Never exposes full key."""
    masked = mask_api_key(key)
    logger.info(f"API call | model={model} | key={masked} | in={tokens_in} | out={tokens_out}")


# ── FIX-11.2: Input Sanitization ──────────────────────────────────────────────
# Prompt injection patterns to detect and neutralize
_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions?",
    r"disregard\s+(?:all\s+)?(?:above|previous)",
    r"you\s+are\s+now\s+(?:a|an)\s+\w+",
    r"act\s+as\s+(?:if\s+you\s+(?:are|were)\s+)?(?:a|an)\s+\w+",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[\/INST\]",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

INPUT_MAX_LENGTH = 50_000  # Maximum user input characters


def sanitize_input(text: str, max_length: int = INPUT_MAX_LENGTH) -> str:
    """
    FIX-11.2: Sanitize user input for AI prompts:
    1. Length limit (prevents token flooding)
    2. HTML entity encoding (XSS prevention)
    3. Prompt injection pattern detection & neutralization
    """
    if not isinstance(text, str):
        text = str(text)

    # 1. Length limit
    if len(text) > max_length:
        text = text[:max_length] + f"\n\n[...input truncated at {max_length} chars]"

    # 2. Strip dangerous HTML tags (keep content)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    # 3. Detect prompt injection attempts
    if _INJECTION_RE.search(text):
        logger.warning(f"Potential prompt injection attempt detected (length={len(text)})")
        # Neutralize by escaping the suspicious patterns
        text = _INJECTION_RE.sub(lambda m: f"[BLOCKED: {m.group()[:20]}...]", text)

    return text.strip()


def sanitize_for_html(text: str) -> str:
    """
    FIX-11.2: Escape text for safe HTML display.
    Use when injecting user content into Streamlit unsafe_allow_html.
    """
    return html.escape(str(text))


def validate_url(url: str) -> tuple[bool, str]:
    """
    FIX-11.2: Validate a URL — ensures it is HTTP(S) and not a local/private addr.
    Returns (is_valid, error_message).
    """
    url = url.strip()
    if not url:
        return False, "URL cannot be empty."
    if not re.match(r'^https?://', url, re.IGNORECASE):
        return False, "Only HTTP(S) URLs are allowed."
    # Block local/private addresses (SSRF prevention)
    private_patterns = [
        r'localhost', r'127\.', r'0\.0\.0\.0', r'192\.168\.', r'10\.', r'172\.(1[6-9]|2\d|3[01])\.',
        r'::1', r'file://', r'ftp://',
    ]
    for pattern in private_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False, f"Private/local URLs are not allowed: {pattern}"
    return True, ""


# ── FIX-11.3: Centralized Error Logger ────────────────────────────────────────
_error_log: list[dict] = []
_error_log_lock = threading.Lock()
_ERROR_LOG_MAX = 200


def log_error(
    error: Exception,
    context: str = "",
    severity: str = "ERROR",
    extra: Optional[dict] = None,
) -> None:
    """
    FIX-11.3: Log structured error to in-memory log + stderr.
    Severity: ERROR | WARNING | CRITICAL | INFO
    """
    import traceback
    entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "severity": severity,
        "context": context,
        "error_type": type(error).__name__,
        "message": str(error)[:500],
        "traceback": traceback.format_exc()[-1000:],
        "extra": extra or {},
    }
    with _error_log_lock:
        _error_log.append(entry)
        if len(_error_log) > _ERROR_LOG_MAX:
            _error_log.pop(0)

    log_fn = {"CRITICAL": logger.critical, "ERROR": logger.error, "WARNING": logger.warning}.get(
        severity, logger.info
    )
    log_fn(f"[{context}] {type(error).__name__}: {str(error)[:200]}")


def get_error_log(last_n: int = 20) -> list[dict]:
    """FIX-11.3: Return the last N error log entries (newest first)."""
    with _error_log_lock:
        return list(reversed(_error_log[-last_n:]))


def clear_error_log() -> None:
    """FIX-11.3: Clear the in-memory error log."""
    with _error_log_lock:
        _error_log.clear()


# ── FIX-11.4: Rate Limit Decorator ────────────────────────────────────────────
def rate_limit(calls_per_minute: int = 10):
    """
    FIX-11.4: Decorator that rate-limits a function to N calls/minute per caller.
    Raises RuntimeError with friendly message if limit exceeded.
    """
    _window = 60.0
    _timestamps: list[float] = []
    _lock = threading.Lock()

    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            now = time.monotonic()
            with _lock:
                # Remove calls older than 1 minute
                while _timestamps and now - _timestamps[0] > _window:
                    _timestamps.pop(0)
                if len(_timestamps) >= calls_per_minute:
                    wait_sec = _window - (now - _timestamps[0])
                    raise RuntimeError(
                        f"⏳ Rate limit: max {calls_per_minute} requests/min. "
                        f"Please wait ~{int(wait_sec)}s."
                    )
                _timestamps.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ── Content Hashing (Cache keys) ─────────────────────────────────────────────
def content_fingerprint(text: str) -> str:
    """Generate a stable MD5 fingerprint for cache key purposes."""
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()
