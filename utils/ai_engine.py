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
import json, time, threading, urllib.request, urllib.error
from typing import Iterator, Optional, Dict, List

# ── Models ─────────────────────────────────────────────────
GEMINI_MODELS = [
    "gemini-2.0-flash",        # primary — 15 RPM, 1500 RPD free
    "gemini-1.5-flash",        # fallback
    "gemini-1.5-flash-8b",     # last-resort — fastest, smallest quota
]
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

GEMINI_RPM     = 15
GEMINI_RPD     = 1_500
GEMINI_TPM     = 1_000_000
GEMINI_SWITCH_RPM = 3   # rotate key when < 3 RPM remain

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
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())

    candidates = result.get("candidates", [])
    if not candidates:
        raise ValueError("Empty candidates in Gemini response")
    parts_out = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts_out)


def _classify_error(err: Exception) -> str:
    s = str(err).lower()
    if "429" in s or "quota" in s or "rate" in s:
        return "rate_limit"
    if "403" in s or "invalid" in s or "api key" in s:
        return "bad_key"
    if "timeout" in s or "timed out" in s:
        return "timeout"
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
    tried: set = set()
    last_err: Exception = RuntimeError("No Gemini keys available.")

    for model in GEMINI_MODELS:
        pool_attempts = max(len(_pool._keys) if _pool._loaded else 1, 1)
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
                if etype == "rate_limit":
                    ks.cooldown(65)
                elif etype == "bad_key":
                    ks.cooldown(3600)  # park bad key for 1 hour
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
def generate(
    prompt: str,
    system: str = "",
    provider: str = "gemini",   # kept for API compat — always gemini now
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
) -> str:
    """Generate a response. Returns full text string."""
    return _call_gemini(
        prompt=prompt,
        system=system,
        image_b64=image_data,
        image_mime=image_mime,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def generate_stream(
    prompt: str,
    system: str = "",
    provider: str = "gemini",   # kept for API compat
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Iterator[str]:
    """Generate a streaming response. Yields text chunks."""
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
