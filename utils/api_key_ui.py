"""
utils/api_key_ui.py — API Key UI + Live Usage Monitor (ExamHelp AI)
Preserves all original functions: render_api_key_section(), api_key_required()
ADDS:
  - render_api_status_bar() — real-time compact usage panel for sidebar
  - Usage tracking hooks: track_api_call(), track_api_error()
"""
from __future__ import annotations
import streamlit as st
import time
from utils.user_key_store import set_user_key, get_user_key, clear_user_key, has_key, detect_provider

# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL PROVIDER META  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
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

# Free-tier daily request limits per provider
_DAILY_LIMITS = {
    "gemini":   1500,
    "groq":     14400,
    "cerebras": 30000,
}


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL FUNCTIONS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def render_api_key_section() -> None:
    """Render the full API key management section inside the Streamlit sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 API Key")

    key, provider = get_user_key()

    if key and provider:
        meta  = _PROVIDER_META.get(provider, {})
        icon  = meta.get("icon", "🔑")
        label = meta.get("label", provider.title())
        model = meta.get("model", "")
        color = meta.get("color", "#2ecc71")

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

        with st.sidebar.expander("Where to get a free key?", expanded=False):
            for prov, meta in _PROVIDER_META.items():
                st.markdown(
                    f"**{meta['icon']} {meta['label']}** — prefix `{meta['prefix']}`  \n"
                    f"{meta['hint']}"
                )


def api_key_required(func):
    """Decorator: wrap a Streamlit page function. Shows gate if no key."""
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


# ─────────────────────────────────────────────────────────────────────────────
# NEW: USAGE TRACKING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _init_usage():
    if "api_usage" not in st.session_state:
        st.session_state.api_usage = {
            "calls":       0,
            "tokens_est":  0,
            "errors":      0,
            "last_call":   None,
            "last_update": time.time(),
            "session_start": time.time(),
        }


def track_api_call(prompt: str = "", response: str = ""):
    """Call this after every successful AI generation to update usage stats."""
    _init_usage()
    tokens = len(prompt.split()) + int(len(response.split()) * 1.3)
    u = st.session_state.api_usage
    u["calls"]      += 1
    u["tokens_est"] += tokens
    u["last_call"]   = time.time()
    u["last_update"] = time.time()


def track_api_error():
    """Call this when an API call fails (quota/error)."""
    _init_usage()
    st.session_state.api_usage["errors"]      += 1
    st.session_state.api_usage["last_update"]  = time.time()


# ─────────────────────────────────────────────────────────────────────────────
# NEW: LIVE API STATUS BAR
# ─────────────────────────────────────────────────────────────────────────────

def render_api_status_bar() -> None:
    """
    Compact real-time API usage monitor for the sidebar.
    Shows: provider, call count, token estimate, error count, usage bar.
    """
    _init_usage()
    key, provider = get_user_key()
    usage = st.session_state.api_usage

    st.sidebar.markdown("""
<style>
@keyframes _pulse_dot {
  0%,100%{opacity:1;transform:scale(1)}
  50%{opacity:.4;transform:scale(1.3)}
}
._live_dot{display:inline-block;width:8px;height:8px;background:#22c55e;
border-radius:50%;animation:_pulse_dot 1.5s infinite;margin-right:6px;vertical-align:middle;}
._api_bar_wrap{background:rgba(15,23,42,0.8);border:1px solid rgba(255,255,255,0.07);
border-radius:12px;padding:12px 14px;margin-bottom:6px;}
._usage_track{background:#1e293b;border-radius:100px;height:4px;width:100%;margin:4px 0;}
._usage_fill{height:4px;border-radius:100px;transition:width .3s;}
</style>
""", unsafe_allow_html=True)

    # Header
    st.sidebar.markdown(
        '<div style="font-size:.78rem;font-weight:700;color:#f8fafc;margin-bottom:6px;">'
        '<span class="_live_dot"></span>⚡ API Status</div>',
        unsafe_allow_html=True
    )

    if not key or not provider:
        st.sidebar.markdown(
            '<div class="_api_bar_wrap" style="color:#64748b;font-size:.75rem;">'
            '⚫ No API key set</div>',
            unsafe_allow_html=True
        )
        return

    meta          = _PROVIDER_META.get(provider, {})
    color         = meta.get("color", "#6366f1")
    icon          = meta.get("icon", "🔑")
    label         = meta.get("label", provider.title())
    daily_limit   = _DAILY_LIMITS.get(provider, 1500)
    calls         = usage.get("calls", 0)
    tokens        = usage.get("tokens_est", 0)
    errors        = usage.get("errors", 0)
    last_call     = usage.get("last_call")
    session_start = usage.get("session_start", time.time())

    pct           = min(100, int(calls / daily_limit * 100))
    bar_color     = "#22c55e" if pct < 60 else "#f59e0b" if pct < 85 else "#ef4444"
    status_label  = "🟢 Active" if calls > 0 else "🟡 Standby"
    if pct >= 95:
        status_label = "🔴 Near Limit"

    # Last call time
    if last_call:
        secs_ago = int(time.time() - last_call)
        if secs_ago < 60:   time_str = f"{secs_ago}s ago"
        elif secs_ago < 3600: time_str = f"{secs_ago//60}m ago"
        else:                time_str = f"{secs_ago//3600}h ago"
        last_str = f"Last call: {time_str}"
    else:
        last_str = "No calls yet this session"

    key_masked = f"…{key[-4:]}" if key and len(key) >= 4 else "…"

    # Session duration
    session_mins = int((time.time() - session_start) / 60)

    st.sidebar.markdown(f"""
<div class="_api_bar_wrap">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span style="color:{color};font-weight:700;font-size:.78rem;">{icon} {label}</span>
    <span style="font-size:.68rem;background:{color}22;color:{color};
    border-radius:100px;padding:1px 8px;">{status_label}</span>
  </div>
  <div style="font-size:.68rem;color:#64748b;margin-bottom:2px;">Key: {key_masked}</div>
  <div class="_usage_track">
    <div class="_usage_fill" style="width:{pct}%;background:{bar_color};"></div>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:.67rem;color:#64748b;margin-top:2px;">
    <span>{calls} calls ({pct}% of {daily_limit:,}/day)</span>
    <span>~{tokens:,} tokens</span>
  </div>
  {f'<div style="font-size:.67rem;color:#ef4444;margin-top:3px;">⚠️ {errors} error(s)</div>' if errors > 0 else ''}
  <div style="font-size:.65rem;color:#475569;margin-top:4px;">{last_str}</div>
</div>
""", unsafe_allow_html=True)

    # Summary row
    st.sidebar.markdown(f"""
<div style="font-size:.67rem;color:#64748b;padding:2px 4px 6px;">
  Session: {session_mins}m · Tokens: ~{tokens:,} · Errors: {errors}
</div>
""", unsafe_allow_html=True)

    # Refresh button
    col_r, col_rst = st.sidebar.columns(2)
    with col_r:
        if st.button("🔄", key="api_status_refresh", use_container_width=True,
                     help="Refresh status"):
            st.session_state.api_usage["last_update"] = time.time()
            st.rerun()
    with col_rst:
        if st.button("↺ Reset", key="api_status_reset", use_container_width=True,
                     help="Reset usage counters"):
            _init_usage()
            st.session_state.api_usage.update({
                "calls": 0, "tokens_est": 0, "errors": 0,
                "last_call": None, "session_start": time.time()
            })
            st.rerun()

    # Last updated
    lu = usage.get("last_update", time.time())
    secs_since = int(time.time() - lu)
    st.sidebar.caption(f"Updated {secs_since}s ago")
    st.sidebar.markdown("---")
