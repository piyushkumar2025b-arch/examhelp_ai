"""
share_addon.py — Real QR Share UI
Tabs: Share Text · Share Image · Share QR Code · Share Chat · Share Any URL
"""
import streamlit as st
import streamlit.components.v1 as components

_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Mono&family=Orbitron:wght@700&display=swap');

.sh-hero {
    background: linear-gradient(135deg,#020617 0%,#0f172a 60%,#1a0030 100%);
    border: 1px solid rgba(99,102,241,.25);
    border-radius: 22px; padding: 28px 36px; margin-bottom: 22px;
    position: relative; overflow: hidden;
}
.sh-hero::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(ellipse 70% 80% at 90% 10%,rgba(99,102,241,.12),transparent 60%),
                radial-gradient(ellipse 50% 60% at 5% 90%,rgba(139,92,246,.08),transparent 60%);
    pointer-events:none;
}
.sh-title {
    font-family:'Orbitron',monospace; font-size:clamp(16px,3vw,28px); font-weight:700;
    background:linear-gradient(90deg,#fff,#a5b4fc 60%,#c084fc);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; margin-bottom:4px;
}
.sh-sub { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px;
    color:rgba(255,255,255,.3); text-transform:uppercase; }
.sh-badge { display:inline-flex; align-items:center; gap:6px;
    background:rgba(99,102,241,.1); border:1px solid rgba(99,102,241,.3);
    border-radius:100px; padding:3px 12px; font-size:9px; letter-spacing:2px;
    font-family:'Space Mono',monospace; color:#a5b4fc; }

.sh-result {
    background:rgba(15,23,42,.9); border:1px solid rgba(99,102,241,.2);
    border-radius:16px; padding:22px; margin-top:16px;
}
.sh-url-box {
    background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08);
    border-radius:10px; padding:10px 14px; font-family:'Space Mono',monospace;
    font-size:.75rem; color:#a5b4fc; word-break:break-all; margin:8px 0;
}
.sh-label { font-size:.7rem; letter-spacing:2px; font-family:'Space Mono',monospace;
    color:rgba(255,255,255,.3); text-transform:uppercase; margin-bottom:3px; }
.sh-success { color:#34d399; font-size:.85rem; font-weight:600; margin-bottom:10px; }
.sh-error   { color:#f87171; font-size:.85rem; }
</style>"""


def _show_result(result: dict, label: str = "Shared"):
    """Render the share result panel with QR, URL and copy button."""
    if not result.get("success"):
        st.error(f"❌ Share failed: {result.get('error','Unknown error')}")
        return

    st.markdown('<div class="sh-result">', unsafe_allow_html=True)
    st.markdown(f'<div class="sh-success">✅ {label} successfully!</div>', unsafe_allow_html=True)

    col_qr, col_info = st.columns([1, 2])

    with col_qr:
        qr = result.get("qr_bytes")
        if qr:
            st.image(qr, caption="Scan to open", use_container_width=True)
            st.download_button("⬇️ Download QR", qr, "share_qr.png",
                               mime="image/png", use_container_width=True, key=f"sh_dl_qr_{label}")
        else:
            st.markdown("⚠️ QR generation failed.")

    with col_info:
        short = result.get("short_url","")
        raw   = result.get("url","")

        st.markdown('<div class="sh-label">Short Link</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sh-url-box">{short}</div>', unsafe_allow_html=True)

        if short != raw:
            st.markdown('<div class="sh-label">Full Upload URL</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sh-url-box">{raw}</div>', unsafe_allow_html=True)

        st.link_button("🔗 Open Link", short or raw, use_container_width=True)

        # Copy-to-clipboard via JS
        components.html(f"""
<button onclick="navigator.clipboard.writeText('{short or raw}');this.textContent='✅ Copied!';"
  style="width:100%;padding:8px 12px;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);
  border-radius:8px;color:#a5b4fc;font-family:Space Mono,monospace;font-size:11px;cursor:pointer;
  transition:.2s;" onmouseout="this.textContent='📋 Copy Link'">📋 Copy Link</button>
""", height=48)

    st.markdown("</div>", unsafe_allow_html=True)


def render_share_center():
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown("""
<div class="sh-hero">
  <div class="sh-badge">🔗 &nbsp;REAL QR SHARING &nbsp;·&nbsp; NO LOGIN NEEDED</div>
  <div class="sh-title">📤 Share & QR Center</div>
  <div class="sh-sub">Upload · Shorten · Generate QR · Share Anything</div>
</div>""", unsafe_allow_html=True)

    try:
        from share_engine import (share_text, share_image, share_qr_image,
                                  share_chat, share_url_direct)
    except ImportError as e:
        st.error(f"share_engine not found: {e}"); return

    tab_text, tab_img, tab_qr, tab_chat, tab_url = st.tabs([
        "📝 Share Text",
        "🖼️ Share Image",
        "📲 Share QR Code",
        "💬 Share Chat",
        "🔗 Share URL",
    ])

    # ── Tab 1: Share Text ─────────────────────────────────────────────────────
    with tab_text:
        st.markdown("**📝 Share any text — paste notes, summaries, essays**")
        title = st.text_input("Title:", value="My Note", key="sh_txt_title")
        text  = st.text_area("Text content:", height=200, key="sh_txt_body",
                             placeholder="Paste your text, notes, study summary…")
        if st.button("📤 Upload & Generate QR", type="primary", use_container_width=True, key="sh_txt_go"):
            if not text.strip():
                st.warning("Enter some text first.")
            else:
                with st.spinner("Uploading & generating QR…"):
                    result = share_text(text, title=title)
                _show_result(result, "Text shared")

    # ── Tab 2: Share Image ────────────────────────────────────────────────────
    with tab_img:
        st.markdown("**🖼️ Share any image — get a real link + scannable QR**")
        img_file = st.file_uploader("Upload image:", type=["png","jpg","jpeg","gif","webp","svg"],
                                    key="sh_img_file")
        if img_file:
            st.image(img_file, width=280)
            if st.button("📤 Upload & Generate QR", type="primary", use_container_width=True, key="sh_img_go"):
                with st.spinner("Uploading image…"):
                    result = share_image(img_file.read(), filename=img_file.name)
                _show_result(result, "Image shared")

    # ── Tab 3: Share QR Code ──────────────────────────────────────────────────
    with tab_qr:
        st.markdown("**📲 Generate a QR from anything and share it as a real URL**")

        qr_type = st.selectbox("QR content type:", ["URL / Link","Plain Text","Phone Number","WiFi","Email"], key="sh_qr_type")
        qr_data = ""

        if qr_type == "URL / Link":
            qr_data = st.text_input("Enter URL:", placeholder="https://example.com", key="sh_qr_url")
        elif qr_type == "Plain Text":
            qr_data = st.text_area("Enter text:", key="sh_qr_text", height=100)
        elif qr_type == "Phone Number":
            ph = st.text_input("Phone:", placeholder="+91 9999999999", key="sh_qr_ph")
            qr_data = f"tel:{ph}" if ph else ""
        elif qr_type == "WiFi":
            wc1, wc2 = st.columns(2)
            ssid = wc1.text_input("SSID:", key="sh_qr_ssid")
            pwd  = wc2.text_input("Password:", type="password", key="sh_qr_pwd")
            sec  = st.selectbox("Security:", ["WPA","WEP","nopass"], key="sh_qr_sec")
            qr_data = f"WIFI:T:{sec};S:{ssid};P:{pwd};;" if ssid else ""
        elif qr_type == "Email":
            em_to  = st.text_input("To:", key="sh_qr_em")
            em_sub = st.text_input("Subject:", key="sh_qr_sub")
            qr_data = f"mailto:{em_to}?subject={em_sub}" if em_to else ""

        theme = st.selectbox("QR Theme:", ["Deep Space","Midnight Blue","Purple Haze","Forest","Gold & Black","Classic"], key="sh_qr_theme")

        if st.button("🔲 Generate QR & Share", type="primary", use_container_width=True, key="sh_qr_go"):
            if not qr_data.strip():
                st.warning("Enter content first.")
            else:
                with st.spinner("Generating QR & uploading…"):
                    from qr_engine import generate_url_qr, generate_text_qr
                    try:
                        from qr_engine import _get_qr, QR_THEMES
                        t = QR_THEMES.get(theme, QR_THEMES["Classic"])
                        qr_bytes = _get_qr(qr_data, fill_color=t["fill"], back_color=t["back"])
                    except Exception:
                        qr_bytes = None

                    if qr_bytes:
                        # Show QR preview immediately
                        st.image(qr_bytes, caption="Your QR Code", width=260)
                        st.download_button("⬇️ Download QR PNG", qr_bytes, "qr_code.png",
                                           key="sh_qr_dl_local", use_container_width=True)
                        # Also upload so it's shareable
                        result = share_qr_image(qr_bytes, label=qr_type.replace(" / ","_"))
                        _show_result(result, "QR Image shared")
                    else:
                        st.error("QR generation failed. Check your inputs.")

    # ── Tab 4: Share Chat ─────────────────────────────────────────────────────
    with tab_chat:
        st.markdown("**💬 Share your current ExamHelp AI chat as a readable page**")

        chat = st.session_state.get("messages", [])
        if not chat:
            st.info("💬 No chat messages yet. Start a conversation first, then come back to share it.")
        else:
            st.success(f"**{len(chat)}** messages ready to share")

            # Preview last 3
            st.markdown("**Preview (last 3 messages):**")
            for msg in chat[-3:]:
                role = "🧑 You" if msg["role"] == "user" else "🎓 AI"
                st.markdown(f'**{role}:** {msg["content"][:120]}…' if len(msg["content"]) > 120 else f'**{role}:** {msg["content"]}')

            if st.button("📤 Upload Chat & Generate QR", type="primary", use_container_width=True, key="sh_chat_go"):
                with st.spinner("Uploading chat history…"):
                    result = share_chat(chat, title="ExamHelp AI Conversation")
                _show_result(result, "Chat shared")

    # ── Tab 5: Share URL ──────────────────────────────────────────────────────
    with tab_url:
        st.markdown("**🔗 Shorten any URL and get an instant QR code**")

        url_input = st.text_input("Enter any URL:", placeholder="https://your-long-url.com/path/...", key="sh_url_input")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⚡ Shorten + QR", type="primary", use_container_width=True, key="sh_url_go"):
                if not url_input.strip():
                    st.warning("Enter a URL first.")
                elif not url_input.startswith(("http://","https://")):
                    st.warning("URL must start with http:// or https://")
                else:
                    with st.spinner("Shortening URL…"):
                        result = share_url_direct(url_input)
                    _show_result(result, "URL shortened")
        with c2:
            # Quick share of the current app's URL (if deployed)
            app_url = st.session_state.get("_app_url", "")
            if st.button("📱 Share This App's URL", use_container_width=True, key="sh_app_url"):
                st.info("Copy your Streamlit Cloud or deployment URL and paste it above to generate a QR.")
