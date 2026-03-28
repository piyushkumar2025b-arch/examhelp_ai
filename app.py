import datetime
import json
import os
import re
import time
import base64
import streamlit as st
try:
    import pandas as pd
except ImportError:
    pd = None
from dotenv import load_dotenv

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None
    go = None

from utils.groq_client import stream_chat_with_groq, transcribe_audio, chat_with_groq
from utils.pdf_handler import extract_text_from_pdf, get_pdf_metadata, get_pdf_summary_stats
from utils.youtube_handler import get_youtube_transcript, format_transcript_as_context, extract_video_id, get_transcript_stats
from utils.web_handler import scrape_web_page, format_web_context, get_web_stats
from utils import key_manager
from utils.personas import PERSONAS, get_persona_names, get_persona_by_name, build_persona_prompt
from utils.ocr_handler import extract_text_from_image
from utils.analytics import get_subject_mastery_radar, get_study_intensity_heatmap, estimate_required_velocity
from utils.app_controller import AppController

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
from chat.share import ChatShare

if "chat" in st.query_params:
    encoded_chat = st.query_params["chat"]
    try:
        import zlib, json, base64
        decoded_bytes = base64.urlsafe_b64decode(encoded_chat.encode("utf-8"))
        decompressed = zlib.decompress(decoded_bytes).decode('utf-8')
        minimal_history = json.loads(decompressed)
        st.session_state.messages = [{"role": m["r"], "content": m["c"]} for m in minimal_history]
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        print(f"Chat load error: {e}")
        st.query_params.clear()


# ─────────────────────────────────────────────
# THEME CSS — Dark & Light modes (Claude-inspired)
# ─────────────────────────────────────────────
def get_theme_css():
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    
    if is_dark:
        colors = {
            "bg": "#0a0a0b", "bg_glass": "rgba(10,10,11,0.65)", "bg2": "#111113", "bg2_glass": "rgba(17,17,19,0.75)", "bg3": "#18181b", "bg3_glass": "rgba(24,24,27,0.7)",
            "border": "#27272a", "bd_glass": "rgba(39,39,42,0.5)", "border2": "#3f3f46",
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
            "bg": "#fafaf9", "bg_glass": "rgba(250,250,249,0.7)", "bg2": "#f5f5f4", "bg2_glass": "rgba(245,245,244,0.75)", "bg3": "#e7e5e4", "bg3_glass": "rgba(231,229,228,0.7)",
            "border": "#d6d3d1", "bd_glass": "rgba(214,211,209,0.5)", "border2": "#a8a29e",
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
    --bg-glass:  {c['bg_glass']};
    --bg2:       {c['bg2']};
    --bg2-glass: {c['bg2_glass']};
    --bg3:       {c['bg3']};
    --bg3-glass: {c['bg3_glass']};
    --border:    {c['border']};
    --bd-glass:  {c['bd_glass']};
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
    --card-shadow:{c['card_shadow']};
    --sans:      'Inter', system-ui, -apple-system, sans-serif;
    --mono:      'JetBrains Mono', monospace;
  }}

  /* ── Reset ── */
  html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
  }}

  #MainMenu, footer {{ visibility: hidden; }}
  .focus-active header {{ display: none !important; }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
    background-color: var(--bg2-glass) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid var(--bd-glass) !important;
    padding-top: 0 !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
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
  @keyframes messageSlideIn {{
    0% {{ transform: translateY(15px); opacity: 0; }}
    100% {{ transform: translateY(0); opacity: 1; }}
  }}
  [data-testid="stChatMessage"] {{
    background: var(--bg2-glass) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--bd-glass) !important;
    border-radius: 12px !important;
    padding: 1.2rem 1.4rem !important;
    margin-bottom: 1.2rem !important;
    animation: messageSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    box-shadow: 0 4px 16px rgba(0,0,0,0.02) !important;
  }}
  
  /* Right align user messages securely */
  [data-testid="stChatMessage"]:has(.user-message-hook) {{
    background: var(--bg3-glass) !important;
    border: 1px solid var(--accent-bd) !important;
    margin-left: 20% !important;
    border-top-right-radius: 2px !important;
    flex-direction: row-reverse !important;
  }}
  /* Left align assistant messages */
  [data-testid="stChatMessage"]:not(:has(.user-message-hook)) {{
    margin-right: 15% !important;
    border-top-left-radius: 2px !important;
  }}
  
  /* Internal spacing inside chat bubbles */
  [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
    line-height: 1.6 !important;
    font-size: 0.95rem !important;
  }}

  /* Action Bar Styling */
  .chat-action-bar {{
    display: flex;
    gap: 8px;
    margin-top: 12px;
    opacity: 0.6;
    transition: opacity 0.2s ease;
  }}
  [data-testid="stChatMessage"]:hover .chat-action-bar {{
    opacity: 1;
  }}
  
  /* ── Chat input ── */
  [data-testid="stChatInputContainer"] {{
    background: linear-gradient(to top, var(--bg) 60%, transparent) !important;
    border-top: none !important;
    padding: 1rem 1.5rem 1.5rem !important;
    position: sticky !important;
    bottom: 0 !important;
  }}
  [data-testid="stChatInputContainer"] textarea {{
    background-color: var(--bg3-glass) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid var(--bd-glass) !important;
    border-radius: 20px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.95rem !important;
    padding: 16px 20px !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 8px 32px var(--card-shadow) !important;
  }}
  [data-testid="stChatInputContainer"] textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px var(--accent-bg), 0 8px 32px var(--card-shadow) !important;
    background-color: var(--bg) !important;
  }}
  [data-testid="stChatInputContainer"] textarea::placeholder {{
    color: var(--text3) !important;
  }}
  [data-testid="stChatInputContainer"] button {{
    background-color: var(--accent) !important;
    border-radius: 10px !important;
    color: white !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
  }}
  [data-testid="stChatInputContainer"] button:hover {{
    background-color: var(--accent2) !important;
    transform: scale(1.05);
  }}
  [data-testid="stChatInputContainer"] button:active {{
    transform: scale(0.95);
  }}

  /* ── Buttons ── */
  .stButton > button {{
    background-color: var(--bg3-glass) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid var(--bd-glass) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
    font-family: var(--sans) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.1rem !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    letter-spacing: 0.015em !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
  }}
  .stButton > button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background-color: var(--accent-bg) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 16px var(--accent-bg) !important;
  }}
  .stButton > button:active {{
    transform: translateY(0px) !important;
  }}

  /* ── Select box ── */
  [data-testid="stSelectbox"] > div > div {{
    background-color: var(--bg3-glass) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--bd-glass) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    transition: all 0.3s ease !important;
  }}

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {{
    background-color: var(--bg3-glass) !important;
    backdrop-filter: blur(8px) !important;
    border: 1.5px dashed var(--bd-glass) !important;
    border-radius: 14px !important;
    padding: 0.4rem !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
  }}
  [data-testid="stFileUploader"]:hover {{
    border-color: var(--accent) !important;
    background-color: var(--accent-bg) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 12px var(--accent-bg) !important;
  }}

  /* ── Text input ── */
  [data-testid="stTextInput"] input {{
    background-color: var(--bg3-glass) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--bd-glass) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 0.88rem !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
  }}
  [data-testid="stTextInput"] input:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-bg) !important;
    background-color: var(--bg) !important;
  }}
  [data-testid="stTextInput"] input::placeholder {{ color: var(--text3) !important; }}

  /* ── Expander ── */
  [data-testid="stExpander"] {{
    background-color: var(--bg2-glass) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--bd-glass) !important;
    border-radius: 12px !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
  }}
  [data-testid="stExpander"]:hover {{
    border-color: var(--border) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.06) !important;
  }}
  [data-testid="stExpander"] summary {{
    font-size: 0.84rem !important;
    color: var(--text) !important;
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
    gap: 6px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: var(--text2);
    font-family: var(--sans);
    margin: 3px 4px 3px 0;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }}
  .source-chip:hover {{ 
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(217,119,6,0.1);
  }}
  .source-chip .chip-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
  }}

  .hero-wrap {{
    text-align: center;
    padding: 4rem 2rem 2rem;
    animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
  }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(24px) scale(0.98); }}
    to   {{ opacity: 1; transform: translateY(0) scale(1); }}
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
    box-shadow: 0 4px 12px var(--accent-bg);
  }}
  .hero-title {{
    font-family: var(--sans);
    font-size: 2.6rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -1.2px;
    line-height: 1.15;
    margin-bottom: 0.6rem;
    text-shadow: 0 4px 20px var(--card-shadow);
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
    background: var(--bg3-glass);
    backdrop-filter: blur(8px);
    border: 1px solid var(--bd-glass);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 0.8rem;
    color: var(--text2);
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  }}
  .pill:hover {{
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-bg);
    transform: translateY(-2px);
    box-shadow: 0 6px 12px var(--accent-bg);
  }}

  .stat-row {{
    display: flex;
    gap: 8px;
    margin: 0.5rem 0;
  }}
  .stat-box {{
    flex: 1;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.7rem 0.5rem;
    text-align: center;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }}
  .stat-box:hover {{
    border-color: var(--accent-bd);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.1);
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
    gap: 12px;
    background: linear-gradient(90deg, var(--bg2-glass), var(--bg3-glass));
    backdrop-filter: blur(12px);
    border: 1px solid var(--bd-glass);
    border-radius: 16px;
    padding: 10px 18px;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
    color: var(--text2);
    flex-wrap: wrap;
    box-shadow: 0 4px 20px var(--card-shadow);
    transition: all 0.3s ease;
  }}
  .study-banner:hover {{
    transform: translateY(-1px);
    box-shadow: 0 8px 24px var(--card-shadow);
  }}
  .study-banner-label {{ color: var(--text3); font-size: 0.76rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}

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
    border: 1px solid var(--border);
    border-radius: 10px;
  }}

  /* ── Light Mode Deep Fix ── */
  .light-active [data-testid="stSidebar"],
  .light-active [data-testid="stSidebar"] * {{
    color: var(--text) !important;
  }}
  .light-active [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {{
    background-color: var(--bg3) !important;
    color: var(--text) !important;
  }}
  .light-active [data-testid="stSidebar"] [data-baseweb="select"] span,
  .light-active [data-testid="stSidebar"] [data-baseweb="select"] div {{
    color: var(--text) !important;
  }}
  .light-active .main .block-container * {{
    color: var(--text);
  }}
  .light-active [data-testid="stChatMessage"] p,
  .light-active [data-testid="stChatMessage"] li,
  .light-active [data-testid="stChatMessage"] h1,
  .light-active [data-testid="stChatMessage"] h2,
  .light-active [data-testid="stChatMessage"] h3 {{
    color: var(--text) !important;
  }}
  .light-active [data-testid="stChatInputContainer"] textarea {{
    background-color: #ffffff !important;
    border: 1px solid #d6d3d1 !important;
    color: #1c1917 !important;
  }}
  .light-active [data-testid="stMarkdownContainer"] p {{
    color: var(--text) !important;
  }}
  .light-active .stat-val {{ color: var(--text) !important; }}
  .light-active .hero-title {{ color: var(--text) !important; }}
  .light-active code {{
    background-color: #e7e5e4 !important;
    color: #b45309 !important;
    border-color: #d6d3d1 !important;
  }}
  .light-active pre {{
    background-color: #f5f5f4 !important;
  }}

  /* ── Scroll-to-Bottom FAB ── */
  .scroll-fab {{
    position: fixed;
    bottom: 100px;
    right: 32px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--accent);
    color: white;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    box-shadow: 0 4px 16px rgba(217,119,6,0.35);
    z-index: 999;
    transition: transform 0.2s, opacity 0.2s;
    opacity: 0.85;
  }}
  .scroll-fab:hover {{
    transform: scale(1.12);
    opacity: 1;
  }}

  /* ── Toolbar row (calendar, calc, focus, etc.) ── */
  .eh-toolbar {{
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 0;
    flex-wrap: wrap;
  }}
  .eh-toolbar-btn {{
    width: 34px; height: 34px;
    display: flex; align-items: center; justify-content: center;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.15s;
    color: var(--text2);
    text-decoration: none;
  }}
  .eh-toolbar-btn:hover {{
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-bg);
  }}
  .eh-toolbar-btn.active {{
    background: var(--accent-bg);
    border-color: var(--accent);
    color: var(--accent);
  }}

  /* ── Calendar popup ── */
  .cal-popup {{
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: 12px;
    padding: 14px;
    margin: 8px 0;
    box-shadow: 0 8px 24px var(--card-shadow);
  }}
  .cal-event {{
    display: flex; align-items: center; gap: 6px;
    padding: 5px 8px; border-radius: 6px;
    background: var(--bg3); border: 1px solid var(--border);
    margin-bottom: 4px; font-size: 0.78rem; color: var(--text2);
  }}
  .cal-event .cal-dot {{
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--accent); flex-shrink: 0;
  }}

  /* ── Calculator ── */
  .calc-popup {{
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: 12px;
    padding: 14px;
    margin: 8px 0;
    box-shadow: 0 8px 24px var(--card-shadow);
  }}
  .calc-display {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
    font-family: var(--mono);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
    text-align: right;
    margin-bottom: 10px;
    min-height: 52px;
    word-break: break-all;
  }}
  .calc-btn-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 4px;
  }}
  .calc-btn {{
    padding: 10px 4px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg3);
    color: var(--text);
    font-family: var(--mono);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.12s;
    text-align: center;
  }}
  .calc-btn:hover {{
    background: var(--accent-bg);
    border-color: var(--accent);
    color: var(--accent);
  }}
  .calc-btn.op {{
    background: var(--accent-bg);
    border-color: var(--accent-bd);
    color: var(--accent);
  }}
  .calc-btn.eq {{
    background: var(--accent);
    color: white;
    border-color: var(--accent);
    grid-column: span 1;
  }}

  /* ── Bookmark ── */
  .bm-btn {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    color: var(--text3);
    font-size: 0.72rem;
    cursor: pointer;
    transition: all 0.15s;
    margin-top: 4px;
  }}
  .bm-btn:hover {{
    color: var(--accent);
    border-color: var(--accent-bd);
    background: var(--accent-bg);
  }}

  /* ── Focus mode Hardened ── */
  .focus-active [data-testid="stSidebar"],
  .focus-active .stat-row,
  .focus-active .section-label,
  .focus-active .tool-card,
  .focus-active .click-container,
  .focus-active .poweredby,
  .focus-active hr,
  .focus-active .eh-toolbar {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
  }}
  
  .focus-active .main .block-container {{
    max-width: 900px !important;
    padding-top: 2rem !important;
  }}

  .focus-banner {{
    background: linear-gradient(90deg, #f59e0b, var(--accent));
    color: white;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(245, 158, 11, 0.2);
    animation: slideDown 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
  }}
  @keyframes slideDown {{ from {{ transform: translateY(-30px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
</style>
"""


st.markdown(get_theme_css(), unsafe_allow_html=True)

# Inject light-mode / focus-mode body classes
_body_classes = []
if st.session_state.get("theme_mode") == "light":
    _body_classes.append("light-active")
if st.session_state.get("focus_mode"):
    _body_classes.append("focus-active")
if _body_classes:
    _cls_js = " ".join(_body_classes)
    st.markdown(f"""<script>document.body.classList.add(..."{_cls_js}".split(" "));</script>""", unsafe_allow_html=True)
else:
    st.markdown("""<script>document.body.classList.remove("light-active","focus-active");</script>""", unsafe_allow_html=True)


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

    # If Focus Mode is ON, we physically remove distractions from the DOM
    if not st.session_state.get("focus_mode"):
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

        st.markdown('<div class="section-label">🎙️ Global Voice</div>', unsafe_allow_html=True)
        v_mode = st.toggle("Voice Mode ON", value=st.session_state.get("voice_mode", False), key="voice_toggle")
        if v_mode != st.session_state.get("voice_mode", False):
            st.session_state.voice_mode = v_mode
            st.rerun()

        st.divider()

    # ── Toolbar Row ──────────────────────────
    tb1, tb2, tb3, tb4, tb5, tb6 = st.columns(6)
    with tb1:
        if st.button("📅", key="tb_cal", help="Calendar", use_container_width=True):
            st.session_state.calculator_open = False
            st.session_state.chat_history_open = False
            st.session_state["calendar_open"] = not st.session_state.get("calendar_open", False)
            st.rerun()
    with tb2:
        if st.button("🧮", key="tb_calc", help="Calculator", use_container_width=True):
            st.session_state["calendar_open"] = False
            st.session_state.chat_history_open = False
            st.session_state.calculator_open = not st.session_state.calculator_open
            st.rerun()
    with tb3:
        if st.button("📈", key="tb_graph", help="Graph Plotter", use_container_width=True):
            st.session_state.app_mode = "graph"
            st.rerun()
    with tb4:
        focus_icon = "🔕" if st.session_state.focus_mode else "🔔"
        if st.button(focus_icon, key="tb_focus", help="Focus Mode", use_container_width=True):
            st.session_state.focus_mode = not st.session_state.focus_mode
            st.rerun()
    with tb5:
        if st.button("🔖", key="tb_bm", help="Bookmarks", use_container_width=True):
            st.session_state["bookmarks_open"] = not st.session_state.get("bookmarks_open", False)
            st.rerun()
    with tb6:
        if st.button("📜", key="tb_hist", help="Chat History", use_container_width=True):
            st.session_state.chat_history_open = not st.session_state.chat_history_open
            st.rerun()

    # ── Calendar Popup ────────────────────────
    if st.session_state.get("calendar_open"):
        st.markdown('<div class="section-label">📅 Calendar</div>', unsafe_allow_html=True)
        cal_date = st.date_input("Date", value=datetime.date.today(), label_visibility="collapsed", key="cal_pick")
        cal_note = st.text_input("Event note", placeholder="e.g. Physics exam Ch.5", label_visibility="collapsed", key="cal_note")
        if st.button("➕ Save Event", use_container_width=True, key="cal_save"):
            if cal_note:
                date_key = cal_date.isoformat()
                if date_key not in st.session_state.calendar_events:
                    st.session_state.calendar_events[date_key] = []
                st.session_state.calendar_events[date_key].append(cal_note)
                st.success(f"Saved: {cal_note} on {cal_date.strftime('%b %d')}")
        # Show upcoming events
        today_str = datetime.date.today().isoformat()
        upcoming = {k: v for k, v in sorted(st.session_state.calendar_events.items()) if k >= today_str}
        if upcoming:
            for date_k, events in list(upcoming.items())[:5]:
                for ev in events:
                    d_label = datetime.date.fromisoformat(date_k).strftime("%b %d")
                    st.markdown(f'<div class="cal-event"><span class="cal-dot"></span><strong>{d_label}</strong> — {ev}</div>', unsafe_allow_html=True)
        else:
            st.caption("No upcoming events")

    # ── Calculator Popup ──────────────────────
    if st.session_state.calculator_open:
        import math
        c_lbl1, c_lbl2 = st.columns([4, 1])
        with c_lbl1:
            st.markdown('<div class="section-label">🧮 Scientific Calculator</div>', unsafe_allow_html=True)
        with c_lbl2:
            if st.button("⛶", key="calc_fullscreen_btn", help="Expand Full Screen", use_container_width=True):
                st.session_state.app_mode = "calculator"
                st.session_state.calculator_open = False
                st.rerun()
                
        if "calc_expr" not in st.session_state:
            st.session_state.calc_expr = ""
            st.session_state.calc_result = ""
        
        calc_input = st.text_input(
            "Expression", 
            value=st.session_state.calc_expr,
            placeholder="e.g. 5+5, sin(pi/4)",
            label_visibility="collapsed",
            key="calc_input_field"
        )
        
        if calc_input != st.session_state.calc_expr:
            st.session_state.calc_expr = calc_input
            
        def _add_calc(val):
            if st.session_state.calc_result and st.session_state.calc_result != "Error":
                if val in ["+", "−", "×", "÷", "^", "%"]:
                    st.session_state.calc_expr = st.session_state.calc_result + val
                else: 
                    st.session_state.calc_expr = val
                st.session_state.calc_result = ""
            else:
                st.session_state.calc_expr += val

        def _eval_calc():
            st.session_state.calc_result = AppController.evaluate_expression(st.session_state.calc_expr)
            if st.session_state.calc_result != "Error":
                st.session_state.calc_expr = st.session_state.calc_result
            
        s1, s2, s3, s4, s5 = st.columns(5)
        for lbl, val, col in [("sin", "sin(", s1), ("cos", "cos(", s2), ("tan", "tan(", s3), ("log", "log(", s4), ("ln", "ln(", s5)]:
            with col: 
                if st.button(lbl, key=f"cb_{lbl}", use_container_width=True): _add_calc(val); st.rerun()
        s6, s7, s8, s9, s10 = st.columns(5)
        for lbl, val, col in [("√", "√(", s6), ("π", "π", s7), ("(", "(", s8), (")", ")", s9), ("e", "e", s10)]:
            with col:
                if st.button(lbl, key=f"cb_{lbl}", use_container_width=True): _add_calc(val); st.rerun()
                
        r1_1, r1_2, r1_3, r1_4, r1_5 = st.columns(5)
        for lbl, val, col in [("7", "7", r1_1), ("8", "8", r1_2), ("9", "9", r1_3), ("÷", "÷", r1_4)]:
            with col:
                if st.button(lbl, key=f"cb_{lbl}", use_container_width=True): _add_calc(val); st.rerun()
        with r1_5:
            if st.button("⌫", key="cb_bk", use_container_width=True):
                st.session_state.calc_expr = st.session_state.calc_expr[:-1]
                st.rerun()
                
        r2_1, r2_2, r2_3, r2_4, r2_5 = st.columns(5)
        for lbl, val, col in [("4", "4", r2_1), ("5", "5", r2_2), ("6", "6", r2_3), ("×", "×", r2_4), ("^", "^", r2_5)]:
            with col:
                if st.button(lbl, key=f"cb_{lbl}", use_container_width=True): _add_calc(val); st.rerun()
                
        r3_1, r3_2, r3_3, r3_4, r3_5 = st.columns(5)
        for lbl, val, col in [("1", "1", r3_1), ("2", "2", r3_2), ("3", "3", r3_3), ("−", "−", r3_4), ("%", "%", r3_5)]:
            with col:
                if st.button(lbl, key=f"cb_{lbl}", use_container_width=True): _add_calc(val); st.rerun()
                
        r4_1, r4_2, r4_3, r4_4, r4_5 = st.columns(5)
        with r4_1:
            if st.button("C", key="cb_clr", use_container_width=True):
                st.session_state.calc_expr = ""
                st.session_state.calc_result = ""
                st.rerun()
        with r4_2:
            if st.button("0", key="cb_0", use_container_width=True): _add_calc("0"); st.rerun()
        with r4_3:
            if st.button(".", key="cb_dot", use_container_width=True): _add_calc("."); st.rerun()
        with r4_4:
            if st.button("=", key="cb_eq", type="primary", use_container_width=True):
                _eval_calc(); st.rerun()
        with r4_5:
            if st.button("+", key="cb_plus", use_container_width=True): _add_calc("+"); st.rerun()
                
        if st.session_state.calc_result:
            bg_col = "var(--green-bg)" if st.session_state.calc_result != "Error" else "rgba(248,113,113,0.08)"
            txt_col = "var(--green)" if st.session_state.calc_result != "Error" else "var(--red)"
            st.markdown(f'<div style="background:{bg_col};border-radius:8px;padding:10px 14px;font-family:var(--mono);font-size:1.1rem;font-weight:700;color:{txt_col};text-align:right;">{st.session_state.calc_result}</div>', unsafe_allow_html=True)

    # ── Bookmarks Panel ───────────────────────
    if st.session_state.get("bookmarks_open"):
        st.markdown('<div class="section-label">🔖 Bookmarks</div>', unsafe_allow_html=True)
        if st.session_state.bookmarks:
            for i, bm in enumerate(st.session_state.bookmarks):
                role_icon = "👤" if bm.get("role") == "user" else "🎓"
                preview = bm.get("content", "")[:80] + ("…" if len(bm.get("content", "")) > 80 else "")
                col_bm, col_del = st.columns([5, 1])
                with col_bm:
                    st.markdown(f'<div class="cal-event"><span class="cal-dot"></span>{role_icon} {preview}</div>', unsafe_allow_html=True)
                with col_del:
                    if st.button("✕", key=f"del_bm_{i}", use_container_width=True):
                        st.session_state.bookmarks.pop(i)
                        st.rerun()
        else:
            st.caption("No bookmarks yet. Use 🔖 in chat to save messages.")

    # ── Chat History Panel ────────────────────
    if st.session_state.chat_history_open:
        st.markdown('<div class="section-label">📜 Chat History</div>', unsafe_allow_html=True)
        if st.session_state.persistent_sessions:
            for sname, sdata in st.session_state.persistent_sessions.items():
                ts = sdata.get("timestamp", "")[:10]
                msg_n = len(sdata.get("messages", []))
                col_h1, col_h2 = st.columns([4, 1])
                with col_h1:
                    st.markdown(f'<div class="cal-event"><span class="cal-dot"></span><strong>{sname}</strong> · {msg_n} msgs · {ts}</div>', unsafe_allow_html=True)
                with col_h2:
                    if st.button("📂", key=f"load_h_{sname}", use_container_width=True):
                        st.session_state.messages = sdata["messages"]
                        st.session_state.context_text = sdata.get("context", "")
                        st.session_state.context_sources = sdata.get("sources", [])
                        st.session_state.chat_history_open = False
                        st.rerun()
        else:
            st.caption("No saved sessions yet. Save one from sidebar.")

    # ── API Key (collapsed) ───────────────────
    override = _get_override_key()
    active_key = key_manager.get_key(override=override)
    if not active_key:
        with st.expander("🔑 Add API Key"):
            manual_key = st.text_input("Groq API Key", type="password", placeholder="gsk_…", help="Get a free key at console.groq.com", key="api_key_input")
            if manual_key:
                st.session_state["manual_api_key"] = manual_key
                st.success("Key saved!", icon="✅")

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
        icons = {"pdf": "📄", "youtube": "▶️", "web": "🌐", "ocr": "📸"}
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
            st.session_state.context_text = ""
            st.session_state.context_sources = []
            st.rerun()

    # ── Academic Goals (New Addition) ─────────
    st.markdown('<div class="section-label">🎯 Academic Goals</div>', unsafe_allow_html=True)
    if "study_goals" not in st.session_state: st.session_state.study_goals = []
    new_goal = st.text_input("Add Goal", placeholder="+ New study goal...", label_visibility="collapsed", key="goal_in")
    if new_goal and st.button("Add", use_container_width=True):
        st.session_state.study_goals.append({"text": new_goal, "done": False})
        st.rerun()
    for i, g in enumerate(st.session_state.study_goals):
        checked = st.checkbox(g["text"], value=g["done"], key=f"goal_{i}")
        if checked != g["done"]:
            st.session_state.study_goals[i]["done"] = checked
    
    st.divider()
    
    # ── Focus Timer ──────────────────────────
    st.markdown('<div class="section-label">⏱️ Focus Timer</div>', unsafe_allow_html=True)
    if "timer_running" not in st.session_state: st.session_state.timer_running = False
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.session_state.timer_start = st.number_input("Mins", min_value=1, max_value=120, value=25, label_visibility="collapsed")
    with col_t2:
        if st.button("▶️ Go" if not st.session_state.timer_running else "⏹️ Stop", use_container_width=True):
            st.session_state.timer_running = not st.session_state.timer_running
    
    # ── OCR / Notes Scanner ─────────────────
    st.markdown('<div class="section-label">📸 Notes Scanner (OCR)</div>', unsafe_allow_html=True)
    scanned_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="ocr_up")
    if scanned_file:
        if st.button("🔍 Run OCR Scan", use_container_width=True):
            with st.spinner("Extracting text from image..."):
                ocr_text = extract_text_from_image(scanned_file.read())
                if ocr_text.startswith("Error"):
                    st.error(ocr_text)
                else:
                    add_context(f"OCR Scan: {scanned_file.name}\n\n{ocr_text}", scanned_file.name, "ocr")
                    st.success(f"✅ Scanned text loaded — {len(ocr_text.split())} words extracted!")

    # ── Mastery Tracker ──────────────────────
    st.markdown('<div class="section-label">📈 Mastery Tracker</div>', unsafe_allow_html=True)
    # Build mastery data from session activity
    _mastery = {}
    if st.session_state.get("card_mastery"):
        passed = sum(1 for v in st.session_state.card_mastery.values() if v == "pass")
        total_cards = len(st.session_state.card_mastery)
        _mastery["Recall"] = int((passed / max(1, total_cards)) * 100)
    if st.session_state.get("quiz_score") and st.session_state.get("quiz_data"):
        _mastery["Comprehension"] = int((st.session_state.quiz_score / max(1, len(st.session_state.quiz_data))) * 100)
    radar_chart = get_subject_mastery_radar(_mastery)
    if radar_chart:
        st.plotly_chart(radar_chart, use_container_width=True, config={'displayModeBar': False})

    # ── Exam Countdown ──────────────────────
    st.markdown('<div class="section-label">🗓️ Exam Countdown</div>', unsafe_allow_html=True)
    if "exam_date" not in st.session_state: st.session_state.exam_date = datetime.date.today() + datetime.timedelta(days=30)
    
    col_e1, col_e2 = st.columns([2, 1])
    with col_e1:
         st.session_state.exam_date = st.date_input("Date", value=st.session_state.exam_date, label_visibility="collapsed")
    with col_e2:
        days_left = (st.session_state.exam_date - datetime.date.today()).days
        color = "var(--green)" if days_left > 14 else "var(--accent)"
        st.markdown(f'<div style="text-align:center; font-weight:800; color:{color}; font-size:1.1rem; padding-top:4px;">{days_left}d</div>', unsafe_allow_html=True)

    # ── Model Intelligence Toggle ────────────
    intelligence_level = st.select_slider(
        "Performance vs Accuracy",
        options=["Fast (8B)", "Smart (70B)"],
        value="Smart (70B)",
        label_visibility="collapsed"
    )
    st.session_state.model_choice = "llama-3.1-8b-instant" if "Fast" in intelligence_level else "llama-3.3-70b-versatile"

    # ── Context Intelligence Dashboard ────────
    if st.session_state.context_text:
        st.markdown('<div class="section-label">📜 Context Summary</div>', unsafe_allow_html=True)
        ctx_hash = hash(st.session_state.context_text)
        if "last_context_summary" not in st.session_state or st.session_state.get("last_context_hash") != ctx_hash:
            with st.spinner("Analyzing content..."):
                try:
                    override_k = _get_override_key()
                    summary_prompt = [
                        {"role": "system", "content": "Briefly summarize the core topics of this material in exactly 3 bullet points with emojis. Be concise."},
                        {"role": "user", "content": st.session_state.context_text[:6000]}
                    ]
                    st.session_state.last_context_summary = chat_with_groq(
                        summary_prompt, model="llama-3.1-8b-instant", override_key=override_k
                    )
                    st.session_state.last_context_hash = ctx_hash
                except Exception:
                    st.session_state.last_context_summary = "📚 Study material loaded and ready for questions."
        
        st.markdown(f'<div style="font-size:0.75rem; color:var(--text3); line-height:1.4; background:var(--bg3); padding:10px; border-radius:8px; border-left:3px solid var(--accent);">{st.session_state.last_context_summary}</div>', unsafe_allow_html=True)

    # ── Academic Progress ─────────────────────
    st.markdown('<div class="section-label">📈 Session Progress</div>', unsafe_allow_html=True)
    concepts_total = len(st.session_state.context_sources)
    actual_words = len(st.session_state.context_text.split()) if st.session_state.context_text else 0
    concepts_pct = int(min(100.0, float(concepts_total) * 10.0))
    words_pct = int(min(100.0, float(actual_words) / 100.0))
    
    st.markdown(f"""
    <div style="background:var(--bg3); border:1px solid var(--border); border-radius:10px; padding:12px; margin-bottom:1rem;">
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text3); margin-bottom:4px;">
            <span>Sources Loaded</span> <span>{concepts_total}</span>
        </div>
        <div style="height:4px; background:var(--bg2); border-radius:2px; margin-bottom:10px;">
            <div style="width:{concepts_pct}%; height:100%; background:var(--accent); border-radius:2px;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text3); margin-bottom:4px;">
            <span>Knowledge Density</span> <span>{actual_words:,} words</span>
        </div>
        <div style="height:4px; background:var(--bg2); border-radius:2px;">
            <div style="width:{words_pct}%; height:100%; background:var(--accent); border-radius:2px; opacity:0.6;"></div>
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

if st.session_state.focus_mode:
    st.markdown('<div class="focus-banner">🔒 Focus Mode Active — All distractions are suppressed. Deep work in progress.</div>', unsafe_allow_html=True)

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
                cards = AppController.generate_flashcards(st.session_state.context_text, lang, _get_override_key())
                if cards:
                    st.session_state.flashcards = cards
                    st.session_state.current_card = 0
                else:
                    st.error("⚠️ Failed to generate flashcards after multiple attempts. Please try again or check your API keys.")
        
        if st.session_state.flashcards:
            cards = st.session_state.flashcards
            idx = st.session_state.current_card
            card = cards[idx]
            
            st.markdown(f"### {lang} Flashcard {idx + 1} / {len(cards)}")
            
            with st.container():
                diff_color = {"easy": "var(--green)", "medium": "var(--accent)", "hard": "var(--red)"}.get(str(card.get('difficulty')).lower(), "var(--text3)")
                st.markdown(f"""
                <div style="background:var(--bg3); border:2px solid var(--accent); border-radius:15px; padding:40px; text-align:center; min-height:220px; display:flex; align-items:center; justify-content:center; flex-direction:column; margin-bottom:20px; box-shadow: 0 10px 40px rgba(0,0,0,0.25);">
                    <div style="display:flex; justify-content:space-between; width:100%; margin-top:-20px; margin-bottom:20px;">
                        <span style="font-size:0.75rem; color:var(--text2); background:var(--bg2); padding:4px 10px; border-radius:12px;">{card.get('subject', 'General')}</span>
                        <span style="font-size:0.75rem; color:{diff_color}; background:var(--bg2); border:1px solid {diff_color}; padding:4px 10px; border-radius:12px; font-weight:700;">{card.get('difficulty', 'Normal')}</span>
                    </div>
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
            
            is_last = idx == len(cards) - 1
            if not is_last:
                col_a, col_b, col_c = st.columns([1,1,1])
            else:
                col_a, col_b, col_c, col_d = st.columns([1,1,1,1])
            
            with col_a:
                if st.button("❌ Need more", use_container_width=True):
                    if "card_mastery" not in st.session_state: st.session_state.card_mastery = {}
                    st.session_state.card_mastery[idx] = "fail"
                    if not is_last:
                        st.session_state.current_card += 1
                        st.rerun()
            with col_b:
                if st.button("💾 Save Deck", use_container_width=True):
                    summary = "\n".join([f"Q: {c['q']} | A: {c['a']}" for c in cards])
                    st.session_state.messages.append({"role": "assistant", "content": f"### 🃏 Generated Flashcards ({lang})\n\n{summary}"})
                    st.success("Saved!")
                if st.button("🔊 Speak", use_container_width=True):
                    AppController.speak(f"Question: {card['q']}. Answer: {card['a']}")
            with col_c:
                if st.button("✅ Got it", use_container_width=True):
                    if "card_mastery" not in st.session_state: st.session_state.card_mastery = {}
                    st.session_state.card_mastery[idx] = "pass"
                    if not is_last:
                        st.session_state.current_card += 1
                        st.rerun()
            if is_last:
                with col_d:
                    if st.button("🏁 Finish", use_container_width=True):
                        st.session_state.flashcards = []
                        st.session_state.card_mastery = {}
                        st.session_state.current_card = 0
                        st.rerun()

            # Progress Bar
            mastery_count = sum(1 for v in st.session_state.get("card_mastery", {}).values() if v == "pass")
            st.markdown(f"""
            <div style="font-size:0.7rem; color:var(--text3); margin-top:10px;">Mastery: {mastery_count} / {len(cards)}</div>
            <div style="height:4px; background:var(--bg2); border-radius:2px; margin-top:4px;">
                <div style="width:{int((mastery_count/len(cards))*100)}%; height:100%; background:var(--green); border-radius:2px;"></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Export Buttons (New Addition)
            st.divider()
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                st.download_button("📤 JSON Export", json.dumps(cards, indent=2), "deck.json", use_container_width=True)
            with col_ex2:
                if pd is not None:
                    df = pd.DataFrame(cards)
                    st.download_button("📊 CSV Export", df.to_csv(index=False), "deck.csv", use_container_width=True)
                else:
                    csv_lines = ["question,answer"] + [f'"{c["q"]}","{c["a"]}"' for c in cards]
                    st.download_button("📊 CSV Export", "\n".join(csv_lines), "deck.csv", use_container_width=True)
    st.stop()

elif app_mode == "calculator":
    st.markdown("## 🧮 Advanced Scientific Calculator")
    st.markdown("A massively powerful, full-screen scientific and programmatic computation engine.")
    
    import math as _math
    if "fs_calc_expr" not in st.session_state:
        st.session_state.fs_calc_expr = ""
        st.session_state.fs_calc_result = ""
        st.session_state.fs_calc_history = []
        
    calc_col1, calc_col2 = st.columns([3, 1])
    
    with calc_col1:
        fs_input = st.text_input("Mathematical Expression", value=st.session_state.fs_calc_expr, key="fs_calc_input", placeholder="e.g. sin(pi/4), log(100), 15 % 4")
        if fs_input != st.session_state.fs_calc_expr:
            st.session_state.fs_calc_expr = fs_input
            
        def _add_fsc(val):
            if st.session_state.fs_calc_result and st.session_state.fs_calc_result != "Error":
                if val in ["+", "−", "×", "÷", "^", "%"]:
                    st.session_state.fs_calc_expr = st.session_state.fs_calc_result + val
                else: 
                    st.session_state.fs_calc_expr = val
                st.session_state.fs_calc_result = ""
            else:
                st.session_state.fs_calc_expr += val
                
        def _eval_fsc():
            expr_to_eval = st.session_state.fs_calc_expr
            st.session_state.fs_calc_result = AppController.evaluate_expression(expr_to_eval)
            if st.session_state.fs_calc_result != "Error":
                st.session_state.fs_calc_history.append(f"{expr_to_eval} = {st.session_state.fs_calc_result}")
                if len(st.session_state.fs_calc_history) > 10: st.session_state.fs_calc_history.pop(0)
                st.session_state.fs_calc_expr = st.session_state.fs_calc_result
                
        g1, g2, g3, g4, g5, g6 = st.columns(6)
        btns_row1 = [("sin", "sin(", g1), ("cos", "cos(", g2), ("tan", "tan(", g3), ("asin", "asin(", g4), ("acos", "acos(", g5), ("atan", "atan(", g6)]
        g7, g8, g9, g10, g11, g12 = st.columns(6)
        btns_row2 = [("log", "log10(", g7), ("ln", "log(", g8), ("log2", "log2(", g9), ("e", "e", g10), ("π", "π", g11), ("√", "√(", g12)]
        g13, g14, g15, g16, g17, g18 = st.columns(6)
        
        btns_row3 = [("7", "7", g13), ("8", "8", g14), ("9", "9", g15), ("÷", "÷", g16), ("(", "(", g17), (")", ")", g18)]
        g19, g20, g21, g22, g23, g24 = st.columns(6)
        btns_row4 = [("4", "4", g19), ("5", "5", g20), ("6", "6", g21), ("×", "×", g22), ("|x|", "abs(", g23), ("mod", "%", g24)]
        g25, g26, g27, g28, g29, g30 = st.columns(6)
        btns_row5 = [("1", "1", g25), ("2", "2", g26), ("3", "3", g27), ("−", "−", g28), ("x²", "**2", g29), ("^", "^", g30)]
        g31, g32, g33, g34, g35, g36 = st.columns(6)
        
        for name, val, col in btns_row1 + btns_row2 + btns_row3 + btns_row4 + btns_row5:
            with col:
                if st.button(name, key=f"fsc_{name}", use_container_width=True):
                    _add_fsc(val); st.rerun()
                    
        with g31:
            if st.button("C", key="fsc_clr", use_container_width=True):
                st.session_state.fs_calc_expr = ""
                st.session_state.fs_calc_result = ""
                st.rerun()
        with g32:
            if st.button("0", key="fsc_0", use_container_width=True): _add_fsc("0"); st.rerun()
        with g33:
            if st.button(".", key="fsc_dot", use_container_width=True): _add_fsc("."); st.rerun()
        with g34:
            if st.button("=", key="fsc_eq", type="primary", use_container_width=True):
                _eval_fsc(); st.rerun()
        with g35:
            if st.button("+", key="fsc_plus", use_container_width=True): _add_fsc("+"); st.rerun()
        with g36:
            if st.button("⌫", key="fsc_bk", use_container_width=True):
                st.session_state.fs_calc_expr = st.session_state.fs_calc_expr[:-1]
                st.rerun()
                
        if st.session_state.fs_calc_result:
            bg_col = "var(--green-bg)" if st.session_state.fs_calc_result != "Error" else "rgba(248,113,113,0.08)"
            txt_col = "var(--green)" if st.session_state.fs_calc_result != "Error" else "var(--red)"
            st.markdown(f'<div style="background:{bg_col};border:1px solid {txt_col};border-radius:15px;padding:25px;font-family:var(--mono);font-size:2.4rem;font-weight:800;color:{txt_col};text-align:right;box-shadow: 0 8px 32px {bg_col};margin-top:20px;">{st.session_state.fs_calc_result}</div>', unsafe_allow_html=True)

    with calc_col2:
        st.markdown('<div class="section-label" style="font-size:0.8rem;">📜 Ledger History</div>', unsafe_allow_html=True)
        if st.session_state.fs_calc_history:
            for item in reversed(st.session_state.fs_calc_history):
                st.markdown(f'<div style="background:var(--bg3); border-radius:8px; padding:10px; font-family:var(--mono); font-size:0.85rem; color:var(--text); margin-bottom:8px; border:1px solid var(--border); box-shadow: 0 2px 4px rgba(0,0,0,0.05);">{item}</div>', unsafe_allow_html=True)
        else:
            st.caption("No history.")
    st.stop()

elif app_mode == "graph":
    from utils.graph_engine import plot_2d_graph, plot_3d_graph
    st.header("📈 Elite Advanced Graphing")
    
    t_2d, t_3d = st.tabs(["2D Functions", "3D Surfaces"])
    
    with t_2d:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown('<div class="section-label">Inputs</div>', unsafe_allow_html=True)
            func_str = st.text_input("f(x) List (comma-separated)", value="sin(x), cos(x)", help="e.g. x**2, sin(a*x)")
            
            c_min, c_max = st.columns(2)
            with c_min:
                x_min = float(st.number_input("X Min", value=-10.0))
            with c_max:
                x_max = float(st.number_input("X Max", value=10.0))
                
            show_deriv = st.checkbox("Show Derivatives f'(x)")
            shade_area = st.checkbox("Shade Curve Areas")
            
        with col2:
            funcs = [f.strip() for f in func_str.split(",") if f.strip()]
            if funcs:
                fig, errs = plot_2d_graph(funcs, x_min=x_min, x_max=x_max, points=500, theme="dark", show_derivative=show_deriv, shade_area=shade_area)
                if errs:
                    for e in errs: st.error(e)
                if fig:
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Start typing mathematically valid f(x) equations to plot them.")

    with t_3d:
        col3, col4 = st.columns([1, 3])
        with col3:
            st.markdown('<div class="section-label">3D Coordinates</div>', unsafe_allow_html=True)
            f3d_str = st.text_input("Z = f(x, y)", value="sin(x*y)", help="e.g. x**2 + y**2")
            
            c3_min, c3_max = st.columns(2)
            with c3_min:
                x3_min = float(st.number_input("X Start", value=-5.0))
                y3_min = float(st.number_input("Y Start", value=-5.0))
            with c3_max:
                x3_max = float(st.number_input("X End", value=5.0))
                y3_max = float(st.number_input("Y End", value=5.0))
                
            res3d = st.slider("Quality Mesh", min_value=15, max_value=80, value=40)
            
        with col4:
            if f3d_str.strip():
                fig3, errs3 = plot_3d_graph(f3d_str, x_min=x3_min, x_max=x3_max, y_min=y3_min, y_max=y3_max, resolution=res3d, theme="dark")
                if errs3:
                    for e in errs3: st.error(e)
                if fig3:
                    fig3.update_layout(height=650)
                    st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Input a z=function to start charting in 3 dimensions.")
    st.stop()

elif app_mode == "quiz":
    st.header("📝 Smart Quiz Mode")
    lang = st.session_state.get("selected_language", "English")
    if not st.session_state.context_text:
        st.warning(f"Please upload context to start a {lang} quiz.")
    else:
        if st.button(f"🪄 Build {lang} Quiz"):
            with st.spinner("Generating challenges..."):
                q_data = AppController.generate_quiz(st.session_state.context_text, lang, _get_override_key())
                if q_data:
                    st.session_state.quiz_data = q_data
                    st.session_state.quiz_current = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_feedback = None
                else:
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
                    type_f, msg_f = st.session_state.quiz_feedback
                    if type_f == "success": st.success(msg_f)
                    else: st.error(msg_f)
                    
                    col_expl, col_cont = st.columns([1,1])
                    with col_expl:
                        if st.button("💡 Explain more", use_container_width=True):
                            st.session_state.queued_prompt = f"Explain the concept behind this question more deeply: {q['q']}. The correct answer was {q['correct']}. Context: {q['explanation']}"
                            st.session_state.app_mode = "chat"
                            st.rerun()
                    with col_cont:
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
                    # Extract mermaid code from markdown fences
                    if "```mermaid" in mm_code:
                        mm_code = mm_code.split("```mermaid", 1)[1]
                        end_idx = mm_code.find("```")
                        if end_idx != -1:
                            mm_code = mm_code[:end_idx]
                    elif "```" in mm_code:
                        parts = mm_code.split("```")
                        if len(parts) >= 3:
                            mm_code = parts[1]
                            # Strip language identifier if present
                            if mm_code.startswith("\n"):
                                mm_code = mm_code[1:]
                            elif mm_code.split("\n", 1)[0].strip().isalpha():
                                mm_code = mm_code.split("\n", 1)[1] if "\n" in mm_code else mm_code
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
    
    col_pl1, col_pl2 = st.columns([2, 1])
    with col_pl1:
        new_task = st.text_input("New Study Task", placeholder="e.g. read chapter 5", label_visibility="collapsed")
    with col_pl2:
        task_deadline = st.date_input("Deadline", label_visibility="collapsed")
        
    if st.button("➕ Add Task", use_container_width=True) and new_task:
        st.session_state.study_tasks.append({
            "task": new_task,
            "deadline": task_deadline.isoformat(),
            "done": False
        })
        st.rerun()
        
    if not st.session_state.context_text:
        st.info("Upload notes to auto-generate tasks from topics.")
    else:
        if st.button("🪄 Auto-Generate Plan from Notes", use_container_width=True):
            with st.spinner(f"Scheduling in {lang}..."):
                prompt = [
                    {"role": "system", "content": f"Extract 5 discrete study tasks from this material. Format strictly as JSON: {{\"tasks\": [\"Task 1\", \"Task 2\"]}}"},
                    {"role": "user", "content": f"Study Context: {st.session_state.context_text[:12000]}"}
                ]
                auto_tasks = AppController._fetch_json(prompt, _get_override_key())
                if auto_tasks:
                    import datetime as dt
                    deadline = dt.date.today() + dt.timedelta(days=1)
                    for t in auto_tasks:
                        st.session_state.study_tasks.append({
                            "task": t, "deadline": deadline.isoformat(), "done": False
                        })
                    st.rerun()

    st.markdown("### 📋 Daily Task List")
    if not st.session_state.study_tasks:
        st.caption("No tasks yet. Add one above or auto-generate from notes.")
    else:
        sorted_tasks = sorted(st.session_state.study_tasks, key=lambda x: (x['done'], x['deadline']))
        for idx, task in enumerate(sorted_tasks):
            cols = st.columns([1, 6, 3, 2])
            with cols[0]:
                is_done = st.checkbox("", value=task['done'], key=f"t_done_{idx}_{task['task']}")
                if is_done != task['done']:
                    for orig_t in st.session_state.study_tasks:
                        if orig_t['task'] == task['task'] and orig_t['deadline'] == task['deadline']:
                            orig_t['done'] = is_done
                    st.rerun()
            with cols[1]:
                if not task['done']: st.markdown(f"**{task['task']}**")
                else: st.markdown(f"~~{task['task']}~~")
            with cols[2]:
                st.caption(f"📅 {task['deadline']}")
            with cols[3]:
                if st.button("🗑️", key=f"t_del_{idx}_{task['task']}"):
                    st.session_state.study_tasks.remove(task)
                    st.rerun()
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
for i_msg, msg in enumerate(st.session_state.messages):
    avatar = "🎓" if msg["role"] == "assistant" else "👤"
    if msg["role"] == "assistant" and persona and st.session_state.selected_persona != "Default (ExamHelp)":
        avatar = persona["emoji"]
        
    with st.chat_message(msg["role"], avatar=avatar):
        # Hidden hook for CSS targeting right-alignment on User
        if msg["role"] == "user":
            st.markdown("<div class='user-message-hook'></div>", unsafe_allow_html=True)
            
        st.markdown(msg["content"])
        
        # Professional Action Bar (ChatGPT-style)
        if msg["role"] == "assistant":
            # Add subtle divider
            st.markdown("<hr style='border: none; border-top: 1px dashed var(--bd-glass); margin: 12px 0;'>", unsafe_allow_html=True)
            
            from chat.feedback import ChatFeedback
            from chat.share import ChatShare
            
            c1, c2, c3, c4, c5, c_fill = st.columns([1, 1, 1, 1, 1, 7])
            with c1:
                if st.button("👍", key=f"like_{i_msg}", help="Good response", use_container_width=True):
                    ChatFeedback.save_feedback(f"msg_{i_msg}", True)
            with c2:
                if st.button("👎", key=f"dislike_{i_msg}", help="Bad response", use_container_width=True):
                    ChatFeedback.save_feedback(f"msg_{i_msg}", False)
            with c3:
                if st.button("📋", key=f"copy_{i_msg}", help="Copy response", use_container_width=True):
                    try:
                        import pyperclip
                        pyperclip.copy(msg["content"])
                        st.toast("Copied to clipboard!", icon="📋")
                    except Exception:
                        st.toast("Clipboard API unavailable. Select and copy manually.", icon="⚠️")
            with c4:
                if st.button("🔄", key=f"regen_{i_msg}", help="Regenerate this response", use_container_width=True):
                    if i_msg == len(st.session_state.messages) - 1:
                        st.session_state.queued_prompt = ChatFeedback.regenerate_prompt(st.session_state.messages)
                        st.rerun()
                    else:
                        st.toast("You can only regenerate the latest message directly.", icon="ℹ️")
            with c5:
                @st.dialog("🔗 Share Chat")
                def share_dialog(idx):
                    st.write("Share this specific conversation state automatically.")
                    code = ChatShare.generate_share_link(st.session_state.messages[:idx+1])
                    share_url = f"?chat={code}"
                    st.code(share_url, language="text")
                    st.info("Append this code block to the initial application URL inside a browser to share securely.")
                
                if st.button("🔗", key=f"share_{i_msg}", help="Share Chat State", use_container_width=True):
                    share_dialog(i_msg)

# ── Auto-scroll to bottom FAB ─────────────────
if st.session_state.messages:
    st.markdown("""
    <button class="scroll-fab" onclick="window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})" title="Scroll to bottom">⬇</button>
    """, unsafe_allow_html=True)

# ── Voice Input & Chat Input ────────────────────────────────
try:
    audio_val = st.audio_input("Record a voice question", label_visibility="collapsed")
except Exception:
    audio_val = None  # Graceful fallback if audio_input not supported

if audio_val and audio_val != st.session_state.get("last_audio"):
    st.session_state.last_audio = audio_val
    with st.spinner("Transcribing voice..."):
        try:
            audio_bytes = audio_val.read()
            if audio_bytes:
                transcript = transcribe_audio(audio_bytes, override_key=_get_override_key())
                if hasattr(transcript, "text") and transcript.text.strip():
                    st.session_state.queued_prompt = transcript.text
                    st.rerun()
                elif isinstance(transcript, str) and transcript.strip():
                    st.session_state.queued_prompt = transcript
                    st.rerun()
        except Exception as e:
            st.error(f"Voice transcription failed: {e}")

user_input = st.chat_input("Ask anything about your study material…", key="chat_input")

if st.session_state.queued_prompt:
    user_input = st.session_state.queued_prompt
    st.session_state.queued_prompt = None

# ── Smart Navigation & Calculus Triggers (Layer 2 - Active Routing)
if user_input and any(user_input.lower().startswith(kw) for kw in ["calculate ", "compute ", "calc ", "solve "]):
    calc_expr_voice = re.sub(r"^(calculate|compute|calc|solve)\s+", "", user_input, flags=re.IGNORECASE).strip()
    res = AppController.evaluate_expression(calc_expr_voice)
    if res and res != "Error":
        st.session_state.calc_expr = str(res)
        st.session_state.calc_result = str(res)
        user_input_disp = f"Calculate: `{calc_expr_voice}`"
        st.session_state.messages.append({"role": "user", "content": user_input_disp})
        st.session_state.messages.append({"role": "assistant", "content": f"🧮 **Calculation Result:**\n\n`{calc_expr_voice}` = **{res}**\n\n💡 Try the native Calculator mode (🧮) for continuous equations."})
        st.rerun()

elif user_input and any(user_input.lower().startswith(kw) for kw in ["plot ", "graph ", "draw graph "]):
    st.session_state.app_mode = "graph"
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": f"📈 **Graph Engine Activated**\n\nI have opened the multi-dimensional graph workspace in your active view."})
    st.rerun()

elif user_input and any(kw in user_input.lower() for kw in ["open quiz", "start quiz"]):
    st.session_state.app_mode = "quiz"
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": f"📝 **Quiz Mode Active**\n\nI have switched your workspace to the Smart Quiz Mode."})
    st.rerun()

elif user_input and any(kw in user_input.lower() for kw in ["open planner", "study planner"]):
    st.session_state.app_mode = "planner"
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": f"📅 **Planner Mode Active**\n\nYour interactive study planner is now open."})
    st.rerun()

# ── Standard Query Processing (Layer 4 - Fusion & Routing)
if user_input:
    override = _get_override_key()
    active_key = key_manager.get_key(override=override)

    if not active_key:
        st.error("No API key available. Please enter a Groq API key in the sidebar.", icon="🔑")
        st.stop()

    from utils.query_engine import QueryEngine
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
        
    # Determine the context injection
    with st.spinner("Consulting Multi-Intelligence Engine..."):
        augmented_prompt, matched_sources, intent = QueryEngine.route_and_enrich(user_input, st.session_state.get("context_text", ""))

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
        if "augmented_prompt" in locals():
            history[-1]["content"] = augmented_prompt # Invisible swap to hide API logic from UI 

        # Build persona prompt
        persona_prompt = ""
        if persona and st.session_state.selected_persona != "Default (ExamHelp)":
            persona_prompt = build_persona_prompt(persona, language=st.session_state.get("selected_language", "English"))
        elif st.session_state.get("selected_language", "English") != "English":
            # If default persona but language changed
            persona_prompt = f"\n\nCRITICAL RULE: You MUST answer strictly in {st.session_state.selected_language}. All explanations, headers, and bullet points must be translated to {st.session_state.selected_language}."
            
        persona_prompt = QueryEngine.get_structured_system_prompt(persona_prompt)

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
                    persona_prompt=persona_prompt
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

    # --- BULLETPROOF IMAGE ENGINE (ZERO-FAILURE PIPELINE) ---
    if "VISUAL_MANIFEST:" in full_response:
        from ai.image_engine import process_visual_request
        images, caption, cleaned_text = process_visual_request(full_response)
        
        # 1. Update text to the clean version
        full_response = cleaned_text
        
        # 2. Render visuals immediately (Zero-placeholder)
        if images:
            st.divider()
            cols = st.columns(len(images))
            for i, img in enumerate(images):
                with cols[i]:
                    st.image(img, use_container_width=True)
            if caption:
                st.caption(f"🖼️ {caption}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    if st.session_state.get("voice_mode") and full_response:
        AppController.speak(full_response)