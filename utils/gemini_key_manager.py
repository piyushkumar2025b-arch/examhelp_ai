"""
gemini_key_manager.py — Smart Gemini API key rotation with proactive quota tracking.

HOW IT WORKS
============
Google Gemini free tier limits (per key):
  - 15 requests per minute (RPM)
  - 1,000,000 tokens per minute (TPM)
  - 1,500 requests per day (RPD)

Strategy:
  1. Track rolling 60-second request window per key.
  2. Pre-emptively rotate before hitting RPM limit (switch at 13/15).
  3. On real 429 → hard cooldown for 65 seconds.
  4. On auth/quota error → disable for 24h.
  5. All 7 keys work simultaneously — round-robin with headroom-first selection.

Configuration
─────────────
Local .env:
    GEMINI_API_KEY_1=AIza...
    GEMINI_API_KEY_2=AIza...   (up to GEMINI_API_KEY_7)

Streamlit Cloud Secrets:
    GEMINI_API_KEY_1 = "AIza..."
    ...

Single legacy key: GEMINI_API_KEY = "AIza..."
"""

from __future__ import annotations
import os
import time
import threading
from collections import deque
from typing import Optional

import streamlit as st

# ── Gemini free-tier limits (conservative) ────────────────────────────────────
REQUEST_WINDOW_SECONDS: float  = 60.0        # rolling window
SOFT_RPM_LIMIT: int            = 13          # switch before 15 RPM limit
HARD_COOLDOWN_SECONDS: float   = 65.0        # after a real 429
DEAD_KEY_SECONDS: float        = 86_400.0    # 24h for auth/quota errors
MAX_KEYS: int                  = 7           # we have 7 Gemini keys
MAX_RETRIES: int               = 0           # set after keys load


# ── Load keys ─────────────────────────────────────────────────────────────────

def _load_gemini_keys() -> list[str]:
    keys: list[str] = []
    for i in range(1, MAX_KEYS + 1):
        var = f"GEMINI_API_KEY_{i}"
        val = ""
        try:
            val = st.secrets.get(var, "") or ""
        except Exception:
            pass
        if not val:
            val = os.getenv(var, "") or ""
        if val.strip():
            keys.append(val.strip())

    # Fallback: single legacy key
    if not keys:
        for var in ("GEMINI_API_KEY",):
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


_RAW_KEYS: list[str] = _load_gemini_keys()
MAX_RETRIES = max(len(_RAW_KEYS) * 2, 6)

# ── Per-key state ──────────────────────────────────────────────────────────────

_lock = threading.Lock()


def _new_state() -> dict:
    return {
        "cooldown_until": 0.0,     # unix ts; 0 = available
        "uses":           0,
        "errors":         0,
        "last_used":      0.0,
        "req_log":        deque(),  # deque of timestamps (one per request)
        "total_requests": 0,
    }


_state: dict[str, dict] = {k: _new_state() for k in _RAW_KEYS}


# ── Request tracking helpers ──────────────────────────────────────────────────

def _reqs_in_window(key: str, now: float) -> int:
    """Count requests made by this key in the last REQUEST_WINDOW_SECONDS."""
    log: deque = _state[key]["req_log"]
    cutoff = now - REQUEST_WINDOW_SECONDS
    while log and log[0] < cutoff:
        log.popleft()
    return len(log)


def _record_request(key: str, now: float) -> None:
    _state[key]["req_log"].append(now)
    _state[key]["total_requests"] += 1


def _is_available(key: str, now: float) -> bool:
    if _state[key]["cooldown_until"] > now:
        return False
    return _reqs_in_window(key, now) < SOFT_RPM_LIMIT


# ── Public API ────────────────────────────────────────────────────────────────

def get_key(override: Optional[str] = None) -> Optional[str]:
    """
    Return the best Gemini key to use right now.
    Priority: fewest requests in rolling window → least recently used.
    """
    if override and override.strip():
        return override.strip()

    now = time.time()
    with _lock:
        available = [k for k in _RAW_KEYS if _is_available(k, now)]
        if available:
            return min(available, key=lambda k: (_reqs_in_window(k, now), _state[k]["last_used"]))

        # All at soft limit — any not hard-cooldown?
        not_hard = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
        if not_hard:
            return min(not_hard, key=lambda k: _reqs_in_window(k, now))

        # All hard-cooldown — pick earliest recovery
        if _RAW_KEYS:
            return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"])

    return None


def get_next_key(exclude_key: Optional[str] = None) -> Optional[str]:
    """Return best key, explicitly excluding one that just failed."""
    now = time.time()
    with _lock:
        candidates = [k for k in _RAW_KEYS if k != exclude_key and _is_available(k, now)]
        if candidates:
            return min(candidates, key=lambda k: (_reqs_in_window(k, now), _state[k]["last_used"]))

        soft_ok = [k for k in _RAW_KEYS
                   if k != exclude_key and _state[k]["cooldown_until"] <= now]
        if soft_ok:
            return min(soft_ok, key=lambda k: _reqs_in_window(k, now))

        remaining = [k for k in _RAW_KEYS if k != exclude_key]
        if remaining:
            return min(remaining, key=lambda k: _state[k]["cooldown_until"])

    return None


def mark_used(key: str) -> None:
    """Record a successful Gemini API call."""
    now = time.time()
    with _lock:
        if key in _state:
            _state[key]["uses"] += 1
            _state[key]["last_used"] = now
            _record_request(key, now)


def mark_rate_limited(key: str) -> None:
    """Hard cooldown — received a 429 from Gemini."""
    now = time.time()
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = now + HARD_COOLDOWN_SECONDS
            # Flood the request log so soft-limit also fires
            for _ in range(SOFT_RPM_LIMIT):
                _state[key]["req_log"].append(now)


def mark_invalid(key: str) -> None:
    """Auth/quota exhausted — disable for 24h."""
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = time.time() + DEAD_KEY_SECONDS


def total_keys() -> int:
    return len(_RAW_KEYS)


def available_keys_count() -> int:
    now = time.time()
    with _lock:
        return sum(1 for k in _RAW_KEYS if _is_available(k, now))


def seconds_until_available(key: str) -> float:
    with _lock:
        return max(0.0, _state[key]["cooldown_until"] - time.time())


def status_table() -> list[dict]:
    now = time.time()
    rows = []
    with _lock:
        for i, k in enumerate(_RAW_KEYS, 1):
            s = _state[k]
            cd = s["cooldown_until"]
            reqs = _reqs_in_window(k, now)
            if cd > now:
                status = f"⏳ cooldown {cd - now:.0f}s"
            elif reqs >= SOFT_RPM_LIMIT:
                status = f"🔴 RPM limit ({reqs}/{SOFT_RPM_LIMIT})"
            else:
                pct = int(reqs / SOFT_RPM_LIMIT * 100)
                status = f"✅ {pct}% used ({reqs}/{SOFT_RPM_LIMIT} req/min)"
            rows.append({
                "key": f"Gemini #{i}  ({k[:8]}…{k[-4:]})",
                "status": status,
                "uses": s["uses"],
                "errors": s["errors"],
                "total_requests": s["total_requests"],
            })
    return rows


def reset_all_cooldowns() -> None:
    with _lock:
        for k in _RAW_KEYS:
            _state[k]["cooldown_until"] = 0.0
            _state[k]["req_log"].clear()
