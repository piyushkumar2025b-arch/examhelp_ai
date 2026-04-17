"""
ui_enhancements.py — ExamHelp AI Premium UI Components v1.0
============================================================
Purely ADDITIVE — no existing files modified.
Import any function from this module and call it from app.py or new_features.py
to inject the enhanced UI block at that location.

Usage:
    from ui_enhancements import (
        inject_premium_css,
        render_live_stats_bar,
        render_api_explorer_panel,
        render_topic_spotlight,
        render_world_clock_bar,
        render_knowledge_pulse,
        render_study_break_widget,
        render_crypto_ticker,
        render_space_widget,
        render_mini_science_feed,
    )
"""
from __future__ import annotations
import datetime
import streamlit as st
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS INJECTION
# ══════════════════════════════════════════════════════════════════════════════

def inject_premium_css() -> None:
    """
    Inject additional premium CSS on top of what app.py already loads.
    Call once at the top of any page render.
    """
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@300;400;600;800&display=swap');

/* ── ENHANCED CSS VARIABLES ── */
:root {
    --eh-green:  #00ffb4;
    --eh-blue:   #00aaff;
    --eh-purple: #b44dff;
    --eh-pink:   #ff44aa;
    --eh-gold:   #ffaa00;
    --eh-glow-g: rgba(0,255,180,0.15);
    --eh-glow-b: rgba(0,170,255,0.15);
    --eh-glow-p: rgba(180,77,255,0.15);
    --card-bg:   rgba(15,20,35,0.7);
    --card-border: rgba(255,255,255,0.06);
    --card-hover: rgba(255,255,255,0.1);
}

/* ── PREMIUM STAT PILL ── */
.eh-stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 100px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: rgba(255,255,255,0.65);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}
.eh-stat-pill:hover {
    background: rgba(0,255,180,0.06);
    border-color: rgba(0,255,180,0.25);
    color: #00ffb4;
}
.eh-stat-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    animation: statPulse 2s ease infinite;
}
@keyframes statPulse {
    0%,100% { opacity:0.5; transform: scale(1); }
    50%      { opacity:1;   transform: scale(1.4); }
}

/* ── PREMIUM CARD ── */
.eh-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 18px;
    padding: 20px 22px;
    backdrop-filter: blur(16px);
    transition: all 0.35s cubic-bezier(.16,1,.3,1);
    position: relative;
    overflow: hidden;
}
.eh-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 18px;
    padding: 1px;
    background: linear-gradient(135deg, rgba(0,255,180,0.08), transparent 60%, rgba(0,170,255,0.06));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
}
.eh-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0,255,180,0.15);
    box-shadow: 0 20px 60px rgba(0,255,180,0.06), 0 8px 30px rgba(0,0,0,0.4);
}

/* ── TICKER STRIP ── */
.eh-ticker {
    display: flex;
    gap: 20px;
    overflow: hidden;
    padding: 10px 0;
    border-top: 1px solid rgba(255,255,255,0.05);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    margin: 12px 0;
}
.eh-ticker-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}

/* ── GLOW BADGE ── */
.eh-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 100px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.eh-badge-green { background: rgba(0,255,180,0.1); color: #00ffb4; border: 1px solid rgba(0,255,180,0.2); }
.eh-badge-blue  { background: rgba(0,170,255,0.1); color: #00aaff; border: 1px solid rgba(0,170,255,0.2); }
.eh-badge-purple{ background: rgba(180,77,255,0.1); color: #b44dff; border: 1px solid rgba(180,77,255,0.2); }
.eh-badge-gold  { background: rgba(255,170,0,0.1);  color: #ffaa00; border: 1px solid rgba(255,170,0,0.2); }
.eh-badge-red   { background: rgba(255,68,100,0.1); color: #ff4464; border: 1px solid rgba(255,68,100,0.2); }

/* ── WORLD CLOCK ── */
.eh-clock-grid {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: space-evenly;
}
.eh-clock-cell {
    text-align: center;
    padding: 12px 18px;
    border-radius: 14px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    min-width: 90px;
    transition: all 0.3s ease;
}
.eh-clock-cell:hover {
    background: rgba(0,255,180,0.05);
    border-color: rgba(0,255,180,0.2);
}
.eh-clock-city {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    color: rgba(255,255,255,0.3);
    text-transform: uppercase;
    margin-bottom: 4px;
}
.eh-clock-time {
    font-family: 'Outfit', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #fff;
}
.eh-clock-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: rgba(255,255,255,0.25);
    margin-top: 3px;
}

/* ── KNOWLEDGE PULSE CARD ── */
.eh-pulse-card {
    border-left: 3px solid var(--eh-green);
    padding: 14px 18px;
    border-radius: 0 14px 14px 0;
    background: rgba(0,255,180,0.03);
    margin-bottom: 10px;
    transition: all 0.3s ease;
}
.eh-pulse-card:hover {
    background: rgba(0,255,180,0.06);
    border-left-color: var(--eh-blue);
    transform: translateX(4px);
}
.eh-pulse-title {
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: rgba(255,255,255,0.9);
    margin-bottom: 4px;
}
.eh-pulse-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: rgba(255,255,255,0.3);
}

/* ── TOPIC SPOTLIGHT ── */
.eh-spotlight {
    background: linear-gradient(135deg, rgba(0,255,180,0.04) 0%, rgba(0,170,255,0.04) 100%);
    border: 1px solid rgba(0,255,180,0.1);
    border-radius: 20px;
    padding: 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.eh-spotlight::after {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(0,255,180,0.04) 0%, transparent 60%);
    animation: spotlightRotate 8s linear infinite;
    pointer-events: none;
}
@keyframes spotlightRotate { to { transform: rotate(360deg); } }
.eh-spotlight-emoji { font-size: 42px; margin-bottom: 12px; display: block; }
.eh-spotlight-word {
    font-family: 'Outfit', sans-serif;
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(90deg, #00ffb4, #00aaff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
}
.eh-spotlight-def {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: rgba(255,255,255,0.6);
    line-height: 1.7;
    max-width: 500px;
    margin: 0 auto;
}

/* ── CRYPTO TICKER ── */
.eh-crypto-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-radius: 12px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 8px;
    transition: all 0.3s ease;
}
.eh-crypto-row:hover {
    background: rgba(255,255,255,0.045);
    border-color: rgba(255,255,255,0.1);
}
.eh-crypto-name { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 600; color: #fff; }
.eh-crypto-sym  { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: rgba(255,255,255,0.3); }
.eh-crypto-price{ font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #fff; }
.eh-change-pos  { color: #00ffb4; font-family: 'JetBrains Mono', monospace; font-size: 11px; }
.eh-change-neg  { color: #ff4464; font-family: 'JetBrains Mono', monospace; font-size: 11px; }

/* ── SECTION HEADER ── */
.eh-section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.eh-section-icon {
    width: 32px; height: 32px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    background: rgba(0,255,180,0.08);
    border: 1px solid rgba(0,255,180,0.15);
}
.eh-section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: rgba(255,255,255,0.9);
}
.eh-section-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: rgba(255,255,255,0.3);
    letter-spacing: 1.5px;
    margin-top: 1px;
}

/* ── SHIMMER SKELETON ── */
.eh-skeleton {
    background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%);
    background-size: 400% 100%;
    animation: shimmer 1.5s ease infinite;
    border-radius: 8px;
    height: 14px;
    margin-bottom: 8px;
}
@keyframes shimmer { 0%{background-position:100% 50%} 100%{background-position:0% 50%} }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LIVE STATS BAR
# ══════════════════════════════════════════════════════════════════════════════

def render_live_stats_bar() -> None:
    """
    Top-of-page live status bar showing ISS position, earthquake alert,
    BTC price, and UTC time — all from zero-auth free APIs.
    Cached per session so it only hits APIs once.
    """
    inject_premium_css()

    # Pull from cache or fetch fresh
    _key = "_ui_stats_bar"
    if _key not in st.session_state:
        stats: dict = {}
        try:
            from free_apis import get_iss_location, get_crypto_price, get_earthquakes
            iss = get_iss_location()
            if iss:
                stats["iss"] = f"🛸 ISS  {iss.get('lat',0):.1f}°N  {iss.get('lon',0):.1f}°E"
            btc = get_crypto_price("bitcoin")
            if btc and btc.get("price"):
                p = btc["price"]
                c = btc.get("change_24h", 0)
                arrow = "▲" if c >= 0 else "▼"
                stats["btc"] = f"₿ ${p:,.0f}  {arrow}{abs(c):.1f}%"
                stats["btc_up"] = c >= 0
            quakes = get_earthquakes(feed="significant_week", limit=1)
            if quakes:
                q = quakes[0]
                stats["quake"] = f"🌍 M{q.get('magnitude','?')} {q.get('place','Unknown')[:30]}"
        except Exception:
            pass
        stats["utc"] = datetime.datetime.utcnow().strftime("🕐 UTC %H:%M")
        st.session_state[_key] = stats

    stats = st.session_state.get(_key, {})
    pills = []
    if stats.get("utc"):
        pills.append(f'<span class="eh-stat-pill"><span class="eh-stat-dot" style="background:#00aaff"></span>{stats["utc"]}</span>')
    if stats.get("iss"):
        pills.append(f'<span class="eh-stat-pill"><span class="eh-stat-dot" style="background:#00ffb4"></span>{stats["iss"]}</span>')
    if stats.get("btc"):
        col = "#00ffb4" if stats.get("btc_up") else "#ff4464"
        pills.append(f'<span class="eh-stat-pill"><span class="eh-stat-dot" style="background:{col}"></span>{stats["btc"]}</span>')
    if stats.get("quake"):
        pills.append(f'<span class="eh-stat-pill"><span class="eh-stat-dot" style="background:#ffaa00"></span>{stats["quake"]}</span>')

    html = f"""
<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:10px 0;margin-bottom:12px;">
  {''.join(pills)}
</div>"""
    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# WORLD CLOCK BAR
# ══════════════════════════════════════════════════════════════════════════════

_WORLD_CITIES = [
    ("New York",  "America/New_York",  "🗽"),
    ("London",    "Europe/London",     "🎡"),
    ("Dubai",     "Asia/Dubai",        "🏙️"),
    ("Mumbai",    "Asia/Kolkata",      "🇮🇳"),
    ("Singapore", "Asia/Singapore",   "🌴"),
    ("Tokyo",     "Asia/Tokyo",        "⛩️"),
    ("Sydney",    "Australia/Sydney",  "🦘"),
]


def render_world_clock_bar() -> None:
    """Compact world clock — shows current time in 7 major cities."""
    inject_premium_css()
    try:
        import zoneinfo
        def _city_time(tz_name: str) -> tuple[str, str]:
            tz = zoneinfo.ZoneInfo(tz_name)
            dt = datetime.datetime.now(tz)
            return dt.strftime("%H:%M"), dt.strftime("%a %d")
    except ImportError:
        def _city_time(tz_name: str) -> tuple[str, str]:
            return "--:--", "---"

    cells = ""
    for city, tz, flag in _WORLD_CITIES:
        t, d = _city_time(tz)
        cells += f"""
<div class="eh-clock-cell">
  <div class="eh-clock-city">{flag} {city}</div>
  <div class="eh-clock-time">{t}</div>
  <div class="eh-clock-date">{d}</div>
</div>"""

    st.markdown(f"""
<div class="eh-card" style="margin-bottom:16px;">
  <div class="eh-section-header">
    <div class="eh-section-icon">🌐</div>
    <div>
      <div class="eh-section-title">World Clock</div>
      <div class="eh-section-sub">LIVE LOCAL TIMES</div>
    </div>
  </div>
  <div class="eh-clock-grid">{cells}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE PULSE — Latest Academic Papers
# ══════════════════════════════════════════════════════════════════════════════

def render_knowledge_pulse(topic: str = "machine learning", limit: int = 4) -> None:
    """
    Shows latest arXiv papers on a topic as a sleek feed.
    Results are session-cached — no repeat API calls.
    """
    inject_premium_css()
    _key = f"_kp_{topic[:20]}"

    if _key not in st.session_state:
        papers = []
        try:
            from free_apis import search_arxiv
            papers = search_arxiv(topic, max_results=limit)
        except Exception:
            pass
        st.session_state[_key] = papers

    papers = st.session_state.get(_key, [])
    if not papers:
        return

    cards = ""
    for p in papers[:limit]:
        authors = ", ".join(p.get("authors", [])[:2])
        if len(p.get("authors", [])) > 2:
            authors += " et al."
        title = p.get("title", "")[:90]
        year  = p.get("published", "")[:4]
        url   = p.get("url", "#")
        cats  = " · ".join(p.get("categories", [])[:2])
        cards += f"""
<div class="eh-pulse-card">
  <div class="eh-pulse-title">{title}{'…' if len(p.get('title',''))>90 else ''}</div>
  <div class="eh-pulse-meta">{authors} &nbsp;·&nbsp; {year} &nbsp;·&nbsp; <span style="color:rgba(0,255,180,0.5)">{cats}</span>
    &nbsp;<a href="{url}" target="_blank" style="color:rgba(0,170,255,0.6);font-size:10px;text-decoration:none;">↗ arXiv</a>
  </div>
</div>"""

    st.markdown(f"""
<div class="eh-card" style="margin-bottom:16px;">
  <div class="eh-section-header">
    <div class="eh-section-icon">📡</div>
    <div>
      <div class="eh-section-title">Knowledge Pulse</div>
      <div class="eh-section-sub">LATEST ARXIV · {topic.upper()}</div>
    </div>
  </div>
  {cards}
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TOPIC SPOTLIGHT — Word / Concept of the Day
# ══════════════════════════════════════════════════════════════════════════════

_SPOTLIGHT_WORDS = [
    ("Osmosis",        "🌊", "passive movement of water molecules across a selectively permeable membrane from a region of higher water potential to a region of lower water potential"),
    ("Photosynthesis", "🌿", "process used by plants and other organisms to convert light energy into chemical energy stored in glucose"),
    ("Entropy",        "🌀", "a thermodynamic quantity representing the unavailability of a system's thermal energy for conversion into mechanical work"),
    ("Mitosis",        "🧬", "a type of cell division resulting in two genetically identical daughter cells, each having the same number of chromosomes as the parent"),
    ("Electrolysis",   "⚡", "chemical decomposition produced by passing an electric current through a liquid or solution containing ions"),
    ("Momentum",       "🎯", "the quantity of motion of a moving body, measured as a product of its mass and velocity"),
    ("Supernova",      "💥", "a powerful and luminous stellar explosion that occurs at the end of certain stars' lives"),
    ("Hegemony",       "🏛️", "leadership or dominance, especially of one country or social group over others"),
    ("Cognition",      "🧠", "the mental action or process of acquiring knowledge and understanding through thought, experience, and the senses"),
    ("Catalyst",       "⚗️", "a substance that increases the rate of a chemical reaction without itself undergoing any permanent chemical change"),
]


def render_topic_spotlight(day_offset: int = 0) -> None:
    """
    Displays an animated word/concept card that cycles daily.
    day_offset lets you ask for tomorrow's or yesterday's word.
    """
    inject_premium_css()
    idx = (datetime.date.today().toordinal() + day_offset) % len(_SPOTLIGHT_WORDS)
    word, emoji, definition = _SPOTLIGHT_WORDS[idx]

    st.markdown(f"""
<div class="eh-spotlight" style="margin-bottom:16px;">
  <span class="eh-spotlight-emoji">{emoji}</span>
  <div class="eh-spotlight-word">{word}</div>
  <div style="margin:8px 0 4px;">
    <span class="eh-badge eh-badge-green">CONCEPT OF THE DAY</span>
  </div>
  <div class="eh-spotlight-def">{definition}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CRYPTO TICKER
# ══════════════════════════════════════════════════════════════════════════════

_CRYPTO_NAMES = {
    "bitcoin": ("Bitcoin",  "BTC", "₿"),
    "ethereum": ("Ethereum", "ETH", "Ξ"),
    "solana":   ("Solana",   "SOL", "◎"),
    "dogecoin": ("Dogecoin", "DOGE","Ð"),
    "cardano":  ("Cardano",  "ADA", "₳"),
}


def render_crypto_ticker(coins: list[str] | None = None, compact: bool = False) -> None:
    """
    Render a live crypto price ticker.
    coins: list of CoinGecko IDs. Default = top 5.
    compact: single-line pill mode (for sidebars).
    """
    inject_premium_css()
    if coins is None:
        coins = list(_CRYPTO_NAMES.keys())

    _key = "_crypto_ticker_" + "_".join(coins[:5])
    if _key not in st.session_state:
        prices = {}
        try:
            from free_apis import get_crypto_batch
            prices = get_crypto_batch(coins) or {}
        except Exception:
            pass
        st.session_state[_key] = prices

    prices = st.session_state.get(_key, {})

    if compact:
        pills = ""
        for coin_id in coins[:5]:
            meta = _CRYPTO_NAMES.get(coin_id, (coin_id.title(), coin_id.upper(), "$"))
            data = prices.get(coin_id, {})
            if not data:
                continue
            p = data.get("price", 0)
            c = data.get("change_24h", 0)
            col = "#00ffb4" if c >= 0 else "#ff4464"
            pills += f'<span class="eh-stat-pill"><span class="eh-stat-dot" style="background:{col}"></span>{meta[2]} <strong style="color:{col}">${p:,.2f}</strong></span>'
        st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{pills}</div>', unsafe_allow_html=True)
        return

    rows = ""
    for coin_id in coins[:6]:
        meta = _CRYPTO_NAMES.get(coin_id, (coin_id.title(), coin_id.upper(), "$"))
        data = prices.get(coin_id, {})
        if not data:
            continue
        p  = data.get("price", 0)
        c  = data.get("change_24h", 0)
        col = "#00ffb4" if c >= 0 else "#ff4464"
        arrow = "▲" if c >= 0 else "▼"
        rows += f"""
<div class="eh-crypto-row">
  <div>
    <div class="eh-crypto-name">{meta[2]} {meta[0]}</div>
    <div class="eh-crypto-sym">{meta[1]}</div>
  </div>
  <div style="text-align:right;">
    <div class="eh-crypto-price">${p:,.4f}</div>
    <div style="color:{col};font-family:'JetBrains Mono',monospace;font-size:11px;">{arrow} {abs(c):.2f}%</div>
  </div>
</div>"""

    st.markdown(f"""
<div class="eh-card" style="margin-bottom:16px;">
  <div class="eh-section-header">
    <div class="eh-section-icon">🪙</div>
    <div>
      <div class="eh-section-title">Crypto Market</div>
      <div class="eh-section-sub">LIVE · COINGECKO · NO KEY</div>
    </div>
  </div>
  {rows}
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SPACE WIDGET — NASA APOD + SpaceX Latest Launch
# ══════════════════════════════════════════════════════════════════════════════

def render_space_widget() -> None:
    """
    Compact space dashboard: NASA APOD title + SpaceX latest launch status.
    Session-cached — hits APIs only once per session.
    """
    inject_premium_css()
    _key = "_space_widget"
    if _key not in st.session_state:
        data: dict = {}
        try:
            from free_apis import get_nasa_apod, get_latest_spacex_launch
            apod = get_nasa_apod()
            if apod:
                data["apod"] = apod
            sx = get_latest_spacex_launch()
            if sx:
                data["spacex"] = sx
        except Exception:
            pass
        st.session_state[_key] = data

    data = st.session_state.get(_key, {})
    apod  = data.get("apod", {})
    spacex = data.get("spacex", {})

    apod_html = ""
    if apod:
        media = apod.get("media_type", "image")
        if media == "image":
            apod_html = f'<img src="{apod["url"]}" style="width:100%;border-radius:12px;margin-bottom:10px;max-height:200px;object-fit:cover;">'
        apod_html += f"""
<div style="font-family:'Outfit',sans-serif;font-size:13px;font-weight:700;color:#fff;margin-bottom:4px;">{apod.get('title','')}</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(255,255,255,0.3);">{apod.get('date','')}</div>
<div style="font-family:'Inter',sans-serif;font-size:12px;color:rgba(255,255,255,0.55);line-height:1.6;margin-top:6px;">{apod.get('explanation','')[:200]}…</div>
"""

    sx_html = ""
    if spacex:
        success = spacex.get("success")
        status_badge = (
            '<span class="eh-badge eh-badge-green">SUCCESS</span>' if success is True else
            '<span class="eh-badge eh-badge-red">FAILED</span>'   if success is False else
            '<span class="eh-badge eh-badge-gold">PENDING</span>'
        )
        patch = spacex.get("links", {}).get("patch", "")
        patch_img = f'<img src="{patch}" style="width:52px;height:52px;border-radius:8px;margin-right:12px;flex-shrink:0;">' if patch else ""
        sx_html = f"""
<div style="display:flex;align-items:center;margin-top:14px;padding:14px;border-radius:14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);">
  {patch_img}
  <div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:rgba(255,255,255,0.3);letter-spacing:2px;margin-bottom:4px;">LATEST SPACEX LAUNCH</div>
    <div style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:700;color:#fff;margin-bottom:4px;">{spacex.get('name','')}</div>
    <div style="display:flex;align-items:center;gap:8px;">{status_badge}<span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(255,255,255,0.3);">{spacex.get('date','')}</span></div>
  </div>
</div>"""

    if not apod_html and not sx_html:
        return

    st.markdown(f"""
<div class="eh-card" style="margin-bottom:16px;">
  <div class="eh-section-header">
    <div class="eh-section-icon">🔭</div>
    <div>
      <div class="eh-section-title">Space Intelligence</div>
      <div class="eh-section-sub">NASA APOD · SPACEX LIVE</div>
    </div>
  </div>
  {apod_html}
  {sx_html}
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MINI SCIENCE FEED — SpaceFlight News + HackerNews
# ══════════════════════════════════════════════════════════════════════════════

def render_mini_science_feed(limit: int = 3) -> None:
    """
    Compact science + tech news feed from SpaceflightNewsAPI + HackerNews.
    Session-cached.
    """
    inject_premium_css()
    _key = "_science_feed"
    if _key not in st.session_state:
        feed = []
        try:
            from free_apis import get_spaceflight_news, get_hackernews_top
            sf = get_spaceflight_news(limit=limit)
            hn = get_hackernews_top(limit=limit, story_type="best")
            for a in sf:
                feed.append({"title": a.get("title",""), "url": a.get("url","#"), "src": "SpaceFlight", "color": "#00aaff"})
            for a in hn:
                feed.append({"title": a.get("title",""), "url": a.get("url","#"), "src": "HackerNews", "color": "#ff6600"})
        except Exception:
            pass
        st.session_state[_key] = feed

    feed = st.session_state.get(_key, [])
    if not feed:
        return

    items_html = ""
    for item in feed[:limit * 2]:
        col   = item.get("color", "#00ffb4")
        title = item.get("title", "")[:70] + ("…" if len(item.get("title","")) > 70 else "")
        src   = item.get("src", "")
        url   = item.get("url", "#")
        items_html += f"""
<div class="eh-pulse-card" style="border-left-color:{col};">
  <div class="eh-pulse-title">
    <a href="{url}" target="_blank" style="color:rgba(255,255,255,0.88);text-decoration:none;">{title}</a>
  </div>
  <div class="eh-pulse-meta"><span style="color:{col}">● {src}</span></div>
</div>"""

    st.markdown(f"""
<div class="eh-card" style="margin-bottom:16px;">
  <div class="eh-section-header">
    <div class="eh-section-icon">📰</div>
    <div>
      <div class="eh-section-title">Science & Tech Feed</div>
      <div class="eh-section-sub">SPACEFLIGHT NEWS · HACKERNEWS · LIVE</div>
    </div>
  </div>
  {items_html}
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STUDY BREAK WIDGET — Advice + Activity + Affirmation
# ══════════════════════════════════════════════════════════════════════════════

def render_study_break_widget() -> None:
    """
    A friendly study-break card with a random activity suggestion,
    motivational affirmation, and life advice — all from free APIs.
    Refreshes on button click.
    """
    inject_premium_css()

    if "break_data" not in st.session_state:
        st.session_state.break_data = {}

    if st.button("🎲 Get Study Break Idea", key="break_btn", use_container_width=True):
        st.session_state.break_data = {}

    if not st.session_state.break_data:
        d: dict = {}
        try:
            from free_apis import get_activity, get_affirmation, get_advice
            act  = get_activity(activity_type="relaxation")
            aff  = get_affirmation()
            adv  = get_advice()
            if act:  d["activity"]    = act
            if aff:  d["affirmation"] = aff
            if adv:  d["advice"]      = adv
        except Exception:
            d["advice"] = "Take a 5-minute walk, drink some water, and breathe deeply."
        st.session_state.break_data = d

    d = st.session_state.break_data
    activity_html = ""
    if d.get("activity"):
        a = d["activity"]
        activity_html = f"""
<div style="padding:14px 16px;border-radius:12px;background:rgba(0,255,180,0.04);border:1px solid rgba(0,255,180,0.1);margin-bottom:10px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:2px;color:rgba(0,255,180,0.5);margin-bottom:6px;">💡 SUGGESTED ACTIVITY</div>
  <div style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:600;color:#fff;">{a.get('activity','')}</div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(255,255,255,0.3);margin-top:4px;">{a.get('type','').upper()} · {a.get('participants',1)} person(s)</div>
</div>"""

    aff_html = ""
    if d.get("affirmation"):
        aff_html = f"""
<div style="padding:14px 16px;border-radius:12px;background:rgba(180,77,255,0.04);border:1px solid rgba(180,77,255,0.1);margin-bottom:10px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:2px;color:rgba(180,77,255,0.5);margin-bottom:6px;">✨ AFFIRMATION</div>
  <div style="font-family:'Inter',sans-serif;font-size:13px;font-style:italic;color:rgba(255,255,255,0.8);">"{d['affirmation']}"</div>
</div>"""

    adv_html = ""
    if d.get("advice"):
        adv_html = f"""
<div style="padding:14px 16px;border-radius:12px;background:rgba(255,170,0,0.04);border:1px solid rgba(255,170,0,0.1);">
  <div style="font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:2px;color:rgba(255,170,0,0.5);margin-bottom:6px;">🔮 LIFE ADVICE</div>
  <div style="font-family:'Inter',sans-serif;font-size:13px;color:rgba(255,255,255,0.75);">{d['advice']}</div>
</div>"""

    st.markdown(f"""
<div class="eh-card" style="margin-bottom:16px;">
  <div class="eh-section-header">
    <div class="eh-section-icon">☕</div>
    <div>
      <div class="eh-section-title">Study Break</div>
      <div class="eh-section-sub">REST WELL · COME BACK STRONGER</div>
    </div>
  </div>
  {activity_html}{aff_html}{adv_html}
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# API EXPLORER PANEL — Interactive API Tester
# ══════════════════════════════════════════════════════════════════════════════

def render_api_explorer_panel() -> None:
    """
    A live interactive panel letting the user pick any integrated free API
    and instantly preview results — useful for the Settings or a new sidebar tab.
    """
    inject_premium_css()

    API_ACTIONS = {
        "📚 Search arXiv papers": ("arXiv", "search_arxiv", str),
        "📖 Search Google Books":  ("Google Books", "search_google_books", str),
        "🧬 Look up species (GBIF)": ("GBIF", "search_species", str),
        "💊 PubChem compound":     ("PubChem", "get_compound", str),
        "🏥 Search PubMed":        ("PubMed", "search_pubmed", str),
        "🚀 SpaceX latest launch": ("SpaceX", "get_latest_spacex_launch", None),
        "🪙 Crypto price (BTC)":   ("CoinGecko", "get_crypto_price", "bitcoin"),
        "🌍 USGS Earthquakes":     ("USGS", "get_earthquakes", None),
        "📰 SpaceFlight News":     ("SpaceFlight", "get_spaceflight_news", None),
        "🍳 Random Meal Recipe":   ("MealDB", "get_random_meal", None),
        "🎭 Meme Templates":       ("Imgflip", "get_meme_templates", None),
        "🌿 Random Advice":        ("AdviceSlip", "get_advice", None),
        "🔭 NASA APOD":            ("NASA", "get_nasa_apod", None),
    }

    st.markdown("""
<div class="eh-section-header" style="margin-bottom:20px;">
  <div class="eh-section-icon">⚡</div>
  <div>
    <div class="eh-section-title">Live API Explorer</div>
    <div class="eh-section-sub">72 FREE APIS · ZERO AUTH · INSTANT RESULTS</div>
  </div>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        choice = st.selectbox("Choose API", list(API_ACTIONS.keys()), key="api_exp_choice")
    with col2:
        label, fn_name, default_arg = API_ACTIONS[choice]
        if default_arg is type(""):
            query = st.text_input("Query / ID", value="machine learning", key="api_exp_query")
        elif isinstance(default_arg, str):
            query = default_arg
        else:
            query = None

    if st.button(f"🚀 Fetch from {label}", key="api_exp_btn", use_container_width=True):
        with st.spinner(f"Calling {label} API…"):
            try:
                import free_apis as fa
                fn = getattr(fa, fn_name)
                if query and default_arg is type(""):
                    result = fn(query)
                elif isinstance(default_arg, str) and default_arg:
                    result = fn(default_arg)
                else:
                    result = fn()
                if result:
                    st.success(f"✅ {label} returned {len(result) if isinstance(result, (list, dict)) else 1} result(s)")
                    st.json(result if isinstance(result, (dict, list)) else {"result": str(result)})
                else:
                    st.warning("No results returned — try a different query or check your connection.")
            except Exception as e:
                st.error(f"API call failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE: render all sidebar widgets in one call
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar_live_panel() -> None:
    """
    Drop-in sidebar enhancement — call from inside `with st.sidebar:` block.
    Renders compact crypto ticker, world times, and break widget.
    """
    inject_premium_css()
    st.markdown("---")
    st.markdown("""
<div style="font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:2px;color:rgba(255,255,255,0.2);text-align:center;margin-bottom:10px;">
  LIVE DATA · FREE APIS
</div>""", unsafe_allow_html=True)
    render_crypto_ticker(compact=True)
    st.markdown("<div style='margin:8px 0;'></div>", unsafe_allow_html=True)
    render_topic_spotlight()
