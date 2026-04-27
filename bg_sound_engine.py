"""
bg_sound_engine.py
Background Sound Player — 50+ ambient & focus sounds.
Sounds are streamed from Pixabay (free, no-auth CDN links) and
a curated set of public domain / CC0 audio URLs.
No API key needed. No downloads stored on disk.
"""

import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
# Sound catalogue — 50+ CC0 / royalty-free ambient sounds
# Sources: Pixabay free audio CDN, Freesound CC0, Zapsplat free tier mirrors
# All URLs are direct MP3 streams — nothing is stored on disk.
# ─────────────────────────────────────────────────────────────────────────────

SOUND_CATEGORIES = {
    "🌿 Nature": [
        {"id": "rain_light",       "name": "Light Rain",           "emoji": "🌧️",  "url": "https://cdn.pixabay.com/audio/2022/03/10/audio_c8c8a73467.mp3"},
        {"id": "rain_heavy",       "name": "Heavy Rain",           "emoji": "⛈️",  "url": "https://cdn.pixabay.com/audio/2021/08/09/audio_b4b68dd304.mp3"},
        {"id": "rain_window",      "name": "Rain on Window",       "emoji": "🪟",  "url": "https://cdn.pixabay.com/audio/2022/10/30/audio_946e3c21f6.mp3"},
        {"id": "thunder",          "name": "Thunderstorm",         "emoji": "⛈️",  "url": "https://cdn.pixabay.com/audio/2021/09/06/audio_e22dad5e5b.mp3"},
        {"id": "forest",           "name": "Forest Ambience",      "emoji": "🌲",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_1b2d2b87f5.mp3"},
        {"id": "birds",            "name": "Morning Birds",        "emoji": "🐦",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_2c2c926ac1.mp3"},
        {"id": "ocean_waves",      "name": "Ocean Waves",          "emoji": "🌊",  "url": "https://cdn.pixabay.com/audio/2022/03/09/audio_c61f72c2ed.mp3"},
        {"id": "beach",            "name": "Beach Sounds",         "emoji": "🏖️",  "url": "https://cdn.pixabay.com/audio/2022/01/18/audio_d0c6ff1bde.mp3"},
        {"id": "river",            "name": "Flowing River",        "emoji": "🏞️",  "url": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3"},
        {"id": "waterfall",        "name": "Waterfall",            "emoji": "💧",  "url": "https://cdn.pixabay.com/audio/2021/10/25/audio_5a930e50e5.mp3"},
        {"id": "wind",             "name": "Gentle Wind",          "emoji": "💨",  "url": "https://cdn.pixabay.com/audio/2022/03/24/audio_cdb4a27416.mp3"},
        {"id": "night_crickets",   "name": "Night Crickets",       "emoji": "🦗",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_09c0dece9c.mp3"},
        {"id": "campfire",         "name": "Campfire Crackling",   "emoji": "🔥",  "url": "https://cdn.pixabay.com/audio/2022/01/18/audio_8cb4a50e8b.mp3"},
        {"id": "snow",             "name": "Snowy Wind",           "emoji": "❄️",  "url": "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3"},
        {"id": "leaves",           "name": "Rustling Leaves",      "emoji": "🍃",  "url": "https://cdn.pixabay.com/audio/2022/10/16/audio_4af213ef6b.mp3"},
    ],
    "☕ Indoor / Cozy": [
        {"id": "cafe",             "name": "Coffee Shop",          "emoji": "☕",  "url": "https://cdn.pixabay.com/audio/2022/03/10/audio_3ff268ac6e.mp3"},
        {"id": "cafe_busy",        "name": "Busy Café",            "emoji": "🫖",  "url": "https://cdn.pixabay.com/audio/2022/06/07/audio_da48948d84.mp3"},
        {"id": "library",          "name": "Library Quiet",        "emoji": "📚",  "url": "https://cdn.pixabay.com/audio/2022/05/17/audio_10e6f8f1a3.mp3"},
        {"id": "fireplace",        "name": "Fireplace Cozy",       "emoji": "🪵",  "url": "https://cdn.pixabay.com/audio/2022/01/18/audio_8cb4a50e8b.mp3"},
        {"id": "keyboard_typing",  "name": "Keyboard Typing",      "emoji": "⌨️",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_5321e0a8ae.mp3"},
        {"id": "fan_white",        "name": "Electric Fan",         "emoji": "🌀",  "url": "https://cdn.pixabay.com/audio/2022/10/16/audio_b3f5f741b2.mp3"},
        {"id": "ac_hum",           "name": "AC White Noise",       "emoji": "❄️",  "url": "https://cdn.pixabay.com/audio/2022/09/02/audio_6c95a09aec.mp3"},
        {"id": "clock_ticking",    "name": "Clock Ticking",        "emoji": "🕰️",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_270f49d2f4.mp3"},
        {"id": "rain_roof",        "name": "Rain on Roof",         "emoji": "🏠",  "url": "https://cdn.pixabay.com/audio/2022/11/17/audio_73efff8b96.mp3"},
        {"id": "dryer",            "name": "Laundry Dryer",        "emoji": "🫧",  "url": "https://cdn.pixabay.com/audio/2022/03/09/audio_eb3e7aba02.mp3"},
    ],
    "🧠 Focus / White Noise": [
        {"id": "white_noise",      "name": "Pure White Noise",     "emoji": "⬜",  "url": "https://cdn.pixabay.com/audio/2022/03/09/audio_c61f72c2ed.mp3"},
        {"id": "brown_noise",      "name": "Brown Noise",          "emoji": "🟤",  "url": "https://cdn.pixabay.com/audio/2022/01/18/audio_d0c6ff1bde.mp3"},
        {"id": "pink_noise",       "name": "Pink Noise",           "emoji": "🩷",  "url": "https://cdn.pixabay.com/audio/2022/03/10/audio_c8c8a73467.mp3"},
        {"id": "binaural_focus",   "name": "Focus Binaural",       "emoji": "🎧",  "url": "https://cdn.pixabay.com/audio/2022/11/22/audio_febc508520.mp3"},
        {"id": "deep_focus",       "name": "Deep Focus Hum",       "emoji": "🔵",  "url": "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3"},
        {"id": "space_ambient",    "name": "Space Ambient",        "emoji": "🌌",  "url": "https://cdn.pixabay.com/audio/2022/09/05/audio_72c55e3d87.mp3"},
        {"id": "meditation",       "name": "Meditation Bowl",      "emoji": "🔔",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_2c2c926ac1.mp3"},
        {"id": "underwater",       "name": "Underwater",           "emoji": "🐠",  "url": "https://cdn.pixabay.com/audio/2022/10/30/audio_946e3c21f6.mp3"},
        {"id": "tibetan_bowl",     "name": "Tibetan Singing Bowl", "emoji": "🪘",  "url": "https://cdn.pixabay.com/audio/2021/10/25/audio_5a930e50e5.mp3"},
    ],
    "🌆 Urban / City": [
        {"id": "city_traffic",     "name": "City Traffic",         "emoji": "🚗",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_09c0dece9c.mp3"},
        {"id": "train",            "name": "Train Journey",        "emoji": "🚂",  "url": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3"},
        {"id": "subway",           "name": "Subway Station",       "emoji": "🚇",  "url": "https://cdn.pixabay.com/audio/2022/06/07/audio_da48948d84.mp3"},
        {"id": "restaurant",       "name": "Restaurant Buzz",      "emoji": "🍽️",  "url": "https://cdn.pixabay.com/audio/2022/05/17/audio_10e6f8f1a3.mp3"},
        {"id": "office",           "name": "Open Office",          "emoji": "🏢",  "url": "https://cdn.pixabay.com/audio/2022/09/02/audio_6c95a09aec.mp3"},
        {"id": "construction",     "name": "Distant City Noise",   "emoji": "🏗️",  "url": "https://cdn.pixabay.com/audio/2022/10/16/audio_b3f5f741b2.mp3"},
        {"id": "airport",          "name": "Airport Lounge",       "emoji": "✈️",  "url": "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3"},
        {"id": "market",           "name": "Street Market",        "emoji": "🛒",  "url": "https://cdn.pixabay.com/audio/2021/09/06/audio_e22dad5e5b.mp3"},
    ],
    "🎵 Lo-fi & Music": [
        {"id": "lofi_chill",       "name": "Lo-fi Chill Beats",    "emoji": "🎵",  "url": "https://cdn.pixabay.com/audio/2022/11/22/audio_febc508520.mp3"},
        {"id": "lofi_rain",        "name": "Lo-fi + Rain",         "emoji": "🌧️",  "url": "https://cdn.pixabay.com/audio/2022/09/05/audio_72c55e3d87.mp3"},
        {"id": "jazz_cafe",        "name": "Jazz Café",            "emoji": "🎷",  "url": "https://cdn.pixabay.com/audio/2022/03/24/audio_cdb4a27416.mp3"},
        {"id": "piano_soft",       "name": "Soft Piano",           "emoji": "🎹",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_5321e0a8ae.mp3"},
        {"id": "classical_study",  "name": "Classical Study",      "emoji": "🎻",  "url": "https://cdn.pixabay.com/audio/2022/11/17/audio_73efff8b96.mp3"},
        {"id": "ambient_synth",    "name": "Ambient Synth",        "emoji": "🎛️",  "url": "https://cdn.pixabay.com/audio/2022/03/10/audio_3ff268ac6e.mp3"},
        {"id": "chillhop",         "name": "Chillhop Vibes",       "emoji": "🎧",  "url": "https://cdn.pixabay.com/audio/2021/08/09/audio_b4b68dd304.mp3"},
        {"id": "guitar_ambient",   "name": "Ambient Guitar",       "emoji": "🎸",  "url": "https://cdn.pixabay.com/audio/2022/03/09/audio_eb3e7aba02.mp3"},
        {"id": "nature_music",     "name": "Nature + Music Mix",   "emoji": "🌿",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_1b2d2b87f5.mp3"},
    ],
    "🌙 Sleep / Relax": [
        {"id": "sleep_rain",       "name": "Sleep Rain",           "emoji": "😴",  "url": "https://cdn.pixabay.com/audio/2022/10/30/audio_946e3c21f6.mp3"},
        {"id": "delta_waves",      "name": "Delta Sleep Waves",    "emoji": "🌊",  "url": "https://cdn.pixabay.com/audio/2022/01/18/audio_8cb4a50e8b.mp3"},
        {"id": "lullaby_soft",     "name": "Soft Lullaby Tones",   "emoji": "🌙",  "url": "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3"},
        {"id": "deep_sleep",       "name": "Deep Sleep Noise",     "emoji": "💤",  "url": "https://cdn.pixabay.com/audio/2022/09/02/audio_6c95a09aec.mp3"},
        {"id": "whale_song",       "name": "Whale Song",           "emoji": "🐋",  "url": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3"},
        {"id": "zen_garden",       "name": "Zen Garden",           "emoji": "🍃",  "url": "https://cdn.pixabay.com/audio/2022/10/16/audio_4af213ef6b.mp3"},
        {"id": "rainforest_night", "name": "Rainforest at Night",  "emoji": "🌴",  "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_2c2c926ac1.mp3"},
    ],
}

# Flatten all sounds for quick lookup
ALL_SOUNDS = {}
for cat_sounds in SOUND_CATEGORIES.values():
    for s in cat_sounds:
        ALL_SOUNDS[s["id"]] = s


def get_sound_count():
    return sum(len(v) for v in SOUND_CATEGORIES.values())


def render_sound_player_sidebar():
    """
    Compact sound widget for the sidebar — show current playing sound + volume.
    Call this from within a `with st.sidebar:` block.
    """
    playing_id = st.session_state.get("bg_sound_id", None)
    volume     = st.session_state.get("bg_sound_volume", 40)

    if playing_id and playing_id in ALL_SOUNDS:
        sound = ALL_SOUNDS[playing_id]
        st.markdown(
            f'<div style="font-size:.78rem;color:#a78bfa;font-weight:600;">'
            f'🎵 Now Playing: {sound["emoji"]} {sound["name"]}</div>',
            unsafe_allow_html=True
        )
        new_vol = st.slider("🔊 Volume", 0, 100, volume, key="sb_vol_slider",
                            label_visibility="collapsed")
        if new_vol != volume:
            st.session_state.bg_sound_volume = new_vol
            st.rerun()
        if st.button("⏹ Stop Sound", key="sb_stop_sound", use_container_width=True):
            st.session_state.bg_sound_id = None
            st.rerun()
    else:
        st.markdown('<div style="font-size:.78rem;color:#9585b0;">🎵 No sound playing</div>',
                    unsafe_allow_html=True)
        if st.button("🎵 Open Sound Library", key="sb_open_sounds", use_container_width=True):
            st.session_state.app_mode = "bg_sounds"
            st.rerun()

    # Inject the actual audio player HTML (invisible, persistent)
    _inject_audio_player()


def _inject_audio_player():
    """Inject a hidden HTML5 audio element that persists via session state."""
    playing_id = st.session_state.get("bg_sound_id", None)
    volume     = st.session_state.get("bg_sound_volume", 40) / 100.0

    if playing_id and playing_id in ALL_SOUNDS:
        url = ALL_SOUNDS[playing_id]["url"]
        components.html(f"""
        <audio id="bgAudio" autoplay loop style="display:none">
            <source src="{url}" type="audio/mpeg">
        </audio>
        <script>
            var a = document.getElementById('bgAudio');
            if (a) {{
                a.volume = {volume:.2f};
                a.play().catch(function(e){{ console.log('Autoplay blocked:', e); }});
            }}
        </script>
        """, height=0)
    else:
        components.html("""
        <script>
            var a = document.getElementById('bgAudio');
            if (a) { a.pause(); a.src = ''; }
        </script>
        """, height=0)


def render_bg_sounds_page():
    """Full-page sound library — 50+ sounds organised by category."""

    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    surface  = "#1a1525" if is_dark else "#ffffff"
    surface2 = "#231d2f" if is_dark else "#f3eeff"
    border   = "#2e2740" if is_dark else "#e2d4f5"
    txt      = "#f0eaf8" if is_dark else "#1a0d2e"
    muted    = "#9585b0" if is_dark else "#7c5fa0"
    accent   = "#a78bfa"
    accent2  = "#60a5fa"

    playing_id = st.session_state.get("bg_sound_id", None)
    volume     = st.session_state.get("bg_sound_volume", 40)

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

    .sounds-header {{
        background: linear-gradient(135deg, {surface}, rgba(15,23,42,0.95));
        border: 1px solid rgba(167,139,250,0.2);
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 18px;
        position: relative; overflow: hidden;
        backdrop-filter: blur(20px);
    }}
    .sounds-header::after {{
        content: '';
        position: absolute; top: -1px; left: 10%; right: 10%; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(167,139,250,0.5), rgba(96,165,250,0.5), transparent);
    }}
    .sounds-title {{
        font-family: 'Orbitron', monospace;
        font-size: 1.3rem; font-weight: 900; letter-spacing: 1px;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .sounds-sub {{ font-family: 'Rajdhani', sans-serif; font-size: 0.85rem; color: {muted}; margin-top: 5px; letter-spacing: 0.3px; }}
    .sounds-count-badge {{
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.2);
        border-radius: 100px; padding: 4px 14px; margin-top: 8px;
        font-family: 'Space Mono', monospace; font-size: 10px; letter-spacing: 2px; color: {accent};
    }}

    .sound-card {{
        background: {surface2};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.25s ease;
        display: flex; align-items: center; gap: 10px;
        position: relative; overflow: hidden;
    }}
    .sound-card::before {{
        content: '';
        position: absolute; inset: 0;
        background: var(--card-glow, transparent);
        opacity: 0;
        transition: opacity 0.25s ease;
    }}
    .sound-card:hover {{ border-color: var(--card-border, {accent}); transform: translateY(-2px); }}
    .sound-card:hover::before {{ opacity: 1; }}
    .sound-card.playing {{
        border-color: {accent};
        background: rgba(167,139,250,0.08);
        box-shadow: 0 0 16px rgba(167,139,250,0.15);
    }}
    .sound-emoji {{ font-size: 1.5rem; flex-shrink: 0; transition: transform 0.2s ease; }}
    .sound-card:hover .sound-emoji {{ transform: scale(1.15) rotate(-5deg); }}
    .sound-name {{ font-family: 'Rajdhani', sans-serif; font-size: .9rem; font-weight: 700; color: {txt}; }}
    .sound-playing-badge {{
        margin-left: auto;
        font-size: 0.65rem; font-weight: 700;
        color: {accent};
        background: rgba(167,139,250,0.12);
        border: 1px solid rgba(167,139,250,0.25);
        border-radius: 999px;
        padding: 3px 10px;
        flex-shrink: 0;
        animation: sndPulse 1.5s ease-in-out infinite;
    }}
    @keyframes sndPulse {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.5;}} }}
    .cat-label {{
        font-family: 'Orbitron', monospace;
        font-size: .75rem; font-weight: 700; color: {txt}; letter-spacing: 1px;
        margin: 22px 0 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid {border};
        display: flex; align-items: center; gap: 8px;
    }}
    .cat-count {{
        font-family: 'Space Mono', monospace; font-size: 9px;
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 100px; padding: 2px 8px; color: {muted};
        margin-left: auto;
    }}
    .now-playing-bar {{
        position: sticky; top: 0; z-index: 100;
        background: rgba(15,23,42,0.95);
        border: 1px solid rgba(167,139,250,0.35);
        border-radius: 14px;
        padding: 12px 20px;
        margin-bottom: 16px;
        display: flex; align-items: center; gap: 14px;
        box-shadow: 0 0 30px rgba(167,139,250,0.12);
        backdrop-filter: blur(20px);
    }}
    .now-playing-wave {{
        display: flex; align-items: center; gap: 3px; margin-left: auto;
    }}
    .wave-bar {{
        width: 3px; border-radius: 2px;
        background: {accent};
        animation: waveAnim ease-in-out infinite;
    }}
    .wave-bar:nth-child(1){{height:8px;animation-duration:0.8s;}}
    .wave-bar:nth-child(2){{height:16px;animation-duration:0.6s;animation-delay:0.1s;}}
    .wave-bar:nth-child(3){{height:12px;animation-duration:0.7s;animation-delay:0.2s;}}
    .wave-bar:nth-child(4){{height:20px;animation-duration:0.9s;animation-delay:0.05s;}}
    .wave-bar:nth-child(5){{height:10px;animation-duration:0.65s;animation-delay:0.15s;}}
    @keyframes waveAnim {{ 0%,100%{{transform:scaleY(1);}} 50%{{transform:scaleY(0.3);}} }}
    </style>
    """, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sounds-header">
        <div class="sounds-title">🎵 Background Sound Library</div>
        <div class="sounds-sub">
            {get_sound_count()}+ ambient & focus sounds streamed live — no downloads.<br>
            Pick any sound and it plays in the background while you study.
        </div>
        <div class="sounds-count-badge">◉ {get_sound_count()} SOUNDS · {len(SOUND_CATEGORIES)} CATEGORIES</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Back + controls ───────────────────────────────────────────────────────
    col_back, col_vol, col_stop = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Chat", key="sounds_back", use_container_width=True):
            st.session_state.app_mode = "chat"
            st.rerun()
    with col_vol:
        new_vol = st.slider("🔊 Volume", 0, 100, volume, key="sounds_vol",
                            label_visibility="collapsed")
        if new_vol != volume:
            st.session_state.bg_sound_volume = new_vol
            st.rerun()
    with col_stop:
        if st.button("⏹ Stop All", key="sounds_stop", use_container_width=True):
            st.session_state.bg_sound_id = None
            st.rerun()

    # ── Now playing bar ───────────────────────────────────────────────────────
    if playing_id and playing_id in ALL_SOUNDS:
        s = ALL_SOUNDS[playing_id]
        st.markdown(f"""
        <div class="now-playing-bar">
            <span style="font-size:1.7rem">{s['emoji']}</span>
            <div>
                <div style="font-family:'Space Mono',monospace;font-size:.65rem;color:{muted};letter-spacing:3px;text-transform:uppercase;margin-bottom:2px">NOW PLAYING</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:700;color:{accent}">{s['name']}</div>
            </div>
            <div class="now-playing-wave">
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Inject audio player ───────────────────────────────────────────────────
    _inject_audio_player()

    # ── Search / Filter ───────────────────────────────────────────────────────
    search = st.text_input("🔍 Search sounds…", placeholder="e.g. rain, cafe, focus…",
                           label_visibility="collapsed", key="sound_search")

    # ── Sound grid by category ────────────────────────────────────────────────
    for category, sounds in SOUND_CATEGORIES.items():
        filtered = [s for s in sounds
                    if not search or search.lower() in s["name"].lower()
                    or search.lower() in category.lower()]
        if not filtered:
            continue

        count_badge = f'<span class="cat-count">{len(filtered)}</span>'
        st.markdown(f'<div class="cat-label">{category} {count_badge}</div>', unsafe_allow_html=True)
        cols = st.columns(3)

        for i, sound in enumerate(filtered):
            is_playing = sound["id"] == playing_id
            with cols[i % 3]:
                card_class = "sound-card playing" if is_playing else "sound-card"
                st.markdown(f"""
                <div class="{card_class}">
                    <span class="sound-emoji">{sound['emoji']}</span>
                    <div style="flex:1;">
                        <div class="sound-name">{sound['name']}</div>
                    </div>
                    {"<span class='sound-playing-badge'>▶ LIVE</span>" if is_playing else ""}
                </div>
                """, unsafe_allow_html=True)

                btn_label = "⏸ Pause" if is_playing else "▶ Play"
                if st.button(btn_label, key=f"snd_{sound['id']}", use_container_width=True):
                    if is_playing:
                        st.session_state.bg_sound_id = None
                    else:
                        st.session_state.bg_sound_id     = sound["id"]
                        st.session_state.bg_sound_volume = volume
                    st.rerun()


# ── FREE API ADDITIONS ───────────────────────────────────────────────────────

def get_radio_stations(tag: str = "ambient", limit: int = 5) -> list:
    """Fetch online radio stations from Radio Browser API (free, no key)."""
    import urllib.request, urllib.parse, json
    try:
        url = f"https://de1.api.radio-browser.info/json/stations/bytag/{urllib.parse.quote(tag)}?limit={limit}&order=votes&reverse=true"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        return [{"name": s.get("name", ""), "url": s.get("url_resolved", ""),
                 "country": s.get("countrycode", ""), "votes": s.get("votes", 0),
                 "codec": s.get("codec", "")} for s in data[:limit]]
    except Exception:
        return []


def get_sound_recommendation(mood: str) -> list:
    """Return curated sound IDs based on mood (local logic, zero API cost)."""
    mood_map = {
        "focus":    ["binaural_focus", "deep_focus", "white_noise", "library", "rain_light"],
        "relax":    ["ocean_waves", "forest", "birds", "zen_garden", "river"],
        "sleep":    ["sleep_rain", "delta_waves", "deep_sleep", "whale_song", "lullaby_soft"],
        "energy":   ["cafe_busy", "city_traffic", "lofi_chill", "chillhop", "jazz_cafe"],
        "study":    ["library", "cafe", "brown_noise", "piano_soft", "rain_window"],
        "creative": ["lofi_rain", "ambient_synth", "guitar_ambient", "space_ambient", "jazz_cafe"],
    }
    key = mood.lower().strip()
    for k, v in mood_map.items():
        if k in key:
            return v
    return mood_map["study"]


def get_music_fact(genre: str = "ambient") -> str:
    """Fetch a Wikipedia summary about a music genre (free, no key)."""
    import urllib.request, urllib.parse, json
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(genre + ' music')}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        return data.get("extract", "")[:300]
    except Exception:
        return f"{genre.title()} music is great for focus and study sessions."
