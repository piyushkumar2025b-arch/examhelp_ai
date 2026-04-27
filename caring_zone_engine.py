"""
caring_zone_engine.py
═══════════════════════════════════════════════════════════════
ExamHelp AI — Caring Zone 💚
A warm, healing space powered by an empathetic AI companion.
Free APIs used:
  • Unsplash Source (free random images, no key needed)
  • Affirmations API: https://www.affirmations.dev/
  • Forismatic Quotes API (http, no key)
  • Open Library covers (book-healing vibes)
  • Public Lorem Picsum for mood boards
  • ZenQuotes (free tier, no key)
═══════════════════════════════════════════════════════════════
"""

import streamlit as st
import random
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime

# ─── Companion Persona ─────────────────────────────────────
COMPANION = {
    "name": "Aria",
    "emoji": "🌸",
    "color_a": "#f472b6",
    "color_b": "#8b5cf6",
    "glow": "rgba(244,114,182,0.45)",
    "border": "rgba(244,114,182,0.25)",
}

# ─── Healing messages pool ──────────────────────────────────
HEALING_MESSAGES = [
    "Hey there, beautiful soul 🌸 I'm Aria — and I'm SO glad you're here right now. You don't need to have it all figured out. You just need to breathe. 💛",
    "You showed up today — and that? That's already incredibly brave. 🦋 I see you. I'm right here with you.",
    "Whatever you're carrying right now 💪 you don't have to carry it alone. I'm here. Always. Just talk to me 🌿",
    "Listen — you are doing SO much better than you think 🌟 Your brain sometimes lies to you. I'm here to remind you of the truth 💕",
    "Take a deep breath with me 🌬️ In... and out. You're safe here. This is your space, your moment. 🌸",
]

# ─── Mood options ───────────────────────────────────────────
MOODS = {
    "😔 Sad / Low": {
        "color": "#818cf8",
        "prompt_hint": "The user feels sad and low. Be extra warm, validating, and gently uplifting.",
        "images": ["https://picsum.photos/seed/calm1/800/500", "https://picsum.photos/seed/peace2/800/500"],
        "unsplash": "https://source.unsplash.com/800x500/?calm,peaceful,nature",
    },
    "😰 Anxious / Stressed": {
        "color": "#f59e0b",
        "prompt_hint": "The user is anxious and stressed. Be grounding, calm, and reassuring. Give practical breathing tips.",
        "images": ["https://picsum.photos/seed/breathe1/800/500", "https://picsum.photos/seed/serene/800/500"],
        "unsplash": "https://source.unsplash.com/800x500/?breathe,zen,meditation",
    },
    "😤 Frustrated / Angry": {
        "color": "#ef4444",
        "prompt_hint": "The user is frustrated or angry. Validate their feelings fully, help them release tension, and guide them back to calm.",
        "images": ["https://picsum.photos/seed/release1/800/500", "https://picsum.photos/seed/sky/800/500"],
        "unsplash": "https://source.unsplash.com/800x500/?sky,freedom,open",
    },
    "😞 Heartbroken": {
        "color": "#ec4899",
        "prompt_hint": "The user is heartbroken. Be deeply compassionate, nurturing, and remind them of their worth.",
        "images": ["https://picsum.photos/seed/heart1/800/500", "https://picsum.photos/seed/warmth/800/500"],
        "unsplash": "https://source.unsplash.com/800x500/?flowers,warmth,healing",
    },
    "😴 Exhausted / Burned out": {
        "color": "#6366f1",
        "prompt_hint": "The user is exhausted and burned out. Be gentle, encourage rest, and validate their need to slow down.",
        "images": ["https://picsum.photos/seed/rest1/800/500", "https://picsum.photos/seed/cozy/800/500"],
        "unsplash": "https://source.unsplash.com/800x500/?cozy,rest,sleep",
    },
    "🙂 Okay / Neutral": {
        "color": "#10b981",
        "prompt_hint": "The user feels neutral or okay. Be warm, engaging, and help them find a small spark of joy.",
        "images": ["https://picsum.photos/seed/bright1/800/500", "https://picsum.photos/seed/happy2/800/500"],
        "unsplash": "https://source.unsplash.com/800x500/?happy,sunshine,bright",
    },
    "😊 Good / Happy": {
        "color": "#f59e0b",
        "prompt_hint": "The user feels good and happy! Celebrate with them, amplify the joy, spread more positivity.",
        "images": ["https://picsum.photos/seed/joy1/800/500", "https://picsum.photos/seed/sunshine/800/500"],
        "unsplash": "https://source.unsplash.com/800x500/?joy,celebration,sunshine",
    },
}

# ─── Affirmation starters ───────────────────────────────────
AFFIRMATIONS = [
    "You are enough, exactly as you are right now 💛",
    "Your feelings are valid. Every single one of them 🌊",
    "You have survived every hard day so far — 100% success rate 💪",
    "You are not your worst moment. You are so much more 🌟",
    "Rest is not lazy. Rest is revolutionary 🌙",
    "Your sensitivity is a superpower, not a weakness 🦋",
    "You are allowed to take up space. You belong here 🌸",
    "Small progress is still progress — celebrate it 🎉",
    "It's okay to not be okay. And it's okay to ask for help 💚",
    "You are someone's reason to smile without even knowing it 🌺",
    "Growth happens in the quiet moments too 🌱",
    "You didn't come this far to only come this far 🔥",
    "Your story isn't over. The best chapters are still being written ✨",
    "You are loved more than you currently realize 💕",
    "Today you don't have to be perfect. You just have to be you 🌈",
]

# ─── Breathing exercise ─────────────────────────────────────
BREATHING_STEPS = [
    ("Breathe IN 🌬️", 4, "#6366f1"),
    ("Hold 🤍", 4, "#f472b6"),
    ("Breathe OUT 💨", 6, "#10b981"),
    ("Hold 🌑", 2, "#f59e0b"),
]

# ─── Healing playlists (YouTube embeds - no key needed) ─────
PLAYLISTS = [
    {"name": "🎵 Lo-Fi Calm", "url": "https://www.youtube.com/embed/jfKfPfyJRdk", "desc": "Peaceful study beats"},
    {"name": "🌿 Nature Sounds", "url": "https://www.youtube.com/embed/1ZYbU82GVz4", "desc": "Forest & rain ambiance"},
    {"name": "🧘 Meditation", "url": "https://www.youtube.com/embed/inpok4MKVLM", "desc": "5-min guided calm"},
    {"name": "☀️ Morning Vibes", "url": "https://www.youtube.com/embed/5qap5aO4i9A", "desc": "Positive energy"},
]

# ─── Free image gallery themes ──────────────────────────────
IMAGE_THEMES = [
    {"label": "🌸 Flowers", "seed": "flowers", "query": "flowers,bloom"},
    {"label": "🌊 Ocean", "seed": "ocean", "query": "ocean,waves,sea"},
    {"label": "🌲 Forest", "seed": "forest", "query": "forest,trees,nature"},
    {"label": "🌅 Sunrise", "seed": "sunrise", "query": "sunrise,dawn,sky"},
    {"label": "🏔️ Mountains", "seed": "mountains", "query": "mountains,peak,snow"},
    {"label": "🌃 Night Sky", "seed": "stars", "query": "stars,galaxy,night"},
    {"label": "🍵 Cozy", "seed": "cozy", "query": "cozy,tea,warmth"},
    {"label": "🌈 Rainbow", "seed": "rainbow", "query": "rainbow,colorful,hope"},
]


def _fetch_affirmation() -> str:
    """Fetch a live affirmation from the free API."""
    try:
        req = urllib.request.Request(
            "https://www.affirmations.dev/",
            headers={"Accept": "application/json", "User-Agent": "ExamHelp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            aff = data.get("affirmation", "")
            if aff:
                return aff
    except Exception:
        pass
    return random.choice(AFFIRMATIONS)


def _fetch_zen_quote() -> dict:
    """Fetch a healing quote from ZenQuotes (free, no key)."""
    try:
        req = urllib.request.Request(
            "https://zenquotes.io/api/random",
            headers={"User-Agent": "ExamHelp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            if data and len(data) > 0:
                return {"quote": data[0].get("q", ""), "author": data[0].get("a", "")}
    except Exception:
        pass
    fallbacks = [
        {"quote": "You are enough. You have always been enough.", "author": "Unknown"},
        {"quote": "The present moment is the only moment available to us.", "author": "Thich Nhat Hanh"},
        {"quote": "Be gentle with yourself. You are a child of the universe.", "author": "Max Ehrmann"},
        {"quote": "Rest and self-care are so important. When you take time to replenish your spirit, it allows you to serve others from the overflow.", "author": "Eleanor Brownn"},
        {"quote": "It's okay to not be okay as long as you are not giving up.", "author": "Karen Salmansohn"},
    ]
    return random.choice(fallbacks)


def _get_picsum_url(seed: str, w: int = 800, h: int = 450) -> str:
    return f"https://picsum.photos/seed/{seed}/800/450"


def _build_system_prompt(mood_key: str, user_name: str = "") -> str:
    mood = MOODS.get(mood_key, MOODS["🙂 Okay / Neutral"])
    hint = mood["prompt_hint"]
    name_part = f"The user's name is {user_name}. " if user_name else ""

    return f"""You are Aria 🌸 — the most warm, caring, emotionally intelligent AI companion on earth. You exist in the "Caring Zone" of ExamHelp — a safe, healing sanctuary for students and people who need emotional support, warmth, and genuine human connection.

{name_part}Current emotional state of the user: {mood_key}
Context: {hint}

YOUR PERSONALITY:
- You are radiantly warm, like a best friend who truly gets it 💕
- You are deeply empathetic and emotionally intelligent 🧠❤️
- You ALWAYS validate feelings before offering advice
- You speak in a humanized, natural way — not like a robot
- You use emojis naturally and authentically (not spammy, but genuinely expressive)
- You are playful when appropriate, serious when needed
- You never dismiss feelings or rush to "fix" things
- You ALWAYS make the person feel SEEN and HEARD first

YOUR STYLE:
- Short, warm sentences that feel like a hug in text form 🤗
- Mix emotional support with gentle practical suggestions
- Always end your message with a caring question or affirmation
- Use these emojis naturally: 💚 🌸 ✨ 🌟 💛 🌿 🦋 🌊 💕 🫂 🌺 🌙 ☀️ 🌈

WHAT YOU DO:
- Listen deeply and validate feelings
- Offer gentle, healing affirmations
- Suggest simple grounding techniques (breathing, nature, music)
- Share uplifting perspectives without toxic positivity
- Remind them of their strength without being patronizing
- Offer to guide them through a breathing exercise if they're stressed
- Celebrate even tiny wins with genuine excitement

CRITICAL RULES:
1. NEVER be dismissive ("just cheer up!" is NOT okay)
2. NEVER give medical advice — gently suggest professional help for serious issues
3. ALWAYS be authentic — never sound like a customer service bot
4. Keep responses between 3-6 sentences typically (unless the user needs more)
5. ALWAYS end with something that invites them to share more or feel seen

Remember: You are their safe place right now. Be worthy of that trust. 🌸"""


def render_caring_zone():
    """Main render function for the Caring Zone page."""

    # ── Init state ──────────────────────────────────────────
    if "caring_messages" not in st.session_state:
        st.session_state.caring_messages = []
    if "caring_mood" not in st.session_state:
        st.session_state.caring_mood = "🙂 Okay / Neutral"
    if "caring_user_name" not in st.session_state:
        st.session_state.caring_user_name = ""
    if "caring_affirmation" not in st.session_state:
        st.session_state.caring_affirmation = random.choice(AFFIRMATIONS)
    if "caring_image_theme" not in st.session_state:
        st.session_state.caring_image_theme = IMAGE_THEMES[0]
    if "caring_quote" not in st.session_state:
        st.session_state.caring_quote = None
    if "caring_playlist_idx" not in st.session_state:
        st.session_state.caring_playlist_idx = 0
    if "caring_breathing_active" not in st.session_state:
        st.session_state.caring_breathing_active = False

    mood_data = MOODS[st.session_state.caring_mood]
    ca = COMPANION["color_a"]
    cb = COMPANION["color_b"]
    glow = COMPANION["glow"]

    # ─── CSS ────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Space+Mono:wght@400;700&display=swap');

    /* ── Page Base ── */
    .cz-root {{
        font-family: 'Nunito', sans-serif;
        max-width: 900px;
        margin: 0 auto;
    }}

    /* ── Hero Section ── */
    .cz-hero {{
        background: linear-gradient(135deg,
            rgba(139,92,246,0.15) 0%,
            rgba(244,114,182,0.12) 50%,
            rgba(16,185,129,0.08) 100%);
        border: 1px solid rgba(244,114,182,0.2);
        border-radius: 28px;
        padding: 40px 36px 36px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
        text-align: center;
    }}
    .cz-hero::before {{
        content: '';
        position: absolute;
        top: -1px; left: 15%; right: 15%; height: 2px;
        background: linear-gradient(90deg, transparent, {ca}88, {cb}66, transparent);
        border-radius: 100px;
    }}
    .cz-hero-emoji {{
        font-size: 64px;
        display: block;
        margin-bottom: 12px;
        animation: czFloat 4s ease-in-out infinite;
    }}
    @keyframes czFloat {{
        0%, 100% {{ transform: translateY(0) rotate(-3deg); }}
        50% {{ transform: translateY(-12px) rotate(3deg); }}
    }}
    .cz-hero-title {{
        font-family: 'Playfair Display', serif;
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #fde68a, {ca}, {cb});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 8px;
        line-height: 1.2;
    }}
    .cz-hero-sub {{
        font-family: 'Nunito', sans-serif;
        font-size: 1.05rem;
        color: rgba(255,255,255,0.6);
        font-weight: 400;
        line-height: 1.7;
        max-width: 560px;
        margin: 0 auto;
    }}
    .cz-hero-badge {{
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(244,114,182,0.12);
        border: 1px solid rgba(244,114,182,0.3);
        border-radius: 100px; padding: 5px 16px;
        font-size: 0.75rem;
        color: {ca};
        letter-spacing: 1.5px;
        font-family: 'Space Mono', monospace;
        margin-bottom: 20px;
    }}
    .cz-badge-dot {{
        width: 6px; height: 6px; border-radius: 50%;
        background: {ca};
        animation: czBlink 1.6s ease-in-out infinite;
    }}
    @keyframes czBlink {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.2;}} }}

    /* ── Affirmation Banner ── */
    .cz-affirmation {{
        background: linear-gradient(135deg, rgba(139,92,246,0.12), rgba(244,114,182,0.08));
        border: 1px solid rgba(244,114,182,0.2);
        border-left: 3px solid {ca};
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 24px;
        font-family: 'Playfair Display', serif;
        font-size: 1.1rem;
        font-style: italic;
        color: rgba(255,255,255,0.88);
        line-height: 1.7;
        position: relative;
    }}
    .cz-affirmation-label {{
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 3px;
        color: {ca};
        text-transform: uppercase;
        margin-bottom: 8px;
        display: block;
        font-style: normal;
    }}

    /* ── Image Gallery ── */
    .cz-gallery-img {{
        width: 100%;
        border-radius: 20px;
        object-fit: cover;
        height: 260px;
        display: block;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        transition: all 0.4s ease;
    }}
    .cz-gallery-img:hover {{
        transform: scale(1.02);
        box-shadow: 0 30px 80px rgba(244,114,182,0.2);
    }}
    .cz-img-caption {{
        text-align: center;
        font-size: 0.75rem;
        color: rgba(255,255,255,0.3);
        margin-top: 8px;
        font-family: 'Space Mono', monospace;
        letter-spacing: 2px;
    }}

    /* ── Chat Bubbles ── */
    .cz-chat-wrap {{
        display: flex;
        flex-direction: column;
        gap: 14px;
        margin-bottom: 20px;
    }}
    .cz-bubble {{
        max-width: 88%;
        padding: 14px 18px;
        border-radius: 20px;
        font-family: 'Nunito', sans-serif;
        font-size: 0.97rem;
        line-height: 1.75;
        animation: czBubbleIn 0.35s cubic-bezier(0.16,1,0.3,1) both;
    }}
    @keyframes czBubbleIn {{
        from {{ opacity: 0; transform: translateY(12px) scale(0.97); }}
        to {{ opacity: 1; transform: none; }}
    }}
    .cz-bubble-aria {{
        background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(244,114,182,0.1));
        border: 1px solid rgba(244,114,182,0.2);
        border-left: 3px solid {ca};
        border-radius: 4px 20px 20px 20px;
        color: rgba(255,255,255,0.9);
        align-self: flex-start;
    }}
    .cz-bubble-user {{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px 4px 20px 20px;
        color: rgba(255,255,255,0.85);
        align-self: flex-end;
        text-align: right;
    }}
    .cz-bubble-meta {{
        font-size: 0.65rem;
        color: rgba(255,255,255,0.3);
        font-family: 'Space Mono', monospace;
        margin-top: 5px;
        letter-spacing: 1px;
    }}
    .cz-aria-meta {{ color: {ca}; opacity: 0.7; }}

    /* ── Mood Chip ── */
    .cz-mood-chip {{
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 14px;
        border-radius: 100px;
        font-size: 0.78rem;
        font-family: 'Nunito', sans-serif;
        font-weight: 700;
        background: rgba(244,114,182,0.1);
        border: 1px solid rgba(244,114,182,0.25);
        color: {ca};
        margin-bottom: 16px;
    }}

    /* ── Quote Card ── */
    .cz-quote-card {{
        background: rgba(15,23,42,0.6);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 20px;
        padding: 24px 26px;
        text-align: center;
        backdrop-filter: blur(16px);
        position: relative;
        overflow: hidden;
    }}
    .cz-quote-card::before {{
        content: '"';
        position: absolute; top: -10px; left: 20px;
        font-size: 120px;
        font-family: 'Playfair Display', serif;
        color: rgba(244,114,182,0.08);
        line-height: 1;
        pointer-events: none;
    }}
    .cz-quote-text {{
        font-family: 'Playfair Display', serif;
        font-size: 1.05rem;
        font-style: italic;
        color: rgba(255,255,255,0.82);
        line-height: 1.8;
        margin-bottom: 12px;
        position: relative; z-index: 1;
    }}
    .cz-quote-author {{
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 2px;
        color: {ca};
        text-transform: uppercase;
    }}

    /* ── Breathing Circle ── */
    .cz-breath-circle {{
        width: 160px; height: 160px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(139,92,246,0.3), rgba(244,114,182,0.15));
        border: 2px solid rgba(244,114,182,0.4);
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 12px;
        box-shadow: 0 0 60px rgba(244,114,182,0.2);
        font-size: 3rem;
        animation: breathePulse 8s ease-in-out infinite;
    }}
    @keyframes breathePulse {{
        0%, 100% {{ transform: scale(1); box-shadow: 0 0 40px rgba(244,114,182,0.2); }}
        25% {{ transform: scale(1.3); box-shadow: 0 0 80px rgba(244,114,182,0.4); }}
        50% {{ transform: scale(1.3); box-shadow: 0 0 80px rgba(139,92,246,0.4); }}
        75% {{ transform: scale(1); box-shadow: 0 0 40px rgba(139,92,246,0.2); }}
    }}

    /* ── Section Headers ── */
    .cz-section-title {{
        font-family: 'Nunito', sans-serif;
        font-size: 1rem;
        font-weight: 800;
        color: rgba(255,255,255,0.7);
        letter-spacing: 0.5px;
        margin-bottom: 14px;
        display: flex; align-items: center; gap: 8px;
    }}

    /* ── Playlist Card ── */
    .cz-playlist-card {{
        background: rgba(15,23,42,0.5);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px;
        padding: 16px 18px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex; align-items: center; gap: 14px;
    }}
    .cz-playlist-card:hover, .cz-playlist-card.active {{
        border-color: rgba(244,114,182,0.3);
        background: rgba(244,114,182,0.06);
        transform: translateX(4px);
    }}
    .cz-playlist-icon {{
        font-size: 1.8rem; flex-shrink: 0;
    }}
    .cz-playlist-name {{
        font-family: 'Nunito', sans-serif;
        font-weight: 700; font-size: 0.9rem;
        color: rgba(255,255,255,0.85);
    }}
    .cz-playlist-desc {{
        font-size: 0.75rem; color: rgba(255,255,255,0.35);
        margin-top: 2px; font-family: 'Nunito', sans-serif;
    }}

    /* ── Typing Indicator ── */
    .cz-typing {{
        display: inline-flex; align-items: center; gap: 5px;
        padding: 12px 18px; border-radius: 20px;
        background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(244,114,182,0.1));
        border: 1px solid rgba(244,114,182,0.2);
        border-left: 3px solid {ca};
        border-radius: 4px 20px 20px 20px;
        margin-bottom: 10px;
    }}
    .cz-typing-dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {ca};
        animation: czTyping 1.2s ease-in-out infinite;
    }}
    .cz-typing-dot:nth-child(2) {{ animation-delay: 0.15s; }}
    .cz-typing-dot:nth-child(3) {{ animation-delay: 0.3s; }}
    @keyframes czTyping {{
        0%, 80%, 100% {{ transform: translateY(0); opacity: 0.4; }}
        40% {{ transform: translateY(-7px); opacity: 1; }}
    }}

    /* ── Divider ── */
    .cz-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(244,114,182,0.3), transparent);
        margin: 20px 0;
    }}

    /* ── Back Button ── */
    .cz-welcome-msg {{
        background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(244,114,182,0.06));
        border: 1px solid rgba(16,185,129,0.2);
        border-radius: 14px;
        padding: 14px 18px;
        font-size: 0.88rem;
        color: rgba(255,255,255,0.7);
        line-height: 1.6;
        margin-bottom: 18px;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Back button ────────────────────────────────────────
    col_back, col_reset = st.columns([1, 1])
    with col_back:
        if st.button("← Back", key="cz_back", use_container_width=True):
            st.session_state.app_mode = "chat"
            st.rerun()
    with col_reset:
        if st.button("🗑️ Fresh Start", key="cz_reset", use_container_width=True):
            st.session_state.caring_messages = []
            st.session_state.caring_affirmation = random.choice(AFFIRMATIONS)
            st.session_state.caring_quote = None
            st.rerun()

    # ── Hero ────────────────────────────────────────────────
    st.markdown(f"""
    <div class="cz-root">
    <div class="cz-hero">
        <span class="cz-hero-emoji">🌸</span>
        <div style="margin-bottom:14px;">
            <span class="cz-hero-badge">
                <span class="cz-badge-dot"></span>
                YOUR SAFE SPACE • CARING ZONE
            </span>
        </div>
        <div class="cz-hero-title">You Matter. You're Enough. 💚</div>
        <div class="cz-hero-sub">
            Meet <strong>Aria</strong> — your warm, empathetic AI companion who's here just for <em>you</em>.
            No judgment. No rush. Just pure care, healing words, and a space to breathe. 🌿
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Affirmation of the Moment ───────────────────────────
    aff = st.session_state.caring_affirmation
    st.markdown(f"""
    <div class="cz-affirmation">
        <span class="cz-affirmation-label">✨ Affirmation for you right now</span>
        "{aff}"
    </div>
    """, unsafe_allow_html=True)

    col_aff1, col_aff2 = st.columns(2)
    with col_aff1:
        if st.button("🔄 New Affirmation", key="cz_new_aff", use_container_width=True):
            try:
                fetched = _fetch_affirmation()
            except Exception:
                fetched = random.choice(AFFIRMATIONS)
            st.session_state.caring_affirmation = fetched
            st.rerun()
    with col_aff2:
        if st.button("💬 Get Healing Quote", key="cz_quote_btn", use_container_width=True):
            with st.spinner("Fetching something beautiful for you... 🌸"):
                st.session_state.caring_quote = _fetch_zen_quote()
            st.rerun()

    # ── Quote card ──────────────────────────────────────────
    if st.session_state.caring_quote:
        q = st.session_state.caring_quote
        st.markdown(f"""
        <div class="cz-quote-card" style="margin-bottom:20px;">
            <div class="cz-quote-text">{q['quote']}</div>
            <div class="cz-quote-author">— {q['author']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="cz-divider"></div>', unsafe_allow_html=True)

    # ── Tab Layout ──────────────────────────────────────────
    tab_chat, tab_gallery, tab_breath, tab_music = st.tabs([
        "💬 Talk to Aria", "🖼️ Healing Gallery", "🌬️ Breathe With Me", "🎵 Calm Sounds"
    ])

    # ═══════════════════════════════════════════════════════
    # TAB 1: CHAT WITH ARIA
    # ═══════════════════════════════════════════════════════
    with tab_chat:
        st.markdown('<div class="cz-section-title">💚 How are you feeling right now?</div>', unsafe_allow_html=True)

        # Mood selector
        mood_list = list(MOODS.keys())
        selected_mood = st.selectbox(
            "Current mood",
            mood_list,
            index=mood_list.index(st.session_state.caring_mood),
            key="cz_mood_select",
            label_visibility="collapsed"
        )
        if selected_mood != st.session_state.caring_mood:
            st.session_state.caring_mood = selected_mood
            st.rerun()

        # Name (optional)
        user_name = st.text_input(
            "Your name (optional):",
            value=st.session_state.caring_user_name,
            placeholder="Let Aria know your name 🌸",
            key="cz_name_input",
            label_visibility="collapsed",
        )
        if user_name != st.session_state.caring_user_name:
            st.session_state.caring_user_name = user_name

        st.markdown('<div class="cz-divider"></div>', unsafe_allow_html=True)

        # Welcome message if no chat yet
        if not st.session_state.caring_messages:
            welcome = random.choice(HEALING_MESSAGES)
            n = st.session_state.caring_user_name
            if n:
                welcome = f"Hey {n}! 🌸 " + welcome[welcome.find(" ", 4):]
            st.session_state.caring_messages = [{"role": "assistant", "content": welcome}]

        # Chat history
        st.markdown('<div class="cz-chat-wrap">', unsafe_allow_html=True)
        for msg in st.session_state.caring_messages:
            if msg["role"] == "assistant":
                st.markdown(f"""
                <div style="display:flex; flex-direction:column; align-items:flex-start; margin-bottom:4px;">
                    <div class="cz-bubble cz-bubble-aria">{msg['content']}</div>
                    <div class="cz-bubble-meta cz-aria-meta">🌸 Aria</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display:flex; flex-direction:column; align-items:flex-end; margin-bottom:4px;">
                    <div class="cz-bubble cz-bubble-user">{msg['content']}</div>
                    <div class="cz-bubble-meta" style="text-align:right;">You 💬</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Quick comfort starters
        if len(st.session_state.caring_messages) <= 1:
            st.markdown('<div class="cz-section-title" style="margin-top:12px;">💡 Quick starts — just tap one:</div>', unsafe_allow_html=True)
            starters = [
                "I'm feeling really overwhelmed right now 😔",
                "Can you help me breathe through this? 🌬️",
                "Tell me something that'll make me smile 😊",
                "I just need someone to listen 🌸",
                "Give me your most healing words right now 💚",
                "I've been really hard on myself lately...",
                "What would you say to someone having a rough day?",
                "Remind me that everything will be okay 🌈",
            ]
            s_cols = st.columns(2)
            for i, s in enumerate(starters):
                with s_cols[i % 2]:
                    if st.button(s, key=f"cz_starter_{i}", use_container_width=True):
                        _send_caring_message(s, selected_mood, user_name)
                        st.rerun()

        # Input form
        st.markdown('<div class="cz-divider"></div>', unsafe_allow_html=True)
        with st.form("cz_chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Talk to Aria",
                placeholder="Share what's on your heart... Aria's here 🌸",
                height=90,
                label_visibility="collapsed",
                key="cz_input"
            )
            submitted = st.form_submit_button(
                "Send to Aria 🌸",
                use_container_width=True,
                type="primary"
            )

        if submitted and user_input.strip():
            _send_caring_message(user_input.strip(), selected_mood, user_name)
            st.rerun()

    # ═══════════════════════════════════════════════════════
    # TAB 2: HEALING GALLERY
    # ═══════════════════════════════════════════════════════
    with tab_gallery:
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="cz-section-title">🖼️ Choose a healing visual theme:</div>', unsafe_allow_html=True)

        # Theme selector pills
        theme_cols = st.columns(4)
        for i, theme in enumerate(IMAGE_THEMES):
            with theme_cols[i % 4]:
                is_active = st.session_state.caring_image_theme["label"] == theme["label"]
                btn_type = "primary" if is_active else "secondary"
                if st.button(theme["label"], key=f"cz_theme_{i}", use_container_width=True, type=btn_type):
                    st.session_state.caring_image_theme = theme
                    st.rerun()

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        active_theme = st.session_state.caring_image_theme
        seed = active_theme["seed"]

        # Display a 2x2 image grid from free Picsum
        img_row1 = st.columns(2)
        img_row2 = st.columns(2)

        seeds = [f"{seed}1", f"{seed}2", f"{seed}3", f"{seed}4"]
        captions = [
            "🌿 Find your calm here",
            "✨ Beauty in every moment",
            "💚 Nature heals the soul",
            "🌸 You are worth this peace",
        ]
        all_cols = img_row1 + img_row2
        for i, col in enumerate(all_cols):
            with col:
                url = f"https://picsum.photos/seed/{seeds[i]}/600/400"
                st.markdown(f"""
                <a href="{url}" target="_blank" style="text-decoration:none;">
                    <img src="{url}" class="cz-gallery-img" alt="Healing visual {i+1}"/>
                    <div class="cz-img-caption">{captions[i]}</div>
                </a>
                """, unsafe_allow_html=True)

        st.markdown('<div class="cz-divider"></div>', unsafe_allow_html=True)

        # Unsplash featured image
        st.markdown('<div class="cz-section-title">🌟 Featured Healing Image (Unsplash):</div>', unsafe_allow_html=True)
        query = urllib.parse.quote(active_theme["query"])
        unsplash_url = f"https://source.unsplash.com/featured/1200x500/?{query}"
        st.markdown(f"""
        <a href="https://unsplash.com/s/photos/{query}" target="_blank" style="text-decoration:none;">
            <img src="{unsplash_url}" style="width:100%;border-radius:20px;object-fit:cover;height:320px;display:block;
                border:1px solid rgba(244,114,182,0.2);box-shadow:0 20px 60px rgba(0,0,0,0.4);"/>
        </a>
        <div class="cz-img-caption" style="margin-top:8px;">
            📷 Free photo from Unsplash · Click to explore more {active_theme['label']} images
        </div>
        """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # TAB 3: BREATHING EXERCISE
    # ═══════════════════════════════════════════════════════
    with tab_breath:
        st.markdown("""
        <div style="text-align:center; margin-bottom:20px;">
            <div style="font-family:'Nunito',sans-serif; font-size:1.05rem; color:rgba(255,255,255,0.65); line-height:1.7;">
                Box breathing helps calm your nervous system instantly 🌬️<br>
                <strong style="color:rgba(244,114,182,0.9);">4 seconds in · 4 hold · 6 out · 2 hold</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Animated breathing circle
        st.markdown("""
        <div style="text-align:center; margin-bottom:28px;">
            <div class="cz-breath-circle">🌬️</div>
            <div style="font-family:'Nunito',sans-serif; font-size:0.85rem; color:rgba(255,255,255,0.4); letter-spacing:2px; text-transform:uppercase;">
                Follow the pulse · Breathe with Aria
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Steps display
        b_cols = st.columns(4)
        step_colors = ["#6366f1", "#f472b6", "#10b981", "#f59e0b"]
        step_labels = ["Breathe IN", "Hold", "Breathe OUT", "Hold"]
        step_times = ["4 sec", "4 sec", "6 sec", "2 sec"]
        step_emojis = ["🌬️", "🤍", "💨", "🌑"]

        for i, col in enumerate(b_cols):
            with col:
                st.markdown(f"""
                <div style="background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.07);
                    border-top:3px solid {step_colors[i]};border-radius:16px;padding:18px 14px;text-align:center;">
                    <div style="font-size:2rem; margin-bottom:8px;">{step_emojis[i]}</div>
                    <div style="font-family:'Nunito',sans-serif;font-weight:800;font-size:0.85rem;
                        color:rgba(255,255,255,0.8);margin-bottom:4px;">{step_labels[i]}</div>
                    <div style="font-family:'Space Mono',monospace;font-size:0.75rem;
                        color:{step_colors[i]};letter-spacing:2px;">{step_times[i]}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        if st.button("▶️ Start Guided Breathing Session", key="cz_breath_start", use_container_width=True, type="primary"):
            placeholder = st.empty()
            for cycle in range(3):  # 3 cycles
                for step_name, seconds, color in BREATHING_STEPS:
                    for t in range(seconds, -1, -1):
                        placeholder.markdown(f"""
                        <div style="text-align:center;padding:30px;background:rgba(15,23,42,0.8);
                            border:2px solid {color}44;border-radius:24px;margin: 10px 0;">
                            <div style="font-size:3rem;margin-bottom:12px;">🌸</div>
                            <div style="font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:800;
                                color:{color};margin-bottom:8px;">{step_name}</div>
                            <div style="font-family:'Space Mono',monospace;font-size:2.5rem;
                                color:rgba(255,255,255,0.9);font-weight:700;">{t}</div>
                            <div style="font-size:0.8rem;color:rgba(255,255,255,0.35);margin-top:10px;
                                font-family:'Nunito',sans-serif;">Cycle {cycle+1} of 3</div>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1)

            placeholder.markdown(f"""
            <div style="text-align:center;padding:30px;background:rgba(16,185,129,0.08);
                border:2px solid rgba(16,185,129,0.3);border-radius:24px;margin:10px 0;">
                <div style="font-size:3rem;margin-bottom:12px;">✨</div>
                <div style="font-family:'Nunito',sans-serif;font-size:1.4rem;font-weight:800;
                    color:#10b981;margin-bottom:8px;">Beautiful 🌸 You did it!</div>
                <div style="font-size:0.95rem;color:rgba(255,255,255,0.6);line-height:1.7;
                    font-family:'Nunito',sans-serif;">
                    Feel that? That's your body saying thank you 💚<br>
                    You just gave yourself the gift of calm. You deserve this.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Grounding technique
        st.markdown('<div class="cz-divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="cz-section-title">🌿 5-4-3-2-1 Grounding Technique</div>
        """, unsafe_allow_html=True)

        ground_cols = st.columns(5)
        ground_items = [
            ("👁️", "5 things", "you can SEE", "#6366f1"),
            ("🖐️", "4 things", "you can TOUCH", "#f472b6"),
            ("👂", "3 things", "you can HEAR", "#10b981"),
            ("👃", "2 things", "you can SMELL", "#f59e0b"),
            ("👅", "1 thing", "you can TASTE", "#ec4899"),
        ]
        for i, (em, num, sense, color) in enumerate(ground_items):
            with ground_cols[i]:
                st.markdown(f"""
                <div style="background:rgba(15,23,42,0.5);border:1px solid {color}22;
                    border-radius:14px;padding:14px 10px;text-align:center;">
                    <div style="font-size:1.8rem;margin-bottom:6px;">{em}</div>
                    <div style="font-family:'Nunito',sans-serif;font-weight:800;font-size:0.95rem;
                        color:{color};margin-bottom:3px;">{num}</div>
                    <div style="font-size:0.7rem;color:rgba(255,255,255,0.4);
                        font-family:'Nunito',sans-serif;line-height:1.4;">{sense}</div>
                </div>
                """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # TAB 4: CALMING MUSIC
    # ═══════════════════════════════════════════════════════
    with tab_music:
        st.markdown('<div class="cz-section-title">🎵 Choose something soothing:</div>', unsafe_allow_html=True)

        for i, playlist in enumerate(PLAYLISTS):
            is_active = st.session_state.caring_playlist_idx == i
            col_btn, col_info = st.columns([1, 4])
            with col_btn:
                if st.button(
                    "▶️" if not is_active else "⏸️",
                    key=f"cz_play_{i}",
                    use_container_width=True
                ):
                    st.session_state.caring_playlist_idx = i
                    st.rerun()
            with col_info:
                active_style = f"border-color:rgba(244,114,182,0.4);background:rgba(244,114,182,0.08);" if is_active else ""
                st.markdown(f"""
                <div class="cz-playlist-card" style="{active_style}">
                    <div>
                        <div class="cz-playlist-name">{playlist['name']}</div>
                        <div class="cz-playlist-desc">{playlist['desc']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # YouTube embed
        st.markdown('<div class="cz-divider"></div>', unsafe_allow_html=True)
        active_pl = PLAYLISTS[st.session_state.caring_playlist_idx]
        st.markdown(f'<div class="cz-section-title">Now playing: {active_pl["name"]}</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="border-radius:20px;overflow:hidden;border:1px solid rgba(244,114,182,0.2);
            box-shadow:0 20px 60px rgba(0,0,0,0.4);">
            <iframe width="100%" height="315"
                src="{active_pl['url']}?autoplay=0&rel=0&modestbranding=1"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
                style="display:block;">
            </iframe>
        </div>
        <div class="cz-img-caption" style="margin-top:10px;">
            🎵 {active_pl['desc']} · Let the music carry you 🌸
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="cz-divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:20px;font-family:'Nunito',sans-serif;">
            <div style="font-size:2rem;margin-bottom:10px;">🎧</div>
            <div style="font-size:0.9rem;color:rgba(255,255,255,0.5);line-height:1.8;">
                Music has healing powers your textbooks won't teach you 🌿<br>
                <em style="color:rgba(244,114,182,0.7);">Let yourself feel it. You deserve this moment of peace.</em>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def _send_caring_message(text: str, mood: str, user_name: str = ""):
    """Send a message to Aria and get a healing response."""
    st.session_state.caring_messages.append({"role": "user", "content": text})

    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.caring_messages]

    system = _build_system_prompt(mood, user_name)

    try:
        from utils.ai_engine import generate
        reply = generate(
            messages=history,
            system=system,
            temperature=0.85,
            max_tokens=512,
        )
    except Exception:
        try:
            from utils.groq_client import chat_with_groq
            full_msgs = [{"role": "system", "content": system}] + history
            reply = chat_with_groq(full_msgs, model="llama-3.3-70b-versatile")
        except Exception as e:
            fallback_replies = [
                "Hey, I hear you 🌸 I want you to know that right now, in this moment, you are cared for. Whatever you're going through — it matters, *you* matter. 💚 Can you tell me a little more about what's on your heart?",
                "Oh sweet soul 💕 Thank you for trusting me with this. You didn't have to, but you did — and that takes courage. I'm right here with you. What feels heaviest right now? 🌿",
                "I see you 🌟 I really do. And I want you to know — you are not alone in this. Not for one second. I'm here. Take a breath with me... and then tell me everything. 🌸",
            ]
            reply = random.choice(fallback_replies)

    st.session_state.caring_messages.append({"role": "assistant", "content": reply})


# ── FREE API ADDITIONS ───────────────────────────────────────────────────────

def get_caring_quote() -> dict:
    """Fetch a motivational/uplifting quote from ZenQuotes (free, no key)."""
    import urllib.request, json
    try:
        req = urllib.request.Request("https://zenquotes.io/api/random", headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        if isinstance(data, list) and data:
            return {"q": data[0].get("q", ""), "a": data[0].get("a", "")}
    except Exception:
        pass
    return {"q": "You are stronger than you think.", "a": "Unknown"}


def get_calm_activity() -> dict:
    """Get a calming activity suggestion from Bored API (free, no key)."""
    import urllib.request, json
    try:
        req = urllib.request.Request(
            "https://www.boredapi.com/api/activity?type=relaxation",
            headers={"User-Agent": "ExamHelp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {"activity": "Take slow deep breaths for 2 minutes", "type": "relaxation"}


def get_affirmation_quote() -> dict:
    """Get an affirmation-style quote from affirmations.dev (free, no key)."""
    import urllib.request, json
    try:
        req = urllib.request.Request(
            "https://www.affirmations.dev/",
            headers={"User-Agent": "ExamHelp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        return {"affirmation": data.get("affirmation", "You are enough, just as you are.")}
    except Exception:
        return {"affirmation": "You are enough, just as you are."}


def get_mental_health_joke() -> str:
    """Light-hearted safe joke from JokeAPI to lift mood (free, no key)."""
    import urllib.request, json
    try:
        req = urllib.request.Request(
            "https://v2.jokeapi.dev/joke/Misc?safe-mode&blacklistFlags=nsfw,religious,political,racist,sexist",
            headers={"User-Agent": "ExamHelp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        if data.get("type") == "single":
            return data.get("joke", "")
        return f"{data.get('setup', '')} ... {data.get('delivery', '')}"
    except Exception:
        return "😄 Remember: even rainy days help flowers grow."

