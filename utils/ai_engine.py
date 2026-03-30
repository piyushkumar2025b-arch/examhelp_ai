"""
ai_engine.py — Gemini-only AI Engine
======================================
9-key rotation, auto-retry, streaming support.
Reads keys from Streamlit Cloud secrets — no hardcoding.

Public API (unchanged from before):
    generate(prompt, system, ...)        -> str
    generate_stream(prompt, system, ...) -> Iterator[str]
    quick_generate(prompt, system)       -> str
    vision_generate(prompt, image_b64)   -> str
    json_generate(prompt, system)        -> str
    get_pool_status()                    -> dict
    reset_all_keys()                     -> None
    get_capacity_summary()               -> str
"""

from __future__ import annotations
import json, time, threading, ssl, urllib.request, urllib.error, sys
from typing import Iterator, Optional, Dict, List

# ── Models ─────────────────────────────────────────────────
GEMINI_MODELS = [
    "gemini-2.0-flash",        # primary — 15 RPM, 1500 RPD free
    "gemini-2.5-flash",        # fallback — newer, separate quota pool
    "gemini-2.0-flash-lite",   # last-resort — lightweight, separate quota
]
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

GEMINI_RPM     = 15
GEMINI_RPD     = 1_500
GEMINI_TPM     = 1_000_000
GEMINI_SWITCH_RPM = 3   # rotate key when < 3 RPM remain

# ── SSL Context (fixes Windows certificate errors) ─────────
def _make_ssl_context() -> ssl.SSLContext:
    """Create SSL context with fallback for systems with broken cert chains."""
    # Try verified first
    try:
        ctx = ssl.create_default_context()
        # Quick test to see if it actually works
        import urllib.request
        test_req = urllib.request.Request("https://generativelanguage.googleapis.com")
        urllib.request.urlopen(test_req, timeout=5, context=ctx)
        return ctx
    except Exception:
        pass
    # Fallback: unverified context (works on systems with broken cert chains)
    try:
        ctx = ssl._create_unverified_context()
        print("[ai_engine] WARNING: Using unverified SSL (cert chain issue). "
              "Run 'pip install certifi' to fix.", file=sys.stderr)
        return ctx
    except Exception:
        return None

_SSL_CTX = _make_ssl_context()

# ── Key Pool ───────────────────────────────────────────────
class _KeyState:
    def __init__(self, key: str):
        self.key          = key
        self.rpm_times: list = []   # timestamps of recent calls
        self.cooldown_until = 0.0
        self.total_calls  = 0
        self.errors       = 0

    def rpm_used(self, now: float) -> int:
        cutoff = now - 60
        self.rpm_times = [t for t in self.rpm_times if t > cutoff]
        return len(self.rpm_times)

    def record_call(self, now: float):
        self.rpm_times.append(now)
        self.total_calls += 1

    def available(self, now: float) -> bool:
        return now >= self.cooldown_until and self.rpm_used(now) < GEMINI_RPM

    def cooldown(self, seconds: float = 65):
        self.cooldown_until = time.monotonic() + seconds


class _KeyPool:
    def __init__(self):
        self._lock  = threading.Lock()
        self._keys: List[_KeyState] = []
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            from utils.secret_manager import GEMINI_KEYS
            self._keys = [_KeyState(k) for k in GEMINI_KEYS]
            self._loaded = True
            print(f"[ai_engine] Key pool loaded: {len(self._keys)} keys", file=sys.stderr)

    def force_reload(self):
        """Force reload keys from secret_manager."""
        with self._lock:
            self._loaded = False
            self._keys = []
        from utils.secret_manager import force_reload_keys
        count = force_reload_keys()
        with self._lock:
            from utils.secret_manager import GEMINI_KEYS
            self._keys = [_KeyState(k) for k in GEMINI_KEYS]
            self._loaded = True
        print(f"[ai_engine] Key pool force-reloaded: {len(self._keys)} keys", file=sys.stderr)
        return count

    def get_best(self, exclude: set = None) -> Optional[_KeyState]:
        self._ensure_loaded()
        exclude = exclude or set()
        now = time.monotonic()
        with self._lock:
            candidates = [
                ks for ks in self._keys
                if ks.key not in exclude and ks.available(now)
            ]
            if not candidates:
                return None
            # Prefer key with most RPM headroom
            return min(candidates, key=lambda ks: ks.rpm_used(now))

    def status(self) -> dict:
        self._ensure_loaded()
        now = time.monotonic()
        with self._lock:
            avail = sum(1 for ks in self._keys if ks.available(now))
            return {
                "total":     len(self._keys),
                "available": avail,
                "cooling":   len(self._keys) - avail,
                "gemini_rpm": avail * GEMINI_RPM,
                "gemini_rpd": avail * GEMINI_RPD,
            }

    def reset(self):
        self._ensure_loaded()
        with self._lock:
            for ks in self._keys:
                ks.cooldown_until = 0
                ks.rpm_times.clear()
                ks.errors = 0


_pool = _KeyPool()


# ── HTTP helpers ───────────────────────────────────────────
def _gemini_request(
    key: str,
    prompt: str,
    system: str,
    model: str,
    image_b64: str = "",
    image_mime: str = "image/jpeg",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    url = f"{GEMINI_API_BASE}/{model}:generateContent?key={key}"

    # Build content parts
    parts: list = []
    if image_b64:
        parts.append({"inline_data": {"mime_type": image_mime, "data": image_b64}})
    parts.append({"text": prompt})

    body: dict = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}

    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # Use SSL context to avoid certificate errors on Windows
    try:
        if _SSL_CTX:
            with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
                result = json.loads(resp.read())
        else:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
    except urllib.error.HTTPError as he:
        # Read error body for better diagnostics
        err_body = ""
        try:
            err_body = he.read().decode()[:500]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {he.code}: {err_body or he.reason}") from he
    except urllib.error.URLError as ue:
        raise RuntimeError(f"Connection error: {ue.reason}") from ue

    candidates = result.get("candidates", [])
    if not candidates:
        # Check for blocked content or other issues
        block_reason = result.get("promptFeedback", {}).get("blockReason", "")
        if block_reason:
            raise ValueError(f"Content blocked: {block_reason}")
        raise ValueError("Empty candidates in Gemini response")
    parts_out = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts_out)


def _classify_error(err: Exception) -> str:
    s = str(err).lower()
    if "429" in s or "quota" in s or "rate" in s or "resource_exhausted" in s:
        return "rate_limit"
    if "403" in s or "permission" in s:
        return "forbidden"
    if "400" in s and ("invalid" in s or "api key" in s):
        return "bad_key"
    if "timeout" in s or "timed out" in s:
        return "timeout"
    if "ssl" in s or "certificate" in s:
        return "ssl_error"
    if "connection" in s or "urlopen" in s:
        return "connection"
    return "unknown"


# ── Core call with rotation ────────────────────────────────
def _call_gemini(
    prompt: str,
    system: str = "",
    image_b64: str = "",
    image_mime: str = "image/jpeg",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    # Auto-reload keys if pool is empty
    if _pool._loaded and len(_pool._keys) == 0:
        _pool.force_reload()

    if not _pool._loaded:
        _pool._ensure_loaded()

    if len(_pool._keys) == 0:
        raise RuntimeError(
            "No Gemini API keys configured. "
            "Add GEMINI_API_KEY_1…9 in .streamlit/secrets.toml "
            "or Streamlit Cloud → App settings → Secrets."
        )

    last_err: Exception = RuntimeError("No Gemini keys available.")

    for model in GEMINI_MODELS:
        # IMPORTANT: Reset tried set PER MODEL so fallback models
        # actually get a chance to try all keys
        tried: set = set()
        pool_attempts = max(len(_pool._keys), 1)

        for _ in range(pool_attempts):
            ks = _pool.get_best(exclude=tried)
            if ks is None:
                break   # all keys exhausted for this model

            now = time.monotonic()
            ks.record_call(now)
            try:
                result = _gemini_request(
                    key=ks.key,
                    prompt=prompt,
                    system=system,
                    model=model,
                    image_b64=image_b64,
                    image_mime=image_mime,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return result
            except Exception as e:
                etype = _classify_error(e)
                ks.errors += 1
                print(f"[ai_engine] Key …{ks.key[-6:]} model={model} error={etype}: {e}", file=sys.stderr)

                if etype == "rate_limit":
                    ks.cooldown(65)
                elif etype == "bad_key":
                    ks.cooldown(600)    # 10 min, not 1 hour
                elif etype == "forbidden":
                    ks.cooldown(300)    # 5 min — could be transient
                elif etype == "ssl_error":
                    # SSL errors affect all keys, no point trying more
                    raise RuntimeError(
                        f"SSL/TLS error connecting to Gemini API: {e}. "
                        "Try: pip install certifi"
                    ) from e
                elif etype == "timeout":
                    ks.cooldown(30)     # short cooldown for timeouts
                # For unknown errors, just try next key (no cooldown)

                tried.add(ks.key)
                last_err = e

    raise last_err


# ── Streaming (sentence-chunked simulation) ───────────────
def _call_gemini_stream(
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Iterator[str]:
    """Yields text in chunks (Gemini REST doesn't stream; we chunk the response)."""
    full = _call_gemini(
        prompt=prompt, system=system,
        temperature=temperature, max_tokens=max_tokens,
    )
    # Yield word-by-word for a streaming feel
    words = full.split(" ")
    chunk = []
    for i, word in enumerate(words):
        chunk.append(word)
        if len(chunk) >= 6 or i == len(words) - 1:
            yield " ".join(chunk) + (" " if i < len(words) - 1 else "")
            chunk = []


# ── Public API ────────────────────────────────────────────
def _messages_to_prompt(
    messages: list,
    context_text: str = "",
    persona_prompt: str = "",
) -> tuple:
    """Convert a messages list into (prompt, system) for Gemini."""
    system_parts = []
    if context_text:
        system_parts.append(f"Context:\n{context_text}")
    if persona_prompt:
        system_parts.append(persona_prompt)
    system = "\n\n".join(system_parts)

    turns = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        turns.append(f"{role.capitalize()}: {content}")
    prompt = "\n".join(turns)
    return prompt, system


def generate(
    prompt: str = "",
    system: str = "",
    provider: str = "gemini",   # kept for API compat — always gemini now
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
    messages: list = None,
    model: str = "",            # ignored — always uses GEMINI_MODELS rotation
    context_text: str = "",
    **kwargs,
) -> str:
    """Generate a response. Returns full text string."""
    if messages:
        prompt, system = _messages_to_prompt(messages, context_text)
    return _call_gemini(
        prompt=prompt,
        system=system,
        image_b64=image_data,
        image_mime=image_mime,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def generate_stream(
    prompt: str = "",
    system: str = "",
    provider: str = "gemini",   # kept for API compat
    temperature: float = 0.7,
    max_tokens: int = 4096,
    messages: list = None,
    model: str = "",            # ignored — always uses GEMINI_MODELS rotation
    context_text: str = "",
    persona_prompt: str = "",
    use_vit_context: bool = False,
    **kwargs,
) -> Iterator[str]:
    """Generate a streaming response. Yields text chunks."""
    if messages:
        prompt, system = _messages_to_prompt(messages, context_text, persona_prompt)
    return _call_gemini_stream(
        prompt=prompt,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def quick_generate(prompt: str, system: str = "") -> str:
    """Fast single-turn generation."""
    return _call_gemini(prompt=prompt, system=system, max_tokens=2048)


def vision_generate(prompt: str, image_b64: str, mime: str = "image/jpeg") -> str:
    """Generate with an image input."""
    return _call_gemini(prompt=prompt, image_b64=image_b64, image_mime=mime)


def json_generate(prompt: str, system: str = "") -> str:
    """Generate and return raw text (parse JSON yourself)."""
    sys = (system + "\n\n" if system else "") + \
          "Respond ONLY with valid JSON. No markdown, no backticks, no explanation."
    return _call_gemini(prompt=prompt, system=sys, temperature=0.2)


def get_pool_status() -> Dict:
    return _pool.status()


def reset_all_keys() -> None:
    _pool.reset()


def force_reload_all() -> int:
    """Force reload keys and reset all cooldowns. Returns key count."""
    count = _pool.force_reload()
    return count


def get_capacity_summary() -> str:
    s = _pool.status()
    return (
        f"Gemini: {s['available']}/{s['total']} keys active | "
        f"~{s['gemini_rpm']} RPM | ~{s['gemini_rpd']} RPD"
    )

# ── Backwards-compat stubs (previously groq functions) ────
def stream_chat_with_groq(*args, **kwargs) -> Iterator[str]:
    """Groq removed — delegates to Gemini stream."""
    prompt = kwargs.get("prompt") or (args[0] if args else "")
    system = kwargs.get("system", "")
    return generate_stream(prompt=prompt, system=system)

def chat_with_groq(*args, **kwargs) -> str:
    """Groq removed — delegates to Gemini."""
    prompt = kwargs.get("prompt") or (args[0] if args else "")
    system = kwargs.get("system", "")
    return generate(prompt=prompt, system=system)

def transcribe_audio(*args, **kwargs) -> str:
    """Audio transcription requires Groq Whisper which has been removed."""
    return "[Audio transcription unavailable — Groq integration removed]"
