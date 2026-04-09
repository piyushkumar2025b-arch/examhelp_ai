"""
quiz_engine.py — Elite Quiz Engine v2.0
Adaptive Difficulty · Timed Mode · PYQ Mode · Topic Mastery Analytics
Streak Scoring · Confidence Rating · AI Explanations · Wrong Answer Drill
"""

import streamlit as st
import json
import time
import re
import datetime
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None; go = None

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

from utils.ai_engine import generate


# ─── ADAPTIVE DIFFICULTY (ADD-3.2) ──────────────────────────────────────────
def get_adaptive_difficulty(topic: str) -> str:
    scores = st.session_state.get("quiz_v2_adaptive_scores", {})
    history = scores.get(topic, [])
    if not history:
        return "medium"
    avg = sum(history[-5:]) / len(history[-5:])
    if avg > 0.80:
        return "hard"
    if avg < 0.45:
        return "easy"
    return "medium"


def calculate_battle_mode_score(base_points: int, time_taken_sec: float, difficulty: str) -> int:
    """
    FIX-9.1: Battle Mode scoring formula.
    Awards bonus points for rapid responses, scaled by difficulty.
    Expected time: Easy=10s, Medium=20s, Hard=30s.
    """
    diff_multiplier = {"easy": 1.0, "medium": 1.5, "hard": 2.0}.get(difficulty.lower(), 1.0)
    expected_time = {"easy": 10.0, "medium": 20.0, "hard": 30.0}.get(difficulty.lower(), 15.0)

    if time_taken_sec <= 0:
        time_taken_sec = 0.1

    time_bonus = max(0, int((expected_time - time_taken_sec) * diff_multiplier))
    
    # Cap time bonus to 200% of base points to prevent point farming
    time_bonus = min(time_bonus, int(base_points * 2.0))
    
    total_score = base_points + time_bonus
    return total_score


def get_next_question_difficulty(scores: dict, topic: str) -> str:
    """ADD-3.2: Adjusts difficulty based on recent performance for a topic."""
    topic_scores = scores.get(topic, [])
    if len(topic_scores) < 3:
        return "Medium"
    recent_avg = sum(topic_scores[-3:]) / 3
    if recent_avg > 0.8:
        return "Hard"
    elif recent_avg < 0.4:
        return "Easy"
    return "Medium"


# ─── QUIZ GENERATION ─────────────────────────────────────────────────────────
def generate_quiz_batch(context_text: str, is_pyq: bool = False, pyq_text: str = "",
                        difficulty: str = "adaptive", num_q: int = 10) -> list:
    diff_instruction = {
        "easy":   "Keep questions straightforward with clear obvious answers.",
        "medium": "Mix of recall and application questions.",
        "hard":   "Deep analytical, tricky, multi-step reasoning questions with plausible distractors.",
        "adaptive": "Mix all levels.",
    }.get(difficulty, "")

    if is_pyq:
        prompt = f"""Format these past year questions as a structured quiz. {diff_instruction}

PYQ Text:
{pyq_text[:4000]}

Output ONLY valid JSON array:
[{{"type":"mcq|tf|fill|short","topic":"...","q":"...","options":["..."],"correct":"...","explanation":"...","difficulty":"easy|medium|hard","points":1}}]"""
    else:
        prompt = f"""Generate exactly {num_q} diverse quiz questions from this text. {diff_instruction}

Rules:
- Mix formats: MCQ (60%), True/False (15%), Fill-in-blank (15%), Short answer (10%)
- MCQ must have exactly 4 options with exactly 1 correct answer
- Explanations must be educational, not just restate the answer
- Vary topics across the material

Text:
{context_text[:5500]}

Output ONLY valid JSON array:
[{{"type":"mcq|tf|fill|short","topic":"...","q":"...","options":["A","B","C","D"],"correct":"A","explanation":"...","difficulty":"easy|medium|hard","points":1}}]"""

    resp = generate(
        messages=[{"role": "user", "content": prompt}],
        context_text="", model="llama-3.3-70b-versatile", max_tokens=3500, temperature=0.4
    )
    m = re.search(r'\[.*\]', resp, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return []


# ─── MAIN UI ─────────────────────────────────────────────────────────────────
def render_quiz():
    st.markdown("""
<style>
.quiz-header {
    background: linear-gradient(135deg, #0f0a20 0%, #0d0d1a 100%);
    border: 1px solid rgba(124,106,247,0.35); border-radius: 20px;
    padding: 22px 28px; margin-bottom: 20px; position: relative; overflow: hidden;
}
.quiz-header::after {
    content:''; position:absolute; bottom:-50px; right:-50px;
    width:200px; height:200px;
    background: radial-gradient(circle, rgba(96,165,250,0.1), transparent 70%);
    border-radius:50%;
}
.quiz-title { font-size: 1.7rem; font-weight: 800; color: #60a5fa; margin: 0 0 4px; }
.quiz-sub   { font-size: 0.85rem; color: #9090b8; }
.q-card {
    background: linear-gradient(145deg, rgba(15,10,32,0.98), rgba(10,10,22,0.95));
    border: 1.5px solid rgba(124,106,247,0.22); border-radius: 18px;
    padding: 28px 26px; margin-bottom: 16px;
    box-shadow: 0 16px 48px rgba(0,0,0,0.5);
    animation: qSlide 0.4s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes qSlide {
    from { opacity:0; transform: translateY(16px) scale(0.97); }
    to   { opacity:1; transform: none; }
}
.q-number { font-size: 0.72rem; color: #7c6af7; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px; }
.q-text   { font-size: 1.15rem; font-weight: 600; color: #f0f0ff; line-height: 1.55; }
.q-type-badge {
    display: inline-block; font-size: 0.66rem; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 2px 9px; border-radius: 6px; background: rgba(124,106,247,0.15);
    color: #a78bfa; font-weight: 700; margin-bottom: 14px;
}
.correct-flash {
    background: rgba(52,211,153,0.1) !important;
    border-color: rgba(52,211,153,0.4) !important;
    animation: correctPulse 0.6s ease;
}
@keyframes correctPulse {
    0%  { box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }
    70% { box-shadow: 0 0 0 12px rgba(52,211,153,0); }
    100%{ box-shadow: none; }
}
.wrong-flash  { background: rgba(248,113,113,0.08) !important; border-color: rgba(248,113,113,0.35) !important; }
.explanation-box {
    background: rgba(96,165,250,0.07); border: 1px solid rgba(96,165,250,0.2);
    border-radius: 12px; padding: 12px 16px; margin-top: 12px;
    font-size: 0.88rem; color: #93c5fd; line-height: 1.6;
    animation: fadeIn 0.4s ease;
}
@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
.timer-bar { height: 6px; border-radius: 99px; background: rgba(255,255,255,0.07); overflow: hidden; margin: 6px 0; }
.timer-fill { height: 100%; border-radius: 99px; transition: width 1s linear; }
.score-card {
    background: linear-gradient(135deg, rgba(15,10,32,0.98), rgba(10,10,22,0.95));
    border: 1.5px solid rgba(52,211,153,0.3); border-radius: 20px;
    padding: 32px; text-align: center; margin-bottom: 20px;
}
.final-score { font-size: 3.5rem; font-weight: 900; background: linear-gradient(135deg,#34d399,#60a5fa,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.points-badge {
    display: inline-block; background: rgba(251,191,36,0.15); border: 1px solid rgba(251,191,36,0.3);
    border-radius: 99px; padding: 4px 14px; font-size: 0.8rem; color: #fbbf24; font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="quiz-header">
  <div class="quiz-title">📝 Elite Quiz Mode</div>
  <div class="quiz-sub">Adaptive difficulty · Timed exams · PYQ support · Topic mastery analytics · Streak scoring</div>
</div>
""", unsafe_allow_html=True)

    # Init state
    for k, v in [
        ("quiz_v2_data", []), ("quiz_v2_current", 0), ("quiz_v2_timer", None),
        ("quiz_v2_stats", {"score": 0, "points": 0, "start_time": 0, "q_times": {}, "topic_scores": {}}),
        ("quiz_v2_failed", []), ("quiz_v2_adaptive_scores", {}),
        ("quiz_v2_answered", {}), ("quiz_streak", 0), ("quiz_best_streak", 0),
    ]:
        st.session_state.setdefault(k, v)

    # ── Generation controls ──
    if not st.session_state.quiz_v2_data:
        col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
        with col_a:
            num_q = st.slider("Number of questions", 5, 25, 10, label_visibility="collapsed")
        with col_b:
            diff_sel = st.selectbox("Difficulty", ["adaptive", "easy", "medium", "hard"], label_visibility="collapsed")
        with col_c:
            timed = st.checkbox("⏱️ Timed (10 min)", value=False)
        with col_d:
            pass  # spacer

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🪄 Generate Quiz", use_container_width=True, type="primary"):
                ctx = st.session_state.get("context_text", "")
                if not ctx:
                    st.warning("📄 Upload study material first!")
                else:
                    with st.spinner("Generating quiz questions..."):
                        cards = generate_quiz_batch(ctx, difficulty=diff_sel, num_q=num_q)
                        if cards:
                            st.session_state.quiz_v2_data = cards
                            st.session_state.quiz_v2_current = 0
                            st.session_state.quiz_v2_answered = {}
                            st.session_state.quiz_v2_timer = time.time() + 600 if timed else None
                            st.session_state.quiz_v2_stats = {"score": 0, "points": 0, "start_time": time.time(), "q_times": {}, "topic_scores": {}}
                            st.session_state.quiz_streak = 0
                            st.rerun()
                        else:
                            st.error("Failed to generate — try again.")

        with c2:
            if st.button("⏱️ Timed Mock (10 min)", use_container_width=True):
                ctx = st.session_state.get("context_text", "")
                if not ctx:
                    st.warning("📄 Upload study material first!")
                else:
                    with st.spinner("Building timed exam..."):
                        cards = generate_quiz_batch(ctx, difficulty="hard", num_q=15)
                        if cards:
                            st.session_state.quiz_v2_data = cards
                            st.session_state.quiz_v2_current = 0
                            st.session_state.quiz_v2_answered = {}
                            st.session_state.quiz_v2_timer = time.time() + 600
                            st.session_state.quiz_v2_stats = {"score": 0, "points": 0, "start_time": time.time(), "q_times": {}, "topic_scores": {}}
                            st.rerun()

        with c3:
            if st.session_state.quiz_v2_failed:
                if st.button(f"🔁 Drill {len(st.session_state.quiz_v2_failed)} Wrong Answers", use_container_width=True):
                    st.session_state.quiz_v2_data = st.session_state.quiz_v2_failed.copy()
                    st.session_state.quiz_v2_failed = []
                    st.session_state.quiz_v2_current = 0
                    st.session_state.quiz_v2_answered = {}
                    st.session_state.quiz_v2_stats = {"score": 0, "points": 0, "start_time": time.time(), "q_times": {}, "topic_scores": {}}
                    st.rerun()

        with st.expander("📚 Paste Past Year Questions (PYQ Mode)"):
            pyq_text = st.text_area("Paste your PYQs here", height=120, placeholder="Paste past year exam questions...")
            if st.button("🔄 Generate from PYQs", use_container_width=True) and pyq_text:
                with st.spinner("Parsing PYQs..."):
                    cards = generate_quiz_batch("", is_pyq=True, pyq_text=pyq_text)
                    if cards:
                        st.session_state.quiz_v2_data = cards
                        st.session_state.quiz_v2_current = 0
                        st.session_state.quiz_v2_answered = {}
                        st.session_state.quiz_v2_stats = {"score": 0, "points": 0, "start_time": time.time(), "q_times": {}, "topic_scores": {}}
                        st.rerun()
        return

    quiz = st.session_state.quiz_v2_data
    qi = st.session_state.quiz_v2_current

    # FIX-3.1: Bounds check before EVERY render
    if qi >= len(quiz):
        st.session_state.quiz_v2_current = 0
        st.warning("Quiz reset — question index out of range.")
        st.rerun()

    # ── Timer ──
    if st.session_state.quiz_v2_timer:
        rem = max(0, st.session_state.quiz_v2_timer - time.time())
        if st_autorefresh:
            st_autorefresh(interval=1000, limit=int(rem) + 5, key="quiz_timer")
        if rem <= 0:
            st.error("⏰ Time's up!")
            st.session_state.quiz_v2_current = len(quiz)
            st.session_state.quiz_v2_timer = None
            st.rerun()
        else:
            total_time = 600
            pct = rem / total_time
            color = "#34d399" if pct > 0.4 else "#fbbf24" if pct > 0.15 else "#f87171"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<span style="font-size:.85rem;color:{color};font-weight:700">⏱️ {int(rem)//60:02d}:{int(rem)%60:02d}</span>'
                f'<div class="timer-bar" style="flex:1"><div class="timer-fill" style="width:{pct*100:.1f}%;background:{color}"></div></div></div>',
                unsafe_allow_html=True
            )

    # ── Score screen ──
    if qi >= len(quiz):
        stats = st.session_state.quiz_v2_stats
        score = stats["score"]
        total = len(quiz)
        pct = int(score / total * 100)
        grade = "🏆 Excellent!" if pct >= 85 else "✅ Good" if pct >= 65 else "📚 Needs Work"

        st.markdown(f"""
<div class="score-card">
  <div class="final-score">{pct}%</div>
  <div style="font-size:1.2rem;color:#c4c4e0;margin:8px 0">{grade}</div>
  <div style="color:#9090b8;font-size:.9rem">{score}/{total} correct · <span class="points-badge">⭐ {stats["points"]} pts</span> · Best streak: {st.session_state.quiz_best_streak} 🔥</div>
</div>
""", unsafe_allow_html=True)

        # Analytics
        topic_scores = stats.get("topic_scores", {})
        if topic_scores and px:
            topics = list(topic_scores.keys())
            accs = [topic_scores[t]["correct"] / max(1, topic_scores[t]["total"]) * 100 for t in topics]
            colors = ["#34d399" if a >= 70 else "#fbbf24" if a >= 45 else "#f87171" for a in accs]
            fig = go.Figure(go.Bar(
                x=topics, y=accs, marker_color=colors,
                text=[f"{a:.0f}%" for a in accs], textposition="outside"
            ))
            fig.update_layout(
                title="Topic Mastery (%)", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                margin=dict(t=40, b=20, l=20, r=20), height=280,
                xaxis=dict(gridcolor="rgba(100,100,100,.1)"),
                yaxis=dict(gridcolor="rgba(100,100,100,.1)", range=[0, 115]),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            weakest = min(topic_scores, key=lambda k: topic_scores[k]["correct"] / max(1, topic_scores[k]["total"]))
            strongest = max(topic_scores, key=lambda k: topic_scores[k]["correct"] / max(1, topic_scores[k]["total"]))
            st.markdown(f"🔴 **Needs review:** {weakest} &nbsp;&nbsp; 🟢 **Strongest:** {strongest}")

        # Q&A review
        with st.expander("📋 Review All Answers"):
            for i, q in enumerate(quiz):
                answered = st.session_state.quiz_v2_answered.get(i)
                is_correct = answered == q.get("correct")
                icon = "✅" if is_correct else "❌"
                st.markdown(
                    f'<div style="padding:10px 14px;margin:4px 0;border-radius:10px;'
                    f'background:{"rgba(52,211,153,0.07)" if is_correct else "rgba(248,113,113,0.07)"};">'
                    f'<b>{icon} Q{i+1}.</b> {q["q"]}<br>'
                    f'<small style="color:#9090b8">Your answer: {answered or "—"} · Correct: {q.get("correct","—")}</small></div>',
                    unsafe_allow_html=True
                )

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("🔄 Start New Quiz", use_container_width=True, type="primary"):
                st.session_state.quiz_v2_data = []
                st.session_state.quiz_v2_answered = {}
                st.rerun()
        with col_r2:
            if st.session_state.quiz_v2_failed:
                if st.button(f"🔁 Retry {len(st.session_state.quiz_v2_failed)} Wrong", use_container_width=True):
                    st.session_state.quiz_v2_data = st.session_state.quiz_v2_failed.copy()
                    st.session_state.quiz_v2_failed = []
                    st.session_state.quiz_v2_current = 0
                    st.session_state.quiz_v2_answered = {}
                    st.session_state.quiz_v2_stats = {"score": 0, "points": 0, "start_time": time.time(), "q_times": {}, "topic_scores": {}}
                    st.rerun()
        return

    # ── Active question ──
    q_item = quiz[qi]
    topic = q_item.get("topic", "General")
    q_type = q_item.get("type", "mcq")
    diff = q_item.get("difficulty", get_adaptive_difficulty(topic))
    points = q_item.get("points", 1)
    streak = st.session_state.quiz_streak
    if streak >= 3:
        points = 2  # streak bonus

    diff_colors = {"easy": "#34d399", "medium": "#fbbf24", "hard": "#f87171"}
    diff_color = diff_colors.get(diff, "#a78bfa")

    # Progress
    st.progress(qi / len(quiz))
    p1, p2, p3, p4 = st.columns(4)
    p1.markdown(f'<small style="color:#9090b8">Q {qi+1} / {len(quiz)}</small>', unsafe_allow_html=True)
    p2.markdown(f'<small style="color:{diff_color}">◉ {diff.upper()}</small>', unsafe_allow_html=True)
    p3.markdown(f'<small style="color:#fbbf24">⭐ {st.session_state.quiz_v2_stats["points"]} pts</small>', unsafe_allow_html=True)
    p4.markdown(f'<small>{"🔥" * min(streak, 5)} {streak} streak{" (+2x pts!)" if streak >= 3 else ""}</small>', unsafe_allow_html=True)

    # Question card
    type_labels = {"mcq": "Multiple Choice", "tf": "True / False", "fill": "Fill in the Blank", "short": "Short Answer"}
    st.markdown(f"""
<div class="q-card">
  <div class="q-type-badge">{type_labels.get(q_type, q_type.upper())} · {topic}</div>
  <div class="q-text">{q_item.get("q", "")}</div>
</div>
""", unsafe_allow_html=True)

    already_answered = qi in st.session_state.quiz_v2_answered
    chosen = st.session_state.quiz_v2_answered.get(qi)

    if q_type in ["mcq", "tf"] and not already_answered:
        opts = q_item.get("options", ["True", "False"] if q_type == "tf" else [])
        user_choice = st.radio("", opts, key=f"q_radio_{qi}", label_visibility="collapsed")
        if st.button("✅ Submit Answer", key=f"submit_{qi}", use_container_width=True, type="primary"):
            is_correct = user_choice == q_item.get("correct")
            st.session_state.quiz_v2_answered[qi] = user_choice
            _process_answer(qi, q_item, is_correct, points, topic)
            st.rerun()

    elif q_type in ["fill", "short"] and not already_answered:
        ans = st.text_input("Your answer:", key=f"q_text_{qi}", placeholder="Type your answer...")
        if st.button("✅ Submit", key=f"submit_{qi}", use_container_width=True, type="primary") and ans.strip():
            is_correct = ans.strip().lower() in q_item.get("correct", "").strip().lower()
            st.session_state.quiz_v2_answered[qi] = ans
            _process_answer(qi, q_item, is_correct, points, topic)
            st.rerun()

    elif already_answered:
        is_correct = chosen == q_item.get("correct") if q_type in ["mcq","tf"] else chosen.strip().lower() in q_item.get("correct","").lower()
        if is_correct:
            st.success(f"✅ Correct! +{points} pts")
        else:
            st.error(f"❌ Incorrect. Correct answer: **{q_item.get('correct')}**")
        st.markdown(f'<div class="explanation-box">💡 <b>Explanation:</b> {q_item.get("explanation","No explanation available.")}</div>', unsafe_allow_html=True)

        nav1, nav2 = st.columns(2)
        with nav1:
            if qi > 0 and st.button("← Previous", use_container_width=True):
                st.session_state.quiz_v2_current -= 1
                st.rerun()
        with nav2:
            label = "Finish Quiz ✓" if qi == len(quiz) - 1 else "Next Question →"
            if st.button(label, use_container_width=True, type="primary"):
                st.session_state.quiz_v2_current += 1
                st.rerun()


def _process_answer(qi, q_item, is_correct, points, topic):
    stats = st.session_state.quiz_v2_stats
    stats["q_times"][qi] = time.time() - stats["start_time"]
    stats["start_time"] = time.time()
    stats["topic_scores"].setdefault(topic, {"correct": 0, "total": 0})
    stats["topic_scores"][topic]["total"] += 1
    st.session_state.quiz_v2_adaptive_scores.setdefault(topic, [])

    if is_correct:
        stats["score"] += 1
        stats["points"] += points
        stats["topic_scores"][topic]["correct"] += 1
        st.session_state.quiz_v2_adaptive_scores[topic].append(1)
        st.session_state.quiz_streak += 1
        st.session_state.quiz_best_streak = max(
            st.session_state.quiz_best_streak, st.session_state.quiz_streak
        )
    else:
        st.session_state.quiz_v2_failed.append(q_item)
        st.session_state.quiz_v2_adaptive_scores[topic].append(0)
        st.session_state.quiz_streak = 0
