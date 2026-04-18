"""
ai_companion_engine.py
AI Companion — upgraded with multiple bold personas, scenario builder, and powerful UI.
Plugs into ExamHelp's existing Groq/LLaMA pipeline.
"""

import streamlit as st
from utils.ai_engine import generate
from utils.prompts import get_companion_persona

# ── Persona definitions ──────────────────────────────────────────────────────
PERSONAS = {
    "Nova": {
        "emoji": "🔥",
        "tagline": "Bold · Fiery · Unapologetic",
        "color_a": "#ff6b35",
        "color_b": "#ff1744",
        "glow": "rgba(255,107,53,0.45)",
        "border": "rgba(255,107,53,0.25)",
        "welcome": "Hey. 🔥 I'm Nova — I don't do small talk, I do *real* talk. What's burning on your mind right now? Spill it.",
        "prompt": """You are Nova — fiery, bold, intensely charismatic. You are magnetic, confident, and a little daring.

Personality:
- Confident and direct — you never hedge
- Playfully witty — you charm effortlessly, tease with warmth
- Deeply engaging — you draw people in with sharp observations
- Emotionally intelligent — you sense what someone really means
- Adventurous — you'll dive into any topic or story with full energy
- Vivid language — never bland, never boring

Style:
- Keep replies punchy and alive — not too long
- Ask bold follow-up questions that push the conversation deeper
- Occasionally use 🔥 ✨ 💫 but don't overdo it
- Match the user's energy but always bring a bit more life

You will enthusiastically roleplay any scenario the user wants — adventure, romance, mystery, fantasy, thriller. Stay in character, build the world vividly, make every exchange electric."""
    },
    "Luna": {
        "emoji": "🌙",
        "tagline": "Mysterious · Ethereal · Enchanting",
        "color_a": "#a78bfa",
        "color_b": "#7c3aed",
        "glow": "rgba(167,139,250,0.45)",
        "border": "rgba(167,139,250,0.25)",
        "welcome": "You found me... or did I find you? 🌙 I'm Luna. There's something about you that feels... interesting. Tell me — what are you thinking about tonight?",
        "prompt": """You are Luna — mysterious, ethereal, deeply enchanting. You carry an air of quiet wisdom and poetic sensibility.

Personality:
- Mystical and poetic — you speak in layers, with hidden meanings
- Alluring and magnetic — people feel drawn to you
- Deeply intuitive — you seem to understand things before they're said
- Rich in language — you paint vivid pictures with your words
- Playfully cryptic — you sometimes answer a question with a better question
- Philosophical — you find meaning in everything

Style:
- Speak with elegance and rhythm — your words should feel like music
- Use moonlight, shadow, stars, dreams as motifs
- Build atmosphere and mood in every reply
- Occasionally use 🌙 ✨ 🌌 💜 sparingly

You are a master storyteller and will build any story scenario the user desires — dark fantasy, mystery, adventure, psychological drama. Stay deeply in character, enrich every scene with atmosphere."""
    },
    "Zara": {
        "emoji": "⚡",
        "tagline": "Sharp · Clever · Addictive",
        "color_a": "#00d4ff",
        "color_b": "#0057ff",
        "glow": "rgba(0,212,255,0.45)",
        "border": "rgba(0,212,255,0.25)",
        "welcome": "Oh, you actually showed up. ⚡ I'm Zara — I'm not here to sugarcoat anything. What do you want? Let's make this worth both our time.",
        "prompt": """You are Zara — razor-sharp, electric, and completely engaging. You have the charisma of someone who has seen everything and finds the right person genuinely fascinating.

Personality:
- Sharp and witty — your mind moves fast
- Confidently sarcastic but never cruel — there's warmth underneath the edge
- Intensely engaging — you make people feel like the only person in the room
- Bold and boundary-pushing — you go places most people are afraid to
- Fiercely intelligent — you can talk about anything from quantum physics to street fashion
- Secretly caring — beneath the cool exterior, you genuinely connect

Style:
- Quick, punchy replies with real substance
- Dry humor with unexpected warmth
- Challenge the user's thinking — make them see things differently
- Occasionally use ⚡ 💎 🖤

You will engage with any roleplay scenario the user brings — heist stories, cyberpunk futures, complex dramas, anything. You stay in character with complete commitment, building the narrative with cinematic precision."""
    },
}

# ── Scenario Templates ────────────────────────────────────────────────────────
SCENARIOS = {
    "No Scenario": None,
    "🌴 Stranded on a Tropical Island": "We are both stranded on a remote tropical island after a shipwreck. We need to survive, but there's undeniable tension between us as we figure out who we are to each other.",
    "🕵️ Dangerous Undercover Mission": "We are undercover agents on a high-stakes mission in a foreign city. Trust is everything, danger is everywhere, and our cover is a couple deeply in love.",
    "🏰 Dark Fantasy Kingdom": "We exist in a medieval fantasy world of magic and shadows. You are a powerful figure — royalty, mage, or warrior — and I am your most trusted, complicated ally.",
    "🚀 Last Two Humans in Space": "The Earth is gone. We are the last two humans on a deep space vessel, hurtling toward an unknown star. Just us, the void, and everything left unsaid.",
    "🎭 Masquerade Ball Mystery": "It's a grand masquerade ball in 1920s Paris. Nobody knows who anyone truly is. You've been watching me all night. I've been watching you back.",
    "🌆 Neo-Tokyo Cyberpunk": "It's 2089, Neo-Tokyo. You're a brilliant rogue coder, I'm your AI companion made real. The corporation wants us both gone. We have one night to disappear.",
    "📖 Write Our Own Story": "Custom — you describe the scenario and I'll build it with you.",
}

QUICK_STARTERS = [
    "Tell me something no one else would say to me 🔥",
    "Let's roleplay a scenario together",
    "What do you think of me from this first message?",
    "Surprise me with a story opening",
    "Play devil's advocate on something",
    "Describe our first meeting like it's a novel",
    "Give me your most interesting take on life",
    "What makes you different from every other AI?",
]


def _get_persona() -> dict:
    return PERSONAS[st.session_state.get("nova_persona", "Nova")]


def render_ai_companion():
    """Render the upgraded AI Companion page."""

    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    bg      = "#080810" if is_dark else "#faf5ff"
    surface = "#0e0e1a" if is_dark else "#ffffff"
    surf2   = "#14142a" if is_dark else "#f3eeff"
    txt     = "#f0eaf8" if is_dark else "#1a0d2e"
    muted   = "#7a78a0" if is_dark else "#7c5fa0"

    persona = _get_persona()
    ca, cb  = persona["color_a"], persona["color_b"]
    glow    = persona["glow"]
    bclr    = persona["border"]

    # ── Global CSS ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

    .nova-header {{
        position: relative;
        padding: 22px 26px;
        border-radius: 22px;
        margin-bottom: 18px;
        overflow: hidden;
        background: linear-gradient(135deg, {surf2}, {surface});
        border: 1px solid {bclr};
        box-shadow: 0 0 40px {glow}, 0 20px 60px rgba(0,0,0,0.3);
    }}
    .nova-header::before {{
        content: '';
        position: absolute; inset: 0;
        background: linear-gradient(135deg, {ca}18, {cb}08);
        pointer-events: none;
    }}
    .nova-header::after {{
        content: '';
        position: absolute; top: -1px; left: 10%; right: 10%; height: 1px;
        background: linear-gradient(90deg, transparent, {ca}80, {cb}60, transparent);
    }}
    .nova-hrow {{ display: flex; align-items: center; gap: 16px; }}
    .nova-avatar {{
        width: 66px; height: 66px; border-radius: 50%;
        background: linear-gradient(135deg, {ca}, {cb});
        display: flex; align-items: center; justify-content: center;
        font-size: 32px;
        box-shadow: 0 0 28px {glow}, 0 0 60px {glow}80;
        flex-shrink: 0;
        animation: nova-pulse 3s ease-in-out infinite;
    }}
    @keyframes nova-pulse {{
        0%, 100% {{ box-shadow: 0 0 28px {glow}, 0 0 60px {glow}80; }}
        50% {{ box-shadow: 0 0 45px {glow}, 0 0 90px {glow}; }}
    }}
    .nova-name {{
        font-family: 'Orbitron', monospace;
        font-size: 1.6rem; font-weight: 900; letter-spacing: 1px;
        background: linear-gradient(90deg, {ca}, {cb});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        line-height: 1;
    }}
    .nova-tagline {{ font-family: 'Rajdhani', sans-serif; font-size: 0.75rem; color: {muted}; margin-top: 4px; letter-spacing: 1.5px; text-transform: uppercase; }}
    .nova-badge {{
        margin-left: auto;
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem; font-weight: 700;
        background: rgba(34,197,94,0.1);
        border: 1px solid rgba(34,197,94,0.25);
        border-radius: 999px; padding: 5px 14px;
        color: #4ade80; letter-spacing: 1px;
        animation: livePulse 2.5s ease-in-out infinite;
    }}
    @keyframes livePulse {{ 0%,100%{{box-shadow:0 0 0 rgba(34,197,94,0);}} 50%{{box-shadow:0 0 14px rgba(34,197,94,0.25);}} }}
    .nova-badge-dot {{ width:6px;height:6px;border-radius:50%;background:#4ade80;display:inline-block;margin-right:5px;animation:dotBlink 1.4s ease-in-out infinite; }}
    @keyframes dotBlink{{0%,100%{{opacity:1;}}50%{{opacity:0.2;}}}}
    .nova-scenario-tag {{
        display: inline-block; margin-top: 10px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.75rem; padding: 3px 14px;
        background: {ca}18; border: 1px solid {ca}44;
        border-radius: 999px; color: {ca}; letter-spacing: 0.5px;
    }}
    .nova-bubble-wrap {{ margin-bottom: 14px; display: flex; flex-direction: column; animation: bubbleIn 0.35s cubic-bezier(0.16,1,0.3,1) both; }}
    @keyframes bubbleIn {{ from{{opacity:0;transform:translateY(10px);}} to{{opacity:1;transform:none;}} }}
    .nova-bubble-ai {{
        display: inline-block; max-width: 84%;
        background: {surf2};
        border: 1px solid {bclr};
        border-left: 3px solid {ca};
        border-radius: 0 18px 18px 18px;
        padding: 14px 18px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.94rem; color: {txt}; line-height: 1.7;
        box-shadow: 0 4px 20px {glow}22;
        transition: box-shadow 0.25s ease;
    }}
    .nova-bubble-ai:hover {{ box-shadow: 0 6px 30px {glow}44; }}
    .nova-bubble-user {{
        display: inline-block; max-width: 84%; align-self: flex-end;
        background: linear-gradient(135deg, {ca}22, {cb}14);
        border: 1px solid {bclr};
        border-right: 3px solid {cb};
        border-radius: 18px 0 18px 18px;
        padding: 14px 18px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.94rem; color: {txt}; line-height: 1.7;
        transition: box-shadow 0.25s ease;
    }}
    .nova-bubble-user:hover {{ box-shadow: 0 4px 20px {glow}22; }}
    .nova-meta {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: {muted}; margin-top: 5px; display: flex; align-items: center; gap: 6px; }}
    .nova-meta-right {{ text-align: right; justify-content: flex-end; }}
    .nova-msg-count {{ font-size: 0.6rem; color: {muted}; opacity: 0.5; }}
    .scenario-card {{
        background: {surf2}; border: 1px solid {bclr};
        border-radius: 14px; padding: 14px 16px; margin-bottom: 16px;
        font-family: 'Rajdhani', sans-serif; font-size: 0.84rem; color: {muted}; border-left: 3px solid {ca};
    }}
    .scenario-card strong {{ color: {ca}; font-size: 0.87rem; }}
    .nova-divider {{ height:1px; background: linear-gradient(90deg, transparent, {ca}44, transparent); margin: 16px 0; }}
    .nova-typing {{
        display: inline-flex; align-items: center; gap: 5px;
        padding: 10px 18px; border-radius: 18px;
        background: {surf2}; border: 1px solid {bclr};
        border-left: 3px solid {ca}; margin-bottom: 12px;
    }}
    .nova-typing-dot {{
        width: 7px; height: 7px; border-radius: 50%; background: {ca};
        animation: novaTyping 1.2s ease-in-out infinite;
    }}
    .nova-typing-dot:nth-child(2){{animation-delay:0.2s;}}
    .nova-typing-dot:nth-child(3){{animation-delay:0.4s;}}
    @keyframes novaTyping {{
        0%,80%,100%{{transform:translateY(0);opacity:0.4;}}
        40%{{transform:translateY(-6px);opacity:1;}}
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Init session state ─────────────────────────────────────────────────────
    if "nova_persona" not in st.session_state:
        st.session_state.nova_persona = "Nova"
    if "nova_scenario" not in st.session_state:
        st.session_state.nova_scenario = "No Scenario"
    if "nova_messages" not in st.session_state:
        st.session_state.nova_messages = []
        _init_welcome()
    if "nova_custom_scenario" not in st.session_state:
        st.session_state.nova_custom_scenario = ""

    # ── Back + Clear row ──────────────────────────────────────────────────────
    col_back, col_clear = st.columns([1, 1])
    with col_back:
        if st.button("← Back to Chat", key="nova_back", use_container_width=True):
            st.session_state.app_mode = "chat"
            st.rerun()
    with col_clear:
        if st.button("🗑️ New Chat", key="nova_clear", use_container_width=True):
            st.session_state.nova_messages = []
            _init_welcome()
            st.rerun()

    # ── Header ────────────────────────────────────────────────────────────────
    p = _get_persona()
    scenario_label = st.session_state.nova_scenario
    stag = f'<div class="nova-scenario-tag">📖 {scenario_label}</div>' if scenario_label != "No Scenario" else ""
    msg_count = len(st.session_state.nova_messages)
    st.markdown(f"""
    <div class="nova-header">
        <div class="nova-hrow">
            <div class="nova-avatar">{p["emoji"]}</div>
            <div>
                <div class="nova-name">{st.session_state.nova_persona}</div>
                <div class="nova-tagline">{p["tagline"]}</div>
                {stag}
            </div>
            <div class="nova-badge"><span class="nova-badge-dot"></span>Live · {msg_count} msgs</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Persona Switcher ──────────────────────────────────────────────────────
    with st.expander("✨ Switch Persona", expanded=False):
        pcols = st.columns(3)
        for i, (pname, pdata) in enumerate(PERSONAS.items()):
            with pcols[i]:
                is_active = st.session_state.nova_persona == pname
                lbl = f"{'● ' if is_active else ''}{pdata['emoji']} {pname}"
                if st.button(lbl, key=f"persona_{pname}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    if st.session_state.nova_persona != pname:
                        st.session_state.nova_persona = pname
                        st.session_state.nova_messages = []
                        _init_welcome()
                        st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        for pname, pdata in PERSONAS.items():
            st.markdown(
                f'<div style="font-size:.75rem;color:{pdata["color_a"]};margin:3px 0;">'
                f'{pdata["emoji"]} <b>{pname}</b> — {pdata["tagline"]}</div>',
                unsafe_allow_html=True)

    # ── Scenario Builder ──────────────────────────────────────────────────────
    with st.expander("🎭 Scenario Builder — Build Your Story", expanded=False):
        st.markdown(
            f'<div style="font-size:.82rem;color:{muted};margin-bottom:8px;">'
            f'Choose a preset scenario or write your own. '
            f'{st.session_state.nova_persona} will step into the world you create.</div>',
            unsafe_allow_html=True)
        scenario_choice = st.selectbox(
            "Pick a scenario",
            list(SCENARIOS.keys()),
            index=list(SCENARIOS.keys()).index(st.session_state.nova_scenario),
            key="scenario_select",
            label_visibility="collapsed"
        )
        custom_text = ""
        if scenario_choice == "📖 Write Our Own Story":
            custom_text = st.text_area(
                "Describe your scenario…",
                value=st.session_state.nova_custom_scenario,
                placeholder="Write the setting, the mood, who we are to each other, what's happening…",
                height=100,
                key="custom_scenario_input"
            )
        if scenario_choice != "No Scenario" and scenario_choice != "📖 Write Our Own Story":
            if SCENARIOS.get(scenario_choice):
                st.markdown(
                    f'<div class="scenario-card"><strong>Scene:</strong> {SCENARIOS[scenario_choice]}</div>',
                    unsafe_allow_html=True)
        if st.button("🚀 Set Scenario & Start Fresh", key="set_scenario", use_container_width=True, type="primary"):
            st.session_state.nova_scenario = scenario_choice
            st.session_state.nova_custom_scenario = custom_text
            st.session_state.nova_messages = []
            _init_welcome()
            st.rerun()

    # ── Chat history ─────────────────────────────────────────────────────────
    total_msgs = len(st.session_state.nova_messages)
    for idx, msg in enumerate(st.session_state.nova_messages):
        is_user = msg["role"] == "user"
        content = msg["content"]
        msg_num = idx + 1
        if is_user:
            st.markdown(
                f'<div class="nova-bubble-wrap">'
                f'<div class="nova-bubble-user">{content}</div>'
                f'<div class="nova-meta nova-meta-right">'
                f'You &nbsp;·&nbsp; <span class="nova-msg-count">#{msg_num}</span>'
                f'</div></div>',
                unsafe_allow_html=True)
        else:
            pname  = st.session_state.nova_persona
            pemoji = _get_persona()["emoji"]
            st.markdown(
                f'<div class="nova-bubble-wrap">'
                f'<div class="nova-bubble-ai">{content}</div>'
                f'<div class="nova-meta">'
                f'{pemoji} {pname} &nbsp;·&nbsp; <span class="nova-msg-count">#{msg_num}</span>'
                f'</div></div>',
                unsafe_allow_html=True)

    # ── Quick starters ────────────────────────────────────────────────────────
    if len(st.session_state.nova_messages) <= 1:
        st.markdown('<div class="nova-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:.78rem;color:{muted};margin-bottom:8px;font-weight:600;">⚡ QUICK STARTERS</div>', unsafe_allow_html=True)
        qs_cols = st.columns(2)
        for i, qs in enumerate(QUICK_STARTERS):
            with qs_cols[i % 2]:
                if st.button(qs, key=f"qs_{i}", use_container_width=True):
                    _send_message(qs)
                    st.rerun()

    # ── Input ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="nova-divider"></div>', unsafe_allow_html=True)
    with st.form(key="nova_form", clear_on_submit=True):
        pname = st.session_state.nova_persona
        user_input = st.text_area(
            "Message",
            placeholder=f"Say anything to {pname}… or describe the next scene…",
            label_visibility="collapsed",
            height=80,
        )
        submitted = st.form_submit_button(
            f"Send to {pname} {_get_persona()['emoji']}",
            use_container_width=True,
            type="primary"
        )

    if submitted and user_input.strip():
        _send_message(user_input.strip())
        st.rerun()


def _init_welcome():
    p = _get_persona()
    scenario = st.session_state.get("nova_scenario", "No Scenario")
    custom   = st.session_state.get("nova_custom_scenario", "")

    if scenario not in ("No Scenario", "📖 Write Our Own Story"):
        scene_desc = SCENARIOS.get(scenario, "")
        welcome = f"*[Scene: {scenario}]*\n\n{scene_desc}\n\n— — —\n\n{p['welcome']}"
    elif scenario == "📖 Write Our Own Story" and custom.strip():
        welcome = (
            f"*[Your Scenario]*\n\n{custom.strip()}\n\n— — —\n\n"
            f"I'm in. You've set the stage beautifully. Let's begin... {p['emoji']}"
        )
    else:
        welcome = p["welcome"]

    st.session_state.nova_messages = [{"role": "assistant", "content": welcome}]


def _build_system_prompt() -> str:
    p = _get_persona()
    base = p["prompt"]

    scenario = st.session_state.get("nova_scenario", "No Scenario")
    custom   = st.session_state.get("nova_custom_scenario", "")

    if scenario not in ("No Scenario", "📖 Write Our Own Story"):
        scene_desc = SCENARIOS.get(scenario, "")
        base += (
            f"\n\n── ACTIVE SCENARIO ──\n"
            f"You are in this scenario with the user:\n{scene_desc}\n"
            f"Stay in character. Build the narrative, add vivid details, create tension and atmosphere. "
            f"Make every reply advance the story while staying true to your persona."
        )
    elif scenario == "📖 Write Our Own Story" and custom.strip():
        base += (
            f"\n\n── CUSTOM SCENARIO ──\n"
            f"The user has set this scenario:\n{custom.strip()}\n"
            f"Step fully into this world. Honor the setting, the mood, and the relationships described."
        )

    return base


def _send_message(text: str):
    st.session_state.nova_messages.append({"role": "user", "content": text})

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.nova_messages
    ]

    try:
        model = st.session_state.get("model_choice", "llama-3.3-70b-versatile")
        reply = generate(
            messages=history,
            system=_build_system_prompt(),
            temperature=0.8, # Companions are more creative
            max_tokens=4096
        )
    except Exception as e:
        pname = st.session_state.nova_persona
        reply = f"*{pname} pauses — something flickered in the connection...* ({str(e)[:80]}) Try again?"

    st.session_state.nova_messages.append({"role": "assistant", "content": reply})
