"""contests_addon.py — Step 27: Contest finder with difficulty filter + reminder"""
import streamlit as st, urllib.request, json

CONTESTS = [
    {"name":"Codeforces Round","url":"https://codeforces.com/contests","diff":"Advanced","type":"Coding","emoji":"💻"},
    {"name":"LeetCode Weekly","url":"https://leetcode.com/contest","diff":"Intermediate","type":"Coding","emoji":"🧩"},
    {"name":"HackerRank Challenges","url":"https://hackerrank.com/contests","diff":"Beginner","type":"Coding","emoji":"🔧"},
    {"name":"Kaggle Competitions","url":"https://kaggle.com/competitions","diff":"Advanced","type":"Data Science","emoji":"📊"},
    {"name":"Google Kickstart","url":"https://codingcompetitions.withgoogle.com","diff":"Advanced","type":"Coding","emoji":"🌐"},
    {"name":"ICPC (ACM)","url":"https://icpc.global","diff":"Expert","type":"Coding","emoji":"🏆"},
    {"name":"NASA Space Apps","url":"https://spaceapps.nasa.gov","diff":"Intermediate","type":"Hackathon","emoji":"🚀"},
    {"name":"DevPost Hackathons","url":"https://devpost.com/hackathons","diff":"Beginner","type":"Hackathon","emoji":"⚡"},
    {"name":"Math Olympiad (IMO)","url":"https://imo-official.org","diff":"Expert","type":"Math","emoji":"📐"},
    {"name":"Physics Olympiad","url":"https://ipho-unofficial.org","diff":"Expert","type":"Science","emoji":"⚛️"},
    {"name":"Quora Quiz","url":"https://quora.com","diff":"Beginner","type":"Quiz","emoji":"❓"},
    {"name":"Science Olympiad","url":"https://soinc.org","diff":"Intermediate","type":"Science","emoji":"🔬"},
]

def render_contests_addon():
    st.markdown("""
    <style>
    .ct-card{background:rgba(10,14,30,0.8);border:1px solid rgba(255,255,255,0.07);
        border-radius:13px;padding:14px 16px;margin-bottom:8px;
        display:flex;align-items:center;gap:14px;}
    .ct-card:hover{border-color:rgba(99,102,241,0.35);}
    </style>""", unsafe_allow_html=True)

    ca1, ca2 = st.tabs(["🏆 Browse Contests", "🔔 My Reminders"])

    with ca1:
        c1, c2 = st.columns(2)
        diff_f = c1.selectbox("Difficulty:", ["All","Beginner","Intermediate","Advanced","Expert"], key="ct_diff")
        type_f = c2.selectbox("Type:", ["All","Coding","Data Science","Hackathon","Math","Science","Quiz"], key="ct_type")
        search = st.text_input("🔍 Search:", key="ct_search")

        shown = 0
        for c in CONTESTS:
            if diff_f != "All" and c["diff"] != diff_f: continue
            if type_f != "All" and c["type"] != type_f: continue
            if search and search.lower() not in c["name"].lower(): continue
            shown += 1
            col_a, col_b, col_c = st.columns([4,2,1])
            col_a.markdown(f"""
            <div class="ct-card">
                <span style="font-size:1.6rem;">{c['emoji']}</span>
                <div>
                    <div style="font-weight:700;color:rgba(255,255,255,0.9);">{c['name']}</div>
                    <div style="font-size:0.72rem;color:rgba(255,255,255,0.4);">{c['type']} · {c['diff']}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            col_b.markdown(f"[🔗 Open]({c['url']})", unsafe_allow_html=False)
            if col_c.button("🔔", key=f"ct_remind_{shown}", use_container_width=True):
                reminders = st.session_state.get("ct_reminders", [])
                if c["name"] not in reminders:
                    reminders.append(c["name"])
                    st.session_state.ct_reminders = reminders
                    st.success(f"✅ Reminder set for {c['name']}")

        if shown == 0:
            st.info("No contests match your filters.")

    with ca2:
        reminders = st.session_state.get("ct_reminders", [])
        if reminders:
            st.markdown(f"**🔔 {len(reminders)} Contest Reminder(s):**")
            for r in reminders:
                col_a, col_b = st.columns([4,1])
                col_a.markdown(f"• {r}")
                if col_b.button("❌", key=f"ct_del_{r[:8]}"):
                    reminders.remove(r); st.session_state.ct_reminders = reminders; st.rerun()
        else:
            st.info("No reminders set. Browse contests and click 🔔 to add.")
