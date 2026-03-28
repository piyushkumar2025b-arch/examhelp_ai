"""
ExamHelp AI — v3.0 Upgraded
Full-featured AI study assistant with elite API key rotation,
glassmorphic UI, multi-source RAG, and complete feature set.
"""

import datetime
import json
import os
import re
import time
import base64
import zlib
import streamlit as st

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None; go = None

from utils.groq_client import stream_chat_with_groq, transcribe_audio, chat_with_groq
from utils.pdf_handler import extract_text_from_pdf, get_pdf_metadata, get_pdf_summary_stats
from utils.youtube_handler import get_youtube_transcript, format_transcript_as_context, extract_video_id, get_transcript_stats
from utils.web_handler import scrape_web_page, format_web_context, get_web_stats
from utils import key_manager
from utils.personas import PERSONAS, get_persona_names, get_persona_by_name, build_persona_prompt
from utils.ocr_handler import extract_text_from_image
from utils.analytics import get_subject_mastery_radar, get_study_intensity_heatmap, estimate_required_velocity
from utils.app_controller import AppController
from dotenv import load_dotenv

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
# SESSION STATE
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],
        "context_text": "",
        "context_sources": [],
        "msg_count": 0,
        "total_output_chars": 0,
        "total_output_lines": 0,
        "total_tokens_used": 0,
        "selected_persona": "Default (ExamHelp)",
        "theme_mode": "dark",
        "selected_language": "English",
        "saved_sessions": {},
        "queued_prompt": None,
        "last_audio": None,
        "app_mode": "chat",
        "voice_mode": False,
        "study_tasks": [],
        "flashcards": [],
        "quiz_data": [],
        "current_card": 0,
        "quiz_score": 0,
        "quiz_current": 0,
        "quiz_feedback": None,
        "bookmarks": [],
        "calendar_events": {},
        "focus_mode": False,
        "calculator_open": False,
        "chat_history_open": False,
        "vector_store": None,
        "model_choice": "llama-3.3-70b-versatile",
        "study_goals": [],
        "exam_date": datetime.date.today() + datetime.timedelta(days=30),
        "last_context_hash": None,
        "last_context_summary": "",
        "card_mastery": {},
        "key_health_expanded": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Persistent sessions from disk
    if "persistent_sessions" not in st.session_state:
        st.session_state.persistent_sessions = {}
        if os.path.exists("sessions.json"):
            try:
                with open("sessions.json", "r") as f:
                    st.session_state.persistent_sessions = json.load(f)
            except Exception:
                pass

    # Vector store
    from memory.vector_store import VectorStore
    if st.session_state.vector_store is None:
        st.session_state.vector_store = VectorStore()

init_state()

# ─────────────────────────────────────────────
# QUERY PARAM ACTIONS
# ─────────────────────────────────────────────
if "action" in st.query_params:
    action = st.query_params["action"]
    _action_prompts = {
        "flashcards": "Based on the provided study material, generate 10 expert Q&A flashcards to drill my knowledge. Format as **Q:** then **A:**.",
        "quiz": "Based on the study material, ask me one multiple-choice question at a time. Wait for my answer before proceeding.",
        "mindmap": "Generate a comprehensive Mermaid.js mind map (graph TD) of key concepts from the study material. Provide ONLY the raw Mermaid code block.",
        "planner": "Create a structured day-by-day revision timetable for the major topics in the study material. Be specific about timeframes and priorities.",
    }
    if action in _action_prompts:
        st.session_state.queued_prompt = _action_prompts[action]

# Shared chat loading
from chat.share import ChatShare
if "chat" in st.query_params:
    try:
        decoded_bytes = base64.urlsafe_b64decode(st.query_params["chat"].encode())
        minimal_history = json.loads(zlib.decompress(decoded_bytes).decode())
        st.session_state.messages = [{"role": m["r"], "content": m["c"]} for m in minimal_history]
        st.query_params.clear()
        st.rerun()
    except Exception:
        st.query_params.clear()


# ─────────────────────────────────────────────
# THEME CSS
# ─────────────────────────────────────────────
def get_theme_css():
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    if is_dark:
        c = {
            "bg": "#0a0a0b", "bg_glass": "rgba(10,10,11,0.65)",
            "bg2": "#111113", "bg2_glass": "rgba(17,17,19,0.75)",
            "bg3": "#18181b", "bg3_glass": "rgba(24,24,27,0.7)",
            "border": "#27272a", "bd_glass": "rgba(39,39,42,0.5)", "border2": "#3f3f46",
            "text": "#fafafa", "text2": "#a1a1aa", "text3": "#52525b",
            "accent": "#d97706", "accent2": "#f59e0b",
            "accent_bg": "rgba(217,119,6,0.08)", "accent_bd": "rgba(217,119,6,0.25)",
            "green": "#4ade80", "green_bg": "rgba(74,222,128,0.08)",
            "red": "#f87171", "blue": "#60a5fa",
            "card_shadow": "rgba(0,0,0,0.3)",
        }
    else:
        c = {
            "bg": "#fafaf9", "bg_glass": "rgba(250,250,249,0.7)",
            "bg2": "#f5f5f4", "bg2_glass": "rgba(245,245,244,0.75)",
            "bg3": "#e7e5e4", "bg3_glass": "rgba(231,229,228,0.7)",
            "border": "#d6d3d1", "bd_glass": "rgba(214,211,209,0.5)", "border2": "#a8a29e",
            "text": "#1c1917", "text2": "#57534e", "text3": "#a8a29e",
            "accent": "#d97706", "accent2": "#b45309",
            "accent_bg": "rgba(217,119,6,0.08)", "accent_bd": "rgba(217,119,6,0.25)",
            "green": "#16a34a", "green_bg": "rgba(22,163,74,0.08)",
            "red": "#dc2626", "blue": "#2563eb",
            "card_shadow": "rgba(0,0,0,0.06)",
        }
    return f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
  :root {{
    --bg:{c['bg']}; --bg-glass:{c['bg_glass']}; --bg2:{c['bg2']}; --bg2-glass:{c['bg2_glass']};
    --bg3:{c['bg3']}; --bg3-glass:{c['bg3_glass']}; --border:{c['border']};
    --bd-glass:{c['bd_glass']}; --border2:{c['border2']};
    --text:{c['text']}; --text2:{c['text2']}; --text3:{c['text3']};
    --accent:{c['accent']}; --accent2:{c['accent2']};
    --accent-bg:{c['accent_bg']}; --accent-bd:{c['accent_bd']};
    --green:{c['green']}; --green-bg:{c['green_bg']};
    --red:{c['red']}; --blue:{c['blue']};
    --card-shadow:{c['card_shadow']};
    --sans:'Inter',system-ui,-apple-system,sans-serif;
    --mono:'JetBrains Mono',monospace;
  }}
  html,body,[data-testid="stAppViewContainer"] {{
    background-color:var(--bg) !important; font-family:var(--sans) !important; color:var(--text) !important;
  }}
  #MainMenu,footer {{ visibility:hidden; }}
  [data-testid="stSidebar"] {{
    background-color:var(--bg2-glass) !important; backdrop-filter:blur(24px) !important;
    -webkit-backdrop-filter:blur(24px) !important; border-right:1px solid var(--bd-glass) !important;
    padding-top:0 !important;
  }}
  [data-testid="stSidebar"] * {{ font-family:var(--sans) !important; }}
  .main .block-container {{
    padding-top:0 !important; padding-bottom:6rem !important;
    max-width:860px !important; margin:0 auto !important;
  }}
  @keyframes msgIn {{ 0% {{transform:translateY(12px);opacity:0}} 100% {{transform:none;opacity:1}} }}
  [data-testid="stChatMessage"] {{
    background:var(--bg2-glass) !important; backdrop-filter:blur(12px) !important;
    border:1px solid var(--bd-glass) !important; border-radius:12px !important;
    padding:1.2rem 1.4rem !important; margin-bottom:1.2rem !important;
    animation:msgIn 0.35s cubic-bezier(.16,1,.3,1) forwards;
  }}
  [data-testid="stChatMessage"]:has(.user-msg-hook) {{
    background:var(--bg3-glass) !important; border:1px solid var(--accent-bd) !important;
    margin-left:18% !important; border-top-right-radius:2px !important;
  }}
  [data-testid="stChatMessage"]:not(:has(.user-msg-hook)) {{
    margin-right:12% !important; border-top-left-radius:2px !important;
  }}
  [data-testid="stChatInputContainer"] {{
    background:linear-gradient(to top,var(--bg) 60%,transparent) !important;
    border-top:none !important; padding:1rem 1.5rem 1.5rem !important;
    position:sticky !important; bottom:0 !important;
  }}
  [data-testid="stChatInputContainer"] textarea {{
    background-color:var(--bg3-glass) !important; backdrop-filter:blur(20px) !important;
    border:1px solid var(--bd-glass) !important; border-radius:20px !important;
    color:var(--text) !important; font-size:.95rem !important; padding:16px 20px !important;
  }}
  [data-testid="stChatInputContainer"] textarea:focus {{
    border-color:var(--accent) !important; box-shadow:0 0 0 3px var(--accent-bg) !important;
  }}
  [data-testid="stChatInputContainer"] button {{
    background-color:var(--accent) !important; border-radius:10px !important; color:white !important;
  }}
  .stButton>button {{
    background-color:var(--bg3-glass) !important; backdrop-filter:blur(10px) !important;
    border:1px solid var(--bd-glass) !important; color:var(--text) !important;
    border-radius:12px !important; font-size:.88rem !important; font-weight:500 !important;
    padding:.5rem 1.1rem !important; transition:all .25s cubic-bezier(.16,1,.3,1) !important;
  }}
  .stButton>button:hover {{
    border-color:var(--accent) !important; color:var(--accent) !important;
    background-color:var(--accent-bg) !important; transform:translateY(-1px) !important;
  }}
  [data-testid="stSelectbox"]>div>div {{
    background-color:var(--bg3-glass) !important; border:1px solid var(--bd-glass) !important;
    border-radius:10px !important; color:var(--text) !important;
  }}
  [data-testid="stFileUploader"] {{
    background-color:var(--bg3-glass) !important; border:1.5px dashed var(--bd-glass) !important;
    border-radius:14px !important; padding:.4rem !important;
  }}
  [data-testid="stFileUploader"]:hover {{ border-color:var(--accent) !important; background-color:var(--accent-bg) !important; }}
  [data-testid="stTextInput"] input {{
    background-color:var(--bg3-glass) !important; border:1px solid var(--bd-glass) !important;
    border-radius:10px !important; color:var(--text) !important; font-size:.88rem !important;
  }}
  [data-testid="stTextInput"] input:focus {{ border-color:var(--accent) !important; box-shadow:0 0 0 3px var(--accent-bg) !important; }}
  [data-testid="stExpander"] {{
    background-color:var(--bg2-glass) !important; backdrop-filter:blur(12px) !important;
    border:1px solid var(--bd-glass) !important; border-radius:12px !important;
  }}
  hr {{ border-color:var(--border) !important; margin:.6rem 0 !important; }}
  ::-webkit-scrollbar {{ width:4px; }}
  ::-webkit-scrollbar-track {{ background:var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background:var(--border2); border-radius:10px; }}
  code {{
    background-color:var(--bg3) !important; border:1px solid var(--border) !important;
    border-radius:5px !important; font-family:var(--mono) !important;
    font-size:.82em !important; padding:2px 6px !important; color:var(--accent) !important;
  }}
  /* Logo */
  .eh-logo {{ display:flex; align-items:center; gap:12px; padding:1.2rem 1rem .8rem; border-bottom:1px solid var(--border); margin-bottom:.8rem; }}
  .eh-logo-icon {{ width:36px; height:36px; background:linear-gradient(135deg,var(--accent),var(--accent2)); border-radius:10px; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 12px rgba(217,119,6,.35); }}
  .eh-logo-title {{ font-size:1.05rem; font-weight:700; color:var(--text); letter-spacing:-.3px; }}
  .eh-logo-sub {{ font-size:.7rem; color:var(--text3); }}
  /* Section labels */
  .section-label {{
    font-size:.68rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase;
    color:var(--text3); margin:1rem 0 .45rem; display:flex; align-items:center; gap:6px;
  }}
  .section-label::after {{ content:''; flex:1; height:1px; background:var(--border); }}
  /* Source chips */
  .source-chip {{
    display:inline-flex; align-items:center; gap:6px; background:var(--bg2);
    border:1px solid var(--border); border-radius:12px; padding:4px 12px;
    font-size:.78rem; color:var(--text2); margin:3px 4px 3px 0;
  }}
  .source-chip .chip-dot {{ width:6px; height:6px; border-radius:50%; background:var(--accent); flex-shrink:0; }}
  /* Hero */
  .hero-wrap {{ text-align:center; padding:3.5rem 2rem 1.5rem; animation:fadeUp .7s cubic-bezier(.16,1,.3,1) both; }}
  @keyframes fadeUp {{ from {{opacity:0;transform:translateY(20px)}} to {{opacity:1;transform:none}} }}
  .hero-badge {{ display:inline-flex; align-items:center; gap:6px; background:var(--accent-bg); border:1px solid var(--accent-bd); border-radius:20px; padding:4px 14px; font-size:.75rem; color:var(--accent); font-weight:500; margin-bottom:1.4rem; }}
  .hero-title {{ font-size:2.4rem; font-weight:800; color:var(--text); letter-spacing:-1.2px; line-height:1.15; margin-bottom:.6rem; }}
  .hero-title em {{ color:var(--accent); font-style:italic; }}
  .hero-sub {{ font-size:.93rem; color:var(--text2); line-height:1.6; max-width:460px; margin:0 auto 1.8rem; }}
  .prompt-pills {{ display:flex; flex-wrap:wrap; gap:8px; justify-content:center; max-width:540px; margin:0 auto; }}
  .pill {{ background:var(--bg3-glass); border:1px solid var(--bd-glass); border-radius:20px; padding:7px 16px; font-size:.8rem; color:var(--text2); cursor:pointer; transition:all .25s ease; }}
  .pill:hover {{ border-color:var(--accent); color:var(--accent); background:var(--accent-bg); transform:translateY(-2px); }}
  /* Stats */
  .stat-row {{ display:flex; gap:8px; margin:.5rem 0; }}
  .stat-box {{ flex:1; background:var(--bg2); border:1px solid var(--border); border-radius:12px; padding:.7rem .5rem; text-align:center; }}
  .stat-val {{ font-size:1.1rem; font-weight:700; color:var(--accent); }}
  .stat-lbl {{ font-size:.65rem; color:var(--text3); text-transform:uppercase; letter-spacing:.06em; margin-top:2px; }}
  /* Key health bar */
  .key-health-bar {{
    height:6px; background:var(--bg3); border-radius:3px; overflow:hidden; margin:4px 0 10px;
  }}
  .key-health-fill {{ height:100%; border-radius:3px; transition:width .5s ease; }}
  /* Study banner */
  .study-banner {{ display:flex; align-items:center; flex-wrap:wrap; gap:6px; background:var(--accent-bg); border:1px solid var(--accent-bd); border-radius:10px; padding:8px 14px; margin-bottom:1rem; }}
  .study-banner-label {{ font-size:.75rem; font-weight:600; color:var(--accent); text-transform:uppercase; letter-spacing:.05em; white-space:nowrap; }}
  /* Focus banner */
  .focus-banner {{ background:linear-gradient(90deg,var(--accent-bg),transparent); border-left:3px solid var(--accent); border-radius:6px; padding:10px 16px; font-size:.85rem; color:var(--accent); margin-bottom:1rem; }}
  /* Persona chip */
  .persona-chip {{ background:var(--accent-bg); border:1px solid var(--accent-bd); border-radius:20px; padding:5px 14px; font-size:.78rem; color:var(--accent); display:inline-block; margin-bottom:.4rem; }}
  /* Flashcard */
  .card-container {{ perspective:800px; }}
  .flashcard {{ background:var(--bg2-glass); border:1.5px solid var(--bd-glass); border-radius:16px; padding:2rem; min-height:180px; display:flex; align-items:center; justify-content:center; text-align:center; font-size:1.1rem; font-weight:500; line-height:1.5; box-shadow:0 8px 32px var(--card-shadow); }}
  /* Tool cards */
  .tool-card {{ display:flex; align-items:center; gap:12px; background:var(--bg2-glass); border:1px solid var(--bd-glass); border-radius:12px; padding:.75rem 1rem; margin-bottom:.5rem; transition:all .2s ease; cursor:pointer; }}
  .tool-card:hover {{ border-color:var(--accent); transform:translateX(3px); }}
  .tool-icon {{ font-size:1.3rem; width:32px; text-align:center; flex-shrink:0; }}
  .tool-name {{ font-size:.88rem; font-weight:600; color:var(--text); display:block; }}
  .tool-desc {{ font-size:.73rem; color:var(--text3); display:block; }}
  /* Progress bars */
  .prog-wrap {{ margin-bottom:.8rem; }}
  .prog-label {{ display:flex; justify-content:space-between; font-size:.72rem; color:var(--text3); margin-bottom:3px; }}
  .prog-bar {{ height:4px; background:var(--bg3); border-radius:2px; }}
  .prog-fill {{ height:100%; border-radius:2px; background:var(--accent); }}
  /* Admin table */
  .key-row {{ display:flex; align-items:center; justify-content:space-between; padding:6px 0; border-bottom:1px solid var(--border); font-size:.78rem; }}
  .key-row:last-child {{ border-bottom:none; }}
  .badge-green {{ background:rgba(74,222,128,.15); color:var(--green); border-radius:6px; padding:2px 8px; font-size:.7rem; font-weight:600; }}
  .badge-red {{ background:rgba(248,113,113,.12); color:var(--red); border-radius:6px; padding:2px 8px; font-size:.7rem; font-weight:600; }}
  .badge-yellow {{ background:rgba(251,191,36,.12); color:#fbbf24; border-radius:6px; padding:2px 8px; font-size:.7rem; font-weight:600; }}
  /* Powered by */
  .poweredby {{ font-size:.65rem; color:var(--text3); text-align:center; padding:.5rem; margin-top:.5rem; }}
  .poweredby span {{ color:var(--accent); font-weight:600; }}
</style>
"""

st.markdown(get_theme_css(), unsafe_allow_html=True)

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
    # Auto-index into RAG vector store
    if st.session_state.vector_store:
        chunks = [new_text[i:i+1000] for i in range(0, len(new_text), 800)]
        try:
            st.session_state.vector_store.add_documents(chunks)
        except Exception:
            pass


def clear_context():
    st.session_state.context_text = ""
    st.session_state.context_sources = []
    st.session_state.last_context_hash = None
    st.session_state.last_context_summary = ""
    if st.session_state.vector_store:
        try:
            st.session_state.vector_store = None
            from memory.vector_store import VectorStore
            st.session_state.vector_store = VectorStore()
        except Exception:
            pass


def export_chat_history() -> str:
    lines = [f"# ExamHelp Chat Export\n_Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"]
    if st.session_state.context_sources:
        lines.append("## Study Materials Used")
        for src in st.session_state.context_sources:
            lines.append(f"- [{src['type'].upper()}] {src['label']}")
        lines.append("")
    persona = st.session_state.get("selected_persona", "Default (ExamHelp)")
    if persona != "Default (ExamHelp)":
        lines.append(f"## AI Persona: {persona}\n")
    lines.append("## Conversation\n")
    for msg in st.session_state.messages:
        role = "**You**" if msg["role"] == "user" else "**ExamHelp**"
        lines.append(f"{role}\n\n{msg['content']}\n\n---\n")
    return "\n".join(lines)


def _get_override_key() -> str | None:
    """Return manual key from sidebar input or session state."""
    return st.session_state.get("manual_api_key") or None


def count_output_stats(text: str):
    st.session_state.total_output_chars += len(text)
    st.session_state.total_output_lines += text.count('\n') + 1


def _key_health_html() -> str:
    """Render compact API key health widget."""
    cap = key_manager.get_total_capacity()
    avail = cap["keys_available"]
    total = cap["keys_total"]
    pct   = int(avail / max(1, total) * 100)
    color = "#4ade80" if pct >= 60 else "#fbbf24" if pct >= 30 else "#f87171"
    return f"""
    <div style="margin-bottom:.5rem;">
      <div style="display:flex;justify-content:space-between;font-size:.7rem;color:var(--text3);margin-bottom:3px;">
        <span>🔑 API Keys ({avail}/{total} active)</span>
        <span style="color:{color};font-weight:600;">{pct}%</span>
      </div>
      <div class="key-health-bar">
        <div class="key-health-fill" style="width:{pct}%;background:{color};"></div>
      </div>
      <div style="display:flex;gap:12px;font-size:.68rem;color:var(--text3);">
        <span>RPM: {cap['rpm_used']}/{cap['rpm_capacity']}</span>
        <span>TPM: {cap['tpm_used']:,}/{cap['tpm_capacity']:,}</span>
        <span>RPD: {cap['rpd_used']}/{cap['rpd_capacity']}</span>
      </div>
    </div>"""


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    if not st.session_state.get("focus_mode"):
        # ── Logo ───────────────────────────────────
        st.markdown("""
        <div class="eh-logo">
          <div class="eh-logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white" opacity="0.9"/>
              <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
              <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>
            </svg>
          </div>
          <div>
            <div class="eh-logo-title">ExamHelp</div>
            <div class="eh-logo-sub">AI Study Assistant · v3.0</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Theme toggle ───────────────────────────
        if st.button(
            "☀️ Light Mode" if st.session_state.theme_mode == "dark" else "🌙 Dark Mode",
            use_container_width=True, key="theme_btn"
        ):
            st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"
            st.rerun()

        # ── Stats row ──────────────────────────────
        msg_count = len(st.session_state.messages)
        src_count = len(st.session_state.context_sources)
        ctx_kb    = round(len(st.session_state.context_text) / 1024, 1)
        tok_used  = st.session_state.get("total_tokens_used", 0)
        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-box"><div class="stat-val">{msg_count}</div><div class="stat-lbl">Msgs</div></div>
          <div class="stat-box"><div class="stat-val">{src_count}</div><div class="stat-lbl">Sources</div></div>
          <div class="stat-box"><div class="stat-val">{ctx_kb}k</div><div class="stat-lbl">Context</div></div>
          <div class="stat-box"><div class="stat-val">{tok_used//1000}k</div><div class="stat-lbl">Tokens</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── API Key health ─────────────────────────
        st.markdown(_key_health_html(), unsafe_allow_html=True)

        # ── Manual key input ───────────────────────
        with st.expander("🔑 Override API Key"):
            manual_key = st.text_input(
                "Groq API Key", type="password", placeholder="gsk_…",
                help="Overrides rotation. Leave blank to use the pool.",
                key="api_key_input", label_visibility="collapsed",
            )
            if manual_key:
                st.session_state.manual_api_key = manual_key.strip()
                st.success("Key set!", icon="✅")
            else:
                st.session_state.pop("manual_api_key", None)

        st.divider()

        # ── AI Persona ─────────────────────────────
        st.markdown('<div class="section-label">🎭 AI Persona</div>', unsafe_allow_html=True)
        persona_names  = get_persona_names()
        cur_persona    = st.session_state.get("selected_persona", "Default (ExamHelp)")
        selected_p     = st.selectbox(
            "Persona", options=persona_names,
            index=persona_names.index(cur_persona) if cur_persona in persona_names else 0,
            label_visibility="collapsed", key="persona_select",
        )
        if selected_p != st.session_state.selected_persona:
            st.session_state.selected_persona = selected_p
            st.rerun()
        pdata = get_persona_by_name(selected_p)
        if pdata and selected_p != "Default (ExamHelp)":
            st.markdown(
                f'<div class="persona-chip">{pdata["emoji"]} {pdata["name"]} · {pdata["era"]}</div>'
                f'<div style="font-size:.73rem;color:var(--text3);margin-bottom:.4rem;">{pdata["mood"]}</div>',
                unsafe_allow_html=True)

        # ── Language ───────────────────────────────
        st.markdown('<div class="section-label">🌍 Language</div>', unsafe_allow_html=True)
        _langs = ["English","Spanish","French","German","Hindi","Mandarin","Japanese","Arabic","Portuguese","Russian"]
        cur_lang = st.session_state.get("selected_language", "English")
        sel_lang = st.selectbox("Lang", _langs,
            index=_langs.index(cur_lang) if cur_lang in _langs else 0,
            label_visibility="collapsed")
        if sel_lang != cur_lang:
            st.session_state.selected_language = sel_lang
            st.rerun()

        # ── Model selector ─────────────────────────
        st.markdown('<div class="section-label">🧠 Model Speed</div>', unsafe_allow_html=True)
        model_choice = st.select_slider(
            "Model", options=["Fast (8B)", "Balanced (70B)"],
            value="Balanced (70B)", label_visibility="collapsed",
        )
        st.session_state.model_choice = (
            "llama-3.1-8b-instant" if "Fast" in model_choice
            else "llama-3.3-70b-versatile"
        )

        # ── Voice mode ─────────────────────────────
        st.markdown('<div class="section-label">🎙️ Voice Mode</div>', unsafe_allow_html=True)
        v_mode = st.toggle("Enable TTS responses", value=st.session_state.get("voice_mode", False))
        if v_mode != st.session_state.voice_mode:
            st.session_state.voice_mode = v_mode

        st.divider()

    # ── Toolbar icons ──────────────────────────────
    tb_cols = st.columns(6)
    _tb_items = [
        ("📅", "tb_cal", "Calendar",    "calendar_open"),
        ("🧮", "tb_calc", "Calculator", None),
        ("📈", "tb_graph", "Graphs",    None),
        ("🔕" if st.session_state.focus_mode else "🔔", "tb_focus", "Focus Mode", None),
        ("🔖", "tb_bm",  "Bookmarks",   "bookmarks_open"),
        ("📜", "tb_hist", "History",    None),
    ]
    for col, (icon, k, tip, toggle_key) in zip(tb_cols, _tb_items):
        with col:
            if st.button(icon, key=k, help=tip, use_container_width=True):
                if k == "tb_calc":
                    st.session_state.calculator_open = not st.session_state.calculator_open
                elif k == "tb_graph":
                    st.session_state.app_mode = "graph"; st.rerun()
                elif k == "tb_focus":
                    st.session_state.focus_mode = not st.session_state.focus_mode; st.rerun()
                elif k == "tb_hist":
                    st.session_state.chat_history_open = not st.session_state.chat_history_open
                elif toggle_key:
                    st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)
                st.rerun()

    # ── Calendar popup ─────────────────────────────
    if st.session_state.get("calendar_open"):
        st.markdown('<div class="section-label">📅 Calendar</div>', unsafe_allow_html=True)
        cal_date = st.date_input("Date", value=datetime.date.today(), label_visibility="collapsed", key="cal_pick")
        cal_note = st.text_input("Event", placeholder="Physics exam Ch.5…", label_visibility="collapsed", key="cal_note")
        if st.button("➕ Save Event", use_container_width=True, key="cal_save") and cal_note:
            dkey = cal_date.isoformat()
            if dkey not in st.session_state.calendar_events:
                st.session_state.calendar_events[dkey] = []
            st.session_state.calendar_events[dkey].append(cal_note)
            st.success(f"Saved: {cal_note}")
        if st.session_state.calendar_events:
            st.markdown("**Upcoming:**")
            for d, events in sorted(st.session_state.calendar_events.items())[-4:]:
                for ev in events:
                    st.markdown(f"📌 `{d}` — {ev}")

    # ── Calculator popup ───────────────────────────
    if st.session_state.calculator_open:
        st.markdown('<div class="section-label">🧮 Calculator</div>', unsafe_allow_html=True)
        if "calc_expr" not in st.session_state: st.session_state.calc_expr = ""
        if "calc_result" not in st.session_state: st.session_state.calc_result = ""
        expr_disp = st.session_state.calc_expr or "0"
        st.markdown(
            f'<div style="background:var(--bg3);border:1px solid var(--border);border-radius:10px;'
            f'padding:12px 16px;font-family:var(--mono);font-size:1.2rem;color:var(--text);'
            f'min-height:52px;text-align:right;margin-bottom:.5rem;">{expr_disp}</div>',
            unsafe_allow_html=True)
        if st.session_state.calc_result:
            st.markdown(
                f'<div style="color:var(--accent);font-weight:700;font-size:1.4rem;text-align:right;'
                f'margin-bottom:.5rem;">= {st.session_state.calc_result}</div>',
                unsafe_allow_html=True)

        def _add_calc(v):
            if v == "C":
                st.session_state.calc_expr = ""
                st.session_state.calc_result = ""
            elif v == "⌫":
                st.session_state.calc_expr = st.session_state.calc_expr[:-1]
            elif v == "=":
                r = AppController.evaluate_expression(st.session_state.calc_expr)
                st.session_state.calc_result = r if r != "Error" else "⚠️ Error"
            else:
                st.session_state.calc_expr += str(v)

        rows = [["7","8","9","÷"],["4","5","6","×"],["1","2","3","−"],["C","0","=","+"],[".","(",")","%"],["⌫","^","√(","π"]]
        for row in rows:
            rc = st.columns(4)
            for ci, btn in enumerate(row):
                with rc[ci]:
                    if st.button(btn, key=f"calc_{btn}_{ci}", use_container_width=True):
                        _add_calc(btn); st.rerun()

    # ── Bookmarks panel ────────────────────────────
    if st.session_state.get("bookmarks_open"):
        st.markdown('<div class="section-label">🔖 Bookmarks</div>', unsafe_allow_html=True)
        if st.session_state.bookmarks:
            for i, bm in enumerate(st.session_state.bookmarks):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"<small>{bm[:80]}…</small>" if len(bm) > 80 else f"<small>{bm}</small>",
                                unsafe_allow_html=True)
                with c2:
                    if st.button("✕", key=f"rm_bm_{i}"):
                        st.session_state.bookmarks.pop(i); st.rerun()
        else:
            st.markdown('<small style="color:var(--text3)">No bookmarks yet. Use ⭐ on any message.</small>',
                        unsafe_allow_html=True)

    # ── Chat history panel ─────────────────────────
    if st.session_state.chat_history_open:
        st.markdown('<div class="section-label">📜 Chat History</div>', unsafe_allow_html=True)
        if st.session_state.messages:
            for msg in st.session_state.messages[-6:]:
                role_icon = "👤" if msg["role"] == "user" else "🎓"
                preview   = msg["content"][:60].replace("\n", " ")
                st.markdown(
                    f'<div style="font-size:.75rem;padding:5px 0;border-bottom:1px solid var(--border);">'
                    f'{role_icon} {preview}…</div>', unsafe_allow_html=True)
        else:
            st.markdown('<small style="color:var(--text3)">No conversation yet.</small>',
                        unsafe_allow_html=True)

    st.divider()

    # ── PDF Upload ─────────────────────────────────
    st.markdown('<div class="section-label">📄 PDF Upload</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload PDFs", type=["pdf"], accept_multiple_files=True,
        label_visibility="collapsed", key="pdf_uploader",
    )
    if uploaded_files:
        if st.button("📥 Load PDFs into Context", use_container_width=True):
            with st.spinner("Extracting text…"):
                loaded = 0
                for uf in uploaded_files:
                    uf.seek(0)
                    try:
                        stats = get_pdf_summary_stats(uf); uf.seek(0)
                        meta  = get_pdf_metadata(uf);      uf.seek(0)
                        text  = extract_text_from_pdf(uf)
                        if text.startswith("Error"):
                            st.error(f"❌ {uf.name}: {text}")
                            continue
                        label = meta.get("title") or uf.name
                        add_context(f"PDF: {label}\n\n{text}", label, "pdf")
                        loaded += 1
                        p = stats.get("pages","?"); w = stats.get("words",0)
                        st.success(f"📄 **{uf.name}** — {p} pages · {w:,} words")
                    except Exception as e:
                        st.error(f"❌ {uf.name}: {e}")
                if loaded:
                    st.success(f"✅ {loaded} PDF(s) loaded!")

    st.divider()

    # ── YouTube ────────────────────────────────────
    st.markdown('<div class="section-label">▶️ YouTube</div>', unsafe_allow_html=True)
    yt_url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=…",
                           label_visibility="collapsed", key="yt_input")
    if yt_url:
        if st.button("🎬 Load Transcript", use_container_width=True):
            with st.spinner("Fetching transcript…"):
                try:
                    transcript, vid_id = get_youtube_transcript(yt_url)
                    stats = get_transcript_stats(transcript)
                    ctx   = format_transcript_as_context(transcript, vid_id)
                    add_context(ctx, f"YT: {vid_id}", "youtube")
                    mins = stats.get("duration_minutes","?"); words = stats.get("word_count",0)
                    st.success(f"▶️ {mins} min · {words:,} words loaded!")
                except ValueError as e:
                    err = str(e).lower()
                    if "transcript" in err or "disabled" in err:
                        st.error("❌ No transcript available for this video.")
                    elif "video id" in err:
                        st.error("❌ Invalid YouTube URL.")
                    else:
                        st.error(f"❌ {e}")

    st.divider()

    # ── Web Scraper ────────────────────────────────
    st.markdown('<div class="section-label">🌐 Web Page</div>', unsafe_allow_html=True)
    web_url = st.text_input("URL", placeholder="https://en.wikipedia.org/wiki/…",
                            label_visibility="collapsed", key="web_input")
    if web_url:
        if st.button("🔗 Load Page", use_container_width=True):
            with st.spinner("Reading page…"):
                try:
                    page_text, page_title = scrape_web_page(web_url)
                    stats = get_web_stats(page_text, page_title)
                    ctx   = format_web_context(page_text, page_title, web_url)
                    add_context(ctx, page_title[:50], "web")
                    words = stats.get("word_count",0)
                    st.success(f"🌐 **{page_title[:38]}** — {words:,} words")
                except Exception as e:
                    st.error(f"❌ {e}")

    st.divider()

    # ── OCR Scanner ────────────────────────────────
    st.markdown('<div class="section-label">📸 Notes Scanner (OCR)</div>', unsafe_allow_html=True)
    scanned = st.file_uploader("Image", type=["png","jpg","jpeg"],
                               label_visibility="collapsed", key="ocr_up")
    if scanned:
        if st.button("🔍 Scan Text", use_container_width=True):
            with st.spinner("Extracting text…"):
                ocr_text = extract_text_from_image(scanned.read())
                if ocr_text.startswith("Error"):
                    st.error(ocr_text)
                else:
                    add_context(f"OCR: {scanned.name}\n\n{ocr_text}", scanned.name, "ocr")
                    st.success(f"✅ {len(ocr_text.split())} words extracted!")

    st.divider()

    # ── Active Context ─────────────────────────────
    if st.session_state.context_sources:
        st.markdown('<div class="section-label">📎 Active Context</div>', unsafe_allow_html=True)
        icons = {"pdf":"📄","youtube":"▶️","web":"🌐","ocr":"📸"}
        chips = "".join([
            f'<span class="source-chip"><span class="chip-dot"></span>{icons.get(s["type"],"📎")} {s["label"][:28]}</span>'
            for s in st.session_state.context_sources
        ])
        st.markdown(f'<div style="margin-bottom:.5rem">{chips}</div>', unsafe_allow_html=True)

        # Context AI summary
        ctx_hash = hash(st.session_state.context_text)
        if st.session_state.last_context_hash != ctx_hash:
            with st.spinner("Summarising…"):
                try:
                    summary_msgs = [
                        {"role":"system","content":"Summarise in exactly 3 bullet points with emojis. Max 20 words each. Be concise."},
                        {"role":"user","content": st.session_state.context_text[:5000]},
                    ]
                    st.session_state.last_context_summary = chat_with_groq(
                        summary_msgs, model="llama-3.1-8b-instant")
                    st.session_state.last_context_hash = ctx_hash
                except Exception:
                    st.session_state.last_context_summary = "📚 Material loaded and ready."

        if st.session_state.last_context_summary:
            st.markdown(
                f'<div style="font-size:.74rem;color:var(--text3);line-height:1.5;background:var(--bg3);'
                f'padding:9px 12px;border-radius:8px;border-left:3px solid var(--accent);">'
                f'{st.session_state.last_context_summary}</div>',
                unsafe_allow_html=True)

        if st.button("🗑️ Clear All Context", use_container_width=True):
            clear_context(); st.rerun()

    st.divider()

    # ── Academic Goals ─────────────────────────────
    st.markdown('<div class="section-label">🎯 Academic Goals</div>', unsafe_allow_html=True)
    new_goal = st.text_input("Goal", placeholder="+ New goal…", label_visibility="collapsed", key="goal_in")
    if new_goal and st.button("Add Goal", use_container_width=True):
        st.session_state.study_goals.append({"text": new_goal, "done": False}); st.rerun()
    for i, g in enumerate(st.session_state.study_goals):
        checked = st.checkbox(g["text"], value=g["done"], key=f"goal_{i}")
        if checked != g["done"]:
            st.session_state.study_goals[i]["done"] = checked

    st.divider()

    # ── Exam Countdown ─────────────────────────────
    st.markdown('<div class="section-label">🗓️ Exam Countdown</div>', unsafe_allow_html=True)
    col_e1, col_e2 = st.columns([2,1])
    with col_e1:
        st.session_state.exam_date = st.date_input(
            "Date", value=st.session_state.exam_date, label_visibility="collapsed")
    with col_e2:
        days_left = (st.session_state.exam_date - datetime.date.today()).days
        color = "var(--green)" if days_left > 14 else "var(--accent)" if days_left > 3 else "var(--red)"
        st.markdown(
            f'<div style="text-align:center;font-weight:800;color:{color};font-size:1.1rem;padding-top:4px;">'
            f'{max(0,days_left)}d</div>', unsafe_allow_html=True)

    st.divider()

    # ── Mastery Tracker ────────────────────────────
    _mastery = {}
    if st.session_state.get("card_mastery"):
        passed = sum(1 for v in st.session_state.card_mastery.values() if v == "pass")
        total_c = len(st.session_state.card_mastery)
        if total_c > 0: _mastery["Recall"] = int((passed/total_c)*100)
    if st.session_state.get("quiz_score") and st.session_state.get("quiz_data"):
        _mastery["Comprehension"] = int((st.session_state.quiz_score / max(1, len(st.session_state.quiz_data))) * 100)
    if _mastery:
        st.markdown('<div class="section-label">📈 Mastery</div>', unsafe_allow_html=True)
        radar = get_subject_mastery_radar(_mastery)
        if radar:
            st.plotly_chart(radar, use_container_width=True, config={"displayModeBar":False})

    st.divider()

    # ── Session Save/Load ──────────────────────────
    st.markdown('<div class="section-label">📁 Study Sessions</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        sess_name = st.text_input("Save As", placeholder="Chapter 4…", label_visibility="collapsed")
        if st.button("💾 Save", use_container_width=True):
            if sess_name and st.session_state.messages:
                st.session_state.persistent_sessions[sess_name] = {
                    "messages": st.session_state.messages.copy(),
                    "context": st.session_state.context_text,
                    "sources": st.session_state.context_sources.copy(),
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                try:
                    with open("sessions.json","w") as f:
                        json.dump(st.session_state.persistent_sessions, f)
                    st.success("Saved!")
                except Exception:
                    st.warning("Saved in memory only.")
    with c4:
        sessions = list(st.session_state.persistent_sessions.keys())
        if sessions:
            load_name = st.selectbox("Load", sessions, label_visibility="collapsed")
            cl1, cl2 = st.columns(2)
            with cl1:
                if st.button("📂", use_container_width=True):
                    d = st.session_state.persistent_sessions[load_name]
                    st.session_state.messages      = d["messages"]
                    st.session_state.context_text  = d["context"]
                    st.session_state.context_sources = d["sources"]
                    st.rerun()
            with cl2:
                if st.button("🗑️", use_container_width=True):
                    del st.session_state.persistent_sessions[load_name]
                    try:
                        with open("sessions.json","w") as f:
                            json.dump(st.session_state.persistent_sessions, f)
                    except Exception: pass
                    st.rerun()
        else:
            if st.button("➕ New Session", use_container_width=True):
                st.session_state.messages = []; st.rerun()

    st.divider()

    # ── Export / New Chat ──────────────────────────
    st.markdown('<div class="section-label">⚙️ Actions</div>', unsafe_allow_html=True)
    ca1, ca2 = st.columns(2)
    with ca1:
        if st.session_state.messages:
            st.download_button(
                "⬇️ Export",
                data=export_chat_history(),
                file_name=f"examhelp_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown", use_container_width=True,
            )
    with ca2:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.total_output_chars = 0
            st.session_state.total_output_lines = 0
            st.session_state.total_tokens_used  = 0
            clear_context()
            st.rerun()

    st.divider()

    # ── Admin: API Key Health Table ────────────────
    with st.expander("🔧 API Key Dashboard"):
        cap = key_manager.get_total_capacity()
        st.markdown(
            f"**{cap['keys_available']}/{cap['keys_total']}** keys active · "
            f"**{cap['rpd_used']:,}/{cap['rpd_capacity']:,}** req/day used")
        rows = key_manager.status_table()
        for r in rows:
            badge_cls = ("badge-green" if "🟢" in r["status"]
                         else "badge-yellow" if "🟡" in r["status"] or "🟠" in r["status"]
                         else "badge-red")
            st.markdown(
                f'<div class="key-row">'
                f'<span style="color:var(--text);font-weight:500;">{r["key"]}</span>'
                f'<span class="{badge_cls}">{r["status"]}</span>'
                f'</div>', unsafe_allow_html=True)
        if st.button("🔄 Reset All Cooldowns", use_container_width=True):
            key_manager.reset_all_cooldowns()
            from utils import gemini_key_manager as gkm
            gkm.reset_all_cooldowns()
            st.success("✅ All cooldowns cleared!")

    # ── Study Toolbox ──────────────────────────────
    st.markdown('<div class="section-label">🛠️ Study Toolbox</div>', unsafe_allow_html=True)
    _tools = [
        ("🃏", "Flashcards",    "Generate Q&A deck",       "flashcards"),
        ("📝", "Quiz Mode",     "MCQ assessment",           "quiz"),
        ("📊", "Mind Map",      "Visual concept map",       "mindmap"),
        ("📅", "Study Planner", "Revision timetable",      "planner"),
        ("📈", "Graph Plotter", "Plot equations",           "graph"),
        ("💬", "Chat",         "Standard AI study chat",   "chat"),
    ]
    for icon, name, desc, mode in _tools:
        col_icon, col_info, col_btn = st.columns([1, 4, 2])
        with col_icon:
            st.markdown(f'<div style="font-size:1.2rem;padding-top:8px;">{icon}</div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(
                f'<div style="font-size:.84rem;font-weight:600;color:var(--text);">{name}</div>'
                f'<div style="font-size:.7rem;color:var(--text3);">{desc}</div>',
                unsafe_allow_html=True)
        with col_btn:
            if st.button("Open", key=f"tool_{mode}", use_container_width=True):
                st.session_state.app_mode = mode
                st.rerun()

    st.markdown('<div class="poweredby">Powered by <span>Groq</span> · <span>Gemini</span> · <span>LLaMA</span></div>',
                unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
persona     = get_persona_by_name(st.session_state.selected_persona)
persona_tag = ""
if persona and st.session_state.selected_persona != "Default (ExamHelp)":
    persona_tag = f' · <span style="color:var(--accent);font-weight:600;">{persona["emoji"]} {persona["name"]}</span>'

st.markdown(f"""
<div style="padding:1.5rem 0 .5rem; border-bottom:1px solid var(--border); margin-bottom:1rem;">
  <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">
    <div style="font-size:1.4rem;font-weight:800;color:var(--text);letter-spacing:-.5px;">ExamHelp</div>
    <div style="font-size:.78rem;color:var(--text3);">AI Study Companion{persona_tag}</div>
  </div>
</div>""", unsafe_allow_html=True)

if st.session_state.focus_mode:
    st.markdown('<div class="focus-banner">🔒 Focus Mode Active — All distractions suppressed. Deep work in progress.</div>',
                unsafe_allow_html=True)

if st.session_state.context_sources:
    icons = {"pdf":"📄","youtube":"▶️","web":"🌐","ocr":"📸"}
    chips = " ".join([
        f'<span class="source-chip"><span class="chip-dot"></span>{icons.get(s["type"],"📎")} {s["label"][:28]}</span>'
        for s in st.session_state.context_sources
    ])
    st.markdown(f'<div class="study-banner"><span class="study-banner-label">Studying →</span>{chips}</div>',
                unsafe_allow_html=True)

app_mode = st.session_state.get("app_mode", "chat")

# ─────────────────────────────────────────────
# FLASHCARD MODE
# ─────────────────────────────────────────────
if app_mode == "flashcards":
    st.subheader("🃏 Flashcard Generator")
    lang = st.session_state.get("selected_language","English")

    if not st.session_state.context_text:
        st.warning("📄 Upload study material first to generate flashcards.")
    else:
        col_gen, col_cnt = st.columns([3,1])
        with col_gen:
            if st.button("🪄 Generate Flashcards", use_container_width=True):
                with st.spinner(f"Creating {lang} deck…"):
                    cards = AppController.generate_flashcards(
                        st.session_state.context_text, lang, _get_override_key())
                    if cards:
                        st.session_state.flashcards   = cards
                        st.session_state.current_card = 0
                        st.session_state.card_mastery = {}
                        st.rerun()
                    else:
                        st.error("⚠️ Generation failed. Check your API keys.")
        with col_cnt:
            if st.session_state.flashcards:
                st.markdown(
                    f'<div style="text-align:center;font-size:.8rem;color:var(--text3);padding-top:8px;">'
                    f'{len(st.session_state.flashcards)} cards</div>',
                    unsafe_allow_html=True)

        if st.session_state.flashcards:
            cards = st.session_state.flashcards
            idx   = st.session_state.current_card

            if idx >= len(cards):
                # Mastery summary
                mastery    = st.session_state.get("card_mastery", {})
                passes     = sum(1 for v in mastery.values() if v == "pass")
                score_pct  = int(passes / len(cards) * 100)
                if score_pct >= 80:
                    emoji = "🌟"
                elif score_pct >= 60:
                    emoji = "👍"
                else:
                    emoji = "📖"

                st.success(f"### {emoji} Deck Complete! **{passes}/{len(cards)}** correct ({score_pct}%)")
                if px and len(mastery) > 0:
                    fig = px.pie(
                        values=[passes, len(cards)-passes],
                        names=["✅ Pass","❌ Review"],
                        hole=0.55,
                        color_discrete_sequence=["#4ade80","#f87171"],
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="var(--text)" if st.session_state.theme_mode == "dark" else "#1c1917",
                        margin=dict(t=10,b=10,l=10,r=10),
                        showlegend=True,
                        legend=dict(orientation="h",yanchor="bottom",y=-0.25),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

                ca, cb = st.columns(2)
                with ca:
                    if st.button("🔁 Retry Missed", use_container_width=True):
                        missed = [c for i,c in enumerate(cards) if mastery.get(i) != "pass"]
                        st.session_state.flashcards   = missed if missed else cards
                        st.session_state.current_card = 0
                        st.session_state.card_mastery = {}
                        st.rerun()
                with cb:
                    if st.button("🔄 Restart All", use_container_width=True):
                        st.session_state.current_card = 0
                        st.session_state.card_mastery = {}
                        st.rerun()
            else:
                card = cards[idx]
                progress_pct = int(idx / len(cards) * 100)
                st.markdown(
                    f'<div class="prog-wrap"><div class="prog-label">'
                    f'<span>Card {idx+1}/{len(cards)}</span><span>{progress_pct}%</span></div>'
                    f'<div class="prog-bar"><div class="prog-fill" style="width:{progress_pct}%;"></div></div></div>',
                    unsafe_allow_html=True)

                difficulty = card.get("difficulty","medium")
                diff_color = {"easy":"var(--green)","medium":"var(--accent)","hard":"var(--red)"}.get(difficulty,"var(--text3)")
                subject    = card.get("subject","")

                st.markdown(
                    f'<div style="display:flex;gap:8px;margin-bottom:.6rem;">'
                    f'<span style="font-size:.72rem;background:var(--bg3);border:1px solid var(--border);'
                    f'border-radius:8px;padding:2px 10px;color:var(--text3);">{subject}</span>'
                    f'<span style="font-size:.72rem;background:var(--bg3);border:1px solid var(--border);'
                    f'border-radius:8px;padding:2px 10px;color:{diff_color};">{difficulty}</span></div>',
                    unsafe_allow_html=True)

                # Show Q, reveal A on toggle
                flip_key = f"flip_{idx}"
                if flip_key not in st.session_state: st.session_state[flip_key] = False

                q_text = card.get("q","Question not found")
                a_text = card.get("a","Answer not found")

                st.markdown(
                    f'<div class="flashcard"><div style="font-size:1rem;font-weight:600;">'
                    f'❓ {q_text}</div></div>', unsafe_allow_html=True)

                if st.session_state[flip_key]:
                    st.markdown(
                        f'<div class="flashcard" style="margin-top:.5rem;border-color:var(--accent-bd);">'
                        f'<div style="font-size:.95rem;">💡 {a_text}</div></div>',
                        unsafe_allow_html=True)

                flip_col, pass_col, fail_col = st.columns(3)
                with flip_col:
                    if st.button("👁️ Reveal Answer", use_container_width=True, key=f"flip_btn_{idx}"):
                        st.session_state[flip_key] = not st.session_state[flip_key]; st.rerun()
                with pass_col:
                    if st.button("✅ Got It", use_container_width=True, key=f"pass_{idx}"):
                        st.session_state.card_mastery[idx] = "pass"
                        st.session_state[flip_key] = False
                        st.session_state.current_card += 1; st.rerun()
                with fail_col:
                    if st.button("❌ Review", use_container_width=True, key=f"fail_{idx}"):
                        st.session_state.card_mastery[idx] = "fail"
                        st.session_state[flip_key] = False
                        st.session_state.current_card += 1; st.rerun()

# ─────────────────────────────────────────────
# QUIZ MODE
# ─────────────────────────────────────────────
elif app_mode == "quiz":
    st.subheader("📝 Smart Quiz Mode")
    lang = st.session_state.get("selected_language","English")

    if not st.session_state.context_text:
        st.warning("📄 Upload study material first to generate a quiz.")
    else:
        if not st.session_state.quiz_data:
            if st.button("🪄 Generate Quiz (5 Questions)", use_container_width=True):
                with st.spinner("Creating quiz…"):
                    q = AppController.generate_quiz(
                        st.session_state.context_text, lang, _get_override_key())
                    if q:
                        st.session_state.quiz_data    = q
                        st.session_state.quiz_current = 0
                        st.session_state.quiz_score   = 0
                        st.session_state.quiz_feedback = None
                        st.rerun()
                    else:
                        st.error("⚠️ Quiz generation failed.")
        else:
            quiz = st.session_state.quiz_data
            qi   = st.session_state.quiz_current

            if qi >= len(quiz):
                # Score screen
                score_pct = int(st.session_state.quiz_score / len(quiz) * 100)
                if score_pct >= 80: grade, gcolor = "A 🌟", "var(--green)"
                elif score_pct >= 60: grade, gcolor = "B 👍", "var(--accent)"
                else: grade, gcolor = "C 📖", "var(--red)"

                st.markdown(
                    f'<div style="text-align:center;padding:2rem;">'
                    f'<div style="font-size:3rem;">{grade.split()[1]}</div>'
                    f'<div style="font-size:2rem;font-weight:800;color:{gcolor};">{score_pct}%</div>'
                    f'<div style="color:var(--text2);margin-top:.5rem;">'
                    f'{st.session_state.quiz_score}/{len(quiz)} correct</div></div>',
                    unsafe_allow_html=True)

                if st.button("🔄 Try Again", use_container_width=True):
                    st.session_state.quiz_current = 0
                    st.session_state.quiz_score   = 0
                    st.session_state.quiz_data    = []
                    st.session_state.quiz_feedback = None
                    st.rerun()
            else:
                q_item = quiz[qi]
                q_text = q_item.get("q","")
                opts   = q_item.get("options", [])
                correct = q_item.get("correct","")
                expl   = q_item.get("explanation","")

                st.markdown(
                    f'<div class="prog-wrap"><div class="prog-label">'
                    f'<span>Q {qi+1}/{len(quiz)}</span>'
                    f'<span>Score: {st.session_state.quiz_score}/{qi}</span></div>'
                    f'<div class="prog-bar"><div class="prog-fill" style="width:{qi/len(quiz)*100:.0f}%;"></div></div></div>',
                    unsafe_allow_html=True)

                st.markdown(f"**{qi+1}. {q_text}**")

                if st.session_state.quiz_feedback is None:
                    for j, opt in enumerate(opts):
                        if st.button(opt, key=f"opt_{qi}_{j}", use_container_width=True):
                            is_correct = (opt == correct or opt.lstrip("ABCD. ") == correct.lstrip("ABCD. "))
                            if is_correct:
                                st.session_state.quiz_score += 1
                                st.session_state.quiz_feedback = ("✅ Correct!", "green", expl)
                            else:
                                st.session_state.quiz_feedback = (f"❌ Wrong — Correct: **{correct}**", "red", expl)
                            st.rerun()
                else:
                    msg, color, exp = st.session_state.quiz_feedback
                    color_map = {"green":"var(--green)","red":"var(--red)"}
                    st.markdown(
                        f'<div style="color:{color_map.get(color,"var(--text)")};font-weight:600;'
                        f'padding:.7rem;background:var(--bg3);border-radius:8px;margin:.5rem 0;">{msg}</div>',
                        unsafe_allow_html=True)
                    if exp:
                        st.markdown(f"💡 *{exp}*")
                    if st.button("Next Question →", use_container_width=True):
                        st.session_state.quiz_current += 1
                        st.session_state.quiz_feedback = None
                        st.rerun()

# ─────────────────────────────────────────────
# MIND MAP MODE
# ─────────────────────────────────────────────
elif app_mode == "mindmap":
    st.subheader("📊 Mind Map Generator")
    if not st.session_state.context_text:
        st.warning("📄 Upload study material to generate a mind map.")
    else:
        if st.button("🪄 Generate Mind Map", use_container_width=True):
            with st.spinner("Building concept map…"):
                try:
                    msgs = [
                        {"role":"system","content":"Generate a Mermaid.js mind map (mindmap syntax). Return ONLY the raw Mermaid code block. No explanation."},
                        {"role":"user","content": f"Create a mind map for:\n{st.session_state.context_text[:8000]}"},
                    ]
                    mm_code = chat_with_groq(msgs, model="llama-3.3-70b-versatile")
                    # Extract code block
                    m = re.search(r"```(?:mermaid)?\n(.+?)```", mm_code, re.DOTALL)
                    if m: mm_code = m.group(1).strip()
                    st.session_state["last_mindmap"] = mm_code
                except Exception as e:
                    st.error(f"❌ {e}")

        if st.session_state.get("last_mindmap"):
            st.code(st.session_state["last_mindmap"], language="mermaid")
            st.info("💡 Copy the code above and paste it into [Mermaid Live Editor](https://mermaid.live) to view the visual map.")
            st.download_button("📥 Download .mmd", st.session_state["last_mindmap"],
                               file_name="mindmap.mmd", mime="text/plain")

# ─────────────────────────────────────────────
# STUDY PLANNER MODE
# ─────────────────────────────────────────────
elif app_mode == "planner":
    st.subheader("📅 Study Planner")
    lang = st.session_state.get("selected_language","English")

    if not st.session_state.context_text:
        st.warning("📄 Upload study material to generate a plan.")
    else:
        num_days = st.slider("Days to study", 3, 30, 7)
        if st.button("🪄 Generate Study Plan", use_container_width=True):
            with st.spinner("Building personalised plan…"):
                tasks = AppController.generate_study_schedule(
                    st.session_state.context_text, num_days, lang, _get_override_key())
                if tasks:
                    st.session_state.study_tasks = tasks
                else:
                    st.error("⚠️ Plan generation failed. Try again.")

        if st.session_state.study_tasks:
            tasks = st.session_state.study_tasks
            # Summary stats
            total_mins = sum(t.get("estimated_minutes",30) for t in tasks)
            done_count = sum(1 for t in tasks if t.get("done"))
            st.markdown(
                f'<div class="stat-row">'
                f'<div class="stat-box"><div class="stat-val">{len(tasks)}</div><div class="stat-lbl">Tasks</div></div>'
                f'<div class="stat-box"><div class="stat-val">{done_count}</div><div class="stat-lbl">Done</div></div>'
                f'<div class="stat-box"><div class="stat-val">{total_mins//60}h{total_mins%60}m</div><div class="stat-lbl">Total</div></div>'
                f'</div>', unsafe_allow_html=True)

            # Priority filter
            filter_p = st.selectbox("Filter by priority", ["All","high","medium","low"], label_visibility="collapsed")
            filtered = [t for t in tasks if filter_p == "All" or t.get("priority") == filter_p]

            for i, task in enumerate(filtered):
                pcolor = {"high":"var(--red)","medium":"var(--accent)","low":"var(--green)"}.get(task.get("priority","medium"),"var(--text3)")
                is_done = task.get("done", False)
                strike  = "text-decoration:line-through;opacity:.5;" if is_done else ""

                c1, c2, c3 = st.columns([1,7,2])
                with c1:
                    if st.checkbox("", value=is_done, key=f"task_done_{i}"):
                        # Find original index
                        orig_idx = tasks.index(task) if task in tasks else i
                        st.session_state.study_tasks[orig_idx]["done"] = True
                    else:
                        orig_idx = tasks.index(task) if task in tasks else i
                        st.session_state.study_tasks[orig_idx]["done"] = False
                with c2:
                    st.markdown(
                        f'<div style="{strike}font-size:.88rem;font-weight:500;color:var(--text);">{task["task"]}</div>'
                        f'<div style="font-size:.72rem;color:var(--text3);">{task.get("topic","")} · {task.get("estimated_minutes",30)}min · '
                        f'<span style="color:{pcolor};">{task.get("priority","medium")}</span></div>',
                        unsafe_allow_html=True)
                with c3:
                    st.markdown(
                        f'<div style="font-size:.7rem;color:var(--text3);text-align:right;padding-top:4px;">'
                        f'📅 {task.get("deadline","")}</div>', unsafe_allow_html=True)

            # Gantt chart
            if go and pd and len(tasks) > 0:
                with st.expander("📊 Gantt Chart"):
                    try:
                        gantt_data = []
                        for t in tasks[:15]:
                            dl = t.get("deadline", datetime.date.today().isoformat())
                            start_d = (datetime.datetime.fromisoformat(dl) - datetime.timedelta(hours=t.get("estimated_minutes",30)/60)).isoformat()
                            gantt_data.append(dict(Task=t["task"][:30], Start=start_d, Finish=dl,
                                                   Priority=t.get("priority","medium")))
                        df_g = pd.DataFrame(gantt_data)
                        fig  = px.timeline(df_g, x_start="Start", x_end="Finish", y="Task", color="Priority",
                                           color_discrete_map={"high":"#f87171","medium":"#fbbf24","low":"#4ade80"})
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                          margin=dict(t=10,b=10,l=10,r=10), height=300)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
                    except Exception:
                        pass

# ─────────────────────────────────────────────
# GRAPH MODE
# ─────────────────────────────────────────────
elif app_mode == "graph":
    st.subheader("📈 Graph Plotter")
    st.markdown("Enter mathematical expressions to visualise them:")

    expr_input = st.text_input(
        "Expression", placeholder="sin(x), x**2 + 2*x - 1, exp(-x)*cos(2*x)",
        label_visibility="collapsed")
    xmin, xmax = st.columns(2)
    with xmin: x_min = st.number_input("x min", value=-10.0, key="gx_min")
    with xmax: x_max = st.number_input("x max", value=10.0, key="gx_max")

    if expr_input and go:
        try:
            import numpy as np
            exprs = [e.strip() for e in expr_input.split(",")]
            fig   = go.Figure()
            x     = np.linspace(x_min, x_max, 500)
            colors = ["#f59e0b","#60a5fa","#4ade80","#f87171","#c084fc"]

            for j, expr in enumerate(exprs[:5]):
                safe = expr.replace("^","**")
                ns   = {"x":x,"sin":np.sin,"cos":np.cos,"tan":np.tan,
                        "exp":np.exp,"log":np.log,"sqrt":np.sqrt,"abs":np.abs,
                        "pi":np.pi,"e":np.e}
                y = eval(safe, {"__builtins__":{}}, ns)
                fig.add_trace(go.Scatter(x=x, y=y, name=expr, line=dict(color=colors[j%len(colors)], width=2.5)))

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="rgba(100,100,100,.2)", zeroline=True, zerolinecolor="rgba(200,200,200,.3)"),
                yaxis=dict(gridcolor="rgba(100,100,100,.2)", zeroline=True, zerolinecolor="rgba(200,200,200,.3)"),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=20,b=20,l=20,r=20), height=420,
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Could not plot: {e}")
    elif not go:
        st.warning("Plotly not installed. Run: `pip install plotly`")

    if st.button("💬 Back to Chat", use_container_width=True):
        st.session_state.app_mode = "chat"; st.rerun()

# ─────────────────────────────────────────────
# CHAT MODE (default)
# ─────────────────────────────────────────────
else:
    # ── Empty state ────────────────────────────────
    if not st.session_state.messages:
        from utils.query_engine import QueryEngine
        st.markdown("""
        <div class="hero-wrap">
          <div class="hero-badge">⚡ Powered by Groq + Gemini — Ultra-Fast AI</div>
          <div class="hero-title">Study smarter with <em>AI</em></div>
          <div class="hero-sub">
            Upload a PDF, paste a YouTube link, or ask any academic question.
            Get expert explanations, flashcards, quizzes, and more.
          </div>
        </div>""", unsafe_allow_html=True)

        QUICK_PROMPTS = [
            "📖 Summarise my uploaded material",
            "🃏 Generate 10 flashcards",
            "📝 Quiz me on this topic",
            "📊 Create a mind map",
            "📅 Build my study plan",
            "💡 Explain from first principles",
            "🧮 Solve a math problem",
            "🌐 Explain a real-world application",
        ]
        cols = st.columns(4)
        for i, prompt in enumerate(QUICK_PROMPTS):
            with cols[i % 4]:
                if st.button(prompt, key=f"qp_{i}", use_container_width=True):
                    st.session_state.queued_prompt = prompt.split(" ",1)[1]
                    st.rerun()

    # ── Chat history ───────────────────────────────
    for i, msg in enumerate(st.session_state.messages):
        is_user = msg["role"] == "user"
        avatar  = "👤" if is_user else (persona["emoji"] if persona and st.session_state.selected_persona != "Default (ExamHelp)" else "🎓")

        with st.chat_message(msg["role"], avatar=avatar):
            if is_user:
                st.markdown(f'<span class="user-msg-hook" style="display:none"></span>', unsafe_allow_html=True)
            st.markdown(msg["content"])

            # Actions row
            if not is_user:
                ac1, ac2, ac3, ac4 = st.columns([1,1,1,5])
                with ac1:
                    if st.button("📋", key=f"copy_{i}", help="Copy"):
                        st.toast("Copied to clipboard!")
                with ac2:
                    if st.button("⭐", key=f"bm_{i}", help="Bookmark"):
                        st.session_state.bookmarks.append(msg["content"][:200])
                        st.toast("Bookmarked!")
                with ac3:
                    if st.button("🔊", key=f"speak_{i}", help="Read aloud"):
                        AppController.speak(msg["content"][:600])
                        st.toast("Playing…")

    # ── Voice input ────────────────────────────────
    try:
        audio_val = st.audio_input("🎙️ Record question", label_visibility="collapsed")
    except Exception:
        audio_val = None

    if audio_val and audio_val != st.session_state.get("last_audio"):
        st.session_state.last_audio = audio_val
        with st.spinner("Transcribing…"):
            try:
                audio_bytes = audio_val.read()
                if audio_bytes:
                    transcript = transcribe_audio(audio_bytes, override_key=_get_override_key())
                    if isinstance(transcript, str) and transcript.strip():
                        st.session_state.queued_prompt = transcript
                        st.rerun()
            except Exception as e:
                st.error(f"Voice error: {e}")

    user_input = st.chat_input("Ask anything about your study material…", key="chat_input")
    txt_low    = user_input.lower() if user_input else ""

    if st.session_state.queued_prompt:
        user_input = st.session_state.queued_prompt
        txt_low    = user_input.lower()
        st.session_state.queued_prompt = None

    # ── Smart triggers ─────────────────────────────
    if user_input and any(user_input.lower().startswith(kw) for kw in ["calculate ","calc ","compute ","solve "]):
        expr = re.sub(r"^(calculate|calc|compute|solve)\s+","",user_input,flags=re.IGNORECASE).strip()
        res  = AppController.evaluate_expression(expr)
        if res and res != "Error":
            st.session_state.messages.append({"role":"user","content":f"Calculate: `{expr}`"})
            st.session_state.messages.append({"role":"assistant","content":
                f"🧮 **Calculation Result:**\n\n`{expr}` = **{res}**\n\n💡 Use the 🧮 calculator in the toolbar for continuous equations."})
            st.rerun()

    elif user_input and any(user_input.lower().startswith(kw) for kw in ["plot ","graph ","draw graph "]):
        st.session_state.app_mode = "graph"
        st.session_state.messages.append({"role":"user","content":user_input})
        st.session_state.messages.append({"role":"assistant","content":"📈 **Graph Plotter Activated**\n\nEnter your expression in the graph workspace."})
        st.rerun()

    elif user_input and any(kw in user_input.lower() for kw in ["open quiz","start quiz","quiz me"]):
        st.session_state.app_mode = "quiz"
        st.session_state.messages.append({"role":"user","content":user_input})
        st.session_state.messages.append({"role":"assistant","content":"📝 **Quiz Mode Activated** — switching workspace."})
        st.rerun()

    elif user_input and any(kw in user_input.lower() for kw in ["open planner","study plan","study planner"]):
        st.session_state.app_mode = "planner"
        st.session_state.messages.append({"role":"user","content":user_input})
        st.session_state.messages.append({"role":"assistant","content":"📅 **Study Planner Activated** — generating your plan."})
        st.rerun()

    elif user_input and any(kw in txt_low for kw in ["mindmap","mind map","concept map"]):
        st.session_state.app_mode = "mindmap"
        st.session_state.messages.append({"role":"user","content":user_input})
        st.session_state.messages.append({"role":"assistant","content":"📊 **Mind Map Generator Activated.**"})
        st.rerun()

    # ── Main query processing ──────────────────────
    elif user_input:
        override   = _get_override_key()
        active_key = key_manager.get_key(override=override)

        if not active_key:
            st.error("⚠️ No API key available. Add a Groq key in the sidebar (🔑 Override API Key).", icon="🔑")
            st.stop()

        from utils.query_engine import QueryEngine

        st.session_state.messages.append({"role":"user","content":user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<span class="user-msg-hook" style="display:none"></span>', unsafe_allow_html=True)
            st.markdown(user_input)

        try:
            augmented_prompt, matched_sources, intent = QueryEngine.route_and_enrich(
                user_input, st.session_state.get("context_text",""))
        except Exception:
            augmented_prompt = user_input
            matched_sources  = []
            intent           = "complex"

        assistant_avatar = persona["emoji"] if (persona and st.session_state.selected_persona != "Default (ExamHelp)") else "🎓"

        with st.chat_message("assistant", avatar=assistant_avatar):
            placeholder   = st.empty()
            full_response = ""
            success       = False

            history = [{"role":m["role"],"content":m["content"]} for m in st.session_state.messages[-12:]]
            history[-1]["content"] = augmented_prompt  # Silently enrich prompt

            # Persona prompt
            persona_prompt = ""
            if persona and st.session_state.selected_persona != "Default (ExamHelp)":
                persona_prompt = build_persona_prompt(persona, language=st.session_state.get("selected_language","English"))
            elif st.session_state.get("selected_language","English") != "English":
                lang = st.session_state.selected_language
                persona_prompt = f"\n\nCRITICAL: Answer STRICTLY in {lang}. All explanations, headers, bullets in {lang}."

            chosen_model = st.session_state.get("model_choice","llama-3.3-70b-versatile")

            # ── TIER 1: Groq (all keys, internal rotation) ──
            try:
                for chunk in stream_chat_with_groq(
                    history,
                    st.session_state.context_text,
                    override_key=override,
                    model=chosen_model,
                    persona_prompt=persona_prompt,
                ):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                success = True
                count_output_stats(full_response)

            except Exception as groq_err:
                # ── TIER 2: Gemini (all keys, internal rotation) ──
                full_response = ""
                try:
                    from ai.gemini_client import stream_chat_with_gemini
                    placeholder.info("⚡ Switching to Gemini backup…", icon="🔄")
                    for chunk in stream_chat_with_gemini(
                        history,
                        context_text=st.session_state.context_text,
                        persona_prompt=persona_prompt,
                    ):
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                    success = True
                    count_output_stats(full_response)

                except Exception as gemini_err:
                    # ── TIER 3: Force-reset cooldowns + retry Groq with fast models ──
                    full_response = ""
                    try:
                        from utils import gemini_key_manager as gkm
                        key_manager.reset_all_cooldowns()
                        gkm.reset_all_cooldowns()
                        placeholder.info("🔄 Resetting key pool and retrying…", icon="⏳")
                        # Try scout model first (high TPD capacity), then 8B
                        for fallback_model in ("llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"):
                            if success:
                                break
                            try:
                                for chunk in stream_chat_with_groq(
                                    history,
                                    st.session_state.context_text,
                                    persona_prompt=persona_prompt,
                                    model=fallback_model,
                                ):
                                    full_response += chunk
                                    placeholder.markdown(full_response + "▌")
                                if full_response:
                                    placeholder.markdown(full_response)
                                    success = True
                                    count_output_stats(full_response)
                            except Exception:
                                full_response = ""
                    except Exception:
                        pass

                    # ── TIER 4: Gemini retry after cooldown reset ──
                    if not success or not full_response:
                        full_response = ""
                        try:
                            from ai.gemini_client import stream_chat_with_gemini
                            from utils import gemini_key_manager as gkm
                            gkm.reset_all_cooldowns()
                            placeholder.info("🔁 Final retry with backup engines…", icon="🛡️")
                            for chunk in stream_chat_with_gemini(
                                history,
                                context_text=st.session_state.context_text,
                                persona_prompt=persona_prompt,
                            ):
                                full_response += chunk
                                placeholder.markdown(full_response + "▌")
                            placeholder.markdown(full_response)
                            success = True
                            count_output_stats(full_response)
                        except Exception:
                            pass

            if not success or not full_response:
                full_response = "⚠️ All AI engines are temporarily at capacity. Please tap **Send** again — keys refresh every 60 seconds and your next message will go through instantly."
                placeholder.warning(full_response)

        # ── Post-processing: Tabbed viewer ─────────────────────
        st.divider()

        from ai.reasoning_engine import humanize_text

        images, caption, cleaned_text = [], "", full_response
        if "VISUAL_MANIFEST:" in full_response:
            try:
                from ai.image_engine import process_visual_request
                images, caption, cleaned_text = process_visual_request(full_response)
            except Exception:
                cleaned_text = full_response

        tab_exp, tab_res, tab_lab, tab_share = st.tabs(["🎓 Explanation","📚 Resources","🛠️ Study Lab","🔗 Share"])

        with tab_exp:
            st.markdown(cleaned_text)
            # Inline math rendering hint
            if any(sym in cleaned_text for sym in ["$$","\\(","\\["]):
                st.info("💡 This response contains LaTeX math. It renders automatically in Streamlit.")

        with tab_res:
            if images:
                st.markdown(f"#### 🖼️ {caption}")
                img_cols = st.columns(min(len(images),3))
                for ci, img in enumerate(images[:3]):
                    with img_cols[ci]:
                        st.image(img, use_container_width=True)
                st.divider()
            st.markdown("#### 🔗 References")
            if matched_sources:
                for s in matched_sources[:5]:
                    label = s.split("//")[-1][:40] if "//" in s else s[:40]
                    st.markdown(f"- [{label}…]({s})")
            else:
                st.info("Direct AI knowledge used — no external links required.")

        with tab_lab:
            st.markdown("#### 📥 Export Study Material")
            from utils.study_generator import StudyGenerator
            col_pdf, col_doc, col_ppt = st.columns(3)
            with col_pdf:
                try:
                    pdf_data = StudyGenerator.generate_pdf("Study Guide", cleaned_text)
                    st.download_button("📄 PDF Guide", pdf_data,
                                       file_name="ExamHelp_Study.pdf", use_container_width=True)
                except Exception:
                    st.button("📄 PDF (unavailable)", disabled=True, use_container_width=True)
            with col_doc:
                try:
                    docx_data = StudyGenerator.generate_docx("Research Notes", cleaned_text)
                    st.download_button("📝 DOCX Note", docx_data,
                                       file_name="ExamHelp_Note.docx", use_container_width=True)
                except Exception:
                    st.button("📝 DOCX (unavailable)", disabled=True, use_container_width=True)
            with col_ppt:
                try:
                    ppt_data = StudyGenerator.generate_ppt("Slide Deck", cleaned_text)
                    st.download_button("📊 PPT Slides", ppt_data,
                                       file_name="ExamHelp_Slides.pptx", use_container_width=True)
                except Exception:
                    st.button("📊 PPT (unavailable)", disabled=True, use_container_width=True)

        with tab_share:
            st.markdown("#### 🔗 Share This Response")
            try:
                share_msgs = [{"r":m["role"][0],"c":m["content"]} for m in st.session_state.messages[-10:]]
                compressed = base64.urlsafe_b64encode(zlib.compress(json.dumps(share_msgs).encode())).decode()
                share_url  = f"?chat={compressed}"
                st.text_input("Share Link", value=share_url, label_visibility="collapsed")
                st.caption("📋 Copy the URL above to share this conversation.")
            except Exception:
                st.info("Sharing unavailable for this session.")

        # Add to history
        st.session_state.messages.append({"role":"assistant","content":cleaned_text})

        # TTS
        if st.session_state.get("voice_mode") and success:
            AppController.speak(cleaned_text[:600])

        # Token tracking (approximate)
        st.session_state.total_tokens_used += len(cleaned_text.split()) * 2
