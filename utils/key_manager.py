"""
key_manager.py — thin compatibility shim
=========================================
Previously managed Groq + Gemini keys. Groq is removed.
Delegates everything to gemini_key_manager / ai_engine.
"""

from utils.gemini_key_manager import status as _gkm_status, get_key

def get_total_capacity() -> dict:
    from utils.ai_engine import get_pool_status
    from utils.omnikey_engine import RPM_SAFE_LIMIT
    s = get_pool_status()
    total   = s.get("total_keys", s.get("total", 1))
    avail   = s.get("available", total)
    rpm_cap = RPM_SAFE_LIMIT * total
    rpd_cap = 1500 * total
    return {
        "keys_available":  avail,
        "keys_total":      total,
        "rpm_used":        0,
        "rpm_capacity":    rpm_cap,
        "tpm_used":        0,
        "tpm_capacity":    total * 1_000_000,
        "rpd_used":        0,
        "rpd_capacity":    rpd_cap,
    }

def status_table() -> list:
    s = _gkm_status()
    total = s.get("total_keys", s.get("total", 0))
    return [
        {"key": f"Key pool ({total} keys)",
         "status": f"🟢 {s['available']} active, {s['cooling_down']} cooling"},
    ]

def reset_all_cooldowns() -> None:
    from utils.ai_engine import reset_all_keys
    reset_all_keys()
