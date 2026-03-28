"""
key_manager.py — Bulletproof Groq API key rotation engine.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXACT GROQ FREE-TIER LIMITS (verified 2025-2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Model                        RPM   RPD     TPM    TPD
  llama-3.3-70b-versatile       30  1,000  12,000  100,000
  llama-3.1-8b-instant          30 14,400   6,000  500,000
  llama-4-scout-17b             30  1,000  30,000  500,000

  RPM  = Requests Per Minute   (rolling 60-second window)
  RPD  = Requests Per Day      (resets midnight UTC)
  TPM  = Tokens Per Minute     (rolling 60-second window)
  TPD  = Tokens Per Day        (resets midnight UTC)

  Response headers expose LIVE remaining values:
    x-ratelimit-remaining-tokens    -> remaining TPM this window
    x-ratelimit-remaining-requests  -> remaining RPD today
    x-ratelimit-reset-tokens        -> e.g. "7.66s" until TPM resets
    retry-after                     -> seconds to wait after 429

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRE-EMPTIVE SWITCH THRESHOLDS (switch BEFORE hitting the wall)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TPM  -> switch when < 2,000 tokens remain in 60s window
  RPM  -> switch when < 4 requests remain in 60s window
  RPD  -> switch when < 10 requests remain for the day
  TPD  -> switch when < 5,000 tokens remain for the day

  On actual 429 -> hard cooldown = retry-after header + 2s
  On auth error -> disable key for 24h
"""

from __future__ import annotations
import os, time, threading, datetime
from collections import deque
from typing import Optional
import streamlit as st

# Exact limits for worst-case model (llama-3.3-70b) used as safe floor
DEFAULT_RPM = 30
DEFAULT_RPD = 1_000
DEFAULT_TPM = 6_000    # smallest tpm across models
DEFAULT_TPD = 100_000

SWITCH_TPM_BELOW = 2_000
SWITCH_RPM_BELOW = 4
SWITCH_RPD_BELOW = 10
SWITCH_TPD_BELOW = 5_000

HARD_COOLDOWN_BASE = 65.0
DEAD_KEY_SECONDS   = 86_400.0
WINDOW = 60.0

MAX_RETRIES: int = 0


def _load_keys() -> list[str]:
    keys: list[str] = []
    for i in range(1, 13):
        val = ""
        try: val = st.secrets.get(f"GROQ_API_KEY_{i}", "") or ""
        except Exception: pass
        if not val: val = os.getenv(f"GROQ_API_KEY_{i}", "") or ""
        if val.strip(): keys.append(val.strip())
    if not keys:
        val = ""
        try: val = st.secrets.get("GROQ_API_KEY", "") or ""
        except Exception: pass
        if not val: val = os.getenv("GROQ_API_KEY", "") or ""
        if val.strip(): keys.append(val.strip())
    return keys


_RAW_KEYS: list[str] = _load_keys()
MAX_RETRIES = max(len(_RAW_KEYS) * 3, 12)
_lock = threading.Lock()


def _midnight_utc() -> float:
    now = datetime.datetime.utcnow()
    t = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return t.timestamp()


def _new_state() -> dict:
    return {
        "cooldown_until": 0.0,
        "rpm_log": deque(),
        "tpm_log": deque(),
        "rpd_used": 0,
        "tpd_used": 0,
        "day_reset_at": _midnight_utc(),
        "hdr_remaining_tokens":   DEFAULT_TPM,
        "hdr_remaining_requests": DEFAULT_RPD,
        "hdr_reset_tokens_at":    0.0,
        "uses": 0, "errors": 0, "last_used": 0.0, "total_tokens": 0,
    }


_state: dict[str, dict] = {k: _new_state() for k in _RAW_KEYS}


def _rpm_in_window(s: dict, now: float) -> int:
    cutoff = now - WINDOW
    log = s["rpm_log"]
    while log and log[0] < cutoff: log.popleft()
    return len(log)


def _tpm_in_window(s: dict, now: float) -> int:
    cutoff = now - WINDOW
    log = s["tpm_log"]
    while log and log[0][0] < cutoff: log.popleft()
    return sum(t for _, t in log)


def _daily_reset(s: dict, now: float) -> None:
    if now >= s["day_reset_at"]:
        s["rpd_used"] = 0
        s["tpd_used"] = 0
        s["day_reset_at"] = _midnight_utc()


def _headroom_score(key: str, now: float) -> float:
    """
    Returns 0.0 if key should NOT be used right now.
    Returns 0.0-1.0 headroom ratio (higher = more room).
    Uses ALL four dimensions: RPM, TPM, RPD, TPD.
    """
    s = _state[key]
    if s["cooldown_until"] > now:
        return 0.0

    _daily_reset(s, now)

    rpm_used = _rpm_in_window(s, now)
    tpm_used = _tpm_in_window(s, now)

    rpm_remaining = DEFAULT_RPM - rpm_used
    tpm_remaining = DEFAULT_TPM - tpm_used
    rpd_remaining = DEFAULT_RPD - s["rpd_used"]
    tpd_remaining = DEFAULT_TPD - s["tpd_used"]

    # Blend with live header values if fresh
    if s["hdr_reset_tokens_at"] > now - WINDOW:
        tpm_remaining = min(tpm_remaining, s["hdr_remaining_tokens"])
        rpd_remaining = min(rpd_remaining, s["hdr_remaining_requests"])

    # Pre-emptive switch — bail before hitting the wall
    if tpm_remaining < SWITCH_TPM_BELOW: return 0.0
    if rpm_remaining < SWITCH_RPM_BELOW: return 0.0
    if rpd_remaining < SWITCH_RPD_BELOW: return 0.0
    if tpd_remaining < SWITCH_TPD_BELOW: return 0.0

    # Bottleneck score — worst dimension determines quality
    return min(
        rpm_remaining / DEFAULT_RPM,
        tpm_remaining / DEFAULT_TPM,
        rpd_remaining / DEFAULT_RPD,
        tpd_remaining / DEFAULT_TPD,
    )


def _is_available(key: str, now: float) -> bool:
    return _headroom_score(key, now) > 0.0


def get_key(override: Optional[str] = None) -> Optional[str]:
    if override and override.strip(): return override.strip()
    now = time.time()
    with _lock:
        ranked = sorted(_RAW_KEYS, key=lambda k: -_headroom_score(k, now))
        if ranked and _headroom_score(ranked[0], now) > 0:
            return ranked[0]
        # All soft-limited — pick least-loaded not on hard cooldown
        not_hard = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
        if not_hard:
            return min(not_hard, key=lambda k: _tpm_in_window(_state[k], now))
        # All hard-cooldown — earliest recovery
        return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"]) if _RAW_KEYS else None


def get_next_key(exclude_keys: Optional[set] = None) -> Optional[str]:
    now = time.time()
    excl = exclude_keys or set()
    with _lock:
        pool = [k for k in _RAW_KEYS if k not in excl]
        if not pool: return None
        ranked = sorted(pool, key=lambda k: -_headroom_score(k, now))
        if ranked and _headroom_score(ranked[0], now) > 0:
            return ranked[0]
        not_hard = [k for k in pool if _state[k]["cooldown_until"] <= now]
        if not_hard:
            return min(not_hard, key=lambda k: _tpm_in_window(_state[k], now))
        return min(pool, key=lambda k: _state[k]["cooldown_until"])


def mark_used(key: str, token_count: int = 0, headers: Optional[dict] = None) -> None:
    now = time.time()
    with _lock:
        if key not in _state: return
        s = _state[key]
        _daily_reset(s, now)
        s["uses"] += 1
        s["last_used"] = now
        s["rpd_used"] += 1
        s["rpm_log"].append(now)
        if token_count > 0:
            s["tpm_log"].append((now, token_count))
            s["tpd_used"] += token_count
            s["total_tokens"] += token_count
        if headers:
            _ingest_headers(s, headers, now)


def _ingest_headers(s: dict, headers: dict, now: float) -> None:
    """Read live remaining values directly from Groq response headers."""
    try:
        rem_tok = headers.get("x-ratelimit-remaining-tokens")
        rem_req = headers.get("x-ratelimit-remaining-requests")
        reset_tok = headers.get("x-ratelimit-reset-tokens", "")

        if rem_tok is not None:
            s["hdr_remaining_tokens"] = int(rem_tok)
            s["hdr_reset_tokens_at"]  = now

        if rem_req is not None:
            s["hdr_remaining_requests"] = int(rem_req)

        # Parse "7.66s" or "1m2.5s" into seconds
        if reset_tok:
            secs = 0.0
            rt = str(reset_tok).rstrip("s")
            if "m" in rt:
                parts = rt.split("m")
                secs = float(parts[0]) * 60 + float(parts[1] or 0)
            else:
                secs = float(rt) if rt else 0.0
            if secs > 0:
                s["hdr_reset_tokens_at"] = now + secs
    except Exception:
        pass


def mark_rate_limited(key: str, retry_after: Optional[float] = None) -> None:
    now = time.time()
    cooldown = (retry_after + 2.0) if retry_after else HARD_COOLDOWN_BASE
    with _lock:
        if key in _state:
            s = _state[key]
            s["errors"] += 1
            s["cooldown_until"] = now + cooldown
            s["rpm_log"].clear()
            s["tpm_log"].clear()
            s["hdr_remaining_tokens"]   = 0
            s["hdr_remaining_requests"] = 0


def mark_invalid(key: str) -> None:
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = time.time() + DEAD_KEY_SECONDS


def reset_all_cooldowns() -> None:
    with _lock:
        for k in _RAW_KEYS:
            s = _state[k]
            s["cooldown_until"] = 0.0
            s["rpm_log"].clear()
            s["tpm_log"].clear()
            s["hdr_remaining_tokens"]   = DEFAULT_TPM
            s["hdr_remaining_requests"] = DEFAULT_RPD


def total_keys() -> int: return len(_RAW_KEYS)
def available_keys_count() -> int:
    now = time.time()
    with _lock: return sum(1 for k in _RAW_KEYS if _is_available(k, now))
def seconds_until_available(key: str) -> float:
    with _lock: return max(0.0, _state[key]["cooldown_until"] - time.time())


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
                "key":    f"Groq #{i} ({k[:8]}…{k[-4:]})",
                "status": status,
                "rpm": f"{_rpm_in_window(s,now)}/{DEFAULT_RPM}",
                "tpm": f"{_tpm_in_window(s,now)}/{DEFAULT_TPM}",
                "rpd": f"{s['rpd_used']}/{DEFAULT_RPD}",
                "uses": s["uses"], "errors": s["errors"],
                "total_tokens": s["total_tokens"],
            })
    return rows
