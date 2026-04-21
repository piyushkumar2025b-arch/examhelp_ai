"""
profile_engine.py — Developer Profile Hub for ExamHelp AI
- Create/load profile by custom ID (stored as JSON)
- Link: GitHub, LeetCode, Codeforces, GeeksForGeeks, LinkedIn
- Fetch live stats from free APIs
- AI Coach chat (contextual, profile-aware)
- Profile card export (download as markdown)
"""
from __future__ import annotations
import streamlit as st
import requests
import json
import os
from pathlib import Path
from typing import Optional, Dict

PROFILES_DIR = Path(__file__).parent / "profiles"
HEADERS = {"User-Agent": "ExamHelpAI/1.0"}


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE STORAGE
# ─────────────────────────────────────────────────────────────────────────────

def _profile_path(user_id: str) -> Path:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c for c in user_id if c.isalnum() or c in "-_")[:32]
    return PROFILES_DIR / f"{safe_id}.json"


def load_profile(user_id: str) -> Optional[Dict]:
    p = _profile_path(user_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_profile(user_id: str, data: Dict):
    p = _profile_path(user_id)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_profiles() -> list:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return [f.stem for f in PROFILES_DIR.glob("*.json")]


# ─────────────────────────────────────────────────────────────────────────────
# PLATFORM STAT FETCHERS (all free, no auth needed)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_github_stats(username: str) -> Dict:
    try:
        r = requests.get(f"https://api.github.com/users/{username}", headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return {"error": f"User not found ({r.status_code})"}
        u = r.json()

        # Get top language from repos
        r2 = requests.get(f"https://api.github.com/users/{username}/repos?per_page=30&sort=pushed",
                          headers=HEADERS, timeout=6)
        lang_count: Dict[str, int] = {}
        if r2.status_code == 200:
            for repo in r2.json():
                lang = repo.get("language")
                if lang:
                    lang_count[lang] = lang_count.get(lang, 0) + 1
        top_lang = max(lang_count, key=lang_count.get) if lang_count else "N/A"

        return {
            "username":     username,
            "name":         u.get("name", username),
            "bio":          u.get("bio", ""),
            "public_repos": u.get("public_repos", 0),
            "followers":    u.get("followers", 0),
            "following":    u.get("following", 0),
            "avatar_url":   u.get("avatar_url", ""),
            "top_language": top_lang,
            "profile_url":  u.get("html_url", f"https://github.com/{username}"),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_leetcode_stats(username: str) -> Dict:
    try:
        r = requests.get(
            f"https://leetcode-stats-api.herokuapp.com/{username}",
            headers=HEADERS, timeout=8
        )
        if r.status_code != 200:
            return {"error": f"LeetCode user not found"}
        d = r.json()
        if d.get("status") == "error":
            return {"error": d.get("message", "Not found")}
        return {
            "username":        username,
            "total_solved":    d.get("totalSolved", 0),
            "easy_solved":     d.get("easySolved", 0),
            "medium_solved":   d.get("mediumSolved", 0),
            "hard_solved":     d.get("hardSolved", 0),
            "acceptance_rate": d.get("acceptanceRate", 0),
            "ranking":         d.get("ranking", 0),
            "profile_url":     f"https://leetcode.com/{username}",
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_codeforces_stats(handle: str) -> Dict:
    try:
        r = requests.get(
            f"https://codeforces.com/api/user.info?handles={handle}",
            headers=HEADERS, timeout=8
        )
        if r.status_code != 200:
            return {"error": "CF API error"}
        data = r.json()
        if data.get("status") != "OK":
            return {"error": data.get("comment", "Not found")}
        u = data["result"][0]
        return {
            "handle":      u.get("handle", handle),
            "rating":      u.get("rating", 0),
            "max_rating":  u.get("maxRating", 0),
            "rank":        u.get("rank", "unrated"),
            "max_rank":    u.get("maxRank", "unrated"),
            "avatar_url":  u.get("avatar", ""),
            "profile_url": f"https://codeforces.com/profile/{handle}",
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_gfg_stats(username: str) -> Dict:
    """Scrape GeeksForGeeks profile (unofficial, may break on site changes)."""
    try:
        r = requests.get(
            f"https://auth.geeksforgeeks.org/user/{username}/profile",
            headers={**HEADERS, "Accept": "text/html"}, timeout=8
        )
        if r.status_code != 200:
            return {"error": f"GFG profile not found"}

        import re
        text = r.text

        score_m = re.search(r'"coding_score"\s*:\s*(\d+)', text)
        solved_m = re.search(r'"problem_solved_today"\s*:\s*(\d+)', text) or \
                   re.search(r'(\d+)\s*[Pp]roblems?\s*[Ss]olved', text)
        inst_m = re.search(r'"institution"\s*:\s*"([^"]+)"', text)

        return {
            "username":      username,
            "coding_score":  int(score_m.group(1)) if score_m else 0,
            "problems_solved": int(solved_m.group(1)) if solved_m else 0,
            "institution":   inst_m.group(1) if inst_m else "N/A",
            "profile_url":   f"https://www.geeksforgeeks.org/user/{username}/",
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# AI COACH
# ─────────────────────────────────────────────────────────────────────────────

def _ai_generate(prompt: str, max_tokens: int = 800) -> str:
    try:
        from utils import ai_engine
        return ai_engine.generate(prompt, max_tokens=max_tokens)
    except Exception:
        try:
            from utils.groq_client import chat_with_groq
            return chat_with_groq([{"role": "user", "content": prompt}], max_tokens=max_tokens)
        except Exception:
            return "AI unavailable. Please check your API key."


def ai_coach_response(profile: Dict, stats: Dict, user_question: str) -> str:
    profile_summary = json.dumps({
        "name": profile.get("name", ""),
        "github": stats.get("github", {}),
        "leetcode": stats.get("leetcode", {}),
        "codeforces": stats.get("codeforces", {}),
    }, indent=2)[:2000]

    prompt = (
        f"You are a senior software engineering career coach and mentor. "
        f"The user's developer profile:\n{profile_summary}\n\n"
        f"User's question: {user_question}\n\n"
        f"Give specific, actionable advice. Be encouraging but honest. "
        f"Reference their actual stats when relevant. Keep response under 300 words."
    )
    return _ai_generate(prompt, max_tokens=600)


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS SCORE (weighted)
# ─────────────────────────────────────────────────────────────────────────────

def compute_progress_score(stats: Dict) -> float:
    """Compute a 0-100 developer progress score from all platform stats."""
    gh  = stats.get("github", {})
    lc  = stats.get("leetcode", {})
    cf  = stats.get("codeforces", {})
    gfg = stats.get("gfg", {})

    score = 0.0
    # GitHub (max 35 pts)
    if not gh.get("error"):
        score += min(gh.get("public_repos", 0) / 50, 1) * 15
        score += min(gh.get("followers", 0) / 100, 1) * 10
        score += 10  # just for being on GitHub
    # LeetCode (max 35 pts)
    if not lc.get("error"):
        score += min(lc.get("total_solved", 0) / 500, 1) * 20
        score += min(lc.get("hard_solved", 0) / 50, 1) * 15
    # Codeforces (max 20 pts)
    if not cf.get("error"):
        score += min(cf.get("rating", 0) / 2000, 1) * 20
    # GFG (max 10 pts)
    if not gfg.get("error"):
        score += min(gfg.get("coding_score", 0) / 500, 1) * 10

    return round(min(score, 100), 1)


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE CARD MARKDOWN EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def profile_to_markdown(profile: Dict, stats: Dict, score: float) -> str:
    gh  = stats.get("github", {})
    lc  = stats.get("leetcode", {})
    cf  = stats.get("codeforces", {})

    lines = [
        f"# 👤 Developer Profile: {profile.get('name', 'Unknown')}",
        f"**ID:** {profile.get('user_id', '')}  |  **Progress Score:** {score}/100",
        "",
        "## 🐙 GitHub",
    ]
    if not gh.get("error"):
        lines += [
            f"- **Repos:** {gh.get('public_repos', 0)}",
            f"- **Followers:** {gh.get('followers', 0)}",
            f"- **Top Language:** {gh.get('top_language', 'N/A')}",
            f"- [View Profile]({gh.get('profile_url', '')})",
        ]
    else:
        lines.append(f"- Not linked")

    lines += ["", "## 🟨 LeetCode"]
    if not lc.get("error"):
        lines += [
            f"- **Total Solved:** {lc.get('total_solved', 0)}",
            f"- **Easy:** {lc.get('easy_solved', 0)} / **Medium:** {lc.get('medium_solved', 0)} / **Hard:** {lc.get('hard_solved', 0)}",
            f"- **Global Rank:** #{lc.get('ranking', 'N/A')}",
            f"- [View Profile]({lc.get('profile_url', '')})",
        ]
    else:
        lines.append("- Not linked")

    lines += ["", "## ⚡ Codeforces"]
    if not cf.get("error"):
        lines += [
            f"- **Rating:** {cf.get('rating', 0)} (Max: {cf.get('max_rating', 0)})",
            f"- **Rank:** {cf.get('rank', 'unrated').title()}",
            f"- [View Profile]({cf.get('profile_url', '')})",
        ]
    else:
        lines.append("- Not linked")

    lines += ["", "---", "*Generated by ExamHelp AI*"]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT PAGE
# ─────────────────────────────────────────────────────────────────────────────

def render_profile_page():
    """Full Developer Profile Hub Streamlit page."""

    st.markdown("""
<style>
.stat-card{background:rgba(15,23,42,0.75);border:1px solid rgba(255,255,255,0.07);
border-radius:16px;padding:20px;text-align:center;transition:all .2s;}
.stat-card:hover{border-color:rgba(99,102,241,0.35);transform:translateY(-3px);}
.stat-val{font-size:2rem;font-weight:900;color:#a5b4fc;line-height:1;}
.stat-lbl{font-size:.75rem;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:1px;}
.plat-badge{display:inline-block;border-radius:100px;padding:4px 14px;
font-size:.75rem;font-weight:700;margin-right:6px;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(236,72,153,0.04));
border:1px solid rgba(99,102,241,0.15);border-radius:20px;padding:28px 32px;margin-bottom:24px;">
  <div style="font-family:monospace;font-size:10px;letter-spacing:4px;
  color:rgba(99,102,241,0.6);text-transform:uppercase;margin-bottom:8px;">DEVELOPER DASHBOARD</div>
  <div style="font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:6px;">👤 My Dev Profile</div>
  <div style="color:rgba(255,255,255,0.45);font-size:.9rem;">
    Link GitHub · LeetCode · Codeforces · GFG · Get personalized AI coaching
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Login / Register ──────────────────────────────────────────────────
    if "profile_loaded" not in st.session_state:
        st.session_state.profile_loaded = False
        st.session_state.profile_data = {}
        st.session_state.profile_stats = {}
        st.session_state.profile_user_id = ""
        st.session_state.coach_history = []

    if not st.session_state.profile_loaded:
        st.markdown("### 🔑 Login or Create Profile")
        col_id, col_btn = st.columns([3, 1])
        with col_id:
            user_id = st.text_input(
                "Profile ID (alphanumeric, choose any)",
                placeholder="e.g. piyush2025, devraj_xyz",
                key="prof_id_input"
            )
        with col_btn:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🔓 Load / Create", use_container_width=True, key="prof_login"):
                if user_id.strip():
                    uid = user_id.strip().lower().replace(" ", "_")
                    existing = load_profile(uid)
                    if existing:
                        st.session_state.profile_data = existing
                        st.success(f"✅ Welcome back, **{existing.get('name', uid)}**!")
                    else:
                        st.session_state.profile_data = {"user_id": uid, "name": uid}
                        save_profile(uid, st.session_state.profile_data)
                        st.success(f"✅ Profile created for **{uid}**!")
                    st.session_state.profile_user_id = uid
                    st.session_state.profile_loaded = True
                    st.rerun()

        existing_ids = list_profiles()
        if existing_ids:
            st.caption(f"Existing profiles: {', '.join(existing_ids[:10])}")
        return

    # ── Profile Tabs ──────────────────────────────────────────────────────
    profile  = st.session_state.profile_data
    user_id  = st.session_state.profile_user_id
    tab_dash, tab_edit, tab_coach, tab_export = st.tabs([
        "📊 Dashboard", "✏️ Edit Profile", "🤖 AI Coach", "📥 Export"
    ])

    # ── DASHBOARD ─────────────────────────────────────────────────────────
    with tab_dash:
        stats = st.session_state.profile_stats

        col_av, col_info = st.columns([1, 3])
        with col_av:
            gh_avatar = stats.get("github", {}).get("avatar_url", "")
            cf_avatar = stats.get("codeforces", {}).get("avatar_url", "")
            avatar = gh_avatar or cf_avatar or profile.get("photo_url", "")
            if avatar:
                st.image(avatar, width=100)
            else:
                st.markdown("""
<div style="width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);
display:flex;align-items:center;justify-content:center;font-size:2.5rem;color:#fff;">
  👤
</div>""", unsafe_allow_html=True)

        with col_info:
            st.markdown(f"## {profile.get('name', user_id)}")
            if profile.get("bio"):
                st.caption(profile["bio"])
            progress_score = compute_progress_score(stats) if stats else 0
            st.progress(progress_score / 100, text=f"Dev Score: {progress_score}/100")

        st.markdown("---")

        if not stats:
            st.info("No platform data loaded yet. Go to **✏️ Edit Profile** to link your accounts and fetch stats.")
        else:
            # GitHub stats
            gh = stats.get("github", {})
            lc = stats.get("leetcode", {})
            cf = stats.get("codeforces", {})
            gfg = stats.get("gfg", {})

            st.markdown("#### 🐙 GitHub")
            if not gh.get("error"):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f'<div class="stat-card"><div class="stat-val">{gh.get("public_repos",0)}</div><div class="stat-lbl">Repos</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="stat-card"><div class="stat-val">{gh.get("followers",0)}</div><div class="stat-lbl">Followers</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="stat-card"><div class="stat-val">{gh.get("following",0)}</div><div class="stat-lbl">Following</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="stat-card"><div class="stat-val" style="font-size:1.1rem">{gh.get("top_language","N/A")}</div><div class="stat-lbl">Top Lang</div></div>', unsafe_allow_html=True)
            else:
                st.caption(f"GitHub: {gh.get('error')}")

            st.markdown("#### 🟨 LeetCode")
            if not lc.get("error"):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f'<div class="stat-card"><div class="stat-val">{lc.get("total_solved",0)}</div><div class="stat-lbl">Total Solved</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="stat-card"><div class="stat-val" style="color:#22c55e">{lc.get("easy_solved",0)}</div><div class="stat-lbl">Easy</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="stat-card"><div class="stat-val" style="color:#f59e0b">{lc.get("medium_solved",0)}</div><div class="stat-lbl">Medium</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="stat-card"><div class="stat-val" style="color:#ef4444">{lc.get("hard_solved",0)}</div><div class="stat-lbl">Hard</div></div>', unsafe_allow_html=True)
                st.caption(f"Global Rank: #{lc.get('ranking','N/A')} · Acceptance: {lc.get('acceptance_rate',0):.1f}%")
            else:
                st.caption(f"LeetCode: {lc.get('error')}")

            st.markdown("#### ⚡ Codeforces")
            if not cf.get("error"):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="stat-card"><div class="stat-val">{cf.get("rating",0)}</div><div class="stat-lbl">Rating</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="stat-card"><div class="stat-val">{cf.get("max_rating",0)}</div><div class="stat-lbl">Max Rating</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="stat-card"><div class="stat-val" style="font-size:1rem">{cf.get("rank","unrated").title()}</div><div class="stat-lbl">Rank</div></div>', unsafe_allow_html=True)
            else:
                st.caption(f"Codeforces: {cf.get('error')}")

            if not gfg.get("error") and gfg.get("coding_score"):
                st.markdown("#### 🟢 GeeksForGeeks")
                c1, c2 = st.columns(2)
                c1.metric("Coding Score", gfg.get("coding_score", 0))
                c2.metric("Problems Solved", gfg.get("problems_solved", 0))

    # ── EDIT PROFILE ──────────────────────────────────────────────────────
    with tab_edit:
        st.markdown("### ✏️ Profile Details")
        with st.form("profile_edit_form"):
            name     = st.text_input("Display Name", value=profile.get("name", user_id))
            bio      = st.text_area("Bio / Tagline", value=profile.get("bio", ""), height=80)
            photo    = st.text_input("Profile Photo URL (optional)", value=profile.get("photo_url", ""),
                                     placeholder="https://avatars.githubusercontent.com/...")

            st.markdown("---")
            st.markdown("#### 🔗 Link Your Platforms")
            gh_user  = st.text_input("GitHub Username",      value=profile.get("github_username", ""))
            lc_user  = st.text_input("LeetCode Username",    value=profile.get("leetcode_username", ""))
            cf_user  = st.text_input("Codeforces Handle",    value=profile.get("cf_handle", ""))
            gfg_user = st.text_input("GeeksForGeeks Username", value=profile.get("gfg_username", ""))
            li_url   = st.text_input("LinkedIn URL (optional)", value=profile.get("linkedin_url", ""),
                                     placeholder="https://linkedin.com/in/yourname")

            st.markdown("---")
            st.markdown("#### 🔑 Your API Keys (Optional — used in all tools)")
            own_gemini = st.text_input("Your Gemini API Key", type="password",
                                       value=profile.get("own_gemini_key", ""),
                                       placeholder="AIza...")
            own_yt     = st.text_input("Your YouTube API Key", type="password",
                                       value=profile.get("own_yt_key", ""),
                                       placeholder="AIza...")

            submitted = st.form_submit_button("💾 Save & Fetch Stats", use_container_width=True, type="primary")

        if submitted:
            updated = {
                **profile,
                "user_id": user_id,
                "name": name,
                "bio": bio,
                "photo_url": photo,
                "github_username":   gh_user,
                "leetcode_username": lc_user,
                "cf_handle":         cf_user,
                "gfg_username":      gfg_user,
                "linkedin_url":      li_url,
                "own_gemini_key":    own_gemini,
                "own_yt_key":        own_yt,
            }
            save_profile(user_id, updated)
            st.session_state.profile_data = updated

            with st.spinner("Fetching your stats from all platforms..."):
                stats = {}
                if gh_user:
                    stats["github"] = fetch_github_stats(gh_user)
                if lc_user:
                    stats["leetcode"] = fetch_leetcode_stats(lc_user)
                if cf_user:
                    stats["codeforces"] = fetch_codeforces_stats(cf_user)
                if gfg_user:
                    stats["gfg"] = fetch_gfg_stats(gfg_user)

                st.session_state.profile_stats = stats

            st.success("✅ Profile saved and stats fetched!")

            if own_gemini:
                try:
                    from utils.key_manager import store_key
                    store_key("GEMINI_API_KEY", own_gemini)
                    st.info("✅ Your Gemini key saved for this session.")
                except Exception:
                    pass

            st.rerun()

    # ── AI COACH ──────────────────────────────────────────────────────────
    with tab_coach:
        st.markdown("### 🤖 AI Career Coach")
        st.caption("Ask anything about your coding journey — AI has your full profile context.")

        if not st.session_state.profile_stats:
            st.info("Link your platforms in **✏️ Edit Profile** first so the AI can give personalized advice.")

        # Chat history display
        for msg in st.session_state.coach_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_input := st.chat_input("Ask your AI coach...", key="coach_input"):
            st.session_state.coach_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("AI thinking..."):
                    reply = ai_coach_response(
                        st.session_state.profile_data,
                        st.session_state.profile_stats,
                        user_input
                    )
                st.markdown(reply)
            st.session_state.coach_history.append({"role": "assistant", "content": reply})

        quick_prompts = [
            "What should I focus on to improve?",
            "Compare my LeetCode vs Codeforces skill",
            "Give me a 30-day study plan",
            "What's my weakest area?",
        ]
        st.markdown("**Quick prompts:**")
        cols = st.columns(2)
        for i, qp in enumerate(quick_prompts):
            with cols[i % 2]:
                if st.button(qp, key=f"qp_{i}", use_container_width=True):
                    st.session_state.coach_history.append({"role": "user", "content": qp})
                    reply = ai_coach_response(
                        st.session_state.profile_data,
                        st.session_state.profile_stats, qp
                    )
                    st.session_state.coach_history.append({"role": "assistant", "content": reply})
                    st.rerun()

    # ── EXPORT ────────────────────────────────────────────────────────────
    with tab_export:
        st.markdown("### 📥 Export Profile Card")
        score = compute_progress_score(st.session_state.profile_stats)
        md_card = profile_to_markdown(
            st.session_state.profile_data,
            st.session_state.profile_stats,
            score
        )
        st.markdown(md_card)
        st.download_button(
            "⬇️ Download Profile Card (.md)",
            md_card.encode(),
            file_name=f"profile_{user_id}.md",
            mime="text/markdown",
            use_container_width=True,
            key="prof_dl"
        )

    # ── Logout button ─────────────────────────────────────────────────────
    st.markdown("---")
    col_lo, col_bk = st.columns(2)
    with col_lo:
        if st.button("🔓 Logout", use_container_width=True, key="prof_logout"):
            for k in ["profile_loaded", "profile_data", "profile_stats", "profile_user_id", "coach_history"]:
                st.session_state.pop(k, None)
            st.rerun()
    with col_bk:
        if st.button("💬 Back to Chat", use_container_width=True, key="prof_back"):
            st.session_state.app_mode = "chat"
            st.rerun()
