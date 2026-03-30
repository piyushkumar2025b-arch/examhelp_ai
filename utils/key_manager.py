# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# key_manager.py — ELITE Groq API Key Rotation Engine v3.0
# 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXACT GROQ FREE-TIER LIMITS (verified March 2026)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   Model                        RPM   RPD      TPM      TPD
#   llama-4-scout-17b-16e         30  1,000   30,000   500,000  ← PRIMARY (best limits)
#   llama-3.3-70b-versatile       30  1,000   12,000   100,000
#   llama-3.1-8b-instant          30 14,400    6,000   500,000
#   whisper-large-v3              20    200      N/A       N/A
# 
# SCORING ALGORITHM v3 — Weighted composite across 4 dimensions:
#   Score = 0.35*rpm_ratio + 0.35*tpm_ratio + 0.20*rpd_ratio + 0.10*tpd_ratio
#   Live Groq headers override local estimates when < 60s old.
#   Consecutive errors apply exponential health penalty.
#   Pre-emptive switch happens BEFORE hitting any wall.
# """
# 
# from __future__ import annotations
# import os, time, threading, datetime, math
# from collections import deque
# from typing import Optional, Dict, Any
# 
# # CRITICAL: Load .env BEFORE key loading (module-level)
# def _force_load_env():
#     """Bulletproof .env loader — works even without python-dotenv."""
#     try:
#         from dotenv import load_dotenv
#         load_dotenv()
#         return
#     except ImportError:
#         pass
#     # Manual fallback: parse .env ourselves
#     import pathlib
#     for env_path in [
#         pathlib.Path(__file__).resolve().parent.parent / ".env",
#         pathlib.Path.cwd() / ".env",
#     ]:
#         if env_path.is_file():
#             try:
#                 for line in env_path.read_text(encoding="utf-8").splitlines():
#                     line = line.strip()
#                     if not line or line.startswith("#") or "=" not in line:
#                         continue
#                     key, _, value = line.partition("=")
#                     key = key.strip()
#                     value = value.strip().strip("'\"")
#                     if key and value and key not in os.environ:
#                         os.environ[key] = value
#             except Exception:
#                 pass
#             break
# 
# _force_load_env()
# 
# try:
#     import streamlit as st
#     _ST = True
# except ImportError:
#     _ST = False
# 
# # Floor limits matched to primary model (llama-4-scout-17b)
# _FLOOR_RPM = 30
# _FLOOR_RPD = 1_000
# _FLOOR_TPM = 30_000
# _FLOOR_TPD = 500_000
# 
# # Pre-emptive switch thresholds (tuned for 30K TPM)
# SWITCH_RPM_BELOW = 5
# SWITCH_TPM_BELOW = 5_000
# SWITCH_RPD_BELOW = 15
# SWITCH_TPD_BELOW = 20_000
# 
# # Timing
# HARD_COOLDOWN_BASE = 67.0
# DEAD_KEY_SECONDS   = 86_400.0
# WINDOW             = 60.0
# 
# # Scoring weights
# W_RPM, W_TPM, W_RPD, W_TPD = 0.35, 0.35, 0.20, 0.10
# 
# MAX_RETRIES: int = 0
# 
# 
# def _load_keys() -> list[str]:
#     keys: list[str] = []
#     for i in range(1, 21):
#         val = ""
#         if _ST:
#             try: val = st.secrets.get(f"GROQ_API_KEY_{i}", "") or ""
#             except Exception: pass
#         if not val: val = os.getenv(f"GROQ_API_KEY_{i}", "") or ""
#         if val.strip(): keys.append(val.strip())
#     if not keys:
#         val = ""
#         if _ST:
#             try: val = st.secrets.get("GROQ_API_KEY", "") or ""
#             except Exception: pass
#         if not val: val = os.getenv("GROQ_API_KEY", "") or ""
#         if val.strip(): keys.append(val.strip())
#     return keys
# 
# 
# _RAW_KEYS: list[str] = _load_keys()
# MAX_RETRIES = max(len(_RAW_KEYS) * 4, 20)
# _lock = threading.RLock()
# 
# 
# def _midnight_utc() -> float:
#     now = datetime.datetime.utcnow()
#     t = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
#     return t.timestamp()
# 
# 
# def _new_state() -> Dict[str, Any]:
#     return {
#         "cooldown_until": 0.0,
#         "rpm_log": deque(),
#         "tpm_log": deque(),
#         "rpd_used": 0,
#         "tpd_used": 0,
#         "day_reset_at": _midnight_utc(),
#         "hdr_remaining_tokens": _FLOOR_TPM,
#         "hdr_remaining_requests": _FLOOR_RPD,
#         "hdr_freshness": 0.0,
#         "uses": 0,
#         "errors": 0,
#         "consecutive_errors": 0,
#         "rate_limit_hits": 0,
#         "last_used": 0.0,
#         "last_error": 0.0,
#         "total_tokens": 0,
#         "total_requests": 0,
#         "model_usage": {},
#     }
# 
# 
# _state: Dict[str, Dict[str, Any]] = {k: _new_state() for k in _RAW_KEYS}
# 
# 
# def _prune(log: deque, cutoff: float, is_tuple: bool) -> None:
#     while log:
#         ts = log[0][0] if is_tuple else log[0]
#         if ts < cutoff: log.popleft()
#         else: break
# 
# 
# def _rpm_in_window(s: Dict, now: float) -> int:
#     _prune(s["rpm_log"], now - WINDOW, False)
#     return len(s["rpm_log"])
# 
# 
# def _tpm_in_window(s: Dict, now: float) -> int:
#     _prune(s["tpm_log"], now - WINDOW, True)
#     return sum(t for _, t in s["tpm_log"])
# 
# 
# def _daily_reset(s: Dict, now: float) -> None:
#     if now >= s["day_reset_at"]:
#         s["rpd_used"] = 0; s["tpd_used"] = 0
#         s["day_reset_at"] = _midnight_utc()
#         s["hdr_remaining_tokens"] = _FLOOR_TPM
#         s["hdr_remaining_requests"] = _FLOOR_RPD
# 
# 
# def _headroom_score(key: str, now: float) -> float:
#     """Weighted headroom score 0.0-1.0. 0.0 = must not use."""
#     s = _state[key]
#     if s["cooldown_until"] > now: return 0.0
#     _daily_reset(s, now)
# 
#     rpm_used = _rpm_in_window(s, now)
#     tpm_used = _tpm_in_window(s, now)
# 
#     rpm_rem = _FLOOR_RPM - rpm_used
#     tpm_rem = _FLOOR_TPM - tpm_used
#     rpd_rem = _FLOOR_RPD - s["rpd_used"]
#     tpd_rem = _FLOOR_TPD - s["tpd_used"]
# 
#     # Blend with live header values (trust decays linearly over 60s)
#     hdr_age = now - s["hdr_freshness"]
#     if hdr_age < WINDOW and s["hdr_freshness"] > 0:
#         trust = max(0.0, 1.0 - hdr_age / WINDOW)
#         tpm_rem = int(tpm_rem * (1 - trust) + s["hdr_remaining_tokens"] * trust)
#         rpd_rem = int(rpd_rem * (1 - trust) + s["hdr_remaining_requests"] * trust)
#         tpm_rem = min(tpm_rem, _FLOOR_TPM - tpm_used)  # clamp
# 
#     # Pre-emptive thresholds
#     if rpm_rem < SWITCH_RPM_BELOW: return 0.0
#     if tpm_rem < SWITCH_TPM_BELOW: return 0.0
#     if rpd_rem < SWITCH_RPD_BELOW: return 0.0
#     if tpd_rem < SWITCH_TPD_BELOW: return 0.0
# 
#     # Weighted composite
#     score = (
#         W_RPM * (rpm_rem / _FLOOR_RPM) +
#         W_TPM * (tpm_rem / _FLOOR_TPM) +
#         W_RPD * (rpd_rem / _FLOOR_RPD) +
#         W_TPD * (tpd_rem / _FLOOR_TPD)
#     )
# 
#     # Health penalty for repeated errors
#     ce = s.get("consecutive_errors", 0)
#     if ce > 0:
#         score *= math.exp(-0.4 * ce)
# 
#     return max(0.0, min(1.0, score))
# 
# 
# def _is_available(key: str, now: float) -> bool:
#     return _headroom_score(key, now) > 0.0
# 
# 
# def get_key(override: Optional[str] = None, model: Optional[str] = None) -> Optional[str]:
#     if override and override.strip(): return override.strip()
#     now = time.time()
#     with _lock:
#         if not _RAW_KEYS: return None
#         scored = sorted(_RAW_KEYS, key=lambda k: -_headroom_score(k, now))
#         if scored and _headroom_score(scored[0], now) > 0: return scored[0]
#         not_hard = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
#         if not_hard: return min(not_hard, key=lambda k: _tpm_in_window(_state[k], now))
#         return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"]) if _RAW_KEYS else None
# 
# 
# def get_next_key(exclude_keys: Optional[set] = None, model: Optional[str] = None) -> Optional[str]:
#     now = time.time()
#     excl = exclude_keys or set()
#     with _lock:
#         pool = [k for k in _RAW_KEYS if k not in excl]
#         if not pool: return None
#         scored = sorted(pool, key=lambda k: -_headroom_score(k, now))
#         if scored and _headroom_score(scored[0], now) > 0: return scored[0]
#         not_hard = [k for k in pool if _state[k]["cooldown_until"] <= now]
#         if not_hard: return min(not_hard, key=lambda k: _tpm_in_window(_state[k], now))
#         return min(pool, key=lambda k: _state[k]["cooldown_until"])
# 
# 
# def mark_used(key: str, token_count: int = 0, headers: Optional[dict] = None, model: Optional[str] = None) -> None:
#     now = time.time()
#     with _lock:
#         if key not in _state: return
#         s = _state[key]
#         _daily_reset(s, now)
#         s["uses"] += 1; s["total_requests"] += 1
#         s["last_used"] = now; s["rpd_used"] += 1
#         s["rpm_log"].append(now)
#         s["consecutive_errors"] = 0  # Reset on success
#         if token_count > 0:
#             s["tpm_log"].append((now, token_count))
#             s["tpd_used"] += token_count
#             s["total_tokens"] += token_count
#         if model:
#             mu = s["model_usage"].setdefault(model, {"requests": 0, "tokens": 0})
#             mu["requests"] += 1; mu["tokens"] += token_count
#         if headers:
#             _ingest_headers(s, headers, now)
# 
# 
# def _ingest_headers(s: Dict, headers: dict, now: float) -> None:
#     try:
#         h = {k.lower(): v for k, v in headers.items()}
#         rem_tok = h.get("x-ratelimit-remaining-tokens")
#         rem_req = h.get("x-ratelimit-remaining-requests")
#         reset_tok = h.get("x-ratelimit-reset-tokens", "")
# 
#         if rem_tok is not None:
#             try:
#                 s["hdr_remaining_tokens"] = int(rem_tok)
#                 s["hdr_freshness"] = now
#             except (ValueError, TypeError): pass
# 
#         if rem_req is not None:
#             try: s["hdr_remaining_requests"] = int(rem_req)
#             except (ValueError, TypeError): pass
# 
#         if reset_tok:
#             try:
#                 secs = 0.0
#                 rt = str(reset_tok).strip().rstrip("s")
#                 if "m" in rt:
#                     parts = rt.split("m")
#                     secs = float(parts[0]) * 60 + float(parts[1] or 0)
#                 else:
#                     secs = float(rt) if rt else 0.0
#                 if secs > 0:
#                     s["hdr_freshness"] = now  # Mark headers as fresh
#             except (ValueError, TypeError): pass
#     except Exception: pass
# 
# 
# def mark_rate_limited(key: str, retry_after: Optional[float] = None) -> None:
#     now = time.time()
#     cooldown = (retry_after + 2.0) if (retry_after and retry_after > 0) else HARD_COOLDOWN_BASE
#     with _lock:
#         if key not in _state: return
#         s = _state[key]
#         s["errors"] += 1; s["rate_limit_hits"] += 1
#         s["consecutive_errors"] = min(s.get("consecutive_errors", 0) + 1, 10)
#         s["last_error"] = now; s["cooldown_until"] = now + cooldown
#         s["rpm_log"].clear(); s["tpm_log"].clear()
#         s["hdr_remaining_tokens"] = 0; s["hdr_remaining_requests"] = 0
#         s["hdr_freshness"] = now
# 
# 
# def mark_invalid(key: str) -> None:
#     now = time.time()
#     with _lock:
#         if key not in _state: return
#         s = _state[key]
#         s["errors"] += 1; s["consecutive_errors"] = 99
#         s["last_error"] = now; s["cooldown_until"] = now + DEAD_KEY_SECONDS
# 
# 
# def mark_error(key: str) -> None:
#     now = time.time()
#     with _lock:
#         if key not in _state: return
#         s = _state[key]
#         s["errors"] += 1
#         s["consecutive_errors"] = min(s.get("consecutive_errors", 0) + 1, 10)
#         s["last_error"] = now
#         penalty = min(5.0 * s["consecutive_errors"], 50.0)
#         s["cooldown_until"] = max(s["cooldown_until"], now + penalty)
# 
# 
# def reset_all_cooldowns() -> None:
#     with _lock:
#         for k in _RAW_KEYS:
#             s = _state[k]
#             s["cooldown_until"] = 0.0; s["rpm_log"].clear(); s["tpm_log"].clear()
#             s["hdr_remaining_tokens"] = _FLOOR_TPM; s["hdr_remaining_requests"] = _FLOOR_RPD
#             s["hdr_freshness"] = 0.0; s["consecutive_errors"] = 0
# 
# 
# def reset_key_cooldown(key: str) -> bool:
#     with _lock:
#         if key not in _state: return False
#         s = _state[key]
#         s["cooldown_until"] = 0.0; s["rpm_log"].clear(); s["tpm_log"].clear()
#         s["consecutive_errors"] = 0
#         s["hdr_remaining_tokens"] = _FLOOR_TPM; s["hdr_remaining_requests"] = _FLOOR_RPD
#         return True
# 
# 
# def total_keys() -> int: return len(_RAW_KEYS)
# 
# def available_keys_count() -> int:
#     now = time.time()
#     with _lock: return sum(1 for k in _RAW_KEYS if _is_available(k, now))
# 
# def seconds_until_available(key: str) -> float:
#     with _lock: return max(0.0, _state.get(key, {}).get("cooldown_until", 0) - time.time())
# 
# def get_total_capacity() -> dict:
#     now = time.time()
#     avail = 0; rpm_used = tpm_used = rpd_used = tpd_used = 0
#     with _lock:
#         for k in _RAW_KEYS:
#             s = _state[k]; _daily_reset(s, now)
#             rpm_used += _rpm_in_window(s, now); tpm_used += _tpm_in_window(s, now)
#             rpd_used += s["rpd_used"]; tpd_used += s["tpd_used"]
#             if _is_available(k, now): avail += 1
#     n = len(_RAW_KEYS)
#     return {"keys_total": n, "keys_available": avail, "keys_cooling": n - avail,
#             "rpm_used": rpm_used, "rpm_capacity": n * _FLOOR_RPM,
#             "tpm_used": tpm_used, "tpm_capacity": n * _FLOOR_TPM,
#             "rpd_used": rpd_used, "rpd_capacity": n * _FLOOR_RPD,
#             "tpd_used": tpd_used, "tpd_capacity": n * _FLOOR_TPD}
# 
# def status_table() -> list[dict]:
#     now = time.time()
#     rows = []
#     with _lock:
#         for i, k in enumerate(_RAW_KEYS, 1):
#             s = _state[k]; _daily_reset(s, now)
#             score = _headroom_score(k, now); cd = s["cooldown_until"]
#             if cd > now:
#                 rem = cd - now
#                 status = f"⛔ dead {rem/3600:.1f}h" if rem > 3600 else f"⏳ cooldown {rem:.0f}s"
#             elif score == 0: status = "🔴 pre-limit"
#             elif score > 0.7: status = f"🟢 {score*100:.0f}%"
#             elif score > 0.35: status = f"🟡 {score*100:.0f}%"
#             else: status = f"🟠 {score*100:.0f}%"
#             rows.append({
#                 "key": f"#{i} …{k[-4:]}", "status": status, "score": round(score, 3),
#                 "rpm": f"{_rpm_in_window(s,now)}/{_FLOOR_RPM}",
#                 "tpm": f"{_tpm_in_window(s,now):,}/{_FLOOR_TPM:,}",
#                 "rpd": f"{s['rpd_used']:,}/{_FLOOR_RPD:,}",
#                 "uses": s["uses"], "errors": s["errors"],
#                 "rl_hits": s["rate_limit_hits"],
#                 "total_tokens": f"{s['total_tokens']:,}",
#             })
#     return rows