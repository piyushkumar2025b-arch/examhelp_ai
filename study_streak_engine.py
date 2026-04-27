"""
study_streak_engine.py — ExamHelp AI Gamification & Study Streak System v2.0
Daily streak tracking, XP system, achievement badges, multi-level heatmap, weekly stats.
"""
import streamlit as st
import datetime
import json
import os


# ─── Achievement Definitions ─────────────────────────────────────────────────
ACHIEVEMENTS = [
    {"id": "first_chat",     "emoji": "💬", "name": "First Contact",       "desc": "Send your first message",                  "xp": 10},
    {"id": "streak_3",       "emoji": "🔥", "name": "On Fire",              "desc": "Study 3 days in a row",                    "xp": 30},
    {"id": "streak_7",       "emoji": "🌟", "name": "Weekly Warrior",       "desc": "Study 7 days in a row",                    "xp": 100},
    {"id": "streak_30",      "emoji": "👑", "name": "Monthly Master",       "desc": "Study 30 days in a row",                   "xp": 500},
    {"id": "pdf_upload",     "emoji": "📄", "name": "Document Scholar",     "desc": "Upload your first PDF",                    "xp": 20},
    {"id": "flashcards_10",  "emoji": "🃏", "name": "Card Collector",       "desc": "Generate 10+ flashcards",                  "xp": 25},
    {"id": "quiz_perfect",   "emoji": "🏆", "name": "Perfect Score",        "desc": "Get 100% on a quiz",                       "xp": 50},
    {"id": "pomo_5",         "emoji": "🍅", "name": "Tomato Master",        "desc": "Complete 5 Pomodoro sessions",              "xp": 40},
    {"id": "pomo_25",        "emoji": "⌛", "name": "Deep Worker",          "desc": "Complete 25 Pomodoro sessions",             "xp": 150},
    {"id": "notes_gen",      "emoji": "📝", "name": "Note Taker",           "desc": "Generate your first smart notes",           "xp": 15},
    {"id": "multi_tool",     "emoji": "🔧", "name": "Swiss Army Brain",     "desc": "Use 5 different tools in one session",      "xp": 35},
    {"id": "chat_50",        "emoji": "🧠", "name": "Deep Thinker",         "desc": "Send 50 messages in total",                 "xp": 60},
    {"id": "research_pro",   "emoji": "🔬", "name": "Research Expert",      "desc": "Use Research Pro tool",                    "xp": 20},
    {"id": "midnight_oil",   "emoji": "🌙", "name": "Night Owl",            "desc": "Study after midnight",                     "xp": 25},
    {"id": "early_bird",     "emoji": "🐦", "name": "Early Bird",           "desc": "Study before 7 AM",                        "xp": 25},
    {"id": "level_5",        "emoji": "⭐", "name": "Rising Star",          "desc": "Reach Level 5",                            "xp": 0},
    {"id": "level_10",       "emoji": "💎", "name": "Diamond Scholar",      "desc": "Reach Level 10",                           "xp": 0},
    {"id": "level_25",       "emoji": "🚀", "name": "Apex Intellect",       "desc": "Reach Level 25",                           "xp": 0},
]

ACHIEVEMENT_MAP = {a["id"]: a for a in ACHIEVEMENTS}

# XP required per level (cumulative)
def _xp_for_level(level: int) -> int:
    return int(100 * (level ** 1.5))

def _level_from_xp(xp: int) -> int:
    lv = 1
    while _xp_for_level(lv + 1) <= xp:
        lv += 1
    return lv

def _xp_progress(xp: int):
    lv = _level_from_xp(xp)
    xp_this = xp - _xp_for_level(lv)
    xp_next = _xp_for_level(lv + 1) - _xp_for_level(lv)
    return lv, xp_this, xp_next


STREAK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

/* ── STREAK HERO ── */
.streak-hero {
  position: relative;
  background: linear-gradient(135deg,
    rgba(15,23,42,0.95) 0%,
    rgba(30,15,60,0.9) 50%,
    rgba(15,23,42,0.95) 100%);
  border: 1px solid rgba(249,115,22,0.25);
  border-radius: 24px;
  padding: 36px 32px;
  backdrop-filter: blur(24px);
  box-shadow: 0 0 80px rgba(249,115,22,0.07), 0 40px 80px rgba(0,0,0,0.45);
  margin-bottom: 20px;
  overflow: hidden;
}
.streak-hero::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 50% 60% at 50% 0%, rgba(249,115,22,0.06) 0%, transparent 70%);
  pointer-events: none;
}
.streak-hero::after {
  content: '';
  position: absolute;
  top: -1px; left: 12%; right: 12%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(249,115,22,0.55), rgba(251,146,60,0.55), transparent);
}
.streak-hero-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.streak-hero-left { flex: 1; text-align: center; }
.streak-flame {
  font-size: 64px;
  line-height: 1;
  margin-bottom: 6px;
  animation: flameFlicker 1.8s ease-in-out infinite;
  display: block;
}
@keyframes flameFlicker {
  0%,100%{transform:scale(1) rotate(-2deg);}
  50%{transform:scale(1.08) rotate(2deg);}
}
.streak-number {
  font-family: 'Orbitron', monospace;
  font-size: clamp(48px,8vw,80px);
  font-weight: 900;
  background: linear-gradient(135deg, #fb923c 0%, #f97316 40%, #ef4444 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 30px rgba(249,115,22,0.4));
  line-height: 1;
  margin-bottom: 4px;
}
.streak-label {
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  letter-spacing: 5px;
  color: rgba(255,255,255,0.35);
  text-transform: uppercase;
  margin-bottom: 20px;
}

/* ── DAILY STATUS ── */
.streak-today-badge {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.25);
  border-radius: 100px; padding: 6px 18px; margin-bottom: 16px;
  font-family: 'Space Mono', monospace; font-size: 10px; letter-spacing: 2px;
  color: #34d399; animation: todayPulse 3s ease-in-out infinite;
}
@keyframes todayPulse { 0%,100%{box-shadow:0 0 0 rgba(16,185,129,0);} 50%{box-shadow:0 0 16px rgba(16,185,129,0.2);} }
.today-dot { width: 6px; height: 6px; background: #34d399; border-radius: 50%; animation: insBlink 1.5s ease-in-out infinite; }
@keyframes insBlink { 0%,100%{opacity:1;} 50%{opacity:0.2;} }

/* ── XP BAR ── */
.xp-section { margin-top: 20px; }
.xp-level-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.xp-level-badge {
  font-family: 'Orbitron', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #a78bfa;
  background: rgba(167,139,250,0.1);
  border: 1px solid rgba(167,139,250,0.25);
  border-radius: 100px;
  padding: 4px 16px;
  letter-spacing: 1px;
}
.xp-count {
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  color: rgba(255,255,255,0.35);
  letter-spacing: 1px;
}
.xp-bar-track {
  height: 8px;
  background: rgba(255,255,255,0.05);
  border-radius: 100px;
  overflow: hidden;
  position: relative;
}
.xp-bar-fill {
  height: 100%;
  border-radius: 100px;
  background: linear-gradient(90deg, #7c3aed, #a78bfa, #c084fc);
  background-size: 200%;
  animation: xpShift 3s ease infinite;
  transition: width 0.8s cubic-bezier(0.16,1,0.3,1);
  position: relative;
}
@keyframes xpShift {
  0%,100%{background-position:0%} 50%{background-position:100%}
}
.xp-bar-glow {
  position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, rgba(167,139,250,0.3), transparent);
  animation: xpScan 2s ease-in-out infinite;
}
@keyframes xpScan {
  0%{transform:translateX(-100%)} 100%{transform:translateX(200%)}
}

/* ── WEEKLY STATS ── */
.weekly-bar-wrap {
  display: flex; align-items: flex-end; gap: 6px;
  height: 70px; padding: 0 4px;
}
.week-bar-col { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.week-bar {
  width: 100%; border-radius: 4px 4px 0 0;
  background: linear-gradient(180deg, rgba(249,115,22,0.7), rgba(249,115,22,0.3));
  transition: height 0.6s cubic-bezier(0.16,1,0.3,1);
  min-height: 4px;
}
.week-bar.today { background: linear-gradient(180deg, #f97316, #fb923c); box-shadow: 0 0 8px rgba(249,115,22,0.4); }
.week-bar.empty { background: rgba(255,255,255,0.05); }
.week-day-lbl { font-family: 'Space Mono', monospace; font-size: 8px; color: rgba(255,255,255,0.25); letter-spacing: 1px; }
.week-day-lbl.today { color: #f97316; }

/* ── CALENDAR HEATMAP ── */
.heatmap-wrap {
  background: rgba(15,23,42,0.6);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 18px;
  padding: 20px 18px;
  margin-bottom: 18px;
}
.heatmap-title {
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  letter-spacing: 4px;
  color: rgba(255,255,255,0.25);
  text-transform: uppercase;
  margin-bottom: 6px;
  display: flex; align-items: center; justify-content: space-between;
}
.heatmap-legend {
  display: flex; align-items: center; gap: 4px;
  font-size: 8px; color: rgba(255,255,255,0.2);
}
.hm-legend-box { width: 10px; height: 10px; border-radius: 2px; }
.heatmap-grid {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.heatmap-day {
  width: 13px;
  height: 13px;
  border-radius: 3px;
  position: relative;
  transition: transform 0.2s ease;
  cursor: default;
}
.heatmap-day:hover { transform: scale(1.4); z-index: 10; }
.hm-0 { background: rgba(255,255,255,0.04); }
.hm-1 { background: rgba(249,115,22,0.2); }
.hm-2 { background: rgba(249,115,22,0.45); }
.hm-3 { background: rgba(249,115,22,0.68); }
.hm-4 { background: rgb(249,115,22); box-shadow: 0 0 4px rgba(249,115,22,0.4); }
.hm-today { outline: 2px solid rgba(255,255,255,0.4); outline-offset: 1px; }

/* ── ACHIEVEMENT CARDS ── */
.ach-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}
.ach-card {
  background: rgba(15,23,42,0.7);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  padding: 16px 14px;
  text-align: center;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.ach-card.unlocked {
  border-color: rgba(167,139,250,0.3);
  background: rgba(99,102,241,0.07);
}
.ach-card.unlocked::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at top, rgba(99,102,241,0.06), transparent 70%);
}
.ach-card.unlocked::after {
  content: '';
  position: absolute; top: -1px; left: 20%; right: 20%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(167,139,250,0.5), transparent);
}
.ach-card.locked { opacity: 0.4; filter: grayscale(0.6); }
.ach-card:hover { transform: translateY(-5px); }
.ach-card.unlocked:hover { box-shadow: 0 10px 30px rgba(99,102,241,0.25); border-color: rgba(167,139,250,0.5); }
.ach-emoji { font-size: 30px; margin-bottom: 10px; display: block; transition: transform 0.3s ease; }
.ach-card:hover .ach-emoji { transform: scale(1.15) rotate(-5deg); }
.ach-name {
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}
.ach-desc {
  font-family: 'Rajdhani', sans-serif;
  font-size: 11px;
  color: rgba(255,255,255,0.35);
  line-height: 1.4;
}
.ach-xp {
  display: inline-block;
  margin-top: 8px;
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  color: #a78bfa;
  letter-spacing: 1px;
  background: rgba(167,139,250,0.1);
  border: 1px solid rgba(167,139,250,0.15);
  border-radius: 100px;
  padding: 3px 10px;
}
.ach-unlock-badge {
  position: absolute;
  top: 8px; right: 10px;
  font-size: 13px;
}

/* ── STATS MINI CARD ── */
.streak-stat-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.streak-stat-card {
  flex: 1; min-width: 90px;
  background: rgba(15,23,42,0.7); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 14px 12px; text-align: center;
  transition: all 0.25s ease;
}
.streak-stat-card:hover { border-color: rgba(249,115,22,0.3); transform: translateY(-2px); }
.streak-stat-val {
  font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 900;
  background: linear-gradient(135deg, #fb923c, #f97316);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  line-height: 1; margin-bottom: 5px;
}
.streak-stat-lbl {
  font-family: 'Space Mono', monospace; font-size: 8px;
  letter-spacing: 2px; color: rgba(255,255,255,0.2); text-transform: uppercase;
}

/* ── SECTION LABEL ── */
.streak-section-label {
  font-family: 'Space Mono', monospace; font-size: 9px; letter-spacing: 4px;
  color: rgba(255,255,255,0.2); text-transform: uppercase;
  margin: 20px 0 12px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex; align-items: center; justify-content: space-between;
}
.streak-count-badge {
  background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.2);
  border-radius: 100px; padding: 2px 10px;
  font-size: 9px; color: #fb923c;
}
</style>
"""

STREAK_FILE = "streak_data.json"


def _load_streak_data() -> dict:
    if "streak_data" not in st.session_state:
        data = {
            "streak": 0,
            "max_streak": 0,
            "total_xp": 0,
            "last_study_date": None,
            "study_days": [],
            "achievements": [],
            "tools_used_today": [],
        }
        if os.path.exists(STREAK_FILE):
            try:
                with open(STREAK_FILE, "r") as f:
                    data.update(json.load(f))
            except Exception:
                pass
        st.session_state.streak_data = data
    return st.session_state.streak_data


def _save_streak_data():
    try:
        with open(STREAK_FILE, "w") as f:
            json.dump(st.session_state.streak_data, f, default=str)
    except Exception:
        pass


def award_xp(amount: int, reason: str = ""):
    """Award XP and check for level-up achievements."""
    data = _load_streak_data()
    old_level = _level_from_xp(data["total_xp"])
    data["total_xp"] += amount
    new_level = _level_from_xp(data["total_xp"])
    if new_level > old_level:
        for lid in [f"level_{n}" for n in [5, 10, 25]]:
            lv = int(lid.split("_")[1])
            if new_level >= lv:
                unlock_achievement(lid)
    _save_streak_data()


def unlock_achievement(ach_id: str):
    """Unlock an achievement if not already unlocked."""
    data = _load_streak_data()
    if ach_id not in data["achievements"] and ach_id in ACHIEVEMENT_MAP:
        data["achievements"].append(ach_id)
        xp = ACHIEVEMENT_MAP[ach_id]["xp"]
        if xp > 0:
            data["total_xp"] += xp
        _save_streak_data()
        st.toast(f"🏆 Achievement unlocked: **{ACHIEVEMENT_MAP[ach_id]['name']}** +{xp} XP")


def record_study_day():
    """Call once per session start to update streak."""
    data = _load_streak_data()
    today = datetime.date.today().isoformat()
    if today in data["study_days"]:
        return
    data["study_days"].append(today)
    last = data.get("last_study_date")
    if last:
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        if last == yesterday:
            data["streak"] += 1
        else:
            data["streak"] = 1
    else:
        data["streak"] = 1
    data["max_streak"] = max(data["streak"], data["max_streak"])
    data["last_study_date"] = today
    _save_streak_data()
    award_xp(10, "Daily study session")
    if data["streak"] >= 3:  unlock_achievement("streak_3")
    if data["streak"] >= 7:  unlock_achievement("streak_7")
    if data["streak"] >= 30: unlock_achievement("streak_30")

    # Time-of-day achievements
    now_hour = datetime.datetime.now().hour
    if now_hour >= 0 and now_hour < 3:
        unlock_achievement("midnight_oil")
    if now_hour < 7:
        unlock_achievement("early_bird")


def render_streak_page():
    """Render the full Study Streak & Gamification page."""
    _load_streak_data()
    record_study_day()
    data = st.session_state.streak_data
    st.markdown(STREAK_CSS, unsafe_allow_html=True)

    streak   = data["streak"]
    max_str  = data["max_streak"]
    total_xp = data["total_xp"]
    level, xp_in, xp_need = _xp_progress(total_xp)
    xp_pct = min(100, int((xp_in / max(1, xp_need)) * 100))
    today_str = datetime.date.today().isoformat()
    studied_today = today_str in set(data["study_days"])

    # ── Hero Card ───────────────────────────────────────────────────────────
    today_badge = ""
    if studied_today:
        today_badge = '<div class="streak-today-badge"><span class="today-dot"></span>STUDIED TODAY · STREAK ACTIVE</div>'

    st.markdown(f"""
    <div class="streak-hero">
      <div class="streak-hero-row">
        <div class="streak-hero-left">
          <span class="streak-flame">{'🔥' if streak > 0 else '💤'}</span>
          <div class="streak-number">{streak}</div>
          <div class="streak-label">Day Study Streak</div>
          {today_badge}
          <div class="xp-section">
            <div class="xp-level-row">
              <div class="xp-level-badge">LVL {level}</div>
              <div class="xp-count">{xp_in} / {xp_need} XP</div>
            </div>
            <div class="xp-bar-track">
              <div class="xp-bar-fill" style="width:{xp_pct}%"></div>
              <div class="xp-bar-glow"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Stats Row ─────────────────────────────────────────────────────
    total_days = len(set(data["study_days"]))
    ach_count  = len(data["achievements"])
    st.markdown(f"""
    <div class="streak-stat-row">
      <div class="streak-stat-card">
        <div class="streak-stat-val">{streak}</div>
        <div class="streak-stat-lbl">Current Streak</div>
      </div>
      <div class="streak-stat-card">
        <div class="streak-stat-val">{max_str}</div>
        <div class="streak-stat-lbl">Best Streak</div>
      </div>
      <div class="streak-stat-card">
        <div class="streak-stat-val">{total_days}</div>
        <div class="streak-stat-lbl">Study Days</div>
      </div>
      <div class="streak-stat-card">
        <div class="streak-stat-val">{total_xp:,}</div>
        <div class="streak-stat-lbl">Total XP</div>
      </div>
      <div class="streak-stat-card">
        <div class="streak-stat-val">{ach_count}</div>
        <div class="streak-stat-lbl">Achievements</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Weekly Activity Bars ────────────────────────────────────────────────
    st.markdown('<div class="streak-section-label">📆 WEEKLY ACTIVITY</div>', unsafe_allow_html=True)
    today       = datetime.date.today()
    study_set   = set(data["study_days"])
    day_names   = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    bars_html = '<div class="weekly-bar-wrap">'
    for i in range(6, -1, -1):
        d       = today - datetime.timedelta(days=i)
        d_str   = d.isoformat()
        studied = d_str in study_set
        is_today = d == today
        day_lbl = day_names[d.weekday()]
        h_pct   = 60 if studied else 4
        bar_cls = "today" if is_today and studied else ("empty" if not studied else "")
        lbl_cls = "today" if is_today else ""
        bars_html += f"""
          <div class="week-bar-col">
            <div class="week-bar {bar_cls}" style="height:{h_pct}px"></div>
            <div class="week-day-lbl {lbl_cls}">{day_lbl}</div>
          </div>"""
    bars_html += '</div>'
    st.markdown(bars_html, unsafe_allow_html=True)

    # ── Heatmap (Last 70 days) ──────────────────────────────────────────────
    st.markdown("""
    <div class="heatmap-wrap">
      <div class="heatmap-title">
        <span>📅 STUDY ACTIVITY — LAST 70 DAYS</span>
        <div class="heatmap-legend">
          <span>Less</span>
          <div class="hm-legend-box hm-0"></div>
          <div class="hm-legend-box hm-2"></div>
          <div class="hm-legend-box hm-4"></div>
          <span>More</span>
        </div>
      </div>
      <div class="heatmap-grid">""", unsafe_allow_html=True)

    cells_html = ""
    for i in range(69, -1, -1):
        d         = (today - datetime.timedelta(days=i)).isoformat()
        is_today_cell = (i == 0)
        today_cls = " hm-today" if is_today_cell else ""
        # Multi-level: could track session count per day in future, for now binary
        intensity = "hm-4" if d in study_set else "hm-0"
        cells_html += f'<div class="heatmap-day {intensity}{today_cls}" title="{d}"></div>'
    st.markdown(cells_html + "</div></div>", unsafe_allow_html=True)

    # ── Achievements ─────────────────────────────────────────────────────────
    unlocked_count = len(data["achievements"])
    st.markdown(f"""
    <div class="streak-section-label">
      🏆 ACHIEVEMENTS
      <span class="streak-count-badge">{unlocked_count}/{len(ACHIEVEMENTS)}</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="ach-grid">', unsafe_allow_html=True)
    ach_html = ""
    for ach in ACHIEVEMENTS:
        unlocked   = ach["id"] in data["achievements"]
        card_cls   = "unlocked" if unlocked else "locked"
        lock_badge = "✅" if unlocked else "🔒"
        ach_html += f"""
        <div class="ach-card {card_cls}">
          <div class="ach-unlock-badge">{lock_badge}</div>
          <span class="ach-emoji">{ach['emoji']}</span>
          <div class="ach-name">{ach['name']}</div>
          <div class="ach-desc">{ach['desc']}</div>
          {f'<div class="ach-xp">+{ach["xp"]} XP</div>' if ach['xp'] > 0 else ''}
        </div>"""
    st.markdown(ach_html + "</div>", unsafe_allow_html=True)

    # ── Actions ─────────────────────────────────────────────────────────────
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🍅 Go to Pomodoro Timer", use_container_width=True, key="streak_pomo"):
            st.session_state.app_mode = "pomodoro"; st.rerun()
    with c2:
        if st.button("🧠 Session Insights", use_container_width=True, key="streak_insights"):
            st.session_state.app_mode = "insights"; st.rerun()
    with c3:
        if st.button("💬 Back to Chat", use_container_width=True, key="streak_back"):
            st.session_state.app_mode = "chat"; st.rerun()


# ── FREE API ADDITIONS ───────────────────────────────────────────────────────

def get_streak_motivation_quote() -> dict:
    """Fetch a motivational quote from ZenQuotes API (free, no key)."""
    import urllib.request, json
    try:
        req = urllib.request.Request("https://zenquotes.io/api/random", headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        if isinstance(data, list) and data:
            return {"q": data[0].get("q", ""), "a": data[0].get("a", "")}
    except Exception:
        pass
    return {"q": "Push yourself because no one else is going to do it for you.", "a": "Unknown"}


def get_daily_trivia_challenge(category: str = "Science: Computers") -> dict:
    """Fetch a trivia question from Open Trivia DB (free, no key)."""
    import urllib.request, urllib.parse, json, html
    category_map = {
        "Science": "17", "Math": "19", "Computers": "18",
        "History": "23", "Geography": "22", "General": "9"
    }
    cat_id = category_map.get(category, "18")
    try:
        url = f"https://opentdb.com/api.php?amount=1&category={cat_id}&difficulty=medium&type=multiple"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        results = data.get("results", [])
        if results:
            q = results[0]
            return {
                "question": html.unescape(q.get("question", "")),
                "correct": html.unescape(q.get("correct_answer", "")),
                "incorrect": [html.unescape(a) for a in q.get("incorrect_answers", [])],
                "difficulty": q.get("difficulty", ""),
                "category": q.get("category", ""),
            }
    except Exception:
        pass
    return {}


def get_xp_number_fact(xp: int) -> str:
    """Get a fun math fact about the XP number (NumbersAPI, free)."""
    import urllib.request
    try:
        req = urllib.request.Request(f"http://numbersapi.com/{xp}/math", headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            return r.read().decode()
    except Exception:
        return f"You have earned {xp:,} XP — keep going!"
