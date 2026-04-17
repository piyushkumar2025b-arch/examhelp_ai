"""
pomodoro_engine.py — ExamHelp AI Pomodoro Focus Engine v2.1
Beautiful, gamified Pomodoro timer with:
- Session goals & subject tracking
- Live motivational quotes via Quotable API (free, no key)
- Ambient sound integration hint
- Improved ring timer with pulsing glow
- Better session history
"""
import streamlit as st
import time
import json
import datetime
from utils.ai_engine import generate
from free_apis import get_random_quote, get_today_quote


# ─── Motivational Quotes Pool ──────────────────────────────────────────────────
FOCUS_QUOTES = [
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Deep work: Professional activities performed in a state of distraction-free concentration.", "Cal Newport"),
    ("It's not that I'm so smart, it's just that I stay with problems longer.", "Albert Einstein"),
    ("Focused, hard work is the real key to success.", "John Carmack"),
    ("You don't rise to the level of your goals; you fall to the level of your systems.", "James Clear"),
    ("The ability to focus is a superpower in an age of distraction.", "Naval Ravikant"),
    ("Small daily improvements are the key to staggering long-term results.", "Robin Sharma"),
    ("Motivation gets you started; habit keeps you going.", "Jim Ryun"),
    ("Your focus determines your reality.", "Qui-Gon Jinn"),
    ("Excellence is not a destination but a continuous journey.", "Brian Tracy"),
]


def get_session_quote() -> tuple:
    """Fetch a live motivational quote (Quotable API) or fall back to local pool."""
    try:
        # Try today's featured quote first
        live = get_today_quote()
        if not live:
            live = get_random_quote(tags="motivational,success,wisdom")
        if live and live.get("text"):
            return (live["text"], live.get("author", "Unknown"))
    except Exception:
        pass
    # Local fallback
    import random
    return random.choice(FOCUS_QUOTES)


# ─── CSS ──────────────────────────────────────────────────────────────────────
POMODORO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

/* ── POMODORO PAGE ── */
.pomo-page {
  max-width: 820px;
  margin: 0 auto;
  padding: 16px;
}

/* ── TIMER CARD ── */
.pomo-card {
  position: relative;
  background: rgba(15,23,42,0.8);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 28px;
  padding: 40px 32px 32px;
  text-align: center;
  backdrop-filter: blur(24px);
  box-shadow:
    0 0 60px rgba(99,102,241,0.08),
    0 40px 80px rgba(0,0,0,0.45),
    inset 0 1px 0 rgba(255,255,255,0.06);
  overflow: hidden;
  margin-bottom: 20px;
}
.pomo-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 60% at 50% 0%,
    rgba(99,102,241,0.07) 0%, transparent 70%);
  pointer-events: none;
}
.pomo-card::after {
  content: '';
  position: absolute;
  top: -1px; left: 8%; right: 8%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.55), rgba(139,92,246,0.55), transparent);
}

/* ── MODE INDICATOR ── */
.pomo-mode-label {
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  letter-spacing: 6px;
  text-transform: uppercase;
  color: rgba(255,255,255,0.25);
  margin-bottom: 22px;
  position: relative;
}
.pomo-mode-label::after {
  content: '';
  display: block;
  width: 30px; height: 1px;
  background: currentColor;
  margin: 6px auto 0;
  opacity: 0.4;
}
.pomo-mode-work   { color: #818cf8; }
.pomo-mode-break  { color: #34d399; }
.pomo-mode-long   { color: #60a5fa; }

/* ── RING TIMER ── */
.pomo-ring-wrap {
  position: relative;
  width: 230px;
  height: 230px;
  margin: 0 auto 28px;
  filter: drop-shadow(0 0 0px transparent);
  transition: filter 0.5s ease;
}
.pomo-ring-wrap:hover {
  filter: drop-shadow(0 0 20px rgba(99,102,241,0.3));
}
.pomo-ring-svg {
  width: 230px;
  height: 230px;
  transform: rotate(-90deg);
}
.pomo-ring-track {
  fill: none;
  stroke: rgba(255,255,255,0.05);
  stroke-width: 10;
}
.pomo-ring-fill {
  fill: none;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s linear;
}
.fill-work  { stroke: url(#workGrad); }
.fill-break { stroke: url(#breakGrad); }
.fill-long  { stroke: url(#longGrad); }

/* Tick marks on ring */
.pomo-ring-ticks {
  position: absolute; inset: 0;
  pointer-events: none;
}

.pomo-time-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.pomo-digits {
  font-family: 'Orbitron', monospace;
  font-size: 54px;
  font-weight: 900;
  letter-spacing: -2px;
  line-height: 1;
  background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 50%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 20px rgba(99,102,241,0.4));
}
.pomo-session-label {
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  letter-spacing: 3px;
  color: rgba(255,255,255,0.25);
}
.pomo-progress-pct {
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  letter-spacing: 2px;
  color: rgba(255,255,255,0.2);
}

/* ── SUBJECT BADGE ── */
.pomo-subject-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 100px;
  padding: 6px 20px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: #a5b4fc;
  letter-spacing: 1px;
  margin-bottom: 24px;
  transition: all 0.25s ease;
}
.pomo-subject-badge:hover { background: rgba(99,102,241,0.18); border-color: rgba(99,102,241,0.4); }

/* ── GOAL BADGE ── */
.pomo-goal-badge {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.2);
  border-radius: 100px; padding: 5px 16px; margin-bottom: 20px;
  font-family: 'Rajdhani', sans-serif; font-size: 13px; color: #6ee7b7;
  letter-spacing: 0.5px;
}

/* ── STATS ROW ── */
.pomo-stats-row {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
  flex-wrap: wrap;
}
.pomo-stat {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  padding: 14px 18px;
  text-align: center;
  min-width: 85px;
  flex: 1;
  max-width: 120px;
  transition: all 0.25s ease;
}
.pomo-stat:hover { border-color: rgba(99,102,241,0.3); transform: translateY(-2px); }
.pomo-stat-val {
  font-family: 'Orbitron', monospace;
  font-size: 22px;
  font-weight: 900;
  background: linear-gradient(135deg, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 5px;
}
.pomo-stat-lbl {
  font-family: 'Space Mono', monospace;
  font-size: 8px;
  letter-spacing: 2px;
  color: rgba(255,255,255,0.2);
  text-transform: uppercase;
}

/* ── QUOTE CARD ── */
.pomo-quote {
  background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(139,92,246,0.03));
  border: 1px solid rgba(99,102,241,0.15);
  border-radius: 16px;
  padding: 16px 22px;
  margin: 14px 0;
  position: relative;
  text-align: left;
}
.pomo-quote::before {
  content: '"';
  position: absolute; top: 8px; left: 14px;
  font-size: 36px; line-height: 1;
  color: rgba(99,102,241,0.2);
  font-family: Georgia, serif;
}
.pomo-quote-text {
  font-family: 'Rajdhani', sans-serif; font-size: 14px;
  color: rgba(255,255,255,0.65); line-height: 1.7;
  padding-left: 20px;
}
.pomo-quote-author {
  font-family: 'Space Mono', monospace; font-size: 9px;
  color: rgba(99,102,241,0.5); letter-spacing: 2px;
  margin-top: 8px; padding-left: 20px;
}

/* ── SESSION LOG ── */
.pomo-log-card {
  background: rgba(15,23,42,0.65);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  padding: 14px 18px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 14px;
  animation: logIn 0.35s cubic-bezier(0.16,1,0.3,1) both;
  transition: all 0.2s ease;
}
.pomo-log-card:hover { border-color: rgba(99,102,241,0.25); transform: translateX(4px); }
@keyframes logIn {
  from { opacity:0; transform:translateX(-10px); }
  to   { opacity:1; transform:none; }
}
.pomo-log-icon {
  font-size: 22px;
  flex-shrink: 0;
}
.pomo-log-subject {
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}
.pomo-log-meta {
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  color: rgba(255,255,255,0.3);
  letter-spacing: 1px;
  margin-top: 3px;
}
.pomo-log-badge {
  margin-left: auto;
  flex-shrink: 0;
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 100px;
  padding: 4px 12px;
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  color: #818cf8;
  letter-spacing: 1px;
}

/* ── AI NUDGE CARD ── */
.pomo-nudge {
  background: linear-gradient(135deg,rgba(99,102,241,0.08),rgba(139,92,246,0.04));
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 16px;
  padding: 18px 22px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  color: rgba(255,255,255,0.75);
  line-height: 1.7;
  margin: 14px 0;
  position: relative;
}
.pomo-nudge::before {
  content: '✦';
  position: absolute;
  top: 14px; right: 16px;
  color: rgba(99,102,241,0.4);
  font-size: 13px;
}

/* ── PULSE ANIMATION FOR ACTIVE TIMER ── */
@keyframes pomoRingPulse {
  0%, 100% { filter: drop-shadow(0 0 8px rgba(99,102,241,0.3)); }
  50%       { filter: drop-shadow(0 0 24px rgba(99,102,241,0.7)); }
}
.pomo-ring-active {
  animation: pomoRingPulse 2.5s ease-in-out infinite;
}

/* ── BREAK PULSE ── */
@keyframes pomoBreakPulse {
  0%, 100% { filter: drop-shadow(0 0 8px rgba(52,211,153,0.3)); }
  50%       { filter: drop-shadow(0 0 24px rgba(52,211,153,0.6)); }
}
.pomo-ring-break {
  animation: pomoBreakPulse 3s ease-in-out infinite;
}

/* ── SECTION LABEL ── */
.pomo-section-label {
  font-family: 'Space Mono', monospace; font-size: 9px; letter-spacing: 4px;
  color: rgba(255,255,255,0.2); text-transform: uppercase;
  margin: 20px 0 12px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
</style>
"""


def _pomo_init():
    """Initialize Pomodoro session state."""
    defaults = {
        "pomo_state":         "idle",
        "pomo_time_left":     25 * 60,
        "pomo_total_time":    25 * 60,
        "pomo_session_num":   0,
        "pomo_sessions_done": 0,
        "pomo_work_mins":     0,
        "pomo_subject":       "General Study",
        "pomo_goal":          "",
        "pomo_log":           [],
        "pomo_work_dur":      25,
        "pomo_break_dur":     5,
        "pomo_long_break":    15,
        "pomo_long_after":    4,
        "pomo_last_tick":     None,
        "pomo_ai_nudge":      "",
        "pomo_nudge_ts":      0,
        "pomo_quote_idx":     0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _pomo_tick():
    """Advance timer by elapsed real-world seconds."""
    now = time.time()
    if st.session_state.pomo_state in ("work", "break", "long_break"):
        if st.session_state.pomo_last_tick:
            elapsed = int(now - st.session_state.pomo_last_tick)
            if elapsed > 0:
                st.session_state.pomo_time_left = max(
                    0, st.session_state.pomo_time_left - elapsed
                )
                if st.session_state.pomo_state == "work":
                    st.session_state.pomo_work_mins += elapsed // 60
        st.session_state.pomo_last_tick = now
    return st.session_state.pomo_time_left == 0


def _pomo_start_work():
    dur = st.session_state.pomo_work_dur * 60
    st.session_state.pomo_state     = "work"
    st.session_state.pomo_time_left = dur
    st.session_state.pomo_total_time = dur
    st.session_state.pomo_last_tick  = time.time()
    st.session_state.pomo_session_num += 1
    # Advance quote
    st.session_state.pomo_quote_idx = (st.session_state.pomo_quote_idx + 1) % len(FOCUS_QUOTES)


def _pomo_start_break(long=False):
    if long:
        dur = st.session_state.pomo_long_break * 60
        st.session_state.pomo_state = "long_break"
    else:
        dur = st.session_state.pomo_break_dur * 60
        st.session_state.pomo_state = "break"
    st.session_state.pomo_time_left  = dur
    st.session_state.pomo_total_time = dur
    st.session_state.pomo_last_tick  = time.time()
    # Log completed work session
    log_entry = {
        "subject": st.session_state.pomo_subject,
        "goal":    st.session_state.pomo_goal,
        "mins":    st.session_state.pomo_work_dur,
        "ts":      datetime.datetime.now().strftime("%H:%M"),
        "date":    datetime.date.today().isoformat(),
    }
    st.session_state.pomo_log.insert(0, log_entry)
    st.session_state.pomo_sessions_done += 1

    # Award XP for completed session
    try:
        from study_streak_engine import award_xp, unlock_achievement
        award_xp(5, "Pomodoro session completed")
        if st.session_state.pomo_sessions_done >= 5:
            unlock_achievement("pomo_5")
        if st.session_state.pomo_sessions_done >= 25:
            unlock_achievement("pomo_25")
    except Exception:
        pass


def _pomo_reset():
    st.session_state.pomo_state      = "idle"
    st.session_state.pomo_time_left  = st.session_state.pomo_work_dur * 60
    st.session_state.pomo_total_time = st.session_state.pomo_work_dur * 60
    st.session_state.pomo_last_tick  = None


def _get_ai_nudge(subject: str) -> str:
    try:
        return generate(
            prompt=f"Give a single powerful, motivational sentence (max 25 words) to a student who just completed a focused Pomodoro study session on: {subject}. Be energetic and specific.",
            system="You return exactly one motivational sentence. No quotes, no extra text.",
            max_tokens=60
        )
    except Exception:
        return "Fantastic focus session! Every minute of deep work compounds into mastery. 🚀"


def render_pomodoro_page():
    """Render the full Pomodoro Focus Engine page."""
    _pomo_init()
    st.markdown(POMODORO_CSS, unsafe_allow_html=True)

    # ── Tick the timer ──────────────────────────────────────────────────────
    session_complete = _pomo_tick()

    if session_complete and st.session_state.pomo_state == "work":
        is_long = (st.session_state.pomo_sessions_done + 1) % st.session_state.pomo_long_after == 0
        _pomo_start_break(long=is_long)
        if time.time() - st.session_state.pomo_nudge_ts > 60:
            st.session_state.pomo_ai_nudge = _get_ai_nudge(st.session_state.pomo_subject)
            st.session_state.pomo_nudge_ts = time.time()
        st.rerun()
    elif session_complete and st.session_state.pomo_state in ("break", "long_break"):
        _pomo_reset()
        st.rerun()

    state   = st.session_state.pomo_state
    t_left  = st.session_state.pomo_time_left
    t_total = st.session_state.pomo_total_time or 1
    mins, secs = divmod(t_left, 60)
    progress   = max(0.0, min(1.0, t_left / t_total))
    pct_done   = int((1 - progress) * 100)
    circumference = 2 * 3.14159 * 95   # radius 95
    dash_offset   = circumference * (1 - progress)

    # Determine mode colour / class
    if state == "break":
        mode_label = "SHORT BREAK"; mode_cls = "pomo-mode-break"; grad_cls = "fill-break"; ring_cls = "pomo-ring-break"
    elif state == "long_break":
        mode_label = "LONG BREAK";  mode_cls = "pomo-mode-long";  grad_cls = "fill-long";  ring_cls = "pomo-ring-break"
    elif state == "work":
        mode_label = "FOCUS SESSION"; mode_cls = "pomo-mode-work"; grad_cls = "fill-work"; ring_cls = "pomo-ring-active"
    else:
        mode_label = "READY TO FOCUS"; mode_cls = "pomo-mode-work"; grad_cls = "fill-work"; ring_cls = ""

    # Goal badge
    goal_html = ""
    if st.session_state.pomo_goal:
        goal_html = f'<div class="pomo-goal-badge">🎯 Goal: {st.session_state.pomo_goal[:60]}</div>'

    st.markdown(f"""
    <div class="pomo-card">
      <div class="pomo-mode-label {mode_cls}">{mode_label}</div>
      <div class="pomo-subject-badge">📚 {st.session_state.pomo_subject}</div>
      {goal_html}
      <div class="pomo-ring-wrap {ring_cls}">
        <svg class="pomo-ring-svg" viewBox="0 0 200 200">
          <defs>
            <linearGradient id="workGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#6366f1"/>
              <stop offset="100%" style="stop-color:#a78bfa"/>
            </linearGradient>
            <linearGradient id="breakGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#34d399"/>
              <stop offset="100%" style="stop-color:#06b6d4"/>
            </linearGradient>
            <linearGradient id="longGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#60a5fa"/>
              <stop offset="100%" style="stop-color:#818cf8"/>
            </linearGradient>
          </defs>
          <circle class="pomo-ring-track" cx="100" cy="100" r="95"/>
          <circle class="pomo-ring-fill {grad_cls}"
            cx="100" cy="100" r="95"
            stroke-dasharray="{circumference:.1f}"
            stroke-dashoffset="{dash_offset:.1f}"/>
        </svg>
        <div class="pomo-time-overlay">
          <div class="pomo-digits">{mins:02d}:{secs:02d}</div>
          <div class="pomo-session-label">SESSION {st.session_state.pomo_session_num}</div>
          <div class="pomo-progress-pct">{pct_done}% COMPLETE</div>
        </div>
      </div>

      <div class="pomo-stats-row">
        <div class="pomo-stat">
          <div class="pomo-stat-val">{st.session_state.pomo_sessions_done}</div>
          <div class="pomo-stat-lbl">Done</div>
        </div>
        <div class="pomo-stat">
          <div class="pomo-stat-val">{st.session_state.pomo_work_mins}</div>
          <div class="pomo-stat-lbl">Focus Mins</div>
        </div>
        <div class="pomo-stat">
          <div class="pomo-stat-val">{st.session_state.pomo_work_mins // 60 if st.session_state.pomo_work_mins >= 60 else 0}</div>
          <div class="pomo-stat-lbl">Hours</div>
        </div>
        <div class="pomo-stat">
          <div class="pomo-stat-val">{len(st.session_state.pomo_log)}</div>
          <div class="pomo-stat-lbl">Log Entries</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Motivational Quote ──────────────────────────────────────────────────
    if state in ("idle", "work"):
        q_idx = st.session_state.pomo_quote_idx % len(FOCUS_QUOTES)
        q_text, q_author = FOCUS_QUOTES[q_idx]
        st.markdown(f"""
        <div class="pomo-quote">
          <div class="pomo-quote-text">{q_text}</div>
          <div class="pomo-quote-author">— {q_author}</div>
        </div>""", unsafe_allow_html=True)

    # ── Controls ────────────────────────────────────────────────────────────
    if state == "idle":
        c1, c2 = st.columns([3, 1])
        with c1:
            if st.button("▶ Start Focus Session", type="primary", use_container_width=True, key="pomo_start"):
                _pomo_start_work()
                st.rerun()
        with c2:
            if st.button("← Back", use_container_width=True, key="pomo_back_idle"):
                st.session_state.app_mode = "chat"; st.rerun()
    elif state == "work":
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            if st.button("⏸ Pause / Reset", use_container_width=True, key="pomo_reset"):
                _pomo_reset(); st.rerun()
        with c2:
            if st.button("⏭ Skip to Break", use_container_width=True, key="pomo_skip"):
                _pomo_start_break(); st.rerun()
        with c3:
            if st.button("←", use_container_width=True, key="pomo_back_work"):
                st.session_state.app_mode = "chat"; st.rerun()
        # Auto-refresh every 5s while running
        st.markdown("""<script>setTimeout(function(){window.location.reload();},5000);</script>""", unsafe_allow_html=True)
    else:  # break
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            if st.button("▶ Start Next Focus", type="primary", use_container_width=True, key="pomo_next"):
                _pomo_start_work(); st.rerun()
        with c2:
            if st.button("⏹ End Session", use_container_width=True, key="pomo_end"):
                _pomo_reset(); st.rerun()
        with c3:
            if st.button("←", use_container_width=True, key="pomo_back_brk"):
                st.session_state.app_mode = "chat"; st.rerun()
        st.markdown("""<script>setTimeout(function(){window.location.reload();},5000);</script>""", unsafe_allow_html=True)

    # ── AI Nudge at break ───────────────────────────────────────────────────
    if st.session_state.pomo_ai_nudge and state in ("break", "long_break"):
        st.markdown(f'<div class="pomo-nudge">✨ {st.session_state.pomo_ai_nudge}</div>',
                    unsafe_allow_html=True)

    # ── Settings Expander ───────────────────────────────────────────────────
    with st.expander("⚙️ Session Settings"):
        st.session_state.pomo_subject = st.text_input(
            "Study Subject", value=st.session_state.pomo_subject, key="pomo_subj_input"
        )
        st.session_state.pomo_goal = st.text_input(
            "Session Goal (optional)", value=st.session_state.pomo_goal,
            placeholder="e.g. Finish Chapter 5 of Thermodynamics",
            key="pomo_goal_input"
        )
        col_a, col_b, col_c = st.columns(3)
        with col_a: st.session_state.pomo_work_dur   = st.number_input("Focus (min)", 5, 90, st.session_state.pomo_work_dur, key="pomo_wd")
        with col_b: st.session_state.pomo_break_dur  = st.number_input("Break (min)", 1, 30, st.session_state.pomo_break_dur, key="pomo_bd")
        with col_c: st.session_state.pomo_long_break = st.number_input("Long Break", 5, 60, st.session_state.pomo_long_break, key="pomo_lb")
        st.session_state.pomo_long_after = st.slider("Long break after N sessions", 2, 8, st.session_state.pomo_long_after, key="pomo_la")

        # Sound hint
        playing_id = st.session_state.get("bg_sound_id")
        if playing_id:
            st.success(f"🎵 Ambient sound is active — great for focus!")
        else:
            if st.button("🎵 Add Ambient Sound for Focus", key="pomo_sound_btn", use_container_width=True):
                st.session_state.app_mode = "bg_sounds"; st.rerun()

        if st.button("Apply & Reset Timer", use_container_width=True, key="pomo_apply"):
            _pomo_reset()
            st.session_state.pomo_time_left  = st.session_state.pomo_work_dur * 60
            st.session_state.pomo_total_time = st.session_state.pomo_work_dur * 60
            st.rerun()

    # ── Session Log ─────────────────────────────────────────────────────────
    if st.session_state.pomo_log:
        st.markdown('<div class="pomo-section-label">📋 SESSION HISTORY</div>', unsafe_allow_html=True)
        for i, entry in enumerate(st.session_state.pomo_log[:8]):
            goal_text = f" · {entry['goal'][:40]}" if entry.get("goal") else ""
            st.markdown(f"""
            <div class="pomo-log-card" style="animation-delay:{i*0.05}s">
              <div class="pomo-log-icon">🍅</div>
              <div style="flex:1;">
                <div class="pomo-log-subject">{entry['subject']}</div>
                <div class="pomo-log-meta">{entry['date']} · {entry['ts']}{goal_text}</div>
              </div>
              <div class="pomo-log-badge">{entry['mins']} MIN</div>
            </div>""", unsafe_allow_html=True)

        col_clr, col_ins = st.columns(2)
        with col_clr:
            if st.button("🗑 Clear History", key="pomo_clear_log", use_container_width=True):
                st.session_state.pomo_log = []
                st.session_state.pomo_sessions_done = 0
                st.session_state.pomo_work_mins = 0
                st.rerun()
        with col_ins:
            if st.button("🧠 View Session Insights", key="pomo_goto_insights", use_container_width=True):
                st.session_state.app_mode = "insights"; st.rerun()
