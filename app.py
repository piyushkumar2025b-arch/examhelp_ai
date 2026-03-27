import streamlit as st
import os
import datetime
from dotenv import load_dotenv

from utils.groq_client import stream_chat_with_groq
from utils.pdf_handler import extract_text_from_pdf, get_pdf_metadata, get_pdf_summary_stats
from utils.youtube_handler import get_youtube_transcript, format_transcript_as_context, extract_video_id, get_transcript_stats
from utils.web_handler import scrape_web_page, format_web_context, get_web_stats
from utils import key_manager

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ExamHelp — AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Premium Editorial UI
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --bg:        #0a0a0b;
    --bg2:       #111113;
    --bg3:       #18181b;
    --border:    #27272a;
    --border2:   #3f3f46;
    --text:      #fafafa;
    --text2:     #a1a1aa;
    --text3:     #52525b;
    --accent:    #f97316;
    --accent2:   #ea580c;
    --accent-bg: rgba(249,115,22,0.08);
    --accent-bd: rgba(249,115,22,0.25);
    --green:     #4ade80;
    --green-bg:  rgba(74,222,128,0.08);
    --red:       #f87171;
    --blue:      #60a5fa;
    --serif:     'Instrument Serif', Georgia, serif;
    --sans:      'DM Sans', system-ui, sans-serif;
    --mono:      'JetBrains Mono', monospace;
  }

  /* ── Reset ── */
  html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
  }

  #MainMenu, footer, header { visibility: hidden; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background-color: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 0 !important;
  }
  [data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
  }
  [data-testid="stSidebar"] * { font-family: var(--sans) !important; }

  /* ── Main area ── */
  .main .block-container {
    padding-top: 0 !important;
    padding-bottom: 6rem !important;
    max-width: 860px !important;
    margin: 0 auto !important;
  }

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.15rem 0 !important;
  }

  /* ── Chat input ── */
  [data-testid="stChatInputContainer"] {
    background: linear-gradient(to top, var(--bg) 70%, transparent) !important;
    border-top: none !important;
    padding: 1rem 1.5rem 1.5rem !important;
    position: sticky !important;
    bottom: 0 !important;
    backdrop-filter: blur(12px) !important;
  }
  [data-testid="stChatInputContainer"] textarea {
    background-color: var(--bg3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.95rem !important;
    padding: 14px 18px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
  }
  [data-testid="stChatInputContainer"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-bg) !important;
  }
  [data-testid="stChatInputContainer"] textarea::placeholder {
    color: var(--text3) !important;
  }
  [data-testid="stChatInputContainer"] button {
    background-color: var(--accent) !important;
    border-radius: 10px !important;
    color: white !important;
    transition: background 0.2s !important;
  }
  [data-testid="stChatInputContainer"] button:hover {
    background-color: var(--accent2) !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    background-color: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text2) !important;
    border-radius: 10px !important;
    font-family: var(--sans) !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.9rem !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.01em !important;
  }
  .stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background-color: var(--accent-bg) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(249,115,22,0.12) !important;
  }

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {
    background-color: var(--bg3) !important;
    border: 1px dashed var(--border2) !important;
    border-radius: 12px !important;
    padding: 0.4rem !important;
    transition: border-color 0.2s !important;
  }
  [data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
  }

  /* ── Text input ── */
  [data-testid="stTextInput"] input {
    background-color: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s !important;
  }
  [data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-bg) !important;
  }
  [data-testid="stTextInput"] input::placeholder { color: var(--text3) !important; }

  /* ── Expander ── */
  [data-testid="stExpander"] {
    background-color: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
  }
  [data-testid="stExpander"] summary {
    font-size: 0.82rem !important;
    color: var(--text2) !important;
    font-weight: 500 !important;
  }

  /* ── Alert/info boxes ── */
  [data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: var(--sans) !important;
    font-size: 0.87rem !important;
  }

  /* ── Divider ── */
  hr { border-color: var(--border) !important; margin: 0.6rem 0 !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text3); }

  /* ── Code ── */
  code {
    background-color: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
    font-family: var(--mono) !important;
    font-size: 0.82em !important;
    padding: 2px 6px !important;
    color: var(--accent) !important;
  }

  /* ── Custom components ── */
  .eh-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 1.2rem 1rem 0.8rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.8rem;
  }
  .eh-logo-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(249,115,22,0.3);
  }
  .eh-logo-text { line-height: 1.2; }
  .eh-logo-title {
    font-size: 1.05rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.3px;
  }
  .eh-logo-sub { font-size: 0.72rem; color: var(--text3); }

  .section-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text3);
    margin: 1rem 0 0.45rem 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  .source-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--bg3);
    border: 1px solid var(--border2);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 0.75rem;
    color: var(--text2);
    font-family: var(--mono);
    margin: 2px 3px 2px 0;
    transition: border-color 0.15s;
  }
  .source-chip:hover { border-color: var(--accent); }
  .source-chip .chip-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    flex-shrink: 0;
  }

  .hero-wrap {
    text-align: center;
    padding: 4rem 2rem 2rem;
    animation: fadeUp 0.6s ease both;
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--accent-bg);
    border: 1px solid var(--accent-bd);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    color: var(--accent);
    font-weight: 500;
    letter-spacing: 0.03em;
    margin-bottom: 1.4rem;
  }
  .hero-title {
    font-family: var(--serif);
    font-size: 2.6rem;
    color: var(--text);
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin-bottom: 0.6rem;
  }
  .hero-title em { color: var(--accent); font-style: italic; }
  .hero-sub {
    font-size: 0.95rem;
    color: var(--text2);
    line-height: 1.6;
    max-width: 460px;
    margin: 0 auto 2rem;
  }
  .prompt-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    max-width: 560px;
    margin: 0 auto;
  }
  .pill {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 0.8rem;
    color: var(--text2);
    cursor: pointer;
    transition: all 0.15s;
  }
  .pill:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-bg);
  }

  .stat-row {
    display: flex;
    gap: 8px;
    margin: 0.5rem 0;
  }
  .stat-box {
    flex: 1;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.6rem 0.5rem;
    text-align: center;
  }
  .stat-val {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    font-family: var(--mono);
  }
  .stat-lbl {
    font-size: 0.65rem;
    color: var(--text3);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 2px;
  }

  .roadmap-item {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 4px;
    transition: background 0.15s;
  }
  .roadmap-item:hover { background: var(--bg3); }
  .roadmap-badge {
    font-size: 0.62rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    flex-shrink: 0;
    margin-top: 2px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .badge-soon { background: rgba(74,222,128,0.12); color: var(--green); border: 1px solid rgba(74,222,128,0.25); }
  .badge-planned { background: rgba(96,165,250,0.1); color: var(--blue); border: 1px solid rgba(96,165,250,0.2); }
  .badge-idea { background: var(--bg3); color: var(--text3); border: 1px solid var(--border); }
  .roadmap-text { font-size: 0.8rem; color: var(--text2); line-height: 1.4; }
  .roadmap-text strong { color: var(--text); display: block; font-size: 0.82rem; }

  .key-status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 8px;
    background: var(--bg3);
    border: 1px solid var(--border);
    margin-bottom: 4px;
    font-family: var(--mono);
    font-size: 0.73rem;
  }
  .key-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
  .dot-green { background: var(--green); box-shadow: 0 0 6px rgba(74,222,128,0.5); }
  .dot-orange { background: var(--accent); box-shadow: 0 0 6px rgba(249,115,22,0.4); }

  .context-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .poweredby {
    font-size: 0.68rem;
    color: var(--text3);
    text-align: center;
    padding: 1rem 0 0.5rem;
    letter-spacing: 0.04em;
  }
  .poweredby span { color: var(--text2); }

  /* ── Studying banner ── */
  .study-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 14px;
    margin-bottom: 1rem;
    font-size: 0.82rem;
    color: var(--text2);
    flex-wrap: wrap;
  }
  .study-banner-label { color: var(--text3); font-size: 0.76rem; }

  /* Chat message user bubble */
  [data-testid="stChatMessage"][data-testid*="user"] {
    padding-left: 2rem !important;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],
        "context_text": "",
        "context_sources": [],
        "msg_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def add_context(new_text: str, source_label: str, source_type: str):
    sep = "\n\n" + "="*60 + "\n\n"
    st.session_state.context_text = (
        (st.session_state.context_text + sep + new_text)
        if st.session_state.context_text else new_text
    )
    st.session_state.context_sources.append({"type": source_type, "label": source_label})

def clear_context():
    st.session_state.context_text = ""
    st.session_state.context_sources = []

def export_chat_history() -> str:
    lines = [f"# ExamHelp Chat Export\n_Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"]
    if st.session_state.context_sources:
        lines.append("## Study Materials Used")
        for src in st.session_state.context_sources:
            lines.append(f"- [{src['type'].upper()}] {src['label']}")
        lines.append("")
    lines.append("## Conversation\n")
    for msg in st.session_state.messages:
        role = "**You**" if msg["role"] == "user" else "**ExamHelp**"
        lines.append(f"{role}\n\n{msg['content']}\n\n---\n")
    return "\n".join(lines)

def _get_override_key() -> str | None:
    try:
        k = st.secrets.get("GROQ_API_KEY", "")
        if k: return k
    except Exception:
        pass
    env_key = os.getenv("GROQ_API_KEY", "")
    if env_key: return env_key
    return st.session_state.get("manual_api_key") or None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    # ── Logo ──────────────────────────────────
    st.markdown("""
    <div class="eh-logo">
      <div class="eh-logo-icon">📚</div>
      <div class="eh-logo-text">
        <div class="eh-logo-title">ExamHelp</div>
        <div class="eh-logo-sub">AI Study Assistant · Groq 70B</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────
    msg_count = len(st.session_state.messages)
    src_count = len(st.session_state.context_sources)
    ctx_kb = round(len(st.session_state.context_text) / 1000, 1)
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-box"><div class="stat-val">{msg_count}</div><div class="stat-lbl">Messages</div></div>
      <div class="stat-box"><div class="stat-val">{src_count}</div><div class="stat-lbl">Sources</div></div>
      <div class="stat-box"><div class="stat-val">{ctx_kb}k</div><div class="stat-lbl">Context</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── API Status ────────────────────────────
    st.markdown('<div class="section-label">🔑 API Status</div>', unsafe_allow_html=True)

    override = _get_override_key()
    active_key = key_manager.get_key(override=override)

    if active_key:
        masked = f"{active_key[:8]}…{active_key[-4:]}"
        st.markdown(f"""
        <div class="key-status-row">
          <div class="key-dot dot-green"></div>
          <span style="color:var(--green); font-weight:600;">Connected</span>
          <span style="color:var(--text3); margin-left:auto;">{masked}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        manual_key = st.text_input(
            "Enter Groq API Key",
            type="password",
            placeholder="gsk_…",
            help="Get a free key at console.groq.com",
        )
        if manual_key:
            st.session_state["manual_api_key"] = manual_key
            st.success("Key saved!", icon="✅")
        else:
            st.warning("No API key — add one above or set GROQ_API_KEY in .env", icon="⚠️")

    with st.expander("🔧 Key Pool Health"):
        rows = key_manager.status_table()
        for r in rows:
            dot = "dot-green" if "available" in r["status"] else "dot-orange"
            st.markdown(
                f'<div class="key-status-row"><div class="key-dot {dot}"></div>'
                f'<span style="color:var(--text2)">{r["key"]}</span>'
                f'<span style="color:var(--text3);margin-left:auto">✓{r["uses"]} ✗{r["errors"]}</span></div>',
                unsafe_allow_html=True,
            )
        if st.button("↺ Reset All Cooldowns", use_container_width=True):
            key_manager.reset_all_cooldowns()
            st.rerun()

    st.divider()

    # ── PDF Upload ────────────────────────────
    st.markdown('<div class="section-label">📄 PDF Upload</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload one or more PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="pdf_uploader",
    )
    if uploaded_files:
        if st.button("📥 Load PDFs into Context", use_container_width=True):
            with st.spinner("Extracting text…"):
                loaded = 0
                for uf in uploaded_files:
                    uf.seek(0)
                    stats = get_pdf_summary_stats(uf)
                    uf.seek(0)
                    meta = get_pdf_metadata(uf)
                    uf.seek(0)
                    text = extract_text_from_pdf(uf)
                    if text.startswith("Error"):
                        st.error(f"Failed: {uf.name}")
                    else:
                        label = meta.get("title") or uf.name
                        add_context(f"PDF: {label}\n\n{text}", label, "pdf")
                        loaded += 1
                        # Show rich stats
                        pages = stats.get("pages", "?")
                        words = stats.get("words", 0)
                        author = stats.get("author", "")
                        toc = stats.get("toc_entries", 0)
                        detail = f"📄 **{uf.name}** — {pages} pages · {words:,} words"
                        if author:
                            detail += f" · by {author}"
                        if toc:
                            detail += f" · {toc} chapters"
                        st.success(detail)
                if loaded:
                    st.success(f"✅ {loaded} PDF(s) ready — ask me anything about them!", icon="📚")

    st.divider()

    # ── YouTube ───────────────────────────────
    st.markdown('<div class="section-label">▶️ YouTube</div>', unsafe_allow_html=True)
    yt_url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=…",
                           label_visibility="collapsed", key="yt_input")
    if yt_url:
        if st.button("🎬 Load Transcript", use_container_width=True):
            with st.spinner("Fetching transcript… this may take a moment"):
                try:
                    transcript, vid_id = get_youtube_transcript(yt_url)
                    stats = get_transcript_stats(transcript)
                    ctx = format_transcript_as_context(transcript, vid_id)
                    add_context(ctx, f"YT: youtube.com/watch?v={vid_id}", "youtube")
                    mins = stats.get("duration_minutes", "?")
                    words = stats.get("word_count", 0)
                    segs = stats.get("segment_count", 0)
                    st.success(f"▶️ **{mins} min** video · {words:,} words · {segs} segments loaded!")
                except ValueError as e:
                    err = str(e)
                    if "transcript" in err.lower() or "disabled" in err.lower() or "no transcript" in err.lower():
                        st.error("❌ No transcript available for this video. Try a video with captions enabled.")
                    elif "video id" in err.lower():
                        st.error("❌ Invalid YouTube URL. Please check the link and try again.")
                    else:
                        st.error(f"❌ {err}")

    st.divider()

    # ── Web Scraper ───────────────────────────
    st.markdown('<div class="section-label">🌐 Web Page</div>', unsafe_allow_html=True)
    web_url = st.text_input("Web URL", placeholder="https://en.wikipedia.org/wiki/…",
                            label_visibility="collapsed", key="web_input")
    if web_url:
        if st.button("🔗 Load Web Page", use_container_width=True):
            with st.spinner("Reading page content…"):
                try:
                    page_text, page_title = scrape_web_page(web_url)
                    stats = get_web_stats(page_text, page_title)
                    ctx = format_web_context(page_text, page_title, web_url)
                    add_context(ctx, page_title[:50], "web")
                    words = stats.get("word_count", 0)
                    short_title = page_title[:40] + ("…" if len(page_title) > 40 else "")
                    st.success(f"🌐 **{short_title}** — {words:,} words extracted!")
                except ValueError as e:
                    err = str(e)
                    if "fetch" in err.lower() or "connect" in err.lower():
                        st.error("❌ Couldn't reach that URL. Check the link or try a different page.")
                    else:
                        st.error(f"❌ {err}")

    st.divider()

    # ── Active Context ────────────────────────
    if st.session_state.context_sources:
        st.markdown('<div class="section-label">📎 Active Context</div>', unsafe_allow_html=True)
        icons = {"pdf": "📄", "youtube": "▶️", "web": "🌐"}
        chips = "".join([
            f'<span class="source-chip"><span class="chip-dot"></span>{icons.get(s["type"],"📎")} {s["label"][:32]}</span>'
            for s in st.session_state.context_sources
        ])
        st.markdown(f'<div style="margin-bottom:0.5rem">{chips}</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear All Context", use_container_width=True):
            clear_context(); st.rerun()
    else:
        st.markdown(
            '<div style="color:var(--text3);font-size:0.8rem;padding:0.3rem 0 0.5rem;">'
            'No context loaded. Upload a PDF, add a YouTube link, or paste a URL above.</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Actions ───────────────────────────────
    st.markdown('<div class="section-label">⚙️ Actions</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.messages:
            st.download_button(
                "⬇️ Export",
                data=export_chat_history(),
                file_name=f"examhelp_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
    with col2:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = []; st.rerun()

    st.divider()

    # ── Feature Roadmap ───────────────────────
    with st.expander("🚀 Upcoming Features"):
        st.markdown("""
        <div style="padding:2px 0">

        <div class="roadmap-item">
          <span class="roadmap-badge badge-soon">Soon</span>
          <div class="roadmap-text">
            <strong>🃏 Flashcard Generator</strong>
            Auto-generate Q&amp;A flashcards from your uploaded material
          </div>
        </div>

        <div class="roadmap-item">
          <span class="roadmap-badge badge-soon">Soon</span>
          <div class="roadmap-text">
            <strong>📝 Smart Quiz Mode</strong>
            AI-generated multiple-choice quizzes with instant feedback
          </div>
        </div>

        <div class="roadmap-item">
          <span class="roadmap-badge badge-planned">Planned</span>
          <div class="roadmap-text">
            <strong>🗂️ Study Sessions</strong>
            Save &amp; reload named chat sessions across browser visits
          </div>
        </div>

        <div class="roadmap-item">
          <span class="roadmap-badge badge-planned">Planned</span>
          <div class="roadmap-text">
            <strong>📊 Mind Map Export</strong>
            Visualise key concepts as an interactive mind map
          </div>
        </div>

        <div class="roadmap-item">
          <span class="roadmap-badge badge-planned">Planned</span>
          <div class="roadmap-text">
            <strong>🌍 Multi-language</strong>
            Chat and receive answers in your preferred language
          </div>
        </div>

        <div class="roadmap-item">
          <span class="roadmap-badge badge-idea">Idea</span>
          <div class="roadmap-text">
            <strong>🎙️ Voice Input</strong>
            Ask questions by speaking instead of typing
          </div>
        </div>

        <div class="roadmap-item">
          <span class="roadmap-badge badge-idea">Idea</span>
          <div class="roadmap-text">
            <strong>📅 Study Planner</strong>
            AI-generated revision timetable based on your topics
          </div>
        </div>

        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="poweredby">Powered by <span>Groq</span> · <span>llama-3.3-70b-versatile</span></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# MAIN CHAT AREA
# ─────────────────────────────────────────────

# ── Header ───────────────────────────────────
st.markdown("""
<div style="padding: 1.5rem 0 0.5rem; border-bottom: 1px solid var(--border); margin-bottom: 1rem;">
  <div style="display:flex; align-items:baseline; gap:10px;">
    <div style="font-family:var(--serif); font-size:1.5rem; color:var(--text); letter-spacing:-0.3px;">
      ExamHelp
    </div>
    <div style="font-size:0.78rem; color:var(--text3);">Your focused AI study companion</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Active sources banner ────────────────────
if st.session_state.context_sources:
    icons = {"pdf": "📄", "youtube": "▶️", "web": "🌐"}
    chips = " ".join([
        f'<span class="source-chip"><span class="chip-dot"></span>'
        f'{icons.get(s["type"],"📎")} {s["label"][:28]}</span>'
        for s in st.session_state.context_sources
    ])
    st.markdown(
        f'<div class="study-banner"><span class="study-banner-label">Studying →</span>{chips}</div>',
        unsafe_allow_html=True,
    )

# ── Empty state ──────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-badge">✦ Powered by Groq · llama-3.3-70b-versatile</div>
      <div class="hero-title">Study smarter,<br><em>not harder</em></div>
      <div class="hero-sub">
        Upload your notes, lecture PDFs, YouTube videos, or any article —
        then ask anything and get sharp, exam-focused answers instantly.
      </div>
      <div class="prompt-pills">
        <div class="pill">📋 Summarise this PDF</div>
        <div class="pill">🎯 What are the key exam topics?</div>
        <div class="pill">🧠 Quiz me on this chapter</div>
        <div class="pill">📌 Explain this concept simply</div>
        <div class="pill">✍️ Generate study notes</div>
        <div class="pill">🔍 Compare these two ideas</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Chat history ──────────────────────────────
for msg in st.session_state.messages:
    avatar = "🎓" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────
user_input = st.chat_input("Ask anything about your study material…", key="chat_input")

if user_input:
    override = _get_override_key()
    active_key = key_manager.get_key(override=override)

    if not active_key:
        st.error("No API key available. Please enter a Groq API key in the sidebar.", icon="🔑")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🎓"):
        placeholder = st.empty()
        full_response = ""
        max_attempts = key_manager.MAX_RETRIES
        attempt = 0
        success = False

        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-20:]]

        while attempt < max_attempts and not success:
            current_key = key_manager.get_key(override=override)
            if not current_key:
                full_response = "⚠️ **All API keys are cooling down.** Please wait ~60 seconds and try again."
                placeholder.warning(full_response)
                break

            full_response = ""
            try:
                for chunk in stream_chat_with_groq(history, st.session_state.context_text, override_key=current_key):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                success = True

            except ValueError as e:
                full_response = f"⚠️ **Configuration Error:** {e}"
                placeholder.error(full_response)
                break

            except Exception as e:
                err_msg = str(e)
                is_rate = "rate_limit" in err_msg.lower() or "429" in err_msg
                is_auth  = "authentication" in err_msg.lower() or "401" in err_msg or "invalid" in err_msg.lower()
                if is_rate or is_auth:
                    reason = "Rate limit" if is_rate else "Invalid key"
                    masked = f"{current_key[:8]}…{current_key[-4:]}"
                    placeholder.warning(f"⚡ {reason} on `{masked}`. Switching keys…", icon="🔄")
                    attempt += 1
                    continue
                else:
                    full_response = f"⚠️ **Error:** {err_msg}"
                    placeholder.error(full_response)
                    break

            attempt += 1

        if not success and not full_response:
            full_response = "⚠️ **All API keys are rate-limited.** Please wait ~60 seconds and try again."
            placeholder.warning(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})