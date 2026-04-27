"""
wellness_addon.py — Steps 17-22
Covers: Pomodoro (ambient sounds, analytics), Study Streak (XP/badges), Study Insights (spaced repetition, gap analysis)
"""
import streamlit as st, random, datetime

# ═══════════════════════════════════
# STEPS 17-18: POMODORO ADDON
# ═══════════════════════════════════

AMBIENT_SOUNDS = [
    {"name":"Rain on Window","emoji":"🌧️","url":"https://www.youtube.com/embed/mPZkdNFkNps?autoplay=1&loop=1"},
    {"name":"Coffee Shop","emoji":"☕","url":"https://www.youtube.com/embed/BOdLmxy06H0?autoplay=1&loop=1"},
    {"name":"Forest Birds","emoji":"🌿","url":"https://www.youtube.com/embed/Qm846KdZN_M?autoplay=1&loop=1"},
    {"name":"Ocean Waves","emoji":"🌊","url":"https://www.youtube.com/embed/V-_O7nl0Ii0?autoplay=1&loop=1"},
    {"name":"White Noise","emoji":"〰️","url":"https://www.youtube.com/embed/nMfPqeZjc2c?autoplay=1&loop=1"},
    {"name":"Lo-Fi Beats","emoji":"🎵","url":"https://www.youtube.com/embed/jfKfPfyJRdk?autoplay=1&loop=1"},
    {"name":"Thunderstorm","emoji":"⛈️","url":"https://www.youtube.com/embed/2Oo_8SBpMIM?autoplay=1&loop=1"},
    {"name":"Library Silence","emoji":"📚","url":"https://www.youtube.com/embed/q76bMs-NwRk?autoplay=1&loop=1"},
]

def render_pomodoro_addon():
    st.markdown("""
    <style>
    .pom-sound-card { background:rgba(10,14,30,0.8);border:1px solid rgba(255,255,255,0.08);
        border-radius:14px;padding:14px;text-align:center;cursor:pointer;
        transition:all 0.25s ease; }
    .pom-sound-card:hover,.pom-sound-card.active {
        border-color:rgba(99,102,241,0.45);transform:translateY(-3px);
        background:rgba(99,102,241,0.1); }
    .pom-stat { background:rgba(10,14,30,0.8);border:1px solid rgba(255,255,255,0.07);
        border-radius:12px;padding:14px;text-align:center; }
    </style>""", unsafe_allow_html=True)

    po1, po2 = st.tabs(["🎵 Ambient Sounds","📊 Session Analytics"])

    with po1:
        st.markdown("**🎵 Focus Ambient Sound Mixer**")
        st.caption("Play relaxing sounds while you work to boost focus 🧠")

        if "pom_sound_idx" not in st.session_state:
            st.session_state.pom_sound_idx = None

        scols = st.columns(4)
        for i, s in enumerate(AMBIENT_SOUNDS):
            with scols[i%4]:
                active = st.session_state.pom_sound_idx == i
                if st.button(f"{s['emoji']} {s['name']}", key=f"pom_sound_{i}",
                             use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state.pom_sound_idx = None if active else i
                    st.rerun()

        idx = st.session_state.pom_sound_idx
        if idx is not None:
            sound = AMBIENT_SOUNDS[idx]
            st.markdown(f"""
            <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.2);
                border-radius:16px;padding:16px;margin-top:12px;">
                <div style="font-size:0.78rem;color:#818cf8;margin-bottom:10px;">
                    🎵 Now playing: <strong>{sound['name']}</strong>
                </div>
                <iframe width="100%" height="80" src="{sound['url']}"
                    frameborder="0" allow="autoplay" style="border-radius:10px;"></iframe>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("▶️ Click a sound above to start playing")

    with po2:
        st.markdown("**📊 Pomodoro Analytics Dashboard**")
        if "pom_history" not in st.session_state:
            st.session_state.pom_history = [
                {"date":str(datetime.date.today()-datetime.timedelta(days=i)),"sessions":random.randint(2,8),"minutes":random.randint(25,200)}
                for i in range(7)
            ]

        hist = st.session_state.pom_history
        total_sessions = sum(h["sessions"] for h in hist)
        total_minutes = sum(h["minutes"] for h in hist)
        avg_sessions = total_sessions / len(hist)

        c1,c2,c3,c4 = st.columns(4)
        for col,(lbl,val,clr) in zip([c1,c2,c3,c4],[
            ("Total Sessions",str(total_sessions),"#6366f1"),
            ("Total Minutes",str(total_minutes),"#06b6d4"),
            ("Daily Average",f"{avg_sessions:.1f}","#10b981"),
            ("Streak Days",str(len(hist)),"#f59e0b"),
        ]):
            col.markdown(f"""
            <div class="pom-stat">
                <div style="font-size:1.4rem;font-weight:800;color:{clr};">{val}</div>
                <div style="font-size:0.6rem;letter-spacing:2px;color:rgba(255,255,255,0.3);">{lbl}</div>
            </div>""", unsafe_allow_html=True)

        # Bar chart
        try:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt, io as _io
            fig,ax=plt.subplots(figsize=(10,4),facecolor='#0a0e1e'); ax.set_facecolor('#0f172a')
            dates=[h["date"][-5:] for h in hist]; sessions=[h["sessions"] for h in hist]
            bars=ax.bar(dates,sessions,color='#6366f188',edgecolor='#6366f1',linewidth=1.5)
            ax.grid(True,axis='y',color='#ffffff10'); ax.tick_params(colors='#ffffff80')
            for sp in ax.spines.values(): sp.set_edgecolor('#ffffff15')
            ax.set_title('Daily Pomodoro Sessions (Last 7 Days)',color='#c7d2fe',fontsize=11)
            plt.tight_layout(); buf=_io.BytesIO(); plt.savefig(buf,format='png',dpi=130,bbox_inches='tight')
            buf.seek(0); plt.close(); st.image(buf,use_container_width=True)
        except Exception: pass

        if st.button("➕ Log Today's Session", key="pom_log", use_container_width=True):
            today = str(datetime.date.today())
            for h in hist:
                if h["date"] == today: h["sessions"]+=1; h["minutes"]+=25; break
            else:
                hist.append({"date":today,"sessions":1,"minutes":25})
            st.success("✅ Session logged!"); st.rerun()


# ═══════════════════════════════════
# STEPS 19-20: STUDY STREAK ADDON
# ═══════════════════════════════════

BADGES = [
    {"id":"first","name":"First Step","emoji":"🌱","desc":"Complete your first study session","xp":10},
    {"id":"streak3","name":"Hat Trick","emoji":"🎩","desc":"3-day study streak","xp":30},
    {"id":"streak7","name":"Week Warrior","emoji":"⚔️","desc":"7-day study streak","xp":100},
    {"id":"streak30","name":"Iron Mind","emoji":"🦾","desc":"30-day study streak","xp":500},
    {"id":"early","name":"Early Bird","emoji":"🌅","desc":"Study before 7 AM","xp":20},
    {"id":"night","name":"Night Owl","emoji":"🦉","desc":"Study after 11 PM","xp":20},
    {"id":"marathon","name":"Marathon","emoji":"🏃","desc":"Study 4+ hours in a day","xp":80},
    {"id":"perfect","name":"Perfect Week","emoji":"⭐","desc":"Study every day for a week","xp":150},
    {"id":"subject5","name":"Polymath","emoji":"🎓","desc":"Study 5 different subjects","xp":60},
    {"id":"social","name":"Collaborator","emoji":"🤝","desc":"Share 10 notes","xp":40},
]

LEVELS = [(0,"Novice","⚪"),(100,"Apprentice","🔵"),(300,"Scholar","🟢"),(700,"Expert","🟡"),
          (1500,"Master","🟠"),(3000,"Grandmaster","🔴"),(6000,"Legend","💜")]

def render_streak_addon():
    st.markdown("""
    <style>
    .str-badge { background:rgba(10,14,30,0.8);border:1px solid rgba(255,255,255,0.08);
        border-radius:14px;padding:16px;text-align:center;transition:all 0.25s ease; }
    .str-badge.earned { border-color:rgba(245,158,11,0.4);background:rgba(245,158,11,0.06); }
    .str-badge:hover { transform:translateY(-3px); }
    .str-level { background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(6,182,212,0.08));
        border:1px solid rgba(99,102,241,0.25);border-radius:18px;padding:20px;margin-bottom:16px; }
    </style>""", unsafe_allow_html=True)

    ss1,ss2,ss3 = st.tabs(["🏅 Badges & XP","📈 Level System","🎯 Challenges"])

    with ss1:
        xp = st.session_state.get("user_xp", 0)
        level_name,level_emoji = "Novice","⚪"
        for threshold,name,emoji in LEVELS:
            if xp >= threshold: level_name,level_emoji = name,emoji
        next_thresh = next((t for t,n,e in LEVELS if t>xp), LEVELS[-1][0])
        progress = min(100, int((xp%max(1,next_thresh))/max(1,next_thresh)*100)) if next_thresh>xp else 100

        st.markdown(f"""
        <div class="str-level">
            <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">
                <div style="font-size:2.5rem;">{level_emoji}</div>
                <div>
                    <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#fff;">{level_name}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#818cf8;">{xp} XP</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.06);border-radius:100px;height:8px;overflow:hidden;">
                <div style="background:linear-gradient(90deg,#6366f1,#06b6d4);width:{progress}%;height:100%;border-radius:100px;transition:width 0.5s ease;"></div>
            </div>
            <div style="font-size:0.72rem;color:rgba(255,255,255,0.3);margin-top:6px;">Next level: {next_thresh} XP</div>
        </div>""", unsafe_allow_html=True)

        earned = st.session_state.get("earned_badges",["first"])
        bcols = st.columns(5)
        for i, badge in enumerate(BADGES):
            is_earned = badge["id"] in earned
            with bcols[i%5]:
                st.markdown(f"""
                <div class="str-badge {'earned' if is_earned else ''}">
                    <div style="font-size:2rem;{'filter:grayscale(1);opacity:0.4' if not is_earned else ''}">{badge['emoji']}</div>
                    <div style="font-size:0.72rem;font-weight:700;color:{'rgba(245,158,11,0.9)' if is_earned else 'rgba(255,255,255,0.3)'};margin-top:6px;">{badge['name']}</div>
                    <div style="font-size:0.62rem;color:rgba(255,255,255,0.3);">+{badge['xp']} XP</div>
                </div>""", unsafe_allow_html=True)
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        if col_a.button("➕ Add 25 XP (Study Session)", key="ss_add_xp", use_container_width=True, type="primary"):
            st.session_state.user_xp = xp + 25
            st.success("🎉 +25 XP earned!"); st.rerun()
        if col_b.button("🔄 Reset XP", key="ss_reset", use_container_width=True):
            st.session_state.user_xp = 0; st.rerun()

    with ss2:
        st.markdown("**📈 XP Level Progression**")
        for threshold, name, emoji in LEVELS:
            is_current = False
            curr_t = next((t for t,n,e in LEVELS if xp >= t), 0)
            is_current = threshold == curr_t
            reached = xp >= threshold
            st.markdown(f"""
            <div style="background:rgba(10,14,30,{'0.9' if is_current else '0.5'});
                border:1px solid rgba({'245,158,11' if is_current else '255,255,255'},{'0.4' if is_current else '0.07'});
                border-radius:12px;padding:12px 18px;margin-bottom:8px;display:flex;align-items:center;gap:14px;
                {'opacity:1' if reached else 'opacity:0.4'};">
                <div style="font-size:1.5rem;">{emoji if reached else '🔒'}</div>
                <div style="flex:1;">
                    <div style="font-weight:700;color:rgba(255,255,255,{'0.9' if reached else '0.4'});">{name}</div>
                    <div style="font-size:0.72rem;font-family:JetBrains Mono,monospace;color:rgba(255,255,255,0.3);">{threshold} XP required</div>
                </div>
                {'<span style="color:#fbbf24;font-size:0.78rem;font-weight:700;">CURRENT</span>' if is_current else ''}
            </div>""", unsafe_allow_html=True)

    with ss3:
        st.markdown("**🎯 Daily Challenges**")
        challenges = [
            ("Study for 30 minutes","🕐","+15 XP"),("Complete 3 Pomodoros","🍅","+30 XP"),
            ("Review yesterday's notes","📝","+10 XP"),("Solve 5 practice problems","✏️","+25 XP"),
            ("Teach someone a concept","🤝","+20 XP"),("Read 10 pages","📖","+15 XP"),
        ]
        if "ss_completed" not in st.session_state: st.session_state.ss_completed = set()
        for ch_name, ch_emoji, ch_xp in challenges:
            done = ch_name in st.session_state.ss_completed
            c1,c2 = st.columns([4,1])
            c1.markdown(f"""
            <div style="background:rgba(10,14,30,{'0.9' if done else '0.6'});border:1px solid rgba({'16,185,129' if done else '255,255,255'},{'0.3' if done else '0.07'});
                border-radius:12px;padding:12px 16px;margin-bottom:6px;display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.3rem;">{'✅' if done else ch_emoji}</span>
                <div>
                    <div style="font-size:0.88rem;color:rgba(255,255,255,{'0.9' if not done else '0.5'});{'text-decoration:line-through' if done else ''}">{ch_name}</div>
                    <div style="font-size:0.7rem;color:#10b981;">{ch_xp}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            if not done:
                if c2.button("✓", key=f"ss_ch_{ch_name[:8]}", use_container_width=True):
                    st.session_state.ss_completed.add(ch_name)
                    xp_gain = int(ch_xp.replace("+","").replace(" XP",""))
                    st.session_state.user_xp = st.session_state.get("user_xp",0) + xp_gain
                    st.balloons(); st.rerun()


# ═══════════════════════════════════
# STEPS 21-22: STUDY INSIGHTS ADDON
# ═══════════════════════════════════

def render_insights_addon():
    st.markdown("""
    <style>
    .si-card { background:rgba(10,14,30,0.8);border:1px solid rgba(99,102,241,0.15);
        border-radius:14px;padding:18px;margin-bottom:12px; }
    .si-tag-hard { background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);
        border-radius:8px;padding:3px 10px;font-size:0.72rem;color:#fca5a5;display:inline-block;margin:2px; }
    .si-tag-ok { background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.2);
        border-radius:8px;padding:3px 10px;font-size:0.72rem;color:#fde68a;display:inline-block;margin:2px; }
    .si-tag-easy { background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
        border-radius:8px;padding:3px 10px;font-size:0.72rem;color:#6ee7b7;display:inline-block;margin:2px; }
    </style>""", unsafe_allow_html=True)

    si1,si2,si3,si4 = st.tabs([
        "🧠 Spaced Repetition","🔍 Knowledge Gap","📈 Performance Predictor","💡 Study Recommendations"
    ])

    with si1:
        st.markdown("**🧠 Spaced Repetition Scheduler**")
        st.markdown("""
        <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.2);
            border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:0.84rem;color:rgba(255,255,255,0.6);line-height:1.65;">
        📅 Spaced repetition is the most effective study technique. Review cards at increasing intervals:
        <strong style="color:#818cf8;">1d → 3d → 7d → 14d → 30d</strong>
        </div>""", unsafe_allow_html=True)

        if "sr_cards" not in st.session_state: st.session_state.sr_cards = []
        c1,c2 = st.columns(2)
        new_concept = c1.text_input("Concept/Topic:", key="si_concept")
        new_subject = c2.text_input("Subject:", key="si_subject")
        difficulty = st.selectbox("Difficulty rating:", ["Easy","Medium","Hard","Very Hard"], key="si_diff")

        if new_concept and st.button("➕ Add to Spaced Repetition", key="si_add", use_container_width=True):
            interval_map = {"Easy":7,"Medium":3,"Hard":1,"Very Hard":1}
            next_review = datetime.date.today() + datetime.timedelta(days=interval_map[difficulty])
            st.session_state.sr_cards.append({
                "concept":new_concept,"subject":new_subject,"difficulty":difficulty,
                "next_review":str(next_review),"reviews":0,"interval":interval_map[difficulty]
            })
            st.success(f"✅ Added! Next review: {next_review}"); st.rerun()

        today = str(datetime.date.today())
        due_cards = [c for c in st.session_state.sr_cards if c["next_review"] <= today]
        if due_cards:
            st.markdown(f"**🔴 {len(due_cards)} cards due for review today:**")
            for card in due_cards:
                col_a, col_b, col_c = st.columns([3,1,1])
                col_a.markdown(f"""
                <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);
                    border-radius:10px;padding:10px 14px;">
                    <div style="font-weight:700;color:rgba(255,255,255,0.9);">{card['concept']}</div>
                    <div style="font-size:0.72rem;color:rgba(255,255,255,0.4);">{card['subject']} · {card['difficulty']}</div>
                </div>""", unsafe_allow_html=True)
                if col_b.button("✅ Remembered", key=f"si_rem_{card['concept'][:8]}"):
                    new_interval = min(card["interval"]*2, 30)
                    card["next_review"] = str(datetime.date.today()+datetime.timedelta(days=new_interval))
                    card["interval"] = new_interval; card["reviews"] += 1; st.rerun()
                if col_c.button("❌ Forgot", key=f"si_for_{card['concept'][:8]}"):
                    card["next_review"] = str(datetime.date.today()+datetime.timedelta(days=1))
                    card["interval"] = 1; st.rerun()

        upcoming = [c for c in st.session_state.sr_cards if c["next_review"] > today]
        if upcoming:
            st.markdown(f"**📅 {len(upcoming)} upcoming reviews:**")
            for c in sorted(upcoming, key=lambda x: x["next_review"])[:5]:
                st.markdown(f"• **{c['concept']}** — review on `{c['next_review']}`")

    with si2:
        st.markdown("**🔍 Knowledge Gap Analyzer**")
        subject = st.text_input("Subject/Course:", placeholder="e.g. Machine Learning, Organic Chemistry", key="si_gap_sub")
        known = st.text_area("What you know well:", placeholder="One topic per line...", height=100, key="si_gap_known")
        struggled = st.text_area("What you struggled with:", placeholder="One topic per line...", height=100, key="si_gap_struggle")

        if subject and st.button("🔍 Analyze Knowledge Gaps", type="primary", use_container_width=True, key="si_gap_btn"):
            with st.spinner("Analyzing your knowledge..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Analyze knowledge gaps for {subject}. Strong areas: {known}. Weak areas: {struggled}. Provide: 1) Full topic list for {subject}, 2) Mark each as Mastered/Partial/Gap, 3) Priority topics to study, 4) Specific resources for weak areas, 5) Estimated time to fill gaps."
                    result = generate(p, max_tokens=2500, temperature=0.3)
                    st.markdown(result)
                except Exception as e: st.error(str(e))

    with si3:
        st.markdown("**📈 Exam Performance Predictor**")
        ex_subject = st.text_input("Subject:", key="si_pred_sub")
        ex_date = st.date_input("Exam Date:", key="si_pred_date")
        ex_scores = st.text_area("Recent test scores (comma separated):",
                                  placeholder="e.g. 72, 68, 75, 80", key="si_pred_scores")
        study_hours = st.number_input("Daily study hours:", min_value=0.5, max_value=16.0, value=3.0, step=0.5, key="si_pred_hours")

        if ex_subject and ex_scores and st.button("📈 Predict Performance", type="primary", use_container_width=True, key="si_pred_btn"):
            try:
                scores = [float(s.strip()) for s in ex_scores.split(",") if s.strip()]
                avg = sum(scores)/len(scores)
                trend = (scores[-1]-scores[0]) if len(scores)>1 else 0
                days_left = (ex_date - datetime.date.today()).days
                from utils.ai_engine import generate
                p = f"Predict exam performance for {ex_subject}. Data: scores={scores}, avg={avg:.1f}%, trend={trend:+.1f}%, days left={days_left}, daily study hours={study_hours}. Predict: expected score range, confidence level, what score is achievable, daily targets, and improvement plan."
                result = generate(p, max_tokens=1500, temperature=0.3)
                st.markdown(result)
            except Exception as e: st.error(str(e))

    with si4:
        st.markdown("**💡 Personalized Study Recommendations**")
        sr_subject = st.text_input("What are you studying?", key="si_rec_sub")
        sr_level = st.selectbox("Your level:", ["Beginner","Intermediate","Advanced"], key="si_rec_lvl")
        sr_goal = st.text_input("Your goal:", placeholder="e.g. Pass GATE exam, Get A+ grade", key="si_rec_goal")
        sr_time = st.number_input("Hours per day available:", min_value=0.5, max_value=12.0, value=2.0, step=0.5, key="si_rec_time")

        if sr_subject and st.button("💡 Get Personalized Plan", type="primary", use_container_width=True, key="si_rec_btn"):
            with st.spinner("Creating personalized plan..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Create a personalized study plan: Subject={sr_subject}, Level={sr_level}, Goal={sr_goal}, Available time={sr_time}h/day. Include: week-by-week schedule, best resources (free & paid), study techniques for this subject, practice materials, and milestones to track progress."
                    result = generate(p, max_tokens=3000, temperature=0.3)
                    st.markdown(result)
                    st.download_button("📥 Save Study Plan", result, "study_plan.txt", key="si_rec_dl")
                except Exception as e: st.error(str(e))
