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
        "model_choice": "llama-4-scout-17b-16e-instruct",
        "study_goals": [],
        "exam_date": datetime.date.today() + datetime.timedelta(days=30),
        "last_context_hash": None,
        "last_context_summary": "",
        "card_mastery": {},
        "key_health_expanded": False,
        # ── Code Debugger ──────────────────────────────────────────
        "debug_language": "Python",
        "debug_mode": "Full Debug",
        "debug_code_input": "",
        "debug_error_input": "",
        "debug_expected_input": "",
        "debug_result": None,
        "debug_history": [],
        # ── Learn Coding ───────────────────────────────────────────
        "learn_language": "Python",
        "learn_level": "Beginner",
        "learn_topic": "",
        "learn_question": "",
        "learn_result": None,
        "learn_history": [],
        "learn_chat_messages": [],
        # ── Essay Writer
        "essay_result": None, "essay_outline": None, "essay_history": [],
        # ── Interview Coach
        "interview_questions": None, "interview_messages": [], "interview_role": "",
        "interview_type": "Behavioural (STAR Method)", "interview_feedback": None,
        # ── Research Assistant
        "research_result": None, "research_history": [],
        # ── Language Tools
        "lang_result": None, "lang_history": [],
        # ── Math & Science Solver
        "solver_result": None, "solver_history": [],
        # ── Smart Notes
        "notes_result": None, "notes_history": [],
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
            "bg": "#080810", "bg_glass": "rgba(8,8,16,0.7)",
            "bg2": "#0e0e1a", "bg2_glass": "rgba(14,14,26,0.8)",
            "bg3": "#13131f", "bg3_glass": "rgba(19,19,31,0.75)",
            "bg4": "#1a1a2e", "bg4_glass": "rgba(26,26,46,0.6)",
            "border": "#1e1e30", "bd_glass": "rgba(80,80,140,0.18)", "border2": "#2a2a45",
            "text": "#f0f0ff", "text2": "#9090b8", "text3": "#44445a",
            "accent": "#7c6af7", "accent2": "#a78bfa",
            "accent_bg": "rgba(124,106,247,0.1)", "accent_bd": "rgba(124,106,247,0.3)",
            "accent_glow": "rgba(124,106,247,0.25)",
            "green": "#34d399", "green_bg": "rgba(52,211,153,0.1)",
            "red": "#f87171", "blue": "#60a5fa",
            "user_bg": "rgba(124,106,247,0.08)", "user_bd": "rgba(124,106,247,0.2)",
            "ai_bg": "rgba(14,14,26,0.9)", "ai_bd": "rgba(80,80,140,0.2)",
            "card_shadow": "rgba(0,0,0,0.5)",
            "mesh1": "#7c6af720", "mesh2": "#a78bfa15", "mesh3": "#60a5fa10",
        }
    else:
        c = {
            "bg": "#f8f8ff", "bg_glass": "rgba(248,248,255,0.8)",
            "bg2": "#f0f0fa", "bg2_glass": "rgba(240,240,250,0.85)",
            "bg3": "#e8e8f5", "bg3_glass": "rgba(232,232,245,0.8)",
            "bg4": "#dcdcf0", "bg4_glass": "rgba(220,220,240,0.7)",
            "border": "#d0d0e8", "bd_glass": "rgba(100,100,180,0.15)", "border2": "#a0a0c8",
            "text": "#1a1a2e", "text2": "#4a4a6a", "text3": "#8888aa",
            "accent": "#6655e8", "accent2": "#8b5cf6",
            "accent_bg": "rgba(102,85,232,0.08)", "accent_bd": "rgba(102,85,232,0.25)",
            "accent_glow": "rgba(102,85,232,0.15)",
            "green": "#059669", "green_bg": "rgba(5,150,105,0.08)",
            "red": "#dc2626", "blue": "#2563eb",
            "user_bg": "rgba(102,85,232,0.06)", "user_bd": "rgba(102,85,232,0.18)",
            "ai_bg": "rgba(240,240,250,0.95)", "ai_bd": "rgba(100,100,180,0.15)",
            "card_shadow": "rgba(0,0,0,0.08)",
            "mesh1": "#6655e818", "mesh2": "#8b5cf612", "mesh3": "#2563eb0e",
        }
    return f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Fira+Code:wght@400;500&display=swap');

  :root {{
    --bg:{c['bg']}; --bg-glass:{c['bg_glass']}; --bg2:{c['bg2']}; --bg2-glass:{c['bg2_glass']};
    --bg3:{c['bg3']}; --bg3-glass:{c['bg3_glass']}; --bg4:{c['bg4']}; --bg4-glass:{c['bg4_glass']};
    --border:{c['border']}; --bd-glass:{c['bd_glass']}; --border2:{c['border2']};
    --text:{c['text']}; --text2:{c['text2']}; --text3:{c['text3']};
    --accent:{c['accent']}; --accent2:{c['accent2']};
    --accent-bg:{c['accent_bg']}; --accent-bd:{c['accent_bd']}; --accent-glow:{c['accent_glow']};
    --green:{c['green']}; --green-bg:{c['green_bg']};
    --red:{c['red']}; --blue:{c['blue']};
    --user-bg:{c['user_bg']}; --user-bd:{c['user_bd']};
    --ai-bg:{c['ai_bg']}; --ai-bd:{c['ai_bd']};
    --card-shadow:{c['card_shadow']};
    --mesh1:{c['mesh1']}; --mesh2:{c['mesh2']}; --mesh3:{c['mesh3']};
    --sans:'Outfit',system-ui,-apple-system,sans-serif;
    --mono:'Fira Code',monospace;
    --radius:16px;
    --radius-sm:10px;
    --radius-lg:24px;
    --trans:all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    --trans-slow:all 0.45s cubic-bezier(0.16, 1, 0.3, 1);
  }}

  /* ── GLOBAL RESET & BASE ── */
  html, body, [data-testid="stAppViewContainer"] {{
    background-color:var(--bg) !important;
    font-family:var(--sans) !important;
    color:var(--text) !important;
    font-feature-settings:'liga' 1,'kern' 1;
    -webkit-font-smoothing:antialiased;
    -moz-osx-font-smoothing:grayscale;
  }}

  /* Animated mesh gradient background */
  [data-testid="stAppViewContainer"]::before {{
    content:'';
    position:fixed; inset:0; z-index:0; pointer-events:none;
    background:
      radial-gradient(ellipse 80% 50% at 20% 20%, var(--mesh1), transparent),
      radial-gradient(ellipse 60% 40% at 80% 80%, var(--mesh2), transparent),
      radial-gradient(ellipse 50% 60% at 50% 50%, var(--mesh3), transparent);
    animation:meshDrift 18s ease-in-out infinite alternate;
  }}
  @keyframes meshDrift {{
    0%   {{ transform:translate(0,0) scale(1); }}
    33%  {{ transform:translate(-1%,1%) scale(1.02); }}
    66%  {{ transform:translate(1%,-1%) scale(0.99); }}
    100% {{ transform:translate(-0.5%,0.5%) scale(1.01); }}
  }}

  [data-testid="stAppViewContainer"] > * {{ position:relative; z-index:1; }}

  #MainMenu, footer, [data-testid="stDeployButton"] {{ visibility:hidden; display:none; }}

  /* ── SCROLLBAR ── */
  ::-webkit-scrollbar {{ width:5px; height:5px; }}
  ::-webkit-scrollbar-track {{ background:transparent; }}
  ::-webkit-scrollbar-thumb {{ background:var(--border2); border-radius:99px; }}
  ::-webkit-scrollbar-thumb:hover {{ background:var(--accent); }}

  /* ── SIDEBAR ── */
  [data-testid="stSidebar"] {{
    background:var(--bg2-glass) !important;
    backdrop-filter:blur(32px) saturate(180%) !important;
    -webkit-backdrop-filter:blur(32px) saturate(180%) !important;
    border-right:1px solid var(--bd-glass) !important;
    padding-top:0 !important;
    box-shadow:4px 0 24px rgba(0,0,0,0.12) !important;
  }}
  [data-testid="stSidebar"] * {{ font-family:var(--sans) !important; }}
  [data-testid="stSidebarContent"] {{ padding-top:0 !important; }}

  /* ── MAIN CONTENT ── */
  .main .block-container {{
    padding-top:0 !important;
    padding-bottom:7rem !important;
    max-width:900px !important;
    margin:0 auto !important;
    padding-left:1.5rem !important;
    padding-right:1.5rem !important;
  }}

  /* ── PAGE LOAD ANIMATION ── */
  @keyframes pageIn {{
    from {{ opacity:0; transform:translateY(10px); }}
    to   {{ opacity:1; transform:none; }}
  }}
  .main .block-container > * {{
    animation:pageIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .main .block-container > *:nth-child(1) {{ animation-delay:0.05s; }}
  .main .block-container > *:nth-child(2) {{ animation-delay:0.10s; }}
  .main .block-container > *:nth-child(3) {{ animation-delay:0.15s; }}
  .main .block-container > *:nth-child(4) {{ animation-delay:0.18s; }}
  .main .block-container > *:nth-child(5) {{ animation-delay:0.20s; }}

  /* ── CHAT MESSAGES ── */
  @keyframes msgSlideIn {{
    from {{ opacity:0; transform:translateY(16px) scale(0.98); }}
    to   {{ opacity:1; transform:none; }}
  }}

  [data-testid="stChatMessage"] {{
    animation:msgSlideIn 0.4s cubic-bezier(0.16,1,0.3,1) forwards !important;
    border-radius:var(--radius) !important;
    padding:1rem 1.25rem !important;
    margin-bottom:0.9rem !important;
    border:1px solid var(--ai-bd) !important;
    background:var(--ai-bg) !important;
    backdrop-filter:blur(16px) !important;
    -webkit-backdrop-filter:blur(16px) !important;
    box-shadow:0 2px 16px var(--card-shadow), 0 0 0 1px var(--bd-glass) !important;
    transition:var(--trans) !important;
    position:relative !important;
    overflow:hidden !important;
  }}

  [data-testid="stChatMessage"]:hover {{
    border-color:var(--accent-bd) !important;
    box-shadow:0 4px 24px var(--card-shadow), 0 0 0 1px var(--accent-bd) !important;
    transform:translateY(-1px) !important;
  }}

  /* AI message — left-aligned with accent left border */
  [data-testid="stChatMessage"]:not(:has(.user-msg-hook)) {{
    margin-right:10% !important;
    border-left:3px solid var(--accent) !important;
    border-top-left-radius:4px !important;
  }}

  /* User message — right-aligned, accent tint */
  [data-testid="stChatMessage"]:has(.user-msg-hook) {{
    background:var(--user-bg) !important;
    border:1px solid var(--user-bd) !important;
    margin-left:15% !important;
    border-top-right-radius:4px !important;
    border-right:3px solid var(--accent2) !important;
  }}

  /* Subtle shimmer on last AI message */
  [data-testid="stChatMessage"]:not(:has(.user-msg-hook)):last-of-type::after {{
    content:'';
    position:absolute; top:0; left:-100%; width:60%; height:100%;
    background:linear-gradient(90deg, transparent, rgba(124,106,247,0.04), transparent);
    animation:shimmer 3s ease-in-out infinite;
  }}
  @keyframes shimmer {{
    0%   {{ left:-100%; }}
    50%  {{ left:150%; }}
    100% {{ left:150%; }}
  }}

  /* Avatar styling */
  [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"],
  [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {{
    border-radius:50% !important;
    width:36px !important;
    height:36px !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    font-size:1rem !important;
    flex-shrink:0 !important;
  }}
  [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {{
    background:linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    box-shadow:0 2px 12px var(--accent-glow) !important;
  }}
  [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {{
    background:var(--bg4) !important;
    border:1px solid var(--bd-glass) !important;
  }}

  /* ── CHAT INPUT ── */
  [data-testid="stChatInputContainer"] {{
    position:sticky !important;
    bottom:0 !important;
    background:linear-gradient(to top, var(--bg) 55%, transparent) !important;
    padding:0.75rem 0 1.5rem !important;
    border-top:none !important;
  }}

  [data-testid="stChatInputContainer"] > div {{
    background:var(--bg3-glass) !important;
    backdrop-filter:blur(24px) saturate(160%) !important;
    -webkit-backdrop-filter:blur(24px) saturate(160%) !important;
    border:1.5px solid var(--bd-glass) !important;
    border-radius:var(--radius-lg) !important;
    box-shadow:0 4px 32px var(--card-shadow), 0 0 0 1px var(--bd-glass) !important;
    transition:var(--trans) !important;
    overflow:hidden !important;
  }}

  [data-testid="stChatInputContainer"] > div:focus-within {{
    border-color:var(--accent-bd) !important;
    box-shadow:0 4px 32px var(--card-shadow), 0 0 0 3px var(--accent-glow) !important;
  }}

  [data-testid="stChatInputContainer"] textarea {{
    background:transparent !important;
    border:none !important;
    outline:none !important;
    color:var(--text) !important;
    font-family:var(--sans) !important;
    font-size:0.95rem !important;
    font-weight:400 !important;
    padding:14px 18px !important;
    resize:none !important;
    box-shadow:none !important;
  }}

  [data-testid="stChatInputContainer"] textarea::placeholder {{
    color:var(--text3) !important;
    font-weight:400 !important;
  }}

  [data-testid="stChatInputContainer"] button {{
    background:linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    border:none !important;
    border-radius:12px !important;
    margin:6px !important;
    color:white !important;
    transition:var(--trans) !important;
    box-shadow:0 2px 12px var(--accent-glow) !important;
  }}
  [data-testid="stChatInputContainer"] button:hover {{
    transform:scale(1.06) !important;
    box-shadow:0 4px 20px var(--accent-glow) !important;
  }}

  /* ── BUTTONS ── */
  .stButton > button {{
    font-family:var(--sans) !important;
    font-size:0.85rem !important;
    font-weight:500 !important;
    border-radius:var(--radius-sm) !important;
    border:1px solid var(--bd-glass) !important;
    background:var(--bg3-glass) !important;
    backdrop-filter:blur(12px) !important;
    color:var(--text) !important;
    padding:0.45rem 1rem !important;
    transition:var(--trans) !important;
    position:relative !important;
    overflow:hidden !important;
    letter-spacing:0.01em !important;
  }}
  .stButton > button::before {{
    content:''; position:absolute; inset:0;
    background:linear-gradient(135deg, var(--accent), var(--accent2));
    opacity:0; transition:opacity 0.25s ease;
    border-radius:inherit;
  }}
  .stButton > button:hover {{
    border-color:var(--accent-bd) !important;
    color:var(--accent) !important;
    transform:translateY(-2px) !important;
    box-shadow:0 4px 20px var(--accent-glow) !important;
  }}
  .stButton > button:active {{
    transform:translateY(0) scale(0.97) !important;
  }}

  /* Primary buttons */
  .stButton > button[kind="primary"] {{
    background:linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color:white !important;
    border-color:transparent !important;
    box-shadow:0 2px 12px var(--accent-glow) !important;
  }}
  .stButton > button[kind="primary"]:hover {{
    color:white !important;
    transform:translateY(-2px) !important;
    box-shadow:0 6px 24px var(--accent-glow) !important;
  }}

  /* ── SELECTBOX ── */
  [data-testid="stSelectbox"] > div > div,
  [data-testid="stSelectbox"] > label + div > div {{
    background:var(--bg3-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    color:var(--text) !important;
    backdrop-filter:blur(12px) !important;
    transition:var(--trans) !important;
    font-family:var(--sans) !important;
  }}
  [data-testid="stSelectbox"] > div > div:hover {{
    border-color:var(--accent-bd) !important;
  }}
  [data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p {{
    font-size:0.85rem !important;
    color:var(--text) !important;
  }}

  /* ── TEXT INPUT ── */
  [data-testid="stTextInput"] input,
  [data-testid="stNumberInput"] input {{
    background:var(--bg3-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    color:var(--text) !important;
    font-family:var(--sans) !important;
    font-size:0.88rem !important;
    padding:0.5rem 0.85rem !important;
    transition:var(--trans) !important;
    backdrop-filter:blur(12px) !important;
  }}
  [data-testid="stTextInput"] input:focus,
  [data-testid="stNumberInput"] input:focus {{
    border-color:var(--accent-bd) !important;
    box-shadow:0 0 0 3px var(--accent-glow) !important;
    outline:none !important;
  }}

  /* ── FILE UPLOADER ── */
  [data-testid="stFileUploader"] {{
    background:var(--bg3-glass) !important;
    border:2px dashed var(--bd-glass) !important;
    border-radius:var(--radius) !important;
    backdrop-filter:blur(12px) !important;
    transition:var(--trans) !important;
    padding:0.5rem !important;
  }}
  [data-testid="stFileUploader"]:hover {{
    border-color:var(--accent-bd) !important;
    background:var(--accent-bg) !important;
    box-shadow:0 0 0 3px var(--accent-glow) !important;
  }}

  /* ── EXPANDER ── */
  [data-testid="stExpander"] {{
    background:var(--bg2-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius) !important;
    backdrop-filter:blur(16px) !important;
    overflow:hidden !important;
    transition:var(--trans) !important;
  }}
  [data-testid="stExpander"]:hover {{
    border-color:var(--accent-bd) !important;
  }}
  [data-testid="stExpander"] summary {{
    font-weight:500 !important;
    color:var(--text) !important;
    font-size:0.88rem !important;
    padding:0.6rem 0.9rem !important;
  }}

  /* ── SPINNER / LOADING ── */
  @keyframes spinnerPulse {{
    0%, 100% {{ opacity:1; transform:scale(1); }}
    50%       {{ opacity:0.6; transform:scale(0.95); }}
  }}
  @keyframes dotBounce {{
    0%, 80%, 100% {{ transform:translateY(0); }}
    40%           {{ transform:translateY(-8px); }}
  }}
  .stSpinner {{
    display:flex !important;
    align-items:center !important;
    gap:8px !important;
  }}
  .stSpinner > div {{
    background:var(--accent) !important;
    border-radius:50% !important;
    width:8px !important; height:8px !important;
    animation:dotBounce 1.2s ease-in-out infinite !important;
  }}
  [data-testid="stStatusWidget"] {{
    background:var(--bg3-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    backdrop-filter:blur(12px) !important;
    padding:0.5rem 0.75rem !important;
  }}

  /* Thinking dots for AI responses */
  @keyframes thinkDot {{
    0%, 80%, 100% {{ opacity:0.2; transform:scale(0.8); }}
    40%           {{ opacity:1; transform:scale(1.2); }}
  }}
  .thinking-dots span {{
    display:inline-block;
    width:6px; height:6px;
    background:var(--accent);
    border-radius:50%;
    margin:0 2px;
    animation:thinkDot 1.4s ease-in-out infinite;
  }}
  .thinking-dots span:nth-child(2) {{ animation-delay:0.2s; }}
  .thinking-dots span:nth-child(3) {{ animation-delay:0.4s; }}

  /* ── TABS ── */
  [data-testid="stTabs"] [data-testid="stTabBar"] {{
    background:var(--bg3-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    padding:3px !important;
    gap:2px !important;
    backdrop-filter:blur(12px) !important;
  }}
  [data-testid="stTabs"] [role="tab"] {{
    border-radius:8px !important;
    color:var(--text3) !important;
    font-size:0.82rem !important;
    font-weight:500 !important;
    padding:0.35rem 0.75rem !important;
    transition:var(--trans) !important;
    border:none !important;
  }}
  [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background:var(--accent) !important;
    color:white !important;
    box-shadow:0 2px 8px var(--accent-glow) !important;
  }}
  [data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {{
    background:var(--bg4-glass) !important;
    color:var(--text2) !important;
  }}

  /* ── SLIDER ── */
  [data-testid="stSlider"] [role="slider"] {{
    background:linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    border:none !important;
    box-shadow:0 0 0 3px var(--accent-glow) !important;
    width:20px !important; height:20px !important;
    transition:var(--trans) !important;
  }}
  [data-testid="stSlider"] [data-testid="stSliderTrack"] > div:first-child {{
    background:var(--accent) !important;
  }}

  /* ── TOGGLE ── */
  [data-testid="stToggle"] > label > div[role="switch"][aria-checked="true"] {{
    background:linear-gradient(90deg, var(--accent), var(--accent2)) !important;
    box-shadow:0 0 12px var(--accent-glow) !important;
  }}

  /* ── CHECKBOX ── */
  [data-testid="stCheckbox"] input[type="checkbox"]:checked + span {{
    background:var(--accent) !important;
    border-color:var(--accent) !important;
  }}

  /* ── ALERTS / STATUS ── */
  [data-testid="stAlert"] {{
    border-radius:var(--radius-sm) !important;
    border:1px solid var(--bd-glass) !important;
    backdrop-filter:blur(12px) !important;
    font-size:0.85rem !important;
    padding:0.65rem 0.9rem !important;
  }}
  .stSuccess {{
    background:var(--green-bg) !important;
    border-color:var(--green) !important;
    color:var(--green) !important;
  }}
  .stError {{
    background:rgba(248,113,113,0.08) !important;
    border-color:var(--red) !important;
    color:var(--red) !important;
  }}
  .stWarning {{
    background:rgba(251,191,36,0.08) !important;
    border-color:#fbbf24 !important;
  }}
  .stInfo {{
    background:var(--accent-bg) !important;
    border-color:var(--accent-bd) !important;
  }}

  /* ── TOAST ── */
  [data-testid="stToast"] {{
    background:var(--bg2-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    backdrop-filter:blur(24px) !important;
    box-shadow:0 8px 32px var(--card-shadow) !important;
    animation:toastIn 0.4s cubic-bezier(0.16,1,0.3,1) !important;
  }}
  @keyframes toastIn {{
    from {{ opacity:0; transform:translateX(20px) scale(0.96); }}
    to   {{ opacity:1; transform:none; }}
  }}

  /* ── DIVIDER ── */
  hr {{
    border:none !important;
    height:1px !important;
    background:linear-gradient(90deg, transparent, var(--border), transparent) !important;
    margin:0.6rem 0 !important;
  }}

  /* ── CODE ── */
  code {{
    background:var(--bg4-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:6px !important;
    font-family:var(--mono) !important;
    font-size:0.8em !important;
    padding:2px 7px !important;
    color:var(--accent2) !important;
    letter-spacing:-0.01em !important;
  }}
  pre {{
    background:var(--bg4-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius) !important;
    padding:1rem 1.2rem !important;
    overflow-x:auto !important;
    backdrop-filter:blur(12px) !important;
  }}
  pre code {{
    background:transparent !important;
    border:none !important;
    padding:0 !important;
    font-size:0.85em !important;
  }}

  /* ── MARKDOWN CONTENT ── */
  [data-testid="stMarkdownContainer"] {{
    font-size:0.93rem !important;
    line-height:1.75 !important;
    color:var(--text) !important;
  }}
  [data-testid="stMarkdownContainer"] h1,
  [data-testid="stMarkdownContainer"] h2,
  [data-testid="stMarkdownContainer"] h3 {{
    color:var(--text) !important;
    font-weight:700 !important;
    letter-spacing:-0.02em !important;
  }}
  [data-testid="stMarkdownContainer"] a {{
    color:var(--accent2) !important;
    text-decoration:none !important;
    border-bottom:1px solid var(--accent-bd) !important;
    transition:var(--trans) !important;
  }}
  [data-testid="stMarkdownContainer"] a:hover {{
    color:var(--accent) !important;
    border-color:var(--accent) !important;
  }}
  [data-testid="stMarkdownContainer"] blockquote {{
    border-left:3px solid var(--accent) !important;
    margin:0 !important;
    padding:0.5rem 1rem !important;
    background:var(--accent-bg) !important;
    border-radius:0 var(--radius-sm) var(--radius-sm) 0 !important;
  }}
  [data-testid="stMarkdownContainer"] table {{
    border-collapse:collapse !important;
    width:100% !important;
    border-radius:var(--radius-sm) !important;
    overflow:hidden !important;
  }}
  [data-testid="stMarkdownContainer"] th {{
    background:var(--bg4-glass) !important;
    padding:0.5rem 0.75rem !important;
    font-size:0.82rem !important;
    font-weight:600 !important;
    text-align:left !important;
    color:var(--text2) !important;
    text-transform:uppercase !important;
    letter-spacing:0.05em !important;
  }}
  [data-testid="stMarkdownContainer"] td {{
    padding:0.5rem 0.75rem !important;
    border-top:1px solid var(--border) !important;
    font-size:0.88rem !important;
  }}
  [data-testid="stMarkdownContainer"] tr:hover td {{
    background:var(--accent-bg) !important;
  }}

  /* ── LOGO ── */
  .eh-logo {{
    display:flex; align-items:center; gap:12px;
    padding:1.25rem 1rem 0.9rem;
    border-bottom:1px solid var(--border);
    margin-bottom:0.75rem;
  }}
  .eh-logo-icon {{
    width:38px; height:38px;
    background:linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius:12px;
    display:flex; align-items:center; justify-content:center;
    box-shadow:0 4px 16px var(--accent-glow);
    animation:logoPulse 4s ease-in-out infinite;
    flex-shrink:0;
  }}
  @keyframes logoPulse {{
    0%, 100% {{ box-shadow:0 4px 16px var(--accent-glow); }}
    50%       {{ box-shadow:0 4px 28px var(--accent-glow), 0 0 0 4px var(--accent-bg); }}
  }}
  .eh-logo-title {{ font-size:1.05rem; font-weight:800; color:var(--text); letter-spacing:-0.4px; }}
  .eh-logo-sub {{ font-size:0.68rem; color:var(--text3); margin-top:1px; letter-spacing:0.02em; }}

  /* ── SECTION LABELS ── */
  .section-label {{
    font-size:0.67rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
    color:var(--text3); margin:1rem 0 0.4rem;
    display:flex; align-items:center; gap:7px;
  }}
  .section-label::after {{
    content:''; flex:1; height:1px;
    background:linear-gradient(to right, var(--border), transparent);
  }}

  /* ── STAT CARDS ── */
  .stat-row {{ display:flex; gap:6px; margin:0.4rem 0; }}
  .stat-box {{
    flex:1;
    background:var(--bg3-glass);
    border:1px solid var(--bd-glass);
    border-radius:var(--radius-sm);
    padding:0.6rem 0.4rem;
    text-align:center;
    backdrop-filter:blur(10px);
    transition:var(--trans);
  }}
  .stat-box:hover {{
    border-color:var(--accent-bd);
    transform:translateY(-2px);
    box-shadow:0 4px 16px var(--accent-glow);
  }}
  .stat-val {{ font-size:1.05rem; font-weight:800; color:var(--accent); line-height:1; }}
  .stat-lbl {{ font-size:0.62rem; color:var(--text3); text-transform:uppercase; letter-spacing:0.07em; margin-top:3px; }}

  /* ── SOURCE CHIPS ── */
  .source-chip {{
    display:inline-flex; align-items:center; gap:6px;
    background:var(--bg3-glass);
    border:1px solid var(--bd-glass);
    border-radius:99px; padding:3px 11px;
    font-size:0.76rem; color:var(--text2);
    margin:2px 3px;
    transition:var(--trans);
    backdrop-filter:blur(8px);
  }}
  .source-chip:hover {{ border-color:var(--accent-bd); color:var(--accent); }}
  .source-chip .chip-dot {{ width:5px; height:5px; border-radius:50%; background:var(--accent); flex-shrink:0; }}

  /* ── KEY HEALTH BAR ── */
  .key-health-bar {{ height:5px; background:var(--bg4); border-radius:99px; overflow:hidden; margin:4px 0 9px; }}
  .key-health-fill {{ height:100%; border-radius:99px; transition:width 0.6s cubic-bezier(0.16,1,0.3,1); }}

  /* ── HERO SECTION ── */
  @keyframes fadeUp {{
    from {{ opacity:0; transform:translateY(24px); }}
    to   {{ opacity:1; transform:none; }}
  }}
  .hero-wrap {{
    text-align:center;
    padding:3rem 1.5rem 1.5rem;
    animation:fadeUp 0.7s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .hero-badge {{
    display:inline-flex; align-items:center; gap:7px;
    background:var(--accent-bg);
    border:1px solid var(--accent-bd);
    border-radius:99px; padding:4px 16px;
    font-size:0.74rem; color:var(--accent); font-weight:600;
    margin-bottom:1.2rem;
    letter-spacing:0.02em;
    animation:badgePop 0.6s 0.2s cubic-bezier(0.16,1,0.3,1) both;
  }}
  @keyframes badgePop {{
    from {{ opacity:0; transform:scale(0.8); }}
    to   {{ opacity:1; transform:scale(1); }}
  }}
  .hero-badge::before {{
    content:'';
    width:6px; height:6px;
    border-radius:50%;
    background:var(--accent);
    box-shadow:0 0 6px var(--accent);
    animation:badgeDot 2s ease-in-out infinite;
  }}
  @keyframes badgeDot {{
    0%, 100% {{ opacity:1; }}
    50% {{ opacity:0.3; }}
  }}
  .hero-title {{
    font-size:2.5rem; font-weight:900;
    color:var(--text);
    letter-spacing:-1.5px; line-height:1.1;
    margin-bottom:0.65rem;
  }}
  .hero-title em {{
    color:transparent;
    background:linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
    font-style:normal;
  }}
  .hero-sub {{
    font-size:0.93rem; color:var(--text2); line-height:1.65;
    max-width:440px; margin:0 auto 1.6rem;
    font-weight:400;
  }}
  .prompt-pills {{
    display:flex; flex-wrap:wrap; gap:7px;
    justify-content:center; max-width:520px; margin:0 auto;
  }}
  .pill {{
    background:var(--bg3-glass);
    border:1px solid var(--bd-glass);
    border-radius:99px; padding:6px 14px;
    font-size:0.78rem; color:var(--text2);
    cursor:pointer;
    transition:var(--trans);
    backdrop-filter:blur(10px);
  }}
  .pill:hover {{
    border-color:var(--accent-bd);
    color:var(--accent);
    background:var(--accent-bg);
    transform:translateY(-2px);
    box-shadow:0 4px 14px var(--accent-glow);
  }}

  /* ── BANNERS ── */
  .study-banner {{
    display:flex; align-items:center; flex-wrap:wrap; gap:6px;
    background:var(--accent-bg);
    border:1px solid var(--accent-bd);
    border-radius:var(--radius-sm);
    padding:8px 14px; margin-bottom:1rem;
    animation:fadeUp 0.4s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .study-banner-label {{
    font-size:0.72rem; font-weight:700;
    color:var(--accent); text-transform:uppercase; letter-spacing:0.08em; white-space:nowrap;
  }}
  .focus-banner {{
    background:linear-gradient(90deg, var(--accent-bg), transparent);
    border-left:3px solid var(--accent);
    border-radius:0 var(--radius-sm) var(--radius-sm) 0;
    padding:10px 16px; font-size:0.85rem;
    color:var(--accent); margin-bottom:1rem;
    animation:fadeUp 0.4s cubic-bezier(0.16,1,0.3,1) both;
  }}

  /* ── PERSONA CHIP ── */
  .persona-chip {{
    background:var(--accent-bg);
    border:1px solid var(--accent-bd);
    border-radius:99px; padding:4px 13px;
    font-size:0.76rem; color:var(--accent);
    display:inline-block; margin-bottom:0.35rem;
    font-weight:500;
  }}

  /* ── FLASHCARD ── */
  .card-container {{ perspective:1000px; }}
  .flashcard {{
    background:var(--bg3-glass);
    border:1.5px solid var(--bd-glass);
    border-radius:var(--radius-lg);
    padding:2.5rem 2rem;
    min-height:190px;
    display:flex; align-items:center; justify-content:center;
    text-align:center;
    font-size:1.1rem; font-weight:500; line-height:1.6;
    box-shadow:0 12px 40px var(--card-shadow), 0 0 0 1px var(--bd-glass);
    backdrop-filter:blur(20px);
    transition:var(--trans-slow);
    animation:cardIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
  }}
  @keyframes cardIn {{
    from {{ opacity:0; transform:rotateY(-8deg) scale(0.95); }}
    to   {{ opacity:1; transform:none; }}
  }}
  .flashcard:hover {{ transform:translateY(-3px); box-shadow:0 20px 56px var(--card-shadow), 0 0 0 1px var(--accent-bd); }}

  /* ── PROGRESS BARS ── */
  .prog-wrap {{ margin-bottom:0.75rem; }}
  .prog-label {{
    display:flex; justify-content:space-between;
    font-size:0.7rem; color:var(--text3); margin-bottom:4px;
  }}
  .prog-bar {{ height:4px; background:var(--bg4); border-radius:99px; overflow:hidden; }}
  .prog-fill {{
    height:100%; border-radius:99px;
    background:linear-gradient(90deg, var(--accent), var(--accent2));
    transition:width 0.6s cubic-bezier(0.16,1,0.3,1);
  }}

  /* ── BADGES ── */
  .badge-green {{ background:rgba(52,211,153,0.15); color:var(--green); border-radius:6px; padding:2px 8px; font-size:0.7rem; font-weight:600; }}
  .badge-red {{ background:rgba(248,113,113,0.12); color:var(--red); border-radius:6px; padding:2px 8px; font-size:0.7rem; font-weight:600; }}
  .badge-yellow {{ background:rgba(251,191,36,0.12); color:#fbbf24; border-radius:6px; padding:2px 8px; font-size:0.7rem; font-weight:600; }}

  /* ── API KEY ROW ── */
  .key-row {{
    display:flex; align-items:center; justify-content:space-between;
    padding:6px 0; border-bottom:1px solid var(--border); font-size:0.78rem;
    transition:var(--trans);
  }}
  .key-row:last-child {{ border-bottom:none; }}
  .key-row:hover {{ background:var(--accent-bg); border-radius:6px; padding:6px 6px; }}

  /* ── POWERED BY ── */
  .poweredby {{
    font-size:0.63rem; color:var(--text3); text-align:center;
    padding:0.5rem; margin-top:0.5rem;
    letter-spacing:0.05em;
  }}
  .poweredby span {{ color:var(--accent); font-weight:600; }}

  /* ── PAGE HEADER ── */
  .page-header {{
    padding:1.25rem 0 0.6rem;
    border-bottom:1px solid var(--border);
    margin-bottom:1rem;
    display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;
  }}
  .page-header-title {{
    font-size:1.5rem; font-weight:900;
    color:var(--text); letter-spacing:-0.5px;
    background:linear-gradient(135deg, var(--text), var(--accent2));
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
  }}
  .page-header-sub {{ font-size:0.78rem; color:var(--text3); font-weight:400; }}

  /* ── DOWNLOAD BUTTONS ── */
  .stDownloadButton > button {{
    font-family:var(--sans) !important;
    background:var(--bg3-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    color:var(--text2) !important;
    font-size:0.82rem !important;
    font-weight:500 !important;
    transition:var(--trans) !important;
  }}
  .stDownloadButton > button:hover {{
    border-color:var(--accent-bd) !important;
    color:var(--accent) !important;
    background:var(--accent-bg) !important;
    transform:translateY(-1px) !important;
  }}

  /* ── RADIO BUTTONS ── */
  [data-testid="stRadio"] label {{
    background:var(--bg3-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    padding:0.4rem 0.9rem !important;
    margin:2px !important;
    font-size:0.85rem !important;
    transition:var(--trans) !important;
    cursor:pointer !important;
  }}
  [data-testid="stRadio"] label:hover {{
    border-color:var(--accent-bd) !important;
    background:var(--accent-bg) !important;
  }}

  /* ── SUBHEADER TITLES ── */
  h1, h2, h3 {{
    font-family:var(--sans) !important;
    font-weight:800 !important;
    letter-spacing:-0.03em !important;
    color:var(--text) !important;
  }}

  /* ── NUMBER INPUT ── */
  [data-testid="stNumberInput"] button {{
    background:var(--bg4) !important;
    border:1px solid var(--bd-glass) !important;
    color:var(--text2) !important;
    border-radius:6px !important;
    transition:var(--trans) !important;
  }}
  [data-testid="stNumberInput"] button:hover {{
    background:var(--accent-bg) !important;
    color:var(--accent) !important;
    border-color:var(--accent-bd) !important;
  }}

  /* ── DATE INPUT ── */
  [data-testid="stDateInput"] input {{
    background:var(--bg3-glass) !important;
    border:1px solid var(--bd-glass) !important;
    border-radius:var(--radius-sm) !important;
    color:var(--text) !important;
    font-family:var(--sans) !important;
    font-size:0.85rem !important;
    transition:var(--trans) !important;
  }}
  [data-testid="stDateInput"] input:focus {{
    border-color:var(--accent-bd) !important;
    box-shadow:0 0 0 3px var(--accent-glow) !important;
  }}

  /* ── SELECT SLIDER ── */
  [data-testid="stSlider"] {{
    padding:0.25rem 0 !important;
  }}

  /* ── SPINNER OVERLAY ── */
  [data-testid="stSpinner"] > div {{
    border-color:var(--accent) transparent var(--accent) transparent !important;
  }}

  /* ── STALE CONTENT FADE ── */
  @keyframes contentFadeIn {{
    from {{ opacity:0.4; }}
    to   {{ opacity:1; }}
  }}
  [data-testid="stMainBlockContainer"] .stMarkdown {{
    animation:contentFadeIn 0.3s ease-out;
  }}
</style>
"""

st.markdown(get_theme_css(), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _safe_js_text(text: str) -> str:
    """Escape text for safe embedding inside a JS string literal."""
    text = re.sub(r'[*#\_`~]', '', text)
    text = re.sub(r'\[.+?\]\(.+?\)', '', text)
    text = re.sub('<[^<]+?>', '', text)
    text = text.replace('\\', '\\\\').replace('"', '').replace("'", '')
    text = text.replace('\n', ' ').replace('\r', ' ')
    return text.strip()


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
        _langs = [
            "English", "Hindi", "Bengali", "Telugu", "Marathi", "Tamil", "Urdu", "Gujarati", "Kannada", "Malayalam", "Punjabi", 
            "Spanish", "French", "German", "Mandarin", "Japanese", "Arabic", "Portuguese", "Russian", "Korean", "Italian", "Turkish",
            "Vietnamese", "Polish", "Ukrainian", "Dutch", "Thai", "Swedish", "Indonesian", "Greek", "Czech", "Romanian", "Hungarian",
            "Hebrew", "Danish", "Finnish", "Norwegian", "Slovak", "Bulgarian", "Croatian", "Serbian", "Lithuanian", "Slovenian",
            "Latvian", "Estonian", "Icelandic", "Swahili", "Amharic", "Yoruba", "Igbo", "Zulu", "Afrikaans", "Hausa", "Oromo",
            "Tagalog", "Malay", "Javanese", "Sundanese", "Kurdish", "Nepali", "Sinhala", "Khmer", "Burmese", "Lao", "Tibetan",
            "Sanskrit", "Pali", "Assamese", "Odia", "Maithili", "Bhojpuri", "Kashmiri", "Sindhi", "Pashto", "Balochi", "Farsi",
            "Latin", "Esperanto"
        ]
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
            "Model", options=["Fast (8B)", "Balanced (Scout 17B)"],
            value="Balanced (Scout 17B)", label_visibility="collapsed",
        )
        st.session_state.model_choice = (
            "llama-3.1-8b-instant" if "Fast" in model_choice
            else "llama-4-scout-17b-16e-instruct"
        )

        # ── Voice mode ─────────────────────────────
        st.markdown('<div class="section-label">🎙️ Voice Mode</div>', unsafe_allow_html=True)
        v_mode = st.toggle("Enable TTS responses", value=st.session_state.get("voice_mode", False))
        if v_mode != st.session_state.voice_mode:
            st.session_state.voice_mode = v_mode

        st.divider()

    # ── Toolbar icons ──────────────────────────────
    tb_cols = st.columns(8)
    _tb_items = [
        ("📅", "tb_cal", "Calendar",    "calendar_open"),
        ("🧮", "tb_calc", "Calculator", None),
        ("📈", "tb_graph", "Graphs",    None),
        ("📝", "tb_editor", "AI Editor", None),
        ("✍️", "tb_story", "Story Builder", None),
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
                elif k == "tb_editor":
                    st.session_state.app_mode = "editor"; st.rerun()
                elif k == "tb_story":
                    st.session_state.app_mode = "story"; st.rerun()
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
                if r != "Error": st.session_state.calc_expr = str(r) # auto-ans
            else:
                st.session_state.calc_expr += str(v)

        # Massive Professional 200+ Button Calculator Engine
        calc_mode = st.selectbox("🧮 Calculator Engine Base", [
            "Standard", "Advanced Scientific", "Calculus & Algebra", 
            "Hyperbolic & Inverse", "Physics & Astro Constants", 
            "Matrix & Vector Algebra", "Statistics & Probability", 
            "Programmer & Logic", "Quantum & Chem Constants"
        ])

        calc_menus = {
            "Standard": [
                ["7", "8", "9", "÷"],
                ["4", "5", "6", "×"],
                ["1", "2", "3", "−"],
                ["C", "0", ".", "+"],
                ["(", ")", "⌫", "="]
            ],
            "Advanced Scientific": [
                ["sin(", "cos(", "tan(", "log("],
                ["sec(", "csc(", "cot(", "ln("],
                ["√(",   "x²",   "x³",   "^"],
                ["e",    "π",    "!",    "|x|"],
                ["mod",  "1/x",  "⌫",   "="]
            ],
            "Calculus & Algebra": [
                ["diff(", "integrate(", "limit(", "Sum("],
                ["Product(", "solve(", "factor(", "expand("],
                ["simplify(", "roots(", "x", "y"],
                ["z", "t", ",", "oo"],
                ["C", "(", "⌫", "="]
            ],
            "Hyperbolic & Inverse": [
                ["sinh(", "cosh(", "tanh(", "asinh("],
                ["acosh(","atanh(","sech(", "csch("],
                ["coth(", "asech(","acsch(","acoth("],
                ["asin(", "acos(", "atan(", "deg2rad("],
                ["rad2deg(","C", "⌫", "="]
            ],
            "Physics & Astro Constants": [
                ["c_LIGHT", "G_GRAV", "h_PLANCK", "hbar"],
                ["m_e", "m_p", "m_n", "e_CHARGE"],
                ["mu_0", "eps_0", "Z_0", "k_BOLTZ"],
                ["M_SUN", "R_SUN", "M_EARTH", "R_EARTH"],
                ["g_EARTH", "AU_DIST","⌫", "="]
            ],
            "Matrix & Vector Algebra": [
                ["Matrix([", "det(", "inv(", "trace("],
                ["transpose(","eigenvals(","eigenvects(","nullspace("],
                ["norm(", "cross(", "dot(", "eye("],
                ["zeros(", "ones(", "[", "]"],
                [",", "C", "⌫", "="]
            ],
            "Statistics & Probability": [
                ["mean(", "median(", "variance(", "std("],
                ["min(", "max(", "cov(", "corr("],
                ["binomial(","poisson(","normal(", "uniform("],
                ["factorial(","nCr(","nPr(", "gamma("],
                [",", "C", "⌫", "="]
            ],
            "Programmer & Logic": [
                ["bin(", "hex(", "oct(", "& (AND)"],
                ["| (OR)", "~ (NOT)", "^ (XOR)", "<<"],
                [">>", "True", "False", "Implies("],
                ["A", "B", "C", "D"],
                ["E", "F", "⌫", "="]
            ],
            "Quantum & Chem Constants": [
                ["N_AVOGADRO", "R_GAS", "F_FARADAY", "Rydberg"],
                ["Bohr_rad", "alpha_fs", "atm_press", "eV_J"],
                ["u_AMU", "sigma_SB", "wien_b", "flux_phi0"],
                ["G_0_cond", "K_J_jos", "R_K_von", "mu_Bohr"],
                ["mu_N", "C", "⌫", "="]
            ]
        }
        
        rows = calc_menus.get(calc_mode, calc_menus["Standard"])
        
        for row in rows:
            rc = st.columns(4)
            for ci, btn in enumerate(row):
                if btn:
                    with rc[ci]:
                        btn_type = "primary" if str(btn) == "=" else "secondary"
                        if st.button(str(btn), key=f"calc_{btn}_{row}_{calc_mode}", use_container_width=True, type=btn_type):
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
        st.session_state.setdefault("yt_transcript_data", None)
        if st.button("🎬 Load Transcript", use_container_width=True):
            with st.spinner("Fetching transcript…"):
                try:
                    transcript, vid_id = get_youtube_transcript(yt_url)
                    stats = get_transcript_stats(transcript)
                    ctx   = format_transcript_as_context(transcript, vid_id)
                    add_context(ctx, f"YT: {vid_id}", "youtube")
                    mins = stats.get("duration_minutes","?"); words = stats.get("word_count",0)
                    st.session_state.yt_transcript_data = {"txt": ctx, "json": json.dumps(transcript, indent=2), "vid": vid_id}
                    st.success(f"▶️ {mins} min · {words:,} words loaded!")
                except ValueError as e:
                    err = str(e).lower()
                    if "transcript" in err or "disabled" in err: st.error("❌ No transcript available for this video.")
                    elif "video id" in err: st.error("❌ Invalid YouTube URL.")
                    else: st.error(f"❌ {e}")

        # YouTube Advanced Download Options
        if st.session_state.get("yt_transcript_data"):
            dx1, dx2 = st.columns(2)
            d_data = st.session_state.yt_transcript_data
            with dx1: st.download_button("📥 .TXT", d_data["txt"], file_name=f"YT_{d_data['vid']}.txt", mime="text/plain", use_container_width=True)
            with dx2: st.download_button("📥 .JSON", d_data["json"], file_name=f"YT_{d_data['vid']}.json", mime="application/json", use_container_width=True)

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
        ("🃏", "Flashcards",      "Generate Q&A deck",           "flashcards"),
        ("📝", "Quiz Mode",       "MCQ assessment",               "quiz"),
        ("📊", "Mind Map",        "Visual concept map",           "mindmap"),
        ("📅", "Study Planner",   "Revision timetable",          "planner"),
        ("📈", "Graph Plotter",   "Plot equations",               "graph"),
        ("✍️", "Story Builder",   "AI creative writing",          "story"),
        ("🐛", "Code Debugger",   "Fix code in any language",     "debugger"),
        ("🎓", "Learn Coding",    "Interactive coding tutor",     "learn_coding"),
        ("📄", "Essay Writer",    "AI academic essay generator",  "essay_writer"),
        ("🎤", "Interview Coach", "Mock interviews + feedback",   "interview_coach"),
        ("🔬", "Research Assist", "Paper analysis & summaries",   "research_assistant"),
        ("🌍", "Language Tools",  "Translate + grammar + learn",  "language_tools"),
        ("🧮", "Science Solver",  "Math & science step solver",   "science_solver"),
        ("📓", "Smart Notes",     "AI notes from any content",    "smart_notes"),
        ("💬", "Chat",            "Standard AI study chat",       "chat"),
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

    # ── Exotic Power Tools ──────────────────────
    st.markdown('<div class="section-label">⚡ Exotic Power Tools</div>', unsafe_allow_html=True)
    _power_tools = [
        ("🔄", "Universal Converter", "Convert any file format instantly", "file_converter"),
        ("🔲", "QR Code Engine",      "Generate pro QR codes & data links", "qr_creator"),
        ("🤖", "AI Text Humaniser",   "Bypass AI detectors & sound human", "ai_humaniser"),
        ("🎨", "HTML Generator",      "AI to beautiful single-page website", "html_generator"),
        ("🕵️", "Reverse Image Search", "AI vision lookup & deep analysis", "image_searcher"),
    ]
    for icon, name, desc, mode in _power_tools:
        col_icon, col_info, col_btn = st.columns([1, 4, 2])
        with col_icon:
            st.markdown(f'<div style="font-size:1.2rem;padding-top:8px;">{icon}</div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(
                f'<div style="font-size:.84rem;font-weight:600;color:var(--text);">{name}</div>'
                f'<div style="font-size:.7rem;color:var(--text3);">{desc}</div>',
                unsafe_allow_html=True)
        with col_btn:
            if st.button("Launch", key=f"ptool_{mode}", use_container_width=True):
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
<div class="page-header">
  <div class="page-header-title">ExamHelp</div>
  <div class="page-header-sub">AI Study Companion{persona_tag}</div>
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
# AI EDITOR MODE
# ─────────────────────────────────────────────
elif app_mode == "editor":
    from ui.doc_editor import render_doc_editor
    render_doc_editor()

# ─────────────────────────────────────────────
# STORY BUILDER MODE
# ─────────────────────────────────────────────
elif app_mode == "story":
    from ui.story_builder import render_story_builder
    render_story_builder()

# ─────────────────────────────────────────────
# CODE DEBUGGER MODE
# ─────────────────────────────────────────────
elif app_mode == "debugger":
    from utils.debugger_engine import (
        debug_code, auto_detect_language, SUPPORTED_LANGUAGES,
    )

    c = {
        "bg": "#080810", "bg2": "#0e0e1a", "bg3": "#13131f",
        "accent": "#7c6af7", "accent2": "#a78bfa",
        "green": "#34d399", "red": "#f87171", "blue": "#60a5fa",
        "text": "#f0f0ff", "text2": "#9090b8", "border": "#1e1e30",
    }

    st.markdown(f"""
<style>
.debug-header {{
    background: linear-gradient(135deg, #1a0a2e 0%, #0d0d1a 100%);
    border: 1px solid #3d2a6b;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}}
.debug-header::before {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(124,106,247,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.debug-title {{ font-size: 1.9rem; font-weight: 800; color: #a78bfa; margin: 0 0 4px; }}
.debug-subtitle {{ font-size: 0.9rem; color: #9090b8; }}
.lang-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(124,106,247,0.12); border: 1px solid rgba(124,106,247,0.3);
    border-radius: 20px; padding: 4px 14px;
    font-size: 0.78rem; font-weight: 600; color: #a78bfa;
    margin: 4px 3px;
}}
.debug-result-box {{
    background: rgba(14,14,26,0.95);
    border: 1px solid rgba(124,106,247,0.25);
    border-radius: 14px;
    padding: 20px;
    margin-top: 20px;
}}
.debug-stat {{
    background: rgba(124,106,247,0.08);
    border: 1px solid rgba(124,106,247,0.2);
    border-radius: 10px;
    padding: 10px 16px;
    text-align: center;
}}
.debug-stat-val {{ font-size: 1.3rem; font-weight: 700; color: #a78bfa; }}
.debug-stat-lbl {{ font-size: 0.7rem; color: #9090b8; margin-top: 2px; }}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="debug-header">
  <div class="debug-title">🐛 Elite Code Debugger</div>
  <div class="debug-subtitle">Multi-language AI-powered debugging · Dedicated Gemini engine · Instant fixes</div>
</div>
""", unsafe_allow_html=True)

    # ── Language grid display ────────────────────────────────────
    lang_names = list(SUPPORTED_LANGUAGES.keys())
    badges = " ".join([
        f'<span class="lang-badge">{SUPPORTED_LANGUAGES[l]["icon"]} {l}</span>'
        for l in lang_names
    ])
    st.markdown(f'<div style="margin-bottom:20px;">{badges}</div>', unsafe_allow_html=True)

    # ── Controls row ─────────────────────────────────────────────
    col_lang, col_mode = st.columns([1, 1])
    with col_lang:
        sel_lang = st.selectbox(
            "🌐 Language",
            lang_names,
            index=lang_names.index(st.session_state.get("debug_language", "Python")),
            key="debug_lang_sel",
        )
        st.session_state.debug_language = sel_lang
    with col_mode:
        debug_mode = st.selectbox(
            "🔧 Debug Mode",
            ["Quick Fix", "Full Debug", "Code Review", "Explain Code", "Optimize"],
            index=["Quick Fix", "Full Debug", "Code Review", "Explain Code", "Optimize"].index(
                st.session_state.get("debug_mode", "Full Debug")
            ),
            key="debug_mode_sel",
        )
        st.session_state.debug_mode = debug_mode

    # ── Code input ───────────────────────────────────────────────
    lang_icon = SUPPORTED_LANGUAGES.get(sel_lang, {}).get("icon", "💻")
    code_input = st.text_area(
        f"{lang_icon} Paste your {sel_lang} code here",
        value=st.session_state.get("debug_code_input", ""),
        height=280,
        placeholder=f"# Paste your {sel_lang} code here...",
        key="debug_code_area",
    )
    st.session_state.debug_code_input = code_input

    # Auto-detect
    if code_input.strip():
        detected = auto_detect_language(code_input)
        if detected != sel_lang:
            st.caption(f"💡 Auto-detected: **{detected}** — change Language above if needed")

    col_err, col_exp = st.columns(2)
    with col_err:
        error_input = st.text_area(
            "⚠️ Error / Exception (optional)",
            value=st.session_state.get("debug_error_input", ""),
            height=100,
            placeholder="Paste the error message or traceback...",
            key="debug_error_area",
        )
        st.session_state.debug_error_input = error_input
    with col_exp:
        expected_input = st.text_area(
            "🎯 Expected Behavior (optional)",
            value=st.session_state.get("debug_expected_input", ""),
            height=100,
            placeholder="What should the code do?",
            key="debug_expected_area",
        )
        st.session_state.debug_expected_input = expected_input

    # ── Debug button ─────────────────────────────────────────────
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    with col_btn1:
        run_debug = st.button(
            f"🚀 {debug_mode} — Analyze Code",
            use_container_width=True,
            type="primary",
            disabled=not code_input.strip(),
        )
    with col_btn2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    with col_btn3:
        if st.button("💬 Back to Chat", use_container_width=True):
            st.session_state.app_mode = "chat"
            st.rerun()

    if clear_btn:
        st.session_state.debug_code_input = ""
        st.session_state.debug_error_input = ""
        st.session_state.debug_expected_input = ""
        st.session_state.debug_result = None
        st.rerun()

    if run_debug and code_input.strip():
        with st.spinner(f"🔍 {debug_mode} in progress — Gemini debug engine activated…"):
            t0 = time.time()
            try:
                result = debug_code(
                    code=code_input,
                    language=sel_lang,
                    error_message=error_input,
                    expected_behavior=expected_input,
                    debug_mode=debug_mode,
                )
                elapsed = time.time() - t0
                st.session_state.debug_result = result
                # Add to history
                st.session_state.debug_history.append({
                    "language": sel_lang,
                    "mode": debug_mode,
                    "code_preview": code_input[:120] + ("…" if len(code_input) > 120 else ""),
                    "result": result,
                    "time": elapsed,
                    "timestamp": time.strftime("%H:%M"),
                })
            except Exception as e:
                st.error(f"❌ Debug engine error: {e}")
                st.session_state.debug_result = None

    # ── Result display ───────────────────────────────────────────
    if st.session_state.get("debug_result"):
        result = st.session_state.debug_result
        history = st.session_state.debug_history
        elapsed = history[-1]["time"] if history else 0

        # Stats row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="debug-stat"><div class="debug-stat-val">{elapsed:.1f}s</div><div class="debug-stat-lbl">Analysis Time</div></div>', unsafe_allow_html=True)
        with c2:
            bug_count = len(re.findall(r'(?i)\b(bug|error|issue|problem|mistake|wrong|fix)\b', result))
            st.markdown(f'<div class="debug-stat"><div class="debug-stat-val">{bug_count}</div><div class="debug-stat-lbl">Issues Found</div></div>', unsafe_allow_html=True)
        with c3:
            lines = code_input.count('\n') + 1
            st.markdown(f'<div class="debug-stat"><div class="debug-stat-val">{lines}</div><div class="debug-stat-lbl">Lines Analyzed</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="debug-stat"><div class="debug-stat-val">{sel_lang}</div><div class="debug-stat-lbl">Language</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="debug-result-box">', unsafe_allow_html=True)
        st.markdown(result)
        st.markdown('</div>', unsafe_allow_html=True)

        # Export
        col_copy, col_dl = st.columns(2)
        with col_dl:
            st.download_button(
                "📥 Download Debug Report",
                data=f"# Debug Report — {sel_lang} — {debug_mode}\n\n{result}",
                file_name=f"debug_report_{sel_lang.lower().replace('/', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    # ── Debug history ────────────────────────────────────────────
    if st.session_state.debug_history:
        with st.expander(f"📜 Debug History ({len(st.session_state.debug_history)} sessions)", expanded=False):
            for i, h in enumerate(reversed(st.session_state.debug_history[-10:])):
                st.markdown(
                    f'**{h["timestamp"]}** · `{h["language"]}` · {h["mode"]} · {h["time"]:.1f}s\n\n'
                    f'```\n{h["code_preview"]}\n```'
                )
                if st.button(f"Load result #{len(st.session_state.debug_history)-i}", key=f"load_debug_{i}"):
                    st.session_state.debug_result = h["result"]
                    st.rerun()
                st.divider()


# ─────────────────────────────────────────────
# LEARN CODING MODE
# ─────────────────────────────────────────────
elif app_mode == "learn_coding":
    from utils.debugger_engine import (
        teach_concept, SUPPORTED_LANGUAGES, CURRICULUM,
        _call_gemini_debug, LEARN_SYSTEM_PROMPT,
    )

    st.markdown("""
<style>
.learn-header {
    background: linear-gradient(135deg, #0a1a2e 0%, #0d1a0d 100%);
    border: 1px solid #1a4a2a;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.learn-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(52,211,153,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.learn-title { font-size: 1.9rem; font-weight: 800; color: #34d399; margin: 0 0 4px; }
.learn-subtitle { font-size: 0.9rem; color: #9090b8; }
.topic-chip {
    display: inline-block;
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.25);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: #34d399;
    margin: 3px;
    cursor: pointer;
}
.learn-result-box {
    background: rgba(14,26,14,0.95);
    border: 1px solid rgba(52,211,153,0.2);
    border-radius: 14px;
    padding: 20px;
    margin-top: 20px;
}
.chat-bubble-user {
    background: rgba(124,106,247,0.1);
    border: 1px solid rgba(124,106,247,0.25);
    border-radius: 14px 14px 4px 14px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}
.chat-bubble-ai {
    background: rgba(52,211,153,0.06);
    border: 1px solid rgba(52,211,153,0.18);
    border-radius: 14px 14px 14px 4px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="learn-header">
  <div class="learn-title">🎓 Learn Coding</div>
  <div class="learn-subtitle">Interactive AI programming tutor · Step-by-step lessons · Practice exercises · Any language</div>
</div>
""", unsafe_allow_html=True)

    # ── Tabs: Structured Lessons vs Free Chat ──────────────────
    tab_lessons, tab_chat, tab_progress = st.tabs(["📚 Structured Lessons", "💬 Ask Anything", "📊 Progress"])

    with tab_lessons:
        col_ll, col_lv = st.columns([1, 1])
        with col_ll:
            lang_names = list(SUPPORTED_LANGUAGES.keys())
            learn_lang = st.selectbox(
                "🌐 Language to Learn",
                lang_names,
                index=lang_names.index(st.session_state.get("learn_language", "Python")),
                key="learn_lang_sel",
            )
            st.session_state.learn_language = learn_lang
        with col_lv:
            learn_level = st.selectbox(
                "📶 Your Level",
                ["Complete Beginner", "Beginner", "Intermediate", "Advanced", "Expert"],
                index=["Complete Beginner", "Beginner", "Intermediate", "Advanced", "Expert"].index(
                    st.session_state.get("learn_level", "Beginner")
                ),
                key="learn_level_sel",
            )
            st.session_state.learn_level = learn_level

        # Topic picker — from curriculum or custom
        topics = CURRICULUM.get(learn_lang, [])
        if topics:
            st.markdown("**📋 Curriculum Topics — Click to Learn:**")
            # Show as clickable buttons in a grid
            cols_per_row = 3
            rows = [topics[i:i+cols_per_row] for i in range(0, len(topics), cols_per_row)]
            for row in rows:
                btncols = st.columns(cols_per_row)
                for ci, topic in enumerate(row):
                    with btncols[ci]:
                        if st.button(topic, key=f"topic_{learn_lang}_{topic}", use_container_width=True):
                            st.session_state.learn_topic = topic
                            st.session_state.learn_result = None

        st.divider()

        custom_topic = st.text_input(
            "✏️ Or type a custom topic",
            value=st.session_state.get("learn_topic", ""),
            placeholder="e.g. Recursion, Binary Trees, REST APIs…",
            key="learn_topic_input",
        )
        if custom_topic:
            st.session_state.learn_topic = custom_topic

        specific_q = st.text_input(
            "❓ Specific question (optional)",
            value=st.session_state.get("learn_question", ""),
            placeholder="e.g. Why does Python pass objects by reference?",
            key="learn_q_input",
        )
        st.session_state.learn_question = specific_q

        col_lb1, col_lb2 = st.columns([2, 1])
        with col_lb1:
            learn_topic_val = st.session_state.get("learn_topic", "")
            start_lesson = st.button(
                f"🚀 Start Lesson: {learn_topic_val or 'Select a topic above'}",
                use_container_width=True,
                type="primary",
                disabled=not learn_topic_val.strip(),
            )
        with col_lb2:
            if st.button("💬 Back to Chat", use_container_width=True):
                st.session_state.app_mode = "chat"
                st.rerun()

        if start_lesson and st.session_state.get("learn_topic", "").strip():
            with st.spinner(f"📖 Generating lesson on {st.session_state.learn_topic}…"):
                try:
                    result = teach_concept(
                        topic=st.session_state.learn_topic,
                        language=learn_lang,
                        level=learn_level,
                        specific_question=st.session_state.get("learn_question", ""),
                    )
                    st.session_state.learn_result = result
                    st.session_state.learn_history.append({
                        "topic": st.session_state.learn_topic,
                        "language": learn_lang,
                        "level": learn_level,
                        "result": result,
                        "timestamp": time.strftime("%H:%M"),
                    })
                except Exception as e:
                    st.error(f"❌ Lesson engine error: {e}")

        if st.session_state.get("learn_result"):
            st.markdown('<div class="learn-result-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.learn_result)
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button(
                "📥 Save Lesson Notes",
                data=f"# {st.session_state.learn_topic} — {learn_lang}\nLevel: {learn_level}\n\n{st.session_state.learn_result}",
                file_name=f"lesson_{st.session_state.learn_topic.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with tab_chat:
        st.markdown("**💬 Ask Any Coding Question — Your AI Tutor Answers Instantly**")

        # Chat history
        for msg in st.session_state.learn_chat_messages:
            css_cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
            icon = "🧑‍💻" if msg["role"] == "user" else "🎓"
            st.markdown(
                f'<div class="{css_cls}">{icon} {msg["content"]}</div>',
                unsafe_allow_html=True,
            )

        user_q = st.text_input(
            "Ask your question",
            placeholder="e.g. What is a pointer? How do I sort a list in Python? Explain Big O notation…",
            key="learn_chat_input",
            label_visibility="collapsed",
        )
        col_ca, col_cb = st.columns([3, 1])
        with col_ca:
            send_chat = st.button("📤 Ask Tutor", use_container_width=True, type="primary")
        with col_cb:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.learn_chat_messages = []
                st.rerun()

        if send_chat and user_q.strip():
            st.session_state.learn_chat_messages.append({"role": "user", "content": user_q})
            learn_lang_chat = st.session_state.get("learn_language", "Python")
            learn_level_chat = st.session_state.get("learn_level", "Beginner")

            history_text = "\n".join([
                f"{'Student' if m['role'] == 'user' else 'Tutor'}: {m['content']}"
                for m in st.session_state.learn_chat_messages[-10:]
            ])

            prompt = f"""STUDENT LEVEL: {learn_level_chat}
PREFERRED LANGUAGE: {learn_lang_chat}

CONVERSATION:
{history_text}

Answer the student's latest question thoroughly, with code examples in {learn_lang_chat}.
"""
            with st.spinner("🎓 Tutor is thinking…"):
                try:
                    answer = _call_gemini_debug(prompt, LEARN_SYSTEM_PROMPT)
                    st.session_state.learn_chat_messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Tutor unavailable: {e}")
            st.rerun()

    with tab_progress:
        history = st.session_state.get("learn_history", [])
        if not history:
            st.info("📭 No lessons completed yet. Start a lesson to track progress!")
        else:
            st.markdown(f"**🏆 Lessons Completed: {len(history)}**")
            for h in reversed(history[-15:]):
                with st.expander(f"📖 {h['timestamp']} · {h['language']} · {h['topic']} ({h['level']})"):
                    st.markdown(h["result"])
            if st.button("🗑️ Clear Progress History"):
                st.session_state.learn_history = []
                st.rerun()



# ══════════════════════════════════════════════════════
# ESSAY WRITER MODE
# ══════════════════════════════════════════════════════
elif app_mode == "essay_writer":
    from utils.essay_engine import (
        generate_essay, improve_essay, generate_outline,
        ESSAY_TYPES, ACADEMIC_LEVELS, CITATION_STYLES,
    )
    st.markdown("""<style>
.ew-header{background:linear-gradient(135deg,#1a0a3e 0%,#0d0d1a 100%);border:1px solid #4a2a8b;border-radius:16px;padding:28px 32px;margin-bottom:24px;}
.ew-title{font-size:1.9rem;font-weight:800;color:#c084fc;margin:0 0 4px;}
.ew-sub{font-size:.9rem;color:#9090b8;}
.ew-box{background:rgba(20,10,40,.95);border:1px solid rgba(192,132,252,.2);border-radius:14px;padding:20px;margin-top:16px;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="ew-header"><div class="ew-title">📄 AI Essay Writer</div><div class="ew-sub">Academic essays, research papers, reports — fully structured, citation-ready</div></div>', unsafe_allow_html=True)

    tab_write, tab_outline, tab_improve, tab_hist = st.tabs(["✍️ Write Essay", "📋 Outline First", "🔧 Improve Essay", "📜 History"])

    with tab_write:
        c1, c2, c3 = st.columns(3)
        with c1:
            etype = st.selectbox("📝 Essay Type", list(ESSAY_TYPES.keys()), key="ew_type")
        with c2:
            elevel = st.selectbox("🎓 Academic Level", ACADEMIC_LEVELS, index=1, key="ew_level")
        with c3:
            ecite = st.selectbox("📚 Citation Style", CITATION_STYLES, key="ew_cite")
        etopic = st.text_input("💡 Essay Topic", placeholder="e.g. The impact of AI on employment in the next decade", key="ew_topic")
        c4, c5 = st.columns(2)
        with c4:
            ewords = st.slider("📏 Word Count", 300, 3000, 800, 100, key="ew_words")
        with c5:
            epoints = st.text_area("🔑 Key Points (optional)", height=80, placeholder="Arguments or points to include...", key="ew_points")
        if st.session_state.get("context_text"):
            use_ctx = st.checkbox("📎 Use uploaded study material as source", value=True, key="ew_ctx")
        else:
            use_ctx = False
        cb1, cb2 = st.columns([2,1])
        with cb1:
            write_btn = st.button("🚀 Generate Essay", type="primary", use_container_width=True, disabled=not etopic.strip(), key="ew_gen")
        with cb2:
            if st.button("💬 Back to Chat", use_container_width=True, key="ew_back"):
                st.session_state.app_mode = "chat"; st.rerun()
        if write_btn and etopic.strip():
            with st.spinner("✍️ Writing your essay..."):
                try:
                    ctx = st.session_state.context_text if use_ctx else ""
                    result = generate_essay(etopic, etype, ewords, elevel, ecite, epoints, ctx)
                    st.session_state.essay_result = result
                    st.session_state.essay_history.append({"topic": etopic, "type": etype, "level": elevel, "result": result, "ts": time.strftime("%H:%M")})
                except Exception as e:
                    st.error(f"❌ Essay engine error: {e}")
        if st.session_state.get("essay_result"):
            st.markdown('<div class="ew-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.essay_result)
            st.markdown('</div>', unsafe_allow_html=True)
            wc = len(st.session_state.essay_result.split())
            st.caption(f"📊 ~{wc} words")
            st.download_button("📥 Download Essay (.md)", st.session_state.essay_result,
                file_name="essay.md", mime="text/markdown", use_container_width=True, key="ew_dl")

    with tab_outline:
        ot = st.text_input("Topic for outline", key="eo_topic", placeholder="Enter topic...")
        oc1, oc2 = st.columns(2)
        with oc1: otype = st.selectbox("Type", list(ESSAY_TYPES.keys()), key="eo_type")
        with oc2: owords = st.slider("Target word count", 300, 3000, 800, 100, key="eo_words")
        if st.button("📋 Generate Outline", type="primary", use_container_width=True, disabled=not ot.strip(), key="eo_btn"):
            with st.spinner("Planning essay structure..."):
                try:
                    result = generate_outline(ot, otype, owords)
                    st.session_state.essay_outline = result
                except Exception as e:
                    st.error(f"❌ {e}")
        if st.session_state.get("essay_outline"):
            st.markdown('<div class="ew-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.essay_outline)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_improve:
        orig = st.text_area("📄 Paste your essay", height=200, key="ei_orig", placeholder="Paste your existing essay here...")
        instr = st.text_input("🔧 Improvement instruction", key="ei_instr",
            placeholder="e.g. Make the argument stronger, add more evidence, improve transitions...")
        if st.button("⚡ Improve Essay", type="primary", use_container_width=True, disabled=not (orig.strip() and instr.strip()), key="ei_btn"):
            with st.spinner("Improving essay..."):
                try:
                    result = improve_essay(orig, instr)
                    st.session_state.essay_result = result
                except Exception as e:
                    st.error(f"❌ {e}")
        if st.session_state.get("essay_result"):
            st.markdown('<div class="ew-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.essay_result)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_hist:
        hist = st.session_state.get("essay_history", [])
        if not hist:
            st.info("No essays written yet.")
        for h in reversed(hist[-10:]):
            with st.expander(f"📄 {h['ts']} · {h['type']} · {h['topic'][:40]}"):
                st.markdown(h["result"])
                st.download_button("📥 Download", h["result"], file_name=f"essay_{h['ts']}.md", key=f"edl_{h['ts']}")


# ══════════════════════════════════════════════════════
# INTERVIEW COACH MODE
# ══════════════════════════════════════════════════════
elif app_mode == "interview_coach":
    from utils.interview_engine import (
        generate_questions, evaluate_answer, mock_interview_response,
        generate_company_research, INTERVIEW_TYPES, EXPERIENCE_LEVELS,
    )
    st.markdown("""<style>
.ic-header{background:linear-gradient(135deg,#0a1e10 0%,#0d1a14 100%);border:1px solid #1a5a2a;border-radius:16px;padding:28px 32px;margin-bottom:24px;}
.ic-title{font-size:1.9rem;font-weight:800;color:#4ade80;margin:0 0 4px;}
.ic-sub{font-size:.9rem;color:#9090b8;}
.ic-q{background:rgba(10,30,16,.9);border:1px solid rgba(74,222,128,.2);border-radius:12px;padding:16px;margin:8px 0;}
.ic-a{background:rgba(26,46,26,.8);border:1px solid rgba(74,222,128,.15);border-radius:12px 12px 12px 4px;padding:14px;margin:6px 0;}
.ic-u{background:rgba(124,106,247,.08);border:1px solid rgba(124,106,247,.2);border-radius:12px 12px 4px 12px;padding:14px;margin:6px 0;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="ic-header"><div class="ic-title">🎤 AI Interview Coach</div><div class="ic-sub">Mock interviews · STAR method · Real-time feedback · Company research</div></div>', unsafe_allow_html=True)

    tab_mock, tab_bank, tab_eval, tab_company = st.tabs(["🎭 Live Mock Interview", "❓ Question Bank", "🎯 Evaluate Answer", "🏢 Company Research"])

    with tab_mock:
        mc1, mc2, mc3 = st.columns(3)
        with mc1: ic_role = st.text_input("Your Target Role", placeholder="e.g. Software Engineer at Google", key="ic_role")
        with mc2: ic_type = st.selectbox("Interview Type", list(INTERVIEW_TYPES.keys()), key="ic_type_mock")
        with mc3: ic_exp = st.selectbox("Experience Level", EXPERIENCE_LEVELS, key="ic_exp")
        st.session_state.interview_role = ic_role

        mb1, mb2, mb3 = st.columns(3)
        with mb1:
            if st.button("🚀 Start / Next Question", type="primary", use_container_width=True, disabled=not ic_role.strip(), key="ic_start"):
                with st.spinner("Interviewer thinking..."):
                    try:
                        st.session_state.interview_type = ic_type
                        resp = mock_interview_response(st.session_state.interview_messages, ic_role, ic_type, "ask")
                        st.session_state.interview_messages.append({"role": "assistant", "content": resp})
                    except Exception as e:
                        st.error(str(e))
        with mb2:
            if st.button("📊 Get Feedback", use_container_width=True, disabled=len(st.session_state.interview_messages) < 2, key="ic_fb"):
                with st.spinner("Generating feedback..."):
                    try:
                        fb = mock_interview_response(st.session_state.interview_messages, ic_role, ic_type, "feedback")
                        st.session_state.interview_feedback = fb
                    except Exception as e:
                        st.error(str(e))
        with mb3:
            if st.button("🗑️ Reset", use_container_width=True, key="ic_reset"):
                st.session_state.interview_messages = []
                st.session_state.interview_feedback = None
                st.rerun()

        # Chat display
        for msg in st.session_state.interview_messages:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="ic-q">🎤 <b>Interviewer:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ic-u">🧑 <b>You:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

        # Answer input
        if st.session_state.interview_messages and st.session_state.interview_messages[-1]["role"] == "assistant":
            user_ans = st.text_area("Your Answer", height=120, key="ic_ans", placeholder="Type your answer here...")
            if st.button("📤 Submit Answer", type="primary", use_container_width=True, disabled=not user_ans.strip(), key="ic_submit"):
                st.session_state.interview_messages.append({"role": "user", "content": user_ans})
                st.rerun()

        if st.session_state.get("interview_feedback"):
            with st.expander("📊 Interview Feedback", expanded=True):
                st.markdown(st.session_state.interview_feedback)

    with tab_bank:
        bc1, bc2 = st.columns(2)
        with bc1: bq_role = st.text_input("Role", placeholder="Software Engineer", key="bq_role")
        with bc2: bq_co = st.text_input("Company/Industry", placeholder="Google / Tech", key="bq_co")
        bc3, bc4, bc5 = st.columns(3)
        with bc3: bq_type = st.selectbox("Type", list(INTERVIEW_TYPES.keys()), key="bq_type")
        with bc4: bq_exp = st.selectbox("Level", EXPERIENCE_LEVELS, key="bq_exp")
        with bc5: bq_n = st.slider("# Questions", 5, 20, 10, key="bq_n")
        if st.button("🎲 Generate Question Bank", type="primary", use_container_width=True, disabled=not bq_role.strip(), key="bq_btn"):
            with st.spinner("Generating tailored questions..."):
                try:
                    result = generate_questions(bq_role, bq_co, bq_type, bq_exp, bq_n)
                    st.session_state.interview_questions = result
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("interview_questions"):
            st.markdown(st.session_state.interview_questions)
            st.download_button("📥 Save Question Bank", st.session_state.interview_questions, file_name="interview_questions.md", use_container_width=True, key="bq_dl")

    with tab_eval:
        eq1 = st.text_area("❓ Interview Question", height=80, key="eq_q", placeholder="Paste the interview question...")
        eq2 = st.text_area("💬 Your Answer", height=150, key="eq_a", placeholder="Type or paste your answer...")
        ec1, ec2 = st.columns(2)
        with ec1: eq_role = st.text_input("Role context", key="eq_role", placeholder="e.g. Product Manager")
        with ec2: eq_type = st.selectbox("Interview type", list(INTERVIEW_TYPES.keys()), key="eq_type")
        if st.button("🎯 Evaluate My Answer", type="primary", use_container_width=True, disabled=not (eq1.strip() and eq2.strip()), key="eq_btn"):
            with st.spinner("Evaluating your answer..."):
                try:
                    fb = evaluate_answer(eq1, eq2, eq_role, eq_type)
                    st.session_state.interview_feedback = fb
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("interview_feedback"):
            st.markdown(st.session_state.interview_feedback)

    with tab_company:
        cr1, cr2 = st.columns(2)
        with cr1: cr_co = st.text_input("Company Name", placeholder="e.g. Google", key="cr_co")
        with cr2: cr_role = st.text_input("Target Role", placeholder="e.g. Software Engineer", key="cr_role")
        if st.button("🏢 Research Company", type="primary", use_container_width=True, disabled=not (cr_co.strip() and cr_role.strip()), key="cr_btn"):
            with st.spinner(f"Researching {cr_co}..."):
                try:
                    result = generate_company_research(cr_co, cr_role)
                    st.markdown(result)
                except Exception as e:
                    st.error(str(e))
    if st.button("💬 Back to Chat", use_container_width=True, key="ic_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════
# RESEARCH ASSISTANT MODE
# ══════════════════════════════════════════════════════
elif app_mode == "research_assistant":
    from utils.research_engine import (
        summarize_paper, extract_concepts, generate_literature_review,
        critique_methodology, generate_research_proposal, explain_statistics,
    )
    st.markdown("""<style>
.ra-header{background:linear-gradient(135deg,#1a1000 0%,#1a0d00 100%);border:1px solid #5a3a00;border-radius:16px;padding:28px 32px;margin-bottom:24px;}
.ra-title{font-size:1.9rem;font-weight:800;color:#fbbf24;margin:0 0 4px;}
.ra-sub{font-size:.9rem;color:#9090b8;}
.ra-box{background:rgba(26,16,0,.95);border:1px solid rgba(251,191,36,.2);border-radius:14px;padding:20px;margin-top:16px;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="ra-header"><div class="ra-title">🔬 Research Assistant</div><div class="ra-sub">Paper summarization · Concept extraction · Literature reviews · Proposal writing</div></div>', unsafe_allow_html=True)

    tab_sum, tab_concepts, tab_lit, tab_critique, tab_prop, tab_stats = st.tabs(
        ["📄 Summarize", "🧠 Extract Concepts", "📚 Lit Review", "🔍 Critique Methods", "📝 Proposal", "📊 Stats Explainer"]
    )

    def _ra_content_source(key):
        src = st.radio("Content source", ["Use uploaded material", "Paste text"], horizontal=True, key=f"ra_src_{key}")
        if src == "Use uploaded material" and st.session_state.get("context_text"):
            return st.session_state.context_text
        else:
            return st.text_area("Paste text", height=200, key=f"ra_txt_{key}", placeholder="Paste paper/article text here...")

    with tab_sum:
        text = _ra_content_source("sum")
        detail = st.selectbox("Detail level", ["Quick (3 bullets)", "Standard", "Deep Analysis"], index=1, key="ra_sum_detail")
        if st.button("📄 Summarize", type="primary", use_container_width=True, disabled=not str(text).strip(), key="ra_sum_btn"):
            with st.spinner("Analyzing paper..."):
                try:
                    r = summarize_paper(str(text), detail)
                    st.session_state.research_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("research_result"):
            st.markdown('<div class="ra-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.research_result)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_concepts:
        text2 = _ra_content_source("con")
        if st.button("🧠 Extract Concepts", type="primary", use_container_width=True, disabled=not str(text2).strip(), key="ra_con_btn"):
            with st.spinner("Extracting concepts..."):
                try:
                    r = extract_concepts(str(text2))
                    st.session_state.research_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("research_result"):
            st.markdown(st.session_state.research_result)

    with tab_lit:
        rc1, rc2 = st.columns(2)
        with rc1: lit_topic = st.text_input("Research Topic", placeholder="e.g. Deep learning in medical imaging", key="lit_topic")
        with rc2: lit_field = st.text_input("Field/Discipline", placeholder="e.g. Computer Science / Medicine", key="lit_field")
        lit_scope = st.text_input("Scope", placeholder="e.g. 2018–2024, English-language studies only", key="lit_scope")
        if st.button("📚 Generate Literature Review", type="primary", use_container_width=True, disabled=not lit_topic.strip(), key="lit_btn"):
            with st.spinner("Writing literature review..."):
                try:
                    r = generate_literature_review(lit_topic, lit_scope, lit_field)
                    st.session_state.research_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("research_result"):
            st.markdown(st.session_state.research_result)
            st.download_button("📥 Download", st.session_state.research_result, file_name="lit_review.md", use_container_width=True, key="lit_dl")

    with tab_critique:
        text3 = _ra_content_source("crit")
        if st.button("🔍 Critique Methodology", type="primary", use_container_width=True, disabled=not str(text3).strip(), key="ra_crit_btn"):
            with st.spinner("Evaluating methodology..."):
                try:
                    r = critique_methodology(str(text3))
                    st.session_state.research_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("research_result"):
            st.markdown(st.session_state.research_result)

    with tab_prop:
        pp1, pp2, pp3 = st.columns(3)
        with pp1: prop_topic = st.text_input("Research Topic", key="prop_topic", placeholder="Your research question...")
        with pp2: prop_field = st.text_input("Field", key="prop_field", placeholder="e.g. Machine Learning")
        with pp3: prop_level = st.selectbox("Level", ["Undergraduate", "Masters", "PhD", "Postdoc", "Industry"], key="prop_level")
        if st.button("📝 Generate Proposal", type="primary", use_container_width=True, disabled=not prop_topic.strip(), key="prop_btn"):
            with st.spinner("Writing research proposal..."):
                try:
                    r = generate_research_proposal(prop_topic, prop_field, prop_level)
                    st.session_state.research_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("research_result"):
            st.markdown(st.session_state.research_result)
            st.download_button("📥 Download Proposal", st.session_state.research_result, file_name="research_proposal.md", use_container_width=True, key="prop_dl")

    with tab_stats:
        text4 = _ra_content_source("stats")
        if st.button("📊 Explain Statistics", type="primary", use_container_width=True, disabled=not str(text4).strip(), key="ra_stats_btn"):
            with st.spinner("Analysing statistics..."):
                try:
                    r = explain_statistics(str(text4))
                    st.session_state.research_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("research_result"):
            st.markdown(st.session_state.research_result)

    if st.button("💬 Back to Chat", use_container_width=True, key="ra_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════
# LANGUAGE TOOLS MODE
# ══════════════════════════════════════════════════════
elif app_mode == "language_tools":
    from utils.language_engine import (
        translate_text, grammar_check, teach_language_basics,
        explain_idioms, generate_language_quiz, LANGUAGES, TRANSLATION_MODES,
    )
    st.markdown("""<style>
.lt-header{background:linear-gradient(135deg,#001a2e 0%,#000d1a 100%);border:1px solid #005a8b;border-radius:16px;padding:28px 32px;margin-bottom:24px;}
.lt-title{font-size:1.9rem;font-weight:800;color:#38bdf8;margin:0 0 4px;}
.lt-sub{font-size:.9rem;color:#9090b8;}
.lt-box{background:rgba(0,26,46,.95);border:1px solid rgba(56,189,248,.2);border-radius:14px;padding:20px;margin-top:16px;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="lt-header"><div class="lt-title">🌍 Language Tools</div><div class="lt-sub">Translate · Grammar check · Learn languages · Idiom explainer · Language quizzes</div></div>', unsafe_allow_html=True)

    tab_trans, tab_gram, tab_learn, tab_idiom, tab_quiz = st.tabs(
        ["🔄 Translate", "✅ Grammar Check", "📖 Learn Language", "🗣️ Idioms & Phrases", "🎯 Language Quiz"]
    )

    with tab_trans:
        t_text = st.text_area("Text to translate", height=150, key="lt_text", placeholder="Enter text to translate...")
        tc1, tc2, tc3 = st.columns(3)
        with tc1: t_src = st.selectbox("From", LANGUAGES, key="lt_src")
        with tc2: t_tgt = st.selectbox("To", LANGUAGES, index=1, key="lt_tgt")
        with tc3: t_mode = st.selectbox("Mode", list(TRANSLATION_MODES.keys()), index=1, key="lt_mode")
        t_explain = st.checkbox("Include cultural notes & pronunciation", value=True, key="lt_explain")
        if st.button("🔄 Translate", type="primary", use_container_width=True, disabled=not t_text.strip(), key="lt_trans_btn"):
            with st.spinner(f"Translating to {t_tgt}..."):
                try:
                    r = translate_text(t_text, t_src, t_tgt, t_mode, t_explain)
                    st.session_state.lang_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("lang_result"):
            st.markdown('<div class="lt-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.lang_result)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_gram:
        g_text = st.text_area("Text to check", height=180, key="lt_gtext", placeholder="Paste text for grammar checking...")
        g_lang = st.selectbox("Language", LANGUAGES, key="lt_glang")
        if st.button("✅ Check Grammar", type="primary", use_container_width=True, disabled=not g_text.strip(), key="lt_gram_btn"):
            with st.spinner("Checking grammar..."):
                try:
                    r = grammar_check(g_text, g_lang)
                    st.session_state.lang_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("lang_result"):
            st.markdown(st.session_state.lang_result)

    with tab_learn:
        ll1, ll2, ll3 = st.columns(3)
        with ll1: l_lang = st.selectbox("Language to learn", LANGUAGES, key="lt_llang")
        with ll2: l_native = st.selectbox("Your language", LANGUAGES, key="lt_lnative")
        with ll3: l_topic = st.text_input("Topic/Grammar area", placeholder="e.g. Present tense verbs", key="lt_ltopic")
        if st.button("📖 Teach Me", type="primary", use_container_width=True, disabled=not l_topic.strip(), key="lt_learn_btn"):
            with st.spinner(f"Preparing lesson on {l_topic} in {l_lang}..."):
                try:
                    r = teach_language_basics(l_lang, l_topic, l_native)
                    st.session_state.lang_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("lang_result"):
            st.markdown(st.session_state.lang_result)

    with tab_idiom:
        i_text = st.text_area("Text with idioms/phrases", height=150, key="lt_itext", placeholder="Paste text containing idioms, slang or phrases...")
        i_lang = st.selectbox("Language", LANGUAGES, key="lt_ilang")
        if st.button("🗣️ Explain Idioms", type="primary", use_container_width=True, disabled=not i_text.strip(), key="lt_idiom_btn"):
            with st.spinner("Analysing expressions..."):
                try:
                    r = explain_idioms(i_text, i_lang)
                    st.session_state.lang_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("lang_result"):
            st.markdown(st.session_state.lang_result)

    with tab_quiz:
        qz1, qz2, qz3 = st.columns(3)
        with qz1: qz_lang = st.selectbox("Language", LANGUAGES, key="lt_qlang")
        with qz2: qz_topic = st.text_input("Topic", placeholder="e.g. Numbers, Greetings", key="lt_qtopic")
        with qz3: qz_level = st.selectbox("Level", ["Beginner","Intermediate","Advanced"], key="lt_qlevel")
        if st.button("🎯 Generate Quiz", type="primary", use_container_width=True, disabled=not qz_topic.strip(), key="lt_quiz_btn"):
            with st.spinner("Creating language quiz..."):
                try:
                    r = generate_language_quiz(qz_lang, qz_topic, qz_level)
                    st.session_state.lang_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("lang_result"):
            st.markdown(st.session_state.lang_result)

    if st.button("💬 Back to Chat", use_container_width=True, key="lt_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════
# SCIENCE / MATH SOLVER MODE
# ══════════════════════════════════════════════════════
elif app_mode == "science_solver":
    from utils.solver_engine import (
        solve_problem, explain_concept, generate_practice_problems,
        check_solution, formula_sheet, SUBJECTS,
    )
    st.markdown("""<style>
.ss-header{background:linear-gradient(135deg,#1a0000 0%,#1a0a00 100%);border:1px solid #5a1a00;border-radius:16px;padding:28px 32px;margin-bottom:24px;}
.ss-title{font-size:1.9rem;font-weight:800;color:#f97316;margin:0 0 4px;}
.ss-sub{font-size:.9rem;color:#9090b8;}
.ss-box{background:rgba(26,6,0,.95);border:1px solid rgba(249,115,22,.2);border-radius:14px;padding:20px;margin-top:16px;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="ss-header"><div class="ss-title">🧮 Science & Math Solver</div><div class="ss-sub">Step-by-step solutions · Concept explainer · Practice problems · Formula sheets</div></div>', unsafe_allow_html=True)

    subject_names = list(SUBJECTS.keys())
    tab_solve, tab_explain, tab_practice, tab_check, tab_formula = st.tabs(
        ["⚡ Solve Problem", "📖 Explain Concept", "🏋️ Practice", "✅ Check My Work", "📋 Formula Sheet"]
    )

    with tab_solve:
        ss1, ss2 = st.columns(2)
        with ss1: sv_subj = st.selectbox("Subject", subject_names, key="ss_subj")
        with ss2: sv_diff = st.selectbox("Difficulty", ["Easy","Standard","Hard","Olympiad/Competition"], index=1, key="ss_diff")
        sv_prob = st.text_area("Problem", height=160, key="ss_prob", placeholder="Type or paste the problem here. Include all given values, units, and what to find...")
        sv_alt = st.checkbox("Show alternative solution method", value=True, key="ss_alt")
        if st.button("⚡ Solve Step-by-Step", type="primary", use_container_width=True, disabled=not sv_prob.strip(), key="ss_solve_btn"):
            with st.spinner(f"Solving {sv_subj} problem..."):
                try:
                    r = solve_problem(sv_prob, sv_subj, sv_alt, sv_diff)
                    st.session_state.solver_result = r
                    st.session_state.solver_history.append({"subj": sv_subj, "prob": sv_prob[:80], "r": r, "ts": time.strftime("%H:%M")})
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("solver_result"):
            st.markdown('<div class="ss-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.solver_result)
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("📥 Save Solution", st.session_state.solver_result, file_name="solution.md", use_container_width=True, key="ss_dl")

    with tab_explain:
        ec1, ec2 = st.columns(2)
        with ec1:
            ex_subj = st.selectbox("Subject", subject_names, key="ex_subj")
            topics = SUBJECTS[ex_subj]["topics"]
        with ec2:
            ex_topic = st.selectbox("Topic", topics, key="ex_topic")
        ex_concept = st.text_input("Specific concept", placeholder="e.g. Rolle's Theorem, Newton's 2nd Law", key="ex_concept")
        ex_depth = st.selectbox("Depth", ["Quick Overview","Standard","Expert Deep Dive"], index=1, key="ex_depth")
        if st.button("📖 Explain", type="primary", use_container_width=True, disabled=not ex_concept.strip(), key="ex_btn"):
            with st.spinner(f"Explaining {ex_concept}..."):
                try:
                    r = explain_concept(ex_concept, ex_subj, ex_depth)
                    st.session_state.solver_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("solver_result"):
            st.markdown(st.session_state.solver_result)

    with tab_practice:
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1: pr_subj = st.selectbox("Subject", subject_names, key="pr_subj")
        with pc2:
            pr_topics = SUBJECTS[pr_subj]["topics"]
            pr_topic = st.selectbox("Topic", pr_topics, key="pr_topic")
        with pc3: pr_diff = st.selectbox("Difficulty", ["Easy","Medium","Hard"], key="pr_diff")
        with pc4: pr_n = st.slider("# Problems", 3, 10, 5, key="pr_n")
        if st.button("🏋️ Generate Practice Problems", type="primary", use_container_width=True, key="pr_btn"):
            with st.spinner("Creating practice problems..."):
                try:
                    r = generate_practice_problems(pr_subj, pr_topic, pr_diff, pr_n)
                    st.session_state.solver_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("solver_result"):
            st.markdown(st.session_state.solver_result)

    with tab_check:
        ck1 = st.text_area("Problem statement", height=100, key="ck_prob", placeholder="Paste the original problem...")
        ck2 = st.text_area("Your solution", height=150, key="ck_sol", placeholder="Paste your solution attempt...")
        ck_subj = st.selectbox("Subject", subject_names, key="ck_subj")
        if st.button("✅ Check My Work", type="primary", use_container_width=True, disabled=not (ck1.strip() and ck2.strip()), key="ck_btn"):
            with st.spinner("Evaluating solution..."):
                try:
                    r = check_solution(ck1, ck2, ck_subj)
                    st.session_state.solver_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("solver_result"):
            st.markdown(st.session_state.solver_result)

    with tab_formula:
        fc1, fc2 = st.columns(2)
        with fc1: fs_subj = st.selectbox("Subject", subject_names, key="fs_subj")
        with fc2:
            fs_topics = SUBJECTS[fs_subj]["topics"]
            fs_topic = st.selectbox("Topic", fs_topics, key="fs_topic")
        if st.button("📋 Generate Formula Sheet", type="primary", use_container_width=True, key="fs_btn"):
            with st.spinner(f"Building {fs_topic} formula sheet..."):
                try:
                    r = formula_sheet(fs_subj, fs_topic)
                    st.session_state.solver_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("solver_result"):
            st.markdown(st.session_state.solver_result)
            st.download_button("📥 Save Formula Sheet", st.session_state.solver_result, file_name="formula_sheet.md", use_container_width=True, key="fs_dl")

    if st.button("💬 Back to Chat", use_container_width=True, key="ss_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════
# SMART NOTES MODE
# ══════════════════════════════════════════════════════
elif app_mode == "smart_notes":
    from utils.notes_engine import (
        generate_notes, smart_summarize, extract_exam_questions,
        build_concept_map, paraphrase_text, NOTE_FORMATS,
    )
    st.markdown("""<style>
.sn-header{background:linear-gradient(135deg,#001a1a 0%,#000d10 100%);border:1px solid #005a5a;border-radius:16px;padding:28px 32px;margin-bottom:24px;}
.sn-title{font-size:1.9rem;font-weight:800;color:#2dd4bf;margin:0 0 4px;}
.sn-sub{font-size:.9rem;color:#9090b8;}
.sn-box{background:rgba(0,26,26,.95);border:1px solid rgba(45,212,191,.2);border-radius:14px;padding:20px;margin-top:16px;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="sn-header"><div class="sn-title">📓 Smart Notes</div><div class="sn-sub">Cornell notes · Cheat sheets · Exam questions · Concept maps · Paraphrase — from any content</div></div>', unsafe_allow_html=True)

    def _sn_source(key):
        if st.session_state.get("context_text"):
            src = st.radio("Source", ["Uploaded material", "Paste text"], horizontal=True, key=f"sn_src_{key}")
            if src == "Uploaded material":
                return st.session_state.context_text
        return st.text_area("Paste content", height=200, key=f"sn_paste_{key}", placeholder="Paste text, notes, or any content to process...")

    tab_notes, tab_sum, tab_exam, tab_map, tab_para = st.tabs(
        ["📝 Smart Notes", "⚡ Summarize", "🎯 Exam Questions", "🗺️ Concept Map", "🔄 Paraphrase"]
    )

    with tab_notes:
        content = _sn_source("notes")
        nc1, nc2, nc3 = st.columns(3)
        with nc1: n_fmt = st.selectbox("Format", list(NOTE_FORMATS.keys()), key="sn_fmt")
        with nc2: n_subj = st.text_input("Subject", placeholder="e.g. Physics", key="sn_subj")
        with nc3: n_focus = st.text_input("Focus area", placeholder="e.g. Key formulas only", key="sn_focus")
        if st.button("📝 Generate Notes", type="primary", use_container_width=True, disabled=not str(content).strip(), key="sn_notes_btn"):
            with st.spinner(f"Creating {n_fmt}..."):
                try:
                    r = generate_notes(str(content), n_fmt, n_subj, n_focus)
                    st.session_state.notes_result = r
                    st.session_state.notes_history.append({"fmt": n_fmt, "subj": n_subj, "r": r, "ts": time.strftime("%H:%M")})
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("notes_result"):
            st.markdown('<div class="sn-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.notes_result)
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("📥 Download Notes", st.session_state.notes_result, file_name=f"{n_fmt.replace(' ','_')}_notes.md", use_container_width=True, key="sn_dl")

    with tab_sum:
        content2 = _sn_source("sum")
        sc1, sc2 = st.columns(2)
        with sc1: s_len = st.selectbox("Length", ["Tweet (280 chars)","Quick (50 words)","Short (150 words)","Medium (300 words)","Long (600 words)","Executive Summary"], index=3, key="sn_slen")
        with sc2: s_style = st.selectbox("Style", ["Academic","Casual","Technical","Journalistic","Simple (ELI5)"], key="sn_sstyle")
        s_preserve = st.text_input("Must include", placeholder="Any specific points that must appear in summary...", key="sn_spreserve")
        if st.button("⚡ Summarize", type="primary", use_container_width=True, disabled=not str(content2).strip(), key="sn_sum_btn"):
            with st.spinner("Summarizing..."):
                try:
                    r = smart_summarize(str(content2), s_len, s_style, s_preserve)
                    st.session_state.notes_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("notes_result"):
            st.markdown('<div class="sn-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.notes_result)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_exam:
        content3 = _sn_source("exam")
        e_type = st.selectbox("Exam type", ["University Exam","School Final Exam","Competitive Exam (UPSC/JEE/NEET)","Professional Certification","Viva/Oral Exam"], key="sn_etype")
        if st.button("🎯 Generate Exam Questions", type="primary", use_container_width=True, disabled=not str(content3).strip(), key="sn_exam_btn"):
            with st.spinner("Predicting exam questions..."):
                try:
                    r = extract_exam_questions(str(content3), e_type)
                    st.session_state.notes_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("notes_result"):
            st.markdown(st.session_state.notes_result)
            st.download_button("📥 Download Q&A", st.session_state.notes_result, file_name="exam_questions.md", use_container_width=True, key="sn_exam_dl")

    with tab_map:
        content4 = _sn_source("map")
        if st.button("🗺️ Build Concept Map", type="primary", use_container_width=True, disabled=not str(content4).strip(), key="sn_map_btn"):
            with st.spinner("Mapping concepts..."):
                try:
                    r = build_concept_map(str(content4))
                    st.session_state.notes_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("notes_result"):
            st.markdown(st.session_state.notes_result)

    with tab_para:
        p_text = st.text_area("Text to paraphrase", height=180, key="sn_ptext", placeholder="Paste text to reword/paraphrase...")
        pp1, pp2 = st.columns(2)
        with pp1: p_style = st.selectbox("Style", ["Academic","Casual","Formal","Simple","Technical"], key="sn_pstyle")
        with pp2: p_simplify = st.checkbox("Simplify (make easier)", key="sn_psimplify")
        if st.button("🔄 Paraphrase", type="primary", use_container_width=True, disabled=not p_text.strip(), key="sn_para_btn"):
            with st.spinner("Paraphrasing..."):
                try:
                    r = paraphrase_text(p_text, p_style, p_simplify)
                    st.session_state.notes_result = r
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("notes_result"):
            st.markdown(st.session_state.notes_result)

    if st.button("💬 Back to Chat", use_container_width=True, key="sn_back"):
        st.session_state.app_mode = "chat"; st.rerun()

# ─── FILE CONVERTER ───────────────────────────────────────────────────────────
elif app_mode == "file_converter":
    from converter_engine import get_supported_formats, convert_file
    st.markdown("## 🔄 Universal File Converter")
    supported = get_supported_formats()
    fmt_list = sorted(supported.keys())
    col1, col2 = st.columns(2)
    with col1:
        from_fmt = st.selectbox("From format", fmt_list, key="conv_from")
    with col2:
        to_fmts = supported.get(from_fmt, [])
        to_fmt = st.selectbox("To format", to_fmts, key="conv_to")
    uploaded = st.file_uploader(f"Upload {from_fmt.upper()} file", type=[from_fmt])
    if uploaded and st.button("Convert Now ⚡", type="primary"):
        with st.spinner("Converting..."):
            data = uploaded.read()
            result, mime, ext, err = convert_file(data, from_fmt, to_fmt, uploaded.name)
        if err:
            st.error(err)
        else:
            st.success("Conversion complete!")
            out_name = uploaded.name.rsplit(".", 1)[0] + "." + ext
            st.download_button(f"⬇️ Download {out_name}", result, file_name=out_name, mime=mime)

# ─── QR CREATOR ───────────────────────────────────────────────────────────────
elif app_mode == "qr_creator":
    from qr_engine import generate_text_qr, generate_url_qr, generate_vcard_qr, generate_wifi_qr, generate_email_qr, generate_phone_qr, generate_sms_qr, qr_to_base64
    st.markdown("## 📲 QR Code Creator")
    qr_type = st.selectbox("QR Type", ["Text / URL","vCard","WiFi","Email","Phone","SMS"])
    qr_bytes = None
    if qr_type == "Text / URL":
        val = st.text_input("Enter text or URL")
        if st.button("Generate QR", type="primary") and val:
            qr_bytes = generate_url_qr(val) if val.startswith("http") else generate_text_qr(val)
    elif qr_type == "vCard":
        n = st.text_input("Full Name"); ph = st.text_input("Phone"); em = st.text_input("Email")
        if st.button("Generate QR", type="primary") and n:
            qr_bytes = generate_vcard_qr(n, ph, em)
    elif qr_type == "WiFi":
        ssid = st.text_input("SSID"); pwd = st.text_input("Password", type="password")
        if st.button("Generate QR", type="primary") and ssid:
            qr_bytes = generate_wifi_qr(ssid, pwd)
    elif qr_type == "Email":
        to = st.text_input("To Email"); subj = st.text_input("Subject")
        if st.button("Generate QR", type="primary") and to:
            qr_bytes = generate_email_qr(to, subj)
    elif qr_type == "Phone":
        ph = st.text_input("Phone Number")
        if st.button("Generate QR", type="primary") and ph:
            qr_bytes = generate_phone_qr(ph)
    elif qr_type == "SMS":
        ph = st.text_input("Phone"); msg = st.text_area("Message")
        if st.button("Generate QR", type="primary") and ph:
            qr_bytes = generate_sms_qr(ph, msg)
    if qr_bytes:
        st.image(qr_bytes, caption="Your QR Code", width=300)
        st.download_button("⬇️ Download QR PNG", qr_bytes, file_name="qr_code.png", mime="image/png")

# ─── AI HUMANISER ─────────────────────────────────────────────────────────────
elif app_mode == "ai_humaniser":
    from humaniser_engine import humanise_text, ai_detection_score, TONE_HINTS
    st.markdown("## ✨ AI Text Humaniser")
    text_in = st.text_area("Paste AI-generated text here", height=220)
    col1, col2 = st.columns(2)
    with col1:
        tone = st.selectbox("Target Tone", list(TONE_HINTS.keys()))
    with col2:
        preserve = st.checkbox("Preserve structure (headings/bullets)", value=True)
    if st.button("Detect AI Score", type="secondary") and text_in:
        det = ai_detection_score(text_in)
        st.metric("AI Detection Score", f"{det['score']}/100", det["label"])
        if det["flags"]:
            for f in det["flags"]: st.markdown(f"- {f}")
    if st.button("Humanise Now ✨", type="primary") and text_in:
        with st.spinner("Humanising..."):
            result = humanise_text(text_in, tone=tone, preserve_structure=preserve)
        st.markdown("### ✅ Humanised Output")
        st.text_area("Result", value=result, height=280)
        st.download_button("⬇️ Download TXT", result.encode(), file_name="humanised.txt", mime="text/plain")

# ─── HTML GENERATOR ───────────────────────────────────────────────────────────
elif app_mode == "html_generator":
    from html_generator_engine import generate_html_page, generate_html_from_file, PAGE_TYPES, COLOR_THEMES
    st.markdown("## 🌐 AI HTML Page Generator")
    tab_text, tab_file = st.tabs(["From Text/Content", "From Uploaded File"])
    with tab_text:
        title = st.text_input("Page Title", value="My Awesome Page")
        content = st.text_area("Content / Brief / Data", height=200)
        col1, col2 = st.columns(2)
        with col1:
            ptype = st.selectbox("Page Type", list(PAGE_TYPES.keys()))
        with col2:
            theme = st.selectbox("Color Theme", list(COLOR_THEMES.keys()))
        charts = st.checkbox("Include Charts (Chart.js)", value=False)
        extra = st.text_input("Extra instructions (optional)")
        if st.button("Generate HTML ⚡", type="primary") and content:
            with st.spinner("Generating beautiful HTML page..."):
                html_out = generate_html_page(content, ptype, title, theme, charts, extra)
            st.success("HTML generated!")
            st.download_button("⬇️ Download HTML", html_out.encode(), file_name=f"{title.replace(' ','_')}.html", mime="text/html")
            with st.expander("Preview HTML Source"):
                st.code(html_out[:3000], language="html")
    with tab_file:
        upl = st.file_uploader("Upload any file to convert to HTML", type=["pdf","txt","csv","json","md","docx"])
        ptype2 = st.selectbox("Layout Style", list(PAGE_TYPES.keys()), key="html_ftype")
        if upl and st.button("Convert to HTML 🌐", type="primary"):
            from converter_engine import _pdf_to_text, _docx_to_text, _csv_to_text, _excel_to_text
            raw = upl.read()
            ext = upl.name.rsplit(".",1)[-1].lower()
            if ext == "pdf":   fc = _pdf_to_text(raw)
            elif ext == "docx": fc = _docx_to_text(raw)
            elif ext == "csv":  fc = _csv_to_text(raw)
            else:               fc = raw.decode("utf-8", errors="replace")
            with st.spinner("Generating HTML from your file..."):
                html_out = generate_html_from_file(fc, ext, upl.name, ptype2)
            st.success("Done!")
            st.download_button("⬇️ Download HTML", html_out.encode(), file_name=upl.name.rsplit(".",1)[0]+".html", mime="text/html")

# ─── IMAGE SEARCHER ───────────────────────────────────────────────────────────
elif app_mode == "image_searcher":
    from image_search_engine import search_by_image
    st.markdown("## 🔍 AI Image Search — Find 20+ Related Links")
    st.caption("Upload any photo and AI will analyze it, identify the subject, and find 20+ links exactly related to it.")
    img_file = st.file_uploader("Upload Image", type=["jpg","jpeg","png","webp","gif"])
    if img_file:
        st.image(img_file, width=320, caption="Uploaded Image")
        if st.button("🔍 Search the Web for This Image", type="primary"):
            img_bytes = img_file.read()
            ext = img_file.name.rsplit(".",1)[-1].lower()
            mime_map = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp","gif":"image/gif"}
            mime = mime_map.get(ext, "image/jpeg")
            with st.spinner("Analyzing image with Gemini Vision + searching the web..."):
                results = search_by_image(img_bytes, mime, img_file.name)
            analysis = results.get("analysis", {})
            st.markdown("### 🧠 AI Analysis")
            col1, col2, col3 = st.columns(3)
            col1.metric("Subject", analysis.get("main_subject","—")[:30])
            col2.metric("Category", analysis.get("category","—"))
            col3.metric("Links Found", len(results.get("links", [])))
            st.markdown(f"**Description:** {analysis.get('description','—')}")
            if analysis.get("visible_text"):
                st.info(f"📝 Text in image: {analysis['visible_text']}")
            if results.get("search_queries"):
                st.markdown("**Search queries used:** " + " · ".join([f"`{q}`" for q in results["search_queries"][:5]]))
            st.markdown(f"### 🔗 {len(results.get('links',[]))} Related Links Found")
            type_icons = {"image_host":"🖼️","encyclopedia":"📚","news":"📰","official":"🏛️","social":"💬","stock":"💼","search_result":"🔎","image_search":"🔍","reverse_image":"🔄"}
            for i, link in enumerate(results.get("links",[]), 1):
                icon = type_icons.get(link.get("type",""), "🔗")
                with st.expander(f"{icon} {i}. {link.get('title','Link')[:70]}"):
                    st.markdown(f"**URL:** [{link.get('url','')}]({link.get('url','')})")
                    st.markdown(f"**Why relevant:** {link.get('reason','')}")
                    st.markdown(f"**Domain:** `{link.get('domain','')}`")

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
            Get expert explanations, flashcards, quizzes, and more.<br><br>
            <span style="color: var(--primary-color);">💡 Kindly upload a PDF, PNG, or other study material to use the document-specific functions below.</span>
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
                        safe_speak = _safe_js_text(msg["content"][:2000])
                        js_code = f'<script>window.parent.speechSynthesis.cancel();const s=new window.parent.SpeechSynthesisUtterance("{safe_speak}");window.parent.speechSynthesis.speak(s);</script>'
                        import streamlit.components.v1 as components
                        components.html(js_code, height=0, width=0)
                        st.toast("Reading aloud...")

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

    elif user_input and any(kw in txt_low for kw in ["debug", "fix my code", "my code has", "code debugger", "open debugger"]):
        st.session_state.app_mode = "debugger"
        st.session_state.messages.append({"role":"user","content":user_input})
        st.session_state.messages.append({"role":"assistant","content":"🐛 **Code Debugger Activated** — paste your code in the debug workspace."})
        st.rerun()

    elif user_input and any(kw in txt_low for kw in ["learn coding", "teach me", "learn python", "learn javascript", "learn c++", "coding tutor", "open learn"]):
        st.session_state.app_mode = "learn_coding"
        st.session_state.messages.append({"role":"user","content":user_input})
        st.session_state.messages.append({"role":"assistant","content":"🎓 **Learn Coding Mode Activated** — choose a language and topic to begin your lesson."})
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

            chosen_model = st.session_state.get("model_choice","llama-4-scout-17b-16e-instruct")

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

        chart_fig = None
        if "CHART_MANIFEST:" in cleaned_text:
            try:
                import json, re
                match = re.search(r'CHART_MANIFEST:\s*(\{.*?\})', cleaned_text, re.DOTALL)
                if match:
                    manifest = json.loads(match.group(1))
                    from utils.graph_engine import generate_advanced_chart
                    chart_fig, _ = generate_advanced_chart(
                        data=manifest.get("data", {}),
                        chart_type=manifest.get("type", "bar"),
                        title=manifest.get("title", "Data Visualization")
                    )
                cleaned_text = re.sub(r'---?\s*CHART_MANIFEST:.*', '', cleaned_text, flags=re.DOTALL).strip()
            except Exception as e:
                import logging
                logging.error(f"Chart manifest error: {e}")

        math_fig = None
        if "MATH_PLOT_MANIFEST:" in cleaned_text:
            try:
                import json, re
                match = re.search(r'MATH_PLOT_MANIFEST:\s*(\{.*?\})', cleaned_text, re.DOTALL)
                if match:
                    m = json.loads(match.group(1))
                    from utils.graph_engine import plot_2d_graph, plot_3d_graph, plot_polar_graph, plot_parametric_3d
                    p_type = m.get("type", "2d")
                    funcs = m.get("functions", [])
                    
                    if p_type == "2d" and funcs:
                        math_fig, _ = plot_2d_graph(funcs, m.get("x_min",-10), m.get("x_max",10))
                    elif p_type == "3d" and funcs:
                        math_fig, _ = plot_3d_graph(funcs[0])
                    elif p_type == "polar" and funcs:
                        math_fig, _ = plot_polar_graph(funcs[0], 0, m.get("theta_max", 31.415))
                    elif p_type == "parametric" and len(funcs) >= 3:
                        math_fig, _ = plot_parametric_3d(funcs[0], funcs[1], funcs[2])
                cleaned_text = re.sub(r'---?\s*MATH_PLOT_MANIFEST:.*', '', cleaned_text, flags=re.DOTALL).strip()
            except Exception as e:
                import logging
                logging.error(f"Math plot error: {e}")

        tab_exp, tab_res, tab_lab, tab_share = st.tabs(["🎓 Explanation","📚 Resources","🛠️ Study Lab","🔗 Share"])

        with tab_exp:
            st.markdown(cleaned_text)
            if chart_fig: st.plotly_chart(chart_fig, use_container_width=True)
            if math_fig: st.plotly_chart(math_fig, use_container_width=True)
                
            # Inline math rendering hint
            if any(sym in cleaned_text for sym in ["$$","\\(","\\["]):
                st.info("💡 This response contains LaTeX math. It renders automatically in Streamlit.")

            # Browser-Native Text-to-Speech execution (If Voice Mode enabled)
            if st.session_state.get("voice_mode"):
                safe_speak = _safe_js_text(cleaned_text[:1500])
                js_code = f'<script>window.speechSynthesis.cancel();const s=new SpeechSynthesisUtterance("{safe_speak}");s.rate=1.0;window.speechSynthesis.speak(s);</script>'
                import streamlit.components.v1 as components
                components.html(js_code, height=0)

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
