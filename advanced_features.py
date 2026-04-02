"""
advanced_features.py — ExamHelp v5.0 Power Upgrades
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Supercharges every existing feature WITHOUT overwriting original code.

• Flashcards     → Battle Mode, AI Tutor chat, Export deck, Mastery heatmap
• Quiz           → Live leaderboard, Multi-player, Detailed analytics, PDF report
• Essay Writer   → Plagiarism style-check, Turnitin-style readability score, Co-write AI
• Debugger       → Live diff viewer, Complexity analyzer, Security audit, Test generator
• Interview      → Video script, Company research, Salary benchmark, Mock AI interviewer
• Research       → Multi-source synthesis, Citation graph, Gap analysis, PDF export
• Presentation   → AI image gen per slide, Speaker coach, Slide critique
• Shopping       → Price history chart, Wishlist comparison, Deal alert
• Language Tools → Pronunciation guide, Dialect detector, Cultural notes
• Chat Powerup   → Emotion-aware mode, Multi-persona debate, Concept mapper
• Citation       → Full 7-style generator (not "coming soon")
• Regex          → Live tester with match highlighting (not "coming soon")
• VIT Academics  → CGPA calculator, Credit planner, Faculty finder (not "coming soon")
• Study Toolkit  → Pomodoro + focus music + progress bar (not "coming soon")
"""

from __future__ import annotations
import streamlit as st
import json
import re
import time
import datetime
import random
import math

try:
    from utils.ai_engine import generate
except ImportError:
    def generate(messages=None, context_text="", model="", max_tokens=1000, temperature=0.7, prompt="", **kwargs):
        return "AI response unavailable."


# ══════════════════════════════════════════════════════════════════════════════
# SHARED CSS (injected once)
# ══════════════════════════════════════════════════════════════════════════════

def _inject_power_css():
    st.markdown("""
<style>
/* Power feature header */
.pf-header{background:linear-gradient(135deg,#0d0520 0%,#050010 100%);
  border:1px solid rgba(167,139,250,0.4);border-radius:18px;
  padding:26px 30px;margin-bottom:18px;position:relative;overflow:hidden;}
.pf-header::after{content:'';position:absolute;top:-60px;right:-60px;
  width:220px;height:220px;
  background:radial-gradient(circle,rgba(167,139,250,0.15),transparent 70%);border-radius:50%;}
.pf-title{font-size:1.9rem;font-weight:900;
  background:linear-gradient(135deg,#a78bfa,#60a5fa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0 0 4px;}
.pf-sub{font-size:.85rem;color:#9090b8;}
/* Power badge */
.power-badge{display:inline-flex;align-items:center;gap:4px;
  background:linear-gradient(135deg,rgba(167,139,250,.15),rgba(96,165,250,.08));
  border:1px solid rgba(167,139,250,.3);border-radius:99px;
  padding:3px 10px;font-size:.7rem;color:#a78bfa;font-weight:700;
  letter-spacing:.04em;margin-left:8px;}
/* Score card */
.score-card{background:rgba(14,14,26,.85);border:1px solid rgba(124,106,247,.25);
  border-radius:14px;padding:16px;text-align:center;transition:all .2s;}
.score-card:hover{border-color:rgba(124,106,247,.6);transform:translateY(-2px);}
.score-val{font-size:2rem;font-weight:900;color:#a78bfa;}
.score-lbl{font-size:.75rem;color:#9090b8;margin-top:2px;}
/* Stat row */
.stat-row{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0;}
/* Match highlight */
.rx-match{background:rgba(250,204,21,.25);border:1px solid rgba(250,204,21,.5);
  border-radius:3px;padding:0 2px;color:#fcd34d;}
/* Pomodoro */
.pomo-ring{font-size:4rem;font-weight:900;color:#a78bfa;text-align:center;line-height:1;}
/* Citation box */
.cit-box{background:rgba(14,14,26,.7);border-left:3px solid #a78bfa;
  border-radius:0 10px 10px 0;padding:14px 16px;margin:10px 0;
  font-family:Georgia,serif;font-size:.88rem;line-height:1.7;color:#d0d0f0;}
/* Battle card */
.battle-card{background:linear-gradient(135deg,rgba(124,106,247,.12),rgba(96,165,250,.06));
  border:1px solid rgba(124,106,247,.3);border-radius:16px;
  padding:20px;margin:10px 0;text-align:center;}
.battle-q{font-size:1.1rem;font-weight:700;color:#e0e0ff;margin-bottom:12px;}
/* Timeline */
.tl-item{border-left:2px solid rgba(167,139,250,.4);padding-left:16px;margin:12px 0;}
.tl-dot{width:10px;height:10px;background:#a78bfa;border-radius:50%;
  display:inline-block;margin-left:-21px;vertical-align:middle;margin-right:8px;}
/* Salary bar */
.sal-bar-wrap{background:rgba(255,255,255,.06);border-radius:99px;height:10px;
  margin:6px 0;overflow:hidden;}
.sal-bar{height:100%;border-radius:99px;
  background:linear-gradient(90deg,#7c6af7,#60a5fa);}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FLASHCARD POWER UPGRADE: BATTLE MODE + AI TUTOR + EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def render_flashcard_battle_mode():
    """Battle mode for flashcards: fast-paced timed quiz."""
    _inject_power_css()
    cards = st.session_state.get("flashcards", [])
    if not cards:
        st.warning("⚠️ Generate flashcards first in the Flashcards tab!")
        return

    st.markdown("""
<div class="pf-header">
  <div class="pf-title">⚡ Battle Mode <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Type the answer before the timer runs out — every second counts!</div>
</div>""", unsafe_allow_html=True)

    if "battle_idx" not in st.session_state:
        st.session_state.battle_idx = 0
        st.session_state.battle_score = 0
        st.session_state.battle_total = 0
        st.session_state.battle_streak = 0
        st.session_state.battle_best_streak = 0
        st.session_state.battle_start = time.time()
        st.session_state.battle_q_start = time.time()
        random.shuffle(cards)

    idx = st.session_state.battle_idx
    if idx >= len(cards):
        # Results screen
        elapsed = time.time() - st.session_state.battle_start
        acc = (st.session_state.battle_score / max(st.session_state.battle_total, 1)) * 100
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="score-card"><div class="score-val">{st.session_state.battle_score}/{st.session_state.battle_total}</div><div class="score-lbl">Score</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="score-card"><div class="score-val">{acc:.0f}%</div><div class="score-lbl">Accuracy</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="score-card"><div class="score-val">{st.session_state.battle_best_streak}🔥</div><div class="score-lbl">Best Streak</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="score-card"><div class="score-val">{elapsed:.0f}s</div><div class="score-lbl">Time</div></div>', unsafe_allow_html=True)
        st.balloons()
        if st.button("🔄 Play Again", type="primary", use_container_width=True, key="battle_again"):
            for k in ["battle_idx","battle_score","battle_total","battle_streak","battle_best_streak","battle_start","battle_q_start"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()
        return

    card = cards[idx]
    q_elapsed = time.time() - st.session_state.battle_q_start
    time_limit = 30
    remaining = max(0, time_limit - q_elapsed)
    progress_val = remaining / time_limit

    st.progress(progress_val, text=f"⏱️ {remaining:.0f}s remaining | Card {idx+1}/{len(cards)} | Score: {st.session_state.battle_score} | Streak: {st.session_state.battle_streak}🔥")

    st.markdown(f"""
<div class="battle-card">
  <div style="font-size:.75rem;color:#a78bfa;margin-bottom:8px;">
    {card.get('topic','')}{' · ' + card.get('difficulty','') if card.get('difficulty') else ''}
  </div>
  <div class="battle-q">❓ {card.get('q','')}</div>
  {f'<div style="font-size:.8rem;color:#9090b8;">💡 Hint: {card.get("hint","")}</div>' if card.get('hint') else ''}
</div>""", unsafe_allow_html=True)

    answer_input = st.text_input("Your answer:", key=f"battle_ans_{idx}", placeholder="Type fast...")
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        if st.button("✅ Submit", type="primary", use_container_width=True, key=f"battle_sub_{idx}"):
            correct_answer = card.get("a", "").lower().strip()
            user_answer = answer_input.lower().strip()
            keywords = [w for w in correct_answer.split() if len(w) > 3]
            matched = sum(1 for k in keywords if k in user_answer)
            is_correct = matched >= max(1, len(keywords) * 0.5)
            st.session_state.battle_total += 1
            if is_correct:
                st.session_state.battle_score += 1
                st.session_state.battle_streak += 1
                st.session_state.battle_best_streak = max(st.session_state.battle_streak, st.session_state.battle_best_streak)
                st.success(f"✅ Correct! {card.get('a','')}")
            else:
                st.session_state.battle_streak = 0
                st.error(f"❌ Answer: {card.get('a','')}")
            time.sleep(1.2)
            st.session_state.battle_idx += 1
            st.session_state.battle_q_start = time.time()
            st.rerun()
    with col2:
        if st.button("⏭️ Skip", use_container_width=True, key=f"battle_skip_{idx}"):
            st.session_state.battle_total += 1
            st.session_state.battle_streak = 0
            st.session_state.battle_idx += 1
            st.session_state.battle_q_start = time.time()
            st.rerun()
    with col3:
        if remaining <= 0:
            st.warning("⏰ Time's up!")
            if st.button("Next →", use_container_width=True, key=f"battle_to_{idx}"):
                st.session_state.battle_total += 1
                st.session_state.battle_streak = 0
                st.session_state.battle_idx += 1
                st.session_state.battle_q_start = time.time()
                st.rerun()


def render_flashcard_ai_tutor():
    """Chat with AI about any flashcard topic."""
    _inject_power_css()
    cards = st.session_state.get("flashcards", [])

    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🧠 AI Tutor Chat <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Ask the AI tutor anything about your flashcard topics — deep explanations, examples, analogies.</div>
</div>""", unsafe_allow_html=True)

    if "tutor_messages" not in st.session_state:
        st.session_state.tutor_messages = []

    topics = list({c.get("topic", "General") for c in cards}) if cards else []
    selected_topic = st.selectbox("Focus on topic:", ["All topics"] + topics, key="tutor_topic")

    for msg in st.session_state.tutor_messages:
        icon = "🧑‍🎓" if msg["role"] == "user" else "🎓"
        with st.chat_message(msg["role"]):
            st.markdown(f"{icon} {msg['content']}")

    user_q = st.chat_input("Ask your AI tutor anything...")
    if user_q:
        st.session_state.tutor_messages.append({"role": "user", "content": user_q})
        context = ""
        if cards and selected_topic != "All topics":
            relevant = [c for c in cards if c.get("topic") == selected_topic]
            context = "\n".join([f"Q: {c['q']}\nA: {c['a']}" for c in relevant[:5]])
        elif cards:
            context = "\n".join([f"Q: {c['q']}\nA: {c['a']}" for c in cards[:8]])

        history = st.session_state.tutor_messages[-8:]
        prompt = f"""You are an expert tutor. The student is studying these flashcard topics.
Flashcard context:
{context}

Answer the student's question with clear explanations, examples, and analogies. Be encouraging.
Question: {user_q}"""
        with st.spinner("Tutor thinking..."):
            response = generate(
                messages=[{"role": "user", "content": prompt}],
                context_text="", model="llama-3.3-70b-versatile", max_tokens=700, temperature=0.5
            )
        st.session_state.tutor_messages.append({"role": "assistant", "content": response})
        st.rerun()

    if st.session_state.tutor_messages:
        if st.button("🗑️ Clear Chat", key="tutor_clear"):
            st.session_state.tutor_messages = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# QUIZ POWER UPGRADE: ANALYTICS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def render_quiz_analytics():
    """Advanced analytics for quiz performance."""
    _inject_power_css()
    scores = st.session_state.get("quiz_v2_adaptive_scores", {})
    quiz_data = st.session_state.get("quiz_v2_data", [])

    st.markdown("""
<div class="pf-header">
  <div class="pf-title">📊 Quiz Analytics <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Topic mastery heatmap · Performance trends · Weak area drill</div>
</div>""", unsafe_allow_html=True)

    if not scores and not quiz_data:
        st.info("📝 Complete at least one quiz to see your analytics.")
        return

    # Overall stats
    if scores:
        all_scores = [s for topic_scores in scores.values() for s in topic_scores]
        if all_scores:
            avg = sum(all_scores) / len(all_scores)
            total_questions = len(all_scores)
            best_topic = max(scores, key=lambda t: sum(scores[t]) / len(scores[t])) if scores else "N/A"
            worst_topic = min(scores, key=lambda t: sum(scores[t]) / len(scores[t])) if scores else "N/A"

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="score-card"><div class="score-val">{avg*100:.0f}%</div><div class="score-lbl">Overall Accuracy</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="score-card"><div class="score-val">{total_questions}</div><div class="score-lbl">Questions Answered</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="score-card"><div class="score-val">🏆</div><div class="score-lbl">Best: {best_topic[:15]}</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="score-card"><div class="score-val">⚠️</div><div class="score-lbl">Weak: {worst_topic[:15]}</div></div>', unsafe_allow_html=True)

            st.markdown("### 📈 Topic Mastery")
            for topic, topic_scores in sorted(scores.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True):
                topic_avg = sum(topic_scores) / len(topic_scores)
                color = "#4ade80" if topic_avg > 0.75 else "#facc15" if topic_avg > 0.45 else "#f87171"
                bar_width = int(topic_avg * 100)
                st.markdown(f"""
<div style="margin:6px 0;">
  <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:3px;">
    <span style="color:#e0e0ff;">{topic}</span>
    <span style="color:{color};font-weight:700;">{topic_avg*100:.0f}%  ({len(topic_scores)} attempts)</span>
  </div>
  <div class="sal-bar-wrap"><div class="sal-bar" style="width:{bar_width}%;background:{color};"></div></div>
</div>""", unsafe_allow_html=True)

    st.markdown("### 🎯 AI Study Recommendations")
    if st.button("Generate Personalized Study Plan", type="primary", key="quiz_study_plan"):
        weak_areas = [t for t, s in scores.items() if sum(s)/len(s) < 0.6] if scores else []
        prompt = f"""Based on quiz performance:
Weak topics (below 60%): {', '.join(weak_areas) if weak_areas else 'None identified yet'}
Total questions answered: {len([s for ts in scores.values() for s in ts]) if scores else 0}

Create a concise, actionable 7-day study plan to improve performance. Include:
1. Daily focus topics
2. Specific techniques for weak areas
3. Practice strategies
4. Estimated time per day

Keep it motivating and practical."""
        with st.spinner("Creating your personalized study plan..."):
            plan = generate(
                messages=[{"role": "user", "content": prompt}],
                context_text="", model="llama-3.3-70b-versatile", max_tokens=800
            )
            st.markdown(plan)


# ══════════════════════════════════════════════════════════════════════════════
# ESSAY POWER UPGRADE: READABILITY SCORER + CO-WRITE AI
# ══════════════════════════════════════════════════════════════════════════════

def render_essay_power_tools():
    """Advanced essay analysis: readability, style, co-write AI."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">✍️ Essay Power Tools <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Readability scorer · Style analyzer · Co-write AI · Argument mapper</div>
</div>""", unsafe_allow_html=True)

    tab_score, tab_cowrite, tab_improve = st.tabs(["📊 Score & Analyze", "🤝 Co-Write AI", "🚀 Instant Improve"])

    with tab_score:
        essay_text = st.text_area("Paste your essay:", height=250, key="ep_essay_text",
                                   placeholder="Paste any essay or paragraph for instant analysis...")
        if essay_text and st.button("📊 Analyze Essay", type="primary", key="ep_analyze"):
            # Basic metrics
            words = essay_text.split()
            sentences = re.split(r'[.!?]+', essay_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
            avg_words_per_sentence = len(words) / max(len(sentences), 1)

            # Flesch Reading Ease (approximate)
            syllables = sum(max(1, len(re.findall(r'[aeiouAEIOU]', w))) for w in words)
            if len(sentences) > 0 and len(words) > 0:
                flesch = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syllables / len(words))
                flesch = max(0, min(100, flesch))
            else:
                flesch = 50

            grade_level = "Graduate" if flesch < 30 else "College" if flesch < 50 else "High School" if flesch < 70 else "Middle School"

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Words", len(words))
            with c2: st.metric("Sentences", len(sentences))
            with c3: st.metric("Paragraphs", len(paragraphs))
            with c4: st.metric("Avg Words/Sentence", f"{avg_words_per_sentence:.1f}")

            st.markdown(f"""
<div class="score-card" style="margin:12px 0;">
  <div class="score-val">{flesch:.0f}/100</div>
  <div class="score-lbl">Readability Score (Flesch) · {grade_level} level</div>
</div>""", unsafe_allow_html=True)

            with st.spinner("AI analyzing your essay..."):
                prompt = f"""Analyze this essay excerpt critically. Provide:

1. **Thesis Strength** (1-10) with explanation
2. **Argument Quality** (1-10) with explanation
3. **Evidence & Support** (1-10) with explanation
4. **Flow & Transitions** (1-10) with explanation
5. **Top 3 Specific Improvements** (be precise, cite exact sentences)
6. **What's Working Well** (genuine strengths)

Essay:
{essay_text[:3000]}"""
                analysis = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                )
                st.markdown(analysis)

    with tab_cowrite:
        st.markdown("**Tell the AI what you're trying to write, and co-create together:**")
        essay_topic = st.text_input("Essay topic / thesis:", key="ep_topic")
        essay_section = st.selectbox("Section to write:", ["Introduction", "Body Paragraph", "Counter-argument", "Conclusion", "Transition sentence", "Topic sentence"], key="ep_section")
        existing = st.text_area("What you have so far (optional):", height=120, key="ep_existing")

        if essay_topic and st.button("🤝 Co-Write This Section", type="primary", key="ep_cowrite"):
            prompt = f"""You are a master essay writer collaborating with a student.

Topic/Thesis: {essay_topic}
Section needed: {essay_section}
Existing text: {existing[:1000] if existing else 'None yet'}

Write a POLISHED, ready-to-use {essay_section} that:
- Perfectly fits the existing text (if any)
- Has a strong topic sentence
- Includes concrete evidence/examples
- Flows naturally into the next section

Write ONLY the section, no meta-commentary."""
            with st.spinner(f"Co-writing {essay_section}..."):
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                )
                st.markdown(f"### ✍️ {essay_section}")
                st.markdown(result)
                st.download_button("⬇️ Copy as Text", result, file_name="essay_section.txt", key="ep_dl")

    with tab_improve:
        improve_text = st.text_area("Paste text to instantly improve:", height=200, key="ep_improve_text")
        improve_style = st.selectbox("Improve towards:", ["Academic (formal & precise)", "Persuasive (compelling & vivid)", "Concise (remove fluff)", "Creative (rich & engaging)", "Simple (clear & accessible)"], key="ep_style")
        if improve_text and st.button("🚀 Improve Now", type="primary", key="ep_improve_btn"):
            with st.spinner("Improving..."):
                prompt = f"""Improve this text to be more {improve_style.split('(')[0].strip()}.

RULES:
- Preserve ALL the original ideas and facts
- Only change wording, structure, and style
- Return ONLY the improved text, nothing else

Original:
{improve_text}"""
                improved = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=600
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original:**")
                    st.markdown(f'<div style="background:rgba(255,80,80,.08);border:1px solid rgba(255,80,80,.2);border-radius:10px;padding:12px;font-size:.88rem;">{improve_text}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown("**Improved:**")
                    st.markdown(f'<div style="background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.2);border-radius:10px;padding:12px;font-size:.88rem;">{improved}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DEBUGGER POWER UPGRADE: SECURITY AUDIT + TEST GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def render_debugger_power_tools():
    """Security audit and test generation for code."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🛡️ Code Power Tools <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Security audit · Unit test generator · Code complexity analyzer · Documentation writer</div>
</div>""", unsafe_allow_html=True)

    tab_sec, tab_test, tab_doc, tab_complex = st.tabs(["🛡️ Security Audit", "🧪 Test Generator", "📄 Doc Writer", "📈 Complexity"])

    with tab_sec:
        lang = st.selectbox("Language", ["Python", "JavaScript", "Java", "C/C++", "PHP", "Go", "Ruby"], key="sec_lang")
        code = st.text_area(f"Paste {lang} code to audit:", height=250, key="sec_code",
                             placeholder="Paste your code here for a deep security analysis...")
        if code and st.button("🛡️ Run Security Audit", type="primary", key="sec_audit"):
            with st.spinner("Security expert auditing code..."):
                prompt = f"""You are a senior security engineer (OWASP, SANS, CEH certified).

Perform a deep security audit of this {lang} code. Check for:
1. **Injection vulnerabilities** (SQL, XSS, Command injection)
2. **Authentication/Authorization flaws**
3. **Sensitive data exposure** (hardcoded credentials, API keys, PII)
4. **Insecure dependencies** or dangerous functions
5. **Logic flaws** that could be exploited
6. **Input validation** issues

For each finding:
- Severity: CRITICAL / HIGH / MEDIUM / LOW
- What is vulnerable
- How it could be exploited
- Exact fix with code

End with a **Security Score: X/10** and summary.

Code:
```{lang.lower()}
{code[:4000]}
```"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_test:
        test_lang = st.selectbox("Language", ["Python (pytest)", "JavaScript (Jest)", "Java (JUnit)", "Go (testing)", "Ruby (RSpec)"], key="test_lang")
        test_code = st.text_area("Paste function/class to test:", height=200, key="test_code")
        test_style = st.selectbox("Test style:", ["Unit tests (happy path + edge cases)", "Property-based tests", "Integration tests", "TDD (failing tests first)"], key="test_style")
        if test_code and st.button("🧪 Generate Tests", type="primary", key="gen_tests"):
            with st.spinner("Writing comprehensive tests..."):
                prompt = f"""You are a senior QA engineer. Write {test_style} for this code in {test_lang}.

Requirements:
- Test EVERY function/method
- Include: happy path, edge cases, error cases, boundary values
- Use descriptive test names (describe what each test proves)
- Include necessary mocks/stubs
- Add comments explaining WHY each test matters

Code to test:
{test_code[:3000]}

Return ONLY the complete, runnable test file."""
                tests = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1000
                )
                st.code(tests, language=test_lang.split("(")[0].strip().lower())
                st.download_button("⬇️ Download Tests", tests, file_name="test_code.py", key="test_dl")

    with tab_doc:
        doc_lang = st.selectbox("Language", ["Python", "JavaScript/TypeScript", "Java", "C/C++", "Go", "Rust"], key="doc_lang")
        doc_code = st.text_area("Paste code to document:", height=200, key="doc_code")
        doc_style = st.selectbox("Doc style:", ["Google style docstrings", "NumPy style docstrings", "JSDoc", "Javadoc", "Rustdoc", "Plain comments"], key="doc_style")
        if doc_code and st.button("📄 Generate Documentation", type="primary", key="gen_doc"):
            with st.spinner("Writing documentation..."):
                prompt = f"""Add comprehensive {doc_style} documentation to every function, class, and method in this {doc_lang} code.

Include for each:
- Purpose and behavior
- All parameters with types and descriptions
- Return value(s) with type
- Exceptions/errors raised
- Usage example (at least one)

Return the COMPLETE code with documentation added. Only return the code, nothing else.

Code:
{doc_code[:3000]}"""
                documented = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1000
                )
                st.code(documented, language=doc_lang.split("/")[0].strip().lower())
                st.download_button("⬇️ Download", documented, file_name="documented_code.py", key="doc_dl")

    with tab_complex:
        cplx_code = st.text_area("Paste code to analyze:", height=200, key="cplx_code")
        if cplx_code and st.button("📈 Analyze Complexity", type="primary", key="cplx_analyze"):
            with st.spinner("Analyzing..."):
                prompt = f"""Analyze the time and space complexity of every function in this code.

For each function:
1. **Time Complexity**: Big-O notation with explanation of the dominant operations
2. **Space Complexity**: Big-O notation with what uses the space
3. **Cyclomatic Complexity**: Estimate (1-10+ scale)
4. **Bottleneck**: Is this the slowest part?
5. **Optimization**: Specific suggestion to improve complexity (if applicable)

End with:
- **Overall Complexity Score**: Best/Average/Worst case
- **Refactor Priority**: Which functions to optimize first

Code:
{cplx_code[:3000]}"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=800
                ))


# ══════════════════════════════════════════════════════════════════════════════
# INTERVIEW POWER UPGRADE: SALARY BENCHMARK + VIDEO SCRIPT
# ══════════════════════════════════════════════════════════════════════════════

def render_interview_power_tools():
    """Salary benchmark, company research, video prep script."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">💼 Interview Power Tools <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Salary benchmarking · Company intelligence · Video script · Body language guide</div>
</div>""", unsafe_allow_html=True)

    tab_sal, tab_company, tab_script, tab_body = st.tabs(["💰 Salary Intel", "🏢 Company Research", "🎬 Video Script", "🧍 Body Language"])

    with tab_sal:
        role_name = st.text_input("Job Role:", placeholder="e.g., Senior Software Engineer, Data Scientist...", key="sal_role")
        exp_years = st.slider("Years of Experience:", 0, 25, 3, key="sal_exp")
        location = st.text_input("Location:", placeholder="e.g., Bangalore, New York, London...", key="sal_loc")
        skills = st.text_input("Key Skills:", placeholder="e.g., Python, ML, AWS, React...", key="sal_skills")

        if role_name and st.button("💰 Get Salary Intelligence", type="primary", key="sal_get"):
            with st.spinner("Researching salary data..."):
                prompt = f"""You are a compensation intelligence expert with access to industry salary data.

Provide detailed salary intelligence for:
- Role: {role_name}
- Experience: {exp_years} years
- Location: {location or 'Global'}
- Skills: {skills or 'Not specified'}

Provide:
1. **Salary Ranges** (percentile 25th / Median / 75th / 90th) in local currency
2. **Total Compensation Breakdown** (Base / Bonus / Equity / Benefits)
3. **By Company Size** (Startup / SMB / Enterprise / FAANG)
4. **Negotiation Anchors** — what to say to get the best offer
5. **Top 5 Highest-Paying Companies** for this role/location
6. **Skills that add ₹/$ Premium** and how much each is worth
7. **3 Red Flags** — offers to avoid or negotiate harder

Format numbers clearly. Be specific and data-driven."""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                )
                st.markdown(result)

    with tab_company:
        company = st.text_input("Company name:", placeholder="e.g., Google, Infosys, Zepto...", key="comp_name")
        role_at = st.text_input("Role you're interviewing for:", key="comp_role")
        if company and st.button("🏢 Research Company", type="primary", key="comp_research"):
            with st.spinner("Researching..."):
                prompt = f"""You are an expert career coach and company researcher.

Research {company} for a candidate interviewing for: {role_at or 'a position'}

Provide:
1. **Company Overview** — business model, revenue, size, stage
2. **Culture & Values** — real culture (not marketing), work-life balance, reviews
3. **Interview Process** — typical rounds, what they test, timeline
4. **Role-Specific Insights** — what this team does, tech stack, team size
5. **Key Metrics to Know** — products, competitors, recent news, growth
6. **Smart Questions to Ask** — 5 impressive questions that show you've researched them
7. **Insider Tips** — what impresses interviewers there, common mistakes

Make it specific and actionable, not generic."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_script:
        script_role = st.text_input("Role/Company:", key="script_role")
        intro_text = st.text_area("Your background (brief):", height=100, key="script_bg",
                                   placeholder="e.g., 3 years Python developer, built ML pipelines at startup, CS grad...")
        script_type = st.selectbox("Script for:", ["Tell me about yourself (2-min intro)", "Why this company?", "Greatest strength story", "Biggest weakness (honest + growth)", "Why should we hire you?"], key="script_type")
        if script_role and intro_text and st.button("🎬 Generate Script", type="primary", key="gen_script"):
            with st.spinner("Writing your interview script..."):
                prompt = f"""You are a world-class interview coach. Write a word-for-word script for: "{script_type}"

Candidate background: {intro_text}
Applying to: {script_role}

Requirements:
- Exactly 90-120 seconds when spoken aloud (roughly 200-250 words)
- Natural, confident, conversational tone (not robotic)
- Specific numbers, achievements, and examples (not vague claims)
- Strong opening hook and memorable closing
- Tailored to the role/company

Write the COMPLETE script, word for word, ready to rehearse.
Then add: KEY DELIVERY TIPS (3 bullet points on how to deliver it)."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=600
                ))

    with tab_body:
        st.markdown("### 🧍 Body Language & Delivery Guide")
        interview_type = st.selectbox("Interview format:", ["In-person", "Video call (Zoom/Meet)", "Phone screen", "Panel interview", "Technical coding interview"], key="bl_type")
        if st.button("Get Body Language Guide", type="primary", key="bl_guide"):
            prompt = f"""Create a practical, specific body language and delivery guide for a {interview_type} interview.

Include:
1. **Pre-interview** (30 min before) — physical and mental preparation
2. **During Interview** — posture, eye contact, hand gestures, voice tone, pace
3. **Common Mistakes** — what interviewers notice negatively
4. **Power Moves** — specific techniques used by top performers
5. **Nervous Habits to Avoid** — specific behaviors to eliminate
6. **Format-Specific Tips** — what matters most for {interview_type}

Be specific and actionable. Include exact techniques."""
            with st.spinner("Creating guide..."):
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                ))


# ══════════════════════════════════════════════════════════════════════════════
# FULL CITATION GENERATOR (replaces "coming soon")
# ══════════════════════════════════════════════════════════════════════════════

def render_citation_generator_v2():
    """Full-featured citation generator for 7 major styles."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">📚 Citation Generator <span class="power-badge">POWER</span></div>
  <div class="pf-sub">APA 7th · MLA 9th · Chicago · Harvard · IEEE · Vancouver · Oxford — instant perfect citations</div>
</div>""", unsafe_allow_html=True)

    tab_gen, tab_batch, tab_convert = st.tabs(["✍️ Generate Citation", "📦 Batch from URL/DOI", "🔄 Convert Style"])

    with tab_gen:
        source_type = st.selectbox("Source type:", [
            "Journal Article", "Book", "Book Chapter", "Website/Webpage",
            "Conference Paper", "Thesis/Dissertation", "Newspaper Article",
            "YouTube/Video", "Report/White Paper", "Podcast Episode"
        ], key="cit_type")

        style = st.selectbox("Citation style:", ["APA 7th", "MLA 9th", "Chicago 17th", "Harvard", "IEEE", "Vancouver", "Oxford"], key="cit_style")

        # Dynamic fields per source type
        col1, col2 = st.columns(2)
        with col1:
            authors = st.text_input("Author(s):", placeholder="Last, First; Last, First", key="cit_authors")
            year = st.text_input("Year:", placeholder="2024", key="cit_year")
            title = st.text_input("Title:", key="cit_title")
        with col2:
            if source_type == "Journal Article":
                journal = st.text_input("Journal name:", key="cit_journal")
                volume = st.text_input("Volume(Issue):", placeholder="12(3)", key="cit_vol")
                pages = st.text_input("Pages:", placeholder="45-67", key="cit_pages")
                doi = st.text_input("DOI:", placeholder="10.xxxx/xxxx", key="cit_doi")
            elif source_type in ("Book", "Book Chapter"):
                publisher = st.text_input("Publisher:", key="cit_pub")
                edition = st.text_input("Edition:", placeholder="3rd", key="cit_ed")
                if source_type == "Book Chapter":
                    editors = st.text_input("Editor(s):", key="cit_eds")
                    book_title = st.text_input("Book title:", key="cit_booktitle")
                    pages = st.text_input("Pages:", key="cit_pages2")
            elif source_type == "Website/Webpage":
                url = st.text_input("URL:", key="cit_url")
                access_date = st.text_input("Access date:", placeholder="April 2, 2026", key="cit_access")
                site_name = st.text_input("Website name:", key="cit_site")

        extra = st.text_area("Any additional info:", height=80, key="cit_extra",
                              placeholder="e.g., city of publication, database name, episode number...")

        if title and st.button("📚 Generate Citation", type="primary", key="gen_cit"):
            with st.spinner("Generating citation..."):
                prompt = f"""You are an expert academic librarian. Generate a PERFECT {style} citation.

Source type: {source_type}
Authors: {authors}
Year: {year}
Title: {title}
Additional info: {extra}
Other fields provided: {col2}

Rules:
1. Follow {style} format EXACTLY — correct punctuation, italics notation, and order
2. Generate the citation for EVERY common variation if details are incomplete
3. Flag anything missing that would make the citation incomplete
4. Show the hanging indent format (use 5 spaces for second line indent)

Output:
**{style} Citation:**
[citation here]

**In-text citation:**
[format]

**Checklist:** [any missing fields that would make it more complete]"""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=400
                )
                st.markdown('<div class="cit-box">' + result.replace('\n', '<br>') + '</div>', unsafe_allow_html=True)
                st.download_button("⬇️ Copy Citation", result, file_name="citation.txt", key="cit_dl")

    with tab_batch:
        st.markdown("**Paste URLs or DOIs (one per line) to generate multiple citations:**")
        sources = st.text_area("URLs / DOIs:", height=150, key="batch_sources",
                               placeholder="https://example.com/paper\n10.1000/journal.example\nhttps://website.com/article")
        batch_style = st.selectbox("Style:", ["APA 7th", "MLA 9th", "Chicago 17th", "Harvard", "IEEE"], key="batch_style")
        if sources and st.button("📦 Generate All Citations", type="primary", key="gen_batch"):
            source_list = [s.strip() for s in sources.strip().split('\n') if s.strip()]
            with st.spinner(f"Generating {len(source_list)} citations..."):
                prompt = f"""Generate {batch_style} citations for each of these sources.

For URLs: extract title, author, site name, and date if visible from the URL pattern.
For DOIs: use the DOI to construct the citation.
If information is unclear, state what's missing.

Sources:
{chr(10).join(source_list)}

Number each citation and provide in-text citation format too."""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                )
                st.markdown(result)
                st.download_button("⬇️ Download All", result, file_name="citations.txt", key="batch_dl")

    with tab_convert:
        st.markdown("**Convert an existing citation from one style to another:**")
        existing_cit = st.text_area("Paste existing citation:", height=120, key="conv_cit")
        from_style = st.selectbox("From style:", ["APA 7th", "MLA 9th", "Chicago 17th", "Harvard", "IEEE", "Vancouver", "Unknown"], key="conv_from_style")
        to_style = st.selectbox("To style:", ["APA 7th", "MLA 9th", "Chicago 17th", "Harvard", "IEEE", "Vancouver", "Oxford"], key="conv_to_style")
        if existing_cit and st.button("🔄 Convert Citation", type="primary", key="do_conv_cit"):
            with st.spinner("Converting..."):
                prompt = f"""Convert this {from_style} citation to {to_style} format exactly.

Original ({from_style}):
{existing_cit}

Rules:
- Extract ALL details from the original
- Reformat perfectly in {to_style}
- Correct any errors from the original along the way
- Also provide the in-text citation format

Output ONLY:
**{to_style} Citation:**
[formatted citation]

**In-text:**
[format]"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=350
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="cit_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# FULL REGEX TESTER (replaces "coming soon")
# ══════════════════════════════════════════════════════════════════════════════

def render_regex_tester_v2():
    """Full live regex tester with match highlighting and AI explain."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🔤 Regex Tester <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Live match highlighting · Group capture · AI pattern builder · Common patterns library</div>
</div>""", unsafe_allow_html=True)

    tab_test, tab_build, tab_library = st.tabs(["🧪 Live Tester", "🤖 AI Pattern Builder", "📚 Pattern Library"])

    with tab_test:
        pattern = st.text_input("Regex pattern:", placeholder=r"e.g.  \b[A-Z][a-z]+\b  or  \d{3}-\d{4}", key="rx_pattern")
        col1, col2, col3 = st.columns(3)
        with col1: flag_i = st.checkbox("Ignore case (i)", key="rx_i")
        with col2: flag_m = st.checkbox("Multiline (m)", key="rx_m")
        with col3: flag_s = st.checkbox("Dotall (s)", key="rx_s")

        test_text = st.text_area("Test text:", height=200, key="rx_text",
                                  placeholder="Paste any text to test your regex against...")

        if pattern and test_text:
            try:
                flags = 0
                if flag_i: flags |= re.IGNORECASE
                if flag_m: flags |= re.MULTILINE
                if flag_s: flags |= re.DOTALL
                compiled = re.compile(pattern, flags)
                matches = list(compiled.finditer(test_text))

                if matches:
                    st.success(f"✅ {len(matches)} match{'es' if len(matches) != 1 else ''} found")

                    # Highlight matches
                    highlighted = test_text
                    offset = 0
                    for m in matches:
                        start = m.start() + offset
                        end = m.end() + offset
                        tag_open = '<span class="rx-match">'
                        tag_close = '</span>'
                        highlighted = highlighted[:start] + tag_open + highlighted[start:end] + tag_close + highlighted[end:]
                        offset += len(tag_open) + len(tag_close)
                    st.markdown(f'<div style="background:rgba(14,14,26,.8);border:1px solid rgba(250,204,21,.2);border-radius:10px;padding:14px;font-family:monospace;font-size:.85rem;line-height:1.7;white-space:pre-wrap;">{highlighted}</div>', unsafe_allow_html=True)

                    # Show match details
                    with st.expander(f"📋 Match Details ({len(matches)} matches)"):
                        for i, m in enumerate(matches[:20]):
                            groups_str = f" · Groups: {m.groups()}" if m.groups() else ""
                            st.code(f"Match {i+1}: '{m.group()}' at [{m.start()}:{m.end()}]{groups_str}")

                    # Show captures
                    if compiled.groups > 0:
                        with st.expander("🎯 Capture Groups"):
                            for i, m in enumerate(matches[:10]):
                                for j, g in enumerate(m.groups(), 1):
                                    st.markdown(f"Match {i+1}, Group {j}: `{g}`")
                else:
                    st.warning("⚠️ No matches found")

                # Replacement
                st.markdown("---")
                replacement = st.text_input("Replace matches with:", placeholder=r"e.g.  [REDACTED]  or  \1-new", key="rx_repl")
                if replacement is not None:
                    replaced = compiled.sub(replacement, test_text)
                    st.markdown("**Result after replacement:**")
                    st.text_area("", replaced, height=120, key="rx_replaced_out")

            except re.error as e:
                st.error(f"❌ Invalid regex: {e}")

        st.markdown("---")
        if pattern and st.button("🤖 Explain This Pattern", key="rx_explain"):
            with st.spinner("Explaining..."):
                prompt = f"""Explain this regex pattern in plain English, step by step:

Pattern: `{pattern}`

Break down every token/group:
1. Explain each part with → notation
2. Give 3 example strings that MATCH
3. Give 3 example strings that DON'T MATCH
4. List any edge cases or gotchas

Keep it clear and educational."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=400
                ))

    with tab_build:
        st.markdown("**Describe what you want to match and the AI will write the regex:**")
        description = st.text_area("Describe the pattern:", height=100, key="rx_desc",
                                   placeholder="e.g., Match all email addresses\nMatch Indian phone numbers with +91 prefix\nExtract all URLs from HTML\nFind dates in DD/MM/YYYY format")
        examples = st.text_input("Example strings that should match:", placeholder="john@email.com, user.name+tag@domain.co.uk", key="rx_examples")
        language = st.selectbox("Language/flavor:", ["Python (re)", "JavaScript", "Java", "PHP", "Perl", "Ruby", "Go"], key="rx_lang")
        if description and st.button("🤖 Build Pattern", type="primary", key="build_rx"):
            with st.spinner("Building regex..."):
                prompt = f"""You are a regex expert. Build the BEST regex pattern for:

Description: {description}
Should match: {examples or 'see description'}
Language: {language}

Provide:
1. **The Pattern**: `[regex here]` (ready to copy-paste)
2. **Flags to use** (if any)
3. **How it works** (brief breakdown)
4. **Test cases**: 5 strings that match, 3 that don't
5. **Variations**: simpler vs stricter versions

Make it production-ready and well-tested."""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                )
                st.markdown(result)

    with tab_library:
        patterns = {
            "📧 Email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "📱 Phone (India)": r"(\+91[\-\s]?)?[6-9]\d{9}",
            "📱 Phone (US)": r"\+?1?\s*\(?[2-9]\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
            "🌐 URL": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:[/\w\-._~:/?#@!$&'()*+,;=%]*)?",
            "🔒 IP Address (v4)": r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
            "📅 Date DD/MM/YYYY": r"\b(0?[1-9]|[12]\d|3[01])/(0?[1-9]|1[012])/([12]\d{3})\b",
            "📅 Date YYYY-MM-DD": r"\b\d{4}-(0?[1-9]|1[012])-(0?[1-9]|[12]\d|3[01])\b",
            "💳 Credit Card": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6011[0-9]{12})\b",
            "🔑 Hex Color": r"#(?:[0-9a-fA-F]{3}){1,2}\b",
            "📮 Pincode (India)": r"\b[1-9][0-9]{5}\b",
            "💰 Currency Amount": r"₹?[$€£¥]?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?",
            "🔐 Password (Strong)": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
            "🏷️ HTML Tags": r"<([a-z][a-z0-9]*)\b[^>]*>(.*?)</\1>",
            "🔢 Integer or Float": r"-?\d+(\.\d+)?",
            "📝 Words only (no numbers)": r"\b[a-zA-Z]+\b",
        }
        for name, pat in patterns.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.code(pat, language="text")
                st.caption(name)
            with col2:
                if st.button("Use →", key=f"rx_use_{name}"):
                    st.session_state["rx_pattern"] = pat
                    st.rerun()
            st.markdown("---")

    if st.button("💬 Back to Chat", use_container_width=True, key="rx_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# VIT ACADEMICS HUB (replaces "coming soon")
# ══════════════════════════════════════════════════════════════════════════════

def render_vit_academics_v2():
    """VIT-specific CGPA calculator, slot finder, credit planner."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🎓 VIT Academics Hub <span class="power-badge">POWER</span></div>
  <div class="pf-sub">CGPA calculator · Credit planner · GPA predictor · Attendance tracker · Faculty finder</div>
</div>""", unsafe_allow_html=True)

    tab_cgpa, tab_credits, tab_att, tab_faq = st.tabs(["📊 CGPA Calculator", "📋 Credit Planner", "📅 Attendance Tracker", "❓ VIT FAQ"])

    with tab_cgpa:
        st.markdown("### 📊 CGPA / GPA Calculator")
        grade_map = {"O (91-100)": 10, "A+ (81-90)": 9, "A (71-80)": 8,
                     "B+ (61-70)": 7, "B (51-60)": 6, "C (45-50)": 5, "F (<45)": 0}

        if "vit_courses" not in st.session_state:
            st.session_state.vit_courses = [{"name": "", "credits": 4, "grade": "A (71-80)"}]

        for i, course in enumerate(st.session_state.vit_courses):
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            with col1:
                st.session_state.vit_courses[i]["name"] = st.text_input(f"Course {i+1}", value=course["name"], key=f"vit_cn_{i}", label_visibility="collapsed", placeholder=f"Course {i+1} name")
            with col2:
                st.session_state.vit_courses[i]["credits"] = st.selectbox("Credits", [1,2,3,4,5], index=[1,2,3,4,5].index(course["credits"]) if course["credits"] in [1,2,3,4,5] else 3, key=f"vit_cr_{i}", label_visibility="collapsed")
            with col3:
                st.session_state.vit_courses[i]["grade"] = st.selectbox("Grade", list(grade_map.keys()), index=list(grade_map.keys()).index(course["grade"]) if course["grade"] in grade_map else 2, key=f"vit_gr_{i}", label_visibility="collapsed")
            with col4:
                if st.button("🗑️", key=f"vit_del_{i}") and len(st.session_state.vit_courses) > 1:
                    st.session_state.vit_courses.pop(i); st.rerun()

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("➕ Add Course", use_container_width=True, key="vit_add"):
                st.session_state.vit_courses.append({"name": "", "credits": 4, "grade": "A (71-80)"}); st.rerun()
        with col_b:
            prev_cgpa = st.number_input("Previous CGPA (optional)", 0.0, 10.0, 0.0, 0.01, key="vit_prev_cgpa")

        if st.button("📊 Calculate CGPA", type="primary", use_container_width=True, key="vit_calc"):
            total_points = sum(c["credits"] * grade_map[c["grade"]] for c in st.session_state.vit_courses)
            total_credits = sum(c["credits"] for c in st.session_state.vit_courses)
            gpa = total_points / total_credits if total_credits > 0 else 0
            letter = "O" if gpa >= 9.5 else "A+" if gpa >= 8.5 else "A" if gpa >= 7.5 else "B+" if gpa >= 6.5 else "B" if gpa >= 5.5 else "C"

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="score-card"><div class="score-val">{gpa:.2f}</div><div class="score-lbl">Semester GPA</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="score-card"><div class="score-val">{total_credits}</div><div class="score-lbl">Total Credits</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="score-card"><div class="score-val">{letter}</div><div class="score-lbl">Grade</div></div>', unsafe_allow_html=True)

            if prev_cgpa > 0:
                # Weighted average (assuming prev = 20 credit-equivalent)
                combined = (prev_cgpa * 20 + gpa * total_credits) / (20 + total_credits)
                st.info(f"📈 Estimated Cumulative CGPA: **{combined:.2f}**")

    with tab_credits:
        st.markdown("### 📋 Degree Credit Planner")
        program = st.selectbox("Program:", ["B.Tech (UG)", "M.Tech (PG)", "MBA", "MCA", "BCA", "M.Sc"], key="vit_prog")
        credits_done = st.number_input("Credits completed so far:", 0, 300, 0, key="vit_cred_done")
        target_cgpa = st.number_input("Target CGPA:", 0.0, 10.0, 8.5, 0.1, key="vit_target")

        total_required = {"B.Tech (UG)": 160, "M.Tech (PG)": 66, "MBA": 96, "MCA": 90, "BCA": 120, "M.Sc": 80}.get(program, 160)
        remaining = max(0, total_required - credits_done)
        progress = credits_done / total_required

        st.progress(progress, text=f"{credits_done}/{total_required} credits ({progress*100:.1f}%)")
        st.markdown(f"**{remaining} credits remaining** to complete your {program}")

        if remaining > 0:
            semesters_left = math.ceil(remaining / 22)  # ~22 credits/semester
            st.info(f"📅 Estimated **{semesters_left} semester(s)** remaining at 22 credits/semester")

    with tab_att:
        st.markdown("### 📅 Attendance Calculator")
        total_classes = st.number_input("Total classes held:", 1, 500, 50, key="att_total")
        attended = st.number_input("Classes attended:", 0, 500, 40, key="att_attended")
        att_pct = (attended / total_classes) * 100 if total_classes > 0 else 0
        color = "#4ade80" if att_pct >= 75 else "#facc15" if att_pct >= 65 else "#f87171"

        st.markdown(f'<div class="score-card"><div class="score-val" style="color:{color};">{att_pct:.1f}%</div><div class="score-lbl">Current Attendance</div></div>', unsafe_allow_html=True)

        if att_pct < 75:
            # How many consecutive classes to reach 75%
            n = 0
            while ((attended + n) / (total_classes + n)) * 100 < 75:
                n += 1
            st.warning(f"⚠️ Below 75%! Attend next **{n} consecutive classes** to reach 75%.")
        else:
            # How many can you bunk
            max_bunk = 0
            while ((attended) / (total_classes + max_bunk + 1)) * 100 >= 75:
                max_bunk += 1
            st.success(f"✅ Safe! You can miss up to **{max_bunk} more classes** and stay above 75%.")

    with tab_faq:
        st.markdown("### ❓ VIT Academic FAQ — Ask Anything")
        vit_q = st.text_input("Your VIT academic question:", placeholder="e.g., How is CGPA calculated at VIT? What is the credit system?", key="vit_faq_q")
        if vit_q and st.button("Get Answer", type="primary", key="vit_faq_btn"):
            with st.spinner("Answering..."):
                prompt = f"""You are a VIT (Vellore Institute of Technology) academic counselor with expert knowledge of VIT's grading system, regulations, FFCS (Fully Flexible Credit System), VTOP portal, curriculum, and academic policies.

Answer this VIT student question accurately and helpfully:
{vit_q}

Include specific details about VIT policies, regulations, and systems where relevant."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="vit_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STUDY TOOLKIT (replaces "coming soon")
# ══════════════════════════════════════════════════════════════════════════════

def render_study_toolkit_v2():
    """Pomodoro timer, focus tools, mind map generator, summary maker."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🎯 Study Toolkit <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Pomodoro timer · AI mind map · Smart summarizer · Cornell notes · Study schedule generator</div>
</div>""", unsafe_allow_html=True)

    tab_pomo, tab_mindmap, tab_summarize, tab_cornell, tab_schedule = st.tabs([
        "⏱️ Pomodoro", "🗺️ Mind Map", "📝 Summarizer", "📋 Cornell Notes", "📅 Study Schedule"
    ])

    with tab_pomo:
        st.markdown("### ⏱️ Pomodoro Focus Timer")
        pomo_work = st.slider("Work session (min):", 5, 60, 25, key="pomo_work")
        pomo_break = st.slider("Break (min):", 1, 30, 5, key="pomo_break")
        pomo_cycles = st.slider("Cycles:", 1, 8, 4, key="pomo_cycles")
        subject = st.text_input("What are you studying?", placeholder="e.g., Thermodynamics Chapter 3", key="pomo_subject")

        total_time = pomo_cycles * pomo_work + (pomo_cycles - 1) * pomo_break
        st.markdown(f"""
<div style="background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.25);border-radius:14px;padding:20px;text-align:center;margin:12px 0;">
  <div class="pomo-ring">{pomo_work}:00</div>
  <div style="color:#9090b8;margin-top:8px;font-size:.9rem;">
    {pomo_cycles} cycles · {total_time} min total · {pomo_cycles * pomo_work} min focus
  </div>
  {f'<div style="color:#a78bfa;font-weight:600;margin-top:6px;">{subject}</div>' if subject else ''}
</div>""", unsafe_allow_html=True)

        # HTML timer
        timer_html = f"""
<div style="text-align:center;padding:10px;">
<div id="timer" style="font-size:5rem;font-weight:900;color:#a78bfa;font-family:monospace;">{pomo_work:02d}:00</div>
<div id="phase" style="color:#9090b8;margin:8px 0;font-size:1rem;">🎯 Focus Time</div>
<div id="cycle_info" style="color:#60a5fa;font-size:.85rem;margin-bottom:16px;">Cycle 1 of {pomo_cycles}</div>
<button onclick="startTimer()" id="startBtn" style="background:linear-gradient(135deg,#7c6af7,#60a5fa);border:none;color:white;padding:12px 32px;border-radius:99px;font-size:1rem;font-weight:700;cursor:pointer;margin:4px;">▶ Start</button>
<button onclick="resetTimer()" style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:white;padding:12px 24px;border-radius:99px;font-size:1rem;cursor:pointer;margin:4px;">↺ Reset</button>
<div id="progress_bar" style="margin-top:16px;height:8px;background:rgba(255,255,255,.1);border-radius:99px;overflow:hidden;">
  <div id="progress_fill" style="height:100%;width:0%;background:linear-gradient(90deg,#7c6af7,#60a5fa);border-radius:99px;transition:width .5s;"></div>
</div>
</div>
<script>
let workSec={pomo_work*60}, breakSec={pomo_break*60}, totalCycles={pomo_cycles};
let curSec=workSec, cycle=1, isWork=true, running=false, interval=null;
const totalWorkSec=workSec;
function pad(n){{return String(n).padStart(2,'0');}}
function update(){{
  document.getElementById('timer').textContent=pad(Math.floor(curSec/60))+':'+pad(curSec%60);
  let total=isWork?workSec:breakSec;
  let pct=(1-curSec/total)*100;
  document.getElementById('progress_fill').style.width=pct+'%';
  document.getElementById('cycle_info').textContent='Cycle '+cycle+' of '+totalCycles;
  document.getElementById('phase').textContent=isWork?'🎯 Focus Time':'☕ Break Time';
}}
function tick(){{
  if(curSec>0){{curSec--;update();}}
  else{{
    if(isWork){{
      if(cycle>=totalCycles){{clearInterval(interval);running=false;
        document.getElementById('phase').textContent='🎉 All done! Great work!';
        document.getElementById('startBtn').textContent='▶ Restart';return;}}
      isWork=false;curSec=breakSec;
    }}else{{cycle++;isWork=true;curSec=workSec;}}
    update();
  }}
}}
function startTimer(){{
  if(running){{clearInterval(interval);running=false;document.getElementById('startBtn').textContent='▶ Resume';}}
  else{{interval=setInterval(tick,1000);running=true;document.getElementById('startBtn').textContent='⏸ Pause';}}
}}
function resetTimer(){{clearInterval(interval);running=false;curSec=workSec;cycle=1;isWork=true;
  document.getElementById('startBtn').textContent='▶ Start';update();}}
update();
</script>"""
        import streamlit.components.v1 as components
        components.html(timer_html, height=320)

    with tab_mindmap:
        mm_topic = st.text_input("Topic for mind map:", placeholder="e.g., Photosynthesis, World War II, Neural Networks", key="mm_topic")
        mm_depth = st.selectbox("Depth:", ["Overview (3 levels)", "Detailed (4 levels)", "Comprehensive (5 levels)"], key="mm_depth")
        if mm_topic and st.button("🗺️ Generate Mind Map", type="primary", key="gen_mm"):
            with st.spinner("Building mind map..."):
                depth = mm_depth.split("(")[1].rstrip(")")
                prompt = f"""Create a structured mind map for: "{mm_topic}"

Format as a hierarchical markdown outline ({depth}):
- Use ## for main branches (5-7 main branches)
- Use ### for sub-branches
- Use - for leaf nodes
- Include key facts, examples, and connections

Then provide a Mermaid mindmap code block:
```mermaid
mindmap
  root(({mm_topic}))
    ...
```

Make it comprehensive and educational."""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=800
                )
                st.markdown(result)

    with tab_summarize:
        sum_text = st.text_area("Text to summarize:", height=200, key="sum_text",
                                 placeholder="Paste lecture notes, textbook chapter, article...")
        sum_style = st.selectbox("Summary format:", [
            "Bullet points (key facts)", "Executive summary (brief)", "Detailed notes (structured)",
            "Concept map (relationships)", "Timeline (if historical)", "Q&A format"
        ], key="sum_style")
        sum_length = st.selectbox("Length:", ["Very brief (100 words)", "Medium (250 words)", "Comprehensive (500 words)"], key="sum_len")
        if sum_text and st.button("📝 Summarize", type="primary", key="do_summarize"):
            with st.spinner("Summarizing..."):
                prompt = f"""Summarize the following text in {sum_length.split('(')[1].rstrip(')')} in {sum_style} format.

Focus on: key concepts, important facts, definitions, relationships, and examples.
For study purposes: highlight what would likely appear in an exam.

Text:
{sum_text[:5000]}"""
                summary = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                )
                st.markdown(summary)
                st.download_button("⬇️ Download Summary", summary, file_name="summary.txt", key="sum_dl")

    with tab_cornell:
        cornell_topic = st.text_input("Topic:", key="cornell_topic")
        cornell_notes = st.text_area("Your rough notes:", height=200, key="cornell_raw",
                                     placeholder="Paste your raw notes, lecture content, or text...")
        if cornell_notes and st.button("📋 Format as Cornell Notes", type="primary", key="gen_cornell"):
            with st.spinner("Formatting..."):
                prompt = f"""Convert these notes into Cornell Note format for: {cornell_topic or 'the topic'}

Structure as:
## 📌 Cue Column (Questions/Keywords)
[List 8-12 questions or keywords that trigger recall of the main ideas]

## 📝 Note-Taking Area (Main Notes)
[Organized, structured notes with key points, facts, examples]

## 💡 Summary (Bottom Section)
[3-5 sentence summary of the entire topic in your own words]

## 🔑 Key Terms
[Important vocabulary with definitions]

Source notes:
{cornell_notes[:4000]}"""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=800
                )
                st.markdown(result)
                st.download_button("⬇️ Download Cornell Notes", result, file_name="cornell_notes.txt", key="cornell_dl")

    with tab_schedule:
        sched_subject = st.text_input("Subjects to study:", placeholder="e.g., Math, Physics, Chemistry, History", key="sched_sub")
        exam_date_input = st.date_input("Exam date:", datetime.date.today() + datetime.timedelta(days=14), key="sched_exam")
        hours_per_day = st.slider("Study hours per day:", 1, 12, 4, key="sched_hours")
        weak_areas = st.text_input("Weak areas (more focus):", key="sched_weak")
        if sched_subject and st.button("📅 Generate Study Schedule", type="primary", key="gen_schedule"):
            days_left = (exam_date_input - datetime.date.today()).days
            with st.spinner("Creating optimized schedule..."):
                prompt = f"""Create a detailed, optimized {days_left}-day study schedule.

Subjects: {sched_subject}
Days until exam: {days_left}
Hours per day: {hours_per_day}
Weak areas (needs more time): {weak_areas or 'None specified'}

Schedule requirements:
1. Day-by-day breakdown with specific topics and times
2. Interleave subjects for better retention (spaced repetition)
3. Give weak areas 30% more time
4. Include review days every 3-4 days
5. Final 2 days = full revision only
6. Include short breaks (Pomodoro-friendly)
7. Add specific study techniques per subject

Format as a clear day-by-day table."""
                schedule = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1000
                )
                st.markdown(schedule)
                st.download_button("⬇️ Download Schedule", schedule, file_name="study_schedule.txt", key="sched_dl")

    if st.button("💬 Back to Chat", use_container_width=True, key="toolkit_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RESEARCH PRO POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_research_power_tools():
    """AI-powered research: multi-source synthesis, gap analysis, literature map."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🔬 Research Power Mode <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Multi-source synthesis · Research gap finder · Methodology advisor · Evidence mapper</div>
</div>""", unsafe_allow_html=True)

    tab_synth, tab_gap, tab_method, tab_abstract = st.tabs([
        "🔗 Source Synthesizer", "🕳️ Gap Finder", "🔭 Methodology Advisor", "📄 Abstract Builder"
    ])

    with tab_synth:
        st.markdown("**Paste multiple sources and get a synthesized analysis:**")
        sources_text = st.text_area("Paste excerpts from multiple sources (separate with ---)", height=250,
                                    key="rp_sources", placeholder="Source 1: ...\n---\nSource 2: ...\n---\nSource 3: ...")
        research_q = st.text_input("Your research question:", key="rp_question")
        synth_type = st.selectbox("Synthesis type:", ["Thematic synthesis", "Narrative synthesis", "Compare & contrast", "Evidence hierarchy", "Chronological development"], key="rp_synth_type")
        if sources_text and research_q and st.button("🔗 Synthesize Sources", type="primary", key="rp_synth"):
            with st.spinner("Synthesizing..."):
                prompt = f"""You are a senior research analyst. Perform a {synth_type} of these sources.

Research question: {research_q}

Sources:
{sources_text[:5000]}

Provide:
1. **Key Themes** across all sources
2. **Points of Agreement** between sources
3. **Points of Contradiction** — where sources disagree
4. **Strongest Evidence** — which claims have most support
5. **Synthesis Paragraph** — a cohesive analytical paragraph integrating all sources
6. **Citation Suggestions** — how to cite each source together

Be analytical, not just descriptive."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_gap:
        topic = st.text_input("Research topic:", key="rp_gap_topic")
        existing = st.text_area("What you know is already researched:", height=150, key="rp_existing",
                                placeholder="e.g., Studies on X show Y, Meta-analyses of Z confirm...")
        if topic and st.button("🕳️ Find Research Gaps", type="primary", key="rp_gap"):
            with st.spinner("Identifying gaps..."):
                prompt = f"""You are a PhD-level research advisor. Identify significant research gaps in: {topic}

Known existing research:
{existing or 'Not specified — identify gaps based on general knowledge of the field'}

Identify:
1. **Methodological Gaps** — what methods haven't been used?
2. **Population Gaps** — what groups haven't been studied?
3. **Geographic Gaps** — what regions are understudied?
4. **Temporal Gaps** — what time periods need more research?
5. **Conceptual Gaps** — what relationships/mechanisms are unclear?
6. **Practical Gaps** — what real-world applications are unexplored?

For each gap, suggest:
- A specific research question that could fill it
- The most appropriate methodology
- Why it matters

Rank by research impact and feasibility."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_method:
        research_topic = st.text_input("Your research topic:", key="rp_meth_topic")
        research_goal = st.selectbox("Research goal:", [
            "Explore a new phenomenon", "Test a hypothesis", "Measure prevalence/frequency",
            "Understand lived experiences", "Compare groups or interventions",
            "Develop/validate an instrument", "Systematic review of existing research"
        ], key="rp_goal")
        discipline = st.text_input("Field/Discipline:", placeholder="e.g., Education, Public Health, Computer Science", key="rp_disc")
        if research_topic and st.button("🔭 Get Methodology Advice", type="primary", key="rp_meth"):
            with st.spinner("Advising..."):
                prompt = f"""You are a research methodology expert. Advise on the best research design.

Topic: {research_topic}
Goal: {research_goal}
Field: {discipline or 'General'}

Provide:
1. **Recommended Methodology** with justification
2. **Research Design** specifics (e.g., RCT, grounded theory, survey)
3. **Data Collection Methods** — what tools/instruments to use
4. **Sampling Strategy** — who, how many, how to select
5. **Analysis Approach** — statistical tests or qualitative methods
6. **Validity & Reliability Strategies** — how to ensure rigor
7. **Ethical Considerations** — what to watch out for
8. **Timeline Estimate** — realistic phases

Alternative methodology if resources are limited: [suggest simpler option]"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_abstract:
        abs_title = st.text_input("Paper/research title:", key="abs_title")
        abs_background = st.text_area("Background/problem:", height=100, key="abs_bg")
        abs_method = st.text_input("Methodology used:", key="abs_method")
        abs_findings = st.text_area("Key findings:", height=100, key="abs_findings")
        abs_type = st.selectbox("Abstract type:", ["Structured (IMRD)", "Unstructured (narrative)", "Informative", "Descriptive"], key="abs_type")
        abs_words = st.selectbox("Word limit:", ["150 words", "250 words", "300 words", "500 words"], key="abs_words")
        if abs_title and abs_findings and st.button("📄 Generate Abstract", type="primary", key="gen_abstract"):
            with st.spinner("Writing abstract..."):
                prompt = f"""Write a {abs_words} {abs_type} academic abstract.

Title: {abs_title}
Background: {abs_background}
Methodology: {abs_method}
Findings: {abs_findings}

Requirements:
- Exactly {abs_words.split()[0]} words maximum
- {abs_type} format
- Academic, precise language
- Include: background/context, objective, method, results, conclusion/implications
- Avoid jargon unless necessary; be accessible to field experts

Return ONLY the abstract text."""
                abstract = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                )
                st.markdown(f'<div class="cit-box">{abstract}</div>', unsafe_allow_html=True)
                wc = len(abstract.split())
                st.caption(f"Word count: {wc}")
                st.download_button("⬇️ Download Abstract", abstract, file_name="abstract.txt", key="abs_dl")

    if st.button("💬 Back to Chat", use_container_width=True, key="rp_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SMART NOTES POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_smart_notes_power():
    """Enhanced smart notes: AI organization, tagging, search, export."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">📒 Smart Notes Pro <span class="power-badge">POWER</span></div>
  <div class="pf-sub">AI tagging · Auto-organize · Key insight extraction · Export to multiple formats</div>
</div>""", unsafe_allow_html=True)

    if "smart_notes_list" not in st.session_state:
        st.session_state.smart_notes_list = []

    tab_write, tab_manage, tab_ai = st.tabs(["✍️ Add Note", "📚 My Notes", "🤖 AI Process"])

    with tab_write:
        note_title = st.text_input("Note title:", key="sn_title")
        note_content = st.text_area("Note content:", height=200, key="sn_content",
                                    placeholder="Write anything — lecture notes, ideas, to-dos, research...")
        note_tag = st.text_input("Tags (comma separated):", placeholder="physics, lecture, chapter5", key="sn_tags")

        if note_content and st.button("💾 Save Note", type="primary", key="sn_save"):
            note = {
                "id": int(time.time()),
                "title": note_title or f"Note {len(st.session_state.smart_notes_list)+1}",
                "content": note_content,
                "tags": [t.strip() for t in note_tag.split(",") if t.strip()],
                "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "summary": ""
            }
            st.session_state.smart_notes_list.append(note)
            st.success(f"✅ Note saved: '{note['title']}'")
            st.rerun()

    with tab_manage:
        notes = st.session_state.smart_notes_list
        if not notes:
            st.info("📝 No notes yet. Add your first note!")
        else:
            # Search
            search = st.text_input("🔍 Search notes:", key="sn_search")
            all_tags = list({tag for n in notes for tag in n.get("tags", [])})
            filter_tag = st.selectbox("Filter by tag:", ["All"] + all_tags, key="sn_filter_tag")

            filtered = notes
            if search:
                filtered = [n for n in filtered if search.lower() in n["content"].lower() or search.lower() in n["title"].lower()]
            if filter_tag != "All":
                filtered = [n for n in filtered if filter_tag in n.get("tags", [])]

            st.markdown(f"**{len(filtered)} note(s)**")
            for note in filtered:
                with st.expander(f"📝 {note['title']} · {note['created']}"):
                    if note.get("tags"):
                        st.markdown(" ".join([f'`{t}`' for t in note["tags"]]))
                    st.markdown(note["content"])
                    if note.get("summary"):
                        st.info(f"🤖 AI Summary: {note['summary']}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🤖 Summarize", key=f"sn_sum_{note['id']}"):
                            with st.spinner("Summarizing..."):
                                summary = generate(
                                    messages=[{"role": "user", "content": f"Summarize in 2 sentences: {note['content'][:2000]}"}],
                                    context_text="", model="llama-3.3-70b-versatile", max_tokens=100
                                )
                                note["summary"] = summary
                                st.rerun()
                    with col2:
                        if st.button("🏷️ Auto-tag", key=f"sn_tag_{note['id']}"):
                            with st.spinner("Tagging..."):
                                tags_resp = generate(
                                    messages=[{"role": "user", "content": f"Give 3-5 short topic tags (comma separated, no hashtags) for: {note['content'][:500]}"}],
                                    context_text="", model="llama-3.3-70b-versatile", max_tokens=50
                                )
                                new_tags = [t.strip().lower() for t in tags_resp.split(",") if t.strip()]
                                note["tags"] = list(set(note.get("tags", []) + new_tags))
                                st.rerun()
                    with col3:
                        if st.button("🗑️ Delete", key=f"sn_del_{note['id']}"):
                            st.session_state.smart_notes_list = [n for n in notes if n["id"] != note["id"]]
                            st.rerun()

    with tab_ai:
        notes = st.session_state.smart_notes_list
        if not notes:
            st.info("Add some notes first!")
        else:
            all_content = "\n\n---\n\n".join([f"# {n['title']}\n{n['content']}" for n in notes[:10]])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔑 Extract Key Insights", use_container_width=True, key="sn_insights"):
                    with st.spinner("Extracting..."):
                        insights = generate(
                            messages=[{"role": "user", "content": f"Extract the 10 most important insights, facts, or action items from these notes:\n{all_content[:4000]}"}],
                            context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                        )
                        st.markdown("### 🔑 Key Insights")
                        st.markdown(insights)
            with col2:
                if st.button("📊 AI Organization", use_container_width=True, key="sn_organize"):
                    with st.spinner("Organizing..."):
                        org = generate(
                            messages=[{"role": "user", "content": f"Suggest how to organize and group these notes into a logical structure with categories and connections:\n{all_content[:3000]}"}],
                            context_text="", model="llama-3.3-70b-versatile", max_tokens=400
                        )
                        st.markdown("### 📊 Suggested Organization")
                        st.markdown(org)

            if st.button("⬇️ Export All Notes", use_container_width=True, key="sn_export"):
                export_text = "\n\n" + "="*60 + "\n\n".join([
                    f"# {n['title']}\nDate: {n['created']}\nTags: {', '.join(n.get('tags',[]))}\n\n{n['content']}\n\n{('AI Summary: ' + n['summary']) if n.get('summary') else ''}"
                    for n in notes
                ])
                st.download_button("⬇️ Download Notes (TXT)", export_text, file_name="my_notes.txt", key="sn_dl")

    if st.button("💬 Back to Chat", use_container_width=True, key="sn_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# DISPATCHER: map app_mode → power upgrade render function
# ══════════════════════════════════════════════════════════════════════════════

POWER_MODE_MAP = {
    "flashcard_battle":       render_flashcard_battle_mode,
    "flashcard_ai_tutor":     render_flashcard_ai_tutor,
    "quiz_analytics":         render_quiz_analytics,
    "essay_power":            render_essay_power_tools,
    "debugger_power":         render_debugger_power_tools,
    "interview_power":        render_interview_power_tools,
    "citation_gen":           render_citation_generator_v2,   # override coming soon
    "regex_tester":           render_regex_tester_v2,         # override coming soon
    "vit_academics":          render_vit_academics_v2,         # override coming soon
    "study_toolkit":          render_study_toolkit_v2,         # override coming soon
    "research_power":         render_research_power_tools,
    "smart_notes_power":      render_smart_notes_power,
}


def dispatch_power_mode(app_mode: str) -> bool:
    """
    Call from app.py BEFORE existing elif chain.
    Returns True if handled here (skip original handler).
    """
    if app_mode in POWER_MODE_MAP:
        POWER_MODE_MAP[app_mode]()
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# ─────────────────── CONTINUATION: BATCH 2 POWER UPGRADES ───────────────────
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE TOOLS POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_language_power():
    """Enhanced language tools: dialect detector, pronunciation, cultural coach."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🌐 Language Power Tools <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Dialect detector · Pronunciation guide · Cultural coach · Phrasebook builder · Live grammar tutor</div>
</div>""", unsafe_allow_html=True)

    tab_detect, tab_phrase, tab_culture, tab_tutor, tab_script = st.tabs([
        "🔍 Dialect Detector", "📖 Phrasebook", "🎭 Culture Coach", "✏️ Grammar Tutor", "✍️ Script Converter"
    ])

    with tab_detect:
        st.markdown("**Paste text in any language — AI identifies the language, dialect, and region:**")
        detect_text = st.text_area("Text to identify:", height=140, key="ld_detect",
                                   placeholder="Paste text in any language, dialect, or script...")
        if detect_text and st.button("🔍 Identify Language & Dialect", type="primary", key="ld_go"):
            with st.spinner("Analyzing..."):
                prompt = f"""You are a computational linguist expert in 200+ languages and their dialects.

Analyze this text and identify:
1. **Primary Language** — with confidence level (%)
2. **Dialect/Variant** — (e.g., Brazilian vs European Portuguese, Egyptian vs Modern Standard Arabic)
3. **Geographic Region** — most likely origin
4. **Register** — formal / informal / colloquial / technical
5. **Script/Writing System** — name and family
6. **Language Family** — (e.g., Indo-European > Romance)
7. **Distinctive Features** — specific words/patterns that helped identify it
8. **Other Possibilities** — 2 alternative languages it could be (with %)

Text:
{detect_text[:2000]}"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                ))

    with tab_phrase:
        st.markdown("**Build an instant phrasebook for any language:**")
        phrase_lang = st.text_input("Target language:", placeholder="e.g., Japanese, Tamil, Arabic, Swahili", key="ph_lang")
        phrase_scenario = st.selectbox("Scenario:", [
            "Travel & Tourism", "Business & Meetings", "Medical / Emergency",
            "University / Academic", "Dating & Social", "Shopping & Bargaining",
            "Restaurant & Food", "Tech & Programming slang", "Custom topic"
        ], key="ph_scenario")
        custom_topic = ""
        if phrase_scenario == "Custom topic":
            custom_topic = st.text_input("Describe your topic:", key="ph_custom")
        native_lang = st.selectbox("Your language:", ["English", "Hindi", "Tamil", "Telugu", "French", "Spanish", "German", "Arabic"], key="ph_native")
        num_phrases = st.slider("Number of phrases:", 10, 30, 20, key="ph_count")

        if phrase_lang and st.button("📖 Build Phrasebook", type="primary", key="ph_build"):
            topic = custom_topic if phrase_scenario == "Custom topic" else phrase_scenario
            with st.spinner(f"Building {phrase_lang} phrasebook..."):
                prompt = f"""Create a practical {num_phrases}-phrase phrasebook for {topic} in {phrase_lang} for a {native_lang} speaker.

Format as a table:
| # | {native_lang} | {phrase_lang} | Pronunciation (Romanized) | Notes |
|---|---|---|---|---|
| 1 | ... | ... | ... | cultural tip or usage note |

Include:
- Essential survival phrases for this scenario
- Cultural do's and don'ts in the notes column
- Pronunciation in simple Roman letters (not IPA)
- Mark VERY IMPORTANT phrases with ⭐

After the table, add:
**🚨 Critical Mistakes to Avoid** (3 common errors for {native_lang} speakers learning {phrase_lang})"""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1200
                )
                st.markdown(result)
                st.download_button("⬇️ Download Phrasebook", result, file_name=f"{phrase_lang}_phrasebook.txt", key="ph_dl")

    with tab_culture:
        st.markdown("**Get a deep cultural briefing before interacting with a culture:**")
        culture = st.text_input("Culture / Country:", placeholder="e.g., Japan, Saudi Arabia, Brazil, Nigeria", key="cult_name")
        context = st.selectbox("Context:", ["Business meeting", "Dining/Food", "Social gathering", "Academic setting", "Negotiation", "Family visit", "Religious site"], key="cult_ctx")
        if culture and st.button("🎭 Get Culture Briefing", type="primary", key="cult_go"):
            with st.spinner("Researching cultural norms..."):
                prompt = f"""You are a cross-cultural communication expert and anthropologist.

Create a comprehensive cultural briefing for: {culture} — Context: {context}

Include:
1. **🤝 Greetings & First Impressions** — correct protocols, what to say/do
2. **🚫 Absolute Don'ts** — things that would cause serious offense
3. **✅ Impressive Behaviors** — things that earn deep respect
4. **💬 Communication Style** — direct vs indirect, eye contact, silence norms
5. **⏰ Time & Punctuality** — expectations and meaning
6. **🍽️ Eating & Drinking** — relevant customs for this context
7. **👗 Dress & Appearance** — what to wear / avoid
8. **🎁 Gift-Giving** — if relevant, what's appropriate
9. **💡 Power Dynamics** — hierarchy, age, gender norms to be aware of
10. **🗣️ 5 Phrases That Will Impress** — local language phrases with pronunciation

Be specific, practical, and culturally sensitive."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_tutor:
        if "grammar_chat" not in st.session_state:
            st.session_state.grammar_chat = []
        st.markdown("**Live grammar tutor — write in your target language, get instant corrections:**")
        tutor_lang = st.selectbox("Language you're learning:", [
            "Spanish", "French", "German", "Japanese", "Mandarin Chinese", "Arabic",
            "Hindi", "Tamil", "Korean", "Italian", "Portuguese", "Russian"
        ], key="gt_lang")
        your_level = st.selectbox("Your level:", ["Beginner (A1-A2)", "Intermediate (B1-B2)", "Advanced (C1-C2)"], key="gt_level")

        for msg in st.session_state.grammar_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_text = st.chat_input(f"Write something in {tutor_lang}...")
        if user_text:
            st.session_state.grammar_chat.append({"role": "user", "content": user_text})
            prompt = f"""You are a patient, encouraging {tutor_lang} grammar tutor for a {your_level} student.

The student wrote: "{user_text}"

Provide:
1. **✅ What's correct** — praise specific things they got right
2. **🔧 Corrections** — list each error with explanation:
   - Original: [what they wrote]
   - Corrected: [fixed version]
   - Why: [clear explanation]
3. **✨ Improved Version** — the whole sentence written naturally
4. **📚 Grammar Tip** — one rule to remember from this error
5. **💬 Continue the Conversation** — ask them a follow-up question in {tutor_lang} (with translation) to keep practicing

Keep it encouraging and motivating!"""
            with st.spinner("Tutor analyzing..."):
                response = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=600
                )
            st.session_state.grammar_chat.append({"role": "assistant", "content": response})
            st.rerun()

        if st.session_state.grammar_chat:
            if st.button("🗑️ New Session", key="gt_clear"):
                st.session_state.grammar_chat = []
                st.rerun()

    with tab_script:
        st.markdown("**Convert between writing scripts (e.g., Devanagari ↔ Roman, Arabic ↔ Roman):**")
        script_text = st.text_area("Input text:", height=120, key="sc_text")
        script_task = st.selectbox("Conversion type:", [
            "Romanize (any script → Roman letters with pronunciation)",
            "Hindi/Devanagari → Romanized transliteration",
            "Arabic → Romanized transliteration",
            "Japanese → Romaji",
            "Korean → Romanized (Revised Romanization)",
            "Tamil → Romanized transliteration",
            "Greek → Roman alphabet equivalent",
            "Russian/Cyrillic → Roman alphabet",
        ], key="sc_task")
        if script_text and st.button("✍️ Convert Script", type="primary", key="sc_go"):
            with st.spinner("Converting..."):
                prompt = f"""Perform this script conversion: {script_task}

Input: {script_text}

Provide:
1. **Converted Text** — the romanization/transliteration
2. **Pronunciation Guide** — how to pronounce each word (syllable by syllable)
3. **Word-by-word breakdown** — for sentences, show each word mapped
4. **Audio pronunciation tip** — describe the hardest sounds to produce"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="lang_power_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCIENCE SOLVER POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_science_power():
    """Power upgrades for science solver: visual step-by-step, unit check, error analysis."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🧪 Science Power Lab <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Dimensional analysis · Error analysis · Lab report writer · Concept visualizer · Exam predictor</div>
</div>""", unsafe_allow_html=True)

    tab_dim, tab_err, tab_lab, tab_predict = st.tabs([
        "📐 Dimensional Analysis", "⚠️ Error Analysis", "🧪 Lab Report Writer", "🎯 Exam Predictor"
    ])

    with tab_dim:
        st.markdown("**Check if your formula/calculation is dimensionally consistent:**")
        formula = st.text_input("Formula or equation:", placeholder="e.g., F = ma, v = u + at, P = IV", key="da_formula")
        given_units = st.text_area("Units of each variable:", height=100, key="da_units",
                                   placeholder="e.g., F in Newtons (kg⋅m/s²), m in kg, a in m/s²")
        if formula and st.button("📐 Analyze Dimensions", type="primary", key="da_go"):
            with st.spinner("Analyzing..."):
                prompt = f"""You are a physics professor performing dimensional analysis.

Formula: {formula}
Given units: {given_units}

Perform complete dimensional analysis:
1. **Convert each variable** to SI base units (kg, m, s, A, K, mol, cd)
2. **Left side dimensions** — fully expanded
3. **Right side dimensions** — fully expanded
4. **Consistency check** — do they match? ✅/❌
5. **If inconsistent** — where the error is and what it should be
6. **Derived unit name** — what the resulting unit is called (if applicable)

Show ALL working clearly with → notation."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=500
                ))

    with tab_err:
        st.markdown("**Calculate and propagate experimental errors:**")
        measurement_type = st.selectbox("Error type:", [
            "Absolute & relative error", "Percentage error", "Error propagation (addition/subtraction)",
            "Error propagation (multiplication/division)", "Standard deviation from repeated measurements",
            "Systematic vs random error analysis"
        ], key="ea_type")
        values = st.text_area("Your measurements/values:", height=120, key="ea_vals",
                               placeholder="e.g., Length = 5.3 ± 0.1 cm, Mass = 200 ± 5 g\nOR paste repeated measurements: 5.1, 5.3, 5.2, 5.4, 5.3")
        if values and st.button("⚠️ Analyze Errors", type="primary", key="ea_go"):
            with st.spinner("Calculating..."):
                prompt = f"""You are a physics lab expert. Perform {measurement_type}.

Data: {values}

Show:
1. **Step-by-step calculation** with formulas used
2. **Final result** with proper uncertainty notation (value ± error)
3. **Significant figures** — correctly rounded
4. **Percentage uncertainty** of final result
5. **Which measurement contributes most** to the total error
6. **How to reduce this error** in a real experiment

Show all working clearly."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=600
                ))

    with tab_lab:
        st.markdown("**Generate a professional lab report from your experiment details:**")
        exp_name = st.text_input("Experiment name:", placeholder="e.g., Determination of g using a simple pendulum", key="lab_name")
        exp_aim = st.text_input("Aim/Objective:", key="lab_aim")
        exp_method = st.text_area("Method/Procedure (brief notes):", height=120, key="lab_method",
                                   placeholder="Jot down what you did, materials used...")
        exp_data = st.text_area("Results/Data:", height=120, key="lab_data",
                                 placeholder="Paste your measurements, tables, graphs description...")
        exp_subject = st.selectbox("Subject:", ["Physics", "Chemistry", "Biology", "Environmental Science", "Computer Science"], key="lab_subj")
        lab_level = st.selectbox("Level:", ["CBSE/ICSE (Class 11-12)", "JEE/NEET level", "Undergraduate (BSc/BTech)", "Postgraduate"], key="lab_level")

        if exp_name and exp_data and st.button("🧪 Generate Lab Report", type="primary", key="lab_go"):
            with st.spinner("Writing lab report..."):
                prompt = f"""Write a professional, complete {lab_level} {exp_subject} lab report.

Experiment: {exp_name}
Aim: {exp_aim or 'To be derived from experiment name'}
Method notes: {exp_method}
Results/Data: {exp_data}

Generate a full lab report with:
1. **Title**
2. **Aim/Objective**
3. **Theory** — relevant physics/chemistry principles with key formulas
4. **Apparatus/Materials**
5. **Procedure** — numbered steps, professional language
6. **Observations & Data Table** — properly formatted
7. **Calculations** — step-by-step with units
8. **Result** — clear statement with units and uncertainty
9. **Error Analysis** — sources and type of errors
10. **Discussion** — interpretation, comparison with theory
11. **Conclusion**
12. **Precautions** — 5 specific safety/accuracy measures

Use scientific language appropriate for {lab_level}."""
                report = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1200
                )
                st.markdown(report)
                st.download_button("⬇️ Download Lab Report", report, file_name="lab_report.txt", key="lab_dl")

    with tab_predict:
        st.markdown("**AI predicts the most likely exam questions from your topic:**")
        pred_topic = st.text_input("Topic/Chapter:", placeholder="e.g., Electromagnetism, Organic Chemistry - Aldehydes", key="ep_topic_sci")
        pred_exam = st.selectbox("Exam type:", [
            "JEE Main", "JEE Advanced", "NEET", "CBSE Class 12 Board",
            "GATE", "GRE Subject", "AP Physics/Chemistry/Biology",
            "A-Level", "IB Diploma", "University Semester Exam"
        ], key="ep_exam")
        pred_subject = st.selectbox("Subject:", ["Physics", "Chemistry", "Biology", "Mathematics"], key="ep_subj")
        if pred_topic and st.button("🎯 Predict Exam Questions", type="primary", key="ep_go"):
            with st.spinner("Predicting..."):
                prompt = f"""You are a veteran {pred_exam} examiner and coaching expert with 15+ years of experience.

Predict the most likely questions from: {pred_topic} ({pred_subject})
Exam: {pred_exam}

Provide:
1. **⭐ HIGH PROBABILITY Questions (will almost certainly appear)** — 5 questions with mark weightage
2. **📊 MEDIUM PROBABILITY Questions** — 5 questions
3. **🧠 Conceptual MCQs** — 5 tricky MCQs with explanations of the trap options
4. **📝 Derivations/Proofs to prepare** — the most important ones
5. **🔢 Numerical Problems** — 3 typical numericals with approach (not full solution)
6. **💡 Examiner's Mindset** — what concept combinations are currently trending

For each question: state why it's likely to appear."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="sci_power_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PRESENTATION BUILDER POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_presentation_power():
    """Power upgrades: slide critic, speaker coaching, presenter notes enhancer."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🎨 Presentation Power Studio <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Slide critic · Speaker notes coach · Storytelling arc · Hook generator · Opening line builder</div>
</div>""", unsafe_allow_html=True)

    tab_critic, tab_hook, tab_story, tab_qa, tab_notes = st.tabs([
        "🔍 Slide Critic", "🎣 Hook Generator", "📖 Story Arc", "❓ Q&A Prep", "🎤 Speaker Notes"
    ])

    with tab_critic:
        slide_content = st.text_area("Paste your slide content (one slide or all slides):", height=250,
                                     key="sc_slides", placeholder="Slide 1: Title\nBullets...\n\nSlide 2: ...")
        audience = st.text_input("Target audience:", placeholder="e.g., investors, students, senior executives", key="sc_audience")
        pres_goal = st.text_input("Goal of the presentation:", placeholder="e.g., secure funding, teach concept, persuade purchase", key="sc_goal")
        if slide_content and st.button("🔍 Critique My Slides", type="primary", key="sc_go"):
            with st.spinner("Expert reviewing your slides..."):
                prompt = f"""You are a TED Talk curator and presentation design expert (Nancy Duarte school).

Critique these slides for: Audience — {audience or 'general'}, Goal — {pres_goal or 'inform/persuade'}

Slides:
{slide_content[:4000]}

Provide slide-by-slide feedback:
**Overall Assessment:**
- Story/Arc: Does it flow? (/10)
- Clarity: Is each slide single-focused? (/10)
- Engagement: Would this keep attention? (/10)
- Action: Does it drive toward the goal? (/10)

**Slide-by-Slide:**
For each slide:
🔴 Problem: [specific issue]
✅ Fix: [exact rewrite or suggestion]

**Top 5 Power Improvements** that would most transform this presentation

**Opening Line Suggestion** — a better way to start that immediately captures attention"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_hook:
        hook_topic = st.text_input("Presentation topic:", key="hook_topic")
        hook_audience = st.text_input("Audience:", key="hook_audience")
        hook_type = st.multiselect("Hook styles to generate:", [
            "Shocking statistic", "Provocative question", "Bold claim/Myth-bust",
            "Personal story opener", "Dramatic scenario", "Quote by authority figure",
            "Counterintuitive statement", "Two-sentence story"
        ], default=["Shocking statistic", "Provocative question", "Bold claim/Myth-bust"], key="hook_types")
        if hook_topic and st.button("🎣 Generate Hooks", type="primary", key="hook_go"):
            with st.spinner("Crafting attention hooks..."):
                styles = "\n".join([f"- {h}" for h in (hook_type or ["Shocking statistic", "Provocative question"])])
                prompt = f"""You are a professional speechwriter and TED Talk coach.

Create powerful opening hooks for a presentation on: {hook_topic}
Audience: {hook_audience or 'general professional'}

Generate one hook for each of these styles:
{styles}

For each hook:
**[Style Name]:**
"[The hook — written exactly as it would be spoken, 1-3 sentences]"
Why it works: [brief explanation]

Make each hook genuinely compelling, specific, and memorable. Not generic."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                ))

    with tab_story:
        story_topic = st.text_input("Presentation topic:", key="sa_topic")
        story_goal = st.selectbox("What do you want the audience to do after?", [
            "Believe something new", "Buy / invest in something",
            "Change their behavior", "Learn a concept deeply",
            "Take immediate action", "Feel inspired / motivated",
            "Approve a proposal", "Remember this info long-term"
        ], key="sa_goal")
        story_duration = st.selectbox("Duration:", ["5 minutes", "10 minutes", "20 minutes", "30 minutes", "45 minutes", "60 minutes"], key="sa_dur")
        if story_topic and st.button("📖 Build Story Arc", type="primary", key="sa_go"):
            with st.spinner("Building narrative arc..."):
                prompt = f"""You are Nancy Duarte (presentation strategist). Build a story arc for:

Topic: {story_topic}
Goal: The audience should {story_goal}
Duration: {story_duration}

Create a complete narrative structure:

**🎭 The Story Spine:**
1. **Opening Hook** — what to say in the first 30 seconds
2. **The Problem/Tension** — what's wrong with the status quo
3. **The Stakes** — why this matters (emotional + logical)
4. **The Journey** — 3 key acts with content beats
5. **The Turn** — the insight/reveal moment
6. **The New World** — what's possible now
7. **The Call to Action** — exactly what to ask the audience to do

**⏱️ Time Breakdown** — minutes per section for {story_duration}

**🔑 3 Core Messages** — the 3 things they must remember

**💡 Presentation Pattern** — which story structure fits best (Hero's Journey / Problem-Solution / Sparkline / etc.)"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_qa:
        qa_topic = st.text_input("Presentation topic:", key="qa_topic")
        qa_audience = st.text_input("Audience type:", key="qa_audience")
        qa_content = st.text_area("Key points from your presentation:", height=150, key="qa_content")
        if qa_topic and st.button("❓ Generate Q&A Prep", type="primary", key="qa_go"):
            with st.spinner("Anticipating questions..."):
                prompt = f"""You are a debate coach and presentation expert. Prepare this speaker for Q&A.

Topic: {qa_topic}
Audience: {qa_audience or 'general'}
Key content: {qa_content or 'Standard presentation on the topic'}

Generate:
**🔥 HARDEST Questions** (5 — ones that will challenge assumptions):
For each: Question | Model Answer | Red flag to avoid

**📊 DATA Questions** (3 — when they'll ask "where's your evidence?"):
For each: Question | How to answer without data | How to answer with data

**🤔 Clarification Questions** (3 — things that are genuinely unclear):
For each: Question | Polished answer

**😤 Skeptic/Hostile Questions** (3 — from someone who disagrees):
For each: Question | De-escalation technique | Substantive answer

**✨ Great Questions to Invite** (3 — ones you WANT to be asked):
For each: Question | Brilliant answer that reinforces your message"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_notes:
        notes_slides = st.text_area("Paste slide content:", height=200, key="sn_slides",
                                    placeholder="Slide 1: Introduction\n- Bullet 1\n- Bullet 2\n\nSlide 2: ...")
        notes_style = st.selectbox("Speaker notes style:", [
            "Detailed script (word-for-word)", "Key talking points only",
            "Story + data blend", "Socratic (question-led)", "Energetic/motivational"
        ], key="sn_style")
        notes_pace = st.selectbox("Speaking pace:", ["Fast (150wpm)", "Natural (130wpm)", "Deliberate (110wpm)"], key="sn_pace")
        if notes_slides and st.button("🎤 Generate Speaker Notes", type="primary", key="sn_go"):
            with st.spinner("Writing speaker notes..."):
                wpm = int(notes_pace.split("(")[1].rstrip("wpm)"))
                prompt = f"""Write detailed {notes_style} speaker notes for each slide.

Speaking style: {notes_style}
Target pace: {wpm} words per minute

Slides:
{notes_slides[:4000]}

For EACH slide write:
**[Slide N: Title]**
🎤 Notes: [what to say — in {notes_style} format]
⏱️ Timing: [estimated seconds at {wpm}wpm]
💡 Emphasis: [which word/phrase to stress most]
➡️ Transition: [how to move to next slide naturally]

End with: **Total estimated presentation time**"""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1000
                )
                st.markdown(result)
                st.download_button("⬇️ Download Speaker Notes", result, file_name="speaker_notes.txt", key="sn_dl_btn")

    if st.button("💬 Back to Chat", use_container_width=True, key="pres_power_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SMART SHOPPING POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_shopping_power():
    """Shopping: AI advisor, price tracker, budget optimizer, gift finder."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🛒 Smart Shopping AI <span class="power-badge">POWER</span></div>
  <div class="pf-sub">AI product advisor · Budget optimizer · Gift finder · Spec comparator · Deal analyzer</div>
</div>""", unsafe_allow_html=True)

    tab_advisor, tab_compare, tab_gift, tab_budget = st.tabs([
        "🤖 AI Advisor", "⚖️ Spec Comparator", "🎁 Gift Finder", "💰 Budget Optimizer"
    ])

    with tab_advisor:
        st.markdown("**Describe what you want to buy and get personalized AI advice:**")
        product_need = st.text_area("What do you want to buy? (be specific):", height=120, key="sa_need",
                                    placeholder="e.g., A laptop for college — mostly for coding, some gaming, budget ₹60,000-80,000, need long battery life...")
        usage_context = st.text_input("Who is it for?", placeholder="e.g., myself (CS student), my parents (60 yr olds), gift for friend", key="sa_who")
        budget_range = st.text_input("Budget:", placeholder="e.g., ₹15,000-20,000 or $200-300", key="sa_budget")

        if product_need and st.button("🤖 Get AI Buying Advice", type="primary", key="sa_go"):
            with st.spinner("AI shopping expert analyzing..."):
                prompt = f"""You are a senior consumer technology expert and personal shopping advisor.

User wants: {product_need}
For: {usage_context or 'themselves'}
Budget: {budget_range or 'not specified'}

Provide expert buying advice:

1. **🏆 TOP RECOMMENDATION** — single best option with exact model name, current price estimate, where to buy
2. **💰 BEST VALUE** — best price-to-performance (if different from above)
3. **⚡ PREMIUM PICK** — if budget allows, what to upgrade to and why
4. **⚠️ AVOID** — 1-2 specific products/brands to avoid for this use case with reasons

For each recommendation:
- Specific model name
- Key specs that matter for this use case
- Price range (India: ₹, specify Amazon/Flipkart/offline)
- One thing to be aware of (limitation or tradeoff)

5. **🧠 BUYING TIPS** — 3 things to check/negotiate before buying
6. **📅 TIMING** — is this a good time to buy or should they wait for sales?"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=800
                ))

    with tab_compare:
        st.markdown("**Compare 2-4 products on any specs you care about:**")
        product1 = st.text_input("Product 1:", placeholder="e.g., iPhone 16, Samsung Galaxy S25", key="cmp_p1")
        product2 = st.text_input("Product 2:", placeholder="e.g., Pixel 9, OnePlus 13", key="cmp_p2")
        product3 = st.text_input("Product 3 (optional):", key="cmp_p3")
        product4 = st.text_input("Product 4 (optional):", key="cmp_p4")
        priorities = st.multiselect("What matters most to you:", [
            "Price/Value", "Performance/Speed", "Battery life", "Camera quality",
            "Build quality/Durability", "Display quality", "Software/Updates",
            "After-sales service", "Portability/Weight", "Storage/RAM"
        ], default=["Price/Value", "Performance/Speed"], key="cmp_prio")

        products = [p for p in [product1, product2, product3, product4] if p.strip()]
        if len(products) >= 2 and st.button("⚖️ Compare Products", type="primary", key="cmp_go"):
            with st.spinner("Comparing..."):
                prompt = f"""You are a product review expert. Compare these products:
{chr(10).join(f'{i+1}. {p}' for i, p in enumerate(products))}

User priorities: {', '.join(priorities)}

Create a detailed comparison:

**📊 Comparison Table:**
| Feature | {" | ".join(products)} |
|---------|{"|-|" * len(products)}
[Fill in key specs and ratings 1-10]

**🏆 WINNER by Category:**
For each priority the user mentioned, which product wins and why (1-2 sentences)

**🎯 VERDICT:**
- Best overall: [product] because...
- Best for [use case 1]: [product]
- Best for [use case 2]: [product]
- Best budget choice: [product]

**⚠️ Deal-breakers to know:**
One significant weakness for each product that isn't obvious from the specs"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_gift:
        recipient = st.text_input("Who is the gift for?", placeholder="e.g., my dad who loves cricket, my best friend who's into skincare", key="gf_who")
        occasion = st.selectbox("Occasion:", ["Birthday", "Anniversary", "Festival (Diwali/Eid/Christmas)", "Graduation", "Wedding", "Thank-you gift", "Just because", "Baby shower", "Housewarming"], key="gf_occ")
        budget = st.text_input("Budget:", placeholder="e.g., ₹500-2000", key="gf_budget")
        interests = st.text_input("Their interests/hobbies:", placeholder="e.g., cooking, gaming, reading, fitness", key="gf_int")
        age_group = st.selectbox("Age group:", ["Child (5-12)", "Teen (13-17)", "Young adult (18-30)", "Adult (30-50)", "Senior (50+)"], key="gf_age")

        if recipient and st.button("🎁 Find Perfect Gift", type="primary", key="gf_go"):
            with st.spinner("Finding the perfect gift..."):
                prompt = f"""You are a professional gift consultant with expertise in Indian and global gifting culture.

Find the perfect gift for:
- Recipient: {recipient}
- Occasion: {occasion}
- Budget: {budget or 'flexible'}
- Interests: {interests or 'general'}
- Age: {age_group}

Provide:
**🏆 TOP 5 GIFT IDEAS** (ranked by appropriateness):
For each:
- Gift name + description
- Why it's perfect for THIS person/occasion
- Price range and where to buy in India
- How to present/wrap it for maximum impact
- Personalization tip — how to make it extra special

**💡 GIFT EXPERIENCE IDEAS** (non-material gifts):
2-3 experience-based alternatives

**🚫 AVOID** — 2 common gift mistakes for this specific situation

**✉️ Gift Message Template** — a heartfelt message to write"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=800
                ))

    with tab_budget:
        st.markdown("**Optimize a list of items within your budget:**")
        items_list = st.text_area("Items you want to buy:", height=150, key="bo_items",
                                   placeholder="New phone ₹50,000\nLaptop bag ₹2,000\nBluetooth headphones ₹5,000\nMouse ₹1,500\nBackup charger ₹800")
        total_budget = st.text_input("Total budget:", placeholder="e.g., ₹55,000", key="bo_budget")
        priority_order = st.text_input("Priority order (most → least important):", placeholder="Phone > Laptop bag > Headphones > ...", key="bo_priority")

        if items_list and total_budget and st.button("💰 Optimize Budget", type="primary", key="bo_go"):
            with st.spinner("Optimizing..."):
                prompt = f"""You are a financial advisor helping optimize a shopping budget.

Items to buy:
{items_list}

Total budget: {total_budget}
Priority order: {priority_order or 'as listed'}

Provide:
1. **📊 Budget Analysis** — total cost vs budget, surplus/deficit
2. **✅ RECOMMENDED LIST** — what to buy now within budget (sorted by priority)
3. **⏳ DEFER LIST** — what to postpone and for how long
4. **💡 SAVINGS TIPS** — specific ways to reduce cost on each item without sacrificing quality
5. **📅 BUYING SEQUENCE** — optimal order to buy (which first for best deals)
6. **🎯 Budget Allocation** — exact amounts to allocate per category

If over budget: suggest specific cheaper alternatives for each item with price and trade-offs."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="shop_power_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PLANNER / STUDY PLANNER POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_planner_power():
    """Advanced study planner with Gantt, AI prioritization, daily digest."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">📅 Smart Planner Pro <span class="power-badge">POWER</span></div>
  <div class="pf-sub">AI task prioritizer · Daily digest · Goal tracker · Deadline calculator · Habit builder</div>
</div>""", unsafe_allow_html=True)

    tab_priority, tab_habit, tab_deadline, tab_daily = st.tabs([
        "🎯 AI Prioritizer", "🔄 Habit Builder", "⏳ Deadline Calculator", "📋 Daily Digest"
    ])

    with tab_priority:
        st.markdown("**Paste your task list and AI will prioritize using Eisenhower Matrix:**")
        tasks_input = st.text_area("Your tasks (one per line):", height=200, key="pp_tasks",
                                   placeholder="Submit assignment\nStudy Chapter 5\nCall mom\nBuy groceries\nPrepare for interview\nRespond to emails\nExercise\nPay electricity bill")
        context_deadline = st.text_input("Any deadlines or context:", placeholder="e.g., Interview tomorrow, exam in 3 days", key="pp_deadline")
        if tasks_input and st.button("🎯 Prioritize with AI", type="primary", key="pp_go"):
            with st.spinner("Prioritizing..."):
                prompt = f"""You are a productivity coach and time management expert.

Prioritize these tasks using the Eisenhower Matrix + urgency/importance scoring:

Tasks:
{tasks_input}

Context: {context_deadline or 'No specific deadlines mentioned'}

Organize into:

**🔴 DO FIRST (Urgent + Important):**
[list tasks with why + suggested time to complete]

**📅 SCHEDULE (Important, Not Urgent):**
[list tasks with best day/time to schedule]

**📞 DELEGATE/MINIMIZE (Urgent, Not Important):**
[list tasks with minimization strategy]

**🗑️ ELIMINATE/DEFER (Neither Urgent nor Important):**
[list tasks]

**⏱️ RECOMMENDED SEQUENCE FOR TODAY:**
Hour-by-hour schedule if they have 8 hours

**💡 PRO TIP:** One insight about their task list pattern"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                ))

    with tab_habit:
        st.markdown("**Design a science-backed habit system:**")
        habit_goal = st.text_input("Habit you want to build:", placeholder="e.g., Exercise daily, Read 30 min/day, Meditate, Study consistently", key="hb_goal")
        current_struggle = st.text_input("Why does it usually fail?", placeholder="e.g., I forget, I'm too tired, I don't feel like it", key="hb_struggle")
        available_time = st.selectbox("Time you can commit daily:", ["5 minutes", "10 minutes", "20 minutes", "30 minutes", "1 hour", "2+ hours"], key="hb_time")
        if habit_goal and st.button("🔄 Design My Habit System", type="primary", key="hb_go"):
            with st.spinner("Designing system..."):
                prompt = f"""You are a behavioral psychologist and habit design expert (James Clear / BJ Fogg school).

Design a complete habit system for: {habit_goal}
Common failure reason: {current_struggle or 'general consistency issues'}
Daily time available: {available_time}

Provide:

**🔬 ROOT CAUSE ANALYSIS** — why this habit fails for most people

**🏗️ THE MINIMUM VIABLE HABIT** — the smallest possible version that still builds the habit

**📅 30-DAY PROGRESSION PLAN:**
- Week 1: [exact habit + cue + reward]
- Week 2: [progression]
- Week 3: [progression]
- Week 4: [full habit]

**⚡ HABIT STACKING** — what existing habit to attach this to

**🔔 IMPLEMENTATION INTENTION** — exact "When X, I will do Y" statement

**🛡️ OBSTACLE PLAN** — for each common failure mode, a specific countermeasure

**📊 HOW TO TRACK PROGRESS** — simple tracking method

**🎉 REWARD SYSTEM** — short, medium, and long-term rewards"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=800
                ))

    with tab_deadline:
        st.markdown("**Calculate realistic timelines for complex tasks:**")
        project = st.text_input("Project/task description:", placeholder="e.g., Write 3000-word research paper on climate change", key="dl_project")
        hard_deadline = st.date_input("Hard deadline:", datetime.date.today() + datetime.timedelta(days=7), key="dl_date")
        hours_per_day_dl = st.slider("Study/work hours available per day:", 1, 14, 4, key="dl_hours")
        complexity = st.selectbox("Complexity level:", ["Simple (clear steps)", "Moderate (some research needed)", "Complex (lots of unknowns)"], key="dl_complexity")

        if project and st.button("⏳ Calculate Timeline", type="primary", key="dl_go"):
            days_left = (hard_deadline - datetime.date.today()).days
            total_hours = days_left * hours_per_day_dl
            with st.spinner("Calculating..."):
                prompt = f"""You are a project manager and time estimation expert.

Project: {project}
Days until deadline: {days_left}
Hours available per day: {hours_per_day_dl} (total: {total_hours} hours)
Complexity: {complexity}

Create a realistic project plan:

**📊 TIME ESTIMATE:**
- Best case: X hours
- Realistic: X hours
- With buffer (20% extra): X hours
- Feasibility: ✅ Comfortable / ⚠️ Tight / 🔴 Very tight

**📅 PHASE-BY-PHASE BREAKDOWN:**
| Phase | Task | Hours | Deadline |
|-------|------|-------|----------|
[Break into 4-6 phases with specific tasks]

**⚠️ RISK ASSESSMENT:**
3 things that could delay this and mitigation strategy

**🚀 IF RUNNING LATE — Emergency Options:**
What to cut, what to simplify, what to do differently

**💡 PROCRASTINATION TRAP:** The most dangerous distraction for this specific project"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                ))

    with tab_daily:
        st.markdown("**Generate your personalized daily study/work digest:**")
        subjects = st.text_input("Today's subjects/work areas:", placeholder="e.g., Physics Ch.7, Math integration, English essay", key="dd_subjects")
        mood = st.selectbox("Your current energy level:", ["🔋 High energy — ready to tackle hard stuff", "⚡ Medium — can focus but need structure", "😴 Low — need easy wins today"], key="dd_mood")
        time_available = st.slider("Hours available today:", 1, 12, 4, key="dd_time")
        if subjects and st.button("📋 Generate My Daily Plan", type="primary", key="dd_go"):
            with st.spinner("Building your day..."):
                energy = mood.split("—")[0].strip()
                prompt = f"""You are a personal productivity coach. Create a detailed daily plan.

Today's topics: {subjects}
Energy level: {energy}
Time available: {time_available} hours

Create a SPECIFIC, hour-by-hour plan:

**🌅 MORNING RITUAL (first 15 min):**
[Specific warm-up activity]

**📚 STUDY BLOCKS:**
[Time-blocked schedule for {time_available} hours, adjusted for {energy} energy]

Format:
[Time] - [Activity] - [Duration] - [Goal/Outcome]

**☕ BREAK STRATEGY:**
When and how to take breaks for maximum recovery

**🎯 TODAY'S TARGETS:**
3 specific measurable goals for each subject

**🌙 END-OF-DAY REVIEW:**
5-minute reflection routine

**💪 MOTIVATION BOOST:**
One powerful quote or thought to keep going today"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="planner_power_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LEARN CODING POWER UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def render_learn_coding_power():
    """Power upgrades for learn coding: project builder, code challenge, career roadmap."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">💻 Coding Accelerator <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Project idea generator · Daily challenge · Career roadmap · Live code review · DSA visualizer</div>
</div>""", unsafe_allow_html=True)

    tab_project, tab_challenge, tab_roadmap, tab_review, tab_dsa = st.tabs([
        "🚀 Project Ideas", "⚔️ Daily Challenge", "🗺️ Career Roadmap", "🔎 Code Review", "📊 DSA Guide"
    ])

    with tab_project:
        skill_level = st.selectbox("Your level:", ["Complete beginner", "Beginner (some basics)", "Intermediate", "Advanced"], key="lcp_level")
        language = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++", "React", "Node.js", "Flutter", "Kotlin", "Swift", "Go", "Rust"], key="lcp_lang")
        interests = st.multiselect("Your interests:", [
            "Web development", "Mobile apps", "Data science/ML", "Games",
            "Automation/Bots", "Cybersecurity", "Blockchain", "IoT/Hardware",
            "Finance/Trading", "Health/Fitness", "Social media", "Productivity tools"
        ], default=["Web development"], key="lcp_interests")
        if st.button("🚀 Generate Project Ideas", type="primary", key="lcp_go"):
            with st.spinner("Generating..."):
                prompt = f"""You are a senior software engineer and coding mentor.

Generate 5 perfectly-calibrated project ideas for a {skill_level} {language} developer interested in: {', '.join(interests)}.

For each project:

**Project N: [Creative Name]**
📝 **What it does:** (2 sentences)
🎯 **Skills you'll learn:** (5 specific skills)
⏱️ **Time estimate:** (realistic)
🔧 **Tech stack:** (exactly what to use)
📦 **Core features to build:** (3-5 MVP features)
🚀 **How to start:** (first 3 steps, very specific)
💡 **Stretch goals:** (2 advanced additions once MVP is done)
🌟 **Why employers love this:** (how it helps career)

Make projects genuinely useful and impressive for a portfolio. Not the same old todo app."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1000
                ))

    with tab_challenge:
        ch_lang = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++", "SQL", "Any"], key="ch_lang")
        ch_level = st.selectbox("Difficulty:", ["Easy (warm-up)", "Medium (interview level)", "Hard (competitive)", "Expert (FAANG-style)"], key="ch_level")
        ch_topic = st.selectbox("Topic:", ["Arrays/Strings", "Linked Lists", "Trees/Graphs", "Dynamic Programming", "Sorting/Searching", "Hash Maps", "Recursion", "System Design concept", "SQL queries", "Surprise me!"], key="ch_topic")

        if st.button("⚔️ Get Challenge", type="primary", key="ch_go"):
            with st.spinner("Creating challenge..."):
                prompt = f"""Create a {ch_level} {ch_topic} coding challenge for {ch_lang}.

Format:

## 🎯 Challenge: [Creative Name]

**Problem Statement:**
[Clear, specific problem with context]

**Input Format:**
[What the function receives]

**Output Format:**
[What it should return]

**Examples:**
```
Input: ...
Output: ...
Explanation: ...
```

**Constraints:**
- Time limit: O(?) expected
- Space limit: O(?) expected
- Edge cases to handle: [list them]

**Hints (use only if stuck):**
1. [Gentle hint]
2. [More specific hint]
3. [Approach hint]

**Test Cases (5):** [edge cases included]

---

After the user submits, they can share their solution and I'll review it."""
                st.session_state["current_challenge"] = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                )

        if "current_challenge" in st.session_state:
            st.markdown(st.session_state["current_challenge"])
            user_sol = st.text_area("Your solution:", height=200, key="ch_sol", placeholder="Paste your code here...")
            if user_sol and st.button("🔍 Review My Solution", type="primary", key="ch_review"):
                with st.spinner("Reviewing..."):
                    review_prompt = f"""Review this solution to the coding challenge:

Challenge:
{st.session_state.get('current_challenge', '')[:1000]}

User's solution in {ch_lang}:
{user_sol}

Provide:
1. **✅ Correctness** — does it solve all cases?
2. **⏱️ Time Complexity** — analysis of their approach
3. **💾 Space Complexity** — analysis
4. **🐛 Bugs Found** — any errors (if any)
5. **✨ Code Quality** — style, naming, readability
6. **🚀 Optimization** — how to make it faster/cleaner
7. **💡 Alternative Approach** — a different solution technique
8. **Score: X/10** with breakdown"""
                    st.markdown(generate(
                        messages=[{"role": "user", "content": review_prompt}],
                        context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                    ))

    with tab_roadmap:
        goal_role = st.text_input("Your target role:", placeholder="e.g., Frontend Developer, ML Engineer, Full-Stack, DevOps", key="rm_role")
        current_level = st.selectbox("Current level:", ["No coding experience", "Beginner (basic syntax)", "Intermediate (built small projects)", "Advanced (professional experience)"], key="rm_current")
        timeline = st.selectbox("Timeline:", ["3 months", "6 months", "1 year", "2 years"], key="rm_timeline")
        if goal_role and st.button("🗺️ Generate Roadmap", type="primary", key="rm_go"):
            with st.spinner("Building roadmap..."):
                prompt = f"""Create a detailed learning roadmap for becoming a {goal_role}.

Current level: {current_level}
Timeline: {timeline}

Generate a phase-by-phase roadmap:

**🗺️ ROADMAP: {goal_role} in {timeline}**

For each phase (divide into 4 phases within {timeline}):

**Phase N: [Name] — [Duration]**
📚 Topics to master: (prioritized list)
🛠️ Tools/Frameworks: (specific ones)
📦 Projects to build: (2-3 specific projects)
📖 Resources: (free online resources — specific URLs if known)
✅ Completion milestone: (how you know you're ready to advance)

**💼 Job-Ready Checklist:**
- Portfolio requirements
- Interview prep topics
- Salary expectations for this path in India

**⚠️ Common mistakes** people make on this path and how to avoid them"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1000
                ))

    with tab_review:
        rev_code = st.text_area("Paste your code for review:", height=250, key="rev_code")
        rev_lang = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "SQL", "HTML/CSS"], key="rev_lang")
        rev_focus = st.multiselect("Review focus:", ["Bug detection", "Performance optimization", "Code readability", "Best practices", "Security", "Design patterns", "Scalability"], default=["Bug detection", "Code readability"], key="rev_focus")
        if rev_code and st.button("🔎 Review Code", type="primary", key="rev_go"):
            with st.spinner("Expert reviewing..."):
                focus_str = ", ".join(rev_focus)
                prompt = f"""You are a Google-level senior engineer doing a rigorous code review.

Focus areas: {focus_str}
Language: {rev_lang}

Code to review:
```{rev_lang.lower()}
{rev_code[:3000]}
```

Provide detailed review:

**📊 Overall Score: X/10**
- Correctness: X/10
- Readability: X/10
- Efficiency: X/10
- Best practices: X/10

**🔴 Must Fix:**
[Line-by-line issues that must be addressed]

**🟡 Should Improve:**
[Non-critical but important improvements]

**🟢 What's Good:**
[Specific praise for good patterns]

**✨ Refactored Version:**
[Key sections rewritten better, with explanations]

**📚 Concept to Study:** One pattern/principle this code would benefit from"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                ))

    with tab_dsa:
        dsa_topic = st.selectbox("DSA Topic:", [
            "Arrays & Strings", "Linked Lists", "Stacks & Queues", "Trees (Binary, BST, AVL)",
            "Heaps & Priority Queues", "Graphs (BFS/DFS)", "Dynamic Programming",
            "Sorting Algorithms", "Searching Algorithms", "Hash Tables",
            "Tries", "Segment Trees", "Divide & Conquer", "Greedy Algorithms", "Backtracking"
        ], key="dsa_topic")
        dsa_lang = st.selectbox("Code examples in:", ["Python", "Java", "C++", "JavaScript"], key="dsa_lang")
        if st.button("📊 Deep Dive", type="primary", key="dsa_go"):
            with st.spinner("Creating DSA guide..."):
                prompt = f"""You are a CS professor and competitive programming coach. Create a complete guide to {dsa_topic}.

Code examples in {dsa_lang}.

Provide:
**📚 {dsa_topic} — Complete Guide**

1. **Core Concept** — intuitive explanation with real-world analogy
2. **Visual Representation** — ASCII art or step-by-step trace
3. **Key Operations & Complexity:**
   | Operation | Time | Space | Notes |
   
4. **Implementation from Scratch:**
```{dsa_lang.lower()}
[Clean, commented implementation]
```

5. **Common Interview Patterns** — 3 problem types that use this
6. **Classic Problem + Solution:**
Problem: [name]
Approach: [explain]
```{dsa_lang.lower()}
[solution code]
```

7. **Edge Cases to Always Handle**
8. **When to Use vs Not Use** — compared to alternatives
9. **Practice Problems** — 5 problems (Easy/Medium/Hard) with LeetCode # if applicable"""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=1200
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="lcp_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MINDMAP POWER UPGRADE (inject inline into existing mindmap mode)
# ══════════════════════════════════════════════════════════════════════════════

def render_mindmap_power():
    """Enhanced mindmap with multiple formats and AI-driven concept linking."""
    _inject_power_css()
    st.markdown("""
<div class="pf-header">
  <div class="pf-title">🗺️ Mind Map Studio <span class="power-badge">POWER</span></div>
  <div class="pf-sub">Mermaid diagrams · Concept web · Hierarchy map · Free-form topic exploration</div>
</div>""", unsafe_allow_html=True)

    tab_from_text, tab_from_topic, tab_concept_web = st.tabs([
        "📄 From Study Material", "💡 From Topic", "🕸️ Concept Web"
    ])

    with tab_from_text:
        mm_text = st.text_area("Paste your study text:", height=200, key="mm_text",
                               placeholder="Paste lecture notes, textbook content, article...")
        mm_depth = st.selectbox("Mind map depth:", ["Overview (3 levels)", "Detailed (4 levels)", "Exhaustive (5 levels)"], key="mm_depth2")
        mm_format = st.selectbox("Output format:", ["Mermaid diagram code", "Indented text outline", "Both"], key="mm_format")

        existing = st.session_state.get("context_text", "")
        use_uploaded = st.checkbox("Use uploaded study material", value=bool(existing), key="mm_use_upload") if existing else False
        source = existing if use_uploaded else mm_text

        if source and st.button("🗺️ Generate Mind Map", type="primary", key="mm_gen"):
            with st.spinner("Building mind map..."):
                depth_n = mm_depth.split("(")[1].rstrip(")")
                prompt = f"""Create a comprehensive mind map for the content below ({depth_n}).

Content:
{source[:5000]}

Provide:
{"**Mermaid Code:**" if "Mermaid" in mm_format else ""}
{"```mermaid" if "Mermaid" in mm_format else ""}
{"mindmap" if "Mermaid" in mm_format else ""}
{"  root((MAIN TOPIC))" if "Mermaid" in mm_format else ""}
{"  [expand to full mind map with all branches]" if "Mermaid" in mm_format else ""}
{"```" if "Mermaid" in mm_format else ""}

{"**Text Outline:**" if "text" in mm_format.lower() or "Both" in mm_format else ""}
{"[Hierarchical indented outline with all branches]" if "text" in mm_format.lower() or "Both" in mm_format else ""}

Make it comprehensive with 5-7 main branches and 3-5 sub-branches each."""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=900
                )
                st.markdown(result)
                # Extract mermaid code
                mermaid_match = re.search(r'```mermaid\n(.*?)```', result, re.DOTALL)
                if mermaid_match:
                    st.code(mermaid_match.group(1), language="mermaid")
                    st.info("💡 Copy the mermaid code above and paste into [mermaid.live](https://mermaid.live) to visualize")
                    st.download_button("⬇️ Download .mmd", mermaid_match.group(1), file_name="mindmap.mmd", key="mm_dl")

    with tab_from_topic:
        topic = st.text_input("Topic to map:", placeholder="e.g., Machine Learning, The French Revolution, DNA Replication", key="mm_topic2")
        angle = st.selectbox("Map angle:", ["Academic/Educational", "Exam-focused (mark-worthy points)", "Conceptual (how things relate)", "Practical/Applied"], key="mm_angle")
        if topic and st.button("💡 Map This Topic", type="primary", key="mm_topic_go"):
            with st.spinner("Mapping..."):
                prompt = f"""Create a {angle} mind map for: {topic}

Generate in Mermaid mindmap syntax:
```mermaid
mindmap
  root(({topic}))
    [Main branch 1]
      [Sub 1a]
      [Sub 1b]
      [Sub 1c]
    [Main branch 2]
      ...
```

Then provide the text outline version as well.

Include: key definitions, relationships, examples, and exam-important points."""
                result = generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=800
                )
                st.markdown(result)
                m = re.search(r'```mermaid\n(.*?)```', result, re.DOTALL)
                if m:
                    st.download_button("⬇️ Download .mmd", m.group(1), file_name="mindmap.mmd", key="mm_tpc_dl")
                    st.info("💡 Paste at [mermaid.live](https://mermaid.live) to see the visual map")

    with tab_concept_web:
        concept = st.text_input("Central concept:", placeholder="e.g., Entropy, Democracy, Neural Network, Photosynthesis", key="cw_concept")
        if concept and st.button("🕸️ Build Concept Web", type="primary", key="cw_go"):
            with st.spinner("Building web..."):
                prompt = f"""Build a rich concept web for: {concept}

Show:
1. **Definition** — concise, precise
2. **Core Properties** — 5 defining characteristics
3. **Prerequisite Concepts** — what you must understand first
4. **Related Concepts** — 8-10 concepts that connect to this
5. **Contrast Concepts** — what this is explicitly NOT
6. **Applications** — 5 real-world applications
7. **Analogies** — 2 everyday analogies that capture the essence
8. **Common Misconceptions** — 3 things people get wrong

Format as a rich network of connections."""
                st.markdown(generate(
                    messages=[{"role": "user", "content": prompt}],
                    context_text="", model="llama-3.3-70b-versatile", max_tokens=700
                ))

    if st.button("💬 Back to Chat", use_container_width=True, key="mm_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# EXTENDED POWER MODE MAP (Batch 2)
# ══════════════════════════════════════════════════════════════════════════════

POWER_MODE_MAP.update({
    "language_tools":          render_language_power,
    "science_solver":          render_science_power,
    "presentation_builder":    render_presentation_power,
    "smart_shopping":          render_shopping_power,
    "planner":                 render_planner_power,
    "learn_coding":            render_learn_coding_power,
    "mindmap":                 render_mindmap_power,
})

