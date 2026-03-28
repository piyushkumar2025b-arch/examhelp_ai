"""
key_manager.py — Smart Groq API key rotation with proactive token-rate tracking.

HOW IT WORKS
============
Groq free tier limits: ~6,000 tokens/min and ~500 requests/day per key.
Instead of waiting for a 429 to hit, we track estimated tokens used per key
in a rolling 60-second window. When a key is approaching its per-minute limit
we pre-emptively switch to the next available key — zero downtime.

On actual 429 received → hard cooldown for 62 seconds.
On auth error         → key marked dead for 24h.

Key Selection Priority
─────────────────────
1. Keys not on cooldown, sorted by fewest tokens used in current window
2. If all on cooldown, pick the one that comes off cooldown soonest

Configuration
─────────────
Local .env:
    GROQ_API_KEY_1=gsk_...
    GROQ_API_KEY_2=gsk_...  (up to GROQ_API_KEY_12)

Streamlit Cloud Secrets:
    GROQ_API_KEY_1 = "gsk_..."
    ...
    GROQ_API_KEY_12 = "gsk_..."

Single legacy key: GROQ_API_KEY = "gsk_..."
"""

from __future__ import annotations
import os
import time
import threading
from collections import deque
from typing import Optional

import streamlit as st

# ── Groq free-tier limits (conservative — actual is ~6k/min) ──────────────────
TOKEN_WINDOW_SECONDS: float = 60.0        # rolling window length
SOFT_TOKEN_LIMIT: int       = 5_000       # switch key before hitting 6k limit
HARD_COOLDOWN_SECONDS: float = 63.0       # wait after a real 429
DEAD_KEY_SECONDS: float      = 86_400.0   # 24h for invalid/auth errors
MAX_RETRIES: int             = 0           # set after keys load (see below)


# ── Load keys ─────────────────────────────────────────────────────────────────

def _load_keys() -> list[str]:
    keys: list[str] = []
    for i in range(1, 13):
        var = f"GROQ_API_KEY_{i}"
        val = ""
        try:
            val = st.secrets.get(var, "") or ""
        except Exception:
            pass
        if not val:
            val = os.getenv(var, "") or ""
        if val.strip():
            keys.append(val.strip())

    if not keys:
        for var in ("GROQ_API_KEY",):
            val = ""
            try:
                val = st.secrets.get(var, "") or ""
            except Exception:
                pass
            if not val:
                val = os.getenv(var, "") or ""
            if val.strip():
                keys.append(val.strip())
                break

    return keys


_RAW_KEYS: list[str] = _load_keys()
MAX_RETRIES = max(len(_RAW_KEYS) * 2, 6)

# ── Per-key state ──────────────────────────────────────────────────────────────

_lock = threading.Lock()

def _new_state() -> dict:
    return {
        "cooldown_until": 0.0,    # unix timestamp; 0 = available
        "uses":           0,       # total successful calls
        "errors":         0,       # total errors
        "last_used":      0.0,     # unix timestamp of last use
        # rolling token tracking: deque of (timestamp, token_count) tuples
        "token_log":      deque(), # type: deque[tuple[float, int]]
        "total_tokens":   0,       # lifetime tokens
    }

_state: dict[str, dict] = {k: _new_state() for k in _RAW_KEYS}


# ── Token tracking helpers ────────────────────────────────────────────────────

def _tokens_in_window(key: str, now: float) -> int:
    """Sum of tokens used by this key in the last TOKEN_WINDOW_SECONDS."""
    log: deque = _state[key]["token_log"]
    cutoff = now - TOKEN_WINDOW_SECONDS
    # Drop expired entries
    while log and log[0][0] < cutoff:
        log.popleft()
    return sum(t for _, t in log)


def _record_tokens(key: str, token_count: int, now: float) -> None:
    _state[key]["token_log"].append((now, token_count))
    _state[key]["total_tokens"] += token_count


def _is_available(key: str, now: float) -> bool:
    if _state[key]["cooldown_until"] > now:
        return False
    return _tokens_in_window(key, now) < SOFT_TOKEN_LIMIT


# ── Public API ────────────────────────────────────────────────────────────────

def get_key(override: Optional[str] = None) -> Optional[str]:
    """
    Return the best key to use right now.
    If override is set it is returned directly (no tracking).
    Priority: fewest tokens in window → least recently used.
    """
    if override and override.strip():
        return override.strip()

    now = time.time()
    with _lock:
        available = [k for k in _RAW_KEYS if _is_available(k, now)]
        if available:
            # Prefer key with most headroom (fewest recent tokens)
            return min(available, key=lambda k: _tokens_in_window(k, now))

        # All soft-limited or hard-cooldown — pick the one that recovers soonest
        # First check if any are just soft-limited (window will clear)
        not_hard = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
        if not_hard:
            return min(not_hard, key=lambda k: _tokens_in_window(k, now))

        # All hard-cooldown — return the one that unblocks first
        if _RAW_KEYS:
            return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"])

    return None


def get_next_key(exclude_key: Optional[str] = None) -> Optional[str]:
    """
    Return the next best key, explicitly excluding one that just failed.
    Used for immediate retry after a rate-limit hit.
    """
    now = time.time()
    with _lock:
        candidates = [k for k in _RAW_KEYS if k != exclude_key and _is_available(k, now)]
        if candidates:
            return min(candidates, key=lambda k: _tokens_in_window(k, now))

        # Fall back to anything not hard-cooldown and not excluded
        soft_ok = [k for k in _RAW_KEYS if k != exclude_key and _state[k]["cooldown_until"] <= now]
        if soft_ok:
            return min(soft_ok, key=lambda k: _tokens_in_window(k, now))

        # All bad — try anything not excluded
        remaining = [k for k in _RAW_KEYS if k != exclude_key]
        if remaining:
            return min(remaining, key=lambda k: _state[k]["cooldown_until"])

    return None


def mark_used(key: str, token_count: int = 0) -> None:
    """Record a successful API call. Pass token_count from usage metadata."""
    now = time.time()
    with _lock:
        if key in _state:
            _state[key]["uses"] += 1
            _state[key]["last_used"] = now
            if token_count > 0:
                _record_tokens(key, token_count, now)


def mark_rate_limited(key: str) -> None:
    """Hard cooldown — received a real 429 from Groq."""
    now = time.time()
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = now + HARD_COOLDOWN_SECONDS
            # Also log a big token spike so the soft-limit also fires
            _record_tokens(key, SOFT_TOKEN_LIMIT, now)


def mark_invalid(key: str) -> None:
    """Auth error — disable for 24 hours."""
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = time.time() + DEAD_KEY_SECONDS


def seconds_until_available(key: str) -> float:
    with _lock:
        return max(0.0, _state[key]["cooldown_until"] - time.time())


def total_keys() -> int:
    return len(_RAW_KEYS)


def available_keys_count() -> int:
    now = time.time()
    with _lock:
        return sum(1 for k in _RAW_KEYS if _is_available(k, now))


def tokens_used_this_minute(key: str) -> int:
    now = time.time()
    with _lock:
        return _tokens_in_window(key, now)


def status_table() -> list[dict]:
    now = time.time()
    rows = []
    with _lock:
        for i, k in enumerate(_RAW_KEYS, 1):
            s = _state[k]
            cd = s["cooldown_until"]
            toks = _tokens_in_window(k, now)
            if cd > now:
                status = f"⏳ cooldown {cd - now:.0f}s"
            elif toks >= SOFT_TOKEN_LIMIT:
                status = f"🔴 token limit ({toks}/{SOFT_TOKEN_LIMIT})"
            else:
                pct = int(toks / SOFT_TOKEN_LIMIT * 100)
                status = f"✅ {pct}% used ({toks}/{SOFT_TOKEN_LIMIT} tok/min)"
            rows.append({
                "key": f"Key #{i}  ({k[:8]}…{k[-4:]})",
                "status": status,
                "uses": s["uses"],
                "errors": s["errors"],
                "tokens_lifetime": s["total_tokens"],
            })
    return rows


def reset_all_cooldowns() -> None:
    with _lock:
        for k in _RAW_KEYS:
            _state[k]["cooldown_until"] = 0.0
            _state[k]["token_log"].clear()
