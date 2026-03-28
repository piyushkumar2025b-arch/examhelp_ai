"""contest_engine.py — Real-time Competitive Programming Contest Tracker.
Sources: Codeforces (official API), AtCoder (unofficial scrape), LeetCode (unofficial API).
"""

import requests
import streamlit as st
from datetime import datetime, timezone
from typing import List, Dict


@st.cache_data(ttl=1800)  # 30-min cache
def fetch_upcoming_contests() -> List[Dict]:
    contests = []

    # 1. Codeforces — official public API, no key needed
    try:
        resp = requests.get("https://codeforces.com/api/contest.list?gym=false", timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "OK":
                for c in data["result"]:
                    if c["phase"] == "BEFORE":
                        dt = datetime.fromtimestamp(c["startTimeSeconds"], tz=timezone.utc)
                        contests.append({
                            "platform": "Codeforces",
                            "name": c["name"],
                            "start_time": dt.strftime("%Y-%m-%d %H:%M UTC"),
                            "duration": f"{c['durationSeconds'] // 3600}h {(c['durationSeconds'] % 3600) // 60}m",
                            "link": f"https://codeforces.com/contests/{c['id']}"
                        })
    except Exception:
        pass

    # 2. AtCoder — unofficial Kenkoooo API (free, no key)
    try:
        resp = requests.get(
            "https://kenkoooo.com/atcoder/resources/contests.json",
            timeout=5
        )
        if resp.status_code == 200:
            for c in resp.json():
                start_ts = c.get("start_epoch_second", 0)
                duration = c.get("duration_second", 0)
                if start_ts > datetime.now(tz=timezone.utc).timestamp():
                    dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
                    contests.append({
                        "platform": "AtCoder",
                        "name": c.get("title", ""),
                        "start_time": dt.strftime("%Y-%m-%d %H:%M UTC"),
                        "duration": f"{duration // 3600}h {(duration % 3600) // 60}m",
                        "link": f"https://atcoder.jp/contests/{c.get('id', '')}"
                    })
    except Exception:
        pass

    # 3. LeetCode — unofficial public contest endpoint
    try:
        headers = {"Content-Type": "application/json",
                   "User-Agent": "Mozilla/5.0"}
        payload = {"query": "{ contestUpcomingContests { title startTime duration titleSlug } }"}
        resp = requests.post("https://leetcode.com/graphql", json=payload,
                             headers=headers, timeout=5)
        if resp.status_code == 200:
            for c in resp.json().get("data", {}).get("contestUpcomingContests", []):
                dt = datetime.fromtimestamp(c["startTime"], tz=timezone.utc)
                dur = c["duration"]
                contests.append({
                    "platform": "LeetCode",
                    "name": c["title"],
                    "start_time": dt.strftime("%Y-%m-%d %H:%M UTC"),
                    "duration": f"{dur // 3600}h {(dur % 3600) // 60}m",
                    "link": f"https://leetcode.com/contest/{c['titleSlug']}"
                })
    except Exception:
        pass

    # Sort by start time, return top 15
    try:
        contests.sort(key=lambda x: x["start_time"])
    except Exception:
        pass
    return contests[:15]


def render_contest_sidebar():
    contests = fetch_upcoming_contests()
    if not contests:
        st.info("No upcoming contests found.")
        return
    st.markdown("### 🏆 Upcoming Contests")
    for c in contests:
        with st.expander(f"{c['platform']}: {c['name'][:35]}"):
            st.write(f"⌚ **Start:** {c['start_time']}")
            st.write(f"⏳ **Duration:** {c['duration']}")
            st.link_button("Go to Contest →", c["link"])
