"""
api_key_ui.py — API Key Entry / Management UI
===============================================
Renders a sidebar section where the user can:
  1. Enter an API key (Gemini, Groq, or Cerebras — auto-detected)
  2. See which provider is active
  3. Remove the key at any time

Usage — call inside your sidebar block:
    from utils.api_key_ui import render_api_key_section
    render_api_key_section()

Provider hints shown to the user:
  Gemini   : key starts with  AIzaSy…  | Free tier: aistudio.google.com
  Groq     : key starts with  gsk_…    | Free tier: console.groq.com
  Cerebras : key starts with  csk-…    | Free tier: cloud.cerebras.ai
"""

from __future__ import annotations
import streamlit as st
from utils.user_key_store import set_user_key, get_user_key, clear_user_key, has_key, detect_provider

# Provider display metadata
_PROVIDER_META = {
    "gemini": {
        "label":  "Gemini (Google)",
        "icon":   "✨",
        "color":  "#4285f4",
        "model":  "gemini-2.5-flash",
        "hint":   "Get a free key at [aistudio.google.com](https://aistudio.google.com)",
        "prefix": "AIzaSy…",
    },
    "groq": {
        "label":  "Groq",
        "icon":   "⚡",
        "color":  "#f55036",
        "model":  "llama-3.1-8b-instant  (500K ctx · 14,400 RPD free)",
        "hint":   "Get a free key at [console.groq.com](https://console.groq.com)",
        "prefix": "gsk_…",
    },
    "cerebras": {
        "label":  "Cerebras",
        "icon":   "🚀",
        "color":  "#ff6b35",
        "model":  "llama3.1-8b  (1,800+ tok/s · ~80,000 WPM)",
        "hint":   "Get a free key at [cloud.cerebras.ai](https://cloud.cerebras.ai)",
        "prefix": "csk-…",
    },
}


def render_api_key_section() -> None:
    """
    Render the full API key management section inside the Streamlit sidebar.
    Call this from your sidebar block.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 API Key")

    key, provider = get_user_key()

    if key and provider:
        meta = _PROVIDER_META.get(provider, {})
        icon  = meta.get("icon", "🔑")
        label = meta.get("label", provider.title())
        model = meta.get("model", "")
        color = meta.get("color", "#2ecc71")

        # Active key badge
        st.sidebar.markdown(
            f'<div style="background:{color}22;border:1px solid {color};'
            f'border-radius:8px;padding:8px 12px;margin-bottom:8px;">'
            f'<span style="color:{color};font-weight:bold;">{icon} {label} Active</span><br>'
            f'<span style="font-size:11px;color:#aaa;">Model: {model}</span><br>'
            f'<span style="font-size:11px;color:#888;">Key: …{key[-6:]}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

        if st.sidebar.button("🗑 Remove Key", key="remove_api_key", use_container_width=True):
            clear_user_key()
            st.rerun()

    else:
        # Key entry form
        with st.sidebar.form("api_key_form", clear_on_submit=True):
            raw = st.text_input(
                "Enter your API Key",
                type="password",
                placeholder="AIzaSy… / gsk_… / csk-…",
                help=(
                    "Paste any one key below:\n"
                    "• Gemini: starts with AIzaSy (aistudio.google.com)\n"
                    "• Groq: starts with gsk_ (console.groq.com)\n"
                    "• Cerebras: starts with csk- (cloud.cerebras.ai)"
                ),
            )
            submitted = st.form_submit_button("✅ Save Key", use_container_width=True)

        if submitted and raw:
            try:
                provider_detected = set_user_key(raw)
                meta = _PROVIDER_META.get(provider_detected, {})
                st.sidebar.success(
                    f"{meta.get('icon','🔑')} {meta.get('label', provider_detected.title())} key saved!"
                )
                st.rerun()
            except ValueError as e:
                st.sidebar.error(str(e))

        # Provider hints
        with st.sidebar.expander("Where to get a free key?", expanded=False):
            for prov, meta in _PROVIDER_META.items():
                st.markdown(
                    f"**{meta['icon']} {meta['label']}** — prefix `{meta['prefix']}`  \n"
                    f"{meta['hint']}"
                )


def api_key_required(func):
    """
    Decorator: wrap a Streamlit page function.
    Shows a friendly gate if no key is set; otherwise calls the function.

    Usage:
        @api_key_required
        def my_page():
            ...
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not has_key():
            st.warning(
                "**No API key set.**  \n"
                "Please enter your API key (Gemini / Groq / Cerebras) "
                "in the **sidebar** to use this feature.",
                icon="🔑",
            )
            return
        return func(*args, **kwargs)

    return wrapper
