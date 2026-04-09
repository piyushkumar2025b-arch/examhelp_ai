"""
gemini_key_manager.py — Compatibility Shim (v2)
=================================================
The 9-key Gemini rotation engine has been retired.
This module is kept only for backward compatibility.
All logic delegates to user_key_store / ai_engine.
"""

from utils.user_key_store import get_user_key


def get_key():
    """Return the user's Gemini key, or None."""
    key, provider = get_user_key()
    if key and provider == "gemini":
        return key
    return None


def mark_rate_limited(key: str) -> None:
    """No-op: no per-key cooldown state in single-key mode."""
    pass


def status() -> dict:
    key = get_key()
    active = 1 if key else 0
    return {
        "total":        active,
        "available":    active,
        "cooling_down": 0,
    }
