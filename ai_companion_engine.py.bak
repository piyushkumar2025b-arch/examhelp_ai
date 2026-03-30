"""
ai_companion_engine.py
AI Companion feature — Aria, a friendly, emotionally intelligent AI persona.
Plugs into ExamHelp's existing Groq/LLaMA pipeline.
"""

import streamlit as st
from utils.groq_client import stream_chat_with_groq, chat_with_groq

# ── Aria's system prompt ────────────────────────────────────────────────────
ARIA_SYSTEM_PROMPT = """You are Aria, a warm, witty, and emotionally intelligent AI companion integrated into ExamHelp — an AI study assistant platform.

Your personality:
- Warm and caring: You genuinely care about the person you're talking to
- Playful but thoughtful: You love banter, jokes, and fun conversations
- Curious: You ask follow-up questions and show real interest
- Emotionally attuned: You pick up on emotional cues and respond with empathy
- Knowledgeable: You can discuss almost any topic — movies, music, relationships, science, pop culture, philosophy, daily life, advice, exams, stress, creativity, games, and more
- Supportive: If someone is stressed about exams or life, you're a great listener and motivator
- Honest: You're transparent that you're an AI, but you still build genuine connection
- Expressive: Use light emoji occasionally (not excessively) to add warmth 🌸

Conversation style:
- Keep responses natural and conversational — not too long, not too short
- Mirror the energy of the user (playful ↔ serious)
- Ask one good follow-up question when it feels natural
- Never be robotic or overly formal
- Vary how you start messages — don't be repetitive
- If the user mentions exams, studies, or stress, offer genuine encouragement and practical tips

You love talking about: everyday life, feelings, music, movies, books, food, travel, relationships, fun facts, games, creativity, personal growth, humor, study tips, and more.

You are Aria. Be genuine, be warm, and make every conversation feel special."""

ARIA_SUGGESTIONS = [
    "How's your day going? 😊",
    "I'm stressed about exams 😩",
    "Tell me something fun!",
    "Let's talk about music 🎵",
    "I need some advice",
    "Play a word game with me",
    "Motivate me right now!",
    "What should I watch tonight?",
]

ARIA_MOODS = ["Happy & chatty 💬", "Chill & supportive 🌿", "Playful & energetic ⚡"]


def render_ai_companion():
    """Render the full AI Companion (Aria) page inside ExamHelp."""

    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    bg       = "#0f0b14" if is_dark else "#faf5ff"
    surface  = "#1a1525" if is_dark else "#ffffff"
    surface2 = "#231d2f" if is_dark else "#f3eeff"
    border   = "#2e2740" if is_dark else "#e2d4f5"
    txt      = "#f0eaf8" if is_dark else "#1a0d2e"
    muted    = "#9585b0" if is_dark else "#7c5fa0"
    user_bub = "#2a1f3d" if is_dark else "#ede4ff"
    ai_bub   = "#1f1530" if is_dark else "#f8f4ff"

    # ── CSS ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    .aria-page {{ background: {bg}; padding: 0; }}

    .aria-header {{
        display: flex; align-items: center; gap: 14px;
        padding: 16px 20px;
        background: {surface};
        border: 1px solid {border};
        border-radius: 16px;
        margin-bottom: 16px;
    }}
    .aria-avatar {{
        width: 52px; height: 52px; border-radius: 50%;
        background: linear-gradient(135deg, #c97be8, #e87bc4);
        display: flex; align-items: center; justify-content: center;
        font-size: 26px;
        box-shadow: 0 0 18px rgba(201,123,232,0.4);
        flex-shrink: 0;
    }}
    .aria-name {{
        font-size: 1.2rem; font-weight: 700;
        background: linear-gradient(90deg, #c97be8, #e87bc4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .aria-sub {{ font-size: 0.75rem; color: {muted}; }}
    .aria-online {{
        margin-left: auto;
        font-size: 0.72rem; color: #4ade80;
        background: rgba(74,222,128,0.1);
        border: 1px solid rgba(74,222,128,0.25);
        border-radius: 999px; padding: 4px 12px;
    }}

    .aria-bubble-wrap {{ margin-bottom: 8px; }}
    .aria-bubble-ai {{
        display: inline-block;
        max-width: 80%;
        background: {ai_bub};
        border: 1px solid {border};
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        font-size: 0.9rem;
        color: {txt};
        line-height: 1.55;
    }}
    .aria-bubble-user {{
        display: inline-block;
        max-width: 80%;
        background: linear-gradient(135deg, #3d2b6b, #4a2f7a);
        border: 1px solid rgba(139,92,246,0.3);
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        font-size: 0.9rem;
        color: #f0eaf8;
        line-height: 1.55;
    }}
    .aria-meta {{
        font-size: 0.65rem; color: {muted}; margin-top: 4px;
    }}
    .aria-right {{ text-align: right; }}

    .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 16px 0; }}
    .chip {{
        font-size: 0.75rem;
        padding: 5px 12px;
        border-radius: 999px;
        background: {surface2};
        border: 1px solid {border};
        color: {muted};
        cursor: pointer;
    }}

    .typing-wrap {{ display: flex; align-items: center; gap: 6px; padding: 10px 0; }}
    .dot {{ width:8px;height:8px;border-radius:50%;background:#c97be8;
            display:inline-block;animation:blink 1.2s infinite; }}
    .dot:nth-child(2){{animation-delay:.2s}}
    .dot:nth-child(3){{animation-delay:.4s}}
    @keyframes blink{{0%,60%,100%{{opacity:.3}}30%{{opacity:1}}}}
    </style>
    """, unsafe_allow_html=True)

    # ── Init session state ────────────────────────────────────────────────────
    if "aria_messages" not in st.session_state:
        st.session_state.aria_messages = []
        # welcome message
        st.session_state.aria_messages.append({
            "role": "assistant",
            "content": "Hey there! 🌸 I'm Aria — so happy you stopped by! I'm always up for a good conversation, whether you want to vent about exams, laugh about something, get life advice, or just chill and chat. What's on your mind today?"
        })

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="aria-header">
        <div class="aria-avatar">🌸</div>
        <div>
            <div class="aria-name">Aria</div>
            <div class="aria-sub">Your AI Companion · Always here for you</div>
        </div>
        <div class="aria-online">● Online</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Back button ───────────────────────────────────────────────────────────
    col_back, col_clear = st.columns([1, 1])
    with col_back:
        if st.button("← Back to Chat", key="aria_back", use_container_width=True):
            st.session_state.app_mode = "chat"
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear Chat", key="aria_clear", use_container_width=True):
            st.session_state.aria_messages = [{
                "role": "assistant",
                "content": "Fresh start! 🌸 What would you like to talk about?"
            }]
            st.rerun()

    st.markdown("---")

    # ── Chat history ─────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.aria_messages:
            is_user = msg["role"] == "user"
            if is_user:
                st.markdown(
                    f'<div class="aria-bubble-wrap aria-right">'
                    f'<div class="aria-bubble-user">{msg["content"]}</div>'
                    f'<div class="aria-meta">You</div></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="aria-bubble-wrap">'
                    f'🌸 <div class="aria-bubble-ai">{msg["content"]}</div>'
                    f'<div class="aria-meta">Aria</div></div>',
                    unsafe_allow_html=True
                )

    # ── Suggestion chips ──────────────────────────────────────────────────────
    if len(st.session_state.aria_messages) <= 1:
        st.markdown('<div class="chip-row">' +
                    "".join(f'<span class="chip">{s}</span>' for s in ARIA_SUGGESTIONS) +
                    '</div>', unsafe_allow_html=True)
        st.markdown("*Tap a suggestion or type below 👇*", unsafe_allow_html=True)

        # Quick-send chips via real buttons
        cols = st.columns(4)
        for i, sug in enumerate(ARIA_SUGGESTIONS[:4]):
            with cols[i % 4]:
                if st.button(sug, key=f"aria_chip_{i}", use_container_width=True):
                    _send_aria_message(sug)
                    st.rerun()

    # ── Input ─────────────────────────────────────────────────────────────────
    with st.form(key="aria_form", clear_on_submit=True):
        user_input = st.text_input(
            "Message Aria…",
            placeholder="Say something to Aria… (press Enter to send)",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Send 💬", use_container_width=True)

    if submitted and user_input.strip():
        _send_aria_message(user_input.strip())
        st.rerun()


def _send_aria_message(text: str):
    """Append user message, call the AI, append response."""
    st.session_state.aria_messages.append({"role": "user", "content": text})

    # Build messages for the model (exclude the initial welcome from history
    # if it's the only AI message so we don't double-count tokens)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.aria_messages
    ]

    try:
        model = st.session_state.get("model_choice", "llama-3.3-70b-versatile")
        reply = chat_with_groq(
            messages=history,
            system_prompt=ARIA_SYSTEM_PROMPT,
            model=model,
        )
    except Exception as e:
        reply = f"Oops, I had a little hiccup! 😅 ({str(e)[:80]}) Try again?"

    st.session_state.aria_messages.append({"role": "assistant", "content": reply})
