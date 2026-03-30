"""
key_manager.py — thin compatibility shim
=========================================
Previously managed Groq + Gemini keys. Groq is removed.
Delegates everything to gemini_key_manager / ai_engine.
"""

from utils.gemini_key_manager import status as _gkm_status, get_key

def get_total_capacity() -> str:
    from utils.ai_engine import get_capacity_summary
    return get_capacity_summary()

def status_table() -> list:
    s = _gkm_status()
    return [
        {"Provider": "Gemini", "Total": s["total"],
         "Available": s["available"], "Cooling": s["cooling_down"]},
    ]

def reset_all_cooldowns() -> None:
    from utils.ai_engine import reset_all_keys
    reset_all_keys()
