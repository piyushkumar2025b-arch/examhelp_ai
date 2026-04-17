"""
daily_briefing_engine.py — ExamHelp AI Personalized Daily Briefing v2.0
Personalized morning / evening briefing with:
- Time-of-day themed hero (morning/afternoon/evening/night)
- Per-session study data pulled from streak engine
- Exam countdown with progress ring
- AI-generated motivation, topic of day, study technique
- Quick-fire morning challenge with reveal
- Productivity checklist
"""
import streamlit as st
import datetime
import json
import re
from utils.ai_engine import generate
from free_apis import (
    get_today_quote, get_trivia, get_public_holidays,
    get_number_fact, get_iss_location,
    get_nasa_apod, get_today_in_history,
    get_crypto_price, get_air_quality_by_city,
    get_world_time, get_earthquakes,
)



BRIEFING_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

/* ── HERO ── */
.briefing-hero {
  position: relative;
  border-radius: 28px;
  padding: 44px 36px 36px;
  backdrop-filter: blur(24px);
  box-shadow: 0 0 100px rgba(99,102,241,0.07), 0 40px 80px rgba(0,0,0,0.45);
  margin-bottom: 22px;
  overflow: hidden;
  transition: background 0.5s ease;
}
.briefing-hero.time-morning {
  background: linear-gradient(135deg, rgba(15,23,42,0.94) 0%, rgba(30,20,50,0.9) 100%);
  border: 1px solid rgba(251,191,36,0.2);
}
.briefing-hero.time-afternoon {
  background: linear-gradient(135deg, rgba(15,23,42,0.94) 0%, rgba(10,30,50,0.9) 100%);
  border: 1px solid rgba(96,165,250,0.2);
}
.briefing-hero.time-evening {
  background: linear-gradient(135deg, rgba(15,23,42,0.94) 0%, rgba(30,10,40,0.9) 100%);
  border: 1px solid rgba(167,139,250,0.2);
}
.briefing-hero.time-night {
  background: linear-gradient(135deg, rgba(8,10,25,0.97) 0%, rgba(15,5,30,0.94) 100%);
  border: 1px solid rgba(99,102,241,0.15);
}
.briefing-hero::after {
  content: '';
  position: absolute;
  top: -1px; left: 8%; right: 8%; height: 1px;
  background: var(--hero-line, linear-gradient(90deg, transparent, rgba(99,102,241,0.55), transparent));
}
.briefing-hero::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 60% 70% at 0% 0%, var(--hero-glow, rgba(99,102,241,0.06)), transparent 70%);
  pointer-events: none;
}

.briefing-time-icon { font-size: 52px; display: block; margin-bottom: 14px; animation: briefIconFloat 4s ease-in-out infinite; }
@keyframes briefIconFloat { 0%,100%{transform:translateY(0) rotate(0deg);} 50%{transform:translateY(-6px) rotate(5deg);} }
.briefing-date {
  font-family: 'Space Mono', monospace;
  font-size: 10px; letter-spacing: 5px;
  color: rgba(255,255,255,0.25); text-transform: uppercase; margin-bottom: 14px;
}
.briefing-greeting {
  font-family: 'Orbitron', monospace;
  font-size: clamp(20px,3.5vw,32px);
  font-weight: 900; letter-spacing: 1px; margin-bottom: 8px;
  background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 40%, #818cf8 70%, #c084fc 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  filter: drop-shadow(0 0 24px rgba(99,102,241,0.35));
}
.briefing-sub {
  font-family: 'Rajdhani', sans-serif; font-size: 15px;
  color: rgba(255,255,255,0.4); letter-spacing: 0.5px;
}

/* ── STREAK HERO BADGE ── */
.streak-badge-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }
.streak-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.25);
  border-radius: 100px; padding: 6px 16px;
  font-family: 'Space Mono', monospace; font-size: 10px;
  color: #fb923c; letter-spacing: 2px;
  animation: stkPulse 3s ease-in-out infinite;
}
@keyframes stkPulse { 0%,100%{box-shadow:0 0 0 rgba(249,115,22,0);} 50%{box-shadow:0 0 16px rgba(249,115,22,0.2);} }
.xp-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.25);
  border-radius: 100px; padding: 6px 16px;
  font-family: 'Space Mono', monospace; font-size: 10px;
  color: #a78bfa; letter-spacing: 2px;
}

/* ── EXAM COUNTDOWN RING ── */
.exam-ring-card {
  background: rgba(15,23,42,0.7);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 22px; padding: 22px 26px;
  margin-bottom: 16px; display: flex; align-items: center; gap: 24px;
  flex-wrap: wrap; transition: all 0.25s ease;
}
.exam-ring-card:hover { border-color: rgba(239,68,68,0.4); transform: translateY(-2px); }
.exam-ring-svg { width: 80px; height: 80px; transform: rotate(-90deg); flex-shrink: 0; }
.exam-ring-track { fill: none; stroke: rgba(255,255,255,0.06); stroke-width: 8; }
.exam-ring-fill { fill: none; stroke-width: 8; stroke-linecap: round; transition: stroke-dashoffset 1s cubic-bezier(0.16,1,0.3,1); }
.ring-danger { stroke: url(#ringDanger); }
.ring-warn   { stroke: url(#ringWarn); }
.ring-good   { stroke: url(#ringGood); }
.exam-ring-info { flex: 1; min-width: 140px; }
.exam-name-lbl {
  font-family: 'Rajdhani', sans-serif; font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 4px;
}
.exam-date-lbl {
  font-family: 'Space Mono', monospace; font-size: 9px;
  color: rgba(255,255,255,0.3); letter-spacing: 1px; margin-bottom: 10px;
}
.exam-days-big {
  font-family: 'Orbitron', monospace; font-size: 36px; font-weight: 900; line-height: 1;
}
.days-danger { color: #ef4444; filter: drop-shadow(0 0 12px rgba(239,68,68,0.5)); }
.days-warn   { color: #f97316; filter: drop-shadow(0 0 12px rgba(249,115,22,0.5)); }
.days-good   { color: #10b981; filter: drop-shadow(0 0 12px rgba(16,185,129,0.5)); }
.exam-days-lbl {
  font-family: 'Space Mono', monospace; font-size: 8px;
  color: rgba(255,255,255,0.25); letter-spacing: 2px;
}

/* ── BRIEFING CARDS ── */
.briefing-card {
  background: rgba(15,23,42,0.65);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 20px; padding: 22px 26px; margin-bottom: 14px;
  position: relative; overflow: hidden;
  animation: briefIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
  transition: all 0.25s ease;
}
.briefing-card:hover { border-color: rgba(255,255,255,0.12); transform: translateY(-2px); }
@keyframes briefIn { from{opacity:0;transform:translateY(10px);} to{opacity:1;transform:none;} }
.briefing-card:nth-child(1){animation-delay:.0s;}
.briefing-card:nth-child(2){animation-delay:.07s;}
.briefing-card:nth-child(3){animation-delay:.14s;}
.briefing-card:nth-child(4){animation-delay:.21s;}
.briefing-card::before {
  content: ''; position: absolute;
  left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--bc-accent, linear-gradient(180deg,#6366f1,#a78bfa));
  border-radius: 3px 0 0 3px;
}
.briefing-card::after {
  content: ''; position: absolute;
  top: -1px; left: 10%; right: 10%; height: 1px;
  background: linear-gradient(90deg, transparent, var(--bc-top, rgba(99,102,241,0.25)), transparent);
}
.bc-purple { --bc-accent:linear-gradient(180deg,#6366f1,#a78bfa); --bc-top:rgba(99,102,241,0.25); }
.bc-green  { --bc-accent:linear-gradient(180deg,#10b981,#34d399); --bc-top:rgba(16,185,129,0.2); }
.bc-blue   { --bc-accent:linear-gradient(180deg,#3b82f6,#60a5fa); --bc-top:rgba(59,130,246,0.2); }
.bc-orange { --bc-accent:linear-gradient(180deg,#f97316,#fb923c); --bc-top:rgba(249,115,22,0.2); }
.bc-pink   { --bc-accent:linear-gradient(180deg,#ec4899,#f472b6); --bc-top:rgba(236,72,153,0.2); }

.briefing-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.briefing-card-icon { font-size: 20px; flex-shrink: 0; }
.briefing-card-title {
  font-family: 'Space Mono', monospace; font-size: 9px;
  letter-spacing: 3px; color: rgba(255,255,255,0.3); text-transform: uppercase;
}
.briefing-card-body {
  font-family: 'Rajdhani', sans-serif; font-size: 15px;
  color: rgba(255,255,255,0.78); line-height: 1.75;
}
.briefing-card-body strong { color: #a5b4fc; }

/* ── CHALLENGE CARD ── */
.challenge-card {
  background: rgba(99,102,241,0.06);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 18px; padding: 22px 24px;
  position: relative; overflow: hidden;
}
.challenge-card::after {
  content: '?';
  position: absolute; bottom: -10px; right: 10px;
  font-size: 120px; opacity: 0.03;
  font-family: 'Orbitron', monospace; font-weight: 900; pointer-events: none;
}
.challenge-q {
  font-family: 'Rajdhani', sans-serif; font-size: 17px; font-weight: 700;
  color: rgba(255,255,255,0.88); line-height: 1.6; margin-bottom: 16px;
}
.challenge-reveal {
  background: rgba(16,185,129,0.07);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 14px; padding: 16px 18px;
  font-family: 'Rajdhani', sans-serif; font-size: 14px;
  color: rgba(255,255,255,0.72); line-height: 1.65;
  animation: revealIn 0.35s cubic-bezier(0.16,1,0.3,1);
}
@keyframes revealIn { from{opacity:0;transform:translateY(6px);} to{opacity:1;transform:none;} }

/* ── CHECKLIST ── */
.check-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  margin-bottom: 8px; cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Rajdhani', sans-serif; font-size: 14px;
  color: rgba(255,255,255,0.65);
}
.check-item:hover { background: rgba(99,102,241,0.07); border-color: rgba(99,102,241,0.2); }
.check-item.done {
  background: rgba(16,185,129,0.06); border-color: rgba(16,185,129,0.2);
  color: rgba(255,255,255,0.4); text-decoration: line-through;
}
.check-bullet { font-size: 16px; flex-shrink: 0; }

/* ── SECTION LABEL ── */
.brief-section { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:4px;
  color:rgba(255,255,255,0.2); text-transform:uppercase;
  margin:24px 0 12px; padding-bottom:8px;
  border-bottom:1px solid rgba(255,255,255,0.06); }
</style>
"""


def _time_of_day():
    h = datetime.datetime.now().hour
    if h < 6:    return "night",     "🌙", "Good Night, Scholar"
    elif h < 12: return "morning",   "☀️", "Good Morning, Scholar"
    elif h < 17: return "afternoon", "🌤️", "Good Afternoon, Scholar"
    elif h < 21: return "evening",   "🌆", "Good Evening, Scholar"
    else:        return "night",     "🌙", "Good Night, Scholar"


def _days_until(target_date) -> int:
    today = datetime.date.today()
    if isinstance(target_date, datetime.datetime):
        target_date = target_date.date()
    try:
        if isinstance(target_date, str):
            target_date = datetime.date.fromisoformat(target_date)
    except Exception:
        return 0
    return max(0, (target_date - today).days)


def render_exam_countdown_widget():
    """Compact sidebar exam countdown widget."""
    exam_date = st.session_state.get("exam_date")
    if not exam_date:
        return
    days = _days_until(exam_date)
    if isinstance(exam_date, str):
        try:
            exam_date = datetime.date.fromisoformat(exam_date)
        except Exception:
            return
    total_prep = 60
    elapsed    = max(0, total_prep - days)
    pct        = min(100, int((elapsed / total_prep) * 100))
    day_cls    = "days-danger" if days <= 7 else ("days-warn" if days <= 14 else "days-good")
    bar_bg     = "#ef4444" if days <= 7 else ("#f97316" if days <= 14 else "#10b981")
    # mini bar
    st.markdown(f"""
    <div style="background:rgba(15,23,42,0.7);border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:12px 14px;margin:6px 0;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <span style="font-size:18px;">🎯</span>
        <div>
          <div style="font-family:'Rajdhani',sans-serif;font-size:13px;font-weight:700;color:#fff;">Exam Countdown</div>
          <div style="font-family:'Space Mono',monospace;font-size:8px;color:rgba(255,255,255,0.3);">{exam_date.strftime('%b %d, %Y')}</div>
        </div>
        <div style="margin-left:auto;font-family:'Orbitron',monospace;font-size:20px;font-weight:900;" class="{day_cls}">{days}</div>
      </div>
      <div style="height:3px;background:rgba(255,255,255,0.05);border-radius:100px;overflow:hidden;">
        <div style="height:100%;width:{pct}%;background:{bar_bg};border-radius:100px;"></div>
      </div>
      <div style="font-family:'Space Mono',monospace;font-size:8px;color:rgba(255,255,255,0.2);margin-top:4px;text-align:right;">{pct}% PREP ELAPSED</div>
    </div>
    """, unsafe_allow_html=True)


def _render_exam_ring(days: int, exam_date, exam_name: str = "Exam"):
    """Render a circular exam countdown card."""
    total_prep = 60
    elapsed    = max(0, total_prep - days)
    pct        = min(100, (elapsed / total_prep))
    circum = 2 * 3.14159 * 34
    offset = circum * (1 - pct)
    day_cls  = "days-danger" if days <= 7 else ("days-warn" if days <= 14 else "days-good")
    ring_cls = "ring-danger" if days <= 7 else ("ring-warn" if days <= 14 else "ring-good")
    if isinstance(exam_date, str):
        try: exam_date = datetime.date.fromisoformat(exam_date)
        except: return
    date_str = exam_date.strftime("%B %d, %Y")

    st.markdown(f"""
    <div class="exam-ring-card">
      <div style="position:relative;width:80px;height:80px;">
        <svg class="exam-ring-svg" viewBox="0 0 80 80">
          <defs>
            <linearGradient id="ringDanger" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#ef4444"/>
              <stop offset="100%" style="stop-color:#f97316"/>
            </linearGradient>
            <linearGradient id="ringWarn" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#f97316"/>
              <stop offset="100%" style="stop-color:#fbbf24"/>
            </linearGradient>
            <linearGradient id="ringGood" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#10b981"/>
              <stop offset="100%" style="stop-color:#34d399"/>
            </linearGradient>
          </defs>
          <circle class="exam-ring-track" cx="40" cy="40" r="34"/>
          <circle class="exam-ring-fill {ring_cls}" cx="40" cy="40" r="34"
            stroke-dasharray="{circum:.1f}" stroke-dashoffset="{offset:.1f}"/>
        </svg>
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
          <div class="exam-days-big {day_cls}" style="font-size:22px;">{days}</div>
          <div class="exam-days-lbl">DAYS</div>
        </div>
      </div>
      <div class="exam-ring-info">
        <div class="exam-name-lbl">🎯 {exam_name}</div>
        <div class="exam-date-lbl">{date_str}</div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:13px;color:rgba(255,255,255,0.45);">
          {"⚠️ Critical — prioritize today!" if days <= 7 else ("📅 Focus and stay consistent." if days <= 14 else "✅ You have time — build strong foundations.")}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_daily_briefing_page():
    """Full daily briefing page."""
    st.markdown(BRIEFING_CSS, unsafe_allow_html=True)

    time_period, emoji_icon, greeting = _time_of_day()
    today_str = datetime.date.today().strftime("%A, %B %d %Y").upper()
    now_str   = datetime.datetime.now().strftime("%H:%M")

    # Time-of-day hero theme
    hero_cls = f"briefing-hero time-{time_period}"
    st.markdown(f"""
    <div class="{hero_cls}">
      <div class="briefing-date">{today_str} · {now_str}</div>
      <span class="briefing-time-icon">{emoji_icon}</span>
      <div class="briefing-greeting">{greeting}</div>
      <div class="briefing-sub">Your personalized AI study intelligence briefing is ready.</div>
      <div class="streak-badge-row">
    """, unsafe_allow_html=True)

    # Streak badges
    try:
        from study_streak_engine import _load_streak_data, _level_from_xp, _xp_progress
        sd  = _load_streak_data()
        lv, xp_in, xp_need = _xp_progress(sd.get("total_xp", 0))
        st.markdown(f"""
        <span class="streak-badge">🔥 {sd.get('streak',0)}-DAY STREAK</span>
        <span class="xp-badge">⭐ LVL {lv} · {sd.get('total_xp',0):,} XP</span>
        <span class="xp-badge">📅 {len(sd.get('study_days',[]))} TOTAL DAYS</span>
        """, unsafe_allow_html=True)
    except Exception:
        pass
    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Exam Countdown ──────────────────────────────────────────────────────
    exam_date = st.session_state.get("exam_date")
    if exam_date:
        exam_name = st.session_state.get("exam_name", "Upcoming Exam")
        days = _days_until(exam_date)
        _render_exam_ring(days, exam_date, exam_name)

    # ── AI Briefing ─────────────────────────────────────────────────────────
    st.markdown('<div class="brief-section">✨ AI MORNING BRIEF</div>', unsafe_allow_html=True)

    brief_key = f"daily_brief_{datetime.date.today().isoformat()}"
    if brief_key not in st.session_state:
        context = st.session_state.get("context_text", "")[:2000]
        subject = st.session_state.get("pomo_subject", "General Study")
        exam_info = ""
        if exam_date:
            try:
                days = _days_until(exam_date)
                exam_info = f"Exam in {days} days. "
            except Exception:
                pass

        with st.spinner("✨ Generating your personalized briefing..."):
            try:
                raw = generate(
                    prompt=f"""Generate a personalized study briefing.
Subject: {subject}. {exam_info}
Context: {context[:800] if context else 'No material yet.'}

Return JSON with:
- "motivation": powerful 1-sentence energizer (max 22 words)
- "topic_of_day": specific focus topic for today (2 sentences)
- "quick_tip": actionable study technique (2-3 sentences)
- "study_schedule": 3-item list of what to do today, each as a string
- "challenge_question": thought-provoking subject question
- "challenge_answer": answer with brief explanation (2-3 sentences)
- "word_of_day": {{"word": "...", "meaning": "...", "example": "..."}}

Return ONLY valid JSON. No extra text.""",
                    system="You are an elite academic AI. Return ONLY valid JSON.",
                    max_tokens=700,
                    temperature=0.7
                )
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    st.session_state[brief_key] = json.loads(m.group(0))
                else:
                    st.session_state[brief_key] = {}
            except Exception:
                st.session_state[brief_key] = {
                    "motivation": "Every great scholar was once a beginner — your effort today is tomorrow's expertise.",
                    "topic_of_day": "Focus on your most challenging concept first. Peak energy = peak learning.",
                    "quick_tip": "Try the Feynman Technique: explain the concept as if teaching a child. Where you stumble = where you need more study.",
                    "study_schedule": ["Review yesterday's notes (15 min)", "Deep focus on hardest topic (45 min)", "Practice questions (30 min)"],
                    "challenge_question": "What is the single most important concept you need to master before your next exam?",
                    "challenge_answer": "Identify your weakest area and dedicate focused time to it today using active recall.",
                    "word_of_day": {"word": "Catalyst", "meaning": "A substance that increases the rate of a reaction without being consumed.", "example": "Enzymes act as biological catalysts."},
                }

    brief = st.session_state.get(brief_key, {})

    # ── Enrich fallback with live free API data ─────────────────────────────
    # If AI gave an empty/failed brief, try enriching from free APIs
    _live_key = f"live_enrich_{datetime.date.today().isoformat()}"
    if _live_key not in st.session_state:
        enrichments = {}
        # Live Quote of the Day
        try:
            q = get_today_quote()
            if q and q.get("text"):
                if not brief.get("motivation"):
                    brief["motivation"] = f"\"{q['text']}\" — {q.get('author','')}"
                enrichments["live_quote"] = {"text": q["text"], "author": q.get("author","")}
        except Exception:
            pass
        # Live Trivia Challenge
        try:
            trivia_q = get_trivia(count=1, category="Science & Nature", difficulty="medium")
            if trivia_q:
                q0 = trivia_q[0]
                if not brief.get("challenge_question"):
                    brief["challenge_question"] = q0["question"]
                    brief["challenge_answer"]  = f"Correct answer: **{q0['correct']}**"
                enrichments["trivia"] = q0
        except Exception:
            pass
        # Public Holidays (for context)
        try:
            today     = datetime.date.today()
            holidays  = get_public_holidays(today.year, "IN")  # India default
            upcoming  = [h for h in holidays if h.get("date", "") >= today.isoformat()][:3]
            enrichments["holidays"] = upcoming
        except Exception:
            pass
        # NASA Astronomy Picture of the Day
        try:
            apod = get_nasa_apod()
            if apod and apod.get("title"):
                enrichments["apod"] = apod
        except Exception:
            pass
        # Today in History
        try:
            history = get_today_in_history()
            if history and history.get("events"):
                enrichments["history"] = history
        except Exception:
            pass
        # Significant earthquakes this week
        try:
            quakes = get_earthquakes(feed="significant_week", limit=3)
            if quakes:
                enrichments["earthquakes"] = quakes
        except Exception:
            pass
        st.session_state[_live_key] = enrichments
    live_data = st.session_state.get(_live_key, {})

    if brief.get("motivation"):
        st.markdown(f"""
        <div class="briefing-card bc-purple" style="animation-delay:0s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">⚡</span>
            <div class="briefing-card-title">Today's Ignition</div>
          </div>
          <div class="briefing-card-body">{brief['motivation']}</div>
        </div>""", unsafe_allow_html=True)

    # Topic of Day
    if brief.get("topic_of_day"):
        st.markdown(f"""
        <div class="briefing-card bc-blue" style="animation-delay:0.07s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">🎯</span>
            <div class="briefing-card-title">Topic of the Day</div>
          </div>
          <div class="briefing-card-body">{brief['topic_of_day']}</div>
        </div>""", unsafe_allow_html=True)

    # Study Tip
    if brief.get("quick_tip"):
        st.markdown(f"""
        <div class="briefing-card bc-green" style="animation-delay:0.14s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">💡</span>
            <div class="briefing-card-title">Pro Study Technique</div>
          </div>
          <div class="briefing-card-body">{brief['quick_tip']}</div>
        </div>""", unsafe_allow_html=True)

    # Word of Day
    wod = brief.get("word_of_day", {})
    if wod.get("word"):
        st.markdown(f"""
        <div class="briefing-card bc-pink" style="animation-delay:0.21s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">📖</span>
            <div class="briefing-card-title">Word of the Day</div>
          </div>
          <div class="briefing-card-body">
            <strong>{wod['word']}</strong> — {wod.get('meaning','')}<br>
            <span style="opacity:0.55;font-size:13px;">"{wod.get('example','')}"</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # Study Schedule checklist
    schedule = brief.get("study_schedule", [])
    if schedule:
        st.markdown('<div class="brief-section">📋 TODAY\'S STUDY PLAN</div>', unsafe_allow_html=True)
        done_key = f"brief_done_{brief_key}"
        if done_key not in st.session_state:
            st.session_state[done_key] = set()
        for i, task in enumerate(schedule[:5]):
            done = i in st.session_state[done_key]
            done_cls = "check-item done" if done else "check-item"
            bullet = "✅" if done else "⬜"
            st.markdown(f'<div class="{done_cls}"><span class="check-bullet">{bullet}</span>{task}</div>',
                        unsafe_allow_html=True)
            if not done and st.button(f"Mark done", key=f"brief_check_{i}_{brief_key}", use_container_width=False):
                st.session_state[done_key].add(i)
                st.rerun()

    # Challenge
    if brief.get("challenge_question"):
        st.markdown('<div class="brief-section">🧠 MORNING CHALLENGE</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="challenge-card"><div class="challenge-q">❓ {brief["challenge_question"]}</div>',
                    unsafe_allow_html=True)

        if "briefing_revealed" not in st.session_state:
            st.session_state["briefing_revealed"] = False

        if st.session_state.get("briefing_revealed"):
            st.markdown(f'<div class="challenge-reveal">✅ {brief.get("challenge_answer","")}</div>',
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("💡 Reveal Answer", use_container_width=True, key="brief_reveal"):
                st.session_state["briefing_revealed"] = True; st.rerun()
        with col_b:
            if st.button("🔄 New Briefing", use_container_width=True, key="brief_regen"):
                if brief_key in st.session_state:
                    del st.session_state[brief_key]
                st.session_state["briefing_revealed"] = False
                st.rerun()
        with col_c:
            subject_input = st.text_input("Subject focus", value=st.session_state.get("pomo_subject",""),
                                          key="brief_subject_inp", label_visibility="collapsed",
                                          placeholder="e.g. Physics, Maths...")
            if subject_input:
                st.session_state.pomo_subject = subject_input

    # ── Live Free API Widgets ────────────────────────────────────────────────
    live_data = st.session_state.get(_live_key, {})

    # Upcoming holidays panel
    holidays = live_data.get("holidays", [])
    if holidays:
        holiday_items = "".join(
            f"<div style='padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);'>"
            f"<span style='color:#fbbf24;font-weight:700;'>{h.get('date','')}</span>"
            f" &nbsp;—&nbsp; {h.get('name','')}"
            f" <span style='font-size:10px;color:rgba(255,255,255,0.3);'>({h.get('type','')})</span></div>"
            for h in holidays[:3]
        )
        st.markdown(f"""
        <div class="briefing-card bc-blue" style="animation-delay:0.5s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">🗓️</span>
            <div class="briefing-card-title">Upcoming Holidays</div>
          </div>
          <div class="briefing-card-body">{holiday_items}</div>
        </div>""", unsafe_allow_html=True)

    # Live quote card
    live_q = live_data.get("live_quote")
    if live_q:
        st.markdown(f"""
        <div style="background:rgba(167,139,250,0.05);border:1px solid rgba(167,139,250,0.15);
            border-left:3px solid #a78bfa;border-radius:14px;padding:16px 20px;margin:12px 0;">
            <div style="font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.3);margin-bottom:8px;">💬 LIVE QUOTE OF THE DAY</div>
            <div style="font-size:15px;color:rgba(255,255,255,0.85);font-style:italic;">"{live_q.get('text','')}"</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.4);margin-top:6px;">— {live_q.get('author','')}</div>
        </div>""", unsafe_allow_html=True)

    # ── NASA Astronomy Picture of the Day ────────────────────────────────────
    apod = live_data.get("apod")
    if apod:
        media = apod.get("media_type", "image")
        img_html = (f'<img src="{apod["url"]}" style="width:100%;border-radius:10px;margin-bottom:10px;">'
                    if media == "image" else
                    f'<a href="{apod["url"]}" target="_blank" style="color:#60a5fa;">▶ View Video</a>')
        st.markdown(f"""
        <div class="briefing-card bc-blue" style="animation-delay:0.55s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">🔭</span>
            <div class="briefing-card-title">NASA: Astronomy Picture of the Day</div>
          </div>
          <div class="briefing-card-body">
            {img_html}
            <strong>{apod.get('title','')}</strong> <span style="font-size:11px;color:rgba(255,255,255,0.35);">({apod.get('date','')})</span>
            <div style="font-size:12px;color:rgba(255,255,255,0.55);margin-top:6px;">{apod.get('explanation','')[:280]}…</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Today in History ─────────────────────────────────────────────────────
    history = live_data.get("history")
    if history and history.get("events"):
        hist_items = "".join(
            f"<div style='padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);'>"
            f"<span style='color:#34d399;font-weight:700;min-width:50px;display:inline-block;'>{e.get('year','')}</span>"
            f" {e.get('text','')[:90]}{'…' if len(e.get('text','')) > 90 else ''}</div>"
            for e in history["events"][:5]
        )
        st.markdown(f"""
        <div class="briefing-card bc-green" style="animation-delay:0.6s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">📜</span>
            <div class="briefing-card-title">Today in History</div>
          </div>
          <div class="briefing-card-body">{hist_items}</div>
        </div>""", unsafe_allow_html=True)

    # ── Significant Earthquakes ───────────────────────────────────────────────
    quakes = live_data.get("earthquakes")
    if quakes:
        quake_items = "".join(
            f"<div style='padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);'>"
            f"<span style='color:#f87171;font-weight:800;'>M{q.get('magnitude','?')}</span>"
            f" {q.get('place','Unknown')} "
            f"<span style='font-size:10px;color:rgba(255,255,255,0.3);'>{q.get('time','')}</span>"
            f"{'  🌊 TSUNAMI' if q.get('tsunami') else ''}</div>"
            for q in quakes[:4]
        )
        st.markdown(f"""
        <div class="briefing-card bc-purple" style="animation-delay:0.65s;">
          <div class="briefing-card-header">
            <span class="briefing-card-icon">🌍</span>
            <div class="briefing-card-title">Significant Earthquakes This Week</div>
          </div>
          <div class="briefing-card-body">{quake_items}</div>
        </div>""", unsafe_allow_html=True)

    # Exam date setter
    with st.expander("🎯 Set Exam Countdown"):
        exam_name_inp = st.text_input("Exam name", value=st.session_state.get("exam_name",""), key="brief_exam_name")
        exam_date_inp = st.date_input("Exam date", key="brief_exam_date")
        if st.button("Save Exam Date", key="brief_save_exam", use_container_width=True):
            st.session_state.exam_date = exam_date_inp.isoformat()
            st.session_state.exam_name = exam_name_inp
            st.rerun()

    # ── Quick Actions
    st.divider()
    st.markdown("#### 🚀 Ready to Study?")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💬 Open Chat", use_container_width=True, key="brief_chat"):
            st.session_state.app_mode = "chat"; st.rerun()
    with c2:
        if st.button("🍅 Pomodoro", use_container_width=True, key="brief_pomo"):
            st.session_state.app_mode = "pomodoro"; st.rerun()
    with c3:
        if st.button("🃏 Flashcards", use_container_width=True, key="brief_cards"):
            st.session_state.app_mode = "flashcards"; st.rerun()
    with c4:
        if st.button("📝 Smart Notes", use_container_width=True, key="brief_notes"):
            st.session_state.app_mode = "smart_notes"; st.rerun()
