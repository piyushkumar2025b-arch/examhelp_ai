"""
gemini_key_manager.py — ELITE Gemini Key Rotation Engine v2.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GEMINI FREE-TIER LIMITS (verified March 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Model                  RPM   RPD      TPM
  gemini-1.5-flash        15   1,500  1,000,000
  gemini-2.5-flash-lite   15   1,000    250,000

  NOTE: Limits are per GCP project. Each key should be from a
  different Google AI Studio project to get independent quota.

  Daily reset: midnight Pacific Time (UTC-8).
  RPM: sliding 60-second window.
"""

from __future__ import annotations
import os, time, threading, datetime, math
from collections import deque
from typing import Optional, Dict, Any

try:
    import streamlit as st
    _ST = True
except ImportError:
    _ST = False

DEFAULT_RPM = 15
DEFAULT_RPD = 1_500

SWITCH_RPM_BELOW = 3
SWITCH_RPD_BELOW = 8

HARD_COOLDOWN_BASE = 67.0
DEAD_KEY_SECONDS   = 86_400.0
WINDOW             = 60.0

MAX_KEYS    = 10  # Expanded from 7
MAX_RETRIES = 0


def _load_gemini_keys() -> list[str]:
    keys: list[str] = []
    for i in range(1, MAX_KEYS + 1):
        val = ""
        if _ST:
            try: val = st.secrets.get(f"GEMINI_API_KEY_{i}", "") or ""
            except Exception: pass
        if not val: val = os.getenv(f"GEMINI_API_KEY_{i}", "") or ""
        if val.strip(): keys.append(val.strip())
    if not keys:
        val = ""
        if _ST:
            try: val = st.secrets.get("GEMINI_API_KEY", "") or ""
            except Exception: pass
        if not val: val = os.getenv("GEMINI_API_KEY", "") or ""
        if val.strip(): keys.append(val.strip())
    return keys


_RAW_KEYS: list[str] = _load_gemini_keys()
MAX_RETRIES = max(len(_RAW_KEYS) * 3, 10)
_lock = threading.RLock()


def _midnight_pt() -> float:
    """Midnight Pacific Time — Gemini RPD resets here (UTC-8)."""
    now_utc = datetime.datetime.utcnow()
    midnight_utc = (now_utc + datetime.timedelta(days=1)).replace(
        hour=8, minute=0, second=0, microsecond=0)
    return midnight_utc.timestamp()


def _new_state() -> Dict[str, Any]:
    return {
        "cooldown_until": 0.0,
        "rpm_log":   deque(),
        "rpd_used":  0,
        "day_reset_at": _midnight_pt(),
        "uses": 0, "errors": 0,
        "consecutive_errors": 0,
        "rate_limit_hits": 0,
        "last_used": 0.0, "last_error": 0.0,
        "total_requests": 0,
    }


_state: Dict[str, Dict[str, Any]] = {k: _new_state() for k in _RAW_KEYS}


def _prune(log: deque, cutoff: float) -> None:
    while log and log[0] < cutoff: log.popleft()


def _rpm_in_window(s: Dict, now: float) -> int:
    _prune(s["rpm_log"], now - WINDOW)
    return len(s["rpm_log"])


def _daily_reset(s: Dict, now: float) -> None:
    if now >= s["day_reset_at"]:
        s["rpd_used"] = 0
        s["day_reset_at"] = _midnight_pt()


def _headroom_score(key: str, now: float) -> float:
    s = _state[key]
    if s["cooldown_until"] > now: return 0.0
    _daily_reset(s, now)

    rpm_rem = DEFAULT_RPM - _rpm_in_window(s, now)
    rpd_rem = DEFAULT_RPD - s["rpd_used"]

    if rpm_rem < SWITCH_RPM_BELOW: return 0.0
    if rpd_rem < SWITCH_RPD_BELOW: return 0.0

    score = 0.5 * (rpm_rem / DEFAULT_RPM) + 0.5 * (rpd_rem / DEFAULT_RPD)

    # Health penalty
    ce = s.get("consecutive_errors", 0)
    if ce > 0:
        score *= math.exp(-0.4 * ce)

    return max(0.0, min(1.0, score))


def _is_available(key: str, now: float) -> bool:
    return _headroom_score(key, now) > 0.0


def get_key(override: Optional[str] = None) -> Optional[str]:
    if override and override.strip(): return override.strip()
    now = time.time()
    with _lock:
        if not _RAW_KEYS: return None
        scored = sorted(_RAW_KEYS, key=lambda k: -_headroom_score(k, now))
        if scored and _headroom_score(scored[0], now) > 0: return scored[0]
        not_hard = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
        if not_hard: return min(not_hard, key=lambda k: _rpm_in_window(_state[k], now))
        return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"]) if _RAW_KEYS else None


def get_next_key(exclude_keys: Optional[set] = None) -> Optional[str]:
    now = time.time()
    excl = exclude_keys or set()
    with _lock:
        pool = [k for k in _RAW_KEYS if k not in excl]
        if not pool: return None
        scored = sorted(pool, key=lambda k: -_headroom_score(k, now))
        if scored and _headroom_score(scored[0], now) > 0: return scored[0]
        not_hard = [k for k in pool if _state[k]["cooldown_until"] <= now]
        if not_hard: return min(not_hard, key=lambda k: _rpm_in_window(_state[k], now))
        return min(pool, key=lambda k: _state[k]["cooldown_until"])


def mark_used(key: str) -> None:
    now = time.time()
    with _lock:
        if key not in _state: return
        s = _state[key]
        _daily_reset(s, now)
        s["uses"] += 1; s["total_requests"] += 1
        s["last_used"] = now; s["rpd_used"] += 1
        s["rpm_log"].append(now)
        s["consecutive_errors"] = 0


def mark_rate_limited(key: str, retry_after: Optional[float] = None) -> None:
    now = time.time()
    cooldown = (retry_after + 2.0) if (retry_after and retry_after > 0) else HARD_COOLDOWN_BASE
    with _lock:
        if key not in _state: return
        s = _state[key]
        s["errors"] += 1; s["rate_limit_hits"] += 1
        s["consecutive_errors"] = min(s.get("consecutive_errors", 0) + 1, 10)
        s["last_error"] = now; s["cooldown_until"] = now + cooldown
        s["rpm_log"].clear()


def mark_invalid(key: str) -> None:
    now = time.time()
    with _lock:
        if key not in _state: return
        s = _state[key]
        s["errors"] += 1; s["consecutive_errors"] = 99
        s["last_error"] = now; s["cooldown_until"] = now + DEAD_KEY_SECONDS


def reset_all_cooldowns() -> None:
    with _lock:
        for k in _RAW_KEYS:
            _state[k]["cooldown_until"] = 0.0
            _state[k]["rpm_log"].clear()
            _state[k]["consecutive_errors"] = 0


def total_keys() -> int: return len(_RAW_KEYS)

def available_keys_count() -> int:
    now = time.time()
    with _lock: return sum(1 for k in _RAW_KEYS if _is_available(k, now))


def status_table() -> list[dict]:
    now = time.time()
    rows = []
    with _lock:
        for i, k in enumerate(_RAW_KEYS, 1):
            s = _state[k]; _daily_reset(s, now)
            score = _headroom_score(k, now); cd = s["cooldown_until"]
            if cd > now:
                rem = cd - now
                status = f"⛔ dead {rem/3600:.1f}h" if rem > 3600 else f"⏳ cooldown {rem:.0f}s"
            elif score == 0: status = "🔴 pre-limit"
            elif score > 0.7: status = f"🟢 {score*100:.0f}%"
            else: status = f"🟡 {score*100:.0f}%"
            rows.append({
                "key": f"Gemini #{i} …{k[-4:]}", "status": status,
                "rpm": f"{_rpm_in_window(s,now)}/{DEFAULT_RPM}",
                "rpd": f"{s['rpd_used']}/{DEFAULT_RPD}",
                "uses": s["uses"], "errors": s["errors"],
                "rl_hits": s.get("rate_limit_hits", 0),
            })
    return rows
