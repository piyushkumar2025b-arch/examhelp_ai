"""profile_addon.py — Step 30: GitHub stats, coding portfolio, skills radar"""
import streamlit as st, urllib.request, json, io

def _github_stats(username: str) -> dict:
    try:
        url = f"https://api.github.com/users/{username}"
        req = urllib.request.Request(url, headers={"User-Agent":"ExamHelp/1.0","Accept":"application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=6) as r:
            user = json.loads(r.read().decode())
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=stars"
        req2 = urllib.request.Request(repos_url, headers={"User-Agent":"ExamHelp/1.0"})
        with urllib.request.urlopen(req2, timeout=6) as r2:
            repos = json.loads(r2.read().decode())
        total_stars = sum(r.get("stargazers_count",0) for r in repos)
        languages = {}
        for r in repos:
            lang = r.get("language")
            if lang: languages[lang] = languages.get(lang, 0) + 1
        top_repos = sorted(repos, key=lambda x: x.get("stargazers_count",0), reverse=True)[:5]
        return {"name":user.get("name",""),"bio":user.get("bio",""),"followers":user.get("followers",0),
                "following":user.get("following",0),"public_repos":user.get("public_repos",0),
                "stars":total_stars,"languages":languages,"top_repos":top_repos,
                "avatar":user.get("avatar_url",""),"location":user.get("location",""),
                "company":user.get("company",""),"blog":user.get("blog","")}
    except Exception as e:
        return {"error": str(e)}

def render_profile_addon():
    pa1, pa2, pa3 = st.tabs(["🐙 GitHub Stats", "📊 Skills Radar", "📄 Portfolio Export"])

    with pa1:
        gh_user = st.text_input("GitHub Username:", placeholder="e.g. torvalds", key="prof_gh_user")
        if gh_user and st.button("🐙 Fetch GitHub Stats", type="primary", use_container_width=True, key="prof_gh_btn"):
            with st.spinner(f"Fetching {gh_user}'s GitHub data..."):
                data = _github_stats(gh_user)
            if "error" in data:
                st.error(f"Error: {data['error']}. Make sure username is correct.")
            else:
                c1,c2,c3,c4 = st.columns(4)
                for col,(lbl,val,clr) in zip([c1,c2,c3,c4],[
                    ("Repos",data['public_repos'],"#6366f1"),
                    ("Stars",data['stars'],"#f59e0b"),
                    ("Followers",data['followers'],"#10b981"),
                    ("Following",data['following'],"#06b6d4"),
                ]):
                    col.markdown(f"""<div style="background:rgba(10,14,30,0.8);border:1px solid {clr}22;border-top:2px solid {clr};border-radius:12px;padding:14px;text-align:center;">
                        <div style="font-size:1.4rem;font-weight:800;color:{clr};">{val}</div>
                        <div style="font-size:0.6rem;letter-spacing:2px;color:rgba(255,255,255,0.3);">{lbl}</div>
                    </div>""", unsafe_allow_html=True)

                if data.get("name") or data.get("bio"):
                    st.markdown(f"**{data.get('name',gh_user)}** · {data.get('bio','')} · 📍 {data.get('location','')}")
                if data.get("blog"): st.markdown(f"🔗 {data['blog']}")

                if data.get("languages"):
                    st.markdown("**🗣️ Top Languages:**")
                    lang_sorted = sorted(data["languages"].items(), key=lambda x: x[1], reverse=True)[:6]
                    try:
                        import matplotlib; matplotlib.use("Agg")
                        import matplotlib.pyplot as plt
                        fig,ax = plt.subplots(figsize=(6,4),facecolor='#0a0e1e')
                        colors = ["#6366f1","#06b6d4","#10b981","#f59e0b","#ec4899","#8b5cf6"]
                        ax.pie([v for _,v in lang_sorted], labels=[k for k,_ in lang_sorted],
                               colors=colors[:len(lang_sorted)], autopct='%1.0f%%',
                               textprops={'color':'white','fontsize':9})
                        ax.set_facecolor('#0a0e1e'); fig.patch.set_facecolor('#0a0e1e')
                        plt.tight_layout(); buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=120,bbox_inches='tight')
                        buf.seek(0); plt.close(); st.image(buf, width=350)
                    except Exception: st.write({k:v for k,v in lang_sorted})

                if data.get("top_repos"):
                    st.markdown("**⭐ Top Repositories:**")
                    for repo in data["top_repos"]:
                        st.markdown(f"• **[{repo['name']}](https://github.com/{gh_user}/{repo['name']})** — ⭐ {repo.get('stargazers_count',0)} · {repo.get('description','')[:60] or 'No description'}")

                if st.button("🤖 AI Career Analysis from GitHub", key="prof_ai_career"):
                    with st.spinner("Analyzing..."):
                        try:
                            from utils.ai_engine import generate
                            langs = ", ".join(f"{k}({v})" for k,v in lang_sorted)
                            ans = generate(f"GitHub user '{gh_user}' has {data['public_repos']} repos, {data['stars']} stars, top languages: {langs}. Provide: career profile, suggested job roles, skill gaps, growth recommendations, and impressive stats to highlight on resume.")
                            st.markdown(ans)
                        except Exception as e: st.error(str(e))

    with pa2:
        st.markdown("**📊 Skills Radar Chart**")
        st.caption("Rate your skills (0-10) and see your radar chart")
        skill_names = ["Python","JavaScript","Data Science","Machine Learning","Web Dev","Algorithms","Databases","DevOps"]
        skills = {}
        s_cols = st.columns(4)
        for i, s in enumerate(skill_names):
            with s_cols[i%4]:
                skills[s] = st.slider(s, 0, 10, 5, key=f"prof_skill_{s}")

        if st.button("📊 Generate Radar Chart", type="primary", use_container_width=True, key="prof_radar"):
            try:
                import matplotlib; matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import numpy as np
                labels = list(skills.keys()); values = list(skills.values())
                N = len(labels); angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
                values += values[:1]; angles += angles[:1]
                fig,ax = plt.subplots(figsize=(7,7),subplot_kw=dict(polar=True),facecolor='#0a0e1e')
                ax.set_facecolor('#0f172a')
                ax.plot(angles, values, 'o-', linewidth=2, color='#6366f1')
                ax.fill(angles, values, alpha=0.25, color='#6366f1')
                ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, size=10, color='white')
                ax.set_ylim(0,10); ax.grid(color='#ffffff20')
                ax.tick_params(colors='#ffffff80')
                [sp.set_visible(False) for sp in ax.spines.values()]
                ax.set_title('My Skills Radar', color='#c7d2fe', fontsize=13, pad=20)
                plt.tight_layout(); buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=150,bbox_inches='tight')
                buf.seek(0); plt.close(); st.image(buf, use_container_width=True)
                st.download_button("📥 Save Chart", buf.getvalue(), "skills_radar.png", key="prof_radar_dl")
            except Exception as e: st.error(str(e))

    with pa3:
        st.markdown("**📄 Portfolio Generator**")
        name = st.text_input("Your Name:", key="prof_name")
        role = st.text_input("Role/Title:", placeholder="Full Stack Developer", key="prof_role")
        summary = st.text_area("Professional Summary:", height=80, key="prof_summary")
        projects = st.text_area("Projects (one per line):", height=80, key="prof_projects")
        skills_txt = st.text_input("Skills (comma separated):", key="prof_skills_txt")
        if name and st.button("📄 Generate Portfolio Bio", type="primary", use_container_width=True, key="prof_bio_btn"):
            with st.spinner("Generating..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Write a professional portfolio bio and README for: Name={name}, Role={role}, Summary={summary}, Projects={projects}, Skills={skills_txt}. Include: compelling intro, project descriptions, tech stack, GitHub README format.")
                    st.markdown(ans)
                    st.download_button("📥 Download Portfolio", ans, "portfolio.md", key="prof_bio_dl")
                except Exception as e: st.error(str(e))
