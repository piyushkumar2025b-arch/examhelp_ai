"""
utils/api_key_ui.py — Multi-Provider API Key UI v2.0 (ExamHelp AI)
===================================================================
Supports 18 providers with beautiful cards, multi-key management,
live usage monitoring, and quick-connect buttons.

Public API:
  render_api_key_section()   → sidebar key management
  render_api_status_bar()    → compact live usage bar
  render_multi_key_manager() → full multi-provider key panel
  api_key_required(func)     → decorator
  track_api_call(...)        → usage tracking hook
  track_api_error()          → error tracking hook
"""
from __future__ import annotations
import streamlit as st
import time
from utils.user_key_store import (
    set_user_key, get_user_key, clear_user_key, has_key,
    detect_provider, PROVIDER_REGISTRY,
    set_multi_keys, get_all_stored_keys, set_primary_provider,
    get_key_for_provider,
)

# ── Provider groups for display ───────────────────────────────────────────────

_FREE_PROVIDERS = [
    ("gemini",      "✨ Google Gemini",    "AIzaSy…",      "#4285f4", "aistudio.google.com — Free 1500 req/day"),
    ("groq",        "⚡ Groq",            "gsk_…",         "#f55036", "console.groq.com — Free 14,400 req/day"),
    ("cerebras",    "🚀 Cerebras",        "csk-…",         "#ff6b35", "cloud.cerebras.ai — Free 30K req/day"),
    ("openrouter",  "🔀 OpenRouter",      "sk-or-…",       "#8b5cf6", "openrouter.ai — Free models available"),
    ("huggingface", "🤗 HuggingFace",     "hf_…",          "#ff9d00", "huggingface.co — Free Inference API"),
    ("fireworks",   "🎆 Fireworks AI",    "fw_…",          "#ef4444", "fireworks.ai — Free tier"),
    ("cohere",      "🧠 Cohere",          "co_…",          "#39a7a3", "dashboard.cohere.com — Free trial"),
    ("sambanova",   "🧬 SambaNova",       "samba_…",       "#e11d48", "cloud.sambanova.ai — Free"),
    ("nvidia",      "🟢 NVIDIA NIM",      "nvapi-…",       "#76b900", "build.nvidia.com — Free tier"),
    ("ai21",        "💎 AI21 Labs",       "auto-detect",   "#7c3aed", "studio.ai21.com — Free trial"),
]

_PAID_PROVIDERS = [
    ("openai",      "🤖 OpenAI",          "sk-…",          "#10a37f", "platform.openai.com — Pay per token"),
    ("anthropic",   "🔮 Anthropic",       "sk-ant-…",      "#c96442", "console.anthropic.com — Pay per token"),
    ("mistral",     "🌬️ Mistral AI",      "manual",        "#ff7000", "console.mistral.ai — Pay per token"),
    ("together",    "🤝 Together AI",     "manual",        "#0ea5e9", "api.together.xyz — Pay per token"),
    ("perplexity",  "🔭 Perplexity",      "pplx-…",        "#20b2aa", "perplexity.ai — Pay per token"),
    ("deepseek",    "🔍 DeepSeek",        "manual",        "#2563eb", "platform.deepseek.com — Very cheap"),
    ("replicate",   "♾️ Replicate",        "r8_…",          "#f59e0b", "replicate.com — Pay per run"),
    ("xai",         "𝕏 xAI Grok",        "xai-…",         "#ffffff", "console.x.ai — Pay per token"),
]

_DAILY_LIMITS = {
    "gemini": 1500, "groq": 14400, "cerebras": 30000,
    "openrouter": 2000, "huggingface": 1000, "fireworks": 1000,
    "cohere": 1000, "sambanova": 1000, "nvidia": 1000, "ai21": 500,
    "openai": 9999, "anthropic": 9999, "mistral": 9999, "together": 9999,
    "perplexity": 9999, "deepseek": 9999, "replicate": 9999, "xai": 9999,
}


# ── Usage tracking ─────────────────────────────────────────────────────────────

def _init_usage():
    if "api_usage" not in st.session_state:
        st.session_state.api_usage = {
            "calls": 0, "tokens_est": 0, "errors": 0,
            "last_call": None, "last_update": time.time(),
            "session_start": time.time(),
        }


def track_api_call(prompt: str = "", response: str = ""):
    _init_usage()
    tokens = len(prompt.split()) + int(len(response.split()) * 1.3)
    u = st.session_state.api_usage
    u["calls"]      += 1
    u["tokens_est"] += tokens
    u["last_call"]   = time.time()
    u["last_update"] = time.time()


def track_api_error():
    _init_usage()
    st.session_state.api_usage["errors"]      += 1
    st.session_state.api_usage["last_update"]  = time.time()


# ── Primary sidebar key section ────────────────────────────────────────────────

def render_api_key_section() -> None:
    """Render the API key management section in the Streamlit sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 API Key")

    key, provider = get_user_key()

    if key and provider:
        meta  = PROVIDER_REGISTRY.get(provider, {})
        icon  = meta.get("icon", "🔑")
        label = meta.get("label", provider.title())
        model = meta.get("model", "")
        color = meta.get("color", "#6366f1")

        st.sidebar.markdown(
            f'<div style="background:{color}22;border:1px solid {color};'
            f'border-radius:10px;padding:10px 14px;margin-bottom:8px;">'
            f'<span style="color:{color};font-weight:bold;font-size:.9rem;">{icon} {label} Active</span><br>'
            f'<span style="font-size:.75rem;color:#94a3b8;">Model: {model}</span><br>'
            f'<span style="font-size:.72rem;color:#64748b;">Key: …{key[-6:]}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.sidebar.columns(2)
        with c1:
            if st.button("🗑 Remove", key="remove_api_key", use_container_width=True):
                clear_user_key()
                st.rerun()
        with c2:
            if st.button("🔄 Switch", key="switch_api_key", use_container_width=True,
                         help="Switch to a different stored provider"):
                st.session_state["_show_key_switcher"] = True

        # Provider switcher
        if st.session_state.get("_show_key_switcher"):
            stored = get_all_stored_keys()
            others = [k for k in stored if k["provider"] != provider]
            if others:
                st.sidebar.markdown("**Switch to:**")
                for k in others:
                    if st.sidebar.button(
                        f"{k['icon']} {k['label']} ({k['key_masked']})",
                        key=f"switch_to_{k['provider']}",
                        use_container_width=True,
                    ):
                        set_primary_provider(k["provider"])
                        st.session_state["_show_key_switcher"] = False
                        st.rerun()
            else:
                st.sidebar.caption("No other keys stored. Add via **Multi-Key Manager**.")
    else:
        _render_key_entry_form()

    # Multi-key count badge
    stored = get_all_stored_keys()
    if len(stored) > 1:
        st.sidebar.markdown(
            f'<div style="font-size:.72rem;color:#6366f1;text-align:center;margin-top:4px;">'
            f'🔐 {len(stored)} providers connected</div>',
            unsafe_allow_html=True,
        )


def _render_key_entry_form():
    """Compact key entry form for sidebar."""
    # Provider selector
    all_providers = list(PROVIDER_REGISTRY.keys())
    provider_labels = {p: f"{PROVIDER_REGISTRY[p]['icon']} {PROVIDER_REGISTRY[p]['label']}" for p in all_providers}

    selected_provider = st.sidebar.selectbox(
        "Provider",
        options=["auto-detect"] + all_providers,
        format_func=lambda p: "🔍 Auto-detect" if p == "auto-detect" else provider_labels.get(p, p),
        key="api_provider_select",
        label_visibility="collapsed",
    )

    with st.sidebar.form("api_key_form", clear_on_submit=True):
        provider_hint = None if selected_provider == "auto-detect" else selected_provider
        placeholder = "Paste your API key here…"
        if provider_hint and provider_hint in PROVIDER_REGISTRY:
            meta = PROVIDER_REGISTRY[provider_hint]
            prefixes = meta.get("prefix", [])
            if prefixes:
                placeholder = f"{prefixes[0]}…"

        raw = st.text_input(
            "API Key",
            type="password",
            placeholder=placeholder,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("✅ Connect", use_container_width=True, type="primary")

    if submitted and raw:
        try:
            prov_detected = set_user_key(raw, provider_hint=provider_hint)
            meta = PROVIDER_REGISTRY.get(prov_detected, {})
            st.sidebar.success(f"{meta.get('icon','🔑')} {meta.get('label', prov_detected)} connected!")
            st.rerun()
        except ValueError as e:
            st.sidebar.error(str(e))

    # Quick-link pills for free providers
    with st.sidebar.expander("🆓 Free API keys", expanded=False):
        for prov, label, prefix, color, hint in _FREE_PROVIDERS[:5]:
            st.markdown(
                f'<div style="font-size:.75rem;margin-bottom:4px;">'
                f'<span style="color:{color};font-weight:700;">{label}</span> — '
                f'<a href="https://{hint.split(" — ")[0]}" target="_blank" '
                f'style="color:{color};">{hint.split(" — ")[0]}</a><br>'
                f'<span style="color:#64748b;">{hint.split(" — ")[-1]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── API status bar ────────────────────────────────────────────────────────────

def render_api_status_bar() -> None:
    """Compact real-time API usage monitor for the sidebar."""
    _init_usage()
    key, provider = get_user_key()
    usage = st.session_state.api_usage

    st.sidebar.markdown("""
<style>
@keyframes _pulse_dot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.3)}}
._live_dot{display:inline-block;width:8px;height:8px;background:#22c55e;
border-radius:50%;animation:_pulse_dot 1.5s infinite;margin-right:6px;vertical-align:middle;}
._api_bar_wrap{background:rgba(15,23,42,0.8);border:1px solid rgba(255,255,255,0.07);
border-radius:12px;padding:12px 14px;margin-bottom:6px;}
._usage_track{background:#1e293b;border-radius:100px;height:4px;width:100%;margin:4px 0;}
._usage_fill{height:4px;border-radius:100px;transition:width .3s;}
</style>
""", unsafe_allow_html=True)

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

    meta          = PROVIDER_REGISTRY.get(provider, {})
    color         = meta.get("color", "#6366f1")
    icon          = meta.get("icon", "🔑")
    label         = meta.get("label", provider.title())
    daily_limit   = _DAILY_LIMITS.get(provider, 1500)
    calls         = usage.get("calls", 0)
    tokens        = usage.get("tokens_est", 0)
    errors        = usage.get("errors", 0)
    last_call     = usage.get("last_call")
    session_start = usage.get("session_start", time.time())

    pct           = min(100, int(calls / daily_limit * 100)) if daily_limit < 9000 else 0
    bar_color     = "#22c55e" if pct < 60 else "#f59e0b" if pct < 85 else "#ef4444"
    status_label  = "🟢 Active" if calls > 0 else "🟡 Standby"
    if pct >= 95:
        status_label = "🔴 Near Limit"

    if last_call:
        secs_ago = int(time.time() - last_call)
        if secs_ago < 60:   time_str = f"{secs_ago}s ago"
        elif secs_ago < 3600: time_str = f"{secs_ago//60}m ago"
        else:               time_str = f"{secs_ago//3600}h ago"
        last_str = f"Last call: {time_str}"
    else:
        last_str = "No calls yet this session"

    key_masked = f"…{key[-4:]}" if key and len(key) >= 4 else "…"
    session_mins = int((time.time() - session_start) / 60)
    limit_str = f"{daily_limit:,}/day" if daily_limit < 9000 else "unlimited"

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
    <span>{calls} calls ({pct}% of {limit_str})</span>
    <span>~{tokens:,} tokens</span>
  </div>
  {f'<div style="font-size:.67rem;color:#ef4444;margin-top:3px;">⚠️ {errors} error(s)</div>' if errors > 0 else ''}
  <div style="font-size:.65rem;color:#475569;margin-top:4px;">{last_str}</div>
</div>
""", unsafe_allow_html=True)

    col_r, col_rst = st.sidebar.columns(2)
    with col_r:
        if st.button("🔄", key="api_status_refresh", use_container_width=True, help="Refresh status"):
            st.rerun()
    with col_rst:
        if st.button("↺ Reset", key="api_status_reset", use_container_width=True, help="Reset counters"):
            _init_usage()
            st.session_state.api_usage.update({
                "calls": 0, "tokens_est": 0, "errors": 0,
                "last_call": None, "session_start": time.time()
            })
            st.rerun()

    lu = usage.get("last_update", time.time())
    st.sidebar.caption(f"Updated {int(time.time() - lu)}s ago · Session {session_mins}m")
    st.sidebar.markdown("---")


# ── Multi-key manager (full page panel) ──────────────────────────────────────

def render_multi_key_manager() -> None:
    """
    Full-page multi-provider API key manager.
    Shows all 18 providers in cards, lets user add/remove keys per-provider.
    """
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
.api-hub-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
    border-radius: 20px; padding: 24px 28px; margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(99,102,241,0.35);
}
.provider-card {
    background: rgba(15,23,42,0.6);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 16px;
    transition: all 0.2s; margin-bottom: 2px;
}
.provider-card:hover { border-color: rgba(99,102,241,0.4); }
.provider-card.active { border-color: var(--pc); box-shadow: 0 0 12px var(--pc-glow); }
</style>

<div class="api-hub-header">
  <div style="font-size:1.6rem;font-weight:800;color:#fff;letter-spacing:-0.5px;">
    🔌 API Connection Hub
  </div>
  <div style="color:rgba(255,255,255,0.6);font-size:.88rem;margin-top:4px;">
    Connect up to 18 AI providers · Switch between them instantly
  </div>
</div>
""", unsafe_allow_html=True)

    key, primary_provider = get_user_key()
    stored_keys = {k["provider"]: k for k in get_all_stored_keys()}

    # ── Free providers section ──────────────────────────────────────────────
    st.markdown("### 🆓 Free Providers")
    st.caption("These have free tiers — no credit card needed")

    cols = st.columns(2)
    for i, (prov, label, prefix, color, hint) in enumerate(_FREE_PROVIDERS):
        with cols[i % 2]:
            is_stored = prov in stored_keys
            is_primary = prov == primary_provider

            status_badge = ""
            if is_primary:
                status_badge = f'<span style="background:{color}33;color:{color};border-radius:6px;padding:2px 8px;font-size:.65rem;font-weight:700;">● PRIMARY</span>'
            elif is_stored:
                status_badge = '<span style="background:#22c55e22;color:#22c55e;border-radius:6px;padding:2px 8px;font-size:.65rem;font-weight:700;">✓ STORED</span>'

            st.markdown(f"""
<div style="background:rgba(15,23,42,0.8);border:1px solid {'rgba('+','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))+',0.4)' if is_stored else 'rgba(255,255,255,0.07)'};
border-radius:14px;padding:14px;margin-bottom:6px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <span style="color:{color};font-weight:700;font-size:.9rem;">{label}</span>
    {status_badge}
  </div>
  <div style="font-size:.72rem;color:#64748b;margin-bottom:4px;">Prefix: <code style="color:#94a3b8;">{prefix}</code></div>
  <div style="font-size:.7rem;color:#22c55e;">{hint}</div>
</div>
""", unsafe_allow_html=True)

            if is_stored and not is_primary:
                if st.button(f"Set as Primary", key=f"set_primary_{prov}", use_container_width=True):
                    set_primary_provider(prov)
                    st.rerun()
            elif not is_stored:
                new_key = st.text_input(
                    f"Key for {label}",
                    type="password",
                    placeholder=f"{prefix}…" if prefix != "manual" else "Paste API key…",
                    key=f"mk_input_{prov}",
                    label_visibility="collapsed",
                )
                if st.button(f"➕ Connect {label.split()[-1]}", key=f"mk_add_{prov}", use_container_width=True):
                    if new_key.strip():
                        try:
                            set_user_key(new_key.strip(), provider_hint=prov)
                            st.success(f"✅ {label} connected!")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
            else:
                st.caption(f"✅ Active primary · Key: …{stored_keys[prov]['key_masked']}")

    # ── Paid providers section ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💳 Premium Providers")
    st.caption("Pay-per-token — better quality, higher limits")

    cols2 = st.columns(2)
    for i, (prov, label, prefix, color, hint) in enumerate(_PAID_PROVIDERS):
        with cols2[i % 2]:
            is_stored = prov in stored_keys
            is_primary = prov == primary_provider

            status_badge = ""
            if is_primary:
                status_badge = f'<span style="background:{color}33;color:{color};border-radius:6px;padding:2px 8px;font-size:.65rem;font-weight:700;">● PRIMARY</span>'
            elif is_stored:
                status_badge = '<span style="background:#22c55e22;color:#22c55e;border-radius:6px;padding:2px 8px;font-size:.65rem;font-weight:700;">✓ STORED</span>'

            st.markdown(f"""
<div style="background:rgba(15,23,42,0.8);border:1px solid {'rgba(255,255,255,0.15)' if is_stored else 'rgba(255,255,255,0.06)'};
border-radius:14px;padding:14px;margin-bottom:6px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <span style="color:{color};font-weight:700;font-size:.9rem;">{label}</span>
    {status_badge}
  </div>
  <div style="font-size:.72rem;color:#64748b;margin-bottom:4px;">Prefix: <code style="color:#94a3b8;">{prefix}</code></div>
  <div style="font-size:.7rem;color:#f59e0b;">{hint}</div>
</div>
""", unsafe_allow_html=True)

            if is_stored and not is_primary:
                if st.button(f"Set as Primary", key=f"set_primary2_{prov}", use_container_width=True):
                    set_primary_provider(prov)
                    st.rerun()
            elif not is_stored:
                new_key = st.text_input(
                    f"Key for {label}",
                    type="password",
                    placeholder=f"{prefix}…" if prefix not in ("manual", "auto-detect") else "Paste API key…",
                    key=f"mk_input2_{prov}",
                    label_visibility="collapsed",
                )
                if st.button(f"➕ Connect {label.split()[-1]}", key=f"mk_add2_{prov}", use_container_width=True):
                    if new_key.strip():
                        try:
                            set_user_key(new_key.strip(), provider_hint=prov)
                            st.success(f"✅ {label} connected!")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
            else:
                st.caption(f"✅ Stored · Key: …{stored_keys[prov]['key_masked']}")

    # ── Connected summary ───────────────────────────────────────────────────
    st.markdown("---")
    all_stored = get_all_stored_keys()
    if all_stored:
        st.markdown(f"### ✅ {len(all_stored)} Provider(s) Connected")
        summary_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;">'
        for k in all_stored:
            prim_badge = " ★" if k["is_primary"] else ""
            summary_html += (
                f'<div style="background:{k["color"]}1a;border:1px solid {k["color"]};'
                f'border-radius:10px;padding:6px 12px;font-size:.78rem;">'
                f'<span style="color:{k["color"]};font-weight:700;">{k["icon"]} {k["label"]}{prim_badge}</span>'
                f'<br><span style="color:#64748b;font-size:.65rem;">{k["key_masked"]} · {k["model"]}</span>'
                f'</div>'
            )
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

        if st.button("🗑 Clear ALL stored keys", key="clear_all_keys"):
            from utils.user_key_store import clear_user_key, _MULTI_SS
            clear_user_key()
            st.session_state.pop(_MULTI_SS, None)
            st.rerun()
    else:
        st.info("No API keys connected yet. Add at least one provider above to start chatting.")


# ── Decorator ────────────────────────────────────────────────────────────────

def api_key_required(func):
    """Decorator: wrap a Streamlit page function. Shows gate if no key."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not has_key():
            st.warning(
                "**No API key set.**  \n"
                "Please enter your API key (Gemini / Groq / OpenAI / or any of 18 providers) "
                "in the **sidebar** to use this feature.",
                icon="🔑",
            )
            return
        return func(*args, **kwargs)

    return wrapper
