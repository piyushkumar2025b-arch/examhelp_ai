import streamlit as st
import os
import datetime
import time
import json
from dotenv import load_dotenv

from utils.groq_client import stream_chat_with_groq, transcribe_audio, chat_with_groq
from utils.pdf_handler import extract_text_from_pdf, get_pdf_metadata, get_pdf_summary_stats
from utils.youtube_handler import get_youtube_transcript, format_transcript_as_context, extract_video_id, get_transcript_stats
from utils.web_handler import scrape_web_page, format_web_context, get_web_stats
from utils import key_manager
from utils.personas import PERSONAS, get_persona_names, get_persona_by_name, build_persona_prompt

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
        "selected_persona": "Default (ExamHelp)",
        "theme_mode": "dark",
        "selected_language": "English",
        "saved_sessions": {},
        "queued_prompt": None,
        "last_audio": None,
        "app_mode": "chat",
        "flashcards": [],
        "quiz_data": [],
        "current_card": 0,
        "quiz_score": 0,
        "quiz_current": 0,
        "quiz_feedback": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    
    # Persistent Session Loading (File-based)
    if "persistent_sessions" not in st.session_state:
        st.session_state.persistent_sessions = {}
        if os.path.exists("sessions.json"):
            try:
                with open("sessions.json", "r") as f:
                    st.session_state.persistent_sessions = json.load(f)
            except Exception:
                pass

init_state()

# ─────────────────────────────────────────────
# QUERY PARAMS DISPATCHER (For Quick Tools)
# ─────────────────────────────────────────────
if "action" in st.query_params:
    action = st.query_params["action"]
    if action == "flashcards":
        st.session_state.queued_prompt = "Based on the provided study material, act as a Flashcard Generator. Create 10 challenging Q&A flashcards to test my knowledge. Format as bold question, then bold answer."
    elif action == "quiz":
        st.session_state.queued_prompt = "Based on the provided study material, act as a Smart Quiz Master. Ask me one multiple-choice question at a time. Wait for my answer before giving feedback and moving to the next question."
    elif action == "mindmap":
        st.session_state.queued_prompt = "Generate a comprehensive Mermaid.js mind map (graph TD) of the key concepts from the study material. Provide ONLY the raw Mermaid code block."
    elif action == "planner":
        st.session_state.queued_prompt = "Create a structured, day-by-day revision timetable based on the major topics in the provided study material. Be highly specific about timeframes."
    
    st.query_params.clear()
    st.rerun()


# ─────────────────────────────────────────────
# THEME CSS — Dark & Light modes (Claude-inspired)
# ─────────────────────────────────────────────
def get_theme_css():
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    
    if is_dark:
        colors = {
            "bg": "#0a0a0b", "bg2": "#111113", "bg3": "#18181b",
            "border": "#27272a", "border2": "#3f3f46",
            "text": "#fafafa", "text2": "#a1a1aa", "text3": "#52525b",
            "accent": "#d97706", "accent2": "#f59e0b",
            "accent_bg": "rgba(217,119,6,0.08)", "accent_bd": "rgba(217,119,6,0.25)",
            "green": "#4ade80", "green_bg": "rgba(74,222,128,0.08)",
            "red": "#f87171", "blue": "#60a5fa",
            "surface": "#1e1e1e", "surface2": "#2a2a2a",
            "card_shadow": "rgba(0,0,0,0.3)",
        }
    else:
        colors = {
            "bg": "#fafaf9", "bg2": "#f5f5f4", "bg3": "#e7e5e4",
            "border": "#d6d3d1", "border2": "#a8a29e",
            "text": "#1c1917", "text2": "#57534e", "text3": "#a8a29e",
            "accent": "#d97706", "accent2": "#b45309",
            "accent_bg": "rgba(217,119,6,0.08)", "accent_bd": "rgba(217,119,6,0.25)",
            "green": "#16a34a", "green_bg": "rgba(22,163,74,0.08)",
            "red": "#dc2626", "blue": "#2563eb",
            "surface": "#ffffff", "surface2": "#f5f5f4",
            "card_shadow": "rgba(0,0,0,0.06)",
        }
    
    c = colors
    return f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --bg:        {c['bg']};
    --bg2:       {c['bg2']};
    --bg3:       {c['bg3']};
    --border:    {c['border']};
    --border2:   {c['border2']};
    --text:      {c['text']};
    --text2:     {c['text2']};
    --text3:     {c['text3']};
    --accent:    {c['accent']};
    --accent2:   {c['accent2']};
    --accent-bg: {c['accent_bg']};
    --accent-bd: {c['accent_bd']};
    --green:     {c['green']};
    --green-bg:  {c['green_bg']};
    --red:       {c['red']};
    --blue:      {c['blue']};
    --surface:   {c['surface']};
    --surface2:  {c['surface2']};
    --sans:      'Inter', system-ui, -apple-system, sans-serif;
    --mono:      'JetBrains Mono', monospace;
  }}

  /* ── Reset ── */
  html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
  }}

  #MainMenu, footer, header {{ visibility: hidden; }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
    background-color: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 0 !important;
  }}
  [data-testid="stSidebar"] > div:first-child {{
    padding-top: 0 !important;
  }}
  [data-testid="stSidebar"] * {{ font-family: var(--sans) !important; }}

  /* ── Main area ── */
  .main .block-container {{
    padding-top: 0 !important;
    padding-bottom: 6rem !important;
    max-width: 860px !important;
    margin: 0 auto !important;
  }}

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {{
    background: transparent !important;
    border: none !important;
    padding: 0.15rem 0 !important;
  }}

  /* ── Chat input ── */
  [data-testid="stChatInputContainer"] {{
    background: linear-gradient(to top, var(--bg) 70%, transparent) !important;
    border-top: none !important;
    padding: 1rem 1.5rem 1.5rem !important;
    position: sticky !important;
    bottom: 0 !important;
    backdrop-filter: blur(12px) !important;
  }}
  [data-testid="stChatInputContainer"] textarea {{
    background-color: var(--bg3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.95rem !important;
    padding: 14px 18px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
  }}
  [data-testid="stChatInputContainer"] textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-bg) !important;
  }}
  [data-testid="stChatInputContainer"] textarea::placeholder {{
    color: var(--text3) !important;
  }}
  [data-testid="stChatInputContainer"] button {{
    background-color: var(--accent) !important;
    border-radius: 10px !important;
    color: white !important;
    transition: background 0.2s !important;
  }}
  [data-testid="stChatInputContainer"] button:hover {{
    background-color: var(--accent2) !important;
  }}

  /* ── Buttons ── */
  .stButton > button {{
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
  }}
  .stButton > button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background-color: var(--accent-bg) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(217,119,6,0.12) !important;
  }}

  /* ── Select box ── */
  [data-testid="stSelectbox"] > div > div {{
    background-color: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
  }}

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {{
    background-color: var(--bg3) !important;
    border: 1px dashed var(--border2) !important;
    border-radius: 12px !important;
    padding: 0.4rem !important;
    transition: border-color 0.2s !important;
  }}
  [data-testid="stFileUploader"]:hover {{
    border-color: var(--accent) !important;
  }}

  /* ── Text input ── */
  [data-testid="stTextInput"] input {{
    background-color: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s !important;
  }}
  [data-testid="stTextInput"] input:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-bg) !important;
  }}
  [data-testid="stTextInput"] input::placeholder {{ color: var(--text3) !important; }}

  /* ── Expander ── */
  [data-testid="stExpander"] {{
    background-color: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
  }}
  [data-testid="stExpander"] summary {{
    font-size: 0.82rem !important;
    color: var(--text2) !important;
    font-weight: 500 !important;
  }}

  /* ── Alert/info boxes ── */
  [data-testid="stAlert"] {{
    border-radius: 10px !important;
    font-family: var(--sans) !important;
    font-size: 0.87rem !important;
  }}

  /* ── Divider ── */
  hr {{ border-color: var(--border) !important; margin: 0.6rem 0 !important; }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 4px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border2); border-radius: 10px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--text3); }}

  /* ── Code ── */
  code {{
    background-color: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
    font-family: var(--mono) !important;
    font-size: 0.82em !important;
    padding: 2px 6px !important;
    color: var(--accent) !important;
  }}

  /* ── Custom components ── */
  .eh-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 1.2rem 1rem 0.8rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.8rem;
  }}
  .eh-logo-icon {{
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 2px 12px rgba(217,119,6,0.35);
    position: relative;
    overflow: hidden;
  }}
  .eh-logo-icon::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.15));
    border-radius: 10px;
  }}
  .eh-logo-icon svg {{
    width: 20px; height: 20px;
    position: relative;
    z-index: 1;
  }}
  .eh-logo-text {{ line-height: 1.2; }}
  .eh-logo-title {{
    font-size: 1.05rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.3px;
  }}
  .eh-logo-sub {{ font-size: 0.7rem; color: var(--text3); }}

  .section-label {{
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text3);
    margin: 1rem 0 0.45rem 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  .source-chip {{
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
  }}
  .source-chip:hover {{ border-color: var(--accent); }}
  .source-chip .chip-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    flex-shrink: 0;
  }}

  .hero-wrap {{
    text-align: center;
    padding: 4rem 2rem 2rem;
    animation: fadeUp 0.6s ease both;
  }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(18px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  .hero-badge {{
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
  }}
  .hero-title {{
    font-family: var(--sans);
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -1px;
    line-height: 1.15;
    margin-bottom: 0.6rem;
  }}
  .hero-title em {{ color: var(--accent); font-style: italic; font-weight: 700; }}
  .hero-sub {{
    font-size: 0.95rem;
    color: var(--text2);
    line-height: 1.6;
    max-width: 460px;
    margin: 0 auto 2rem;
  }}
  .prompt-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    max-width: 560px;
    margin: 0 auto;
  }}
  .pill {{
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 0.8rem;
    color: var(--text2);
    cursor: pointer;
    transition: all 0.15s;
  }}
  .pill:hover {{
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-bg);
  }}

  .stat-row {{
    display: flex;
    gap: 8px;
    margin: 0.5rem 0;
  }}
  .stat-box {{
    flex: 1;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.55rem 0.4rem;
    text-align: center;
    transition: border-color 0.2s, transform 0.15s;
  }}
  .stat-box:hover {{
    border-color: var(--accent-bd);
    transform: translateY(-1px);
  }}
  .stat-val {{
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
    font-family: var(--mono);
  }}
  .stat-lbl {{
    font-size: 0.62rem;
    color: var(--text3);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 2px;
  }}

  .roadmap-item {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 4px;
    transition: background 0.15s;
  }}
  .roadmap-item:hover {{ background: var(--bg3); }}
  .roadmap-badge {{
    font-size: 0.62rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    flex-shrink: 0;
    margin-top: 2px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }}
  .badge-soon {{ background: rgba(74,222,128,0.12); color: var(--green); border: 1px solid rgba(74,222,128,0.25); }}
  .badge-planned {{ background: rgba(96,165,250,0.1); color: var(--blue); border: 1px solid rgba(96,165,250,0.2); }}
  .badge-idea {{ background: var(--bg3); color: var(--text3); border: 1px solid var(--border); }}
  .roadmap-text {{ font-size: 0.8rem; color: var(--text2); line-height: 1.4; }}
  .roadmap-text strong {{ color: var(--text); display: block; font-size: 0.82rem; }}

  .key-status-row {{
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
  }}
  .key-dot {{ width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
  .dot-green {{ background: var(--green); box-shadow: 0 0 6px rgba(74,222,128,0.5); }}
  .dot-orange {{ background: var(--accent); box-shadow: 0 0 6px rgba(217,119,6,0.4); }}
  .dot-red {{ background: var(--red); box-shadow: 0 0 6px rgba(248,113,113,0.4); }}

  .context-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }}

  .poweredby {{
    font-size: 0.68rem;
    color: var(--text3);
    text-align: center;
    padding: 1rem 0 0.5rem;
    letter-spacing: 0.04em;
  }}
  .poweredby span {{ color: var(--text2); }}

  .study-banner {{
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
  }}
  .study-banner-label {{ color: var(--text3); font-size: 0.76rem; }}

  /* ── Persona card ── */
  .persona-chip {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--accent-bg);
    border: 1px solid var(--accent-bd);
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 0.78rem;
    color: var(--accent);
    font-weight: 600;
    margin-bottom: 0.5rem;
    animation: fadeUp 0.3s ease;
  }}

  /* ── Status indicators ── */
  .status-indicator {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 8px;
    background: var(--bg3);
    border: 1px solid var(--border);
    font-size: 0.73rem;
    font-family: var(--mono);
    margin-bottom: 4px;
    transition: border-color 0.2s;
  }}
  .status-indicator:hover {{
    border-color: var(--border2);
  }}

  /* ── Theme toggle button ── */
  .theme-toggle {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 8px;
    background: var(--bg3);
    border: 1px solid var(--border);
    font-size: 0.78rem;
    color: var(--text2);
    cursor: pointer;
    transition: all 0.15s;
    width: 100%;
    justify-content: center;
  }}
  .theme-toggle:hover {{
    border-color: var(--accent);
    color: var(--accent);
  }}

  /* ── Chat message user bubble ── */
  [data-testid="stChatMessage"][data-testid*="user"] {{
    padding-left: 2rem !important;
  }}

  /* ── Perfect Toolbox Fix (No Gaps) ── */
  [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {{
    gap: 0 !important;
    padding-bottom: 0 !important;
  }}
  .toolbox-wrap {{
    margin-bottom: 12px;
  }}
  .tool-card {{
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    display: flex;
    align-items: center;
    gap: 15px;
    height: 78px;
    box-sizing: border-box;
    position: relative;
    z-index: 1;
    pointer-events: none;
    margin-top: 6px;
  }}
  .tool-card:hover {{
    border-color: var(--accent);
    background: var(--accent-bg);
    transform: translateX(4px);
    box-shadow: 0 10px 40px rgba(0,0,0,0.3), inset 6px 0 0 var(--accent);
  }}
  .tool-icon {{
    width: 44px; height: 44px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }}
  .tool-info {{ flex: 1; }}
  .tool-name {{ font-size: 0.95rem; font-weight: 800; color: var(--text); display: block; letter-spacing: -0.2px; }}
  .tool-desc {{ font-size: 0.74rem; color: var(--text3); line-height: 1.3; margin-top: 2px; }}

  /* The actual button overlap logic */
  div[data-testid="stSidebar"] .stButton {{
    height: 78px;
    padding: 0 !important;
    margin: 0 !important;
  }}
  div[data-testid="stSidebar"] .stButton > button {{
    position: absolute;
    width: 100% !important;
    height: 78px !important;
    margin-top: 6px !important;
    opacity: 0 !important;
    z-index: 100;
    cursor: pointer;
    border: none !important;
  }}
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
    
    persona = st.session_state.get("selected_persona", "Default (ExamHelp)")
    if persona != "Default (ExamHelp)":
        lines.append(f"## AI Persona: {persona}\n")
    
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

def count_output_stats(text: str):
    """Update running output statistics."""
    st.session_state.total_output_chars += len(text)
    st.session_state.total_output_lines += text.count('\n') + 1


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    # ── Logo ──────────────────────────────────
    st.markdown("""
    <div class="eh-logo">
      <div class="eh-logo-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white" opacity="0.9"/>
          <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
          <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>
        </svg>
      </div>
      <div class="eh-logo-text">
        <div class="eh-logo-title">ExamHelp</div>
        <div class="eh-logo-sub">AI Study Assistant · Groq LLM</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Theme Toggle ─────────────────────────
    theme_icon = "☀️" if st.session_state.theme_mode == "dark" else "🌙"
    theme_label = "Light Mode" if st.session_state.theme_mode == "dark" else "Dark Mode"
    if st.button(f"{theme_icon} {theme_label}", use_container_width=True, key="theme_btn"):
        st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"
        st.rerun()

    # ── Stats ─────────────────────────────────
    msg_count = len(st.session_state.messages)
    src_count = len(st.session_state.context_sources)
    ctx_kb = round(float(len(st.session_state.context_text)) / 1024.0, 2)
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-box"><div class="stat-val">{msg_count}</div><div class="stat-lbl">Messages</div></div>
      <div class="stat-box"><div class="stat-val">{src_count}</div><div class="stat-lbl">Sources</div></div>
      <div class="stat-box"><div class="stat-val">{ctx_kb}k</div><div class="stat-lbl">Context</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── AI Persona Selector ──────────────────
    st.markdown('<div class="section-label">🎭 AI Persona</div>', unsafe_allow_html=True)
    
    persona_names = get_persona_names()
    current_persona = st.session_state.get("selected_persona", "Default (ExamHelp)")
    
    selected = st.selectbox(
        "Choose AI Character",
        options=persona_names,
        index=persona_names.index(current_persona) if current_persona in persona_names else 0,
        label_visibility="collapsed",
        key="persona_select",
    )
    
    if selected != st.session_state.selected_persona:
        st.session_state.selected_persona = selected
        st.rerun()
    
    persona_data = get_persona_by_name(selected)
    if persona_data and selected != "Default (ExamHelp)":
        st.markdown(
            f'<div class="persona-chip">{persona_data["emoji"]} {persona_data["name"]} · {persona_data["era"]}</div>'
            f'<div style="font-size:0.75rem;color:var(--text3);margin-bottom:0.5rem;line-height:1.4;">{persona_data["mood"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">🌍 Language</div>', unsafe_allow_html=True)
    languages = ["English", "Spanish", "French", "German", "Hindi", "Mandarin", "Japanese", "Arabic"]
    current_lang = st.session_state.get("selected_language", "English")
    sel_lang = st.selectbox("Select Language", languages, index=languages.index(current_lang) if current_lang in languages else 0, label_visibility="collapsed")
    if sel_lang != current_lang:
        st.session_state.selected_language = sel_lang
        st.rerun()

    st.divider()

    # ── API Status ────────────────────────────
    st.markdown('<div class="section-label">🔑 API Status</div>', unsafe_allow_html=True)

    override = _get_override_key()
    active_key = key_manager.get_key(override=override)
    total_keys = key_manager.total_keys()
    avail_keys = key_manager.available_keys_count()

    if active_key:
        masked = f"{active_key[:8]}…{active_key[-4:]}"
        st.markdown(f"""
        <div class="key-status-row" style="margin-bottom:0.5rem;">
          <div class="key-dot dot-green"></div>
          <span style="color:var(--green); font-weight:600;">Connected</span>
          <span style="color:var(--text3); margin-left:auto; font-size:0.68rem;">{masked}</span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔧 Key Pool Health"):
            for row in key_manager.status_table():
                status_color = "var(--green)" if "available" in row["status"].lower() else "var(--accent)"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg3); padding:6px 8px; border-radius:6px; margin-bottom:4px; font-size:0.73rem; border:1px solid var(--border); font-family:var(--mono);">
                  <div style="display:flex; align-items:center; gap:6px;">
                    <div class="key-dot" style="background:{status_color}"></div>
                    <span style="color:var(--text2);">{row['key']}</span>
                  </div>
                  <div style="color:var(--text3); display:flex; gap:8px;">
                    <span title="Uses">✓{row['uses']}</span>
                    <span title="Errors">✕{row['errors']}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            if st.button("↺ Reset All Cooldowns", use_container_width=True):
                key_manager.reset_all_cooldowns()
                st.rerun()
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

    st.divider()

    # ── Output Stats (replaces Key Pool Health) ──
    st.markdown('<div class="section-label">📊 Output Stats</div>', unsafe_allow_html=True)
    
    out_chars = st.session_state.get("total_output_chars", 0)
    out_lines = st.session_state.get("total_output_lines", 0)
    
    if out_chars >= 1000:
        chars_display = f"{out_chars/1000:.1f}k"
    else:
        chars_display = str(out_chars)
    
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-box"><div class="stat-val">{chars_display}</div><div class="stat-lbl">Characters</div></div>
      <div class="stat-box"><div class="stat-val">{out_lines}</div><div class="stat-lbl">Lines</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Network Status ────────────────────────
    st.markdown('<div class="section-label">🌐 Network</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div id="net-status">
      <div class="status-indicator" id="online-status">
        <div class="key-dot dot-green" id="online-dot"></div>
        <span id="online-text" style="color:var(--green);font-weight:600;">Online</span>
        <span id="speed-text" style="color:var(--text3);margin-left:auto;">Connected</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── PDF Upload ────────────────────────────
    st.markdown('<div class="section-label">📄 PDF Upload</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload one or more PDFs (max 10MB each)",
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
            st.session_state.messages = []
            st.session_state.total_output_chars = 0
            st.session_state.total_output_lines = 0
            st.rerun()

    # ── Academic Analytics (New) ──────────────
    st.markdown('<div class="section-label">📈 Academic Analytics</div>', unsafe_allow_html=True)
    msg_total = len(st.session_state.messages)
    concepts_total = len(st.session_state.context_sources)
    
    # Calculate total words in current context
    word_count_total = sum(len(s.get("label", "").split()) for s in st.session_state.context_sources) # simplistic proxy
    # Better: access the text directly
    actual_words = len(st.session_state.context_text.split())
    
    st.markdown(f"""
    <div style="background:var(--bg3); border:1px solid var(--border); border-radius:10px; padding:12px; margin-bottom:1rem;">
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text3); margin-bottom:4px;">
            <span>Concepts Mastered</span> <span>{concepts_total}</span>
        </div>
        <div style="height:4px; background:var(--bg2); border-radius:2px; margin-bottom:10px;">
            <div style="width:{min(100, concepts_total*10)}%; height:100%; background:var(--accent); border-radius:2px;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text3); margin-bottom:4px;">
            <span>Knowledge Density</span> <span>{actual_words:,} words</span>
        </div>
        <div style="height:4px; background:var(--bg2); border-radius:2px;">
            <div style="width:{min(100, actual_words/100)}%; height:100%; background:var(--accent); border-radius:2px; opacity:0.6;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Study Sessions (Interactive) ──────────
    st.markdown('<div class="section-label">📁 Study Sessions</div>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        session_name = st.text_input("Save As", placeholder="e.g. Chapter 4", label_visibility="collapsed")
        if st.button("💾 Save", use_container_width=True):
            if session_name and st.session_state.messages:
                session_data = {
                    "messages": st.session_state.messages.copy(), 
                    "context": st.session_state.context_text,
                    "sources": st.session_state.context_sources.copy(),
                    "timestamp": datetime.datetime.now().isoformat()
                }
                st.session_state.persistent_sessions[session_name] = session_data
                # Save to disk
                with open("sessions.json", "w") as f:
                    json.dump(st.session_state.persistent_sessions, f)
                st.success("Saved to disk!")
    with col4:
        if st.session_state.persistent_sessions:
            load_options = list(st.session_state.persistent_sessions.keys())
            load_name = st.selectbox("Load File", load_options, label_visibility="collapsed")
            col_l, col_n = st.columns([1, 1])
            with col_l:
                if st.button("📂 Load", use_container_width=True):
                    data = st.session_state.persistent_sessions[load_name]
                    st.session_state.messages = data["messages"]
                    st.session_state.context_text = data["context"]
                    st.session_state.context_sources = data["sources"]
                    st.rerun()
            with col_n:
                if st.button("➕ New", use_container_width=True):
                    st.session_state.messages = []; st.session_state.context_sources = []; st.rerun()
        else:
            st.selectbox("Load File", ["No sessions saved"], disabled=True, label_visibility="collapsed")
            if st.button("➕ New Session", use_container_width=True):
                st.session_state.messages = []; st.rerun()

    # ── Study Toolbox (Real Options) ──────────
    st.markdown('<div class="section-label">🛠️ Study Toolbox</div>', unsafe_allow_html=True)
    
    tools = [
        {"id": "flash", "name": "Flashcards", "icon": "🃏", "desc": "Structured Q&A drill", "mode": "flashcards"},
        {"id": "quiz", "name": "Quiz Mode", "icon": "📝", "desc": "Interactive assessment", "mode": "quiz"},
        {"id": "map", "name": "Mind Map", "icon": "📊", "desc": "Visual concept mapping", "mode": "mindmap"},
        {"id": "plan", "name": "Study Planner", "icon": "📅", "desc": "Tailored revision timetable", "mode": "planner"},
        {"id": "voice", "name": "Voice Assistant", "icon": "🎙️", "desc": "Speak to your tutor", "mode": "voice"},
        {"id": "chat", "name": "Standard Chat", "icon": "💬", "desc": "General study conversation", "mode": "chat"},
    ]

    for t in tools:
        st.markdown(f"""
        <div class="click-container">
            <div class="tool-card">
                <div class="tool-icon">{t['icon']}</div>
                <div class="tool-info">
                    <span class="tool-name">{t['name']}</span>
                    <span class="tool-desc">{t['desc']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Hidden button overlay
        st.markdown('<div style="margin-top:-60px">', unsafe_allow_html=True)
        if st.button(" ", key=f"tool_{t['id']}", use_container_width=True):
            st.session_state.app_mode = t['mode']
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom:1rem"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="poweredby">Powered by <span>Groq</span> · <span>llama-3.3-70b-versatile</span></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# MAIN CHAT AREA
# ─────────────────────────────────────────────

# ── Header ───────────────────────────────────
persona = get_persona_by_name(st.session_state.selected_persona)
persona_tag = ""
if persona and st.session_state.selected_persona != "Default (ExamHelp)":
    persona_tag = f' · <span style="color:var(--accent);font-weight:600;">{persona["emoji"]} {persona["name"]}</span>'

st.markdown(f"""
<div style="padding: 1.5rem 0 0.5rem; border-bottom: 1px solid var(--border); margin-bottom: 1rem;">
  <div style="display:flex; align-items:baseline; gap:10px; flex-wrap:wrap;">
    <div style="font-size:1.4rem; font-weight:800; color:var(--text); letter-spacing:-0.5px;">
      ExamHelp
    </div>
    <div style="font-size:0.78rem; color:var(--text3);">Your focused AI study companion{persona_tag}</div>
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

app_mode = st.session_state.get("app_mode", "chat")

if app_mode == "flashcards":
    st.header("🃏 Flashcard Generator")
    lang = st.session_state.get("selected_language", "English")
    if not st.session_state.context_text:
        st.warning(f"Please upload material to generate {lang} flashcards.")
    else:
        if st.button("🪄 Generate Professional Flashcards"):
            with st.spinner(f"Creating {lang} study deck..."):
                prompt = [
                    {"role": "system", "content": f"You are a master educator. Create 10 expert Q&A flashcards based strictly on the study material. "
                                                  f"Return ONLY a strictly valid JSON object. Do NOT include any preamble, notes, or explanations. "
                                                  f"Format: {{\"flashcards\": [{{'q': 'Question text', 'a': 'Answer text'}}]}}. "
                                                  f"All content MUST be in {lang}."},
                    {"role": "user", "content": f"Study Material: {st.session_state.context_text[:12000]}"}
                ]
                success_gen = False
                for _ in range(key_manager.MAX_RETRIES):
                    try:
                        res_raw = chat_with_groq(prompt, json_mode=True, override_key=_get_override_key())
                        res_content = res_raw.strip()
                        if not res_content.startswith("{"):
                            idx = res_content.find("{")
                            if idx != -1: res_content = res_content[idx:]
                        data = json.loads(res_content)
                        st.session_state.flashcards = data.get("flashcards") or list(data.values())[0]
                        st.session_state.current_card = 0
                        success_gen = True
                        break
                    except Exception as e:
                        time.sleep(1)
                        continue
                if not success_gen:
                    st.error("⚠️ Failed to generate flashcards after multiple attempts. Please try again or check your API keys.")
        
        if st.session_state.flashcards:
            cards = st.session_state.flashcards
            idx = st.session_state.current_card
            card = cards[idx]
            
            st.markdown(f"### {lang} Flashcard {idx + 1} / {len(cards)}")
            
            with st.container():
                st.markdown(f"""
                <div style="background:var(--bg3); border:2px solid var(--accent); border-radius:15px; padding:40px; text-align:center; min-height:220px; display:flex; align-items:center; justify-content:center; flex-direction:column; margin-bottom:20px; box-shadow: 0 10px 40px rgba(0,0,0,0.25);">
                    <div style="color:var(--text3); font-size:0.8rem; margin-bottom:12px; text-transform:uppercase; letter-spacing:1px; font-weight:700;">Question</div>
                    <div style="font-size:1.6rem; font-weight:800; color:var(--text); line-height:1.2;">{card['q']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("👁️ Reveal Answer"):
                    st.markdown(f"""
                    <div style="background:var(--green-bg); border:1px solid var(--green); border-radius:12px; padding:25px; text-align:center; margin-top:10px;">
                        <div style="color:var(--green); font-size:0.8rem; margin-bottom:12px; text-transform:uppercase; letter-spacing:1px; font-weight:700;">Answer</div>
                        <div style="font-size:1.4rem; color:var(--text); font-weight:500;">{card['a']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns([1,1,1])
            with col_a:
                if st.button("⬅️ Back", disabled=(idx == 0), use_container_width=True):
                    st.session_state.current_card -= 1; st.rerun()
            with col_b:
                if st.button("💾 Save to Chat", use_container_width=True):
                    summary = "\n".join([f"Q: {c['q']} | A: {c['a']}" for c in cards])
                    st.session_state.messages.append({"role": "assistant", "content": f"### 🃏 Generated Flashcards ({lang})\n\n{summary}"})
                    st.success("Saved to history!")
            with col_c:
                if st.button("Next ➡️", disabled=(idx == len(cards)-1), use_container_width=True):
                    st.session_state.current_card += 1; st.rerun()
    st.stop()

elif app_mode == "quiz":
    st.header("📝 Smart Quiz Mode")
    lang = st.session_state.get("selected_language", "English")
    if not st.session_state.context_text:
        st.warning(f"Please upload context to start a {lang} quiz.")
    else:
        if st.button(f"🪄 Build {lang} Quiz"):
            with st.spinner("Generating challenges..."):
                prompt = [
                    {"role": "system", "content": f"Create 5 challenging MCQs based strictly on the provided text. "
                                                  f"Return ONLY a strictly valid JSON object. No preamble. "
                                                  f"Format: {{\"quiz\": [{{'q': '...', 'options': ['A', 'B', 'C', 'D'], 'correct': 'Correct Option Text', 'explanation': 'Brief reason'}}]}}. "
                                                  f"All content MUST be in {lang}."},
                    {"role": "user", "content": f"Context Material: {st.session_state.context_text[:12000]}"}
                ]
                success_gen = False
                for _ in range(key_manager.MAX_RETRIES):
                    try:
                        res_raw = chat_with_groq(prompt, json_mode=True, override_key=_get_override_key())
                        res_content = res_raw.strip()
                        if not res_content.startswith("{"):
                            idx = res_content.find("{")
                            if idx != -1: res_content = res_content[idx:]
                        data = json.loads(res_content)
                        st.session_state.quiz_data = data.get("quiz") or list(data.values())[0]
                        st.session_state.quiz_current = 0
                        st.session_state.quiz_score = 0
                        st.session_state.quiz_feedback = None
                        success_gen = True
                        break
                    except Exception as e:
                        time.sleep(1)
                        continue
                if not success_gen:
                    st.error("⚠️ Quiz generation failed. Try reloading your study material.")

        if st.session_state.quiz_data:
            quiz = st.session_state.quiz_data
            idx = st.session_state.quiz_current
            
            if idx < len(quiz):
                q = quiz[idx]
                st.markdown(f"### Assessment: Question {idx + 1} of {len(quiz)}")
                st.info(f"**{q['q']}**")
                
                choice = st.radio(f"Select your {lang} answer:", q['options'], key=f"qz_{idx}")
                
                col_s, col_n = st.columns([1,1])
                with col_s:
                    if st.button("✅ Submit Result", use_container_width=True) and not st.session_state.quiz_feedback:
                        if choice == q['correct']:
                            st.session_state.quiz_score += 1
                            st.session_state.quiz_feedback = ("success", f"⚡ **Correct!** {q['explanation']}")
                        else:
                            st.session_state.quiz_feedback = ("error", f"❌ **Not quite.** Correct was: {q['correct']}. {q['explanation']}")
                        st.rerun()

                if st.session_state.quiz_feedback:
                    type, msg = st.session_state.quiz_feedback
                    if type == "success": st.success(msg)
                    else: st.error(msg)
                    with col_n:
                        if st.button("Continue ➡️", use_container_width=True):
                            st.session_state.quiz_current += 1
                            st.session_state.quiz_feedback = None
                            st.rerun()
            else:
                st.balloons()
                st.success(f"### 🎉 Quiz Finished!\n**Final Performance:** {st.session_state.quiz_score} / {len(quiz)}")
                if st.button("🔄 Try Again", use_container_width=True):
                    st.session_state.quiz_data = []; st.rerun()
    st.stop()

elif app_mode == "mindmap":
    st.header("📊 Interactive Concept Map")
    lang = st.session_state.get("selected_language", "English")
    if not st.session_state.context_text:
        st.warning(f"Please provide context to visualize it in {lang}.")
    else:
        if st.button("🪄 Map Out Core Concepts"):
            with st.spinner(f"Mapping relationships in {lang}..."):
                prompt = [
                    {"role": "system", "content": f"Create a detailed Mermaid.js mind map (graph TD) node-by-node. Language: {lang}. Output ONLY raw mermaid code block."},
                    {"role": "user", "content": f"Context: {st.session_state.context_text[:12000]}"}
                ]
                try:
                    mm_code = chat_with_groq(prompt, override_key=_get_override_key())
                    if "```mermaid" in mm_code: mm_code = mm_code.split("```mermaid")[1].split("```")[0]
                    elif "```" in mm_code: mm_code = mm_code.split("```")[1].split("```")[0]
                    st.session_state.mindmap_code = mm_code.strip()
                except Exception as e:
                    st.error(f"Visualization Error: {e}")

        if st.session_state.get("mindmap_code"):
            # Mermaid Renderer
            html_code = f"""
            <div id="mermaid-root" style="background:var(--bg3); padding:20px; border-radius:12px; border:1px solid var(--border);">
                <pre class="mermaid">{st.session_state.mindmap_code}</pre>
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
            </script>
            """
            import streamlit.components.v1 as components
            components.html(html_code, height=600, scrolling=True)
            
            with st.expander("🛠️ Mind Map Options"):
                st.code(st.session_state.mindmap_code, language="mermaid")
                if st.button("💾 Keep Map in History"):
                    st.session_state.messages.append({"role": "assistant", "content": f"### 📊 Concept Map ({lang})\n```mermaid\n{st.session_state.mindmap_code}\n```"})
                    st.success("Map saved!")
    st.stop()

elif app_mode == "planner":
    st.header("📅 Study Planner")
    lang = st.session_state.get("selected_language", "English")
    if not st.session_state.context_text:
        st.warning(f"Upload notes to generate a {lang} timetable.")
    else:
        if st.button("🪄 Create Professional Study Schedule"):
            with st.spinner(f"Scheduling in {lang}..."):
                prompt = [
                    {"role": "system", "content": f"You are a master of scientific revision planning. Create a detailed, day-by-day revision timetable based on the major topics. "
                                                  f"Be specific about hours, sub-topics, active recall slots, and breaks. "
                                                  f"Response MUST be in {lang}. Use Markdown with emojis."},
                    {"role": "user", "content": f"Study Context: {st.session_state.context_text[:12000]}"}
                ]
                try:
                    # Using the direct helper for speed
                    st.session_state.study_plan_content = chat_with_groq(prompt, override_key=_get_override_key())
                except Exception as e:
                    st.error(f"Planning Error: {e}")

        if st.session_state.get("study_plan_content"):
            st.markdown(st.session_state.study_plan_content)
            col_pl, col_dl = st.columns([1,1])
            with col_pl:
                if st.button("💾 Save Plan to Chat", use_container_width=True):
                    st.session_state.messages.append({"role": "assistant", "content": f"### 📅 {lang} Revision Plan\n{st.session_state.study_plan_content}"})
                    st.success("Plan saved to history!")
            with col_dl:
                 st.download_button("📥 Download as TXT", st.session_state.study_plan_content, "study_plan.txt", use_container_width=True)
    st.stop()

elif app_mode == "voice":
    st.header("🎙️ Intelligent Voice Mode")
    lang_v = st.session_state.get("selected_language", "English")
    st.markdown(f"Discuss your materials in **{lang_v}**. Use commands like *'Generate quiz'* or *'Create mind map'*.")
    audio_val = st.audio_input("Start speaking...", key="voice_main")
    if audio_val:
        with st.spinner("Processing voice context..."):
            try:
                transcript = transcribe_audio(audio_val.read(), override_key=_get_override_key())
                txt = transcript.text if hasattr(transcript, "text") else str(transcript)
                if txt.strip():
                    txt_low = txt.lower()
                    if "quiz" in txt_low: st.session_state.app_mode = "quiz"
                    elif "flash" in txt_low: st.session_state.app_mode = "flashcards"
                    elif "map" in txt_low: st.session_state.app_mode = "mindmap"
                    elif "plan" in txt_low: st.session_state.app_mode = "planner"
                    else: st.session_state.queued_prompt = txt
                    st.rerun()
            except Exception as e:
                st.error(f"Voice Recognition Error: {e}")
    st.stop()

# ── Empty state (Chat Mode Only) ───────────────────────
if not st.session_state.messages and app_mode == "chat":
    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-badge">✦ Powered by Groq · llama-3.3-70b-versatile</div>
      <div class="hero-title">Study smarter,<br><em>not harder</em></div>
      <div class="hero-sub">
        Upload your notes, lecture PDFs, YouTube videos, or any article —
        then ask anything and get sharp, exam-focused answers instantly.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Chat history ──────────────────────────────
for msg in st.session_state.messages:
    avatar = "🎓" if msg["role"] == "assistant" else "👤"
    # Use persona emoji for assistant if persona is active
    if msg["role"] == "assistant" and persona and st.session_state.selected_persona != "Default (ExamHelp)":
        avatar = persona["emoji"]
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Voice Input & Chat Input ────────────────────────────────
audio_val = st.audio_input("Record a voice question", label_visibility="collapsed")
if audio_val and audio_val != st.session_state.get("last_audio"):
    st.session_state.last_audio = audio_val
    with st.spinner("Transcribing voice..."):
        try:
            transcript = transcribe_audio(audio_val.read(), override_key=_get_override_key())
            if hasattr(transcript, "text") and transcript.text.strip():
                st.session_state.queued_prompt = transcript.text
            elif isinstance(transcript, str) and transcript.strip():
                st.session_state.queued_prompt = transcript
        except Exception as e:
            st.error(f"Voice transcription failed: {e}")

user_input = st.chat_input("Ask anything about your study material…", key="chat_input")

if st.session_state.queued_prompt:
    user_input = st.session_state.queued_prompt
    st.session_state.queued_prompt = None

if user_input:
    override = _get_override_key()
    active_key = key_manager.get_key(override=override)

    if not active_key:
        st.error("No API key available. Please enter a Groq API key in the sidebar.", icon="🔑")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Determine assistant avatar
    assistant_avatar = "🎓"
    if persona and st.session_state.selected_persona != "Default (ExamHelp)":
        assistant_avatar = persona["emoji"]

    with st.chat_message("assistant", avatar=assistant_avatar):
        placeholder = st.empty()
        full_response = ""
        max_attempts = key_manager.MAX_RETRIES
        attempt = 0
        success = False

        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-20:]]

        # Build persona prompt
        persona_prompt = ""
        if persona and st.session_state.selected_persona != "Default (ExamHelp)":
            persona_prompt = build_persona_prompt(persona, language=st.session_state.get("selected_language", "English"))
        elif st.session_state.get("selected_language", "English") != "English":
            # If default persona but language changed
            persona_prompt = f"\n\nCRITICAL RULE: You MUST answer strictly in {st.session_state.selected_language}. All explanations, headers, and bullet points must be translated to {st.session_state.selected_language}."

        while attempt < max_attempts and not success:
            current_key = key_manager.get_key(override=override)
            if not current_key:
                full_response = "⚠️ **All API keys are cooling down.** Please wait ~60 seconds and try again."
                placeholder.warning(full_response)
                break

            full_response = ""
            try:
                for chunk in stream_chat_with_groq(
                    history,
                    st.session_state.context_text,
                    override_key=current_key,
                    persona_prompt=persona_prompt,
                    language=st.session_state.get("selected_language", "English")
                ):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                success = True

                # Track output stats
                count_output_stats(full_response)

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
                    placeholder.warning(f"⚡ {reason} on `{masked}`. Switching to next key…", icon="🔄")
                    # Key is already marked by groq_client, get next one
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