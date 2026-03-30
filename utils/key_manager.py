from utils.gemini_key_manager import status as _gkm_status, get_key

def get_total_capacity() -> dict:
    from utils.ai_engine import get_pool_status
    s = get_pool_status()
    total   = s.get("total", 0)
    avail   = s.get("available", 0)
    rpm_cap = s.get("gemini_rpm", total * 15)
    rpd_cap = s.get("gemini_rpd", total * 1500)
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
    return [
        {"key": f"Key pool ({s['total']} keys)",
         "status": f"🟢 {s['available']} active, {s['cooling_down']} cooling"},
    ]

def reset_all_cooldowns() -> None:
    from utils.ai_engine import reset_all_keys
    reset_all_keys()