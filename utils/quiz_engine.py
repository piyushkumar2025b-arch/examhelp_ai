"""
quiz_engine.py — Advanced Quiz Powerup
Timed Mode, Adaptive Difficulty, Mixed Formats, Analytics, PYQ
"""

import streamlit as st
import json
import time
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from utils.ai_engine import generate

def get_adaptive_difficulty(topic: str) -> str:
    scores = st.session_state.get("quiz_v2_adaptive_scores", {})
    history = scores.get(topic, [])
    if not history: return "medium"
    
    avg = sum(history) / len(history)
    if avg > 0.8: return "hard"
    if avg < 0.4: return "easy"
    return "medium"

def generate_quiz_batch(context_text: str, is_pyq: bool = False, pyq_text: str = ""):
    if is_pyq:
        prompt = f"Format these past year questions into a structured Quiz. Mixed format (MCQ, True/False, Fill in Blank, Short Answer).\n{pyq_text}\nOutput valid JSON array: [{{'type': 'mcq|tf|fill|short', 'topic': '...', 'q': '...', 'options': ['...'], 'correct': '...', 'explanation': '...'}}]"
    else:
        prompt = f"Generate a 10-question mixed format quiz (MCQ, True/False, Fill blank, Short answer) based on this text. Topics should vary. Output valid JSON array. Difficulty levels should adapt.\nText:\n{context_text[:5000]}"
    
    resp = generate(
        messages=[{"role": "user", "content": prompt}],
        context_text="", model="llama-4-scout-17b-16e-instruct", max_tokens=3000
    )
    
    import re
    m = re.search(r'\[.*\]', resp, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except:
            return []
    return []

def render_quiz():
    st.subheader("📝 Elite Quiz & Mock Exams")
    
    if "quiz_v2_data" not in st.session_state: st.session_state.quiz_v2_data = []
    if "quiz_v2_current" not in st.session_state: st.session_state.quiz_v2_current = 0
    if "quiz_v2_timer" not in st.session_state: st.session_state.quiz_v2_timer = None
    if "quiz_v2_stats" not in st.session_state: st.session_state.quiz_v2_stats = {"score":0, "start_time":0, "q_times":{}, "topic_scores":{}}
    if "quiz_v2_failed" not in st.session_state: st.session_state.quiz_v2_failed = []

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🪄 Generate Quick Quiz"):
            with st.spinner("Generating mixed format quiz..."):
                cards = generate_quiz_batch(st.session_state.get("context_text",""))
                if cards:
                    st.session_state.quiz_v2_data = cards
                    st.session_state.quiz_v2_current = 0
                    st.session_state.quiz_v2_timer = None
                    st.session_state.quiz_v2_stats = {"score":0, "start_time":time.time(), "q_times":{}, "topic_scores":{}}
                    st.rerun()

    with c2:
        if st.button("⏱️ Timed Mock Exam (10 min)"):
            with st.spinner("Generating mock exam..."):
                cards = generate_quiz_batch(st.session_state.get("context_text",""))
                if cards:
                    st.session_state.quiz_v2_data = cards
                    st.session_state.quiz_v2_current = 0
                    st.session_state.quiz_v2_timer = time.time() + 600
                    st.session_state.quiz_v2_stats = {"score":0, "start_time":time.time(), "q_times":{}, "topic_scores":{}}
                    st.rerun()

    with c3:
        if st.session_state.quiz_v2_failed:
            if st.button("🔁 Drill Wrong Answers"):
                st.session_state.quiz_v2_data = st.session_state.quiz_v2_failed
                st.session_state.quiz_v2_failed = []
                st.session_state.quiz_v2_current = 0
                st.session_state.quiz_v2_timer = None
                st.session_state.quiz_v2_stats = {"score":0, "start_time":time.time(), "q_times":{}, "topic_scores":{}}
                st.rerun()

    with st.expander("📚 Past Year Questions (PYQ) Mode"):
        pyq_text = st.text_area("Paste PYQs here to generate structured quiz")
        if st.button("Generate from PYQs") and pyq_text:
            with st.spinner("Parsing PYQs..."):
                cards = generate_quiz_batch("", is_pyq=True, pyq_text=pyq_text)
                if cards:
                    st.session_state.quiz_v2_data = cards
                    st.session_state.quiz_v2_current = 0
                    st.rerun()

    quiz = st.session_state.quiz_v2_data
    if not quiz:
        st.info("No active quiz. Generate one to start!")
        return

    qi = st.session_state.quiz_v2_current

    # Timer Logic
    if st.session_state.quiz_v2_timer:
        rem = st.session_state.quiz_v2_timer - time.time()
        st_autorefresh(interval=1000, limit=int(rem)+2, key="qtimer")
        if rem <= 0:
            st.error("⏰ Time's up! Auto-submitting quiz.")
            st.session_state.quiz_v2_current = len(quiz)
            st.session_state.quiz_v2_timer = None
            st.rerun()
        else:
            st.warning(f"⏱️ Time Remaining: {int(rem)//60:02d}:{int(rem)%60:02d}")

    # Score screen
    if qi >= len(quiz):
        st.success(f"🎉 Quiz Complete! Final Score: {st.session_state.quiz_v2_stats['score']}/{len(quiz)}")
        
        # Analytics Plot
        scores = st.session_state.quiz_v2_stats["topic_scores"]
        if scores:
            topic_names = list(scores.keys())
            topic_vals = [scores[t]["correct"]/scores[t]["total"]*100 for t in topic_names]
            
            fig = px.bar(x=topic_names, y=topic_vals, title="Topic Mastery (%)", labels={'x': 'Topic', 'y': "Accuracy %"})
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
            weakest = min(scores.keys(), key=lambda k: scores[k]["correct"]/scores[k]["total"])
            st.markdown(f"**Weakest Topic:** {weakest} (Needs review)")

        if st.button("Start Over"):
            st.session_state.quiz_v2_data = []
            st.rerun()
        return

    # Render Question
    q_item = quiz[qi]
    topic = q_item.get("topic", "General")
    q_type = q_item.get("type", "mcq")
    diff = get_adaptive_difficulty(topic)

    st.progress((qi) / len(quiz))
    st.markdown(f"**Question {qi+1}/{len(quiz)}** | Topic: {topic} | Difficulty: {diff.upper()}")
    st.markdown(f"### {q_item.get('q')}")

    ans_submitted = False
    is_correct = False
    
    if q_type in ["mcq", "tf"]:
        opts = q_item.get("options", ["True", "False"] if q_type=="tf" else [])
        choice = st.radio("Select answer:", opts, key=f"q_{qi}")
        if st.button("Submit Answer"):
            is_correct = (choice == q_item.get("correct"))
            ans_submitted = True
    else:
        ans = st.text_input("Your answer:", key=f"q_{qi}")
        if st.button("Submit Answer"):
            is_correct = (ans.strip().lower() == q_item.get("correct", "").strip().lower())
            ans_submitted = True

    if ans_submitted:
        # Time calc
        elapsed = time.time() - st.session_state.quiz_v2_stats["start_time"]
        st.session_state.quiz_v2_stats["start_time"] = time.time()
        st.session_state.quiz_v2_stats["q_times"][qi] = elapsed
        
        # Topic Score tracking
        if topic not in st.session_state.quiz_v2_stats["topic_scores"]:
            st.session_state.quiz_v2_stats["topic_scores"][topic] = {"correct":0, "total":0}
        st.session_state.quiz_v2_stats["topic_scores"][topic]["total"] += 1

        # Adaptive history
        if topic not in st.session_state.quiz_v2_adaptive_scores:
            st.session_state.quiz_v2_adaptive_scores[topic] = []

        if is_correct:
            st.success("✅ Correct!")
            st.session_state.quiz_v2_stats["score"] += 1
            st.session_state.quiz_v2_stats["topic_scores"][topic]["correct"] += 1
            st.session_state.quiz_v2_adaptive_scores[topic].append(1)
        else:
            st.error(f"❌ Incorrect. Correct answer: {q_item.get('correct')}")
            st.session_state.quiz_v2_failed.append(q_item)
            st.session_state.quiz_v2_adaptive_scores[topic].append(0)
            
        st.info(f"💡 Explanation: {q_item.get('explanation')}")
        
        if st.button("Next Question ➡️", key="next_q"):
            st.session_state.quiz_v2_current += 1
            st.rerun()
