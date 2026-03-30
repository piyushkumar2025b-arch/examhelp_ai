"""
gemini_key_manager.py — 9-Key Gemini Rotation Engine
=====================================================
Reads GEMINI_API_KEY_1 … GEMINI_API_KEY_9 from Streamlit secrets.
Round-robin rotation with per-key RPM cooldown.

Free-tier limits (per key, per project):
  gemini-2.0-flash   : 15 RPM, 1500 RPD, 1M TPM
  gemini-1.5-flash-8b: 15 RPM, 1000 RPD, 250K TPM
"""

from __future__ import annotations
import time, threading
from typing import List, Optional

from utils.secret_manager import GEMINI_KEYS

_lock   = threading.Lock()
_index  = 0          # round-robin cursor
_cooldowns: dict = {}  # key -> cooldown_until timestamp

RPM_WINDOW   = 60     # seconds
RPM_LIMIT    = 14     # stay 1 below hard limit for safety
COOLDOWN_SEC = 65     # back off for 65 s after hitting limit

def _now() -> float:
    return time.monotonic()

def get_key() -> Optional[str]:
    """Return the next available key, or None if all are cooling down."""
    global _index
    if not GEMINI_KEYS:
        return None
    with _lock:
        n = len(GEMINI_KEYS)
        for _ in range(n):
            key = GEMINI_KEYS[_index % n]
            _index = (_index + 1) % n
            if _now() >= _cooldowns.get(key, 0):
                return key
    return None  # all keys on cooldown

def mark_rate_limited(key: str) -> None:
    """Call this when a 429 is received for a key."""
    with _lock:
        _cooldowns[key] = _now() + COOLDOWN_SEC

def status() -> dict:
    """Return a status dict for display."""
    now = _now()
    total = len(GEMINI_KEYS)
    available = sum(1 for k in GEMINI_KEYS if now >= _cooldowns.get(k, 0))
    return {
        "total": total,
        "available": available,
        "cooling_down": total - available,
    }
