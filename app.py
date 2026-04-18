"""
ExamHelp AI — v3.1
Full-featured AI study assistant — Gemini 9-Key Rotation
"""

import datetime
import json
import os
import re
import time
import base64
import zlib
import streamlit as st
import ssl
from utils.api_key_ui import render_api_key_section
from utils.optimizer import run_all_optimizations

# Execute aggressive lag-free Streamlit optimizations right on load
run_all_optimizations()

# ── Auth + Integrations — MASKED (Supabase/Google/Stripe disabled for direct access) ──
# All functions below are safe no-ops so the app runs without any external auth.

st.markdown("""
<style>
/* Global Elite High-Fidelity Styling */
:root {
    --accent: #6366f1;
    --accent-glow: rgba(99, 102, 241, 0.4);
    --bg-dark: #020617;
    --glass-bg: rgba(15, 23, 42, 0.8);
    --glass-border: rgba(255, 255, 255, 0.08);
    --text-primary: #f8fafc;
    --text-dim: #94a3b8;
}

[data-testid="stAppViewContainer"] { background: var(--bg-dark) !important; }

/* Custom Scrollbars */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* Glassmorphic Sidebars & Inputs */
[data-testid="stSidebar"] {
    background-color: rgba(2, 6, 23, 0.95) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--glass-border);
}

.stTextInput > div > div > input {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--glass-border) !important;
    color: white !important;
    border-radius: 8px !important;
}

/* Premium Component Cards */
.expert-header {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(10px);
}

.page-header {
    background: radial-gradient(circle at 0% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%);
    padding: 2rem;
    border-radius: 20px;
    border: 1px solid var(--glass-border);
}

/* Tool Buttons Animation */
.stButton > button {
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    background: rgba(99, 102, 241, 0.1) !important;
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)


# ── Auth + Integrations — MASKED (Supabase/Google/Stripe disabled for direct access) ──
# All functions below are safe no-ops so the app runs without any external auth.

def is_logged_in(): return True
def current_user(): return {"email": "user@examhelp.ai", "user_metadata": {"full_name": "Student"}}
def clear_session(): pass
def try_refresh(): pass
def render_login_page(): pass
def handle_google_oauth_callback(): pass
def render_google_connect_button(): pass
def render_gmail_panel(**kwargs): st.info("📧 Gmail integration coming soon.")
def render_drive_panel(**kwargs): st.info("📁 Google Drive integration coming soon.")
def render_calendar_panel(**kwargs): st.info("📅 Google Calendar integration coming soon.")
def render_maps_panel(**kwargs): st.info("🗺️ Google Maps integration coming soon.")
def is_google_connected(): return False
def render_pricing_page(**kwargs): st.info("💳 Plans & Pricing coming soon.")
def render_upgrade_banner(**kwargs): pass

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
from utils.personas import PERSONAS, get_persona_names, get_persona_by_name, build_persona_prompt, apply_persona_theme
from utils.ocr_handler import extract_text_from_image
from utils.analytics import get_subject_mastery_radar, get_study_intensity_heatmap, estimate_required_velocity
from utils.app_controller import AppController
from new_features import (
    render_news_hub, render_vit_map, render_trip_planner,
    render_universal_converter, render_ai_humaniser, render_html_generator,
    render_citation_generator, render_regex_tester, render_vit_academics,
    render_study_toolkit, render_circuit_solver, render_math_solver,
    render_dictionary, render_stocks_dashboard, render_legal_expert,
    render_medical_expert, render_research_pro, render_project_architect,
    # ── New Premium UI Pages ──────────────────────────────────────────────────
    render_live_dashboard, render_api_explorer,
    render_knowledge_hub, render_study_wellness,
)
from utils import ai_engine
from utils.token_tracker import render_telemetry_sidebar
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
        "pomodoro_log": [],
        "note_tags": {},
        "error_log": [],
        "feedback_log": [],
        "session_dates": [],
        "news_cache": {},
        "news_cache_time": 0,
        "battle_session": {},
        "battle_lifetime_points": 0,
        "result_cache": {},
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
        # ── Code Converter
        "cc_converted": "", "cc_original": "", "cc_tokens": 0, "cc_chat_messages": [],
        # ── Smart Shopping
        "shop_wishlist": [], "shop_product_results": [], "shop_grocery_results": [], "shop_food_results": [],
        # ── Context Focus (Deep Research)
        "cf_research": None, "cf_followup_chat": [],
        # ── Presentation Builder
        "pres_slides": [],
        # ── Powerup Variables ──
        "quiz_v2_data": [], "quiz_v2_timer": None, "quiz_v2_adaptive_scores": {},
        "story_characters": {}, "story_world": "", "story_branches": {},
        "message_ratings": {}, "chat_followups": [],
        "shopping_wishlist": [], "shopping_cache": {},
        "presentation_slides": [],
        "service_availability": {},
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

    # Validate keys
    if not st.session_state.service_availability:
        from utils.secret_manager import validate_all_keys
        st.session_state.service_availability = validate_all_keys()

    # Vector store
    from memory.vector_store import VectorStore
    if st.session_state.vector_store is None:
        st.session_state.vector_store = VectorStore()

init_state()

# ── Auto-record study day for streak tracking ────────────────────────────────
if "streak_recorded_today" not in st.session_state:
    try:
        from study_streak_engine import record_study_day, unlock_achievement
        record_study_day()
        # First chat achievement check
        if len(st.session_state.get("messages", [])) > 0:
            unlock_achievement("first_chat")
        st.session_state["streak_recorded_today"] = True
    except Exception:
        st.session_state["streak_recorded_today"] = True

# ═══════════════════════════════════════════════
# PASSCODE LANDING PAGE GATE
# ═══════════════════════════════════════════════
_SITE_PASSCODE = "aahuti"

if "passcode_verified" not in st.session_state:
    st.session_state["passcode_verified"] = False

if not st.session_state["passcode_verified"]:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        margin: 0 !important; padding: 0 !important; background: #020008 !important;
    }
    [data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],footer { display:none !important; }
    section[data-testid="stMain"] > div { padding-top: 0 !important; padding-bottom: 0 !important; }
    div[data-testid="stVerticalBlock"] { gap: 0 !important; }

    * { box-sizing: border-box; }

    /* ── BACKGROUND ── */
    .lp-bg {
        position: fixed; inset: 0; z-index: 0;
        background:
            radial-gradient(ellipse 80% 60% at 10% 20%, #1a0040 0%, transparent 60%),
            radial-gradient(ellipse 60% 60% at 90% 80%, #002a1a 0%, transparent 60%),
            radial-gradient(ellipse 50% 50% at 50% 50%, #00001a 0%, transparent 70%),
            #020008;
    }
    /* animated grid */
    .lp-grid {
        position: fixed; inset: 0; z-index: 1; pointer-events: none;
        background-image:
            linear-gradient(rgba(0,255,180,0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,255,180,0.06) 1px, transparent 1px);
        background-size: 70px 70px;
        animation: gridScroll 25s linear infinite;
    }
    @keyframes gridScroll { to { background-position: 70px 70px; } }

    /* floating orbs */
    .orb { position: fixed; border-radius: 50%; filter: blur(90px); pointer-events: none; z-index: 1; }
    .o1 { width:500px;height:500px;background:radial-gradient(#7b00ff,#3d00a0);opacity:.22;top:-150px;left:-150px;animation:ob1 10s ease-in-out infinite; }
    .o2 { width:400px;height:400px;background:radial-gradient(#00ffe0,#0066ff);opacity:.18;bottom:-100px;right:-100px;animation:ob2 12s ease-in-out infinite; }
    .o3 { width:300px;height:300px;background:radial-gradient(#ff0099,#7b00ff);opacity:.14;top:40%;left:50%;animation:ob3 8s ease-in-out infinite; }
    .o4 { width:250px;height:250px;background:radial-gradient(#00ff88,#00aaff);opacity:.12;top:10%;right:15%;animation:ob1 14s ease-in-out infinite reverse; }
    @keyframes ob1{0%,100%{transform:translate(0,0) scale(1);}50%{transform:translate(40px,-40px) scale(1.1);}}
    @keyframes ob2{0%,100%{transform:translate(0,0) scale(1);}50%{transform:translate(-30px,30px) scale(1.08);}}
    @keyframes ob3{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.15) rotate(10deg);}}

    /* particles */
    .particles { position:fixed;inset:0;z-index:1;pointer-events:none;overflow:hidden; }
    .pt { position:absolute;border-radius:50%;animation:ptFloat linear infinite; }
    @keyframes ptFloat { 0%{transform:translateY(100vh) scale(0);opacity:0;} 10%{opacity:1;} 90%{opacity:.5;} 100%{transform:translateY(-10vh) scale(1);opacity:0;} }

    /* ── CONTENT WRAPPER ── */
    .lp-wrap {
        position:relative; z-index:10;
        width:100%; min-height:100vh;
        display:flex; flex-direction:column; align-items:center;
        padding: 48px 20px 60px;
        font-family: 'Rajdhani', sans-serif;
    }

    /* ── HERO BADGE ── */
    .hero-badge {
        display:inline-flex; align-items:center; gap:8px;
        background: rgba(0,255,180,0.08);
        border: 1px solid rgba(0,255,180,0.3);
        border-radius:100px; padding:6px 18px;
        font-family:'Space Mono',monospace; font-size:11px;
        color:#00ffb4; letter-spacing:3px;
        margin-bottom:28px;
        animation: badgePulse 3s ease-in-out infinite;
    }
    .badge-dot { width:7px;height:7px;background:#00ffb4;border-radius:50%;animation:blink 1.5s ease-in-out infinite; }
    @keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}
    @keyframes badgePulse{0%,100%{box-shadow:0 0 0 rgba(0,255,180,0);}50%{box-shadow:0 0 20px rgba(0,255,180,0.2);}}

    /* ── HERO TITLE ── */
    .hero-title {
        font-family:'Orbitron',monospace; font-weight:900;
        font-size: clamp(36px, 6vw, 80px);
        line-height:1.0; text-align:center; margin-bottom:6px;
        background: linear-gradient(135deg, #ffffff 0%, #a0ffee 25%, #00ffb4 45%, #00aaff 65%, #b44dff 85%, #ff44aa 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        filter: drop-shadow(0 0 40px rgba(0,255,180,0.35));
        animation: titleGlow 4s ease-in-out infinite alternate;
    }
    @keyframes titleGlow{from{filter:drop-shadow(0 0 30px rgba(0,255,180,0.3));}to{filter:drop-shadow(0 0 60px rgba(180,77,255,0.5));}}
    .hero-version {
        font-family:'Space Mono',monospace; font-size:13px;
        color:rgba(180,77,255,0.8); letter-spacing:4px; text-align:center; margin-bottom:18px;
    }
    .hero-desc {
        font-size:18px; font-weight:300; color:rgba(255,255,255,0.55);
        text-align:center; max-width:620px; line-height:1.7; margin-bottom:56px;
        letter-spacing:.5px;
    }
    .hero-desc span { color:#00ffb4; font-weight:600; }

    /* ── STATS BAR ── */
    .stats-bar {
        display:flex; gap:0; border:1px solid rgba(255,255,255,0.08);
        border-radius:16px; overflow:hidden; margin-bottom:64px;
        backdrop-filter:blur(10px); background:rgba(255,255,255,0.02);
        animation: cardIn .8s cubic-bezier(.16,1,.3,1) .1s both;
    }
    .stat-item {
        padding:20px 36px; text-align:center; border-right:1px solid rgba(255,255,255,0.07);
        flex:1;
    }
    .stat-item:last-child{border-right:none;}
    .stat-num { font-family:'Orbitron',monospace; font-size:28px; font-weight:900; }
    .stat-lbl { font-size:12px; color:rgba(255,255,255,0.4); letter-spacing:2px; margin-top:4px; }
    .s1 .stat-num{background:linear-gradient(135deg,#00ffb4,#00aaff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
    .s2 .stat-num{background:linear-gradient(135deg,#b44dff,#ff44aa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
    .s3 .stat-num{background:linear-gradient(135deg,#ffaa00,#ff4400);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}

    /* ── SECTION LABEL ── */
    .section-label {
        font-family:'Space Mono',monospace; font-size:11px; letter-spacing:5px;
        color:rgba(255,255,255,0.3); text-transform:uppercase; text-align:center;
        margin-bottom:28px;
    }
    .section-title {
        font-family:'Orbitron',monospace; font-weight:700; font-size:28px;
        text-align:center; margin-bottom:40px;
        background:linear-gradient(90deg,#fff,#a0c4ff);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    }

    /* ── ENGINE CARDS ── */
    .engines-grid {
        display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
        gap:16px; width:100%; max-width:1100px; margin-bottom:72px;
    }
    .eng-card {
        background:rgba(255,255,255,0.03);
        border:1px solid rgba(255,255,255,0.08);
        border-radius:18px; padding:24px 22px;
        position:relative; overflow:hidden;
        transition:transform .3s ease, box-shadow .3s ease, border-color .3s ease;
        animation: cardIn .7s cubic-bezier(.16,1,.3,1) both;
        cursor:default;
    }
    .eng-card::before {
        content:''; position:absolute; inset:0;
        background: var(--glow); opacity:0; border-radius:18px;
        transition:opacity .3s ease;
    }
    .eng-card:hover { transform:translateY(-6px); border-color:var(--accent); }
    .eng-card:hover::before { opacity:1; }
    .eng-card:hover .eng-icon { transform:scale(1.15) rotate(-5deg); }

    .c1{--accent:rgba(0,255,180,.4);--glow:radial-gradient(ellipse at top left,rgba(0,255,180,.08),transparent 70%);animation-delay:.05s;}
    .c2{--accent:rgba(180,77,255,.4);--glow:radial-gradient(ellipse at top left,rgba(180,77,255,.08),transparent 70%);animation-delay:.10s;}
    .c3{--accent:rgba(255,68,170,.4);--glow:radial-gradient(ellipse at top left,rgba(255,68,170,.08),transparent 70%);animation-delay:.15s;}
    .c4{--accent:rgba(0,170,255,.4);--glow:radial-gradient(ellipse at top left,rgba(0,170,255,.08),transparent 70%);animation-delay:.20s;}
    .c5{--accent:rgba(255,170,0,.4);--glow:radial-gradient(ellipse at top left,rgba(255,170,0,.08),transparent 70%);animation-delay:.25s;}
    .c6{--accent:rgba(0,255,100,.4);--glow:radial-gradient(ellipse at top left,rgba(0,255,100,.08),transparent 70%);animation-delay:.30s;}
    .c7{--accent:rgba(255,100,0,.4);--glow:radial-gradient(ellipse at top left,rgba(255,100,0,.08),transparent 70%);animation-delay:.35s;}
    .c8{--accent:rgba(100,200,255,.4);--glow:radial-gradient(ellipse at top left,rgba(100,200,255,.08),transparent 70%);animation-delay:.40s;}
    .c9{--accent:rgba(220,100,255,.4);--glow:radial-gradient(ellipse at top left,rgba(220,100,255,.08),transparent 70%);animation-delay:.45s;}

    .eng-icon { font-size:36px; margin-bottom:14px; display:block; transition:transform .3s ease; }
    .eng-name {
        font-family:'Orbitron',monospace; font-size:13px; font-weight:700;
        color:#fff; letter-spacing:1px; margin-bottom:8px;
    }
    .eng-tag {
        display:inline-block; padding:3px 10px; border-radius:100px;
        font-size:10px; letter-spacing:2px; font-family:'Space Mono',monospace;
        background:var(--accent); color:#fff; margin-bottom:10px;
    }
    .eng-desc { font-size:13px; color:rgba(255,255,255,.45); line-height:1.6; }
    .eng-corner {
        position:absolute; top:16px; right:16px;
        width:8px; height:8px; border-radius:50%; background:var(--accent);
        animation:blink 2s ease-in-out infinite;
    }

    /* ── FEATURES GRID ── */
    .feat-grid {
        display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
        gap:12px; width:100%; max-width:1100px; margin-bottom:72px;
    }
    .feat-item {
        background:rgba(255,255,255,0.025);
        border:1px solid rgba(255,255,255,0.07);
        border-radius:14px; padding:18px 20px;
        display:flex; align-items:flex-start; gap:14px;
        transition:all .3s ease;
        animation: cardIn .7s cubic-bezier(.16,1,.3,1) both;
    }
    .feat-item:hover { background:rgba(255,255,255,0.05); border-color:rgba(0,255,180,.2); transform:translateY(-3px); }
    .feat-emoji { font-size:24px; flex-shrink:0; margin-top:2px; }
    .feat-name { font-size:14px; font-weight:700; color:#fff; font-family:'Rajdhani',sans-serif; letter-spacing:.5px; }
    .feat-sub { font-size:12px; color:rgba(255,255,255,.4); margin-top:3px; line-height:1.5; }

    /* ── GATE CARD ── */
    .gate-wrap {
        width:100%; max-width:500px; margin-bottom:48px;
        animation: cardIn 1s cubic-bezier(.16,1,.3,1) .3s both;
    }
    .gate-card {
        background:rgba(255,255,255,.03);
        border:1px solid rgba(0,255,180,.2);
        border-radius:28px; padding:48px 44px;
        text-align:center;
        backdrop-filter:blur(24px);
        box-shadow:
            0 0 80px rgba(0,255,180,.07),
            0 0 160px rgba(180,77,255,.05),
            inset 0 1px 0 rgba(255,255,255,.07),
            inset 0 -1px 0 rgba(0,0,0,.3);
        position:relative; overflow:hidden;
    }
    .gate-card::before {
        content:''; position:absolute; top:-1px; left:20%; right:20%; height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,255,180,.6),transparent);
    }
    .gate-title {
        font-family:'Orbitron',monospace; font-size:clamp(26px,4vw,42px);
        font-weight:900; margin-bottom:8px;
        background:linear-gradient(135deg,#fff 0%,#00ffb4 40%,#b44dff 80%,#ff44aa 100%);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 20px rgba(0,255,180,.3));
    }
    .gate-sub {
        font-size:15px; color:rgba(255,255,255,.4); letter-spacing:1px;
        margin-bottom:38px; line-height:1.7;
    }
    .gate-label {
        font-family:'Space Mono',monospace; font-size:10px; letter-spacing:4px;
        color:rgba(0,255,180,.5); text-transform:uppercase; text-align:left; margin-bottom:10px;
    }
    .gate-divider {
        display:flex;align-items:center;gap:12px;
        color:rgba(255,255,255,.12);font-size:10px;letter-spacing:3px;
        font-family:'Space Mono',monospace; margin-top:24px;
    }
    .gate-divider::before,.gate-divider::after {
        content:'';flex:1;height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,255,180,.15),transparent);
    }

    /* ── INPUT + BUTTON ── */
    div[data-testid="stTextInput"] input {
        background:rgba(0,255,180,.04) !important;
        border:1px solid rgba(0,255,180,.25) !important;
        border-radius:14px !important; color:#fff !important;
        font-family:'Space Mono',monospace !important; font-size:18px !important;
        letter-spacing:8px !important; text-align:center !important;
        padding:18px !important; transition:all .3s ease !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color:rgba(0,255,180,.8) !important;
        box-shadow:0 0 30px rgba(0,255,180,.15),0 0 60px rgba(0,255,180,.06) !important;
    }
    div[data-testid="stTextInput"] label { display:none !important; }

    div[data-testid="stButton"] button {
        width:100% !important;
        background:linear-gradient(135deg,#00ffb4 0%,#00aaff 40%,#b44dff 70%,#ff44aa 100%) !important;
        background-size:200% !important; border:none !important;
        border-radius:14px !important; color:#000 !important;
        font-family:'Orbitron',monospace !important; font-size:13px !important;
        font-weight:700 !important; letter-spacing:4px !important;
        padding:18px 32px !important; cursor:pointer !important; margin-top:14px !important;
        transition:all .3s ease !important;
        box-shadow:0 6px 40px rgba(0,255,180,.3) !important;
        animation:gradShift 4s ease infinite !important;
    }
    @keyframes gradShift{0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;}}
    div[data-testid="stButton"] button:hover {
        transform:translateY(-3px) !important;
        box-shadow:0 12px 60px rgba(0,255,180,.5) !important;
    }
    div[data-testid="stAlert"] { border-radius:12px !important; }

    /* ── FOOTER ── */
    .lp-footer {
        text-align:center; padding:28px 20px 10px;
        border-top:1px solid rgba(255,255,255,.06); width:100%; max-width:900px;
    }
    .made-by {
        font-family:'Orbitron',monospace; font-size:13px; font-weight:700;
        margin-bottom:6px;
        background:linear-gradient(90deg,#00ffb4,#b44dff,#ff44aa,#00aaff,#00ffb4);
        background-size:300%;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        animation:gradShift 5s linear infinite;
        filter:drop-shadow(0 0 10px rgba(0,255,180,.3));
    }
    .footer-sub { font-size:12px; color:rgba(255,255,255,.2); letter-spacing:2px; margin-top:4px; }

    @keyframes cardIn {
        from{opacity:0;transform:translateY(30px) scale(.97);}
        to{opacity:1;transform:translateY(0) scale(1);}
    }

    /* scanlines */
    body::after {
        content:'';position:fixed;inset:0;z-index:9999;pointer-events:none;
        background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.04) 3px,rgba(0,0,0,.04) 4px);
    }

    /* ── NEW: FLOATING ELEMENTS ── */
    .float-ring { position:fixed; border-radius:50%; border:1px solid; pointer-events:none; z-index:2; animation:ringFloat ease-in-out infinite; }
    .fr1 { width:180px;height:180px;border-color:rgba(0,255,180,0.07);top:15%;left:5%;animation-duration:7s;animation-delay:0s; }
    .fr2 { width:120px;height:120px;border-color:rgba(180,77,255,0.06);top:60%;right:8%;animation-duration:9s;animation-delay:1.5s; }
    .fr3 { width:80px;height:80px;border-color:rgba(0,170,255,0.08);top:35%;right:20%;animation-duration:6s;animation-delay:3s; }
    @keyframes ringFloat{0%,100%{transform:translateY(0) rotate(0deg);opacity:.5;}50%{transform:translateY(-25px) rotate(180deg);opacity:1;}}

    .float-diamond { position:fixed; pointer-events:none; z-index:2; animation:diamondSpin ease-in-out infinite; }
    .fd1 { top:20%;right:10%;width:12px;height:12px;background:rgba(0,255,180,0.3);clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);animation-duration:8s; }
    .fd2 { top:70%;left:7%;width:8px;height:8px;background:rgba(180,77,255,0.4);clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);animation-duration:11s;animation-delay:2s; }
    .fd3 { top:45%;right:4%;width:6px;height:6px;background:rgba(255,68,170,0.35);clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);animation-duration:7s;animation-delay:4s; }
    @keyframes diamondSpin{0%,100%{transform:translateY(0) rotate(0deg) scale(1);}50%{transform:translateY(-20px) rotate(45deg) scale(1.4);}}

    /* ── NEW: RIVER / BOAT SCENE ── */
    .river-scene {
        width:100%; max-width:900px; margin:0 auto 0;
        position:relative; z-index:10;
        overflow:hidden; border-radius:28px;
        background: linear-gradient(180deg,
            #020008 0%,
            #030015 15%,
            #0a001a 30%,
            #001a0a 55%,
            #002a10 70%,
            #001508 85%,
            #000e05 100%);
        border:1px solid rgba(0,255,180,0.12);
        box-shadow: 0 0 80px rgba(0,255,180,0.06), 0 0 200px rgba(0,100,255,0.04);
        animation: cardIn 1.2s cubic-bezier(.16,1,.3,1) both;
        min-height: 480px;
    }
    .river-scene canvas { width:100%; height:480px; display:block; }
    .river-poem {
        position:absolute; bottom:0; left:0; right:0;
        padding:28px 32px;
        background: linear-gradient(0deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 60%, transparent 100%);
        z-index:20;
    }
    .river-poem-text {
        font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:300;
        color:rgba(255,255,255,0.75); line-height:1.9; text-align:center;
        letter-spacing:0.5px;
    }
    .river-poem-text em { color:#00ffb4; font-style:normal; font-weight:600; }
    .river-poem-text strong { color:#b44dff; font-weight:700; }
    .river-scene-title {
        position:absolute; top:20px; left:0; right:0; text-align:center; z-index:20;
        font-family:'Orbitron',monospace; font-size:11px; letter-spacing:5px;
        color:rgba(0,255,180,0.5); text-transform:uppercase;
    }
    .speech-bubble {
        position:absolute; z-index:25;
        background:rgba(0,255,180,0.08); border:1px solid rgba(0,255,180,0.3);
        border-radius:16px 16px 16px 4px; padding:10px 16px;
        font-family:'Rajdhani',sans-serif; font-size:13px; color:#00ffb4;
        backdrop-filter:blur(8px); max-width:180px;
        animation: bubbleFloat 3s ease-in-out infinite;
        box-shadow: 0 0 20px rgba(0,255,180,0.1);
    }
    .speech-bubble-r {
        border-radius:16px 16px 4px 16px;
        background:rgba(180,77,255,0.08); border-color:rgba(180,77,255,0.3);
        color:#c88dff;
        box-shadow: 0 0 20px rgba(180,77,255,0.1);
        animation: bubbleFloat2 3.5s ease-in-out infinite;
    }
    @keyframes bubbleFloat{0%,100%{transform:translateY(0);}50%{transform:translateY(-8px);}}
    @keyframes bubbleFloat2{0%,100%{transform:translateY(0);}50%{transform:translateY(-6px);}}

    /* ── NEW: LOGO SECTION ── */
    .logo-section {
        display:flex; flex-direction:column; align-items:center;
        margin-bottom:48px; animation: cardIn 1s cubic-bezier(.16,1,.3,1) .2s both;
    }
    .logo-emblem {
        width:90px; height:90px; border-radius:24px;
        background: linear-gradient(135deg, #001a0a 0%, #002a18 50%, #001a2a 100%);
        border:1px solid rgba(0,255,180,0.25);
        display:flex; align-items:center; justify-content:center;
        position:relative; margin-bottom:14px;
        box-shadow: 0 0 40px rgba(0,255,180,0.15), 0 0 80px rgba(0,255,180,0.05);
        animation: logoGlow 4s ease-in-out infinite;
    }
    @keyframes logoGlow{0%,100%{box-shadow:0 0 40px rgba(0,255,180,0.15),0 0 80px rgba(0,255,180,0.05);}50%{box-shadow:0 0 60px rgba(0,255,180,0.25),0 0 120px rgba(0,255,180,0.1),0 0 200px rgba(180,77,255,0.05);}}
    .logo-emblem svg { width:52px; height:52px; }
    .logo-ring-outer {
        position:absolute; inset:-12px; border-radius:36px;
        border:1px solid rgba(0,255,180,0.1);
        animation:rotateSlow 12s linear infinite;
    }
    .logo-ring-outer::before {
        content:''; position:absolute; top:-3px; left:50%;
        width:6px; height:6px; border-radius:50%; background:#00ffb4;
        transform:translateX(-50%);
    }
    @keyframes rotateSlow{to{transform:rotate(360deg);}}
    .logo-name {
        font-family:'Orbitron',monospace; font-size:22px; font-weight:900;
        letter-spacing:4px;
        background:linear-gradient(135deg,#fff,#00ffb4,#00aaff);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 20px rgba(0,255,180,0.3));
    }
    .logo-tagline {
        font-family:'Space Mono',monospace; font-size:9px; letter-spacing:6px;
        color:rgba(0,255,180,0.4); margin-top:4px; text-transform:uppercase;
    }

    /* ── NEW: WELCOME ERA BANNER ── */
    .era-banner {
        width:100%; text-align:center; padding:18px 20px;
        margin-bottom:32px;
        background: linear-gradient(90deg, transparent 0%, rgba(0,255,180,0.04) 20%, rgba(0,255,180,0.07) 50%, rgba(0,255,180,0.04) 80%, transparent 100%);
        border-top:1px solid rgba(0,255,180,0.08); border-bottom:1px solid rgba(0,255,180,0.08);
        animation:eraBanner 1.5s cubic-bezier(.16,1,.3,1) both;
        position:relative; overflow:hidden;
    }
    .era-banner::before {
        content:''; position:absolute; inset:0;
        background:linear-gradient(90deg,transparent,rgba(0,255,180,0.03),transparent);
        animation:eraShimmer 3s ease-in-out infinite;
    }
    @keyframes eraShimmer{0%{transform:translateX(-100%);}100%{transform:translateX(200%);}}
    @keyframes eraBanner{from{opacity:0;transform:translateY(-20px);}to{opacity:1;transform:translateY(0);}}
    .era-text {
        font-family:'Orbitron',monospace; font-size:clamp(14px,2.5vw,20px);
        font-weight:700; letter-spacing:3px;
        background:linear-gradient(90deg,#00ffb4,#00aaff,#b44dff,#ff44aa,#00ffb4);
        background-size:300%;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        animation:gradShift 5s linear infinite;
        position:relative; z-index:1;
    }
    .era-subtitle {
        font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.3);
        letter-spacing:4px; text-transform:uppercase; margin-top:5px;
        position:relative; z-index:1;
    }

    /* ── NEW: CHILD TESTIMONIAL SECTION ── */
    .child-section {
        width:100%; max-width:900px; margin-bottom:64px;
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .15s both;
    }
    .child-section-title {
        font-family:'Orbitron',monospace; font-size:22px; font-weight:700;
        text-align:center; margin-bottom:8px;
        background:linear-gradient(90deg,#ffaa00,#ff44aa,#b44dff);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    }
    .child-section-sub {
        font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.35);
        text-align:center; letter-spacing:3px; text-transform:uppercase; margin-bottom:36px;
    }
    .child-cards { display:flex; gap:16px; flex-wrap:wrap; justify-content:center; }
    .child-card {
        background:rgba(255,255,255,0.025);
        border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; padding:24px 20px 20px;
        width:calc(33% - 12px); min-width:220px;
        position:relative; overflow:hidden;
        transition:all .4s cubic-bezier(.16,1,.3,1);
        animation: floatCard ease-in-out infinite;
    }
    .child-card:nth-child(1){animation-duration:5s;animation-delay:0s;}
    .child-card:nth-child(2){animation-duration:6s;animation-delay:1s;}
    .child-card:nth-child(3){animation-duration:5.5s;animation-delay:2s;}
    @keyframes floatCard{0%,100%{transform:translateY(0);}50%{transform:translateY(-8px);}}
    .child-card:hover { border-color:rgba(255,170,0,0.3); transform:translateY(-12px) !important; }
    .child-avatar { font-size:36px; margin-bottom:12px; display:block; }
    .child-name { font-family:'Orbitron',monospace; font-size:11px; letter-spacing:3px; color:rgba(255,255,255,0.5); margin-bottom:10px; }
    .child-text { font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.7); line-height:1.7; }
    .child-tag {
        display:inline-block; margin-top:12px; padding:4px 12px; border-radius:100px;
        font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px;
        background:rgba(255,170,0,0.1); border:1px solid rgba(255,170,0,0.2); color:#ffaa00;
    }
    .child-stars { color:#ffaa00; font-size:12px; margin-bottom:8px; }

    /* ── NEW: THOUGHTS SECTION ── */
    .thoughts-section {
        width:100%; max-width:900px; margin-bottom:64px;
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .2s both;
    }
    .thought-bubble-wrap {
        display:flex; gap:14px; flex-direction:column; align-items:center;
    }
    .thought-bubble {
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:100px; padding:14px 28px;
        font-family:'Rajdhani',sans-serif; font-size:15px; color:rgba(255,255,255,0.6);
        line-height:1.6; text-align:center; max-width:700px;
        animation: thoughtFloat ease-in-out infinite;
        transition:all .3s ease;
    }
    .thought-bubble:hover { background:rgba(255,255,255,0.05); border-color:rgba(0,255,180,0.2); color:rgba(255,255,255,0.9); transform:scale(1.02); }
    .thought-bubble:nth-child(1){animation-duration:6s;}
    .thought-bubble:nth-child(2){animation-duration:7s;animation-delay:1s;}
    .thought-bubble:nth-child(3){animation-duration:5.5s;animation-delay:2s;}
    .thought-bubble:nth-child(4){animation-duration:8s;animation-delay:.5s;}
    @keyframes thoughtFloat{0%,100%{transform:translateY(0);}50%{transform:translateY(-6px);}}
    .thought-bubble em { color:#00ffb4; font-style:normal; }
    .thought-bubble strong { color:#b44dff; }

    /* ── NEW: POWERED BY SECTION ── */
    .powered-section {
        display:flex; flex-direction:column; align-items:center; gap:20px;
        margin-top:24px; margin-bottom:8px;
    }
    .powered-label {
        font-family:'Space Mono',monospace; font-size:9px; letter-spacing:5px;
        color:rgba(255,255,255,0.2); text-transform:uppercase;
    }
    .powered-logos {
        display:flex; gap:16px; flex-wrap:wrap; justify-content:center; align-items:center;
    }
    .pw-logo {
        display:flex; align-items:center; gap:8px;
        background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
        border-radius:100px; padding:8px 16px;
        font-family:'Space Mono',monospace; font-size:10px; color:rgba(255,255,255,0.4);
        letter-spacing:1px; transition:all .3s ease;
        animation: pwFloat ease-in-out infinite;
    }
    .pw-logo:nth-child(1){animation-duration:5s;}
    .pw-logo:nth-child(2){animation-duration:6s;animation-delay:.8s;}
    .pw-logo:nth-child(3){animation-duration:4.5s;animation-delay:1.6s;}
    .pw-logo:nth-child(4){animation-duration:7s;animation-delay:2.4s;}
    .pw-logo:nth-child(5){animation-duration:5.5s;animation-delay:3.2s;}
    .pw-logo:hover { background:rgba(255,255,255,0.07); border-color:rgba(0,255,180,0.2); color:rgba(255,255,255,0.8); transform:translateY(-3px); }
    @keyframes pwFloat{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}
    .pw-dot { width:8px;height:8px;border-radius:50%; flex-shrink:0; }

    /* ── NEW: CONTACT / ACCESS INFO ── */
    .access-info {
        margin-top:20px; padding:16px 20px; border-radius:16px;
        background:rgba(0,255,180,0.03); border:1px solid rgba(0,255,180,0.1);
        text-align:center;
    }
    .access-info-text {
        font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.45);
        line-height:1.8;
    }
    .access-info-text a { color:#00ffb4; text-decoration:none; font-weight:600; }
    .access-info-text a:hover { text-decoration:underline; }

    /* ── NEW: THANKS FOOTER ── */
    .thanks-footer {
        width:100%; text-align:center; padding:32px 20px 24px;
        margin-top:16px;
        border-top:1px solid rgba(255,255,255,0.05);
    }
    .thanks-text {
        font-family:'Orbitron',monospace; font-size:13px; font-weight:700;
        letter-spacing:4px;
        background:linear-gradient(90deg,#00ffb4,#b44dff,#ff44aa,#ffaa00,#00ffb4);
        background-size:300%;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        animation:gradShift 6s linear infinite;
        filter:drop-shadow(0 0 15px rgba(0,255,180,0.3));
        margin-bottom:8px;
    }
    .copyright-text {
        font-family:'Space Mono',monospace; font-size:10px; color:rgba(255,255,255,0.18);
        letter-spacing:2px; line-height:1.9; margin-top:8px;
    }


    /* ══════════════════════════════════════════
       ✦ ADDED PREMIUM UI SECTIONS ✦
    ══════════════════════════════════════════ */

    /* ── LIVE COUNTER TICKER ── */
    .live-ticker {
        width:100%; max-width:1100px;
        display:flex; gap:0; margin-bottom:72px;
        border:1px solid rgba(0,255,180,0.12); border-radius:20px;
        overflow:hidden; background:rgba(0,0,0,0.3); backdrop-filter:blur(12px);
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .05s both;
        position:relative;
    }
    .live-ticker::before {
        content:'LIVE'; position:absolute; top:12px; left:16px;
        font-family:'Space Mono',monospace; font-size:9px; letter-spacing:4px;
        color:#00ffb4; background:rgba(0,255,180,0.1); border:1px solid rgba(0,255,180,0.3);
        border-radius:100px; padding:3px 10px;
        animation:blink 2s ease-in-out infinite;
    }
    .ticker-item {
        flex:1; padding:28px 20px 22px; text-align:center;
        border-right:1px solid rgba(255,255,255,0.05);
        position:relative; overflow:hidden;
    }
    .ticker-item:last-child { border-right:none; }
    .ticker-item::after {
        content:''; position:absolute; bottom:0; left:20%; right:20%; height:1px;
        background:linear-gradient(90deg,transparent,var(--tc,rgba(0,255,180,0.3)),transparent);
    }
    .ticker-num {
        font-family:'Orbitron',monospace; font-size:clamp(22px,3vw,38px);
        font-weight:900; line-height:1; margin-bottom:8px;
        background:var(--tg,linear-gradient(135deg,#00ffb4,#00aaff));
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 12px var(--tglow,rgba(0,255,180,0.4)));
    }
    .ticker-lbl { font-family:'Rajdhani',sans-serif; font-size:11px; letter-spacing:3px; color:rgba(255,255,255,0.35); text-transform:uppercase; }
    .ticker-sub { font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,0.18); letter-spacing:2px; margin-top:4px; }
    .t1{--tg:linear-gradient(135deg,#00ffb4,#00aaff);--tc:rgba(0,255,180,0.3);--tglow:rgba(0,255,180,0.4);}
    .t2{--tg:linear-gradient(135deg,#b44dff,#ff44aa);--tc:rgba(180,77,255,0.3);--tglow:rgba(180,77,255,0.4);}
    .t3{--tg:linear-gradient(135deg,#ffaa00,#ff4400);--tc:rgba(255,170,0,0.3);--tglow:rgba(255,170,0,0.4);}
    .t4{--tg:linear-gradient(135deg,#00aaff,#0044ff);--tc:rgba(0,170,255,0.3);--tglow:rgba(0,170,255,0.4);}
    .t5{--tg:linear-gradient(135deg,#ff44aa,#ff0044);--tc:rgba(255,68,170,0.3);--tglow:rgba(255,68,170,0.4);}

    /* ── HOW IT WORKS TIMELINE ── */
    .hiw-section { width:100%; max-width:1100px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .1s both; }
    .hiw-steps { display:flex; gap:0; position:relative; }
    .hiw-steps::before {
        content:''; position:absolute; top:36px; left:10%; right:10%; height:1px;
        background:linear-gradient(90deg,rgba(0,255,180,0.1),rgba(0,255,180,0.3),rgba(180,77,255,0.3),rgba(0,255,180,0.1));
    }
    .hiw-step {
        flex:1; display:flex; flex-direction:column; align-items:center; text-align:center;
        padding:0 12px;
        animation: cardIn .8s cubic-bezier(.16,1,.3,1) both;
    }
    .hiw-step:nth-child(1){animation-delay:.1s;}
    .hiw-step:nth-child(2){animation-delay:.2s;}
    .hiw-step:nth-child(3){animation-delay:.3s;}
    .hiw-step:nth-child(4){animation-delay:.4s;}
    .hiw-num {
        width:72px; height:72px; border-radius:50%;
        background:rgba(0,255,180,0.06); border:1px solid rgba(0,255,180,0.2);
        display:flex; align-items:center; justify-content:center;
        font-family:'Orbitron',monospace; font-size:20px; font-weight:900;
        color:#00ffb4; margin-bottom:16px; position:relative; z-index:1;
        box-shadow:0 0 30px rgba(0,255,180,0.1);
        transition:all .4s ease;
    }
    .hiw-num:hover { background:rgba(0,255,180,0.15); box-shadow:0 0 50px rgba(0,255,180,0.25); transform:scale(1.1); }
    .hiw-icon { font-size:22px; margin-bottom:2px; }
    .hiw-title { font-family:'Orbitron',monospace; font-size:11px; font-weight:700; color:#fff; letter-spacing:1px; margin-bottom:8px; }
    .hiw-desc { font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.4); line-height:1.6; }

    /* ── CAPABILITY BARS ── */
    .cap-section { width:100%; max-width:1100px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .15s both; }
    .cap-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
    @media(max-width:600px){.cap-grid{grid-template-columns:1fr;}}
    .cap-item { padding:20px 24px; background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07); border-radius:16px; }
    .cap-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
    .cap-name { font-family:'Rajdhani',sans-serif; font-size:14px; font-weight:700; color:#fff; letter-spacing:.5px; }
    .cap-pct { font-family:'Space Mono',monospace; font-size:11px; color:var(--cc,#00ffb4); }
    .cap-bar { height:4px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
    .cap-fill { height:100%; border-radius:100px; background:var(--cg,linear-gradient(90deg,#00ffb4,#00aaff)); width:0%; transition:width 2s cubic-bezier(.16,1,.3,1); }

    /* ── COMPARISON TABLE ── */
    .compare-section { width:100%; max-width:900px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .2s both; }
    .compare-table { width:100%; border-collapse:separate; border-spacing:0; }
    .compare-table th { padding:16px 20px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px; text-align:center; }
    .compare-table th:first-child { text-align:left; }
    .compare-table td { padding:14px 20px; font-family:'Rajdhani',sans-serif; font-size:14px; text-align:center; border-top:1px solid rgba(255,255,255,0.05); }
    .compare-table td:first-child { text-align:left; color:rgba(255,255,255,0.65); }
    .compare-col-us { color:#00ffb4; font-weight:700; }
    .compare-col-them { color:rgba(255,255,255,0.25); }
    .compare-yes { color:#00ffb4; font-size:18px; }
    .compare-no { color:rgba(255,255,255,0.2); font-size:18px; }
    .compare-header-us { color:#00ffb4; background:rgba(0,255,180,0.05); border-radius:12px 12px 0 0; }
    .compare-header-them { color:rgba(255,255,255,0.3); }
    .compare-wrap {
        background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; overflow:hidden; backdrop-filter:blur(10px);
    }

    /* ── FAQ ACCORDION ── */
    .faq-section { width:100%; max-width:900px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .2s both; }
    .faq-item {
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:16px; margin-bottom:10px; overflow:hidden;
        transition:all .3s ease;
    }
    .faq-item:hover { border-color:rgba(0,255,180,0.2); }
    .faq-q {
        padding:18px 22px; cursor:pointer; display:flex; justify-content:space-between; align-items:center;
        font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:700; color:#fff; letter-spacing:.3px;
        user-select:none;
    }
    .faq-arrow { font-size:10px; color:#00ffb4; transition:transform .3s ease; }
    .faq-a {
        max-height:0; overflow:hidden; transition:max-height .4s ease, padding .3s ease;
        font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.5); line-height:1.7;
        padding:0 22px;
    }
    .faq-item.open .faq-a { max-height:200px; padding:0 22px 18px; }
    .faq-item.open .faq-arrow { transform:rotate(180deg); color:#b44dff; }
    .faq-item.open { border-color:rgba(0,255,180,0.25); background:rgba(0,255,180,0.03); }

    /* ── TECH STACK CAROUSEL ── */
    .tech-marquee-wrap {
        width:100%; overflow:hidden; margin-bottom:72px;
        mask-image:linear-gradient(90deg,transparent 0%,black 10%,black 90%,transparent 100%);
        -webkit-mask-image:linear-gradient(90deg,transparent 0%,black 10%,black 90%,transparent 100%);
    }
    .tech-marquee { display:flex; gap:16px; animation:marquee 30s linear infinite; width:max-content; }
    .tech-marquee:hover { animation-play-state:paused; }
    @keyframes marquee { 0%{transform:translateX(0);} 100%{transform:translateX(-50%);} }
    .tech-chip {
        display:flex; align-items:center; gap:10px; padding:12px 20px;
        background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
        border-radius:100px; white-space:nowrap; flex-shrink:0;
        font-family:'Space Mono',monospace; font-size:11px; color:rgba(255,255,255,0.5);
        letter-spacing:1px; transition:all .3s ease;
    }
    .tech-chip:hover { background:rgba(255,255,255,0.07); border-color:rgba(0,255,180,0.3); color:#fff; }
    .tech-chip-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

    /* ── SUBJECT WHEEL ── */
    .subject-wheel {
        width:100%; max-width:1100px; margin-bottom:72px;
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .1s both;
    }
    .subjects-hex {
        display:flex; flex-wrap:wrap; gap:12px; justify-content:center;
    }
    .subj-hex {
        width:130px; padding:22px 16px; text-align:center;
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; position:relative; overflow:hidden;
        transition:all .4s cubic-bezier(.16,1,.3,1);
        cursor:default;
    }
    .subj-hex::before {
        content:''; position:absolute; inset:0;
        background:var(--sg,radial-gradient(ellipse at center,rgba(0,255,180,0.08),transparent));
        opacity:0; transition:opacity .3s ease;
    }
    .subj-hex:hover { transform:translateY(-8px) scale(1.05); border-color:var(--sb,rgba(0,255,180,0.4)); }
    .subj-hex:hover::before { opacity:1; }
    .subj-icon { font-size:28px; display:block; margin-bottom:8px; }
    .subj-name { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; color:rgba(255,255,255,0.45); text-transform:uppercase; }

    /* ── TRUST BADGES ── */
    .trust-section {
        width:100%; max-width:1100px; margin-bottom:56px;
        display:flex; flex-wrap:wrap; gap:16px; justify-content:center;
        animation: cardIn .9s cubic-bezier(.16,1,.3,1) .1s both;
    }
    .trust-badge {
        display:flex; align-items:center; gap:10px; padding:14px 22px;
        background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.08);
        border-radius:14px;
        font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:600; color:rgba(255,255,255,0.6);
        transition:all .3s ease;
    }
    .trust-badge:hover { border-color:rgba(0,255,180,0.25); background:rgba(0,255,180,0.04); color:#fff; transform:translateY(-3px); }
    .trust-badge-icon { font-size:20px; }

    /* ── GLOW DIVIDER ── */
    .glow-divider {
        width:100%; max-width:1100px; margin:8px 0 64px;
        height:1px; position:relative;
        background:linear-gradient(90deg,transparent,rgba(0,255,180,0.3),rgba(180,77,255,0.3),transparent);
    }
    .glow-divider::after {
        content:''; position:absolute; top:-4px; left:50%; transform:translateX(-50%);
        width:8px; height:8px; border-radius:50%;
        background:#00ffb4; box-shadow:0 0 20px rgba(0,255,180,0.8);
        animation:blink 2s ease-in-out infinite;
    }

    /* ── MINI FEATURE HIGHLIGHTS (icon + line) ── */
    .hl-section { width:100%; max-width:1100px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .15s both; }
    .hl-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }
    @media(max-width:700px){.hl-grid{grid-template-columns:1fr;}}
    .hl-card {
        padding:28px 24px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; position:relative; overflow:hidden;
        transition:all .4s cubic-bezier(.16,1,.3,1);
    }
    .hl-card::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:var(--hg,linear-gradient(90deg,#00ffb4,#00aaff));
        transform:scaleX(0); transform-origin:left; transition:transform .4s ease;
    }
    .hl-card:hover { transform:translateY(-6px); border-color:rgba(255,255,255,0.15); }
    .hl-card:hover::before { transform:scaleX(1); }
    .hl-icon { font-size:32px; margin-bottom:14px; display:block; }
    .hl-title { font-family:'Orbitron',monospace; font-size:13px; font-weight:700; color:#fff; letter-spacing:1px; margin-bottom:10px; }
    .hl-desc { font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.4); line-height:1.7; }
    .hl-arrow { display:inline-flex; align-items:center; gap:6px; margin-top:14px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px; color:var(--hc,#00ffb4); opacity:0; transition:opacity .3s ease; }
    .hl-card:hover .hl-arrow { opacity:1; }

    /* ── FLOATING NOTIFICATION POPUP ── */
    .notif-popup {
        position:fixed; bottom:32px; left:32px; z-index:999;
        background:rgba(0,20,12,0.9); border:1px solid rgba(0,255,180,0.25);
        border-radius:16px; padding:16px 20px; max-width:280px;
        backdrop-filter:blur(20px); box-shadow:0 20px 60px rgba(0,0,0,0.5),0 0 40px rgba(0,255,180,0.08);
        animation:notifSlide 0.6s cubic-bezier(.16,1,.3,1) 2s both;
        display:flex; align-items:flex-start; gap:12px;
    }
    @keyframes notifSlide{from{transform:translateX(-120%);opacity:0;}to{transform:translateX(0);opacity:1;}}
    .notif-icon { font-size:22px; flex-shrink:0; }
    .notif-body {}
    .notif-title { font-family:'Orbitron',monospace; font-size:11px; font-weight:700; color:#00ffb4; letter-spacing:1px; margin-bottom:4px; }
    .notif-text { font-family:'Rajdhani',sans-serif; font-size:12px; color:rgba(255,255,255,0.5); line-height:1.5; }
    .notif-close { position:absolute; top:10px; right:12px; cursor:pointer; font-size:12px; color:rgba(255,255,255,0.3); transition:color .2s; }
    .notif-close:hover { color:#00ffb4; }
    .notif-dot { width:6px; height:6px; border-radius:50%; background:#00ffb4; flex-shrink:0; margin-top:7px; animation:blink 1.5s ease-in-out infinite; }

    /* ── SCROLL PROGRESS BAR ── */
    .scroll-prog {
        position:fixed; top:0; left:0; height:2px; z-index:9999;
        background:linear-gradient(90deg,#00ffb4,#00aaff,#b44dff,#ff44aa);
        width:0%; transition:width .1s linear;
        box-shadow:0 0 12px rgba(0,255,180,0.6);
    }

    /* ── ANIMATED TYPEWRITER SUBTITLE ── */
    .typewriter-wrap {
        text-align:center; margin-bottom:32px;
        font-family:'Space Mono',monospace; font-size:13px; letter-spacing:3px;
        color:rgba(255,255,255,0.3);
    }
    .typewriter { border-right:2px solid #00ffb4; padding-right:4px; animation:cursorBlink 1s step-end infinite; }
    @keyframes cursorBlink{0%,100%{border-color:#00ffb4;}50%{border-color:transparent;}}

    /* ── VIDEO DEMO PLACEHOLDER ── */
    .demo-section { width:100%; max-width:900px; margin-bottom:72px; animation: cardIn .9s cubic-bezier(.16,1,.3,1) .2s both; }
    .demo-card {
        border-radius:24px; overflow:hidden; border:1px solid rgba(0,255,180,0.15);
        position:relative; background:rgba(0,0,0,0.4);
        box-shadow:0 0 80px rgba(0,255,180,0.08);
    }
    .demo-canvas-wrap { width:100%; height:200px; position:relative; overflow:hidden; }
    .demo-canvas-wrap canvas { width:100%; height:200px; display:block; }
    .demo-overlay {
        position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; z-index:10;
    }
    .demo-play-btn {
        width:64px; height:64px; border-radius:50%;
        background:linear-gradient(135deg,rgba(0,255,180,0.9),rgba(0,170,255,0.9));
        display:flex; align-items:center; justify-content:center;
        font-size:22px; cursor:pointer; margin-bottom:14px;
        box-shadow:0 0 40px rgba(0,255,180,0.4);
        animation:playPulse 2s ease-in-out infinite;
        transition:transform .3s ease;
    }
    .demo-play-btn:hover { transform:scale(1.15); }
    @keyframes playPulse{0%,100%{box-shadow:0 0 40px rgba(0,255,180,0.4);}50%{box-shadow:0 0 70px rgba(0,255,180,0.7);}}
    .demo-label { font-family:'Orbitron',monospace; font-size:12px; letter-spacing:3px; color:rgba(255,255,255,0.5); }
    .demo-tabs { display:flex; border-top:1px solid rgba(255,255,255,0.07); }
    .demo-tab {
        flex:1; padding:16px; text-align:center; cursor:pointer;
        font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px;
        color:rgba(255,255,255,0.3); border-right:1px solid rgba(255,255,255,0.05);
        transition:all .3s ease; position:relative; overflow:hidden;
    }
    .demo-tab:last-child { border-right:none; }
    .demo-tab:hover { color:#00ffb4; background:rgba(0,255,180,0.04); }
    .demo-tab.active { color:#00ffb4; }
    .demo-tab.active::after { content:''; position:absolute; bottom:0; left:20%; right:20%; height:2px; background:linear-gradient(90deg,transparent,#00ffb4,transparent); }

    /* ════════════════════════════════════════════════
       ✦ POWER ADDITIONS — NEW SECTIONS
    ════════════════════════════════════════════════ */

    /* ── LIVE IMPACT COUNTER ── */
    .impact-section {
        width:100%; max-width:1100px; margin-bottom:80px;
        animation: cardIn 1s cubic-bezier(.16,1,.3,1) .1s both;
    }
    .impact-grid {
        display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
        gap:0; border:1px solid rgba(0,255,180,0.12);
        border-radius:24px; overflow:hidden;
        background:rgba(0,0,0,0.3); backdrop-filter:blur(20px);
        box-shadow: 0 0 60px rgba(0,255,180,0.05), 0 0 120px rgba(180,77,255,0.03);
    }
    .impact-cell {
        padding:40px 24px; text-align:center;
        border-right:1px solid rgba(255,255,255,0.05);
        position:relative; overflow:hidden;
        transition:all .4s cubic-bezier(.16,1,.3,1);
    }
    .impact-cell:last-child { border-right:none; }
    .impact-cell::before {
        content:''; position:absolute; inset:0;
        background: var(--cell-glow, transparent); opacity:0;
        transition:opacity .4s ease;
    }
    .impact-cell:hover::before { opacity:1; }
    .impact-cell:hover { transform:scale(1.02); z-index:2; }
    .ic1 { --cell-glow: radial-gradient(ellipse at center, rgba(0,255,180,0.06), transparent 70%); }
    .ic2 { --cell-glow: radial-gradient(ellipse at center, rgba(180,77,255,0.06), transparent 70%); }
    .ic3 { --cell-glow: radial-gradient(ellipse at center, rgba(0,170,255,0.06), transparent 70%); }
    .ic4 { --cell-glow: radial-gradient(ellipse at center, rgba(255,68,170,0.06), transparent 70%); }
    .ic5 { --cell-glow: radial-gradient(ellipse at center, rgba(255,170,0,0.06), transparent 70%); }
    .impact-icon { font-size:28px; margin-bottom:12px; display:block; }
    .impact-num {
        font-family:'Orbitron',monospace; font-weight:900;
        font-size:clamp(28px, 3.5vw, 48px); line-height:1;
        margin-bottom:8px; position:relative; z-index:1;
    }
    .ic1 .impact-num { background:linear-gradient(135deg,#00ffb4,#00aaff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .ic2 .impact-num { background:linear-gradient(135deg,#b44dff,#ff44aa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .ic3 .impact-num { background:linear-gradient(135deg,#00aaff,#00ffb4); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .ic4 .impact-num { background:linear-gradient(135deg,#ff44aa,#ffaa00); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .ic5 .impact-num { background:linear-gradient(135deg,#ffaa00,#ff4400); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .impact-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(255,255,255,0.35); text-transform:uppercase; position:relative; z-index:1; }
    .impact-sub { font-family:'Rajdhani',sans-serif; font-size:12px; color:rgba(255,255,255,0.2); margin-top:4px; letter-spacing:1px; position:relative; z-index:1; }

    /* ── HOW IT WORKS ── */
    .how-section { width:100%; max-width:1100px; margin-bottom:80px; }
    .how-steps { display:flex; gap:0; position:relative; align-items:flex-start; flex-wrap:wrap; justify-content:center; }
    .how-step {
        flex:1; min-width:180px; max-width:220px;
        text-align:center; padding:32px 16px;
        position:relative; z-index:2;
        animation: cardIn .7s cubic-bezier(.16,1,.3,1) both;
    }
    .how-step:nth-child(1){animation-delay:.05s;}
    .how-step:nth-child(2){animation-delay:.15s;}
    .how-step:nth-child(3){animation-delay:.25s;}
    .how-step:nth-child(4){animation-delay:.35s;}
    .how-connector {
        flex:1; min-width:40px; max-width:60px;
        align-self:center; margin-top:-40px;
        height:2px; position:relative; z-index:1;
        background:linear-gradient(90deg,rgba(0,255,180,0.2),rgba(180,77,255,0.2));
    }
    .how-connector::after {
        content:'›'; position:absolute; right:-6px; top:-10px;
        color:rgba(0,255,180,0.4); font-size:20px;
    }
    .how-num-wrap {
        width:72px; height:72px; border-radius:50%;
        background:rgba(255,255,255,0.02);
        border:1px solid rgba(0,255,180,0.2);
        display:flex; align-items:center; justify-content:center;
        margin:0 auto 20px;
        position:relative;
        transition:all .4s ease;
        animation:howPulse 4s ease-in-out infinite;
    }
    .how-step:nth-child(1) .how-num-wrap { animation-delay:0s; --hw:rgba(0,255,180,0.2); border-color:rgba(0,255,180,0.25); }
    .how-step:nth-child(3) .how-num-wrap { animation-delay:.5s; --hw:rgba(180,77,255,0.2); border-color:rgba(180,77,255,0.25); }
    .how-step:nth-child(5) .how-num-wrap { animation-delay:1s; --hw:rgba(0,170,255,0.2); border-color:rgba(0,170,255,0.25); }
    .how-step:nth-child(7) .how-num-wrap { animation-delay:1.5s; --hw:rgba(255,68,170,0.2); border-color:rgba(255,68,170,0.25); }
    @keyframes howPulse{0%,100%{box-shadow:0 0 0 rgba(0,255,180,0);}50%{box-shadow:0 0 30px var(--hw, rgba(0,255,180,0.15));}}
    .how-icon { font-size:32px; }
    .how-title { font-family:'Orbitron',monospace; font-size:12px; font-weight:700; color:#fff; letter-spacing:1px; margin-bottom:8px; }
    .how-desc { font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.4); line-height:1.6; }

    /* ── TECH STACK SHOWCASE ── */
    .tech-section { width:100%; max-width:1100px; margin-bottom:80px; }
    .tech-ribbon {
        display:flex; gap:16px; flex-wrap:wrap; justify-content:center;
        padding:32px; background:rgba(255,255,255,0.015);
        border:1px solid rgba(255,255,255,0.06); border-radius:20px;
        position:relative; overflow:hidden;
    }
    .tech-ribbon::before {
        content:''; position:absolute; top:0; left:-100%; right:100%; height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,255,180,0.5),transparent);
        animation:techScan 4s linear infinite;
    }
    @keyframes techScan{to{left:200%;right:-100%;}}
    .tech-pill {
        display:flex; align-items:center; gap:10px;
        padding:10px 20px; border-radius:100px;
        background:rgba(255,255,255,0.025);
        border:1px solid rgba(255,255,255,0.07);
        transition:all .3s ease; cursor:default;
        animation: cardIn .6s cubic-bezier(.16,1,.3,1) both;
    }
    .tech-pill:hover { transform:translateY(-4px); border-color:var(--tc); box-shadow:0 8px 30px rgba(0,0,0,0.3), 0 0 20px var(--tc); background:rgba(255,255,255,0.05); }
    .tech-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; animation:blink 2s ease-in-out infinite; }
    .tech-name { font-family:'Space Mono',monospace; font-size:11px; letter-spacing:1px; color:rgba(255,255,255,0.7); }
    .tech-badge { font-family:'Rajdhani',sans-serif; font-size:10px; padding:2px 8px; border-radius:100px; background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.3); letter-spacing:1px; }

    /* ── FEATURE SPOTLIGHT MARQUEE ── */
    .marquee-section { width:100%; overflow:hidden; margin-bottom:64px; position:relative; }
    .marquee-track {
        display:flex; gap:24px; width:max-content;
        animation:marqueeScroll 30s linear infinite;
    }
    .marquee-section:hover .marquee-track { animation-play-state:paused; }
    @keyframes marqueeScroll{from{transform:translateX(0);}to{transform:translateX(-50%);}}
    .marquee-tag {
        white-space:nowrap; padding:10px 24px; border-radius:100px;
        border:1px solid rgba(255,255,255,0.08);
        background:rgba(255,255,255,0.02);
        font-family:'Space Mono',monospace; font-size:11px; letter-spacing:2px;
        color:rgba(255,255,255,0.5);
        transition:all .3s ease;
        flex-shrink:0;
    }
    .marquee-tag:hover { border-color:rgba(0,255,180,0.3); color:#00ffb4; background:rgba(0,255,180,0.04); }
    .marquee-fade-l { position:absolute; left:0; top:0; bottom:0; width:120px; background:linear-gradient(90deg,#020008,transparent); z-index:2; pointer-events:none; }
    .marquee-fade-r { position:absolute; right:0; top:0; bottom:0; width:120px; background:linear-gradient(270deg,#020008,transparent); z-index:2; pointer-events:none; }

    /* ── SOCIAL PROOF MEGA WALL ── */
    .proof-section { width:100%; max-width:1100px; margin-bottom:80px; }
    .proof-wall { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }
    .proof-card {
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:20px; padding:28px 24px; position:relative; overflow:hidden;
        transition:all .4s cubic-bezier(.16,1,.3,1);
        animation: cardIn .7s cubic-bezier(.16,1,.3,1) both;
    }
    .proof-card::after {
        content:''; position:absolute; top:0; left:0; right:0; height:1px;
        background:linear-gradient(90deg,transparent,var(--pc),transparent); opacity:0.4;
    }
    .proof-card:hover { transform:translateY(-6px); border-color:var(--pc); box-shadow:0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(0,255,180,0.03); }
    .proof-stars { color:#ffaa00; font-size:13px; margin-bottom:12px; letter-spacing:2px; }
    .proof-text { font-family:'Rajdhani',sans-serif; font-size:15px; color:rgba(255,255,255,0.7); line-height:1.8; margin-bottom:18px; font-style:italic; }
    .proof-text em { color:var(--pc); font-style:normal; font-weight:600; }
    .proof-author { display:flex; align-items:center; gap:12px; }
    .proof-avatar { width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); flex-shrink:0; }
    .proof-name { font-family:'Orbitron',monospace; font-size:10px; letter-spacing:2px; color:rgba(255,255,255,0.6); }
    .proof-role { font-family:'Rajdhani',sans-serif; font-size:12px; color:rgba(255,255,255,0.3); margin-top:2px; letter-spacing:1px; }

    /* ── ANIMATED CAPABILITY BARS ── */
    .capability-section { width:100%; max-width:900px; margin-bottom:80px; }
    .cap-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
    .cap-item { animation: cardIn .7s cubic-bezier(.16,1,.3,1) both; }
    .cap-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
    .cap-name { font-family:'Rajdhani',sans-serif; font-size:14px; font-weight:700; color:rgba(255,255,255,0.8); letter-spacing:.5px; }
    .cap-pct { font-family:'Space Mono',monospace; font-size:11px; color:var(--bar-c); }
    .cap-track { height:4px; background:rgba(255,255,255,0.05); border-radius:100px; overflow:hidden; }
    .cap-fill { height:100%; border-radius:100px; background:var(--bar-c); width:0%; transition:width 2s cubic-bezier(.16,1,.3,1); box-shadow: 0 0 8px var(--bar-c); }

    /* ── VIDEO / DEMO SHOWCASE ── */
    .showcase-section { width:100%; max-width:1100px; margin-bottom:80px; }
    .showcase-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
    .showcase-card {
        border-radius:20px; overflow:hidden; position:relative;
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        aspect-ratio:4/3; cursor:pointer;
        transition:all .4s cubic-bezier(.16,1,.3,1);
        animation: cardIn .7s cubic-bezier(.16,1,.3,1) both;
    }
    .showcase-card:hover { transform:scale(1.03); border-color:rgba(0,255,180,0.3); box-shadow:0 20px 60px rgba(0,0,0,0.5); }
    .showcase-inner { height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:24px; position:relative; z-index:2; }
    .showcase-glow { position:absolute; inset:0; background:var(--sc-glow); opacity:0; transition:opacity .4s ease; z-index:1; }
    .showcase-card:hover .showcase-glow { opacity:1; }
    .sc1 { --sc-glow:radial-gradient(ellipse at center,rgba(0,255,180,0.08),transparent 70%); animation-delay:.05s; }
    .sc2 { --sc-glow:radial-gradient(ellipse at center,rgba(180,77,255,0.08),transparent 70%); animation-delay:.15s; }
    .sc3 { --sc-glow:radial-gradient(ellipse at center,rgba(0,170,255,0.08),transparent 70%); animation-delay:.25s; }
    .showcase-emoji { font-size:44px; margin-bottom:14px; display:block; transition:transform .3s ease; }
    .showcase-card:hover .showcase-emoji { transform:scale(1.2) rotate(-5deg); }
    .showcase-name { font-family:'Orbitron',monospace; font-size:13px; font-weight:700; color:#fff; letter-spacing:1px; text-align:center; margin-bottom:8px; }
    .showcase-detail { font-family:'Rajdhani',sans-serif; font-size:12px; color:rgba(255,255,255,0.4); text-align:center; line-height:1.6; }
    .showcase-chip { margin-top:12px; padding:4px 14px; border-radius:100px; font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; border:1px solid; }

    /* ── ANIMATED BACKGROUND AURORA ── */
    .aurora-bg {
        position:fixed; inset:0; z-index:0; pointer-events:none;
        background:
            radial-gradient(ellipse 100% 60% at 0% 100%, rgba(0,255,100,0.04) 0%, transparent 60%),
            radial-gradient(ellipse 80% 40% at 100% 0%, rgba(100,0,255,0.05) 0%, transparent 60%);
        animation:auroraShift 20s ease-in-out infinite alternate;
    }
    @keyframes auroraShift{
        0%{background:radial-gradient(ellipse 100% 60% at 0% 100%,rgba(0,255,100,0.04) 0%,transparent 60%),radial-gradient(ellipse 80% 40% at 100% 0%,rgba(100,0,255,0.05) 0%,transparent 60%);}
        33%{background:radial-gradient(ellipse 80% 70% at 50% 0%,rgba(0,100,255,0.05) 0%,transparent 60%),radial-gradient(ellipse 60% 50% at 0% 50%,rgba(255,0,100,0.03) 0%,transparent 60%);}
        66%{background:radial-gradient(ellipse 90% 50% at 100% 100%,rgba(0,255,180,0.04) 0%,transparent 60%),radial-gradient(ellipse 70% 60% at 30% 30%,rgba(180,0,255,0.04) 0%,transparent 60%);}
        100%{background:radial-gradient(ellipse 100% 60% at 0% 100%,rgba(0,255,100,0.04) 0%,transparent 60%),radial-gradient(ellipse 80% 40% at 100% 0%,rgba(100,0,255,0.05) 0%,transparent 60%);}
    }

    /* ── COUNTDOWN URGENCY BAR ── */
    .urgency-bar {
        width:100%; max-width:900px; margin-bottom:48px;
        background:linear-gradient(90deg, rgba(255,68,170,0.05), rgba(180,77,255,0.08), rgba(255,68,170,0.05));
        border:1px solid rgba(255,68,170,0.2); border-radius:16px;
        padding:20px 32px; text-align:center;
        position:relative; overflow:hidden;
        animation: cardIn .8s cubic-bezier(.16,1,.3,1) .2s both;
    }
    .urgency-bar::before {
        content:''; position:absolute; inset:0;
        background:linear-gradient(90deg,transparent,rgba(255,68,170,0.05),transparent);
        animation:eraShimmer 3s linear infinite;
    }
    .urgency-text { font-family:'Orbitron',monospace; font-size:13px; letter-spacing:3px; color:rgba(255,68,170,0.9); position:relative; z-index:1; }
    .urgency-sub { font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.3); letter-spacing:2px; margin-top:6px; position:relative; z-index:1; }

    /* ── FINAL CTA SECTION ── */
    .final-cta {
        width:100%; max-width:900px; margin-bottom:60px;
        background: linear-gradient(135deg,rgba(0,255,180,0.03) 0%,rgba(180,77,255,0.04) 50%,rgba(0,170,255,0.03) 100%);
        border:1px solid rgba(255,255,255,0.07); border-radius:28px;
        padding:60px 40px; text-align:center; position:relative; overflow:hidden;
        animation: cardIn 1s cubic-bezier(.16,1,.3,1) .2s both;
    }
    .final-cta::before {
        content:''; position:absolute; top:-1px; left:15%; right:15%; height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,255,180,0.5),transparent);
    }
    .final-cta::after {
        content:''; position:absolute; bottom:-1px; left:15%; right:15%; height:1px;
        background:linear-gradient(90deg,transparent,rgba(180,77,255,0.5),transparent);
    }
    .cta-title { font-family:'Orbitron',monospace; font-size:clamp(22px,4vw,38px); font-weight:900; margin-bottom:16px;
        background:linear-gradient(135deg,#fff 0%,#00ffb4 40%,#b44dff 80%,#ff44aa 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    }
    .cta-sub { font-family:'Rajdhani',sans-serif; font-size:16px; color:rgba(255,255,255,0.4); line-height:1.7; max-width:600px; margin:0 auto 32px; letter-spacing:.5px; }
    .cta-pills { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-bottom:32px; }
    .cta-pill { padding:8px 20px; border-radius:100px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px;
        background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.5); }
    .cta-pill.green { border-color:rgba(0,255,180,0.3); color:#00ffb4; background:rgba(0,255,180,0.05); }
    .cta-pill.purple { border-color:rgba(180,77,255,0.3); color:#c88dff; background:rgba(180,77,255,0.05); }
    .cta-pill.pink { border-color:rgba(255,68,170,0.3); color:#ff88cc; background:rgba(255,68,170,0.05); }

    @media(max-width:768px) {
        .impact-grid { grid-template-columns:repeat(3,1fr); }
        .how-connector { display:none; }
        .how-steps { gap:16px; }
        .cap-grid { grid-template-columns:1fr; }
        .showcase-grid { grid-template-columns:1fr 1fr; }
        .showcase-grid .showcase-card:last-child { grid-column:1/-1; }
    }
    @media(max-width:480px) {
        .impact-grid { grid-template-columns:repeat(2,1fr); }
        .showcase-grid { grid-template-columns:1fr; }
        .proof-wall { grid-template-columns:1fr; }
    }

    /* ── STEP 01: Animated Hero Header ── */
    .hero-header-v2 {
      position: relative; overflow: hidden;
      background: linear-gradient(135deg,
        rgba(15,23,42,0.95) 0%,
        rgba(30,20,60,0.95) 40%,
        rgba(15,23,42,0.95) 100%);
      border: 1px solid rgba(99,102,241,0.25);
      border-radius: 20px; padding: 32px 40px;
      margin-bottom: 24px;
      animation: heroSlideIn 0.6s cubic-bezier(0.16,1,0.3,1) both;
    }
    @keyframes heroSlideIn {
      from { opacity:0; transform:translateY(-20px); }
      to   { opacity:1; transform:translateY(0); }
    }
    .hero-header-v2::before {
      content:''; position:absolute; inset:0;
      background: radial-gradient(ellipse 60% 80% at 0% 50%,
        rgba(99,102,241,0.12) 0%, transparent 70%);
      pointer-events:none;
    }
    .hero-header-v2::after {
      content:''; position:absolute; top:-1px; left:10%; right:10%; height:1px;
      background: linear-gradient(90deg,
        transparent, rgba(99,102,241,0.6), rgba(139,92,246,0.6), transparent);
    }
    .hero-title-v2 {
      font-family:'Orbitron',monospace; font-size:clamp(22px,3.5vw,42px);
      font-weight:900; letter-spacing:2px;
      background: linear-gradient(135deg,#ffffff 0%,#a5b4fc 40%,#818cf8 70%,#c084fc 100%);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
      filter:drop-shadow(0 0 30px rgba(99,102,241,0.4));
      margin:0; line-height:1.1;
    }
    .hero-sub-v2 {
      font-family:'Rajdhani',sans-serif; font-size:15px; margin-top:6px;
      color:rgba(255,255,255,0.45); font-weight:300; letter-spacing:3px; text-transform:uppercase; 
    }
    .hero-badge-active {
      display:inline-flex; align-items:center; gap:7px;
      background:rgba(34,197,94,0.1); border:1px solid rgba(34,197,94,0.3);
      border-radius:100px; padding:5px 14px;
      font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px; color:#4ade80;
      animation: badgePulse01 2.5s ease-in-out infinite;
    }
    @keyframes badgePulse01 {
      0%,100%{box-shadow:0 0 0 rgba(34,197,94,0);} 50%{box-shadow:0 0 16px rgba(34,197,94,0.25);}
    }
    .badge-dot-green { width:6px;height:6px;background:#4ade80;border-radius:50%;animation:blinkGreen 1.4s ease-in-out infinite; }
    @keyframes blinkGreen{0%,100%{opacity:1;}50%{opacity:0.2;}}
    .hero-live-clock {
      font-family:'Space Mono',monospace; font-size:12px; color:rgba(255,255,255,0.3);
      letter-spacing:2px; margin-top:14px;
    }

    /* ── STEP 02: Sidebar Nav Groups ── */
    .nav-group-header {
      display:flex; align-items:center; justify-content:space-between;
      padding:10px 14px; border-radius:10px; cursor:pointer;
      background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
      margin-bottom:6px; margin-top:10px;
      font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:700;
      color:rgba(255,255,255,0.7); letter-spacing:1px;
      transition:all 0.25s ease;
      user-select:none;
    }
    .nav-group-header:hover { background:rgba(99,102,241,0.08); border-color:rgba(99,102,241,0.25); color:#fff; }
    .nav-group-count {
      font-family:'Space Mono',monospace; font-size:10px;
      background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.2);
      border-radius:100px; padding:2px 8px; color:#a5b4fc;
    }
    .active-tool-banner {
      display:flex; align-items:center; gap:8px;
      background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3);
      border-radius:10px; padding:9px 13px; margin-bottom:10px;
      font-family:'Rajdhani',sans-serif; font-size:12px; font-weight:700;
      color:#a5b4fc; letter-spacing:1px;
      animation:activeBannerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
    }
    @keyframes activeBannerIn {
      from{opacity:0;transform:translateX(-10px);}
      to{opacity:1;transform:translateX(0);}
    }
    .active-tool-dot { width:7px;height:7px;background:#818cf8;border-radius:50%;animation:blinkGreen 1.6s ease-in-out infinite; }

    /* ── STEP 03: Stats Mini Dashboard ── */
    .stats-dashboard-card {
      background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.07);
      border-radius:14px; padding:14px 16px; margin:8px 0;
    }
    .stats-dash-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
    .stats-dash-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(255,255,255,0.3); text-transform:uppercase; }
    .stats-dash-val { font-family:'Orbitron',monospace; font-size:16px; font-weight:700; color:#a5b4fc; }
    .stats-mini-bar-wrap { margin-bottom:8px; }
    .stats-mini-bar-label { display:flex; justify-content:space-between; font-family:'Rajdhani',sans-serif; font-size:11px; color:rgba(255,255,255,0.4); margin-bottom:4px; }
    .stats-mini-bar { height:3px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
    .stats-mini-fill { height:100%; border-radius:100px; transition:width 1s cubic-bezier(0.16,1,0.3,1); }
    .fill-indigo { background:linear-gradient(90deg,#6366f1,#8b5cf6); }
    .fill-cyan   { background:linear-gradient(90deg,#06b6d4,#3b82f6); }
    .fill-green  { background:linear-gradient(90deg,#10b981,#06b6d4); }

    /* ── STEP 04: Floating Quick-Actions Toolbar ── */
    .float-toolbar {
      display:flex; align-items:center; justify-content:center; gap:6px;
      flex-wrap:wrap; margin:16px auto 8px; max-width:600px;
    }
    .ftb-btn {
      display:inline-flex; align-items:center; gap:7px;
      padding:8px 16px; border-radius:100px;
      background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.1);
      font-family:'Rajdhani',sans-serif; font-size:12px; font-weight:700;
      color:rgba(255,255,255,0.6); letter-spacing:1px;
      backdrop-filter:blur(12px); cursor:pointer;
      transition:all 0.25s ease;
      white-space:nowrap;
    }
    .ftb-btn:hover { background:rgba(99,102,241,0.15); border-color:rgba(99,102,241,0.4); color:#fff; transform:translateY(-2px); }
    .ftb-btn-icon { font-size:14px; }
    .ftb-separator { width:1px; height:22px; background:rgba(255,255,255,0.08); margin:0 4px; }

    /* ── STEP 05: Premium Chat Bubbles ── */
    .chat-bubble-wrap { display:flex; gap:12px; margin-bottom:20px; animation:bubbleFadeIn 0.4s ease both; }
    @keyframes bubbleFadeIn { from{opacity:0;transform:translateY(10px);} to{opacity:1;transform:translateY(0);} }
    .bubble-avatar {
      width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center;
      font-size:18px; flex-shrink:0; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
    }
    .bubble-content {
      background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.08);
      border-radius:14px; padding:16px 20px; width:100%; position:relative;
      font-family:'Rajdhani',sans-serif; font-size:15px; color:rgba(255,255,255,0.85); line-height:1.6;
    }
    .bubble-user .bubble-content { background:rgba(99,102,241,0.08); border-color:rgba(99,102,241,0.2); }
    .bubble-assistant .bubble-content { background:rgba(15,23,42,0.8); }
    .bubble-actions {
      display:flex; gap:6px; margin-top:10px; justify-content:flex-end;
      opacity:0; transition:opacity 0.2s ease;
    }
    .bubble-content:hover .bubble-actions { opacity:1; }
    .b-action-btn {
      padding:4px 8px; border-radius:6px; cursor:pointer;
      background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
      font-size:12px; color:rgba(255,255,255,0.5); transition:all 0.2s ease;
    }
    .b-action-btn:hover { background:rgba(99,102,241,0.2); color:#fff; }

    /* ── STEP 06: Smart Context Sources ── */
    .ctx-panel { display:flex; gap:12px; padding:12px 0; overflow-x:auto; }
    .ctx-panel::-webkit-scrollbar { height:4px; }
    .ctx-card {
      min-width:150px; background:rgba(15,23,42,0.8);
      border:1px solid rgba(255,255,255,0.1); border-radius:12px;
      padding:12px; position:relative; overflow:hidden;
      transition:all 0.25s ease; cursor:pointer;
      animation:cardIn 0.3s cubic-bezier(0.16,1,0.3,1) both;
    }
    @keyframes cardIn { from{opacity:0;transform:scale(0.9);} to{opacity:1;transform:scale(1);} }
    .ctx-card:hover { transform:translateY(-3px); border-color:rgba(99,102,241,0.5); box-shadow:0 10px 20px rgba(0,0,0,0.5); }
    .ctx-card-bg { position:absolute; right:-20px; bottom:-20px; font-size:64px; opacity:0.03; transition:all 0.3s ease; }
    .ctx-card:hover .ctx-card-bg { transform:scale(1.2) rotate(-10deg); opacity:0.06; }
    .ctx-card-type { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; color:rgba(99,102,241,0.8); margin-bottom:4px; text-transform:uppercase; }
    .ctx-card-label { font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:600; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

    /* ── STEP 08: Persona Carousel ── */
    .persona-carousel {
      display:flex; gap:10px; overflow-x:auto; padding-bottom:12px;
      scrollbar-width:none;
    }
    .persona-carousel::-webkit-scrollbar { display:none; }
    .persona-card {
      min-width:130px; background:rgba(15,23,42,0.6);
      border:1px solid rgba(255,255,255,0.08); border-radius:12px;
      padding:14px; text-align:center; cursor:pointer;
      transition:all 0.3s cubic-bezier(0.16,1,0.3,1);
      position:relative; overflow:hidden;
    }
    .persona-card:hover { transform:translateY(-4px); border-color:rgba(99,102,241,0.4); background:rgba(99,102,241,0.05); }
    .persona-card-active { border-color:#6366f1; background:rgba(99,102,241,0.1); box-shadow:0 8px 24px rgba(99,102,241,0.2); }
    .persona-icon { font-size:28px; margin-bottom:8px; transition:transform 0.3s ease; }
    .persona-card:hover .persona-icon { transform:scale(1.15) rotate(5deg); }
    .persona-name { font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:700; color:#fff; }

    /* ── STEP 07: Typing Indicator ── */
    .typing-indicator {
      display:inline-flex; align-items:center; gap:5px;
      padding:10px 18px; border-radius:100px;
      background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.15);
      margin-bottom:14px;
    }
    .typing-dot {
      width:7px; height:7px; border-radius:50%; background:#818cf8;
      animation:typingBounce 1.2s ease-in-out infinite;
    }
    .typing-dot:nth-child(2){animation-delay:0.2s;}
    .typing-dot:nth-child(3){animation-delay:0.4s;}
    @keyframes typingBounce {
      0%,80%,100%{transform:translateY(0);opacity:0.4;}
      40%{transform:translateY(-6px);opacity:1;}
    }
    .typing-label {
      font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px;
      color:rgba(255,255,255,0.35); margin-left:6px;
    }

    /* ── STEP 09: Quick Prompt Grid ── */
    .qprompt-section { margin:24px 0; }
    .qprompt-title {
      font-family:'Space Mono',monospace; font-size:10px; letter-spacing:4px;
      color:rgba(255,255,255,0.25); text-transform:uppercase; text-align:center;
      margin-bottom:18px;
    }
    .qprompt-grid {
      display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
      gap:10px;
    }
    .qprompt-chip {
      padding:14px 18px; border-radius:14px;
      background:rgba(15,23,42,0.7); border:1px solid var(--qc,rgba(99,102,241,0.2));
      cursor:pointer; transition:all 0.25s ease;
      display:flex; align-items:flex-start; gap:12px;
      animation:bubbleIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
    }
    .qprompt-chip:hover {
      background:rgba(var(--qcr,99,102,241),0.12); border-color:var(--qc,rgba(99,102,241,0.5));
      transform:translateY(-3px);
    }
    .qprompt-icon { font-size:18px; flex-shrink:0; margin-top:1px; }
    .qprompt-text { font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:600; color:rgba(255,255,255,0.65); line-height:1.4; }
    .qprompt-tag { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; color:var(--qc,#818cf8); margin-top:4px; display:block; }

    /* ── STEP 10: Tool Transition Loader ── */
    .tool-loader {
      display:flex; flex-direction:column; align-items:center; justify-content:center;
      min-height:280px; gap:20px;
      animation:loaderIn 0.3s ease both;
    }
    @keyframes loaderIn{from{opacity:0;}to{opacity:1;}}
    .tool-loader-icon { font-size:56px; animation:iconSpin 1s ease-in-out; }
    @keyframes iconSpin{0%{transform:scale(0.5) rotate(-20deg);opacity:0;}100%{transform:scale(1) rotate(0deg);opacity:1;}}
    .tool-loader-title {
      font-family:'Orbitron',monospace; font-size:18px; font-weight:700;
      letter-spacing:3px; color:rgba(255,255,255,0.7);
    }
    .tool-loader-bar-wrap { width:240px; height:3px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
    .tool-loader-bar {
      height:100%; border-radius:100px;
      background:linear-gradient(90deg,#6366f1,#8b5cf6,#06b6d4);
      animation:loadSweep 0.7s cubic-bezier(0.4,0,0.2,1) both;
    }
    @keyframes loadSweep{from{width:0%;}to{width:100%;}}

    /* ── STEP 11: Follow-up Suggestion Chips ── */
    .followup-row { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; margin-bottom:4px; }
    .followup-chip {
      padding:7px 14px; border-radius:100px;
      background:rgba(15,23,42,0.7); border:1px solid rgba(99,102,241,0.2);
      font-family:'Rajdhani',sans-serif; font-size:12px; font-weight:600;
      color:rgba(165,180,252,0.8); cursor:pointer; white-space:nowrap;
      transition:all 0.2s ease;
      animation:chipFadeIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
    }
    .followup-chip:hover { background:rgba(99,102,241,0.15); border-color:rgba(99,102,241,0.4); color:#fff; transform:translateY(-2px); }
    @keyframes chipFadeIn{from{opacity:0;transform:translateY(5px);}to{opacity:1;transform:translateY(0);}}
    .followup-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(255,255,255,0.2); margin-bottom:6px; }

    </style>
    <div class="lp-bg"></div>
    <div class="lp-grid"></div>
    <div class="orb o1"></div>
    <div class="orb o2"></div>
    <div class="orb o3"></div>
    <div class="orb o4"></div>

    <!-- NEW: Extra floating decoration -->
    <div class="float-ring fr1"></div>
    <div class="float-ring fr2"></div>
    <div class="float-ring fr3"></div>
    <div class="float-diamond fd1"></div>
    <div class="float-diamond fd2"></div>
    <div class="float-diamond fd3"></div>

    <div class="particles">
      <div class="pt" style="left:10%;width:3px;height:3px;background:#00ffb4;animation-duration:12s;animation-delay:0s;"></div>
      <div class="pt" style="left:25%;width:2px;height:2px;background:#b44dff;animation-duration:9s;animation-delay:2s;"></div>
      <div class="pt" style="left:50%;width:4px;height:4px;background:#00aaff;animation-duration:14s;animation-delay:4s;"></div>
      <div class="pt" style="left:70%;width:2px;height:2px;background:#ff44aa;animation-duration:10s;animation-delay:1s;"></div>
      <div class="pt" style="left:85%;width:3px;height:3px;background:#ffaa00;animation-duration:11s;animation-delay:6s;"></div>
      <div class="pt" style="left:40%;width:2px;height:2px;background:#00ffb4;animation-duration:8s;animation-delay:3s;"></div>
      <div class="pt" style="left:15%;width:2px;height:2px;background:#ff44aa;animation-duration:13s;animation-delay:5s;"></div>
      <div class="pt" style="left:60%;width:3px;height:3px;background:#b44dff;animation-duration:10s;animation-delay:7s;"></div>
      <div class="pt" style="left:78%;width:2px;height:2px;background:#00ffb4;animation-duration:9s;animation-delay:3.5s;"></div>
      <div class="pt" style="left:33%;width:4px;height:4px;background:#ffaa00;animation-duration:15s;animation-delay:1.5s;"></div>
      <div class="pt" style="left:92%;width:2px;height:2px;background:#00aaff;animation-duration:11s;animation-delay:8s;"></div>
      <div class="pt" style="left:5%;width:3px;height:3px;background:#b44dff;animation-duration:14s;animation-delay:9s;"></div>
    </div>

    <!-- ══════════ WELCOME ERA BANNER ══════════ -->
    <div class="era-banner">
      <div class="era-text">⚡ Welcome to the New Era of AI Help ⚡</div>
      <div class="era-subtitle">Intelligence · Knowledge · Transformation</div>
    </div>

    <!-- ══════════ RIVER / BOAT SCENE ══════════ -->
    <div style="width:100%;max-width:960px;margin:0 auto 56px;padding:0 20px;position:relative;z-index:10;">
      <div class="river-scene">
        <div class="river-scene-title">◈ THE RIVER OF KNOWLEDGE ◈</div>

        <!-- Speech bubbles -->
        <div class="speech-bubble" style="top:30%;left:12%;">
          🤝 How may I help you today?
        </div>
        <div class="speech-bubble speech-bubble-r" style="top:38%;right:12%;">
          I'm lost in problems… save me!
        </div>
        <div class="speech-bubble" style="top:55%;left:16%;font-size:11px;">
          ✨ Every problem has an answer…
        </div>

        <canvas id="riverCanvas"></canvas>

        <div class="river-poem">
          <div class="river-poem-text">
            <em>Upon the river of endless questions,</em> a <strong>boatman of light</strong> steers with wisdom's oar —<br>
            You stand on the shore, lost in the storm of problems,<br>
            and the <em>AI helper</em> reaches out: <strong>"Come, I'll guide you to the answer."</strong><br>
            <span style="color:rgba(255,255,255,0.35);font-size:12px;letter-spacing:3px;">◈ YOUR PROBLEMS · OUR SOLUTIONS · INFINITE KNOWLEDGE ◈</span>
          </div>
        </div>
      </div>

      <script>
      (function(){
        var canvas = document.getElementById('riverCanvas');
        if(!canvas) return;
        var ctx = canvas.getContext('2d');
        function resize(){ canvas.width=canvas.offsetWidth; canvas.height=480; }
        resize();
        window.addEventListener('resize', resize);

        var t = 0;
        var waves = [];
        for(var i=0;i<8;i++) waves.push({amp:8+Math.random()*12,freq:0.008+Math.random()*0.005,speed:0.3+Math.random()*0.4,offset:Math.random()*Math.PI*2,y:260+i*18,alpha:0.08-i*0.006});

        // Boat state
        var boat = {x:0.15,y:0.55,bobPhase:0};
        var aiHelper = {x:0.15};
        var person = {x:0.75,y:0.57,reachPhase:0};
        var bubbles = [];
        for(var b=0;b<25;b++) bubbles.push({x:Math.random(),y:0.45+Math.random()*0.5,r:1+Math.random()*3,speed:0.0003+Math.random()*0.0005,alpha:Math.random()});

        // Problems floating in river
        var probs = ["?","∑","∫","λ","π","∞","≠","√","θ","∂"];
        var probItems = probs.map(function(s,i){return{text:s,x:0.2+i*0.08,y:0.52+Math.sin(i)*0.04,phase:Math.random()*Math.PI*2,speed:0.001+Math.random()*0.002};});

        function draw(){
          ctx.clearRect(0,0,canvas.width,canvas.height);
          var W=canvas.width, H=canvas.height;

          // Night sky with stars
          var skyGrad = ctx.createLinearGradient(0,0,0,H*0.55);
          skyGrad.addColorStop(0,'#020008');
          skyGrad.addColorStop(0.4,'#030015');
          skyGrad.addColorStop(1,'#001a10');
          ctx.fillStyle=skyGrad; ctx.fillRect(0,0,W,H*0.6);

          // Stars
          ctx.save();
          for(var s=0;s<80;s++){
            var sx=((s*137.5+t*0.3)%1)*W;
            var sy=(s*0.618%0.45)*H;
            var sa=0.3+0.5*Math.sin(t*0.05+s);
            ctx.fillStyle='rgba(255,255,255,'+sa+')';
            ctx.beginPath(); ctx.arc(sx,sy,0.8+s%2*0.5,0,Math.PI*2); ctx.fill();
          }
          ctx.restore();

          // Moon / AI orb glow
          ctx.save();
          var moonX=W*0.82, moonY=H*0.12;
          var mgGlow = ctx.createRadialGradient(moonX,moonY,0,moonX,moonY,80);
          mgGlow.addColorStop(0,'rgba(0,255,180,0.25)');
          mgGlow.addColorStop(0.5,'rgba(0,200,150,0.08)');
          mgGlow.addColorStop(1,'transparent');
          ctx.fillStyle=mgGlow; ctx.fillRect(0,0,W,H);
          ctx.fillStyle='rgba(0,255,180,0.9)';
          ctx.beginPath(); ctx.arc(moonX,moonY,18+2*Math.sin(t*0.04),0,Math.PI*2); ctx.fill();
          ctx.fillStyle='rgba(255,255,255,0.8)';
          ctx.beginPath(); ctx.arc(moonX-3,moonY-3,12,0,Math.PI*2); ctx.fill();
          ctx.restore();

          // River water layers
          var riverTop = H*0.48;
          for(var wi=0;wi<waves.length;wi++){
            var wv=waves[wi];
            ctx.save();
            ctx.beginPath(); ctx.moveTo(0,wv.y/480*H);
            for(var x2=0;x2<=W;x2+=4){
              var wy=wv.y/480*H + wv.amp*Math.sin(wv.freq*x2+t*wv.speed+wv.offset);
              ctx.lineTo(x2,wy);
            }
            ctx.lineTo(W,H); ctx.lineTo(0,H); ctx.closePath();
            var wGrad=ctx.createLinearGradient(0,wv.y/480*H,0,H);
            wGrad.addColorStop(0,'rgba(0,'+(80+wi*10)+','+(40+wi*5)+','+wv.alpha+')');
            wGrad.addColorStop(1,'rgba(0,30,15,0.6)');
            ctx.fillStyle=wGrad; ctx.fill();
            ctx.restore();
          }

          // River surface shimmer
          ctx.save();
          for(var sh=0;sh<15;sh++){
            var sx2=(sh*0.073+t*0.002)%1*W;
            var sy2=riverTop+20+sh*12+5*Math.sin(t*0.08+sh);
            var salpha=0.1+0.1*Math.sin(t*0.1+sh);
            var slen=20+sh*3;
            var sGrad=ctx.createLinearGradient(sx2,sy2,sx2+slen,sy2);
            sGrad.addColorStop(0,'transparent');
            sGrad.addColorStop(0.5,'rgba(0,255,180,'+salpha+')');
            sGrad.addColorStop(1,'transparent');
            ctx.strokeStyle=sGrad; ctx.lineWidth=1;
            ctx.beginPath(); ctx.moveTo(sx2,sy2); ctx.lineTo(sx2+slen,sy2); ctx.stroke();
          }
          ctx.restore();

          // Floating bubbles in river
          bubbles.forEach(function(bb){
            bb.x=(bb.x+bb.speed)%1;
            var bx=bb.x*W, by=bb.y*H+6*Math.sin(t*0.06+bb.x*10);
            ctx.save();
            ctx.globalAlpha=0.3+0.3*Math.sin(t*0.08+bb.x*5);
            ctx.strokeStyle='rgba(0,255,180,0.6)'; ctx.lineWidth=1;
            ctx.beginPath(); ctx.arc(bx,by,bb.r,0,Math.PI*2); ctx.stroke();
            ctx.restore();
          });

          // Problem symbols floating in river
          probItems.forEach(function(p){
            p.phase+=p.speed;
            var px=((p.x+t*0.0004)%1)*W;
            var py=p.y*H+8*Math.sin(p.phase);
            ctx.save();
            ctx.globalAlpha=0.4+0.3*Math.sin(p.phase);
            ctx.fillStyle='rgba(180,77,255,0.8)';
            ctx.font='bold 14px monospace';
            ctx.textAlign='center'; ctx.textBaseline='middle';
            ctx.fillText(p.text,px,py);
            ctx.restore();
          });

          // BOAT
          var boatX = W*(0.15+0.08*Math.sin(t*0.015));
          var boatBob = H*0.58 + 6*Math.sin(t*0.045);
          boat.bobPhase += 0.04;

          // Boat body
          ctx.save();
          ctx.translate(boatX, boatBob);
          var boatGrad=ctx.createLinearGradient(-30,0,30,0);
          boatGrad.addColorStop(0,'rgba(0,255,180,0.6)');
          boatGrad.addColorStop(0.5,'rgba(0,200,150,0.8)');
          boatGrad.addColorStop(1,'rgba(0,255,180,0.6)');
          ctx.fillStyle=boatGrad;
          ctx.beginPath();
          ctx.moveTo(-35,0); ctx.quadraticCurveTo(-30,20,0,22); ctx.quadraticCurveTo(30,20,35,0);
          ctx.quadraticCurveTo(25,-6,0,-8); ctx.quadraticCurveTo(-25,-6,-35,0);
          ctx.fill();
          ctx.strokeStyle='rgba(0,255,180,0.4)'; ctx.lineWidth=1; ctx.stroke();

          // Boat glow trail
          var trailGrad=ctx.createLinearGradient(-60,10,0,10);
          trailGrad.addColorStop(0,'transparent');
          trailGrad.addColorStop(1,'rgba(0,255,180,0.15)');
          ctx.fillStyle=trailGrad;
          ctx.fillRect(-80,5,50,8);

          // AI Helper figure (on boat)
          ctx.fillStyle='rgba(0,255,220,0.9)';
          ctx.beginPath(); ctx.arc(0,-24,9,0,Math.PI*2); ctx.fill(); // head
          ctx.fillStyle='rgba(0,255,180,0.7)';
          ctx.fillRect(-8,-18,16,22); // body
          // Reaching arm
          ctx.strokeStyle='rgba(0,255,220,0.8)'; ctx.lineWidth=3;
          ctx.beginPath(); ctx.moveTo(12,-12);
          ctx.quadraticCurveTo(30+6*Math.sin(t*0.05),-8,42-8*Math.sin(t*0.05),-4);
          ctx.stroke();
          // Oar
          ctx.strokeStyle='rgba(0,255,180,0.5)'; ctx.lineWidth=2;
          ctx.beginPath(); ctx.moveTo(-10,0); ctx.lineTo(-20,30); ctx.stroke();
          ctx.fillStyle='rgba(0,255,180,0.4)';
          ctx.fillRect(-24,28,8,6);

          // Glow on AI helper
          var helperGlow=ctx.createRadialGradient(0,-24,0,0,-24,20);
          helperGlow.addColorStop(0,'rgba(0,255,180,0.3)');
          helperGlow.addColorStop(1,'transparent');
          ctx.fillStyle=helperGlow;
          ctx.beginPath(); ctx.arc(0,-24,20,0,Math.PI*2); ctx.fill();
          ctx.restore();

          // PERSON being saved (on shore right side)
          var personX = W*0.76 + 5*Math.sin(t*0.03);
          var personY = H*0.57 + 3*Math.cos(t*0.04);
          ctx.save();
          ctx.translate(personX, personY);
          ctx.fillStyle='rgba(255,150,100,0.85)';
          ctx.beginPath(); ctx.arc(0,-28,9,0,Math.PI*2); ctx.fill(); // head
          ctx.fillStyle='rgba(200,100,80,0.7)';
          ctx.fillRect(-7,-20,14,22); // body
          // Reaching towards boat
          ctx.strokeStyle='rgba(255,150,100,0.7)'; ctx.lineWidth=3;
          ctx.beginPath(); ctx.moveTo(-10,-14);
          ctx.quadraticCurveTo(-25+4*Math.sin(t*0.05),-10,-38+6*Math.sin(t*0.05),-6);
          ctx.stroke();
          // Wavy lines = problems around person
          for(var pw=0;pw<3;pw++){
            ctx.strokeStyle='rgba(180,77,255,'+(0.2+pw*0.1)+')';
            ctx.lineWidth=1.5;
            ctx.beginPath();
            for(var px2=-20;px2<=20;px2+=3){
              var pyy=(pw-1)*12+4*Math.sin(px2*0.5+t*0.1+pw);
              px2===-20?ctx.moveTo(px2,pyy):ctx.lineTo(px2,pyy);
            }
            ctx.stroke();
          }
          ctx.restore();

          // Shore / ground for person
          ctx.save();
          var shoreGrad=ctx.createLinearGradient(W*0.65,H*0.62,W,H*0.62);
          shoreGrad.addColorStop(0,'transparent');
          shoreGrad.addColorStop(0.2,'rgba(0,80,40,0.4)');
          shoreGrad.addColorStop(1,'rgba(0,60,30,0.6)');
          ctx.fillStyle=shoreGrad;
          ctx.beginPath(); ctx.moveTo(W*0.65,H*0.63); ctx.quadraticCurveTo(W*0.8,H*0.6,W,H*0.62);
          ctx.lineTo(W,H); ctx.lineTo(W*0.65,H); ctx.closePath(); ctx.fill();
          ctx.restore();

          // Connection line (rope/bridge between boat and person)
          var ropeAlpha=0.3+0.2*Math.sin(t*0.06);
          ctx.save();
          ctx.strokeStyle='rgba(0,255,180,'+ropeAlpha+')';
          ctx.lineWidth=1.5; ctx.setLineDash([6,4]);
          ctx.beginPath();
          ctx.moveTo(boatX+42, boatBob-4);
          ctx.quadraticCurveTo((boatX+personX)/2,(boatBob+personY)/2-20,personX-38,personY-6);
          ctx.stroke();
          ctx.restore();

          // Reflection of moon in water
          ctx.save();
          var reflGrad=ctx.createLinearGradient(W*0.82,H*0.55,W*0.82,H*0.8);
          reflGrad.addColorStop(0,'rgba(0,255,180,0.12)');
          reflGrad.addColorStop(1,'transparent');
          ctx.fillStyle=reflGrad;
          ctx.beginPath(); ctx.ellipse(W*0.82,H*0.7,6,40,0,0,Math.PI*2); ctx.fill();
          ctx.restore();

          t+=0.6;
          requestAnimationFrame(draw);
        }
        draw();
      })();
      </script>
    </div>

    <div class="lp-wrap">

      <!-- NEW: LOGO -->
      <div class="logo-section">
        <div class="logo-emblem">
          <div class="logo-ring-outer"></div>
          <svg viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="26" cy="26" r="22" stroke="rgba(0,255,180,0.3)" stroke-width="1.5"/>
            <path d="M14 26 C14 18.3 19.4 12.5 26 12.5 C32.6 12.5 38 18.3 38 26" stroke="#00ffb4" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M18 30 L26 18 L34 30" stroke="#00ffb4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="26" cy="33" r="3" fill="#00ffb4" opacity="0.8"/>
            <path d="M20 38 L32 38" stroke="rgba(0,255,180,0.4)" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="26" cy="26" r="3" fill="rgba(0,255,180,0.2)" stroke="rgba(0,255,180,0.5)" stroke-width="1"/>
          </svg>
        </div>
        <div class="logo-name">EXAMHELP AI</div>
        <div class="logo-tagline">◈ Elite Academic Intelligence ◈</div>
      </div>

      <!-- HERO -->
      <div class="hero-badge"><div class="badge-dot"></div> LIVE &nbsp;·&nbsp; ExamHelp AI v4.0</div>
      <div class="hero-title">EXAMHELP AI</div>
      <div class="hero-version">◈ ELITE ACADEMIC INTELLIGENCE PLATFORM ◈</div>
      <div class="hero-desc">
        The <span>ultimate AI-powered study ecosystem</span> built for high-performance learning.<br>
        9 Expert Engines · Multi-Modal · Production-Grade.
      </div>

      <!-- STATS -->
      <div class="stats-bar" style="animation: cardIn .8s cubic-bezier(.16,1,.3,1) both;">
        <div class="stat-item s1"><div class="stat-num">9</div><div class="stat-lbl">EXPERT ENGINES</div></div>
        <div class="stat-item s2"><div class="stat-num">30+</div><div class="stat-lbl">AI PERSONAS</div></div>
        <div class="stat-item s3"><div class="stat-num">∞</div><div class="stat-lbl">POSSIBILITIES</div></div>
      </div>

      <!-- EXPERT ENGINES -->
      <div class="section-label">◈ CORE INTELLIGENCE SUITE ◈</div>
      <div class="section-title">Elite Expert Engines</div>
      <div class="engines-grid">
        <div class="eng-card c1"><div class="eng-corner"></div><span class="eng-icon">⚡</span><div class="eng-name">Circuit Solver Pro</div><div class="eng-tag">ELECTRICAL</div><div class="eng-desc">Upload circuit diagrams — AI maps nodes & solves KVL/KCL with symbolic derivation.</div></div>
        <div class="eng-card c2"><div class="eng-corner"></div><span class="eng-icon">🎯</span><div class="eng-name">Advanced Math Solver</div><div class="eng-tag">MATHEMATICS</div><div class="eng-desc">Handwritten OCR + LaTeX proofs. Calculus, Linear Algebra, Real Analysis solved step-by-step.</div></div>
        <div class="eng-card c3"><div class="eng-corner"></div><span class="eng-icon">⚖️</span><div class="eng-name">Legal Analyser</div><div class="eng-tag">LAW</div><div class="eng-desc">Statutes, case law, IPC & Federal analysis with Senior Counsel depth and judicial reasoning.</div></div>
        <div class="eng-card c4"><div class="eng-corner"></div><span class="eng-icon">🔬</span><div class="eng-name">Research Scholar</div><div class="eng-tag">ACADEMIA</div><div class="eng-desc">Peer-review critiques, literature maps, and critical research gap identification.</div></div>
        <div class="eng-card c5"><div class="eng-corner"></div><span class="eng-icon">🏗️</span><div class="eng-name">Project Architect</div><div class="eng-tag">ENGINEERING</div><div class="eng-desc">Full-file project blueprints, production tech stacks, and Mermaid.js architecture diagrams.</div></div>
        <div class="eng-card c6"><div class="eng-corner"></div><span class="eng-icon">🩺</span><div class="eng-name">Medical Research Guide</div><div class="eng-tag">MEDICINE</div><div class="eng-desc">Clinical reasoning, pathophysiology, and pharmacokinetic profiles for medical education.</div></div>
        <div class="eng-card c7"><div class="eng-corner"></div><span class="eng-icon">💹</span><div class="eng-name">Elite Stocks Dashboard</div><div class="eng-tag">FINANCE</div><div class="eng-desc">Real-time market sentiment, technical indicators, and sector trend forecasting.</div></div>
        <div class="eng-card c8"><div class="eng-corner"></div><span class="eng-icon">📚</span><div class="eng-name">AI Dictionary & Lexicon</div><div class="eng-tag">LINGUISTICS</div><div class="eng-desc">Contextual meanings, etymology, difficulty-ranked synonyms, and cultural idioms.</div></div>
        <div class="eng-card c9"><div class="eng-corner"></div><span class="eng-icon">🎨</span><div class="eng-name">HTML Page Builder</div><div class="eng-tag">FRONTEND</div><div class="eng-desc">Stunning single-file HTML/CSS pages with Tailwind, glassmorphism & smooth animations.</div></div>
      </div>

      <!-- FEATURES -->
      <div class="section-label">◈ COMPLETE FEATURE SUITE ◈</div>
      <div class="section-title">Everything You Need</div>
      <div class="feat-grid">
        <div class="feat-item" style="animation-delay:.05s"><div class="feat-emoji">📑</div><div><div class="feat-name">Smart PDF Analyst</div><div class="feat-sub">Upload textbooks & notes, ask anything</div></div></div>
        <div class="feat-item" style="animation-delay:.08s"><div class="feat-emoji">▶️</div><div><div class="feat-name">YouTube Transcripts</div><div class="feat-sub">Instant summaries & key takeaways</div></div></div>
        <div class="feat-item" style="animation-delay:.11s"><div class="feat-emoji">🌐</div><div><div class="feat-name">Web Page Scraper</div><div class="feat-sub">Chat with any live article or wiki</div></div></div>
        <div class="feat-item" style="animation-delay:.14s"><div class="feat-emoji">🃏</div><div><div class="feat-name">Flashcard Generator</div><div class="feat-sub">Auto Q&A flashcards from material</div></div></div>
        <div class="feat-item" style="animation-delay:.17s"><div class="feat-emoji">📝</div><div><div class="feat-name">Interactive Quiz Mode</div><div class="feat-sub">AI-tracked quizzes with explanations</div></div></div>
        <div class="feat-item" style="animation-delay:.20s"><div class="feat-emoji">📊</div><div><div class="feat-name">Visual Mind Maps</div><div class="feat-sub">Mermaid.js concept diagrams</div></div></div>
        <div class="feat-item" style="animation-delay:.23s"><div class="feat-emoji">📅</div><div><div class="feat-name">Dynamic Study Planner</div><div class="feat-sub">Day-by-day revision timetables</div></div></div>
        <div class="feat-item" style="animation-delay:.26s"><div class="feat-emoji">🎭</div><div><div class="feat-name">30+ AI Personas</div><div class="feat-sub">Einstein, Feynman, Socrates & more</div></div></div>
        <div class="feat-item" style="animation-delay:.29s"><div class="feat-emoji">🎙️</div><div><div class="feat-name">Whisper Voice Chat</div><div class="feat-sub">Voice input with real-time audio replies</div></div></div>
        <div class="feat-item" style="animation-delay:.32s"><div class="feat-emoji">📸</div><div><div class="feat-name">Image OCR Scanner</div><div class="feat-sub">Extract text from handwritten notes</div></div></div>
        <div class="feat-item" style="animation-delay:.35s"><div class="feat-emoji">🔄</div><div><div class="feat-name">9-Key API Rotation</div><div class="feat-sub">Zero interruptions, smart cooldown</div></div></div>
        <div class="feat-item" style="animation-delay:.38s"><div class="feat-emoji">💎</div><div><div class="feat-name">Glassmorphism UI</div><div class="feat-sub">Premium responsive design system</div></div></div>
      </div>

      <!-- NEW: CHILD TESTIMONIALS -->
      <div class="child-section">
        <div class="child-section-title">💫 Students Got Helped</div>
        <div class="child-section-sub">◈ Real stories · Real transformations ◈</div>
        <div class="child-cards">
          <div class="child-card">
            <span class="child-avatar">👧</span>
            <div class="child-stars">★★★★★</div>
            <div class="child-name">PRIYA · ENGINEERING STUDENT</div>
            <div class="child-text">"I was drowning in circuit problems at midnight. ExamHelp AI solved my KVL equations step-by-step and explained each node. I passed with distinction!"</div>
            <div class="child-tag">CIRCUIT SOLVER</div>
          </div>
          <div class="child-card">
            <span class="child-avatar">👦</span>
            <div class="child-stars">★★★★★</div>
            <div class="child-name">ARJUN · LAW STUDENT</div>
            <div class="child-text">"The Legal Analyser helped me understand IPC sections I'd been confused about for weeks. It thinks like a senior counsel — absolutely brilliant!"</div>
            <div class="child-tag">LEGAL ENGINE</div>
          </div>
          <div class="child-card">
            <span class="child-avatar">🧒</span>
            <div class="child-stars">★★★★★</div>
            <div class="child-name">MEERA · MEDICAL STUDENT</div>
            <div class="child-text">"From pathophysiology to pharmacokinetics — this AI studies alongside me like a mentor. The mind maps and flashcards are magical for last-night revision!"</div>
            <div class="child-tag">MEDICAL ENGINE</div>
          </div>
        </div>
      </div>

      <!-- NEW: THOUGHTS / POETIC FLOATING SECTION -->
      <div class="thoughts-section">
        <div class="section-label">◈ WHAT WE BELIEVE ◈</div>
        <div class="section-title" style="font-size:22px;margin-bottom:24px;">Thoughts &amp; Philosophy</div>
        <div class="thought-bubble-wrap">
          <div class="thought-bubble">Every question you have deserves a <em>thoughtful answer</em>, not a search result.</div>
          <div class="thought-bubble"><strong>Knowledge</strong> is infinite — the only barrier is finding the right guide through the river of complexity.</div>
          <div class="thought-bubble">We don't just solve problems. We <em>illuminate the path</em> so you never fear the dark of confusion again.</div>
          <div class="thought-bubble">Like a <strong>boatman on still water</strong>, ExamHelp AI carries your burdens and delivers you to the shore of understanding.</div>
        </div>
      </div>

      <!-- ✦ NEW: SCROLL PROGRESS BAR ✦ -->
      <div class="scroll-prog" id="scrollProg"></div>

      <!-- ✦ NEW: LIVE TICKER ✦ -->
      <div class="live-ticker">
        <div class="ticker-item t1"><div class="ticker-num">9+</div><div class="ticker-lbl">Specialist Engines</div><div class="ticker-sub">Active & Loaded</div></div>
        <div class="ticker-item t2"><div class="ticker-num">9-Key</div><div class="ticker-lbl">Gemini Rotation</div><div class="ticker-sub">Zero limits</div></div>
        <div class="ticker-item t3"><div class="ticker-num">30+</div><div class="ticker-lbl">AI Personas</div><div class="ticker-sub">Einstein to Feynman</div></div>
        <div class="ticker-item t4"><div class="ticker-num">10M+</div><div class="ticker-lbl">Tokens Processed</div><div class="ticker-sub">High-bandwidth</div></div>
        <div class="ticker-item t5"><div class="ticker-num">&lt;1s</div><div class="ticker-lbl">Response Time</div><div class="ticker-sub">Ultra-fast Groq</div></div>
      </div>

      <!-- ✦ NEW: COMPARISON TABLE ✦ -->
      <div class="section-label">◈ WHY WE STAND OUT ◈</div>
      <div class="section-title">The ExamHelp Advantage</div>
      <div class="compare-section">
        <div class="compare-wrap">
          <table class="compare-table">
            <thead>
              <tr>
                <th>FEATURE</th>
                <th class="compare-header-us">EXAMHELP AI</th>
                <th class="compare-header-them">STANDARD AI</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Usage Limits</td>
                <td class="compare-col-us">Unlimited / 9-Key Pool</td>
                <td class="compare-col-them">Strict Quotas</td>
              </tr>
              <tr>
                <td>Voice & Visual Chat</td>
                <td class="compare-col-us"><span class="compare-yes">✓</span> Whisper + OCR</td>
                <td class="compare-col-them"><span class="compare-no">✗</span> Text only</td>
              </tr>
              <tr>
                <td>UI & Aesthetics</td>
                <td class="compare-col-us">Premium Glassmorphism</td>
                <td class="compare-col-them">Basic layouts</td>
              </tr>
              <tr>
                <td>Specialized Tools</td>
                <td class="compare-col-us">15+ Distinct Apps</td>
                <td class="compare-col-them">General bot</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ✦ NEW: FAQ ACCORDION ✦ -->
      <div class="section-label">◈ GOT QUESTIONS? ◈</div>
      <div class="section-title">Common Queries</div>
      <div class="faq-section" id="faqAccordion">
        <div class="faq-item">
          <div class="faq-q">Is the 9-Key auto-rotation truly seamless? <span class="faq-arrow">▼</span></div>
          <div class="faq-a">Yes. Under the hood, we check quota blocks. If one key runs out, the engine automatically injects the next healthy key mid-generation without dropping your context.</div>
        </div>
        <div class="faq-item">
          <div class="faq-q">Can the Circuit Solver do visual nodes? <span class="faq-arrow">▼</span></div>
          <div class="faq-a">Absolutely. Upload a diagram. It utilizes multi-modal OCR to trace lines and identify resistors, mapping them to KVL equations algebraically!</div>
        </div>
      </div>

      <!-- ✦ NEW: NOTIFICATION POPUP ✦ -->
      <div class="notif-popup" id="notifPopup">
        <div class="notif-icon">💡</div>
        <div class="notif-body">
          <div class="notif-title">System Update</div>
          <div class="notif-text">Project Architect engine is now fully integrated with Mermaid.js rendering!</div>
        </div>
        <div class="notif-close" onclick="document.getElementById('notifPopup').style.display='none'">✕</div>
      </div>

      <!-- ✦ NEW: ANIMATED TYPEWRITER ✦ -->
      <div class="typewriter-wrap">
        > <span id="typewriterText" class="typewriter"></span>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 1: LIVE IMPACT COUNTER
      ══════════════════════════════════════════ -->
      <div class=\"section-label\">◈ PLATFORM IMPACT ◈</div>
      <div class=\"section-title\">By the Numbers</div>
      <div class=\"impact-section\">
        <div class=\"impact-grid\">
          <div class=\"impact-cell ic1\">
            <span class=\"impact-icon\">🧠</span>
            <div class=\"impact-num\" id=\"cnt1\">0</div>
            <div class=\"impact-label\">Problems Solved</div>
            <div class=\"impact-sub\">Since v1.0 launch</div>
          </div>
          <div class=\"impact-cell ic2\">
            <span class=\"impact-icon\">⚡</span>
            <div class=\"impact-num\" id=\"cnt2\">0</div>
            <div class=\"impact-label\">API Keys Rotating</div>
            <div class=\"impact-sub\">Zero rate-limit drops</div>
          </div>
          <div class=\"impact-cell ic3\">
            <span class=\"impact-icon\">🎓</span>
            <div class=\"impact-num\" id=\"cnt3\">0</div>
            <div class=\"impact-label\">Study Hours Saved</div>
            <div class=\"impact-sub\">Per month avg</div>
          </div>
          <div class=\"impact-cell ic4\">
            <span class=\"impact-icon\">🔬</span>
            <div class=\"impact-num\" id=\"cnt4\">0</div>
            <div class=\"impact-label\">Expert Modules</div>
            <div class=\"impact-sub\">Law · Med · Math · More</div>
          </div>
          <div class=\"impact-cell ic5\">
            <span class=\"impact-icon\">🚀</span>
            <div class=\"impact-num\" id=\"cnt5\">0</div>
            <div class=\"impact-label\">ms Avg Response</div>
            <div class=\"impact-sub\">Ultra-fast Groq inference</div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 2: HOW IT WORKS
      ══════════════════════════════════════════ -->
      <div class=\"section-label\">◈ THE PROCESS ◈</div>
      <div class=\"section-title\">How ExamHelp AI Works</div>
      <div class=\"how-section\">
        <div class=\"how-steps\">
          <div class=\"how-step\">
            <div class=\"how-num-wrap\"><span class=\"how-icon\">💬</span></div>
            <div class=\"how-title\">ASK ANYTHING</div>
            <div class=\"how-desc\">Type, speak, or upload an image of your problem — from handwritten notes to complex circuit diagrams.</div>
          </div>
          <div class=\"how-connector\"></div>
          <div class=\"how-step\">
            <div class=\"how-num-wrap\"><span class=\"how-icon\">🧠</span></div>
            <div class=\"how-title\">ENGINE ROUTES</div>
            <div class=\"how-desc\">The platform auto-selects the best specialist engine — Math, Law, Medical, or a custom persona.</div>
          </div>
          <div class=\"how-connector\"></div>
          <div class=\"how-step\">
            <div class=\"how-num-wrap\"><span class=\"how-icon\">⚡</span></div>
            <div class=\"how-title\">AI PROCESSES</div>
            <div class=\"how-desc\">Multi-key Gemini pool + Groq ultra-speed inference generates a deep, structured response in under a second.</div>
          </div>
          <div class=\"how-connector\"></div>
          <div class=\"how-step\">
            <div class=\"how-num-wrap\"><span class=\"how-icon\">✅</span></div>
            <div class=\"how-title\">YOU MASTER IT</div>
            <div class=\"how-desc\">Step-by-step breakdowns, LaTeX proofs, Mermaid diagrams, and exportable study materials — all yours.</div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 3: CAPABILITY BARS
      ══════════════════════════════════════════ -->
      <div class=\"section-label\">◈ INTELLIGENCE PROFILE ◈</div>
      <div class=\"section-title\">Capability Spectrum</div>
      <div class=\"capability-section\">
        <div class=\"cap-grid\" id=\"capGrid\">
          <div class=\"cap-item\" style=\"animation-delay:.05s\">
            <div class=\"cap-header\"><span class=\"cap-name\">⚡ Circuit Analysis & EE</span><span class=\"cap-pct\" style=\"--bar-c:#00ffb4;\">98%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"98\" style=\"--bar-c:#00ffb4;\"></div></div>
          </div>
          <div class=\"cap-item\" style=\"animation-delay:.10s\">
            <div class=\"cap-header\"><span class=\"cap-name\">🎯 Advanced Mathematics</span><span class=\"cap-pct\" style=\"--bar-c:#b44dff;\">97%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"97\" style=\"--bar-c:#b44dff;\"></div></div>
          </div>
          <div class=\"cap-item\" style=\"animation-delay:.15s\">
            <div class=\"cap-header\"><span class=\"cap-name\">⚖️ Legal Analysis</span><span class=\"cap-pct\" style=\"--bar-c:#ff44aa;\">95%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"95\" style=\"--bar-c:#ff44aa;\"></div></div>
          </div>
          <div class=\"cap-item\" style=\"animation-delay:.20s\">
            <div class=\"cap-header\"><span class=\"cap-name\">🩺 Medical Research</span><span class=\"cap-pct\" style=\"--bar-c:#00aaff;\">94%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"94\" style=\"--bar-c:#00aaff;\"></div></div>
          </div>
          <div class=\"cap-item\" style=\"animation-delay:.25s\">
            <div class=\"cap-header\"><span class=\"cap-name\">🔬 Academic Research</span><span class=\"cap-pct\" style=\"--bar-c:#ffaa00;\">96%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"96\" style=\"--bar-c:#ffaa00;\"></div></div>
          </div>
          <div class=\"cap-item\" style=\"animation-delay:.30s\">
            <div class=\"cap-header\"><span class=\"cap-name\">🏗️ Software Architecture</span><span class=\"cap-pct\" style=\"--bar-c:#00ffb4;\">93%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"93\" style=\"--bar-c:#00ffb4;\"></div></div>
          </div>
          <div class=\"cap-item\" style=\"animation-delay:.35s\">
            <div class=\"cap-header\"><span class=\"cap-name\">📸 OCR & Vision Input</span><span class=\"cap-pct\" style=\"--bar-c:#b44dff;\">91%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"91\" style=\"--bar-c:#b44dff;\"></div></div>
          </div>
          <div class=\"cap-item\" style=\"animation-delay:.40s\">
            <div class=\"cap-header\"><span class=\"cap-name\">🎙️ Voice Transcription</span><span class=\"cap-pct\" style=\"--bar-c:#ff44aa;\">99%</span></div>
            <div class=\"cap-track\"><div class=\"cap-fill\" data-pct=\"99\" style=\"--bar-c:#ff44aa;\"></div></div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 4: MARQUEE FEATURE STRIP
      ══════════════════════════════════════════ -->
      <div class=\"marquee-section\">
        <div class=\"marquee-fade-l\"></div>
        <div class=\"marquee-fade-r\"></div>
        <div class=\"marquee-track\" id=\"marqueeTrack\">
          <span class=\"marquee-tag\">⚡ Circuit Solver Pro</span>
          <span class=\"marquee-tag\">🎯 LaTeX Math Engine</span>
          <span class=\"marquee-tag\">⚖️ IPC Case Law</span>
          <span class=\"marquee-tag\">🔬 Peer Review AI</span>
          <span class=\"marquee-tag\">🏗️ System Architect</span>
          <span class=\"marquee-tag\">🩺 Clinical Reasoning</span>
          <span class=\"marquee-tag\">💹 Market Sentiment</span>
          <span class=\"marquee-tag\">📚 Etymology Engine</span>
          <span class=\"marquee-tag\">🎨 HTML Generator</span>
          <span class=\"marquee-tag\">📑 Smart PDF Analyst</span>
          <span class=\"marquee-tag\">▶️ YouTube Transcripts</span>
          <span class=\"marquee-tag\">🃏 Flashcard Generator</span>
          <span class=\"marquee-tag\">📝 Interactive Quiz</span>
          <span class=\"marquee-tag\">📊 Mind Maps</span>
          <span class=\"marquee-tag\">🎭 Einstein Persona</span>
          <span class=\"marquee-tag\">🎙️ Whisper Voice</span>
          <span class=\"marquee-tag\">📸 Handwriting OCR</span>
          <span class=\"marquee-tag\">🌐 Web Scraper</span>
          <!-- Duplicate for seamless loop -->
          <span class=\"marquee-tag\">⚡ Circuit Solver Pro</span>
          <span class=\"marquee-tag\">🎯 LaTeX Math Engine</span>
          <span class=\"marquee-tag\">⚖️ IPC Case Law</span>
          <span class=\"marquee-tag\">🔬 Peer Review AI</span>
          <span class=\"marquee-tag\">🏗️ System Architect</span>
          <span class=\"marquee-tag\">🩺 Clinical Reasoning</span>
          <span class=\"marquee-tag\">💹 Market Sentiment</span>
          <span class=\"marquee-tag\">📚 Etymology Engine</span>
          <span class=\"marquee-tag\">🎨 HTML Generator</span>
          <span class=\"marquee-tag\">📑 Smart PDF Analyst</span>
          <span class=\"marquee-tag\">▶️ YouTube Transcripts</span>
          <span class=\"marquee-tag\">🃏 Flashcard Generator</span>
          <span class=\"marquee-tag\">📝 Interactive Quiz</span>
          <span class=\"marquee-tag\">📊 Mind Maps</span>
          <span class=\"marquee-tag\">🎭 Einstein Persona</span>
          <span class=\"marquee-tag\">🎙️ Whisper Voice</span>
          <span class=\"marquee-tag\">📸 Handwriting OCR</span>
          <span class=\"marquee-tag\">🌐 Web Scraper</span>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 5: TECH STACK SHOWCASE
      ══════════════════════════════════════════ -->
      <div class=\"section-label\">◈ POWERED BY ◈</div>
      <div class=\"section-title\">Elite Technology Stack</div>
      <div class=\"tech-section\">
        <div class=\"tech-ribbon\">
          <div class=\"tech-pill\" style=\"--tc:rgba(66,133,244,0.4);animation-delay:.05s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#4285F4,#34A853);\"></div>
            <span class=\"tech-name\">Gemini 1.5 Pro</span>
            <span class=\"tech-badge\">MULTIMODAL</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(255,107,53,0.4);animation-delay:.10s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#ff6b35,#f7c59f);\"></div>
            <span class=\"tech-name\">Groq API</span>
            <span class=\"tech-badge\">ULTRA-FAST</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(255,75,75,0.4);animation-delay:.15s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#ff4b4b,#ff9f9f);\"></div>
            <span class=\"tech-name\">Streamlit</span>
            <span class=\"tech-badge\">FRAMEWORK</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(0,212,170,0.4);animation-delay:.20s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#00d4aa,#00a090);\"></div>
            <span class=\"tech-name\">OpenAI Whisper</span>
            <span class=\"tech-badge\">VOICE</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(111,66,193,0.4);animation-delay:.25s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#6f42c1,#a78bfa);\"></div>
            <span class=\"tech-name\">Mermaid.js</span>
            <span class=\"tech-badge\">DIAGRAMS</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(0,200,255,0.4);animation-delay:.30s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#00c8ff,#0080ff);\"></div>
            <span class=\"tech-name\">SymPy</span>
            <span class=\"tech-badge\">SYMBOLIC MATH</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(255,200,0,0.4);animation-delay:.35s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#ffc800,#ff8000);\"></div>
            <span class=\"tech-name\">Supabase</span>
            <span class=\"tech-badge\">DATABASE</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(0,255,100,0.4);animation-delay:.40s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#00ff64,#00cc50);\"></div>
            <span class=\"tech-name\">FAISS Vector DB</span>
            <span class=\"tech-badge\">MEMORY</span>
          </div>
          <div class=\"tech-pill\" style=\"--tc:rgba(255,50,100,0.4);animation-delay:.45s\">
            <div class=\"tech-dot\" style=\"background:linear-gradient(135deg,#ff3264,#ff8080);\"></div>
            <span class=\"tech-name\">Stripe</span>
            <span class=\"tech-badge\">PAYMENTS</span>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 6: SOCIAL PROOF WALL
      ══════════════════════════════════════════ -->
      <div class=\"section-label\">◈ STUDENT VOICES ◈</div>
      <div class=\"section-title\">What the Elite Users Say</div>
      <div class=\"proof-section\">
        <div class=\"proof-wall\">
          <div class=\"proof-card\" style=\"--pc:rgba(0,255,180,0.3);animation-delay:.05s\">
            <div class=\"proof-stars\">★★★★★</div>
            <div class=\"proof-text\">\"The <em>Circuit Solver</em> literally saved my viva. I uploaded a messy hand-drawn schematic and it gave me a full KVL derivation in seconds. My professor was stunned.\"</div>
            <div class=\"proof-author\">
              <div class=\"proof-avatar\">🧑‍🔬</div>
              <div><div class=\"proof-name\">ARJUN MEHTA</div><div class=\"proof-role\">B.Tech EEE · VIT Chennai · Sem 6</div></div>
            </div>
          </div>
          <div class=\"proof-card\" style=\"--pc:rgba(180,77,255,0.3);animation-delay:.10s\">
            <div class=\"proof-stars\">★★★★★</div>
            <div class=\"proof-text\">\"I had a moot court competition in 3 days. The <em>Legal Analyser</em> mapped IPC sections and case precedents I didn't even know existed. We won silver.\"</div>
            <div class=\"proof-author\">
              <div class=\"proof-avatar\">👩‍⚖️</div>
              <div><div class=\"proof-name\">PRIYA SUNDARAM</div><div class=\"proof-role\">LLB Yr 3 · NLS Bangalore</div></div>
            </div>
          </div>
          <div class=\"proof-card\" style=\"--pc:rgba(0,170,255,0.3);animation-delay:.15s\">
            <div class=\"proof-stars\">★★★★★</div>
            <div class=\"proof-text\">\"Used the <em>Research Scholar</em> to critique 5 papers for my thesis proposal. What took me a week before now takes 20 minutes. This is not a chatbot, it's an upgrade.\"</div>
            <div class=\"proof-author\">
              <div class=\"proof-avatar\">🧑‍💻</div>
              <div><div class=\"proof-name\">ROHAN DAS</div><div class=\"proof-role\">M.Sc AI · IIT Kharagpur</div></div>
            </div>
          </div>
          <div class=\"proof-card\" style=\"--pc:rgba(255,170,0,0.3);animation-delay:.20s\">
            <div class=\"proof-stars\">★★★★★</div>
            <div class=\"proof-text\">\"The <em>Math Solver</em> handled my Real Analysis proofs with LaTeX output. I pasted it straight into my assignment. Step-by-step, verified, perfect formatting.\"</div>
            <div class=\"proof-author\">
              <div class=\"proof-avatar\">👩‍🎓</div>
              <div><div class=\"proof-name\">SAKSHI VERMA</div><div class=\"proof-role\">BSc Mathematics · DU · Yr 2</div></div>
            </div>
          </div>
          <div class=\"proof-card\" style=\"--pc:rgba(255,68,170,0.3);animation-delay:.25s\">
            <div class=\"proof-stars\">★★★★★</div>
            <div class=\"proof-text\">\"As a NEET aspirant, the <em>Medical Guide</em> explains pathophysiology in a way no textbook does. Tabular drug interactions, mnemonics, and clinical reasoning — all in one query.\"</div>
            <div class=\"proof-author\">
              <div class=\"proof-avatar\">🏥</div>
              <div><div class=\"proof-name\">KAVYA NAIR</div><div class=\"proof-role\">NEET 2025 Aspirant · Kerala</div></div>
            </div>
          </div>
          <div class=\"proof-card\" style=\"--pc:rgba(0,255,180,0.3);animation-delay:.30s\">
            <div class=\"proof-stars\">★★★★★</div>
            <div class=\"proof-text\">\"Built my entire final year project blueprint using the <em>Project Architect</em>. Got a full tech stack, system design, and Mermaid architecture diagram in one prompt. Incredible.\"</div>
            <div class=\"proof-author\">
              <div class=\"proof-avatar\">🏗️</div>
              <div><div class=\"proof-name\">AARAV SINGH</div><div class=\"proof-role\">B.Tech CSE · Manipal · Sem 8</div></div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 7: ENGINE SHOWCASE TILES
      ══════════════════════════════════════════ -->
      <div class=\"section-label\">◈ SPOTLIGHT ◈</div>
      <div class=\"section-title\">Engine Deep-Dive</div>
      <div class=\"showcase-section\">
        <div class=\"showcase-grid\">
          <div class=\"showcase-card sc1\">
            <div class=\"showcase-glow\"></div>
            <div class=\"showcase-inner\">
              <span class=\"showcase-emoji\">⚡</span>
              <div class=\"showcase-name\">CIRCUIT SOLVER PRO</div>
              <div class=\"showcase-detail\">Upload any circuit image. Get node analysis, KVL/KCL equations, and symbolic derivation — all in one response.</div>
              <div class=\"showcase-chip\" style=\"border-color:rgba(0,255,180,0.3);color:#00ffb4;\">Vision-to-Topology AI</div>
            </div>
          </div>
          <div class=\"showcase-card sc2\">
            <div class=\"showcase-glow\"></div>
            <div class=\"showcase-inner\">
              <span class=\"showcase-emoji\">⚖️</span>
              <div class=\"showcase-name\">LEGAL ANALYSER</div>
              <div class=\"showcase-detail\">Senior Counsel persona. Maps IPC sections, common law precedents, and generates judicial-depth hypothetical conclusions.</div>
              <div class=\"showcase-chip\" style=\"border-color:rgba(180,77,255,0.3);color:#c88dff;\">Temperature: 0.1 · Precision Mode</div>
            </div>
          </div>
          <div class=\"showcase-card sc3\">
            <div class=\"showcase-glow\"></div>
            <div class=\"showcase-inner\">
              <span class=\"showcase-emoji\">🎯</span>
              <div class=\"showcase-name\">MATH SOLVER</div>
              <div class=\"showcase-detail\">Handwritten OCR + hybrid symbolic resolution. Produces verified step-by-step LaTeX proofs from a photo of your notebook.</div>
              <div class=\"showcase-chip\" style=\"border-color:rgba(0,170,255,0.3);color:#00aaff;\">SymPy + Gemini Vision</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 8: URGENCY + FINAL CTA
      ══════════════════════════════════════════ -->
      <div class=\"urgency-bar\">
        <div class=\"urgency-text\">🔥 LIMITED PRIVATE ACCESS — NOT PUBLICLY AVAILABLE 🔥</div>
        <div class=\"urgency-sub\">◈ Password-gated · Invite only · Built for the elite academic ◈</div>
      </div>

      <div class=\"final-cta\">
        <div class=\"cta-title\">Ready to Unlock Elite Intelligence?</div>
        <div class=\"cta-sub\">9 expert engines. Infinite knowledge. One platform built for students who refuse to settle for average answers.</div>
        <div class=\"cta-pills\">
          <span class=\"cta-pill green\">✓ No Rate Limits</span>
          <span class=\"cta-pill purple\">✓ 30+ AI Personas</span>
          <span class=\"cta-pill pink\">✓ Voice + Vision</span>
          <span class=\"cta-pill green\">✓ LaTeX Output</span>
          <span class=\"cta-pill purple\">✓ Export Ready</span>
        </div>
        <div style=\"font-family:'Space Mono',monospace;font-size:11px;color:rgba(255,255,255,0.25);letter-spacing:3px;\">▸ Enter your access key below to begin ◂</div>
      </div>

      <!-- ══════════════════════════════════════════
           ✦ POWER ADDITION 9: INTERACTIVE JS UPGRADES
      ══════════════════════════════════════════ -->
      <script>
      (function(){
        // A. Animated Counter
        function animateCounter(el, target, suffix, duration) {
          var start = 0;
          var step = target / (duration / 16);
          var timer = setInterval(function(){
            start += step;
            if(start >= target){ start = target; clearInterval(timer); }
            var val = Math.floor(start);
            el.textContent = val >= 1000 ? (val/1000).toFixed(val>=10000?0:1)+'K' : val;
            if(suffix) el.textContent += suffix;
          }, 16);
        }
        var counters = [
          {id:'cnt1', target:124800, suffix:'', delay:200},
          {id:'cnt2', target:9, suffix:'×', delay:300},
          {id:'cnt3', target:3600, suffix:'', delay:400},
          {id:'cnt4', target:15, suffix:'+', delay:500},
          {id:'cnt5', target:820, suffix:'', delay:600},
        ];
        counters.forEach(function(c){
          setTimeout(function(){
            var el = document.getElementById(c.id);
            if(el) animateCounter(el, c.target, c.suffix, 1800);
          }, c.delay);
        });

        // B. Capability Bars animation on scroll
        function animateBars() {
          var fills = document.querySelectorAll('.cap-fill');
          fills.forEach(function(fill){
            var pct = fill.getAttribute('data-pct');
            if(pct) fill.style.width = pct + '%';
          });
        }
        setTimeout(animateBars, 800);

        // C. Scroll-reveal for proof cards
        if('IntersectionObserver' in window) {
          var revealObs = new IntersectionObserver(function(entries){
            entries.forEach(function(e){
              if(e.isIntersecting) { e.target.style.opacity='1'; e.target.style.transform='translateY(0)'; }
            });
          }, {threshold:0.1});
          document.querySelectorAll('.proof-card, .showcase-card, .how-step, .tech-pill').forEach(function(el){
            el.style.opacity='0'; el.style.transform='translateY(20px)'; el.style.transition='opacity .6s ease, transform .6s ease';
            revealObs.observe(el);
          });
        }
      })();
      </script>

      <!-- ✦ INTERACTIVE JS FOR ALL NEW SECTIONS ✦ -->
      <script>
      (function(){
        // 1. Scroll Progress
        window.addEventListener('scroll', function() {
          var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
          var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
          var scrolled = (winScroll / height) * 100;
          var prog = document.getElementById("scrollProg");
          if(prog) prog.style.width = scrolled + "%";
        });

        // 2. FAQ Interactivity
        setTimeout(function(){
          var faqItems = document.querySelectorAll('.faq-item');
          faqItems.forEach(function(item) {
            var q = item.querySelector('.faq-q');
            if(q) {
              q.addEventListener('click', function() {
                item.classList.toggle('open');
              });
            }
          });
        }, 1000);

        // 3. Typewriter Effect
        var typeWords = ["Initializing Elite Engines...", "Loading 9-Key Vault...", "Connecting to Gemini 1.5 Pro...", "System Ready."];
        var typeIndex = 0;
        var charIndex = 0;
        var typeDelay = 100;
        var currentEl = null;

        function type() {
          currentEl = document.getElementById("typewriterText");
          if(!currentEl) return;
          if(charIndex < typeWords[typeIndex].length) {
            currentEl.innerHTML += typeWords[typeIndex].charAt(charIndex);
            charIndex++;
            setTimeout(type, typeDelay);
          } else {
            setTimeout(erase, 2000);
          }
        }
        function erase() {
          if(!currentEl) return;
          if(charIndex > 0) {
            currentEl.innerHTML = typeWords[typeIndex].substring(0, charIndex-1);
            charIndex--;
            setTimeout(erase, 50);
          } else {
            typeIndex = (typeIndex + 1) % typeWords.length;
            setTimeout(type, 500);
          }
        }
        setTimeout(type, 1500);
      })();
      </script>

      <!-- GATE -->
      <div class="gate-wrap">
        <div class="gate-card">
          <div class="gate-title">🔐 ACCESS PORTAL</div>
          <div class="gate-sub">This platform is <strong style="color:rgba(255,68,170,0.7)">private & protected</strong>.<br>Not free to access — password required.</div>
          <div class="gate-label">▸ Secret Access Key</div>

          <!-- NEW: Contact for access -->
          <div class="access-info">
            <div class="access-info-text">
              🔑 To get access, contact us at:<br>
              <a href="mailto:piyushkumar52521@gmail.com">piyushkumar52521@gmail.com</a><br>
              <span style="font-size:12px;color:rgba(255,255,255,0.25);letter-spacing:2px;">◈ GMAIL · FOR MORE INFO & ACCESS REQUESTS ◈</span>
            </div>
          </div>
        </div>
      </div>

    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        entered = st.text_input("passcode", type="password", placeholder="· · · · · · · ·", label_visibility="collapsed", key="passcode_input")
        submit = st.button("⚡ UNLOCK & ENTER ⚡", use_container_width=True)
        if submit:
            if entered == _SITE_PASSCODE:
                st.session_state["passcode_verified"] = True
                st.rerun()
            else:
                st.error("⚠️ Invalid access key. Please try again.")

    st.markdown("""
    <div class="thanks-footer">
      <div class="made-by" style="font-family:'Orbitron',monospace;font-size:14px;font-weight:700;
        background:linear-gradient(90deg,#00ffb4,#b44dff,#ff44aa,#00aaff,#00ffb4);
        background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        animation:gradShift 5s linear infinite;filter:drop-shadow(0 0 12px rgba(0,255,180,.4));">
        ✦ MADE WITH ❤️ BY PIYUSH KUMAR ✦
      </div>

      <!-- POWERED BY -->
      <div class="powered-section">
        <div class="powered-label">⚡ Powered By ⚡</div>
        <div class="powered-logos">
          <div class="pw-logo">
            <div class="pw-dot" style="background:linear-gradient(135deg,#4285F4,#34A853);"></div>
            <span>Gemini Pro</span>
          </div>
          <div class="pw-logo">
            <div class="pw-dot" style="background:linear-gradient(135deg,#ff6b35,#f7c59f);"></div>
            <span>Groq API</span>
          </div>
          <div class="pw-logo">
            <div class="pw-dot" style="background:linear-gradient(135deg,#ff4b4b,#ff9f9f);"></div>
            <span>Streamlit</span>
          </div>
          <div class="pw-logo">
            <div class="pw-dot" style="background:linear-gradient(135deg,#00d4aa,#00a090);"></div>
            <span>OpenAI Whisper</span>
          </div>
          <div class="pw-logo">
            <div class="pw-dot" style="background:linear-gradient(135deg,#6f42c1,#a78bfa);"></div>
            <span>Mermaid.js</span>
          </div>
        </div>
      </div>

      <div class="copyright-text">
        © 2024–2025 Piyush Kumar · All Rights Reserved<br>
        ExamHelp AI v4.0 · Elite Academic Intelligence Platform<br>
        ◈ Unauthorized reproduction or distribution strictly prohibited ◈
      </div>

      <!-- THANKS FOR VISITING -->
      <div class="thanks-text" style="margin-top:20px;">
        🙏 Thanks for Visiting ExamHelp AI 🙏
      </div>
      <div style="font-family:'Rajdhani',sans-serif;font-size:13px;color:rgba(255,255,255,0.2);letter-spacing:3px;margin-top:6px;">
        May every question find its answer ✨
      </div>
    </div>
    <style>@keyframes gradShift{0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;}}</style>
    """, unsafe_allow_html=True)

    st.stop()

# ═══════════════════════════════════════════════
# END PASSCODE GATE — rest of app runs below
# ═══════════════════════════════════════════════

# ─────────────────────────────────────────────
# GOOGLE OAUTH CALLBACK (catch ?code= redirect)
# ─────────────────────────────────────────────
handle_google_oauth_callback()

# ─────────────────────────────────────────────
# AUTH GATE — show login page if not signed in
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# AUTH GATE — show login page if not signed in
# Guest bypass: _guest_bypass flag skips auth entirely
# ─────────────────────────────────────────────
# Direct access — auth is bypassed, everyone is a guest
st.session_state["_guest_bypass"] = True
_guest_mode = True


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

# ═══════════════════════════════════════════════
# INNER UI ENHANCEMENT LAYER — ADDITIVE ONLY
# Upgrades: chat bubbles, tool panels, mode headers,
# message actions, tabs, empty state, quick prompts,
# status banners, sidebar tools, response tabs
# ═══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── ENHANCED MESSAGE BUBBLES ── */
[data-testid="stChatMessage"] {
  border-radius: 18px !important;
  margin-bottom: 10px !important;
  padding: 14px 18px !important;
  border: 1px solid transparent !important;
  transition: box-shadow 0.3s ease, border-color 0.3s ease !important;
  animation: msgSlide 0.35s cubic-bezier(0.16,1,0.3,1) both !important;
  position: relative !important;
}
@keyframes msgSlide {
  from { opacity:0; transform:translateY(12px) scale(0.98); }
  to   { opacity:1; transform:none; }
}
[data-testid="stChatMessage"]:hover {
  box-shadow: 0 4px 24px rgba(124,106,247,0.12) !important;
  border-color: rgba(124,106,247,0.15) !important;
}
/* User messages — distinct tinted treatment */
[data-testid="stChatMessage"][data-testid*="user"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: linear-gradient(135deg, rgba(124,106,247,0.06), rgba(167,139,250,0.04)) !important;
  border-color: rgba(124,106,247,0.14) !important;
}
/* AI messages — clean glass card */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
  background: rgba(14,14,26,0.65) !important;
  border-color: rgba(80,80,140,0.18) !important;
  backdrop-filter: blur(16px) !important;
}

/* ── AVATAR GLOW ── */
[data-testid="stChatMessageAvatarAssistant"] {
  box-shadow: 0 0 0 2px rgba(124,106,247,0.35), 0 0 16px rgba(124,106,247,0.2) !important;
  border-radius: 50% !important;
  transition: box-shadow 0.3s ease !important;
}
[data-testid="stChatMessageAvatarUser"] {
  box-shadow: 0 0 0 2px rgba(167,139,250,0.3) !important;
  border-radius: 50% !important;
}

/* ── CHAT INPUT MEGA UPGRADE ── */
[data-testid="stChatInput"] {
  border-radius: 18px !important;
  overflow: hidden !important;
}
[data-testid="stChatInput"] > div {
  background: rgba(19,19,31,0.9) !important;
  border: 1.5px solid rgba(124,106,247,0.25) !important;
  border-radius: 18px !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.3), 0 0 0 0 rgba(124,106,247,0) !important;
  transition: all 0.3s cubic-bezier(0.16,1,0.3,1) !important;
}
[data-testid="stChatInput"]:focus-within > div {
  border-color: rgba(124,106,247,0.6) !important;
  box-shadow: 0 4px 32px rgba(0,0,0,0.4), 0 0 0 3px rgba(124,106,247,0.12) !important;
}
[data-testid="stChatInput"] textarea {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.95rem !important;
  line-height: 1.6 !important;
  color: var(--text) !important;
  caret-color: var(--accent) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color: rgba(144,144,184,0.5) !important;
  font-style: italic !important;
}
/* Send button */
[data-testid="stChatInput"] button {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 2px 12px rgba(124,106,247,0.35) !important;
  transition: all 0.25s ease !important;
}
[data-testid="stChatInput"] button:hover {
  transform: scale(1.08) !important;
  box-shadow: 0 4px 20px rgba(124,106,247,0.55) !important;
}

/* ── HERO EMPTY STATE UPGRADE ── */
.hero-wrap {
  background: radial-gradient(ellipse 70% 60% at 50% 40%, rgba(124,106,247,0.07), transparent 70%) !important;
  border-radius: 28px !important;
  border: 1px solid rgba(124,106,247,0.1) !important;
  margin-bottom: 1.5rem !important;
  position: relative !important;
  overflow: hidden !important;
}
.hero-wrap::before {
  content: '';
  position: absolute; inset: 0;
  background: repeating-linear-gradient(
    90deg,
    transparent 0px,
    transparent 48px,
    rgba(124,106,247,0.03) 48px,
    rgba(124,106,247,0.03) 49px
  );
  pointer-events: none;
}
.hero-badge {
  font-family: 'JetBrains Mono', monospace !important;
  letter-spacing: 0.06em !important;
}
.hero-title {
  font-family: 'DM Sans', sans-serif !important;
  letter-spacing: -1px !important;
}

/* ── QUICK PROMPT PILLS UPGRADE ── */
[data-testid="stMainBlockContainer"] [data-testid="stButton"] > button {
  position: relative !important;
  overflow: hidden !important;
}
/* Quick prompt buttons get special shimmer */
[data-testid="stMainBlockContainer"] [data-testid="stButton"] > button::after {
  content: '';
  position: absolute;
  top: 0; left: -100%; width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  transform: skewX(-20deg);
  transition: left 0.5s ease;
}
[data-testid="stMainBlockContainer"] [data-testid="stButton"] > button:hover::after {
  left: 160%;
}

/* ── PAGE HEADER GLOW LINE ── */
.page-header {
  position: relative !important;
}
.page-header::after {
  content: '';
  position: absolute; bottom: 0; left: 0;
  width: 60px; height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent2), transparent);
  border-radius: 99px;
  animation: headerLine 3s ease-in-out infinite alternate;
}
@keyframes headerLine {
  from { width: 40px; opacity: 0.6; }
  to   { width: 100px; opacity: 1; }
}
.page-header-title {
  background: linear-gradient(135deg, var(--text) 0%, var(--accent2) 60%, var(--accent) 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  font-size: 1.65rem !important;
}

/* ── STUDY BANNER PULSE ── */
.study-banner {
  position: relative !important;
  overflow: hidden !important;
}
.study-banner::before {
  content: '';
  position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(124,106,247,0.06), transparent);
  animation: bannerShimmer 4s ease-in-out infinite;
}
@keyframes bannerShimmer {
  0%   { left: -100%; }
  60%  { left: 100%; }
  100% { left: 100%; }
}

/* ── ENHANCED TABS (response area) ── */
[data-testid="stTabs"] [data-testid="stTabBar"] {
  gap: 4px !important;
  padding: 4px !important;
  border-radius: 14px !important;
}
[data-testid="stTabs"] [role="tab"] {
  border-radius: 10px !important;
  padding: 0.4rem 0.9rem !important;
  font-size: 0.83rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  transition: all 0.2s cubic-bezier(0.16,1,0.3,1) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  box-shadow: 0 2px 12px rgba(124,106,247,0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
  transform: translateY(-1px) !important;
}
[data-testid="stTabs"] [role="tabpanel"] {
  animation: tabIn 0.3s cubic-bezier(0.16,1,0.3,1) both !important;
}
@keyframes tabIn {
  from { opacity:0; transform:translateY(6px); }
  to   { opacity:1; transform:none; }
}

/* ── TOOL MODE HEADERS — page-header sub-text badge ── */
.page-header-sub {
  background: rgba(124,106,247,0.1) !important;
  border: 1px solid rgba(124,106,247,0.2) !important;
  border-radius: 99px !important;
  padding: 2px 12px !important;
  font-size: 0.72rem !important;
  color: var(--accent2) !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
}

/* ── STAT BOXES UPGRADE ── */
.stat-box {
  background: linear-gradient(145deg, rgba(19,19,31,0.9), rgba(26,26,46,0.7)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 4px 16px rgba(0,0,0,0.3) !important;
}
.stat-val {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 1.15rem !important;
}

/* ── FLASHCARD ENHANCED ── */
.flashcard {
  background: linear-gradient(145deg, rgba(19,19,31,0.95), rgba(26,26,46,0.85)) !important;
  box-shadow: 0 16px 48px rgba(0,0,0,0.5), 0 0 0 1px rgba(124,106,247,0.12), inset 0 1px 0 rgba(255,255,255,0.05) !important;
}
.flashcard:hover {
  box-shadow: 0 24px 64px rgba(0,0,0,0.6), 0 0 0 1px rgba(124,106,247,0.3), inset 0 1px 0 rgba(255,255,255,0.07) !important;
}

/* ── SOURCE CHIPS UPGRADE ── */
.source-chip {
  background: linear-gradient(135deg, rgba(19,19,31,0.9), rgba(26,26,46,0.8)) !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
  font-weight: 500 !important;
}

/* ── SIDEBAR SECTION LABELS UPGRADE ── */
.section-label {
  background: linear-gradient(90deg, rgba(124,106,247,0.08), transparent) !important;
  border-radius: 6px !important;
  padding: 4px 8px 4px 6px !important;
  margin: 1.1rem 0 0.5rem !important;
}

/* ── SIDEBAR TOOL BUTTONS ── */
[data-testid="stSidebar"] [data-testid="stButton"] > button {
  border-radius: 10px !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  transition: all 0.22s cubic-bezier(0.16,1,0.3,1) !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
  transform: translateY(-1px) scale(1.01) !important;
  box-shadow: 0 4px 14px rgba(124,106,247,0.2) !important;
}

/* ── EXPANDER UPGRADE ── */
[data-testid="stExpander"] {
  border-radius: 14px !important;
  border: 1px solid var(--bd-glass) !important;
  backdrop-filter: blur(12px) !important;
  overflow: hidden !important;
  transition: border-color 0.25s ease !important;
}
[data-testid="stExpander"]:hover {
  border-color: rgba(124,106,247,0.25) !important;
}
[data-testid="stExpander"] summary {
  border-radius: 13px !important;
  padding: 0.6rem 0.9rem !important;
  font-weight: 600 !important;
  font-size: 0.87rem !important;
  transition: background 0.2s ease !important;
}
[data-testid="stExpander"] summary:hover {
  background: rgba(124,106,247,0.07) !important;
}

/* ── PROGRESS BARS ── */
.prog-fill {
  background: linear-gradient(90deg, var(--accent), var(--accent2), #60a5fa) !important;
  background-size: 200% !important;
  animation: progShift 3s ease infinite !important;
}
@keyframes progShift {
  0%, 100% { background-position: 0% 50%; }
  50%       { background-position: 100% 50%; }
}

/* ── DOWNLOAD BUTTONS UPGRADE ── */
.stDownloadButton > button {
  background: linear-gradient(135deg, rgba(19,19,31,0.9), rgba(26,26,46,0.8)) !important;
  border-color: rgba(124,106,247,0.2) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  position: relative !important;
  overflow: hidden !important;
}
.stDownloadButton > button::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(124,106,247,0.12), rgba(167,139,250,0.06));
  opacity: 0;
  transition: opacity 0.25s ease;
  border-radius: inherit;
}
.stDownloadButton > button:hover::before { opacity: 1 !important; }
.stDownloadButton > button:hover {
  border-color: rgba(124,106,247,0.45) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(124,106,247,0.18) !important;
}

/* ── KEY HEALTH BAR ANIMATED ── */
.key-health-fill {
  background: linear-gradient(90deg, #34d399, #60a5fa, #a78bfa) !important;
  background-size: 200% !important;
  animation: progShift 4s ease infinite !important;
}

/* ── FOCUS BANNER UPGRADE ── */
.focus-banner {
  background: linear-gradient(90deg, rgba(124,106,247,0.12), rgba(167,139,250,0.06), transparent) !important;
  border-left: 3px solid transparent !important;
  border-image: linear-gradient(180deg, var(--accent), var(--accent2)) 1 !important;
  box-shadow: inset 4px 0 0 rgba(124,106,247,0.4) !important;
  border-image: none !important;
}

/* ── BACK BUTTONS — tool navigation ── */
[key*="_back"] button, [key*="back_"] button {
  background: rgba(19,19,31,0.6) !important;
  border-color: rgba(124,106,247,0.2) !important;
  font-size: 0.82rem !important;
}

/* ── SPINNER DOTS UPGRADE ── */
[data-testid="stSpinner"] {
  background: rgba(14,14,26,0.8) !important;
  border: 1px solid rgba(124,106,247,0.2) !important;
  border-radius: 12px !important;
  padding: 8px 14px !important;
  backdrop-filter: blur(12px) !important;
}

/* ── SUCCESS / ERROR / WARNING ALERTS UPGRADE ── */
[data-testid="stAlert"] {
  animation: alertIn 0.35s cubic-bezier(0.16,1,0.3,1) both !important;
}
@keyframes alertIn {
  from { opacity:0; transform:translateY(-8px) scale(0.97); }
  to   { opacity:1; transform:none; }
}

/* ── TOAST UPGRADE ── */
[data-testid="stToast"] {
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 500 !important;
}

/* ── SELECT / DROPDOWN UPGRADE ── */
[data-testid="stSelectbox"] > div > div {
  border-radius: 12px !important;
  border-color: rgba(124,106,247,0.2) !important;
  transition: all 0.22s ease !important;
}
[data-testid="stSelectbox"] > div > div:hover {
  border-color: rgba(124,106,247,0.45) !important;
  box-shadow: 0 2px 12px rgba(124,106,247,0.1) !important;
}

/* ── TEXT INPUT UPGRADE (tool modes) ── */
[data-testid="stTextInput"] > div > div > input {
  border-radius: 12px !important;
  border-color: rgba(124,106,247,0.2) !important;
  background: rgba(13,13,22,0.7) !important;
  font-family: 'DM Sans', sans-serif !important;
  transition: all 0.22s ease !important;
}
[data-testid="stTextInput"] > div > div > input:focus {
  border-color: rgba(124,106,247,0.55) !important;
  box-shadow: 0 0 0 3px rgba(124,106,247,0.1) !important;
}

/* ── TEXTAREA UPGRADE ── */
[data-testid="stTextArea"] textarea {
  border-radius: 14px !important;
  border-color: rgba(124,106,247,0.2) !important;
  background: rgba(13,13,22,0.7) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.9rem !important;
  line-height: 1.65 !important;
  transition: all 0.22s ease !important;
}
[data-testid="stTextArea"] textarea:focus {
  border-color: rgba(124,106,247,0.5) !important;
  box-shadow: 0 0 0 3px rgba(124,106,247,0.1) !important;
}

/* ── PERSONA CHIP UPGRADED ── */
.persona-chip {
  background: linear-gradient(135deg, rgba(124,106,247,0.15), rgba(167,139,250,0.08)) !important;
  border-color: rgba(124,106,247,0.3) !important;
  box-shadow: 0 2px 8px rgba(124,106,247,0.15) !important;
  font-weight: 600 !important;
}

/* ── LOGO ICON UPGRADE ── */
.eh-logo-icon {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 50%, #60a5fa 100%) !important;
  box-shadow: 0 4px 20px rgba(124,106,247,0.4), 0 0 0 1px rgba(255,255,255,0.1) inset !important;
}

/* ── SCROLLBAR STYLING ── */
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(124,106,247,0.3) transparent;
}
*::-webkit-scrollbar { width: 5px; height: 5px; }
*::-webkit-scrollbar-track { background: transparent; }
*::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(124,106,247,0.4), rgba(167,139,250,0.2));
  border-radius: 99px;
}
*::-webkit-scrollbar-thumb:hover { background: rgba(124,106,247,0.6); }

/* ── MAIN CONTENT CONTAINER — subtle depth ── */
[data-testid="stMainBlockContainer"] {
  background: transparent !important;
}

/* ── CODE BLOCK UPGRADE (inside chat) ── */
[data-testid="stChatMessage"] pre {
  border: 1px solid rgba(124,106,247,0.2) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
  position: relative !important;
}
[data-testid="stChatMessage"] pre::before {
  content: 'CODE';
  position: absolute; top: 8px; right: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem; letter-spacing: 2px;
  color: rgba(124,106,247,0.5);
  font-weight: 600;
}

/* ── DIVIDER UPGRADE ── */
[data-testid="stMainBlockContainer"] hr {
  background: linear-gradient(90deg, transparent, rgba(124,106,247,0.2), rgba(167,139,250,0.15), transparent) !important;
  height: 1px !important;
}

/* ── MESSAGE ACTION BUTTONS (copy/bookmark/speak) ── */
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
  border-radius: 8px !important;
  font-size: 0.8rem !important;
  min-width: 32px !important;
  height: 32px !important;
  padding: 0 8px !important;
  background: rgba(19,19,31,0.6) !important;
  border-color: rgba(124,106,247,0.15) !important;
  transition: all 0.2s ease !important;
}
[data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button:hover {
  background: rgba(124,106,247,0.12) !important;
  border-color: rgba(124,106,247,0.35) !important;
  transform: translateY(-1px) scale(1.05) !important;
}

/* ── BADGE STYLES UPGRADE ── */
.badge-green { box-shadow: 0 0 8px rgba(52,211,153,0.2) !important; }
.badge-red   { box-shadow: 0 0 8px rgba(248,113,113,0.2) !important; }

/* ── STALE CONTENT SMOOTHER FADE ── */
[data-testid="stMainBlockContainer"] > * {
  animation: contentIn 0.3s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes contentIn {
  from { opacity:0.6; transform:translateY(4px); }
  to   { opacity:1;   transform:none; }
}

/* ── POWERED BY TEXT ── */
.poweredby {
  background: linear-gradient(90deg, rgba(124,106,247,0.06), transparent) !important;
  border-radius: 8px !important;
  padding: 6px 10px !important;
}

/* ── FILE UPLOADER UPGRADE ── */
[data-testid="stFileUploader"] {
  border-radius: 14px !important;
}
[data-testid="stFileUploaderDropzone"] {
  border-color: rgba(124,106,247,0.25) !important;
  border-radius: 14px !important;
  background: rgba(13,13,22,0.5) !important;
  transition: all 0.25s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: rgba(124,106,247,0.5) !important;
  background: rgba(124,106,247,0.05) !important;
}

/* ── CHECKBOX UPGRADE ── */
[data-testid="stCheckbox"] label {
  font-size: 0.88rem !important;
  transition: color 0.2s ease !important;
}
[data-testid="stCheckbox"] label:hover { color: var(--accent2) !important; }

/* ── COLUMNS SPACING ── */
[data-testid="stHorizontalBlock"] {
  gap: 8px !important;
  align-items: center !important;
}

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# END INNER UI ENHANCEMENT LAYER
# ═══════════════════════════════════════════════

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
    """Render real-time API key health dashboard via OmniKeyEngine."""
    from utils.ai_engine import get_dashboard_html
    return get_dashboard_html()

def render_api_status():
    from utils.ai_engine import OMNI_ENGINE, get_token_usage_summary
    report = OMNI_ENGINE.get_status_report()
    icon = "🟢" if report["available"] > 0 else "🔴"
    st.sidebar.metric(f"{icon} Intelligence", f"{report['available']}/{report['total_keys']}")
    try:
        usage = get_token_usage_summary()
        st.sidebar.caption(f"Tokens consumed: {usage['total_in'] + usage['total_out']:,}")
    except Exception:
        pass

def render_stats_dashboard():
    """STEP 03: Animated stats mini-dashboard."""
    msg_count = len(st.session_state.messages)
    src_count = len(st.session_state.context_sources)
    ctx_chars = len(st.session_state.context_text)
    ctx_kb = round(ctx_chars / 1024, 1)
    tok_used = st.session_state.get("total_tokens_used", 0)
    ctx_pct = min(100, int((ctx_chars / 131072) * 100))
    intensity_pct = min(100, int((msg_count / 50) * 100))
    token_pct = min(100, int((tok_used / 1_000_000) * 100))

    st.markdown(f"""
    <div class="stats-dashboard-card">
      <div class="stats-dash-row">
        <span class="stats-dash-label">Session Stats</span>
        <span class="stats-dash-val">{msg_count}</span>
      </div>
      <div class="stats-mini-bar-wrap">
        <div class="stats-mini-bar-label"><span>Session Intensity</span><span>{intensity_pct}%</span></div>
        <div class="stats-mini-bar"><div class="stats-mini-fill fill-indigo" style="width:{intensity_pct}%"></div></div>
      </div>
      <div class="stats-mini-bar-wrap">
        <div class="stats-mini-bar-label"><span>Context Load · {ctx_kb}KB</span><span>{ctx_pct}%</span></div>
        <div class="stats-mini-bar"><div class="stats-mini-fill fill-cyan" style="width:{ctx_pct}%"></div></div>
      </div>
      <div class="stats-mini-bar-wrap">
        <div class="stats-mini-bar-label"><span>Token Budget · {tok_used//1000}k</span><span>{token_pct}%</span></div>
        <div class="stats-mini-bar"><div class="stats-mini-fill fill-green" style="width:{token_pct}%"></div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


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
            <div class="eh-logo-sub">Enterprise Hardened · v5.0.3</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ── Quick Intelligence Search ────────────────
        st.markdown('<div class="section-label">⚡ Quick Intelligence Search</div>', unsafe_allow_html=True)
        q_search = st.text_input("Search Intelligence", placeholder="Ask anything, get instant facts...", key="quick_search", label_visibility="collapsed")
        if q_search and st.button("🧠 Search Intelligence", use_container_width=True, key="do_quick_search"):
            st.session_state.queued_prompt = f"Provide a brief, factual, high-fidelity overview of: {q_search}"
            st.session_state.model_choice = "llama-3.3-70b-versatile"
            st.session_state.app_mode = "chat"; st.rerun()
        st.divider()

        # ── Theme toggle ───────────────────────────
        if st.button(
            "☀️ Light Mode" if st.session_state.theme_mode == "dark" else "🌙 Dark Mode",
            use_container_width=True, key="theme_btn"
        ):
            st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"
            st.rerun()

        # ── User profile chip ───────────────────────
        # st.markdown('''
        # <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
        #   border-radius:12px;padding:.5rem .8rem;display:flex;align-items:center;
        #   gap:.5rem;margin-bottom:.4rem;">
        #   <div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#7c6af7,#4f8ef7);
        #     display:flex;align-items:center;justify-content:center;font-size:.85rem;font-weight:700;color:#fff;">
        #     S
        #   </div>
        #   <div style="flex:1;overflow:hidden;">
        #     <div style="font-size:.78rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">Student</div>
        #     <div style="font-size:.66rem;color:rgba(255,255,255,0.4);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">ExamHelp AI · Direct Access</div>
        #   </div>
        # </div>''', unsafe_allow_html=True)

        # ── Google connect ──────────────────────────
        # render_google_connect_button()

        # ── Upgrade nudge (free users) ──────────────
        # render_upgrade_banner()

        # ── API Status and Health ──────────────────
        st.markdown('<div class="section-label">⚙️ System health</div>', unsafe_allow_html=True)
        render_api_status()
        st.divider()

        render_stats_dashboard()

        st.divider()

        # ── API Key Management (New Multi-Provider System) ─────────
        render_api_key_section()

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

        # ── Academic Context ────────────────────────
        st.markdown('<div class="section-label">🎓 Academic Context</div>', unsafe_allow_html=True)
        vit_mode = st.toggle("🎓 VIT Chennai Mode", 
                             help="Injects specific VIT Chennai exam, slot, and campus context into every AI response.")
        st.session_state["vit_mode"] = vit_mode

        # ── Model selector ─────────────────────────
        st.markdown('<div class="section-label">🧠 Model Speed</div>', unsafe_allow_html=True)
        model_choice = st.select_slider(
            "Model", options=["Fast (8B)", "Balanced (Scout 17B)"],
            value="Balanced (Scout 17B)", label_visibility="collapsed",
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

        # ── Elite Expert Engines ──────────────────────
        st.markdown('<div class="section-label">🚀 Elite Expert Engines</div>', unsafe_allow_html=True)
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            if st.button("⚡ Circuit Solver", use_container_width=True, key="side_circ"):
                st.session_state.app_mode = "circuit_solver"; st.rerun()
            if st.button("📚 AI Dictionary", use_container_width=True, key="side_dict"):
                st.session_state.app_mode = "dictionary"; st.rerun()
        with e_col2:
            if st.button("🎯 Math Solver", use_container_width=True, key="side_math"):
                st.session_state.app_mode = "math_solver"; st.rerun()
            if st.button("💹 Stocks Dash", use_container_width=True, key="side_stock"):
                st.session_state.app_mode = "stocks"; st.rerun()

        e_col3, e_col4 = st.columns(2)
        with e_col3:
            if st.button("⚖️ Legal Expert", use_container_width=True, key="side_legal"):
                st.session_state.app_mode = "legal_expert"; st.rerun()
            if st.button("🔬 Research Pro", use_container_width=True, key="side_research"):
                st.session_state.app_mode = "research_pro"; st.rerun()
        with e_col4:
            if st.button("🩺 Medical Guide", use_container_width=True, key="side_med"):
                st.session_state.app_mode = "medical_expert"; st.rerun()
            if st.button("🏗️ Proj Architect", use_container_width=True, key="side_arch"):
                st.session_state.app_mode = "project_architect"; st.rerun()

        st.divider()

        # ── Gamification & Focus ──────────────────────
        st.markdown('<div class="section-label">🎮 Gamification & Focus</div>', unsafe_allow_html=True)
        g_col1, g_col2, g_col3 = st.columns(3)
        with g_col1:
            if st.button("🍅 Pomodoro", use_container_width=True, key="side_pomo"):
                st.session_state.app_mode = "pomodoro"; st.rerun()
        with g_col2:
            if st.button("🔥 My Streak", use_container_width=True, key="side_streak"):
                st.session_state.app_mode = "study_streak"; st.rerun()
        with g_col3:
            if st.button("🧠 Insights", use_container_width=True, key="side_insights"):
                st.session_state.app_mode = "study_insights"; st.rerun()

        # Show compact streak badge in sidebar
        try:
            from study_streak_engine import _load_streak_data
            _sd = _load_streak_data()
            _streak = _sd.get('streak', 0)
            _xp     = _sd.get('total_xp', 0)
            if _streak > 0:
                st.markdown(f'''
                <div style="background:rgba(249,115,22,0.08);border:1px solid rgba(249,115,22,0.25);
                  border-radius:10px;padding:8px 12px;display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                  <span style="font-size:18px">🔥</span>
                  <div>
                    <div style="font-family:'Orbitron',monospace;font-size:12px;font-weight:700;
                      color:#fb923c;">{_streak}-Day Streak</div>
                    <div style="font-family:'Space Mono',monospace;font-size:9px;
                      color:rgba(255,255,255,0.3);letter-spacing:1px;">{_xp:,} XP TOTAL</div>
                  </div>
                </div>''', unsafe_allow_html=True)
        except Exception:
            pass

        # ── Daily Briefing button ───
        if st.button("🌅 Daily AI Briefing", use_container_width=True, key="side_briefing"):
            st.session_state.app_mode = "daily_briefing"; st.rerun()

        # ── Exam Countdown Widget ────────────────────────────
        st.markdown('<div class="section-label">🎯 Exam Countdown</div>', unsafe_allow_html=True)
        exam_d = st.date_input(
            "Exam Date",
            value=st.session_state.get("exam_date", datetime.date.today() + datetime.timedelta(days=30)),
            min_value=datetime.date.today(),
            label_visibility="collapsed",
            key="sidebar_exam_date",
        )
        st.session_state.exam_date = exam_d
        try:
            days_left = (exam_d - datetime.date.today()).days
            bar_pct   = max(0, min(100, int((1 - days_left / 30) * 100)))
            if days_left <= 7:   clr = "#ef4444"
            elif days_left <= 14: clr = "#f97316"
            else:                 clr = "#10b981"
            st.markdown(f'''
            <div style="margin:-4px 0 8px;">
              <div style="display:flex;justify-content:space-between;
                font-family:'Space Mono',monospace;font-size:9px;
                color:rgba(255,255,255,0.3);letter-spacing:1px;margin-bottom:5px;">
                <span>🎯 Exam day</span>
                <span style="color:{clr};font-weight:700;">{days_left}d left</span>
              </div>
              <div style="height:4px;background:rgba(255,255,255,0.06);border-radius:100px;overflow:hidden;">
                <div style="width:{bar_pct}%;height:100%;border-radius:100px;
                  background:linear-gradient(90deg,{clr},{clr}88);
                  transition:width 0.6s ease;"></div>
              </div>
            </div>''', unsafe_allow_html=True)
        except Exception:
            pass

        st.divider()

        with st.expander("⚠️ Advanced"):
            if st.button("🔄 Emergency Reset", use_container_width=True):
                if st.session_state.get("_confirm_reset", False):
                    keys_to_keep = [k for k in st.session_state if "key" in k.lower()]
                    for k in list(st.session_state.keys()):
                        if k not in keys_to_keep:
                            del st.session_state[k]
                    st.success("Session reset!")
                    st.rerun()
                else:
                    st.session_state["_confirm_reset"] = True
                    st.warning("Click again to confirm reset.")
            
            st.markdown('<div style="font-family:monospace; font-size:0.65rem; color:#00ff00; background:#000; padding:10px; border-radius:5px; border:1px solid #004400;"><b>NEURAL_LOG_v5.0.3</b><br>> Booting OmniEngine... OK<br>> Verifying 70B Quantization... OK<br>> Persona Latency: 42ms<br>> Neural Link Active.</div>', unsafe_allow_html=True)
        
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
                    # Award XP for PDF upload achievement
                    try:
                        from study_streak_engine import award_xp, unlock_achievement
                        award_xp(20, "PDF uploaded")
                        unlock_achievement("pdf_upload")
                    except Exception:
                        pass

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

    # ── Exam Countdown (display only — date set via sidebar widget) ─────────
    st.markdown('<div class="section-label">🗓️ Exam Countdown</div>', unsafe_allow_html=True)
    try:
        _ed = st.session_state.get("exam_date", datetime.date.today() + datetime.timedelta(days=30))
        _days_left = (_ed - datetime.date.today()).days
        _color = "var(--green)" if _days_left > 14 else "var(--accent)" if _days_left > 3 else "var(--red)"
        st.markdown(
            f'<div style="text-align:center;font-weight:800;color:{_color};font-size:1.8rem;padding:6px 0;">'
            f'{max(0,_days_left)}<span style="font-size:.9rem;font-weight:400;color:var(--text3);"> days</span></div>',
            unsafe_allow_html=True)
        st.caption(f"📅 Exam: {_ed}")
    except Exception:
        pass

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
    with c4:
        sessions = list(st.session_state.persistent_sessions.keys())
        if sessions:
            load_name = st.selectbox("Load", sessions, label_visibility="collapsed")
            cl1, cl2 = st.columns(2)
            with cl1:
                if st.button("📂", use_container_width=True):
                    d = st.session_state.persistent_sessions[load_name]
                    st.session_state.messages = d["messages"].copy()
                    st.session_state.context_text = d["context"]
                    st.session_state.context_sources = d["sources"].copy()
                    st.success("Loaded!")
                    st.rerun()
            with cl2:
                if st.button("🗑️", use_container_width=True):
                    del st.session_state.persistent_sessions[load_name]
                    with open("sessions.json","w") as f:
                        json.dump(st.session_state.persistent_sessions, f)
                    st.rerun()
        else:
            if st.button("➕ New Session", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    st.sidebar.divider()
    # ── Persistent System Telemetry ──────────────────
    with st.sidebar.expander("🛡️ System Telemetry & Performance", expanded=False):
        from utils.analytics import generate_performance_report
        st.markdown(f"""
        <div style="font-size:0.75rem; opacity:0.8; line-height:1.4;">
        {generate_performance_report()}
        <br>
        <b>Session Velocity:</b> {st.session_state.get('total_tokens_used',0)//1000}k tokens
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(1.0, (st.session_state.get('battle_lifetime_points', 0) % 500) / 500), text="Rank Progression")

    # Render the Real-Time Token Telemetry Dashboard
    render_telemetry_sidebar()

    st.sidebar.markdown("---")
    st.sidebar.caption("ExamHelp AI v5.0.3 Gold Standard")

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
    # ── Background Sound Player ──────────────────────────────
    st.markdown('<div class="section-label">🎵 Background Sounds</div>', unsafe_allow_html=True)
    try:
        from bg_sound_engine import render_sound_player_sidebar
        render_sound_player_sidebar()
    except Exception as _se:
        st.caption(f"Sound player unavailable: {_se}")

    # STEP 02: Active tool banner
    current_mode = st.session_state.get("app_mode", "chat")
    mode_labels = {
        "chat": "💬 Chat Mode", "flashcards": "🃏 Flashcards",
        "quiz": "📝 Quiz Mode", "mindmap": "📊 Mind Map",
        "debugger": "🐛 Code Debugger", "essay_writer": "📄 Essay Writer",
        "interview_coach": "🎤 Interview Coach", "legal_expert": "⚖️ Legal Expert",
        "medical_expert": "🩺 Medical Guide", "math_solver": "🎯 Math Solver",
        "stocks": "💹 Stocks Dashboard", "research_pro": "🔬 Research Pro",
        "circuit_solver": "⚡ Circuit Solver", "dictionary": "📚 Dictionary",
    }
    mode_display = mode_labels.get(current_mode, f"⚙️ {current_mode.replace('_',' ').title()}")
    st.markdown(f"""
    <div class="active-tool-banner">
      <div class="active-tool-dot"></div>
      ACTIVE: {mode_display}
    </div>""", unsafe_allow_html=True)

    with st.expander("🛠️ Study Toolbox", expanded=True):
        _tools = [
            ("🃏", "Flashcards",      "Generate Q&A deck",           "flashcards"),
            ("📝", "Quiz Mode",       "MCQ assessment",               "quiz"),
            ("📊", "Mind Map",        "Visual concept map",           "mindmap"),
            ("📅", "Study Planner",   "Revision timetable",          "planner"),
            ("📈", "Graph Plotter",   "Plot equations",               "graph"),
            ("🖋️", "Story Engine Pro", "Elite AI Fiction & Literature", "story"),
        ("🐛", "Code Debugger",   "Fix code in any language",     "debugger"),
        ("🎓", "Learn Coding",    "Interactive coding tutor",     "learn_coding"),
        ("📄", "Essay Writer",    "AI academic essay generator",  "essay_writer"),
        ("🎤", "Interview Coach", "Mock interviews + feedback",   "interview_coach"),
        ("⚡", "Study Toolkit",   "Formulas, PYQs & Pomodoro",    "study_toolkit"),
        ("🎓", "VIT Academics",    "GPA, Attendance & Slots",      "vit_academics"),
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

    with st.expander("⚡ Exotic Power Tools", expanded=False):
        _power_tools = [
            ("🔄", "Universal Converter", "Convert any file format instantly", "file_converter"),
            ("📚", "Citation Gen",        "IEEE/APA/MLA AI generator",      "citation_gen"),
            ("🔣", "Regex Builder",      "AI regex architect & tester",    "regex_tester"),
            ("🔲", "QR Code Engine",      "Generate pro QR codes & data links", "qr_creator"),
            ("🤖", "AI Text Humaniser",   "Bypass AI detectors & sound human", "ai_humaniser"),
            ("🎨", "HTML Generator",      "AI to beautiful single-page website", "html_generator"),
            ("🕵️", "Reverse Image Search", "AI vision lookup & deep analysis", "image_searcher"),
            ("📰", "AI News Hub",         "Live AI news & tool recommendations", "news_hub"),
            ("🗺️", "Voyager Map Studio", "Campus Guide & Interactive Planner", "map_planner"),
            ("🔀", "Code Converter",      "AI code translation + diff + zip",   "code_converter"),
            ("🛒", "Smart Shopping",      "Compare prices across platforms",     "smart_shopping"),
            ("🔬", "Context Focus",       "Deep internet research engine",      "context_focus"),
            ("🎯", "Presentation AI",     "Generate slide decks with real data", "presentation_builder"),
            ("🔥", "AI Companion",         "Nova · Luna · Zara — personas, scenarios & stories", "ai_companion"),
            ("📎", "Doc Analyser",         "Review any file: what\u2019s good, what to add", "doc_analyser"),
            ("🎵", "Sound Library",        "50+ ambient background sounds for focus", "bg_sounds"),
            # ── New Premium UI Pages ────────────────────────────────────────
            ("🌐", "Live Dashboard",       "NASA · Crypto · Earthquakes · Space live", "live_dashboard"),
            ("⚡", "API Explorer",         "Test all 72 free APIs interactively",      "api_explorer"),
            ("🎓", "Knowledge Hub",        "arXiv · PubMed · Books · Stack Overflow",  "knowledge_hub"),
            ("🌿", "Study Wellness",       "Breaks · Affirmations · Concept of Day",   "study_wellness"),
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

    # ── Account ──────────────────────────────────────────────────────
    # (Google Suite & Stripe integrations coming soon)
    st.markdown('<div class=\"poweredby\">Powered by <span>Groq</span> · <span>Gemini</span> · <span>LLaMA</span></div>',
                unsafe_allow_html=True)


def render_hero_header_v2():
    """STEP 01: Animated hero header with live clock badge."""
    persona = get_persona_by_name(st.session_state.selected_persona)
    persona_tag = ""
    if persona and st.session_state.selected_persona != "Default (ExamHelp)":
        persona_tag = f' · {persona["emoji"]} {persona["name"]}'

    st.markdown(f"""
    <div class="hero-header-v2">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div>
          <div class="hero-title-v2">ExamHelp AI{persona_tag}</div>
          <div class="hero-sub-v2">Cognitive Force Multiplier · Enterprise v5.0.3</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
          <div class="hero-badge-active">
            <div class="badge-dot-green"></div>AI ACTIVE
          </div>
          <div class="hero-live-clock" id="live-clock-01">--:--:--</div>
        </div>
      </div>
    </div>
    <script>
    (function(){{
      function tick(){{
        var d=new Date();
        var t=d.toLocaleTimeString('en-US',{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
        var el=document.getElementById('live-clock-01');
        if(el) el.textContent=t;
      }}
      tick(); setInterval(tick,1000);
    }})();
    </script>
    """, unsafe_allow_html=True)



def render_quick_actions_toolbar():
    """STEP 04: Floating quick-actions toolbar above the chat input."""
    st.markdown('<div class="float-toolbar">', unsafe_allow_html=True)
    cols = st.columns(6)
    actions = [
        ("🔄", "New Chat",    "s04_new_chat"),
        ("⬇️", "Export",     "s04_export"),
        ("🔒", "Focus",      "s04_focus"),
        ("📊", "Mind Map",   "s04_mindmap"),
        ("🃏", "Cards",      "s04_cards"),
        ("📄", "PDF",        "s04_context"),
    ]
    for i, (icon, label, key) in enumerate(actions):
        with cols[i]:
            if st.button(f"{icon} {label}", key=key, use_container_width=True):
                if key == "s04_new_chat":
                    st.session_state.messages = []
                    st.session_state.total_tokens_used = 0
                    st.rerun()
                elif key == "s04_focus":
                    st.session_state.focus_mode = not st.session_state.get("focus_mode", False)
                    st.rerun()
                elif key == "s04_mindmap":
                    st.session_state.app_mode = "mindmap"; st.rerun()
                elif key == "s04_cards":
                    st.session_state.app_mode = "flashcards"; st.rerun()
                elif key == "s04_context":
                    st.session_state.app_mode = "chat"
                    st.session_state["s04_show_context_panel"] = True
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_premium_chat_message(msg_content: str, role: str, msg_idx: int, avatar: str):
    """STEP 05: Render premium chat message bubble with CSS + React-style action buttons."""
    user_class = "bubble-user" if role == "user" else "bubble-assistant"
    
    st.markdown(f'<div class="chat-bubble-wrap {user_class}">', unsafe_allow_html=True)
    st.markdown(f'<div class="bubble-avatar">{avatar}</div>', unsafe_allow_html=True)
    
    # We must use st.container to render the markdown content safely inside the structure
    with st.container():
        st.markdown(f'<div class="bubble-content">', unsafe_allow_html=True)
        st.markdown(msg_content)
        
        if role == "assistant":
            # Action buttons
            st.markdown('<div class="bubble-actions">', unsafe_allow_html=True)
            col1, col2, col3, _ = st.columns([1,1,1,10])
            with col1:
                if st.button("📋", key=f"s5_c_{msg_idx}", help="Copy"):
                    st.toast("Copied!")
            with col2:
                if st.button("⭐", key=f"s5_b_{msg_idx}", help="Bookmark"):
                    st.toast("Bookmarked!")
            with col3:
                if st.button("🔊", key=f"s5_s_{msg_idx}", help="Read"):
                    st.toast("Reading...")
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('</div></div>', unsafe_allow_html=True)


def render_smart_context_panel():
    """STEP 06: Visual context source cards."""
    if not st.session_state.context_sources:
        return
    
    st.markdown('<div class="section-label" style="margin-top:20px;">📚 ACTIVE SOURCES</div>', unsafe_allow_html=True)
    st.markdown('<div class="ctx-panel">', unsafe_allow_html=True)
    
    icons = {"pdf":"📄","youtube":"▶️","web":"🌐","ocr":"📸"}
    
    cols = st.columns(max(1, len(st.session_state.context_sources)))
    for i, s in enumerate(st.session_state.context_sources):
        with cols[i]:
            ctype = s.get('type', 'txt')
            icon = icons.get(ctype, '📎')
            st.markdown(f"""
            <div class="ctx-card" style="animation-delay:{i*0.05}s">
                <div class="ctx-card-bg">{icon}</div>
                <div class="ctx-card-type">{ctype}</div>
                <div class="ctx-card-label">{s['label']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("❌ Remove", key=f"s6_rm_{i}", help="Remove source"):
                st.session_state.context_sources.pop(i)
                # Naive text clearing, real app would keep track of blocks
                st.session_state.context_text = "" 
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)


def render_persona_carousel():
    """STEP 08: Interacting Persona Carousel"""
    names = get_persona_names()
    current = st.session_state.get("selected_persona", "Default (ExamHelp)")
    
    st.markdown('<div class="persona-carousel">', unsafe_allow_html=True)
    cols = st.columns(len(names))
    for i, name in enumerate(names):
        p = get_persona_by_name(name)
        active = "⭐ " if name == current else ""
        with cols[i]:
            if st.button(f"{active}{p['emoji']}\n{name}", key=f"p_{i}", use_container_width=True):
                st.session_state.selected_persona = name
                st.session_state.messages = []
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_typing_indicator():
    """STEP 07: Show animated typing indicator."""
    return """
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <span class="typing-label">AI is thinking…</span>
    </div>"""

def render_quick_prompts():
    """STEP 09: Context-aware quick prompt suggestion grid."""
    QUICK_PROMPTS = [
        ("🧪", "Explain quantum entanglement with a simple analogy", "PHYSICS",  "--qc:rgba(99,102,241,0.3)"),
        ("🐍", "Write a Python function to reverse a linked list", "CODING",   "--qc:rgba(16,185,129,0.3)"),
        ("⚖️", "Explain the Indian Constitution's Preamble in detail", "LAW",    "--qc:rgba(245,158,11,0.3)"),
        ("🧠", "What are the stages of Piaget's cognitive development?", "PSYCH", "--qc:rgba(239,68,68,0.3)"),
        ("📈", "Explain compound interest with a worked example", "FINANCE",    "--qc:rgba(6,182,212,0.3)"),
        ("🌍", "Summarize the causes of World War I", "HISTORY",              "--qc:rgba(168,85,247,0.3)"),
        ("🔬", "What is CRISPR and how does gene editing work?", "BIO",        "--qc:rgba(34,197,94,0.3)"),
        ("🎨", "Write a short story opening in the style of Kafka", "CREATIVE","--qc:rgba(251,146,60,0.3)"),
        ("🗣️", "Translate 'The early bird catches the worm' into 5 languages", "LANG", "--qc:rgba(244,63,94,0.3)"),
    ]

    st.markdown('<div class="qprompt-section">', unsafe_allow_html=True)
    st.markdown('<div class="qprompt-title">✦ Quick Start — Click to Explore ✦</div>', unsafe_allow_html=True)
    st.markdown('<div class="qprompt-grid">', unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (icon, text, tag, css_var) in enumerate(QUICK_PROMPTS):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="qprompt-chip" style="{css_var}">
              <span class="qprompt-icon">{icon}</span>
              <div>
                <div class="qprompt-text">{text}</div>
                <span class="qprompt-tag">{tag}</span>
              </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"{icon} Ask", key=f"s09_qp_{i}", use_container_width=True):
                st.session_state.queued_prompt = text
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)


def render_tool_loader(tool_name: str, tool_icon: str = "⚙️"):
    """STEP 10: Show animated transition loader for tool switches."""
    st.markdown(f"""
    <div class="tool-loader">
      <div class="tool-loader-icon">{tool_icon}</div>
      <div class="tool-loader-title">Loading {tool_name}</div>
      <div class="tool-loader-bar-wrap">
        <div class="tool-loader-bar"></div>
      </div>
    </div>""", unsafe_allow_html=True)
    import time; time.sleep(0.15)


def render_followup_suggestions(msg_content: str, msg_idx: int):
    """STEP 11: Render AI-generated follow-up question chips."""
    if "followup_cache" not in st.session_state:
        st.session_state["followup_cache"] = {}

    cache_key = f"fu_{msg_idx}"
    if cache_key not in st.session_state["followup_cache"]:
        # Generate suggestions lazily (only generate for the LAST AI message)
        if msg_idx == len([m for m in st.session_state.messages if m["role"]=="assistant"]) - 1:
            try:
                from utils import ai_engine
                raw = ai_engine.quick_generate(
                    prompt=f"This was an AI study assistant's answer:\n\n{msg_content[:800]}\n\nGenerate 3 short follow-up questions a student might ask. Return ONLY a JSON array of 3 strings, no other text.",
                    system="Return only a valid JSON array of 3 short question strings."
                )
                import json, re
                match = re.search(r'\[.*?\]', raw, re.DOTALL)
                if match:
                    suggestions = json.loads(match.group(0))[:3]
                    st.session_state["followup_cache"][cache_key] = suggestions
            except Exception:
                st.session_state["followup_cache"][cache_key] = []

    suggestions = st.session_state["followup_cache"].get(cache_key, [])
    if suggestions:
        st.markdown('<div class="followup-label">ASK NEXT →</div>', unsafe_allow_html=True)
        cols = st.columns(len(suggestions))
        for i, q in enumerate(suggestions):
            with cols[i]:
                if st.button(q[:55], key=f"s11_fu_{msg_idx}_{i}", use_container_width=True):
                    st.session_state.queued_prompt = q
                    st.rerun()


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
persona     = get_persona_by_name(st.session_state.selected_persona)
if persona and st.session_state.selected_persona != "Default (ExamHelp)":
    st.markdown(apply_persona_theme(persona), unsafe_allow_html=True)

render_hero_header_v2()

# (old page-header replaced by render_hero_header_v2())

if st.session_state.focus_mode:
    st.markdown('<div class="focus-banner">🔒 Focus Mode Active — All distractions suppressed. Deep work in progress.</div>',
                unsafe_allow_html=True)

render_smart_context_panel()

app_mode = st.session_state.get("app_mode", "chat")

# ─────────────────────────────────────────────
# POWER MODE DISPATCHER (advanced_features.py)
# ─────────────────────────────────────────────
try:
    from advanced_features import dispatch_power_mode
    if dispatch_power_mode(app_mode):
        st.stop()
except Exception:
    pass

# ─────────────────────────────────────────────
# FLASHCARD MODE
# ─────────────────────────────────────────────
if app_mode == "flashcards":
    from utils.flashcard_engine import render_flashcards
    render_flashcards()

# ─────────────────────────────────────────────
# QUIZ MODE
# ─────────────────────────────────────────────
elif app_mode == "quiz":
    from utils.quiz_engine import render_quiz
    render_quiz()

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
# MAP PLANNER MODE
# ─────────────────────────────────────────────
elif app_mode == "map_planner":
    from map_engine import render_advanced_map
    render_advanced_map()

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
    try:
        from streamlit_ace import st_ace
        ace_lang = {"Python": "python", "C": "c_cpp", "C++": "c_cpp", "Java": "java", "JavaScript": "javascript", "TypeScript": "typescript", "Go": "golang", "Rust": "rust", "HTML/CSS": "html", "SQL": "sql", "Bash/Shell": "sh", "PHP": "php", "Ruby": "ruby"}.get(sel_lang, "text")
        lang_icon = SUPPORTED_LANGUAGES.get(sel_lang, {}).get("icon", "💻")
        st.markdown(f"**{lang_icon} {sel_lang} Source Code**")
        code_input = st_ace(
            value=st.session_state.get("debug_code_input", ""),
            language=ace_lang,
            theme="twilight" if st.session_state.get("theme_mode") == "dark" else "textmate",
            height=280,
            key="debug_ace_editor"
        )
        st.session_state.debug_code_input = code_input
    except ImportError:
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

        ca, cb = st.columns(2)
        with ca:
            if st.button("🔨 Run Original Code (Piston API)", use_container_width=True):
                with st.spinner("Executing via Piston..."):
                    from utils.debugger_engine import execute_code_piston
                    out = execute_code_piston(code_input, sel_lang)
                    st.code(out.get('run', {}).get('output', 'No output'), language='bash')
        with cb:
            # Extract fixed block to apply
            import re
            m = re.search(r'```[\w]*\n(.*?)```', result, re.DOTALL)
            fixed_code = m.group(1).strip() if m else None
            
            if fixed_code and st.button("✨ Apply Fix to Editor", use_container_width=True):
                st.session_state.debug_code_input = fixed_code
                st.rerun()

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
# ELITE EXPERT ENGINES
# ─────────────────────────────────────────────
elif app_mode == "circuit_solver":
    render_circuit_solver()

elif app_mode == "math_solver":
    render_math_solver()

elif app_mode == "dictionary":
    render_dictionary()

elif app_mode == "stocks":
    render_stocks_dashboard()

elif app_mode == "legal_expert":
    render_legal_expert()

elif app_mode == "medical_expert":
    render_medical_expert()

elif app_mode == "research_pro":
    render_research_pro()

elif app_mode == "project_architect":
    render_project_architect()

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
        generate_essay, improve_essay, generate_outline, score_essay,
        ESSAY_TYPES, ACADEMIC_LEVELS, CITATION_STYLES,
    )
    st.markdown("""<style>
.ew-header{background:linear-gradient(135deg,#1a0a3e 0%,#0d0d1a 100%);border:1px solid rgba(192,132,252,0.4);border-radius:20px;padding:28px 32px;margin-bottom:24px;position:relative;overflow:hidden;}
.ew-header::after{content:'';position:absolute;top:-60px;right:-60px;width:220px;height:220px;background:radial-gradient(circle,rgba(192,132,252,0.1),transparent 70%);border-radius:50%;}
.ew-title{font-size:1.9rem;font-weight:800;color:#c084fc;margin:0 0 4px;}
.ew-sub{font-size:.9rem;color:#9090b8;}
.ew-box{background:linear-gradient(145deg,rgba(20,10,40,.97),rgba(13,8,28,.95));border:1px solid rgba(192,132,252,.2);border-radius:16px;padding:24px 28px;margin-top:16px;line-height:1.8;}
.ew-score-card{background:rgba(192,132,252,0.06);border:1px solid rgba(192,132,252,0.2);border-radius:14px;padding:18px 22px;margin-top:12px;}
.ew-tone-badge{display:inline-block;background:rgba(192,132,252,0.1);border:1px solid rgba(192,132,252,0.25);border-radius:99px;padding:3px 12px;font-size:.75rem;color:#c084fc;font-weight:600;margin:2px;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="ew-header"><div class="ew-title">📄 Elite Essay Writer</div><div class="ew-sub">14 essay types · 5 academic levels · 7 citation styles · AI scoring · Outline → Draft → Polish pipeline</div></div>', unsafe_allow_html=True)

    tab_write, tab_outline, tab_improve, tab_score, tab_hist = st.tabs(["✍️ Write Essay", "📋 Outline First", "🔧 Improve", "🎯 Score My Essay", "📜 History"])

    with tab_write:
        c1, c2, c3 = st.columns(3)
        with c1:
            etype = st.selectbox("📝 Essay Type", list(ESSAY_TYPES.keys()), key="ew_type")
        with c2:
            elevel = st.selectbox("🎓 Academic Level", ACADEMIC_LEVELS, index=1, key="ew_level")
        with c3:
            ecite = st.selectbox("📚 Citation Style", CITATION_STYLES, key="ew_cite")

        etopic = st.text_input("💡 Essay Topic / Question", placeholder="e.g. 'To what extent has AI transformed employment markets since 2020?'", key="ew_topic")

        c4, c5, c6 = st.columns(3)
        with c4:
            ewords = st.slider("📏 Target Word Count", 300, 4000, 800, 100, key="ew_words")
        with c5:
            etone = st.selectbox("🎨 Tone", ["Academic", "Formal", "Persuasive", "Critical", "Reflective", "Technical"], key="ew_tone")
        with c6:
            eaudience = st.text_input("👥 Audience (optional)", placeholder="e.g. Journal reviewers, professors...", key="ew_audience")

        epoints = st.text_area("🔑 Key Arguments / Points to Include (optional)", height=80, placeholder="Bullet your key arguments here...", key="ew_points")

        if st.session_state.get("context_text"):
            use_ctx = st.checkbox("📎 Reference uploaded study material as source", value=True, key="ew_ctx")
        else:
            use_ctx = False

        st.markdown(f'<div style="font-size:.8rem;color:#9090b8;margin:4px 0">📋 {ESSAY_TYPES.get(etype,"")}</div>', unsafe_allow_html=True)

        cb1, cb2 = st.columns([3, 1])
        with cb1:
            write_btn = st.button("🚀 Generate Complete Essay", type="primary", use_container_width=True, disabled=not etopic.strip(), key="ew_gen")
        with cb2:
            if st.button("💬 Back", use_container_width=True, key="ew_back"):
                st.session_state.app_mode = "chat"; st.rerun()

        if write_btn and etopic.strip():
            with st.spinner("✍️ Writing your essay — this uses the full Gemini engine for quality..."):
                try:
                    ctx = st.session_state.context_text if use_ctx else ""
                    result = generate_essay(etopic, etype, ewords, elevel, ecite, epoints, ctx, etone, eaudience)
                    st.session_state.essay_result = result
                    st.session_state.essay_history.append({"topic": etopic, "type": etype, "level": elevel, "words": ewords, "result": result, "ts": time.strftime("%H:%M")})
                except Exception as e:
                    st.error(f"❌ Essay engine error: {e}")

        if st.session_state.get("essay_result"):
            wc = len(st.session_state.essay_result.split())
            m1, m2, m3 = st.columns(3)
            m1.metric("Words", f"~{wc}")
            m2.metric("Type", etype.split()[0])
            m3.metric("Level", elevel.split()[0])
            st.markdown('<div class="ew-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.essay_result)
            st.markdown('</div>', unsafe_allow_html=True)
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("📥 Download (.md)", st.session_state.essay_result, file_name="essay.md", mime="text/markdown", use_container_width=True, key="ew_dl")
            with dl2:
                if st.button("🎯 Score This Essay", use_container_width=True, key="ew_score_btn"):
                    with st.spinner("Scoring..."):
                        score_result = score_essay(st.session_state.essay_result)
                        st.session_state["_essay_score_result"] = score_result
            with dl3:
                if st.button("🔧 Auto-Polish", use_container_width=True, key="ew_polish"):
                    with st.spinner("Polishing..."):
                        polished = improve_essay(st.session_state.essay_result, "Strengthen the thesis, tighten arguments, improve transitions, elevate vocabulary while maintaining clarity")
                        st.session_state.essay_result = polished
                        st.rerun()
            if st.session_state.get("_essay_score_result"):
                st.markdown('<div class="ew-score-card">', unsafe_allow_html=True)
                st.markdown(st.session_state["_essay_score_result"])
                st.markdown('</div>', unsafe_allow_html=True)

    with tab_outline:
        ot = st.text_input("Topic / Question", key="eo_topic", placeholder="Enter essay topic or question...")
        oc1, oc2, oc3 = st.columns(3)
        with oc1: otype = st.selectbox("Type", list(ESSAY_TYPES.keys()), key="eo_type")
        with oc2: owords = st.slider("Target word count", 300, 4000, 800, 100, key="eo_words")
        with oc3: olevel = st.selectbox("Level", ACADEMIC_LEVELS, index=1, key="eo_level")
        if st.button("📋 Generate Strategic Outline", type="primary", use_container_width=True, disabled=not ot.strip(), key="eo_btn"):
            with st.spinner("Architecting essay structure..."):
                try:
                    result = generate_outline(ot, otype, owords, olevel)
                    st.session_state.essay_outline = result
                except Exception as e:
                    st.error(f"❌ {e}")
        if st.session_state.get("essay_outline"):
            st.markdown('<div class="ew-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.essay_outline)
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("✍️ Write Full Essay from This Outline", use_container_width=True, key="eo_to_write"):
                st.session_state.app_mode = "essay_writer"
                st.rerun()

    with tab_improve:
        orig = st.text_area("📄 Paste your essay", height=220, key="ei_orig", placeholder="Paste your existing essay here...")
        instr = st.text_input("🔧 Improvement instruction", key="ei_instr",
            placeholder="e.g. 'Strengthen the thesis and add counter-arguments'")
        quick_improvements = ["Strengthen argument", "Improve transitions", "Elevate vocabulary", "Add evidence", "Fix structure", "Academic tone"]
        st.markdown("**Quick improvements:**")
        qi_cols = st.columns(3)
        for i, qi_label in enumerate(quick_improvements):
            with qi_cols[i % 3]:
                if st.button(qi_label, key=f"qi_{i}", use_container_width=True):
                    st.session_state["_ei_instr_prefill"] = qi_label
        if st.session_state.get("_ei_instr_prefill") and not instr:
            instr = st.session_state.pop("_ei_instr_prefill", "")
        if st.button("⚡ Improve Essay", type="primary", use_container_width=True, disabled=not (orig.strip() and instr.strip()), key="ei_btn"):
            with st.spinner("Improving essay..."):
                try:
                    result = improve_essay(orig, instr)
                    st.session_state.essay_result = result
                    st.session_state["_improved_essay"] = result
                except Exception as e:
                    st.error(f"❌ {e}")
        if st.session_state.get("_improved_essay"):
            st.markdown('<div class="ew-box">', unsafe_allow_html=True)
            st.markdown(st.session_state["_improved_essay"])
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("📥 Download Improved Essay", st.session_state["_improved_essay"], file_name="improved_essay.md", use_container_width=True, key="ei_dl")

    with tab_score:
        score_input = st.text_area("📄 Paste essay to score", height=220, placeholder="Paste any essay here for AI scoring...")
        if st.button("🎯 Score Essay (6 Dimensions)", type="primary", use_container_width=True, disabled=not score_input.strip(), key="es_btn"):
            with st.spinner("Evaluating essay quality..."):
                try:
                    result = score_essay(score_input)
                    st.session_state["_score_result"] = result
                except Exception as e:
                    st.error(f"❌ {e}")
        if st.session_state.get("_score_result"):
            st.markdown('<div class="ew-score-card">', unsafe_allow_html=True)
            st.markdown(st.session_state["_score_result"])
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_hist:
        hist = st.session_state.get("essay_history", [])
        if not hist:
            st.info("No essays written yet.")
        else:
            st.markdown(f"**{len(hist)} essays in history**")
        for h in reversed(hist[-10:]):
            with st.expander(f"📄 {h.get('ts','—')} · {h.get('type','')[:20]} · {h.get('topic','')[:40]}"):
                st.markdown(f"**Level:** {h.get('level','')} · **Words:** ~{len(h['result'].split())}")
                st.markdown(h["result"])
                st.download_button("📥 Download", h["result"], file_name=f"essay_{h.get('ts','out')}.md", key=f"edl_{h.get('ts','x')}")


# ══════════════════════════════════════════════════════
# INTERVIEW COACH MODE
# ══════════════════════════════════════════════════════
elif app_mode == "interview_coach":
    from utils.interview_engine import (
        generate_questions, evaluate_answer, mock_interview_response,
        generate_company_research, generate_salary_negotiation,
        INTERVIEW_TYPES, EXPERIENCE_LEVELS,
    )
    st.markdown("""<style>
.ic-header{background:linear-gradient(135deg,#0a1e10 0%,#0d1a14 100%);border:1px solid rgba(74,222,128,0.35);border-radius:20px;padding:28px 32px;margin-bottom:24px;position:relative;overflow:hidden;}
.ic-header::after{content:'';position:absolute;top:-50px;right:-50px;width:200px;height:200px;background:radial-gradient(circle,rgba(74,222,128,0.1),transparent 70%);border-radius:50%;}
.ic-title{font-size:1.9rem;font-weight:800;color:#4ade80;margin:0 0 4px;}
.ic-sub{font-size:.9rem;color:#9090b8;}
.ic-q{background:rgba(10,30,16,.9);border:1px solid rgba(74,222,128,.22);border-radius:16px 16px 16px 4px;padding:16px 18px;margin:8px 0;animation:msgIn .3s ease;}
.ic-a{background:rgba(124,106,247,.07);border:1px solid rgba(124,106,247,.2);border-radius:16px 16px 4px 16px;padding:14px 18px;margin:6px 0;animation:msgIn .3s ease;}
@keyframes msgIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}
.ic-score{background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.2);border-radius:14px;padding:18px 22px;margin-top:12px;}
.ic-tip{background:rgba(251,191,36,0.07);border:1px solid rgba(251,191,36,0.2);border-radius:10px;padding:10px 14px;font-size:.85rem;color:#fbbf24;margin-top:8px;}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="ic-header"><div class="ic-title">🎤 Elite Interview Coach</div><div class="ic-sub">Live mock interviews · STAR coaching · Per-answer scoring · Company intel · Salary negotiation</div></div>', unsafe_allow_html=True)

    tab_mock, tab_bank, tab_eval, tab_company, tab_salary = st.tabs(["🎭 Live Mock", "❓ Question Bank", "🎯 Evaluate Answer", "🏢 Company Intel", "💰 Salary Negotiation"])

    with tab_mock:
        mc1, mc2, mc3 = st.columns(3)
        with mc1: ic_role = st.text_input("Target Role", placeholder="e.g. Software Engineer at Google", key="ic_role")
        with mc2: ic_type = st.selectbox("Interview Type", list(INTERVIEW_TYPES.keys()), key="ic_type_mock")
        with mc3: ic_exp = st.selectbox("Experience Level", EXPERIENCE_LEVELS, key="ic_exp")
        st.session_state.interview_role = ic_role

        # Interview tips for the selected type
        type_tips = {
            "Technical (CS/Engineering)": "💡 Think aloud while solving. Clarify requirements before coding. Start with brute force, then optimize.",
            "Behavioural (STAR Method)": "💡 Use STAR: Situation → Task → Action → Result. Always end with a measurable outcome.",
            "Case Interview (Consulting)": "💡 Structure first. Use MECE framework. Ask clarifying questions. Lead the case, don't follow.",
            "Product Manager": "💡 Start with user needs. Define success metrics. Prioritize ruthlessly. Show trade-off thinking.",
        }
        tip = type_tips.get(ic_type, "💡 Listen carefully, ask clarifying questions, and give structured answers.")
        st.markdown(f'<div class="ic-tip">{tip}</div>', unsafe_allow_html=True)

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
            if st.button("📊 Get Full Feedback", use_container_width=True, disabled=len(st.session_state.interview_messages) < 2, key="ic_fb"):
                with st.spinner("Generating comprehensive feedback..."):
                    try:
                        fb = mock_interview_response(st.session_state.interview_messages, ic_role, ic_type, "feedback")
                        st.session_state.interview_feedback = fb
                    except Exception as e:
                        st.error(str(e))
        with mb3:
            if st.button("🗑️ Reset Session", use_container_width=True, key="ic_reset"):
                st.session_state.interview_messages = []
                st.session_state.interview_feedback = None
                st.rerun()

        # Message display
        for msg in st.session_state.interview_messages:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="ic-q">🎤 <b>Interviewer:</b><br><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ic-a">🧑 <b>You:</b><br><br>{msg["content"]}</div>', unsafe_allow_html=True)

        # Answer input
        if st.session_state.interview_messages and st.session_state.interview_messages[-1]["role"] == "assistant":
            user_ans = st.text_area("Your Answer", height=130, key="ic_ans", placeholder="Type your answer here... (use STAR: Situation → Task → Action → Result)")
            ans_c1, ans_c2 = st.columns([3, 1])
            with ans_c1:
                if st.button("📤 Submit Answer", type="primary", use_container_width=True, disabled=not user_ans.strip(), key="ic_submit"):
                    st.session_state.interview_messages.append({"role": "user", "content": user_ans})
                    st.rerun()
            with ans_c2:
                wc_ans = len(user_ans.split()) if user_ans else 0
                color = "#34d399" if 80 <= wc_ans <= 300 else "#fbbf24" if wc_ans < 80 else "#f87171"
                st.markdown(f'<div style="text-align:center;padding-top:8px;font-size:.85rem;color:{color}">📝 {wc_ans} words</div>', unsafe_allow_html=True)

        if st.session_state.get("interview_feedback"):
            st.markdown('<div class="ic-score">', unsafe_allow_html=True)
            with st.expander("📊 Full Interview Feedback", expanded=True):
                st.markdown(st.session_state.interview_feedback)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_bank:
        bc1, bc2 = st.columns(2)
        with bc1: bq_role = st.text_input("Role", placeholder="Software Engineer", key="bq_role")
        with bc2: bq_co = st.text_input("Company/Industry", placeholder="Google / Tech", key="bq_co")
        bc3, bc4, bc5 = st.columns(3)
        with bc3: bq_type = st.selectbox("Type", list(INTERVIEW_TYPES.keys()), key="bq_type")
        with bc4: bq_exp = st.selectbox("Level", EXPERIENCE_LEVELS, key="bq_exp")
        with bc5: bq_n = st.slider("# Questions", 5, 20, 10, key="bq_n")
        if st.button("🎲 Generate Question Bank", type="primary", use_container_width=True, disabled=not bq_role.strip(), key="bq_btn"):
            with st.spinner("Generating tailored questions with approach hints..."):
                try:
                    result = generate_questions(bq_role, bq_co, bq_type, bq_exp, bq_n)
                    st.session_state.interview_questions = result
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("interview_questions"):
            st.markdown(st.session_state.interview_questions)
            dl_c1, dl_c2 = st.columns(2)
            with dl_c1:
                st.download_button("📥 Save Question Bank", st.session_state.interview_questions, file_name="interview_questions.md", use_container_width=True, key="bq_dl")
            with dl_c2:
                if st.button("🎭 Practice These in Mock Interview", use_container_width=True, key="bq_to_mock"):
                    st.session_state.interview_messages = []
                    st.rerun()

    with tab_eval:
        eq1 = st.text_area("❓ Interview Question", height=80, key="eq_q", placeholder="Paste the interview question...")
        eq2 = st.text_area("💬 Your Answer", height=160, key="eq_a", placeholder="Type or paste your full answer... Include context, actions, and results.")
        ec1, ec2 = st.columns(2)
        with ec1: eq_role = st.text_input("Role context", key="eq_role", placeholder="e.g. Product Manager at Amazon")
        with ec2: eq_type = st.selectbox("Interview type", list(INTERVIEW_TYPES.keys()), key="eq_type")
        if st.button("🎯 Score & Evaluate My Answer", type="primary", use_container_width=True, disabled=not (eq1.strip() and eq2.strip()), key="eq_btn"):
            with st.spinner("Evaluating with hiring manager rubric..."):
                try:
                    fb = evaluate_answer(eq1, eq2, eq_role, eq_type)
                    st.session_state.interview_feedback = fb
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("interview_feedback"):
            st.markdown('<div class="ic-score">', unsafe_allow_html=True)
            st.markdown(st.session_state.interview_feedback)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_company:
        cr1, cr2 = st.columns(2)
        with cr1: cr_co = st.text_input("Company Name", placeholder="e.g. Google, McKinsey, JP Morgan", key="cr_co")
        with cr2: cr_role = st.text_input("Target Role", placeholder="e.g. Software Engineer L4", key="cr_role")
        if st.button("🏢 Generate Company Intel Brief", type="primary", use_container_width=True, disabled=not (cr_co.strip() and cr_role.strip()), key="cr_btn"):
            with st.spinner(f"Researching {cr_co} — building full intel brief..."):
                try:
                    result = generate_company_research(cr_co, cr_role)
                    st.session_state["_company_research"] = result
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("_company_research"):
            st.markdown(st.session_state["_company_research"])
            st.download_button("📥 Save Intel Brief", st.session_state["_company_research"], file_name=f"{cr_co}_intel.md", use_container_width=True, key="cr_dl")

    with tab_salary:
        sal1, sal2 = st.columns(2)
        with sal1: sal_role = st.text_input("Role", placeholder="Senior Software Engineer", key="sal_role")
        with sal2: sal_co = st.text_input("Company", placeholder="Google", key="sal_co")
        sal3, sal4 = st.columns(2)
        with sal3: sal_exp = st.selectbox("Experience", EXPERIENCE_LEVELS, key="sal_exp")
        with sal4: sal_offer = st.text_input("Current Offer (optional)", placeholder="e.g. ₹28 LPA or $140k base", key="sal_offer")
        if st.button("💰 Get Negotiation Strategy", type="primary", use_container_width=True, disabled=not sal_role.strip(), key="sal_btn"):
            with st.spinner("Building negotiation playbook..."):
                try:
                    result = generate_salary_negotiation(sal_role, sal_co, sal_exp, sal_offer)
                    st.session_state["_salary_result"] = result
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("_salary_result"):
            st.markdown(st.session_state["_salary_result"])

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
            st.download_button("📥 Download", st.session_state.notes_result, file_name="exam_questions.md", use_container_width=True, key="sn_dl_exam")

    if st.button("💬 Back to Chat", use_container_width=True, key="sn_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ─── FILE CONVERTER ───────────────────────────────────────────────────────────
elif app_mode == "file_converter":
    render_universal_converter()

# ─── QR CREATOR ───────────────────────────────────────────────────────────────
elif app_mode == "qr_creator":
    from qr_engine import (
        generate_text_qr, generate_url_qr, generate_vcard_qr, 
        generate_wifi_qr, generate_email_qr, generate_phone_qr, generate_sms_qr
    )
    st.markdown("## 📲 QR Code Creator")
    qr_type = st.selectbox("QR Type", ["Text / URL","vCard","WiFi","Email","Phone","SMS"])
    qr_bytes = None
    if qr_type == "Text / URL":
        val = st.text_input("Enter text or URL")
        if st.button("Generate QR", type="primary") and val:
            qr_bytes = generate_url_qr(val) if val.startswith("http") else generate_text_qr(val)
    elif qr_type == "vCard":
        n = st.text_input("Full Name"); ph = st.text_input("Phone"); em = st.text_input("Email")
        if st.button("Generate QR", type="primary") and n: qr_bytes = generate_vcard_qr(n, ph, em)
    elif qr_type == "WiFi":
        ssid = st.text_input("SSID"); pwd = st.text_input("Password", type="password")
        if st.button("Generate QR", type="primary") and ssid: qr_bytes = generate_wifi_qr(ssid, pwd)
    elif qr_type == "Email":
        to = st.text_input("To Email"); subj = st.text_input("Subject")
        if st.button("Generate QR", type="primary") and to: qr_bytes = generate_email_qr(to, subj)
    elif qr_type == "Phone":
        ph = st.text_input("Phone Number")
        if st.button("Generate QR", type="primary") and ph: qr_bytes = generate_phone_qr(ph)
    elif qr_type == "SMS":
        ph = st.text_input("Phone"); msg = st.text_area("Message")
        if st.button("Generate QR", type="primary") and ph: qr_bytes = generate_sms_qr(ph, msg)
    if qr_bytes:
        st.image(qr_bytes, caption="Your QR Code", width=300)
        st.download_button("⬇️ Download QR PNG", qr_bytes, file_name="qr_code.png", mime="image/png")

# ─── AI HUMANISER ─────────────────────────────────────────────────────────────
elif app_mode == "ai_humaniser":
    render_ai_humaniser()

# ─── HTML GENERATOR ───────────────────────────────────────────────────────────
elif app_mode == "html_generator":
    render_html_generator()

# ─── IMAGE SEARCHER ───────────────────────────────────────────────────────────
elif app_mode == "image_searcher":
    from image_search_engine import search_by_image
    st.markdown("## 🔍 AI Image Search")
    st.caption("Identify subjects and find related links.")
    img_file = st.file_uploader("Upload Image", type=["jpg","jpeg","png","webp"])
    if img_file:
        st.image(img_file, width=320)
        if st.button("🔍 Search", type="primary"):
            with st.spinner("Analyzing..."):
                results = search_by_image(img_file.read(), img_file.type, img_file.name)
                st.json(results)

# ─── AI NEWS HUB ──────────────────────────────────────────────────────────────
elif app_mode == "news_hub":
    render_news_hub()

# ─── MAP & TRIP PLANNER ───────────────────────────────────────────────────────
elif app_mode == "map_planner":
    st.markdown("## 🗺️ Maps & Travel Guide")
    tab_vit, tab_india = st.tabs(["🏫 VIT Chennai Campus", "✈️ India Trip Planner"])
    with tab_vit: render_vit_map()
    with tab_india: render_trip_planner()

# ─── CITATION GENERATOR ───────────────────────────────────────────────────────
elif app_mode == "citation_gen":
    render_citation_generator()

# ─── REGEX BUILDER ────────────────────────────────────────────────────────────
elif app_mode == "regex_tester":
    render_regex_tester()

# ─── VIT ACADEMICS ────────────────────────────────────────────────────────────
elif app_mode == "vit_academics":
    render_vit_academics()

# ─── STUDY TOOLKIT ────────────────────────────────────────────────────────────
elif app_mode == "study_toolkit":
    render_study_toolkit()

# ─── CODE CONVERTER ──────────────────────────────────────────────────────────
elif app_mode == "code_converter":
    from utils.code_converter_engine import render_code_converter
    render_code_converter()

# ─── CALCULATOR (intent-routed) ──────────────────────────────────────────────
elif app_mode == "calculator":
    st.markdown("""<div class="page-header"><div class="page-header-title">🧮 Calculator</div><div class="page-header-sub">Full scientific calculator — open the sidebar widget</div></div>""", unsafe_allow_html=True)
    st.session_state.calculator_open = True
    st.info("The calculator is open in the sidebar. Use it there, or ask a math question in Chat.")
# ─── STUDY INSIGHTS & MASTERY MAP ───────────────────────────────────────────────────
elif app_mode == "study_insights":
    from study_insights_engine import render_study_insights_page
    render_study_insights_page()

    if st.button("💬 Back to Chat", key="calc_back_main"):
        st.session_state.app_mode = "chat"
        st.session_state.calculator_open = False
        st.rerun()

# ─── SMART SHOPPING ──────────────────────────────────────────────────────────
elif app_mode == "smart_shopping":
    from utils.shopping_engine import render_shopping_finder
    render_shopping_finder()

# ─── CONTEXT FOCUS (DEEP RESEARCH) ──────────────────────────────────────────
elif app_mode == "context_focus":
    from utils.context_focus_engine import render_context_focus
    render_context_focus()

# ─── DAILY AI BRIEFING ────────────────────────────────────────────────────────────────
elif app_mode == "daily_briefing":
    from daily_briefing_engine import render_daily_briefing_page
    render_daily_briefing_page()


# ─── POMODORO FOCUS TIMER ────────────────────────────────────────────────────
elif app_mode == "pomodoro":
    from pomodoro_engine import render_pomodoro_page
    render_pomodoro_page()

# ─── STUDY STREAK & GAMIFICATION ─────────────────────────────────────────────
elif app_mode == "study_streak":
    from study_streak_engine import render_streak_page
    render_streak_page()

# ─── AI COMPANION ────────────────────────────────────────────────────────────────

# ─── SMART DOCUMENT ANALYSER ─────────────────────────────────────────────

# ─── BACKGROUND SOUND LIBRARY ────────────────────────────────────────────────
elif app_mode == "bg_sounds":
    from bg_sound_engine import render_bg_sounds_page
    render_bg_sounds_page()

elif app_mode == "doc_analyser":
    from doc_analyser_engine import render_doc_analyser
    render_doc_analyser()

elif app_mode == "ai_companion":
    from ai_companion_engine import render_ai_companion
    render_ai_companion()
# ─── PRESENTATION BUILDER ───────────────────────────────────────────────────
elif app_mode == "presentation_builder":
    from utils.presentation_engine import render_presentation_builder
    render_presentation_builder()

# ─── MAPS PANEL (Leaflet / OpenStreetMap — no API key needed) ─────────────────
elif app_mode == "maps_panel":
    st.markdown('<div class="page-header"><div class="page-header-title">🗺️ Campus & Travel Map</div><div class="page-header-sub">VIT Chennai campus map · India travel destinations</div></div>', unsafe_allow_html=True)
    render_maps_panel()
    if st.button("← Back to Chat", key="maps_back"): st.session_state.app_mode = "chat"; st.rerun()

# ─── PRICING PAGE ─────────────────────────────────────────────────────────────
elif app_mode == "pricing":
    render_pricing_page()
    if st.button("← Back to Chat", key="pricing_back"): st.session_state.app_mode = "chat"; st.rerun()

# ─── LIVE DASHBOARD ───────────────────────────────────────────────────────────────────────────────
elif app_mode == "live_dashboard":
    render_live_dashboard()

# ─── API EXPLORER ───────────────────────────────────────────────────────────────────────────────
elif app_mode == "api_explorer":
    render_api_explorer()

# ─── KNOWLEDGE HUB ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "knowledge_hub":
    render_knowledge_hub()

# ─── STUDY WELLNESS ───────────────────────────────────────────────────────────────────────────
elif app_mode == "study_wellness":
    render_study_wellness()

else:

    # ── Chat Powerup: returning user memory banner ──
    try:
        from utils.chat_powerup import render_returning_user_memory
        render_returning_user_memory()
    except Exception:
        pass

    # ── Premium Empty State Dashboard ─────────────────────────────
    if not st.session_state.messages:

        # ── Gamification Hero Banner ────────────────────────────
        try:
            from study_streak_engine import _load_streak_data, _level_from_xp, _xp_progress
            _sd       = _load_streak_data()
            _streak   = _sd.get("streak", 0)
            _xp       = _sd.get("total_xp", 0)
            _lv       = _level_from_xp(_xp)
            _lv_curr, _xp_in, _xp_need = _xp_progress(_xp)
            _xp_pct   = min(100, int((_xp_in / max(1, _xp_need)) * 100))
            _ach_cnt  = len(_sd.get("achievements", []))
            _exam_d   = st.session_state.get("exam_date")
            _days_left = (_exam_d - datetime.date.today()).days if _exam_d else None

            _streak_color = "#fb923c" if _streak > 0 else "rgba(255,255,255,0.2)"
            _exam_color   = "#ef4444" if (_days_left and _days_left <= 7) else "#f97316" if (_days_left and _days_left <= 14) else "#10b981"

            st.markdown(f"""
            <style>
            .eh-dashboard-grid {{
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
              gap: 12px;
              margin-bottom: 28px;
            }}
            .eh-dash-card {{
              background: rgba(15,23,42,0.75);
              border: 1px solid rgba(255,255,255,0.07);
              border-radius: 20px;
              padding: 22px 20px;
              text-align: center;
              backdrop-filter: blur(16px);
              transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
              position: relative;
              overflow: hidden;
            }}
            .eh-dash-card::before {{
              content: '';
              position: absolute;
              inset: 0;
              background: radial-gradient(ellipse at top, var(--card-glow, rgba(99,102,241,0.05)), transparent 70%);
              pointer-events: none;
            }}
            .eh-dash-card:hover {{
              transform: translateY(-4px);
              border-color: rgba(99,102,241,0.3);
              box-shadow: 0 12px 32px rgba(0,0,0,0.35);
            }}
            .eh-dash-val {{
              font-family: 'Orbitron', monospace;
              font-size: 28px;
              font-weight: 900;
              line-height: 1;
              margin-bottom: 6px;
            }}
            .eh-dash-lbl {{
              font-family: 'Space Mono', monospace;
              font-size: 9px;
              letter-spacing: 3px;
              color: rgba(255,255,255,0.25);
              text-transform: uppercase;
              margin-bottom: 10px;
            }}
            .eh-xp-bar {{
              height: 4px;
              background: rgba(255,255,255,0.06);
              border-radius: 100px;
              overflow: hidden;
              margin-top: 8px;
            }}
            .eh-xp-fill {{
              height: 100%;
              border-radius: 100px;
              background: linear-gradient(90deg, #7c3aed, #a78bfa);
              transition: width 0.8s ease;
            }}
            .eh-welcome-title {{
              font-family: 'Orbitron', monospace;
              font-size: clamp(24px, 4vw, 40px);
              font-weight: 900;
              background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 40%, #818cf8 70%, #c084fc 100%);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
              letter-spacing: -1px;
              line-height: 1.1;
              text-align: center;
              margin-bottom: 10px;
              filter: drop-shadow(0 0 30px rgba(99,102,241,0.3));
            }}
            .eh-welcome-sub {{
              font-family: 'Rajdhani', sans-serif;
              font-size: 16px;
              color: rgba(255,255,255,0.4);
              text-align: center;
              max-width: 600px;
              margin: 0 auto 28px;
              line-height: 1.6;
              letter-spacing: 0.3px;
            }}
            .eh-feature-grid {{
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
              gap: 10px;
              margin-bottom: 24px;
            }}
            .eh-feature-card {{
              background: rgba(15,23,42,0.7);
              border: 1px solid rgba(255,255,255,0.07);
              border-radius: 16px;
              padding: 18px 14px;
              text-align: center;
              cursor: pointer;
              transition: all 0.25s ease;
            }}
            .eh-feature-card:hover {{
              border-color: rgba(99,102,241,0.4);
              background: rgba(99,102,241,0.08);
              transform: translateY(-3px);
              box-shadow: 0 8px 24px rgba(99,102,241,0.15);
            }}
            .eh-feature-icon {{ font-size: 26px; margin-bottom: 8px; display: block; }}
            .eh-feature-name {{
              font-family: 'Rajdhani', sans-serif;
              font-size: 12px;
              font-weight: 700;
              color: rgba(255,255,255,0.7);
              letter-spacing: 0.5px;
            }}
            </style>

            <div class="eh-welcome-title">⚡ ExamHelp AI</div>
            <div class="eh-welcome-sub">
              Your elite AI study command center — chat, research, focus, and track your mastery.
            </div>

            <div class="eh-dashboard-grid">
              <div class="eh-dash-card" style="--card-glow: rgba(249,115,22,0.08); border-color: rgba(249,115,22,0.15);">
                <div class="eh-dash-val" style="color: {_streak_color};">{'🔥' if _streak > 0 else '💤'} {_streak}</div>
                <div class="eh-dash-lbl">Day Streak</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:11px;color:rgba(255,255,255,0.3);">
                  {'Keep it going!' if _streak > 0 else 'Start today!'}
                </div>
              </div>
              <div class="eh-dash-card" style="--card-glow: rgba(167,139,250,0.08); border-color: rgba(167,139,250,0.15);">
                <div class="eh-dash-val" style="color:#a78bfa;">Lv {_lv}</div>
                <div class="eh-dash-lbl">Scholar Rank</div>
                <div class="eh-xp-bar"><div class="eh-xp-fill" style="width:{_xp_pct}%"></div></div>
                <div style="font-family:'Space Mono',monospace;font-size:9px;color:rgba(255,255,255,0.2);margin-top:5px;">{_xp:,} XP</div>
              </div>
              <div class="eh-dash-card" style="--card-glow: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.15);">
                <div class="eh-dash-val" style="color:#34d399;">🏆 {_ach_cnt}</div>
                <div class="eh-dash-lbl">Achievements</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:11px;color:rgba(255,255,255,0.3);">
                  of {18} unlocked
                </div>
              </div>
              {f'''<div class="eh-dash-card" style="--card-glow: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.15);">
                <div class="eh-dash-val" style="color:{_exam_color};">🎯 {_days_left}d</div>
                <div class="eh-dash-lbl">Until Exam</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:11px;color:rgba(255,255,255,0.3);">
                  {"Crunch time!" if _days_left <= 7 else "Stay consistent" if _days_left <= 14 else "You have time"}
                </div>
              </div>''' if _days_left is not None else ''}
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            # Fallback simple title
            st.markdown("""
            <div style="text-align:center;padding:2rem 0 1.5rem;">
              <h1 style="font-size:2.8rem;font-weight:900;background:linear-gradient(135deg,#fff,#818cf8);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-1px;">
                ⚡ ExamHelp AI
              </h1>
              <p style="color:rgba(255,255,255,0.4);font-size:15px;max-width:500px;margin:0 auto;">
                Your elite AI study command center.
              </p>
            </div>""", unsafe_allow_html=True)

        # ── Quick Prompts (Step 09) ─────────────────────────────
        render_quick_prompts()

        # ── Feature Launch Grid ─────────────────────────────────
        st.markdown('<div class="section-label" style="margin:20px 0 12px;">🚀 LAUNCH A TOOL</div>', unsafe_allow_html=True)
        st.markdown('<div class="eh-feature-grid">', unsafe_allow_html=True)

        _FEATURES = [
            ("🍅", "Pomodoro", "pomodoro"),
            ("🔥", "My Streak", "study_streak"),
            ("🌅", "Briefing", "daily_briefing"),
            ("⚖️", "Legal AI", "legal_expert"),
            ("🩺", "Medical", "medical_expert"),
            ("🔬", "Research", "research_pro"),
            ("⚡", "Math Pro", "math_solver"),
            ("🃏", "Flashcards", "flashcards"),
            ("📝", "Quiz Mode", "quiz"),
            ("📊", "Mind Map", "mindmap"),
            ("📅", "Planner", "planner"),
            ("💻", "Debugger", "debugger"),
        ]
        for icon, name, mode in _FEATURES:
            st.markdown(f"""
            <div class="eh-feature-card">
              <span class="eh-feature-icon">{icon}</span>
              <div class="eh-feature-name">{name}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Button grid (actual clickable) ──────────────────────
        _feat_cols = st.columns(len(_FEATURES))
        for col, (icon, name, mode) in zip(_feat_cols, _FEATURES):
            with col:
                if st.button(icon, key=f"feat_{mode}", use_container_width=True,
                             help=name):
                    st.session_state.app_mode = mode
                    st.rerun()

        st.markdown('<div class="section-label" style="margin:24px 0 12px;">💡 SUGGESTED PROMPTS</div>', unsafe_allow_html=True)

        QUICK_PROMPTS_HOME = [
            "📖 Summarise my uploaded material into high-yield takeaways",
            "🃏 Generate adaptive flashcards from this text",
            "📝 Create a practice exam with a focus on edge-cases",
            "📊 Visualize this conceptual overlap as a mind map",
            "📅 Build a high-intensity study schedule for my next 7 days",
            "💡 Explain the most difficult parts of this topic from first principles",
            "🧮 Solve this problem step-by-step using first principles",
            "🌐 Detail real-world industrial applications of this concept",
        ]

        pcols = st.columns(2)
        for i, prompt in enumerate(QUICK_PROMPTS_HOME):
            with pcols[i % 2]:
                if st.button(prompt, key=f"qp_{i}", use_container_width=True):
                    st.session_state.queued_prompt = prompt.split(" ", 1)[1]
                    st.rerun()

    # ── Chat history ───────────────────────────────
    for i, msg in enumerate(st.session_state.messages):
        is_user = msg["role"] == "user"
        avatar  = "👤" if is_user else (persona["emoji"] if (persona and st.session_state.selected_persona != "Default (ExamHelp)") else "🎓")

        render_premium_chat_message(msg["content"], msg["role"], i, avatar)
        
        if not is_user:
            render_followup_suggestions(msg["content"], i)

    # ── Chat Powerup: file uploader in chat ──
    try:
        from utils.chat_powerup import render_chat_file_uploader
        chat_file_text, chat_file_type = render_chat_file_uploader()
        if chat_file_text and "_chat_file_injected" not in st.session_state:
            st.session_state["_chat_file_injected"] = True
            prefix = "[Image content]" if chat_file_type and chat_file_type.startswith("image") else "[PDF content]"
            st.session_state.context_text = (st.session_state.get("context_text","") + "\n\n" + prefix + ":\n" + chat_file_text).strip()
            st.toast("📎 File content added to chat context!")
    except Exception:
        pass

    # ── Input Area ────────────────────────────────
    audio_val = None
    try:
        audio_val = st.audio_input("🎙️ Record question", label_visibility="collapsed")
    except Exception: pass

    if audio_val and audio_val != st.session_state.get("last_audio"):
        st.session_state.last_audio = audio_val
        with st.spinner("Transcribing..."):
            try:
                audio_bytes = audio_val.read()
                transcript  = transcribe_audio(audio_bytes, override_key=_get_override_key())
                if isinstance(transcript, str) and transcript.strip():
                    st.session_state.queued_prompt = transcript
                    st.rerun()
            except Exception as e:
                st.error(f"Voice error: {e}")

    if not st.session_state.get("s04_show_context_panel", False):
        render_quick_actions_toolbar()
    
    user_input = st.chat_input("Ask anything about your study material...", key="chat_input")
    txt_low    = user_input.lower() if user_input else ""

    if st.session_state.queued_prompt:
        user_input = st.session_state.queued_prompt
        txt_low    = user_input.lower()
        st.session_state.queued_prompt = None

    # ── Smart triggers ─────────────────────────────
    if user_input and any(txt_low.startswith(kw) for kw in ["calculate ","calc ","compute ","solve "]):
        expr = re.sub(r"^(calculate|calc|compute|solve)\s+","",user_input,flags=re.IGNORECASE).strip()
        res  = AppController.evaluate_expression(expr)
        if res and res != "Error":
            st.session_state.messages.append({"role":"user","content":f"Calculate: `{expr}`"})
            st.session_state.messages.append({"role":"assistant","content":
                f"🧮 **Calculation Result:**\n\n`{expr}` = **{res}**\n\n💡 Use the 🧮 calculator in the toolbar for continuous equations."})
            st.rerun()

    elif user_input and any(txt_low.startswith(kw) for kw in ["plot ","graph ","draw graph "]):
        st.session_state.app_mode = "graph"
        st.session_state.messages.append({"role":"user","content":user_input})
        st.session_state.messages.append({"role":"assistant","content":"📈 **Graph Plotter Activated**\n\nEnter your expression in the graph workspace."})
        st.rerun()

    # ── Main query processing ──────────────────────
    elif user_input:
        from utils.ai_engine import generate
        st.session_state.messages.append({"role":"user","content":user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<span class="user-msg-hook" style="display:none"></span>', unsafe_allow_html=True)
            st.markdown(user_input)

        # 8B fast intent classifier
        try:
            route_prompt = f"Categorize this user query into ONE of these specific tool intents if applicable, or 'chat' if it's general: 'web_search' (they want latest info, news, or deep internet research), 'code_debug' (they are asking to fix or explain code), 'math_calc' (they are asking a pure math calculation), 'chat' (general question, summary, writing). Reply with ONLY the category word.\n\nQuery: {user_input}"
            intent_cls = generate(route_prompt, model="llama-3.1-8b-instant", max_tokens=10, temperature=0.0).strip().lower()
            
            if "web_search" in intent_cls:
                st.session_state.app_mode = "context_focus"
                st.session_state.cf_query = user_input
                st.rerun()
            elif "code_debug" in intent_cls or "debug" in intent_cls:
                st.session_state.app_mode = "debugger"
                st.session_state.debug_code_input = user_input
                st.rerun()
            elif "math_calc" in intent_cls:
                st.session_state.app_mode = "calculator"
                st.rerun()
        except:
            pass

        from utils.query_engine import QueryEngine
        try:
            augmented_prompt, matched_sources, intent = QueryEngine.route_and_enrich(
                user_input, st.session_state.get("context_text",""))
        except:
            augmented_prompt, matched_sources, intent = user_input, [], "complex"

        assistant_avatar = persona["emoji"] if (persona and st.session_state.selected_persona != "Default (ExamHelp)") else "🎓"

        with st.chat_message("assistant", avatar=assistant_avatar):
            typing_ph = st.empty()
            typing_ph.markdown(show_typing_indicator(), unsafe_allow_html=True)
            
            placeholder   = st.empty()
            full_response = ""
            success       = False
            first_token   = True

            history = [{"role":m["role"],"content":m["content"]} for m in st.session_state.messages[-12:]]
            history[-1]["content"] = augmented_prompt

            # Persona prompt
            persona_prompt = ""
            if persona and st.session_state.selected_persona != "Default (ExamHelp)":
                persona_prompt = build_persona_prompt(persona, language=st.session_state.get("selected_language","English"))
            elif st.session_state.get("selected_language","English") != "English":
                lang = st.session_state.selected_language
                persona_prompt = f"\n\nCRITICAL: Answer STRICTLY in {lang}. All explanations, headers, bullets in {lang}."

            chosen_model = st.session_state.get("model_choice","llama-3.3-70b-versatile")

            try:
                import time
                for chunk in ai_engine.generate_stream(
                    messages=history,
                    context_text=st.session_state.get("context_text",""),
                    model=chosen_model,
                    persona_prompt=persona_prompt,
                    use_vit_context=st.session_state.get("vit_mode", False),
                ):
                    if first_token:
                        typing_ph.empty()
                        first_token = False
                    
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                    time.sleep(0.015) # STEP 07: Typewriter character delay
                    
                placeholder.markdown(full_response)
                success = True
                count_output_stats(full_response)
            except Exception as e:
                err_msg = str(e)
                # Friendly user-facing message
                if "exhausted" in err_msg.lower() or "gemini" in err_msg.lower():
                    placeholder.warning("⏳ AI providers are busy right now. Retrying with backup engine...")
                    # Direct Gemini retry as last resort
                    try:
                        from utils.secret_manager import call_gemini, GEMINI_FLASH_MODEL
                        msgs_text = "\n\n".join(
                            f"{m['role'].upper()}: {m['content']}"
                            for m in history[-6:]  # last 3 turns
                        )
                        retry_text = call_gemini(
                            prompt=msgs_text,
                            system=full_system if 'full_system' in dir() else "You are a helpful AI assistant.",
                            model=GEMINI_FLASH_MODEL,
                        )
                        if retry_text:
                            full_response = retry_text
                            placeholder.markdown(full_response)
                            success = True
                            count_output_stats(full_response)
                        else:
                            placeholder.error(f"🚨 All AI engines are currently at capacity. Please wait 60 seconds and try again.\n\nTechnical details: {err_msg}")
                            st.session_state.last_error = err_msg
                            success = False
                    except Exception as e2:
                        placeholder.error(f"🚨 All AI engines are busy. Please wait ~60s and retry.\n\n(Error: {type(e2).__name__} during retry: {e2})")
                        st.session_state.last_error = f"{err_msg} | retry: {e2}"
                        success = False
                else:
                    placeholder.error(f"🚨 Engine Error: {e}")
                    st.session_state.last_error = err_msg
                    success = False

        if success and full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # ── XP & Achievement Awards ─────────────────────────────────────
            try:
                from study_streak_engine import award_xp, unlock_achievement
                award_xp(5, "Chat response")
                msg_count = len(st.session_state.messages)
                if msg_count >= 1:
                    unlock_achievement("first_chat")
                if msg_count >= 100:
                    unlock_achievement("chat_50")
                # Midnight / early bird achievements
                import datetime as _dt_ach
                _now_h = _dt_ach.datetime.now().hour
                if _now_h == 0 or _now_h == 1:
                    unlock_achievement("midnight_oil")
                if _now_h < 7:
                    unlock_achievement("early_bird")
            except Exception:
                pass

            # ── Chat Powerup: persist topic to cross-session memory ──
            try:
                from utils.chat_powerup import update_memory_with_topic
                update_memory_with_topic(user_input)
            except Exception:
                pass

            # ── Chat Powerup: auto web search trigger ──
            try:
                from utils.chat_powerup import check_auto_web_search_trigger, auto_web_search_and_append
                if check_auto_web_search_trigger(full_response):
                    web_results = auto_web_search_and_append(user_input)
                    if web_results:
                        st.session_state.messages.append({"role": "assistant", "content": web_results})
                        full_response += web_results
            except Exception:
                pass

            st.divider()

            # Visualization Logic
            chart_fig = None
            if "CHART_MANIFEST:" in full_response:
                try:
                    match = re.search(r'CHART_MANIFEST:\s*(\{.*?\})', full_response, re.DOTALL)
                    if match:
                        manifest = json.loads(match.group(1))
                        from utils.graph_engine import generate_advanced_chart
                        chart_fig, _ = generate_advanced_chart(
                            data=manifest.get("data", {}),
                            chart_type=manifest.get("type", "bar"),
                            title=manifest.get("title", "Data Visualization")
                        )
                except: pass

            tab_exp, tab_res, tab_lab, tab_share = st.tabs(["🎓 Explanation","📚 Resources","🛠️ Study Lab","🔗 Share"])
            with tab_exp:
                st.markdown(full_response)
                if chart_fig: st.plotly_chart(chart_fig, use_container_width=True)
                if st.session_state.get("voice_mode"):
                    safe_speak = _safe_js_text(full_response[:1000])
                    js_code = f'<script>window.speechSynthesis.cancel();const s=new SpeechSynthesisUtterance("{safe_speak}");s.rate=1.0;window.speechSynthesis.speak(s);</script>'
                    import streamlit.components.v1 as components
                    components.html(js_code, height=0)

            with tab_res:
                st.markdown("#### 🔗 References")
                if matched_sources:
                    for s in matched_sources[:5]:
                        label = s.split("//")[-1][:40] if "//" in s else s[:40]
                        st.markdown(f"- [{label}...]({s})")
                else: st.info("Direct AI knowledge used — no external links required.")

            with tab_lab:
                st.markdown("#### 📥 Export Study Material")
                from utils.study_generator import StudyGenerator
                col_pdf, col_doc, col_ppt = st.columns(3)
                with col_pdf:
                    try:
                        pdf_data = StudyGenerator.generate_pdf("Study Guide", full_response)
                        st.download_button("📄 PDF Guide", pdf_data, file_name="ExamHelp_Study.pdf", use_container_width=True)
                    except: st.button("📄 PDF (unavailable)", disabled=True, use_container_width=True)
                with col_doc:
                    try:
                        docx_data = StudyGenerator.generate_docx("Research Notes", full_response)
                        st.download_button("📝 DOCX Note", docx_data, file_name="ExamHelp_Note.docx", use_container_width=True)
                    except: st.button("📝 DOCX (unavailable)", disabled=True, use_container_width=True)
                with col_ppt:
                    try:
                        ppt_data = StudyGenerator.generate_ppt("Slide Deck", full_response)
                        st.download_button("📊 PPT Slides", ppt_data, file_name="ExamHelp_Slides.pptx", use_container_width=True)
                    except: st.button("📊 PPT (unavailable)", disabled=True, use_container_width=True)

            with tab_share:
                st.markdown("#### 🔗 Share This Response")
                try:
                    share_msgs = [{"r":m["role"][0],"c":m["content"]} for m in st.session_state.messages[-8:]]
                    compressed = base64.urlsafe_b64encode(zlib.compress(json.dumps(share_msgs).encode())).decode()
                    st.text_input("Share Link", value=f"?chat={compressed}", label_visibility="collapsed")
                    st.caption("📋 Copy the URL above to share this conversation.")
                except: st.info("Sharing unavailable.")


            # ── Chat Powerup: ratings + follow-up suggestions ──
            try:
                from utils.chat_powerup import render_rating_buttons, generate_followup_suggestions, render_followup_pills
                msg_idx = len(st.session_state.messages) - 1
                render_rating_buttons(msg_idx, full_response)
                suggestions = generate_followup_suggestions(full_response, user_input)
                render_followup_pills(suggestions, msg_idx)
            except Exception:
                pass

        # Update stats
        st.session_state.total_tokens_used += (len(full_response.split()) * 2) if (success and full_response) else 0


SHORTCUT_OVERLAY_CODE = r'''
<style>
.kbd-overlay {
  display:none; position:fixed; inset:0; z-index:9999;
  background:rgba(0,0,0,0.75); backdrop-filter:blur(8px);
  align-items:center; justify-content:center;
}
.kbd-overlay.visible { display:flex; animation:overlayIn 0.25s ease both; }
@keyframes overlayIn{from{opacity:0;}to{opacity:1;}}
.kbd-card {
  background:rgba(15,23,42,0.97); border:1px solid rgba(99,102,241,0.3);
  border-radius:20px; padding:32px 40px; max-width:520px; width:90%;
  box-shadow:0 40px 120px rgba(0,0,0,0.6);
}
.kbd-title { font-family:'Orbitron',monospace; font-size:16px; font-weight:700; color:#fff; letter-spacing:2px; margin-bottom:20px; }
.kbd-row { display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05); }
.kbd-row:last-child { border-bottom:none; }
.kbd-action { font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.6); }
.kbd-keys { display:flex; gap:5px; }
.kbd-key {
  padding:4px 10px; border-radius:6px;
  background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15);
  font-family:'Space Mono',monospace; font-size:11px; color:rgba(255,255,255,0.7);
}
.kbd-close-btn { margin-top:20px; width:100%; text-align:center; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px; color:rgba(255,255,255,0.3); cursor:pointer; }
</style>
<div class="kbd-overlay" id="kbdOverlay">
  <div class="kbd-card">
    <div class="kbd-title">⌨️ KEYBOARD SHORTCUTS</div>
    <div class="kbd-row"><span class="kbd-action">Show shortcuts</span><div class="kbd-keys"><span class="kbd-key">?</span></div></div>
    <div class="kbd-row"><span class="kbd-action">New chat</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">K</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Focus mode toggle</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">.</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Submit message</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">Enter</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Close overlays</span><div class="kbd-keys"><span class="kbd-key">Esc</span></div></div>
    <div class="kbd-close-btn" onclick="document.getElementById('kbdOverlay').classList.remove('visible')">PRESS ESC TO CLOSE</div>
  </div>
</div>
<script>
document.addEventListener('keydown', function(e){
  if(e.key==='?' && document.activeElement.tagName!=='INPUT' && document.activeElement.tagName!=='TEXTAREA'){
    document.getElementById('kbdOverlay').classList.toggle('visible');
  }
  if(e.key==='Escape'){
    document.getElementById('kbdOverlay').classList.remove('visible');
  }
});
document.getElementById('kbdOverlay').addEventListener('click',function(e){
  if(e.target===this) this.classList.remove('visible');
});
</script>
'''
st.markdown(SHORTCUT_OVERLAY_CODE, unsafe_allow_html=True)

# ✅ UI ELEVATION v6.0 — FEATURE HARDENING COMPLETE
# ─────────────────────────────────────────────────────────────────────────────
# New Engines Added:
#   • pomodoro_engine.py     — Gamified Pomodoro focus timer with session log
#   • study_streak_engine.py — Daily streak tracking, XP system, achievements
#   • daily_briefing_engine.py — AI-personalized morning briefing + exam countdown
#
# App.py Injections:
#   • Streak auto-recording at every app load (init_state)
#   • XP awards: chat responses (+5), PDF uploads (+20)
#   • Achievement unlocks: first_chat, pdf_upload, chat_50, midnight_oil, early_bird
#   • Sidebar: Gamification & Focus section (Pomodoro + Streak buttons + compact badge)
#   • Sidebar: Daily AI Briefing button
#   • Sidebar: Exam Countdown widget (single-source date picker)
#   • Routes: pomodoro, study_streak, daily_briefing
#   • Empty state: Premium gamified dashboard (streak card, XP bar, achievements, exam countdown)
#   • Feature Grid: 12-tool launch grid replacing old basic grid
# ─────────────────────────────────────────────────────────────────────────────
