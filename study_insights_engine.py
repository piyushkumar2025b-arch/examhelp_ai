"""
study_insights_engine.py — ExamHelp AI Session Insights & Mastery Map v2.0
Analyses the current chat conversation to produce:
  • Topics Coverage Map (improved visual chips with relevance sizing)
  • Concept Mastery Gauge (animated, color-coded bars + circular dial)
  • Weak Areas Radar (with actionable tips)
  • Suggested Next Steps (with difficulty tags)
  • Session Timeline (with timestamps)
  • Session Quality Score (circular dial)
  • Live Trivia Challenge (OpenTrivia DB — free, no key)
  • Motivational Quote (Quotable API — free, no key)
"""
import streamlit as st
import re
import json
import datetime
from utils.ai_engine import generate, quick_generate
from free_apis import get_trivia, get_random_quote, get_number_fact


INSIGHTS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

/* ── PAGE WRAPPER ── */
.ins-page { max-width: 960px; margin: 0 auto; }

/* ── HERO ── */
.ins-hero {
  background: linear-gradient(135deg, rgba(15,23,42,0.95) 0%, rgba(20,14,50,0.92) 100%);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 24px;
  padding: 28px 30px 24px;
  backdrop-filter: blur(24px);
  box-shadow: 0 0 80px rgba(99,102,241,0.08), 0 40px 80px rgba(0,0,0,0.45);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}
.ins-hero::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 60% 80% at 0% 50%, rgba(99,102,241,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.ins-hero::after {
  content: '';
  position: absolute;
  top: -1px; left: 8%; right: 8%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.6), rgba(139,92,246,0.6), transparent);
}
.ins-hero-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.ins-hero-left {}
.ins-hero-title {
  font-family: 'Orbitron', monospace;
  font-size: 24px;
  font-weight: 900;
  background: linear-gradient(135deg, #fff, #a5b4fc, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 5px;
}
.ins-hero-sub {
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  color: rgba(255,255,255,0.35);
  letter-spacing: 0.3px;
}
.ins-hero-badge {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3);
  border-radius: 100px; padding: 5px 14px;
  font-family: 'Space Mono', monospace; font-size: 10px;
  color: #a5b4fc; letter-spacing: 2px; margin-top: 8px;
}
.ins-badge-dot { width: 6px; height: 6px; background: #818cf8; border-radius: 50%; animation: insBlink 1.5s ease-in-out infinite; }
@keyframes insBlink { 0%,100%{opacity:1;} 50%{opacity:0.2;} }

/* ── QUALITY SCORE DIAL ── */
.quality-dial-wrap {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  flex-shrink: 0;
}
.quality-dial-svg { width: 100px; height: 100px; transform: rotate(-90deg); }
.quality-dial-track { fill: none; stroke: rgba(255,255,255,0.06); stroke-width: 8; }
.quality-dial-fill {
  fill: none; stroke-width: 8; stroke-linecap: round;
  transition: stroke-dashoffset 1s cubic-bezier(0.16,1,0.3,1);
}
.dial-great  { stroke: url(#dialGradGreat); }
.dial-good   { stroke: url(#dialGradGood); }
.dial-needs  { stroke: url(#dialGradNeeds); }
.quality-dial-center {
  position: relative; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.quality-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  pointer-events: none;
}
.quality-num {
  font-family: 'Orbitron', monospace; font-size: 22px; font-weight: 900;
  color: #a5b4fc; line-height: 1;
}
.quality-lbl {
  font-family: 'Space Mono', monospace; font-size: 7px;
  color: rgba(255,255,255,0.25); letter-spacing: 2px; margin-top: 2px;
}
.quality-tag {
  font-family: 'Space Mono', monospace; font-size: 9px; letter-spacing: 2px;
  color: rgba(255,255,255,0.35); text-align: center;
}

/* ── STAT CARDS ROW ── */
.ins-stats-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.ins-stat-card {
  flex: 1; min-width: 100px;
  background: rgba(15,23,42,0.7); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 14px 16px; text-align: center;
  transition: all 0.25s ease;
}
.ins-stat-card:hover { border-color: rgba(99,102,241,0.4); transform: translateY(-2px); }
.ins-stat-val {
  font-family: 'Orbitron', monospace; font-size: 22px; font-weight: 900;
  background: linear-gradient(135deg, #818cf8, #c084fc);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  line-height: 1; margin-bottom: 4px;
}
.ins-stat-lbl {
  font-family: 'Space Mono', monospace; font-size: 8px;
  letter-spacing: 2px; color: rgba(255,255,255,0.25); text-transform: uppercase;
}

/* ── TOPIC PILL ── */
.topic-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 100px;
  padding: 5px 14px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #a5b4fc;
  margin: 3px;
  transition: all 0.2s ease;
  cursor: default;
}
.topic-chip:hover {
  background: rgba(99,102,241,0.2);
  border-color: rgba(99,102,241,0.5);
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 4px 16px rgba(99,102,241,0.2);
}
.topic-chip .tc-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #818cf8;
  flex-shrink: 0;
  animation: insBlink 2s ease-in-out infinite;
}
.topic-chip.tc-lg { font-size: 15px; padding: 7px 18px; }
.topic-chip.tc-sm { font-size: 11px; padding: 4px 10px; opacity: 0.75; }

/* ── MASTERY GAUGE ── */
.mastery-bar-wrap {
  margin-bottom: 14px;
  animation: masteryIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes masteryIn { from{opacity:0;transform:translateX(-8px);} to{opacity:1;transform:none;} }
.mastery-bar-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.mastery-bar-name {
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: rgba(255,255,255,0.85);
}
.mastery-bar-pct {
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  letter-spacing: 1px;
  font-weight: 700;
}
.mastery-track {
  height: 8px;
  background: rgba(255,255,255,0.05);
  border-radius: 100px;
  overflow: hidden;
  position: relative;
}
.mastery-fill {
  height: 100%;
  border-radius: 100px;
  transition: width 1s cubic-bezier(0.16,1,0.3,1);
  position: relative;
}
.mastery-fill::after {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  animation: masteryShimmer 2s ease-in-out infinite;
}
@keyframes masteryShimmer { 0%{transform:translateX(-100%);} 100%{transform:translateX(200%);} }
.mf-high   { background: linear-gradient(90deg, #10b981, #34d399); box-shadow: 0 0 8px rgba(16,185,129,0.4); }
.mf-medium { background: linear-gradient(90deg, #f97316, #fbbf24); box-shadow: 0 0 8px rgba(249,115,22,0.4); }
.mf-low    { background: linear-gradient(90deg, #ef4444, #f87171); box-shadow: 0 0 8px rgba(239,68,68,0.4); }
.pct-high   { color: #34d399; }
.pct-medium { color: #fbbf24; }
.pct-low    { color: #f87171; }

.mastery-mini-tag {
  font-family: 'Space Mono', monospace; font-size: 9px; letter-spacing: 1px;
  padding: 2px 8px; border-radius: 100px; margin-left: 8px;
}
.tag-high   { background: rgba(16,185,129,0.1); color: #34d399; border: 1px solid rgba(16,185,129,0.2); }
.tag-medium { background: rgba(249,115,22,0.1); color: #fbbf24; border: 1px solid rgba(249,115,22,0.2); }
.tag-low    { background: rgba(239,68,68,0.1); color: #f87171; border: 1px solid rgba(239,68,68,0.2); }

/* ── WEAK AREA CARD ── */
.weak-card {
  background: rgba(239,68,68,0.04);
  border: 1px solid rgba(239,68,68,0.15);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 10px;
  display: flex;
  gap: 14px;
  align-items: flex-start;
  animation: weakIn 0.35s cubic-bezier(0.16,1,0.3,1) both;
  transition: all 0.25s ease;
}
.weak-card:hover { border-color: rgba(239,68,68,0.35); transform: translateX(4px); }
@keyframes weakIn {
  from { opacity:0; transform:translateX(12px); }
  to   { opacity:1; transform:none; }
}
.weak-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
.weak-topic {
  font-family: 'Rajdhani', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #fca5a5;
  margin-bottom: 5px;
}
.weak-reason {
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  color: rgba(255,255,255,0.45);
  line-height: 1.5;
}
.weak-tip {
  display: inline-block; margin-top: 8px;
  font-family: 'Space Mono', monospace; font-size: 9px; letter-spacing: 1px;
  background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.15);
  border-radius: 100px; padding: 3px 10px; color: #f87171;
}

/* ── NEXT STEP CARDS ── */
.next-card {
  background: rgba(16,185,129,0.04);
  border: 1px solid rgba(16,185,129,0.15);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 10px;
  display: flex;
  gap: 14px;
  align-items: flex-start;
  transition: all 0.25s ease;
  animation: nextIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes nextIn { from{opacity:0;transform:translateY(8px);} to{opacity:1;transform:none;} }
.next-card:hover { border-color: rgba(16,185,129,0.35); transform: translateX(4px); }
.next-num {
  font-family: 'Orbitron', monospace;
  font-size: 18px;
  font-weight: 900;
  color: #34d399;
  flex-shrink: 0;
  width: 28px;
  text-align: center;
  line-height: 1;
  margin-top: 2px;
}
.next-text {
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  color: rgba(255,255,255,0.75);
  line-height: 1.5;
  flex: 1;
}
.next-diff {
  flex-shrink: 0; align-self: flex-start;
  font-family: 'Space Mono', monospace; font-size: 9px; letter-spacing: 1px;
  padding: 3px 8px; border-radius: 100px;
  background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.2);
  color: #34d399; margin-top: 2px;
}

/* ── TIMELINE ── */
.timeline-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 16px;
  position: relative;
  animation: timelineIn 0.3s ease both;
}
@keyframes timelineIn { from{opacity:0;transform:translateY(6px);} to{opacity:1;transform:none;} }
.timeline-item::before {
  content: '';
  position: absolute;
  left: 14px; top: 30px;
  bottom: -16px; width: 1px;
  background: linear-gradient(180deg, rgba(99,102,241,0.25), transparent);
}
.timeline-item:last-child::before { display: none; }
.timeline-dot {
  width: 30px; height: 30px;
  border-radius: 50%;
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
  margin-top: 2px;
  transition: all 0.2s ease;
}
.timeline-dot:hover { border-color: rgba(99,102,241,0.6); background: rgba(99,102,241,0.2); }
.timeline-meta {
  display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
}
.timeline-role {
  font-family: 'Space Mono', monospace;
  font-size: 8px;
  color: rgba(255,255,255,0.25);
  letter-spacing: 2px;
  text-transform: uppercase;
}
.timeline-turn {
  font-family: 'Space Mono', monospace;
  font-size: 8px;
  color: rgba(99,102,241,0.5);
  letter-spacing: 1px;
}
.timeline-content {
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  color: rgba(255,255,255,0.6);
  line-height: 1.5;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  padding: 9px 13px;
  flex: 1;
  border: 1px solid rgba(255,255,255,0.05);
  transition: all 0.2s ease;
}
.timeline-content:hover { background: rgba(255,255,255,0.05); border-color: rgba(99,102,241,0.2); }
.timeline-user .timeline-content { border-left: 2px solid rgba(99,102,241,0.4); }
.timeline-ai .timeline-content { border-left: 2px solid rgba(16,185,129,0.4); }

/* ── KEY INSIGHT ── */
.ins-key-insight {
  background: linear-gradient(135deg, rgba(99,102,241,0.07), rgba(139,92,246,0.04));
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 16px;
  padding: 18px 22px;
  margin: 14px 0;
  font-family: 'Rajdhani', sans-serif;
  font-size: 15px;
  color: rgba(255,255,255,0.8);
  line-height: 1.7;
  position: relative;
  overflow: hidden;
}
.ins-key-insight::before {
  content: '✦';
  position: absolute; top: 14px; right: 16px;
  color: rgba(99,102,241,0.4); font-size: 14px;
}
.ins-key-insight::after {
  content: '';
  position: absolute; top: -1px; left: 15%; right: 15%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent);
}

/* ── EMPTY INSIGHTS ── */
.ins-empty {
  text-align: center;
  padding: 70px 20px;
  font-family: 'Rajdhani', sans-serif;
  color: rgba(255,255,255,0.3);
}
.ins-empty-icon { font-size: 52px; margin-bottom: 16px; display: block; animation: emptyFloat 3s ease-in-out infinite; }
@keyframes emptyFloat { 0%,100%{transform:translateY(0);} 50%{transform:translateY(-8px);} }
.ins-empty-title { font-size: 20px; font-weight: 700; margin-bottom: 10px; color: rgba(255,255,255,0.5); }
.ins-empty-sub   { font-size: 14px; line-height: 1.7; }

/* ── EXPORT BAR ── */
.ins-export-bar {
  display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
  background: rgba(15,23,42,0.6); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 12px 16px; margin-top: 4px;
}
.ins-export-label {
  font-family: 'Space Mono', monospace; font-size: 9px;
  color: rgba(255,255,255,0.25); letter-spacing: 3px; text-transform: uppercase;
  margin-right: 8px;
}
</style>
"""


def _analyse_with_ai(messages: list) -> dict:
    """Send conversation to AI for structured insights extraction."""
    convo = "\n\n".join(
        f"{'USER' if m['role']=='user' else 'AI'}: {m['content'][:500]}"
        for m in messages[-20:]
    )

    prompt = f"""Analyse this study conversation and return a JSON object with:

{{
  "topics": ["topic1", "topic2", ...],           // list of up to 8 topics covered
  "topic_relevance": [85, 70, 60, ...],          // relevance scores 0-100 for each topic (same length as topics)
  "mastery": [{{"name": "Topic", "score": 75, "verdict": "Strong"}}, ...],  // 0-100 mastery scores for 4-6 topics, verdict: Strong/Developing/Needs Work
  "weak_areas": [{{"topic": "X", "reason": "brief reason", "tip": "specific action to improve"}}],  // 2-3 weak areas
  "next_steps": [{{"step": "step text", "difficulty": "Easy/Medium/Hard"}}],  // 4 concrete recommended next steps
  "session_quality": 85,                         // overall session quality 0-100
  "key_insight": "One powerful insight about the student's learning in this session",
  "mood": "focused"                              // one word descriptor: focused/curious/struggling/productive
}}

Conversation:
{convo}

Return ONLY valid JSON. No markdown. No explanation."""

    raw = quick_generate(
        prompt=prompt,
        system="You are an expert learning analytics AI. Return only valid JSON with no extra text.",
        max_tokens=1000,
        temperature=0.3,
    )
    try:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception:
        pass
    return {}


def _export_session_text(messages: list, data: dict) -> str:
    """Generate a plain-text export of the session insights."""
    lines = [
        f"ExamHelp AI — Session Insights Report",
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 50,
        "",
        f"SESSION QUALITY: {data.get('session_quality', 'N/A')}/100",
        f"KEY INSIGHT: {data.get('key_insight', 'N/A')}",
        "",
        "TOPICS COVERED:",
        *[f"  • {t}" for t in data.get("topics", [])],
        "",
        "MASTERY GAUGE:",
        *[f"  • {m.get('name','')}: {m.get('score',0)}% — {m.get('verdict','')}" for m in data.get("mastery", [])],
        "",
        "WEAK AREAS:",
        *[f"  ⚠ {w.get('topic','')}: {w.get('reason','')}" for w in data.get("weak_areas", [])],
        "",
        "RECOMMENDED NEXT STEPS:",
        *[f"  {i+1}. {s.get('step', s) if isinstance(s, dict) else s}" for i, s in enumerate(data.get("next_steps", []))],
        "",
        "CONVERSATION SUMMARY:",
        f"  Total messages: {len(messages)}",
        f"  Words processed: ~{sum(len(m['content'].split()) for m in messages):,}",
    ]
    return "\n".join(lines)


def render_study_insights_page():
    """Full-page Study Session Insights."""
    st.markdown(INSIGHTS_CSS, unsafe_allow_html=True)

    messages = st.session_state.get("messages", [])

    # ── Hero with quality dial ────────────────────────────────────────────────
    msg_count  = len(messages)
    word_count = sum(len(m["content"].split()) for m in messages)

    # Load or generate insights first (needed for dial)
    cache_key = f"session_insights_{len(messages)}"
    data = {}
    if messages:
        if cache_key not in st.session_state:
            with st.spinner("🔍 Analysing your session..."):
                st.session_state[cache_key] = _analyse_with_ai(messages)
        data = st.session_state.get(cache_key, {})

    quality = data.get("session_quality", 0)
    q_color_cls = "dial-great" if quality > 75 else "dial-good" if quality > 50 else "dial-needs"
    q_color_hex = "#34d399" if quality > 75 else "#fbbf24" if quality > 50 else "#f87171"
    q_label     = "GREAT" if quality > 75 else "GOOD" if quality > 50 else "NEEDS WORK"
    circum = 2 * 3.14159 * 36  # radius 36
    offset = circum * (1 - quality / 100) if quality else circum
    mood   = data.get("mood", "—")

    st.markdown(f"""
    <div class="ins-hero">
      <div class="ins-hero-row">
        <div class="ins-hero-left">
          <div class="ins-hero-title">🧠 Session Insights</div>
          <div class="ins-hero-sub">
            AI-powered learning analytics · {msg_count} messages · ~{word_count:,} words
          </div>
          <div class="ins-hero-badge">
            <span class="ins-badge-dot"></span>
            MOOD: {mood.upper()} &nbsp;·&nbsp; LIVE ANALYSIS
          </div>
        </div>
        <div class="quality-dial-wrap">
          <div style="position:relative;width:100px;height:100px;">
            <svg class="quality-dial-svg" viewBox="0 0 80 80">
              <defs>
                <linearGradient id="dialGradGreat" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#10b981"/>
                  <stop offset="100%" style="stop-color:#34d399"/>
                </linearGradient>
                <linearGradient id="dialGradGood" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#f97316"/>
                  <stop offset="100%" style="stop-color:#fbbf24"/>
                </linearGradient>
                <linearGradient id="dialGradNeeds" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#ef4444"/>
                  <stop offset="100%" style="stop-color:#f87171"/>
                </linearGradient>
              </defs>
              <circle class="quality-dial-track" cx="40" cy="40" r="36"/>
              <circle class="quality-dial-fill {q_color_cls}"
                cx="40" cy="40" r="36"
                stroke-dasharray="{circum:.1f}"
                stroke-dashoffset="{offset:.1f}"/>
            </svg>
            <div class="quality-overlay">
              <div class="quality-num" style="color:{q_color_hex}">{quality}</div>
              <div class="quality-lbl">QUALITY</div>
            </div>
          </div>
          <div class="quality-tag" style="color:{q_color_hex}">{q_label}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    if not messages:
        st.markdown("""
        <div class="ins-empty">
          <span class="ins-empty-icon">💭</span>
          <div class="ins-empty-title">No Session Yet</div>
          <div class="ins-empty-sub">
            Start a study conversation, then come back here for<br>
            AI-powered insights on your learning progress.
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button("💬 Start Studying", use_container_width=True, key="ins_start"):
            st.session_state.app_mode = "chat"; st.rerun()
        return

    # ── Quick stats row ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="ins-stats-row">
      <div class="ins-stat-card">
        <div class="ins-stat-val">{msg_count}</div>
        <div class="ins-stat-lbl">Messages</div>
      </div>
      <div class="ins-stat-card">
        <div class="ins-stat-val">{len(data.get("topics", []))}</div>
        <div class="ins-stat-lbl">Topics</div>
      </div>
      <div class="ins-stat-card">
        <div class="ins-stat-val">{len(data.get("weak_areas", []))}</div>
        <div class="ins-stat-lbl">Weak Areas</div>
      </div>
      <div class="ins-stat-card">
        <div class="ins-stat-val">{len(data.get("mastery", []))}</div>
        <div class="ins-stat-lbl">Mastered</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Key Insight ───────────────────────────────────────────────────────────
    if data.get("key_insight"):
        st.markdown(f"""
        <div class="ins-key-insight">
          {data['key_insight']}
        </div>""", unsafe_allow_html=True)

    tab_topics, tab_mastery, tab_weak, tab_next, tab_timeline = st.tabs([
        "📚 Topics", "🎯 Mastery", "⚠️ Weak Areas", "🚀 Next Steps", "📋 Timeline"
    ])

    # ── Topics ────────────────────────────────────────────────────────────────
    with tab_topics:
        topics    = data.get("topics", [])
        relevance = data.get("topic_relevance", [80] * len(topics))
        if topics:
            st.markdown('<div style="margin-top:10px;line-height:2.2;">', unsafe_allow_html=True)
            chips = ""
            for i, t in enumerate(topics):
                rel = relevance[i] if i < len(relevance) else 80
                size_cls = "tc-lg" if rel >= 80 else ("tc-sm" if rel < 60 else "")
                chips += f'<span class="topic-chip {size_cls}"><span class="tc-dot"></span>{t}</span>'
            st.markdown(chips + "</div>", unsafe_allow_html=True)
        else:
            st.info("Topics will appear once the AI analyses your session.")

        if topics:
            st.markdown('<div style="margin-top:24px;font-family:Space Mono,monospace;font-size:9px;letter-spacing:4px;color:rgba(255,255,255,0.2);text-transform:uppercase;margin-bottom:12px;">DEEP DIVE INTO TOPIC</div>', unsafe_allow_html=True)
            t_cols = st.columns(min(len(topics), 3))
            for i, t in enumerate(topics[:6]):
                with t_cols[i % 3]:
                    if st.button(f"📖 {t[:28]}", key=f"ins_topic_{i}", use_container_width=True):
                        st.session_state.queued_prompt = f"Give me a deep, comprehensive explanation of {t} with examples, formulas, and exam tips."
                        st.session_state.app_mode = "chat"
                        st.rerun()

    # ── Mastery Gauges ────────────────────────────────────────────────────────
    with tab_mastery:
        mastery = data.get("mastery", [])
        if mastery:
            st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
            for item in mastery:
                score   = item.get("score", 50)
                verdict = item.get("verdict", "")
                cls     = "mf-high" if score >= 70 else "mf-medium" if score >= 40 else "mf-low"
                pct_cls = "pct-high" if score >= 70 else "pct-medium" if score >= 40 else "pct-low"
                tag_cls = "tag-high" if score >= 70 else "tag-medium" if score >= 40 else "tag-low"
                st.markdown(f"""
                <div class="mastery-bar-wrap">
                  <div class="mastery-bar-label">
                    <div>
                      <span class="mastery-bar-name">{item.get('name','')}</span>
                      {f'<span class="mastery-mini-tag {tag_cls}">{verdict}</span>' if verdict else ''}
                    </div>
                    <span class="mastery-bar-pct {pct_cls}">{score}%</span>
                  </div>
                  <div class="mastery-track">
                    <div class="mastery-fill {cls}" style="width:{score}%"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Study more content for the AI to measure your mastery.")

    # ── Weak Areas ────────────────────────────────────────────────────────────
    with tab_weak:
        weak = data.get("weak_areas", [])
        if weak:
            st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
            for i, w in enumerate(weak):
                tip_html = f'<div class="weak-tip">💡 {w["tip"]}</div>' if w.get("tip") else ""
                st.markdown(f"""
                <div class="weak-card" style="animation-delay:{i*0.1}s">
                  <div class="weak-icon">⚠️</div>
                  <div>
                    <div class="weak-topic">{w.get('topic','')}</div>
                    <div class="weak-reason">{w.get('reason','')}</div>
                    {tip_html}
                  </div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            if st.button("🎯 Generate Targeted Practice on Weak Areas", type="primary",
                         use_container_width=True, key="ins_weak_practice"):
                weak_topics = ", ".join(w.get("topic","") for w in weak)
                st.session_state.queued_prompt = (
                    f"Create a focused practice session targeting my weak areas: {weak_topics}. "
                    f"Include explanations, worked examples, and 5 practice problems for each."
                )
                st.session_state.app_mode = "chat"
                st.rerun()
        else:
            st.success("🎉 No significant weak areas detected in this session!")

    # ── Next Steps ────────────────────────────────────────────────────────────
    with tab_next:
        steps = data.get("next_steps", [])
        if steps:
            st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
            for i, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    step_text = step.get("step", "")
                    difficulty = step.get("difficulty", "")
                else:
                    step_text = step
                    difficulty = ""
                diff_html = f'<div class="next-diff">{difficulty}</div>' if difficulty else ""
                st.markdown(f"""
                <div class="next-card" style="animation-delay:{i*0.08}s">
                  <div class="next-num">{i}</div>
                  <div class="next-text">{step_text}</div>
                  {diff_html}
                </div>""", unsafe_allow_html=True)

            st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
            first_step = steps[0].get("step", steps[0]) if isinstance(steps[0], dict) else steps[0]
            if st.button("▶ Start with Step 1", type="primary",
                         use_container_width=True, key="ins_step1"):
                st.session_state.queued_prompt = first_step
                st.session_state.app_mode = "chat"
                st.rerun()
        else:
            st.info("Chat more to get personalised next-step recommendations.")

    # ── Timeline ─────────────────────────────────────────────────────────────
    with tab_timeline:
        st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
        for i, msg in enumerate(messages[-12:]):
            is_user  = msg["role"] == "user"
            icon     = "👤" if is_user else "🎓"
            role_lbl = "YOU" if is_user else "AI TUTOR"
            role_cls = "timeline-user" if is_user else "timeline-ai"
            preview  = msg["content"][:220].replace("\n", " ")
            turn_num = len(messages) - len(messages[-12:]) + i + 1
            st.markdown(f"""
            <div class="timeline-item {role_cls}" style="animation-delay:{i*0.05}s">
              <div class="timeline-dot">{icon}</div>
              <div style="flex:1;">
                <div class="timeline-meta">
                  <div class="timeline-role">{role_lbl}</div>
                  <div class="timeline-turn">· Turn {turn_num}</div>
                </div>
                <div class="timeline-content">{preview}{'...' if len(msg['content']) > 220 else ''}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    # ── Export ────────────────────────────────────────────────────────────────
    if data:
        export_text = _export_session_text(messages, data)
        st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
        st.download_button(
            label="📥 Export Session Report",
            data=export_text,
            file_name=f"examhelp_session_{datetime.date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
            key="ins_export"
        )

    # ── Actions ───────────────────────────────────────────────────────────────
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💬 Back to Chat", use_container_width=True, key="ins_back"):
            st.session_state.app_mode = "chat"; st.rerun()
    with c2:
        if st.button("🔄 Refresh Analysis", use_container_width=True, key="ins_refresh"):
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.rerun()
    with c3:
        if st.button("🍅 Focus Session", use_container_width=True, key="ins_pomo"):
            st.session_state.app_mode = "pomodoro"; st.rerun()
