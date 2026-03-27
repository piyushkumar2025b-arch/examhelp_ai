import streamlit as st
import os
import datetime
from dotenv import load_dotenv

from utils.groq_client import stream_chat_with_groq
from utils.pdf_handler import extract_text_from_pdf, get_pdf_metadata
from utils.youtube_handler import get_youtube_transcript, format_transcript_as_context, extract_video_id
from utils.web_handler import scrape_web_page, format_web_context

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
# CUSTOM CSS — Claude-like UI
# ─────────────────────────────────────────────
st.markdown("""
<style>
  /* Import fonts */
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

  /* Global reset */
  html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f0f10 !important;
    font-family: 'Sora', sans-serif !important;
    color: #ececec !important;
  }

  /* Hide default Streamlit header/footer */
  #MainMenu, footer, header { visibility: hidden; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #161617 !important;
    border-right: 1px solid #2a2a2b !important;
  }
  [data-testid="stSidebar"] * { font-family: 'Sora', sans-serif !important; }

  /* Main area padding */
  .main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 5rem !important;
    max-width: 820px !important;
    margin: 0 auto !important;
  }

  /* Chat messages */
  [data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.2rem 0 !important;
  }

  /* User message bubble */
  [data-testid="stChatMessage"][data-testid*="user"] .stMarkdown,
  div[class*="user"] .stMarkdown {
    background: #1e1e1f !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 12px 16px !important;
  }

  /* Chat input box */
  [data-testid="stChatInputContainer"] {
    background-color: #161617 !important;
    border-top: 1px solid #2a2a2b !important;
    padding: 0.75rem 1rem !important;
    position: sticky !important;
    bottom: 0 !important;
  }
  [data-testid="stChatInputContainer"] textarea {
    background-color: #1e1e1f !important;
    border: 1px solid #3a3a3b !important;
    border-radius: 12px !important;
    color: #ececec !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
  }
  [data-testid="stChatInputContainer"] textarea:focus {
    border-color: #cc785c !important;
    box-shadow: 0 0 0 2px rgba(204,120,92,0.18) !important;
  }

  /* Send button */
  [data-testid="stChatInputContainer"] button {
    background-color: #cc785c !important;
    border-radius: 8px !important;
    color: white !important;
  }

  /* Buttons */
  .stButton > button {
    background-color: #1e1e1f !important;
    border: 1px solid #3a3a3b !important;
    color: #ececec !important;
    border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.85rem !important;
    transition: all 0.18s ease !important;
  }
  .stButton > button:hover {
    border-color: #cc785c !important;
    color: #cc785c !important;
    background-color: rgba(204,120,92,0.08) !important;
  }

  /* File uploader */
  [data-testid="stFileUploader"] {
    background-color: #1a1a1b !important;
    border: 1px dashed #3a3a3b !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
  }

  /* Text input */
  [data-testid="stTextInput"] input {
    background-color: #1e1e1f !important;
    border: 1px solid #3a3a3b !important;
    border-radius: 10px !important;
    color: #ececec !important;
    font-family: 'Sora', sans-serif !important;
  }
  [data-testid="stTextInput"] input:focus {
    border-color: #cc785c !important;
  }

  /* Divider */
  hr { border-color: #2a2a2b !important; }

  /* Context badge */
  .context-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1e2a24;
    border: 1px solid #2d5a3d;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #5ccc8a;
    font-family: 'JetBrains Mono', monospace;
    margin: 2px 4px 2px 0;
  }

  /* Section headers in sidebar */
  .sidebar-section {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #666 !important;
    margin: 1.2rem 0 0.5rem 0;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: #0f0f10; }
  ::-webkit-scrollbar-thumb { background: #2a2a2b; border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: #3a3a3b; }

  /* Code blocks */
  code {
    background-color: #1e1e1f !important;
    border: 1px solid #2a2a2b !important;
    border-radius: 5px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85em !important;
    padding: 2px 5px !important;
    color: #cc785c !important;
  }

  /* Expander */
  [data-testid="stExpander"] {
    background-color: #161617 !important;
    border: 1px solid #2a2a2b !important;
    border-radius: 10px !important;
  }

  /* Success / warning / error */
  [data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],
        "context_text": "",
        "context_sources": [],   # list of dicts: {type, label}
        "api_key_set": False,
        "theme": "dark",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def add_context(new_text: str, source_label: str, source_type: str):
    """Append new context and register its source badge."""
    separator = "\n\n" + "="*60 + "\n\n"
    if st.session_state.context_text:
        st.session_state.context_text += separator + new_text
    else:
        st.session_state.context_text = new_text

    st.session_state.context_sources.append({
        "type": source_type,
        "label": source_label,
    })


def clear_context():
    st.session_state.context_text = ""
    st.session_state.context_sources = []


def export_chat_history() -> str:
    """Export chat messages as a markdown string."""
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


### ── API KEY ROTATION ──────────────────────────────────────────────────
# Three keys tried in order. Key 1 = env/.env/manual, Keys 2 & 3 = hardcoded fallbacks.
_FALLBACK_KEYS = [
    "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",   # key 1
    "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",   # key 2
    "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",   # key 3
    "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",   # key 4
    "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",   # key 5
    "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",   # key 6
]

def _get_primary_key() -> str | None:
    """Return user-supplied key (env / secrets / manual input), if any."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    key = os.getenv("GROQ_API_KEY")
    if key and key not in _FALLBACK_KEYS:   # avoid re-adding fallbacks
        return key
    return st.session_state.get("manual_api_key", None)

def get_api_key() -> str | None:
    """Return the currently active API key (primary or current fallback index)."""
    primary = _get_primary_key()
    idx = st.session_state.get("_key_idx", 0)

    all_keys = ([primary] if primary else []) + _FALLBACK_KEYS
    if not all_keys:
        return None
    # Clamp index
    idx = min(idx, len(all_keys) - 1)
    return all_keys[idx]

def _rotate_key() -> bool:
    """
    Advance to the next available key.
    Returns True if a new key is available, False if all are exhausted.
    """
    primary = _get_primary_key()
    all_keys = ([primary] if primary else []) + _FALLBACK_KEYS
    idx = st.session_state.get("_key_idx", 0) + 1
    if idx < len(all_keys):
        st.session_state["_key_idx"] = idx
        return True
    return False

def _reset_key_rotation():
    st.session_state["_key_idx"] = 0


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    # Logo / Title
    st.markdown("""
    <div style='padding: 0.5rem 0 1rem 0;'>
      <div style='font-size:1.5rem; font-weight:700; letter-spacing:-0.5px; color:#ececec;'>
        📚 ExamHelp
      </div>
      <div style='font-size:0.78rem; color:#666; margin-top:2px;'>
        AI-powered study assistant
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── API KEY ──────────────────────────────
    st.markdown('<div class="sidebar-section">🔑 API Configuration</div>', unsafe_allow_html=True)

    primary = _get_primary_key()
    all_keys = ([primary] if primary else []) + _FALLBACK_KEYS
    key_idx = st.session_state.get("_key_idx", 0)
    key_idx = min(key_idx, len(all_keys) - 1)
    active_key = all_keys[key_idx] if all_keys else None
    active_num = key_idx + 1

    if active_key:
        os.environ["GROQ_API_KEY"] = active_key
        st.success(f"API key #{active_num} of {len(all_keys)} active ✓", icon="✅")
        if key_idx > 0:
            if st.button("🔁 Reset to Key #1", use_container_width=True):
                _reset_key_rotation()
                st.rerun()
    else:
        manual_key = st.text_input(
            "Enter Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get a free key at console.groq.com",
        )
        if manual_key:
            st.session_state["manual_api_key"] = manual_key
            os.environ["GROQ_API_KEY"] = manual_key
            st.success("API key saved!", icon="✅")
        else:
            st.warning("Add your Groq API key to start chatting.", icon="⚠️")

    st.divider()

    # ── PDF UPLOAD ────────────────────────────
    st.markdown('<div class="sidebar-section">📄 Upload PDF</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload one or more PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="pdf_uploader",
    )

    if uploaded_files:
        if st.button("📥 Load PDF(s) into Context", use_container_width=True):
            with st.spinner("Extracting text from PDF(s)..."):
                loaded_count = 0
                for uf in uploaded_files:
                    uf.seek(0)
                    meta = get_pdf_metadata(uf)
                    uf.seek(0)
                    text = extract_text_from_pdf(uf)
                    if text.startswith("Error"):
                        st.error(f"Failed: {uf.name} — {text}")
                    else:
                        label = meta.get("title") or uf.name
                        add_context(f"PDF: {label}\n\n{text}", label, "pdf")
                        loaded_count += 1
                if loaded_count:
                    st.success(f"Loaded {loaded_count} PDF(s) into context!", icon="📄")

    st.divider()

    # ── YOUTUBE ────────────────────────────────
    st.markdown('<div class="sidebar-section">▶️ YouTube Video</div>', unsafe_allow_html=True)
    yt_url = st.text_input(
        "YouTube URL",
        placeholder="https://youtube.com/watch?v=...",
        label_visibility="collapsed",
        key="yt_input",
    )
    if yt_url:
        if st.button("🎬 Load YouTube Transcript", use_container_width=True):
            with st.spinner("Fetching transcript..."):
                try:
                    transcript, vid_id = get_youtube_transcript(yt_url)
                    context_text = format_transcript_as_context(transcript, vid_id)
                    label = f"YT: youtube.com/watch?v={vid_id}"
                    add_context(context_text, label, "youtube")
                    st.success("YouTube transcript loaded!", icon="▶️")
                except ValueError as e:
                    st.error(str(e))

    st.divider()

    # ── WEB LINK ──────────────────────────────
    st.markdown('<div class="sidebar-section">🌐 Web Page / Article</div>', unsafe_allow_html=True)
    web_url = st.text_input(
        "Web URL",
        placeholder="https://en.wikipedia.org/wiki/...",
        label_visibility="collapsed",
        key="web_input",
    )
    if web_url:
        if st.button("🔗 Load Web Page", use_container_width=True):
            with st.spinner("Scraping page content..."):
                try:
                    page_text, page_title = scrape_web_page(web_url)
                    context_text = format_web_context(page_text, page_title, web_url)
                    add_context(context_text, page_title[:50], "web")
                    st.success(f"Loaded: {page_title[:40]}...", icon="🌐")
                except ValueError as e:
                    st.error(str(e))

    st.divider()

    # ── ACTIVE CONTEXT ───────────────────────
    if st.session_state.context_sources:
        st.markdown('<div class="sidebar-section">📎 Active Context</div>', unsafe_allow_html=True)
        for src in st.session_state.context_sources:
            icon = {"pdf": "📄", "youtube": "▶️", "web": "🌐"}.get(src["type"], "📎")
            st.markdown(f"""
            <div class="context-badge">{icon} {src['label'][:35]}</div>
            """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("🗑️ Clear All Context", use_container_width=True):
            clear_context()
            st.rerun()
    else:
        st.markdown('<div style="color:#444; font-size:0.82rem; margin-top:0.5rem;">No context loaded yet.<br>Upload a PDF, paste a YouTube link, or add a web URL above.</div>', unsafe_allow_html=True)

    st.divider()

    # ── EXPORT + CLEAR ────────────────────────
    st.markdown('<div class="sidebar-section">⚙️ Actions</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.messages:
            export_md = export_chat_history()
            st.download_button(
                label="⬇️ Export",
                data=export_md,
                file_name=f"examhelp_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
    with col2:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.markdown('<div style="color:#333; font-size:0.72rem; margin-top:2rem; text-align:center;">Powered by Groq · llama-3.1-8b-instant</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN CHAT AREA
# ─────────────────────────────────────────────

# Header
st.markdown("""
<div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
  <div style='font-size:1.1rem; font-weight:600; color:#ececec; letter-spacing:-0.3px;'>ExamHelp</div>
  <div style='font-size:0.8rem; color:#555; margin-top:2px;'>Your focused AI study companion</div>
</div>
""", unsafe_allow_html=True)

# Active context chips in main area (if any)
if st.session_state.context_sources:
    chips_html = "".join([
        f'<span class="context-badge">'
        f'{"📄" if s["type"]=="pdf" else "▶️" if s["type"]=="youtube" else "🌐"} '
        f'{s["label"][:30]}</span>'
        for s in st.session_state.context_sources
    ])
    st.markdown(
        f'<div style="text-align:center; margin-bottom:0.8rem;">'
        f'<span style="font-size:0.75rem; color:#555; margin-right:6px;">Studying:</span>'
        f'{chips_html}</div>',
        unsafe_allow_html=True
    )

# Welcome message if no chat yet
if not st.session_state.messages:
    st.markdown("""
    <div style='
      text-align:center;
      padding: 3rem 2rem;
      color: #444;
    '>
      <div style='font-size:2.8rem; margin-bottom:1rem;'>📚</div>
      <div style='font-size:1.05rem; font-weight:500; color:#666; margin-bottom:0.5rem;'>
        Ready to help you study
      </div>
      <div style='font-size:0.85rem; color:#444; line-height:1.7;'>
        Upload PDFs · Add YouTube links · Paste article URLs<br>
        Then ask anything about your study material
      </div>
      <div style='margin-top:1.5rem; display:flex; gap:0.5rem; justify-content:center; flex-wrap:wrap;'>
        <div style='background:#1a1a1b; border:1px solid #2a2a2b; border-radius:20px; padding:6px 14px; font-size:0.78rem; color:#888;'>
          "Summarise this PDF for me"
        </div>
        <div style='background:#1a1a1b; border:1px solid #2a2a2b; border-radius:20px; padding:6px 14px; font-size:0.78rem; color:#888;'>
          "What are the key exam topics?"
        </div>
        <div style='background:#1a1a1b; border:1px solid #2a2a2b; border-radius:20px; padding:6px 14px; font-size:0.78rem; color:#888;'>
          "Quiz me on this chapter"
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Render chat history ──────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🎓" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# ── Chat input ───────────────────────────────
user_input = st.chat_input(
    placeholder="Ask anything about your study material…",
    key="chat_input",
)

if user_input:
    # Check API key
    if not get_api_key():
        st.error("Please enter your Groq API key in the sidebar first!", icon="🔑")
        st.stop()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Stream assistant response (with automatic API key rotation)
    with st.chat_message("assistant", avatar="🎓"):
        response_placeholder = st.empty()
        full_response = ""

        # Build message history for API (last 20 messages)
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[-20:]
        ]

        max_attempts = 6
        attempt = 0
        success = False

        while attempt < max_attempts and not success:
            current_key = get_api_key()
            if not current_key:
                full_response = "⚠️ **No API key available.** All keys exhausted or none configured."
                response_placeholder.error(full_response)
                break

            os.environ["GROQ_API_KEY"] = current_key
            full_response = ""
            try:
                for chunk in stream_chat_with_groq(history, st.session_state.context_text):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                success = True

            except ValueError as e:
                full_response = f"⚠️ **Configuration Error:** {str(e)}"
                response_placeholder.error(full_response)
                break

            except Exception as e:
                err_msg = str(e)
                is_rate_limit = "rate_limit" in err_msg.lower() or "429" in err_msg
                is_auth_error = "api_key" in err_msg.lower() or "authentication" in err_msg.lower() or "401" in err_msg

                if is_rate_limit or is_auth_error:
                    reason = "Rate limit hit" if is_rate_limit else "Invalid/expired key"
                    key_num = st.session_state.get("_key_idx", 0) + 1
                    if _rotate_key():
                        next_num = st.session_state.get("_key_idx", 0) + 1
                        response_placeholder.warning(
                            f"⚡ {reason} on key #{key_num}. Switching to key #{next_num} automatically…",
                            icon="🔄"
                        )
                        attempt += 1
                        continue
                    else:
                        full_response = "⚠️ **All API keys exhausted.** Please add a new Groq API key in the sidebar."
                        response_placeholder.error(full_response)
                        break
                else:
                    full_response = f"⚠️ **Error:** {err_msg}"
                    response_placeholder.error(full_response)
                    break

            attempt += 1

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": full_response})