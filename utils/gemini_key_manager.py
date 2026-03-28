"""
gemini_key_manager.py — Bulletproof Gemini API key rotation engine.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXACT GEMINI FREE-TIER LIMITS (verified March 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Model                  RPM   RPD      TPM
  gemini-1.5-flash        15   1,500  1,000,000
  gemini-2.5-flash        10     250    250,000
  gemini-2.5-flash-lite   15   1,000    250,000

  CRITICAL: Limits are per GOOGLE CLOUD PROJECT, NOT per API key.
  Multiple keys from the same project share the same quota pool.
  We treat each of our 7 keys as a separate project (which they are
  if the user created them in different AI Studio projects).

  Rolling window: RPM uses a sliding 60-second window.
  Daily reset: RPD resets at midnight Pacific Time.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRE-EMPTIVE SWITCH THRESHOLDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RPM -> switch when < 3 requests remain in 60s window
  RPD -> switch when < 5 requests remain today
"""

from __future__ import annotations
import os, time, threading, datetime
from collections import deque
from typing import Optional
import streamlit as st

# Using gemini-1.5-flash limits as baseline (most generous, widely available)
DEFAULT_RPM = 15
DEFAULT_RPD = 1_500
DEFAULT_TPM = 1_000_000   # effectively unlimited for our usage

SWITCH_RPM_BELOW = 3
SWITCH_RPD_BELOW = 5

HARD_COOLDOWN_BASE = 67.0   # 60s window + 7s buffer
DEAD_KEY_SECONDS   = 86_400.0
WINDOW = 60.0

MAX_KEYS    = 7
MAX_RETRIES = 0


def _load_gemini_keys() -> list[str]:
    keys: list[str] = []
    for i in range(1, MAX_KEYS + 1):
        val = ""
        try: val = st.secrets.get(f"GEMINI_API_KEY_{i}", "") or ""
        except Exception: pass
        if not val: val = os.getenv(f"GEMINI_API_KEY_{i}", "") or ""
        if val.strip(): keys.append(val.strip())
    if not keys:
        val = ""
        try: val = st.secrets.get("GEMINI_API_KEY", "") or ""
        except Exception: pass
        if not val: val = os.getenv("GEMINI_API_KEY", "") or ""
        if val.strip(): keys.append(val.strip())
    return keys


_RAW_KEYS: list[str] = _load_gemini_keys()
MAX_RETRIES = max(len(_RAW_KEYS) * 3, 7)
_lock = threading.Lock()


def _midnight_pt() -> float:
    """Midnight Pacific Time (UTC-8 / UTC-7 DST) — Gemini RPD resets here."""
    now_utc = datetime.datetime.utcnow()
    # Use UTC-8 as conservative approximation
    midnight_utc = (now_utc + datetime.timedelta(days=1)).replace(
        hour=8, minute=0, second=0, microsecond=0)
    return midnight_utc.timestamp()


def _new_state() -> dict:
    return {
        "cooldown_until": 0.0,
        "rpm_log":  deque(),   # timestamps
        "rpd_used": 0,
        "day_reset_at": _midnight_pt(),
        "uses": 0, "errors": 0, "last_used": 0.0, "total_requests": 0,
    }


_state: dict[str, dict] = {k: _new_state() for k in _RAW_KEYS}


def _rpm_in_window(s: dict, now: float) -> int:
    cutoff = now - WINDOW
    log = s["rpm_log"]
    while log and log[0] < cutoff: log.popleft()
    return len(log)


def _daily_reset(s: dict, now: float) -> None:
    if now >= s["day_reset_at"]:
        s["rpd_used"] = 0
        s["day_reset_at"] = _midnight_pt()


def _headroom_score(key: str, now: float) -> float:
    s = _state[key]
    if s["cooldown_until"] > now: return 0.0
    _daily_reset(s, now)

    rpm_remaining = DEFAULT_RPM - _rpm_in_window(s, now)
    rpd_remaining = DEFAULT_RPD - s["rpd_used"]

    if rpm_remaining < SWITCH_RPM_BELOW: return 0.0
    if rpd_remaining < SWITCH_RPD_BELOW: return 0.0

    return min(rpm_remaining / DEFAULT_RPM, rpd_remaining / DEFAULT_RPD)


def _is_available(key: str, now: float) -> bool:
    return _headroom_score(key, now) > 0.0


def get_key(override: Optional[str] = None) -> Optional[str]:
    if override and override.strip(): return override.strip()
    now = time.time()
    with _lock:
        ranked = sorted(_RAW_KEYS, key=lambda k: -_headroom_score(k, now))
        if ranked and _headroom_score(ranked[0], now) > 0: return ranked[0]
        not_hard = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
        if not_hard: return min(not_hard, key=lambda k: _rpm_in_window(_state[k], now))
        return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"]) if _RAW_KEYS else None


def get_next_key(exclude_keys: Optional[set] = None) -> Optional[str]:
    now = time.time()
    excl = exclude_keys or set()
    with _lock:
        pool = [k for k in _RAW_KEYS if k not in excl]
        if not pool: return None
        ranked = sorted(pool, key=lambda k: -_headroom_score(k, now))
        if ranked and _headroom_score(ranked[0], now) > 0: return ranked[0]
        not_hard = [k for k in pool if _state[k]["cooldown_until"] <= now]
        if not_hard: return min(not_hard, key=lambda k: _rpm_in_window(_state[k], now))
        return min(pool, key=lambda k: _state[k]["cooldown_until"])


def mark_used(key: str) -> None:
    now = time.time()
    with _lock:
        if key not in _state: return
        s = _state[key]
        _daily_reset(s, now)
        s["uses"]     += 1
        s["last_used"]  = now
        s["rpd_used"]  += 1
        s["total_requests"] += 1
        s["rpm_log"].append(now)


def mark_rate_limited(key: str, retry_after: Optional[float] = None) -> None:
    now = time.time()
    cooldown = (retry_after + 2.0) if retry_after else HARD_COOLDOWN_BASE
    with _lock:
        if key in _state:
            s = _state[key]
            s["errors"] += 1
            s["cooldown_until"] = now + cooldown
            s["rpm_log"].clear()


def mark_invalid(key: str) -> None:
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = time.time() + DEAD_KEY_SECONDS


def reset_all_cooldowns() -> None:
    with _lock:
        for k in _RAW_KEYS:
            _state[k]["cooldown_until"] = 0.0
            _state[k]["rpm_log"].clear()


def total_keys() -> int: return len(_RAW_KEYS)
def available_keys_count() -> int:
    now = time.time()
    with _lock: return sum(1 for k in _RAW_KEYS if _is_available(k, now))


def status_table() -> list[dict]:
    now = time.time()
    rows = []
    with _lock:
        for i, k in enumerate(_RAW_KEYS, 1):
            s = _state[k]
            _daily_reset(s, now)
            score = _headroom_score(k, now)
            cd    = s["cooldown_until"]
            if cd > now:   status = f"⏳ cooldown {cd-now:.0f}s"
            elif score==0: status = "🔴 pre-limit → switching"
            else:          status = f"✅ {score*100:.0f}% headroom"
            rows.append({
                "key":    f"Gemini #{i} ({k[:8]}…{k[-4:]})",
                "status": status,
                "rpm": f"{_rpm_in_window(s,now)}/{DEFAULT_RPM}",
                "rpd": f"{s['rpd_used']}/{DEFAULT_RPD}",
                "uses": s["uses"], "errors": s["errors"],
            })
    return rows
