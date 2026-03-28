"""contest_engine.py — Real-time Competitive Programming Contest Tracker.

Connects to Codeforces and AtCoder to fetch upcoming academic competitions.
"""

import requests
import streamlit as st
from datetime import datetime, timezone
from typing import List, Dict

@st.cache_data(ttl=3600)
def fetch_upcoming_contests() -> List[Dict]:
    """Fetch and normalize upcoming coding contests from Codeforces."""
    contests = []
    
    # 1. Codeforces API
    try:
        cf_url = "https://codeforces.com/api/contest.list?gym=false"
        resp = requests.get(cf_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] == "OK":
                for c in data["result"]:
                    if c["phase"] == "BEFORE":
                        # Convert timestamp
                        dt = datetime.fromtimestamp(c["startTimeSeconds"], tz=timezone.utc)
                        contests.append({
                            "platform": "Codeforces",
                            "name": c["name"],
                            "start_time": dt.strftime("%Y-%m-%d %H:%M UTC"),
                            "duration": f"{c['durationSeconds'] // 3600}h",
                            "link": f"https://codeforces.com/contests/{c['id']}"
                        })
    except Exception:
        pass

    # Sort by start time
    contests.sort(key=lambda x: x["start_time"])
    return contests[:10]

def render_contest_sidebar():
    """Renders the contest list in a streamlined UI block."""
    contests = fetch_upcoming_contests()
    if not contests:
        st.info("No upcoming contests found.")
        return

    st.markdown("### 🏆 Upcoming Contests")
    for c in contests:
        with st.expander(f"{c['platform']}: {c['name'][:30]}..."):
            st.write(f"⌚ **Start:** {c['start_time']}")
            st.write(f"⏳ **Duration:** {c['duration']}")
            st.link_button("Go to Contest", c["link"])
