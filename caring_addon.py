"""caring_addon.py — Step 32: Mood tracker with chart + AI journaling"""
import streamlit as st, datetime, io, random

MOODS = ["😄 Great","😊 Good","😐 Neutral","😔 Low","😢 Sad","😤 Stressed","😰 Anxious","🤩 Excited"]
JOURNAL_PROMPTS = [
    "What made you smile today, even just a little?",
    "What is one thing you are grateful for right now?",
    "Describe a challenge you faced today. What did you learn?",
    "What would you tell your past self from a year ago?",
    "What emotion is taking up the most space in you right now?",
    "Write about someone who made a positive difference in your life.",
    "What is one thing you want to let go of today?",
    "Describe your ideal tomorrow. What would make it perfect?",
    "What are 3 small wins you had this week?",
    "If your emotions were weather, what would today's forecast be?",
]

def render_caring_addon():
    ca1, ca2, ca3 = st.tabs(["📊 Mood Tracker", "📓 AI Journal", "💆 Affirmations"])

    with ca1:
        st.markdown("**📊 Daily Mood Tracker**")
        today = str(datetime.date.today())
        if "cz_mood_log" not in st.session_state: st.session_state.cz_mood_log = []

        sel_mood = st.selectbox("How are you feeling right now?", MOODS, key="cz_mood_sel")
        mood_note = st.text_input("Any note? (optional):", placeholder="e.g. exam stress, slept badly...", key="cz_mood_note")
        if st.button("📊 Log This Mood", type="primary", use_container_width=True, key="cz_log_mood"):
            st.session_state.cz_mood_log.append({"date":today,"mood":sel_mood,"note":mood_note,"time":datetime.datetime.now().strftime("%H:%M")})
            st.success(f"✅ Logged: {sel_mood}")
            st.rerun()

        log = st.session_state.cz_mood_log
        if log:
            st.markdown(f"**📈 Mood History ({len(log)} entries):**")
            last_7 = log[-14:]
            for entry in reversed(last_7):
                st.markdown(f"""
                <div style="background:rgba(10,14,30,0.7);border:1px solid rgba(244,114,182,0.12);
                    border-radius:10px;padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;gap:12px;">
                    <span style="font-size:1.3rem;">{entry['mood'].split()[0]}</span>
                    <div style="flex:1;">
                        <div style="font-size:0.85rem;color:rgba(255,255,255,0.7);">{entry['mood'][2:]}</div>
                        {f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.35);">{entry["note"]}</div>' if entry.get('note') else ''}
                    </div>
                    <div style="font-size:0.65rem;color:rgba(255,255,255,0.25);">{entry['date']} {entry.get('time','')}</div>
                </div>""", unsafe_allow_html=True)

            # Chart
            try:
                import matplotlib; matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                mood_scores = {"😄 Great":5,"😊 Good":4,"😐 Neutral":3,"🤩 Excited":5,"😔 Low":2,"😢 Sad":1,"😤 Stressed":2,"😰 Anxious":2}
                scores = [mood_scores.get(e["mood"],3) for e in last_7]
                dates  = [e["date"][-5:] for e in last_7]
                fig,ax = plt.subplots(figsize=(10,3.5), facecolor='#0a0e1e'); ax.set_facecolor('#0f172a')
                ax.plot(dates, scores, 'o-', color='#f472b6', linewidth=2.5, markersize=7)
                ax.fill_between(range(len(scores)), scores, alpha=0.2, color='#f472b6')
                ax.set_ylim(0,6); ax.set_yticks([1,2,3,4,5]); ax.set_yticklabels(["Sad","Low","OK","Good","Great"], color='#ffffff80')
                ax.set_xticks(range(len(dates))); ax.set_xticklabels(dates, rotation=30, color='#ffffff80', fontsize=8)
                ax.grid(True, color='#ffffff10'); ax.set_title("Mood Trend", color='#f9a8d4', fontsize=11)
                [sp.set_edgecolor('#ffffff15') for sp in ax.spines.values()]
                plt.tight_layout(); buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=130,bbox_inches='tight')
                buf.seek(0); plt.close(); st.image(buf, use_container_width=True)
            except Exception: pass

            if st.button("🤖 AI Mood Insights", key="cz_ai_mood"):
                with st.spinner("Analyzing your mood pattern..."):
                    try:
                        from utils.ai_engine import generate
                        moods_str = ", ".join(f"{e['date']}: {e['mood']}" for e in last_7[-7:])
                        ans = generate(f"Analyze this person's mood pattern over the past week: {moods_str}. Provide: pattern observation, possible triggers, personalized self-care suggestions, and an encouraging message.")
                        st.markdown(ans)
                    except Exception as e: st.error(str(e))

    with ca2:
        st.markdown("**📓 AI-Powered Journaling**")
        if st.button("🎲 Random Prompt", key="cz_rand_prompt"):
            st.session_state.cz_prompt = random.choice(JOURNAL_PROMPTS); st.rerun()
        prompt = st.session_state.get("cz_prompt", JOURNAL_PROMPTS[0])
        st.markdown(f"""
        <div style="background:rgba(244,114,182,0.07);border:1px solid rgba(244,114,182,0.2);
            border-radius:14px;padding:16px;margin-bottom:14px;font-style:italic;
            color:rgba(255,255,255,0.7);">💭 {prompt}</div>""", unsafe_allow_html=True)
        journal_entry = st.text_area("Write freely — this is your safe space:", height=200, key="cz_journal_text")
        if journal_entry and st.button("💚 Get AI Response & Insights", type="primary", use_container_width=True, key="cz_journal_ai"):
            with st.spinner("Aria is reading your journal..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Someone shared this journal entry: '{journal_entry}'. Respond as Aria, a warm empathetic AI companion. Acknowledge their feelings, validate their experience, offer 2-3 gentle insights or reframes, and end with a caring, hopeful message. Be human and warm, not clinical."
                    response = generate(p, max_tokens=800, temperature=0.85)
                    st.markdown(f"""
                    <div style="background:rgba(244,114,182,0.06);border:1px solid rgba(244,114,182,0.2);
                        border-radius:16px;padding:20px;font-size:0.9rem;color:rgba(255,255,255,0.78);line-height:1.85;">
                        <div style="font-size:0.65rem;letter-spacing:3px;color:#f472b6;margin-bottom:12px;">ARIA'S RESPONSE 💚</div>
                        {response}
                    </div>""", unsafe_allow_html=True)
                except Exception as e: st.error(str(e))
        if journal_entry:
            today_str = str(datetime.date.today())
            st.download_button("📥 Save Journal Entry", f"{today_str}\n{prompt}\n\n{journal_entry}", f"journal_{today_str}.txt", key="cz_jrnl_dl")

    with ca3:
        st.markdown("**💆 Daily Affirmations**")
        aff_mood = st.selectbox("I need affirmations for:", ["General positivity","Exam anxiety","Self-confidence","Motivation","Grief/Loss","Social anxiety","Body image","Academic pressure"], key="cz_aff_mood")
        if st.button("✨ Generate Affirmations", type="primary", use_container_width=True, key="cz_aff_btn"):
            with st.spinner("Creating affirmations..."):
                try:
                    from utils.ai_engine import generate
                    affirmations = generate(f"Create 10 powerful, personal affirmations for someone dealing with {aff_mood}. Each should feel genuine, not generic. First person, present tense. Numbered list.", max_tokens=600, temperature=0.7)
                    aff_lines = [l.strip() for l in affirmations.split("\n") if l.strip() and any(c.isalpha() for c in l)]
                    for line in aff_lines[:10]:
                        st.markdown(f"""
                        <div style="background:rgba(244,114,182,0.06);border:1px solid rgba(244,114,182,0.15);
                            border-radius:12px;padding:12px 16px;margin-bottom:8px;font-size:0.9rem;
                            color:rgba(255,255,255,0.8);font-style:italic;line-height:1.6;">✨ {line}</div>""", unsafe_allow_html=True)
                except Exception as e: st.error(str(e))
