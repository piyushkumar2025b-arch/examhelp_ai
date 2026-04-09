"""
user_key_store.py — User-Provided API Key Manager
===================================================
Single-key model: the user pastes ONE API key (Gemini, Groq, or Cerebras).
The system auto-detects which provider the key belongs to and routes
all AI calls through that provider.

Key detection heuristics
  Gemini  : starts with "AIzaSy"
  Groq    : starts with "gsk_"
  Cerebras: starts with "csk-"   (Cerebras API keys begin with csk-)

Storage
  Keys are stored ONLY in st.session_state["_user_api_key"] at runtime.
  They are NEVER written to disk, env vars, or st.secrets.
  Users can clear the key at any time.

Public API
  set_user_key(raw)   → stores key + detected provider; raises ValueError on unknown
  get_user_key()      → returns (key, provider) or (None, None)
  clear_user_key()    → wipes key from session
  detect_provider(raw)→ returns "gemini" | "groq" | "cerebras" | None
  has_key()           → True if a valid key is currently set
"""

from __future__ import annotations
import streamlit as st
from typing import Optional, Tuple


# ── Provider detection ────────────────────────────────────────────────────────

def detect_provider(raw: str) -> Optional[str]:
    """
    Inspect the key prefix and return the provider name, or None if unknown.
    """
    key = raw.strip()
    if key.startswith("AIzaSy"):
        return "gemini"
    if key.startswith("gsk_"):
        return "groq"
    if key.startswith("csk-"):
        return "cerebras"
    return None


# ── Session-state helpers ─────────────────────────────────────────────────────

_KEY_SS   = "_user_api_key"
_PROV_SS  = "_user_api_provider"


def set_user_key(raw: str) -> str:
    """
    Store a user-supplied API key after auto-detecting its provider.
    Returns the detected provider name ("gemini", "groq", "cerebras").
    Raises ValueError if the key format is unrecognised.
    """
    key = raw.strip()
    provider = detect_provider(key)
    if provider is None:
        raise ValueError(
            "Unrecognised API key format.\n"
            "• Gemini keys start with  AIzaSy…\n"
            "• Groq keys start with    gsk_…\n"
            "• Cerebras keys start with csk-…"
        )
    st.session_state[_KEY_SS]  = key
    st.session_state[_PROV_SS] = provider
    return provider


def get_user_key() -> Tuple[Optional[str], Optional[str]]:
    """Return (api_key, provider) or (None, None) if nothing is set."""
    key  = st.session_state.get(_KEY_SS)
    prov = st.session_state.get(_PROV_SS)
    if key and prov:
        return key, prov
    return None, None


def clear_user_key() -> None:
    """Remove the stored key and provider from session."""
    st.session_state.pop(_KEY_SS,  None)
    st.session_state.pop(_PROV_SS, None)


def has_key() -> bool:
    """True if the user has entered a valid key this session."""
    key, _ = get_user_key()
    return bool(key)
