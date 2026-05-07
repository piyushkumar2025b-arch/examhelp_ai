"""
contest_engine.py — Contest Tracker for ExamHelp AI v3.0
Platforms: Codeforces ⚡, LeetCode 🟨, AtCoder 🔵, CodeChef 🍴, HackerEarth 🔶, HackerRank 🟢
v3.0 fixes:
  - Cards now render as styled HTML (no raw code showing)
  - Live contests properly detected and displayed
  - Real-time countdown via st.empty + st_autorefresh or manual loop
  - start/end times shown as human-readable local strings
  - Reminders persist in session_state
"""
from __future__ import annotations
import streamlit as st
import requests
import json
import time
import datetime
from typing import List, Dict, Optional

HEADERS = {"User-Agent": "ExamHelpAI/3.0"}

PLATFORM_META = {
    "Codeforces":  {"icon": "⚡", "color": "#3b82f6"},
    "LeetCode":    {"icon": "🟨", "color": "#f59e0b"},
    "AtCoder":     {"icon": "🔵", "color": "#06b6d4"},
    "CodeChef":    {"icon": "🍴", "color": "#a16207"},
    "HackerEarth": {"icon": "🔶", "color": "#f97316"},
    "HackerRank":  {"icon": "🟢", "color": "#22c55e"},
}

# ─────────────────────────────────────────────────────────────────────────────
# TIME HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _parse_iso(s: str) -> Optional[datetime.datetime]:
    if not s:
        return None
    try:
        s = s.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
        except Exception:
            return None


def _duration_str(seconds: int) -> str:
    if seconds <= 0:
        return "TBD"
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    if h >= 24:
        d = h // 24
        return f"{d}d {h % 24}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def _countdown_str(dt: Optional[datetime.datetime]) -> str:
    if not dt:
        return "Unknown"
    now = _now_utc()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    delta = dt - now
    if delta.total_seconds() <= 0:
        return "Started"
    total_s = int(delta.total_seconds())
    d, rem = divmod(total_s, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d > 0:
        return f"{d}d {h}h {m}m"
    if h > 0:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def _fmt_dt(dt: Optional[datetime.datetime]) -> str:
    if not dt:
        return "TBD"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.strftime("%b %d, %H:%M UTC")


def _status(start: Optional[datetime.datetime], end: Optional[datetime.datetime]) -> str:
    now = _now_utc()
    if start and start.tzinfo is None:
        start = start.replace(tzinfo=datetime.timezone.utc)
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=datetime.timezone.utc)
    if not start:
        return "upcoming"
    if start > now:
        return "upcoming"
    if end and end < now:
        return "ended"
    return "ongoing"


# ─────────────────────────────────────────────────────────────────────────────
# FETCHERS
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_codeforces() -> List[Dict]:
    contests = []
    try:
        r = requests.get("https://codeforces.com/api/contest.list", timeout=8, headers=HEADERS)
        if r.status_code != 200:
            return []
        for c in r.json().get("result", [])[:40]:
            if c.get("phase") == "FINISHED":
                continue
            start_ts = c.get("startTimeSeconds")
            dur_s    = c.get("durationSeconds", 0)
            start_dt = datetime.datetime.fromtimestamp(start_ts, tz=datetime.timezone.utc) if start_ts else None
            end_dt   = (start_dt + datetime.timedelta(seconds=dur_s)) if (start_dt and dur_s) else None
            st_      = _status(start_dt, end_dt)
            contests.append({
                "platform":      "Codeforces",
                "name":          c.get("name", ""),
                "start_time":    start_dt.isoformat() if start_dt else "",
                "end_time":      end_dt.isoformat() if end_dt else "",
                "start_fmt":     _fmt_dt(start_dt),
                "end_fmt":       _fmt_dt(end_dt),
                "duration":      _duration_str(dur_s),
                "link":          f"https://codeforces.com/contest/{c.get('id', '')}",
                "status":        st_,
                "platform_icon": "⚡",
                "_start_dt":     start_dt,
                "_end_dt":       end_dt,
            })
    except Exception:
        pass
    return contests


def _fetch_leetcode() -> List[Dict]:
    contests = []
    try:
        r = requests.get(
            "https://leetcode.com/graphql",
            json={"query": "{ allContests { title titleSlug startTime duration } }"},
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=8
        )
        if r.status_code != 200:
            return []
        for c in r.json().get("data", {}).get("allContests", [])[:20]:
            start_ts = c.get("startTime", 0)
            dur_s    = c.get("duration", 0)
            start_dt = datetime.datetime.fromtimestamp(start_ts, tz=datetime.timezone.utc) if start_ts else None
            end_dt   = (start_dt + datetime.timedelta(seconds=dur_s)) if (start_dt and dur_s) else None
            st_      = _status(start_dt, end_dt)
            if st_ == "ended":
                continue
            contests.append({
                "platform":      "LeetCode",
                "name":          c.get("title", ""),
                "start_time":    start_dt.isoformat() if start_dt else "",
                "end_time":      end_dt.isoformat() if end_dt else "",
                "start_fmt":     _fmt_dt(start_dt),
                "end_fmt":       _fmt_dt(end_dt),
                "duration":      _duration_str(dur_s),
                "link":          f"https://leetcode.com/contest/{c.get('titleSlug', '')}",
                "status":        st_,
                "platform_icon": "🟨",
                "_start_dt":     start_dt,
                "_end_dt":       end_dt,
            })
    except Exception:
        pass
    return contests


def _fetch_atcoder() -> List[Dict]:
    contests = []
    try:
        r = requests.get("https://atcoder.jp/contests/", timeout=8, headers=HEADERS)
        if r.status_code != 200:
            return []
        import re
        rows = re.findall(
            r'<tr[^>]*>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*><a href="([^"]+)">([^<]+)</a>',
            r.text
        )
        for start_text, link_path, name in rows[:15]:
            link = f"https://atcoder.jp{link_path}"
            try:
                start_dt = datetime.datetime.strptime(start_text.strip(), "%Y-%m-%d %H:%M:%S+0900")
                start_dt = start_dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
            except Exception:
                start_dt = None
            end_dt = (start_dt + datetime.timedelta(hours=2)) if start_dt else None
            st_    = _status(start_dt, end_dt)
            if st_ == "ended":
                continue
            contests.append({
                "platform":      "AtCoder",
                "name":          name.strip(),
                "start_time":    start_dt.isoformat() if start_dt else "",
                "end_time":      end_dt.isoformat() if end_dt else "",
                "start_fmt":     _fmt_dt(start_dt),
                "end_fmt":       _fmt_dt(end_dt),
                "duration":      "2h",
                "link":          link,
                "status":        st_,
                "platform_icon": "🔵",
                "_start_dt":     start_dt,
                "_end_dt":       end_dt,
            })
    except Exception:
        pass
    return contests


def _fetch_codechef() -> List[Dict]:
    contests = []
    try:
        r = requests.get(
            "https://www.codechef.com/api/list/contests/all",
            timeout=8, headers=HEADERS
        )
        if r.status_code != 200:
            return []
        data = r.json()
        # present_contests first so live ones appear
        for section in ["present_contests", "future_contests"]:
            for c in data.get(section, [])[:10]:
                code      = c.get("contest_code", "")
                start_str = c.get("contest_start_date_iso", c.get("contest_start_date", ""))
                end_str   = c.get("contest_end_date_iso",   c.get("contest_end_date",   ""))
                dur_s     = c.get("contest_duration", 0)
                start_dt  = _parse_iso(start_str)
                end_dt    = _parse_iso(end_str)
                st_       = _status(start_dt, end_dt)
                contests.append({
                    "platform":      "CodeChef",
                    "name":          c.get("contest_name", code),
                    "start_time":    start_dt.isoformat() if start_dt else "",
                    "end_time":      end_dt.isoformat()   if end_dt   else "",
                    "start_fmt":     _fmt_dt(start_dt),
                    "end_fmt":       _fmt_dt(end_dt),
                    "duration":      _duration_str(int(dur_s) * 60 if dur_s else 0),
                    "link":          f"https://www.codechef.com/{code}",
                    "status":        st_,
                    "platform_icon": "🍴",
                    "_start_dt":     start_dt,
                    "_end_dt":       end_dt,
                })
    except Exception:
        pass
    return contests


def _fetch_hackerearth() -> List[Dict]:
    contests = []
    try:
        r = requests.get("https://www.hackerearth.com/chrome-extension/events/", timeout=8, headers=HEADERS)
        if r.status_code != 200:
            return []
        data = r.json()
        for c in (data.get("response", []) or [])[:10]:
            start_str = c.get("start_utc", c.get("start_tz", ""))
            end_str   = c.get("end_utc",   c.get("end_tz",   ""))
            start_dt  = _parse_iso(start_str)
            end_dt    = _parse_iso(end_str)
            dur_s     = (end_dt - start_dt).total_seconds() if (start_dt and end_dt) else 0
            st_       = _status(start_dt, end_dt)
            if st_ == "ended":
                continue
            contests.append({
                "platform":      "HackerEarth",
                "name":          c.get("title", "HackerEarth Challenge"),
                "start_time":    start_dt.isoformat() if start_dt else "",
                "end_time":      end_dt.isoformat()   if end_dt   else "",
                "start_fmt":     _fmt_dt(start_dt),
                "end_fmt":       _fmt_dt(end_dt),
                "duration":      _duration_str(int(dur_s)),
                "link":          c.get("url", "https://www.hackerearth.com/challenges/"),
                "status":        st_,
                "platform_icon": "🔶",
                "_start_dt":     start_dt,
                "_end_dt":       end_dt,
            })
    except Exception:
        pass
    return contests


def _fetch_hackerrank() -> List[Dict]:
    contests = []
    try:
        r = requests.get(
            "https://www.hackerrank.com/rest/contests/upcoming?limit=10",
            timeout=8, headers=HEADERS
        )
        if r.status_code != 200:
            return []
        for c in r.json().get("models", [])[:10]:
            slug      = c.get("slug", "")
            start_str = c.get("start_time", "")
            end_str   = c.get("end_time", "")
            start_dt  = _parse_iso(start_str)
            end_dt    = _parse_iso(end_str)
            dur_s     = (end_dt - start_dt).total_seconds() if (start_dt and end_dt) else 0
            contests.append({
                "platform":      "HackerRank",
                "name":          c.get("name", slug),
                "start_time":    start_dt.isoformat() if start_dt else "",
                "end_time":      end_dt.isoformat()   if end_dt   else "",
                "start_fmt":     _fmt_dt(start_dt),
                "end_fmt":       _fmt_dt(end_dt),
                "duration":      _duration_str(int(dur_s)),
                "link":          f"https://www.hackerrank.com/contests/{slug}",
                "status":        _status(start_dt, end_dt),
                "platform_icon": "🟢",
                "_start_dt":     start_dt,
                "_end_dt":       end_dt,
            })
    except Exception:
        pass
    return contests


# ─────────────────────────────────────────────────────────────────────────────
# UNIFIED FETCH
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all_contests(platforms: Optional[List[str]] = None) -> List[Dict]:
    all_fetchers = {
        "Codeforces":  _fetch_codeforces,
        "LeetCode":    _fetch_leetcode,
        "AtCoder":     _fetch_atcoder,
        "CodeChef":    _fetch_codechef,
        "HackerEarth": _fetch_hackerearth,
        "HackerRank":  _fetch_hackerrank,
    }
    if platforms:
        fetchers = {k: v for k, v in all_fetchers.items() if k in platforms}
    else:
        fetchers = all_fetchers

    all_contests = []
    seen_names = set()
    for name, fn in fetchers.items():
        try:
            for c in fn():
                key = f"{c['platform']}-{c['name']}"
                if key not in seen_names:
                    seen_names.add(key)
                    all_contests.append(c)
        except Exception:
            pass

    all_contests.sort(
        key=lambda x: x.get("_start_dt") or datetime.datetime(2099, 1, 1, tzinfo=datetime.timezone.utc)
    )
    return all_contests


def get_ongoing_contests() -> List[Dict]:
    return [c for c in fetch_all_contests() if c["status"] == "ongoing"]


def get_upcoming_contests(hours_ahead: int = 72) -> List[Dict]:
    cutoff = _now_utc() + datetime.timedelta(hours=hours_ahead)
    result = []
    for c in fetch_all_contests():
        if c["status"] != "upcoming":
            continue
        start_dt = c.get("_start_dt")
        if start_dt and start_dt <= cutoff:
            result.append(c)
        elif not start_dt:
            result.append(c)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# CARD HTML BUILDER  (renders properly — no raw code shown)
# ─────────────────────────────────────────────────────────────────────────────

def _build_card_html(c: Dict, show_reminder_btn: bool = True) -> str:
    meta   = PLATFORM_META.get(c["platform"], {"icon": "🏆", "color": "#6b7280"})
    color  = meta["color"]
    icon   = meta["icon"]
    is_live = c["status"] == "ongoing"

    live_badge = (
        '<span style="display:inline-flex;align-items:center;gap:5px;'
        'padding:3px 10px;border-radius:100px;'
        'background:rgba(239,68,68,0.15);color:#ef4444;'
        'border:1px solid rgba(239,68,68,0.35);'
        'font-size:.68rem;font-weight:700;letter-spacing:2px;'
        'animation:livePulse 1.5s ease infinite;">● LIVE</span>'
        if is_live else ""
    )

    cd_str = _countdown_str(c.get("_start_dt")) if not is_live else "Live now!"
    start_label = f"🗓 {c.get('start_fmt', c.get('start_time','TBD'))}"
    end_label   = f"🏁 {c.get('end_fmt',   c.get('end_time',  ''))}" if c.get("end_fmt") or c.get("end_time") else ""

    btn_label = "Participate →" if is_live else "Register →"

    reminder_key = f"{c['platform']}-{c['name']}"
    reminders    = st.session_state.get("ct_reminders", [])
    already_set  = any(r.get("key") == reminder_key for r in reminders)

    reminder_html = ""
    if show_reminder_btn and not is_live:
        rb_color  = "#10b981" if already_set else "#818cf8"
        rb_border = "rgba(16,185,129,0.3)" if already_set else "rgba(99,102,241,0.3)"
        rb_bg     = "rgba(16,185,129,0.08)" if already_set else "rgba(99,102,241,0.08)"
        rb_label  = "✅ Reminder Set" if already_set else "⏰ Set Reminder"
        reminder_html = f"""
<div style="margin-top:8px;">
  <span style="display:inline-block;padding:4px 12px;border-radius:8px;
    border:1px solid {rb_border};background:{rb_bg};color:{rb_color};
    font-size:.73rem;font-family:monospace;">
    {rb_label}
  </span>
</div>"""

    border_color = "rgba(239,68,68,0.25)" if is_live else "rgba(255,255,255,0.07)"
    bg_extra     = "linear-gradient(135deg,rgba(239,68,68,0.04),rgba(13,17,23,1))" if is_live else "rgba(13,17,23,0.8)"

    return f"""
<div style="background:{bg_extra};border:1px solid {border_color};border-radius:16px;
  padding:18px 20px;margin-bottom:10px;
  display:flex;align-items:flex-start;justify-content:space-between;
  flex-wrap:wrap;gap:12px;
  transition:border-color .2s;">
  <div style="flex:1;min-width:200px;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
      <span style="padding:3px 10px;border-radius:100px;
        background:{color}22;color:{color};
        font-size:.7rem;font-weight:700;font-family:monospace;">
        {icon} {c['platform']}
      </span>
      {live_badge}
    </div>
    <div style="font-weight:800;font-size:1rem;color:#f8fafc;margin-bottom:8px;line-height:1.35;">
      {c['name'][:80]}{'…' if len(c['name'])>80 else ''}
    </div>
    <div style="display:flex;gap:14px;flex-wrap:wrap;font-size:.8rem;color:#64748b;">
      <span>⏱ {c['duration']}</span>
      <span style="color:{'#ef4444' if is_live else '#e2e8f0'};font-weight:{'700' if is_live else '400'};">
        {'● ' if is_live else ''}{'⏳ ' if not is_live else ''}{cd_str}
      </span>
      <span>{start_label}</span>
      {f'<span>{end_label}</span>' if end_label else ''}
    </div>
    {reminder_html}
  </div>
  <a href="{c['link']}" target="_blank"
     style="display:inline-block;padding:10px 20px;border-radius:12px;
     background:linear-gradient(135deg,{color},{color}99);
     color:#fff;font-size:.82rem;font-weight:700;
     text-decoration:none;white-space:nowrap;align-self:center;">
    {btn_label}
  </a>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR WIDGET
# ─────────────────────────────────────────────────────────────────────────────

def render_contest_sidebar():
    st.sidebar.markdown("### 🏆 Upcoming Contests")
    try:
        contests = get_upcoming_contests(hours_ahead=48)[:5]
        if not contests:
            st.sidebar.caption("No upcoming contests found.")
        for c in contests:
            meta = PLATFORM_META.get(c["platform"], {"icon": "🏆", "color": "#6b7280"})
            st.sidebar.markdown(
                f"{meta['icon']} **{c['name'][:30]}**  \n"
                f"⏰ {_countdown_str(c.get('_start_dt'))}  \n"
                f"[Register →]({c['link']})"
            )
    except Exception:
        st.sidebar.caption("Contest fetch unavailable.")


# ─────────────────────────────────────────────────────────────────────────────
# FULL PAGE UI  — v3 (renders cards as real HTML, not code)
# ─────────────────────────────────────────────────────────────────────────────

def render_contest_page():
    st.markdown("""
<style>
@keyframes livePulse{0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.3)}50%{box-shadow:0 0 0 6px rgba(239,68,68,0)}}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.07),rgba(16,185,129,0.04));
border:1px solid rgba(99,102,241,0.15);border-radius:20px;padding:28px 32px;margin-bottom:24px;">
  <div style="font-family:monospace;font-size:10px;letter-spacing:4px;
  color:rgba(99,102,241,0.7);text-transform:uppercase;margin-bottom:8px;">LIVE TRACKER · ALL PLATFORMS</div>
  <div style="font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:6px;">🏆 Contest Tracker</div>
  <div style="color:rgba(255,255,255,0.45);font-size:.9rem;">
    ⚡ Codeforces · 🟨 LeetCode · 🔵 AtCoder · 🍴 CodeChef · 🔶 HackerEarth · 🟢 HackerRank
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────
    with st.expander("🔧 Platform & Duration Filters", expanded=False):
        sel_platforms = st.multiselect(
            "Platforms",
            list(PLATFORM_META.keys()),
            default=list(PLATFORM_META.keys()),
            key="ct_platforms"
        )
        dur_filter = st.radio(
            "Duration", ["All", "≤2h", "2-5h", "5h+"],
            horizontal=True, key="ct_dur_filter"
        )

    col_ref, col_auto = st.columns([1, 1])
    refresh_btn  = col_ref.button("🔄 Refresh Now", use_container_width=True, key="ct_refresh")
    auto_refresh = col_auto.checkbox("⏱ Auto-refresh (30s)", key="ct_auto_refresh")

    # ── Auto-refresh ──────────────────────────────────────────────────────
    if auto_refresh:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=30_000, key="ct_tick")
        except ImportError:
            st.caption("Install streamlit-autorefresh for live ticking.")

    # ── Load contests (cached 5 min) ──────────────────────────────────────
    cache_key      = "ct_cache"
    cache_time_key = "ct_cache_time"
    now_ts         = time.time()

    if refresh_btn or cache_key not in st.session_state or \
       (now_ts - st.session_state.get(cache_time_key, 0)) > 300:
        with st.spinner("⏳ Fetching live data from all platforms…"):
            contests = fetch_all_contests(sel_platforms if sel_platforms else None)
        st.session_state[cache_key]      = contests
        st.session_state[cache_time_key] = now_ts
    else:
        contests = st.session_state[cache_key]
        if sel_platforms:
            contests = [c for c in contests if c["platform"] in sel_platforms]

    # Duration filter
    def _dur_ok(c):
        d = c.get("duration", "")
        if dur_filter == "All":
            return True
        try:
            total_h = 0
            if "d" in d:
                total_h = int(d.split("d")[0]) * 24
            elif "h" in d:
                total_h = int(d.split("h")[0])
            elif "m" in d:
                total_h = int(d.split("m")[0]) / 60
        except Exception:
            return True
        if dur_filter == "≤2h":  return total_h <= 2
        if dur_filter == "2-5h": return 2 < total_h <= 5
        if dur_filter == "5h+":  return total_h > 5
        return True

    contests = [c for c in contests if _dur_ok(c)]

    live     = [c for c in contests if c["status"] == "ongoing"]
    upcoming = [c for c in contests if c["status"] == "upcoming"]

    # ── Stats ─────────────────────────────────────────────────────────────
    now_dt       = _now_utc()
    today_c      = _now_utc() + datetime.timedelta(hours=24)
    week_c       = _now_utc() + datetime.timedelta(days=7)
    today_list   = [c for c in upcoming if c.get("_start_dt") and c["_start_dt"] <= today_c]
    week_list    = [c for c in upcoming if c.get("_start_dt") and c["_start_dt"] <= week_c]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🔴 Live Now",      len(live))
    m2.metric("📅 Today",         len(today_list))
    m3.metric("📆 This Week",     len(week_list))
    m4.metric("📋 Total Tracked", len(contests))

    st.markdown("---")

    if "ct_reminders" not in st.session_state:
        st.session_state.ct_reminders = []

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_live, tab_upcoming, tab_reminders = st.tabs([
        f"🔴 Live Now ({len(live)})",
        f"📅 Upcoming ({len(upcoming)})",
        f"⏰ Reminders ({len(st.session_state.ct_reminders)})",
    ])

    # ── Live tab ──────────────────────────────────────────────────────────
    with tab_live:
        if not live:
            st.info("🔍 No contests are live right now. Check back soon or hit Refresh.")
        else:
            html_parts = [_build_card_html(c, show_reminder_btn=False) for c in live]
            st.markdown("".join(html_parts), unsafe_allow_html=True)

    # ── Upcoming tab ──────────────────────────────────────────────────────
    with tab_upcoming:
        if not upcoming:
            st.info("No upcoming contests found. Try refreshing or expanding platform filters.")
        else:
            # Render cards, then add Streamlit reminder buttons below each
            for c in upcoming[:30]:
                st.markdown(_build_card_html(c, show_reminder_btn=False), unsafe_allow_html=True)
                reminder_key = f"{c['platform']}-{c['name']}"
                already = any(r.get("key") == reminder_key for r in st.session_state.ct_reminders)
                btn_label = "✅ Reminder Set" if already else "⏰ Set Reminder"
                safe_key  = f"rem_{abs(hash(reminder_key)) % 10**9}"
                if st.button(btn_label, key=safe_key, use_container_width=False):
                    if already:
                        st.session_state.ct_reminders = [
                            r for r in st.session_state.ct_reminders if r.get("key") != reminder_key
                        ]
                        st.rerun()
                    else:
                        meta = PLATFORM_META.get(c["platform"], {"icon": "🏆"})
                        st.session_state.ct_reminders.append({
                            "key":        reminder_key,
                            "name":       c["name"],
                            "platform":   c["platform"],
                            "icon":       meta["icon"],
                            "start_time": c.get("start_time", ""),
                            "start_fmt":  c.get("start_fmt", ""),
                            "link":       c["link"],
                        })
                        st.success(f"✅ Reminder set for {c['name']}")
                        st.rerun()

    # ── Reminders tab ─────────────────────────────────────────────────────
    with tab_reminders:
        reminders = st.session_state.ct_reminders
        if not reminders:
            st.info("No reminders set. Go to Upcoming and click 'Set Reminder'.")
        else:
            st.markdown(f"**{len(reminders)} reminder(s) set:**")
            for i, rem in enumerate(reminders):
                start_dt = _parse_iso(rem.get("start_time", ""))
                cd       = _countdown_str(start_dt)
                col_r, col_del = st.columns([6, 1])
                with col_r:
                    st.markdown(f"""
<div style="background:rgba(15,23,42,0.6);border:1px solid rgba(99,102,241,0.2);
border-radius:12px;padding:14px 18px;margin-bottom:8px;">
  <div style="font-weight:700;color:#f8fafc;margin-bottom:4px;">
    {rem['icon']} {rem['name']}
  </div>
  <div style="font-size:.78rem;color:#94a3b8;">
    {rem['platform']} &middot; ⏳ {cd}
    &middot; 🗓 {rem.get('start_fmt', rem.get('start_time',''))}
    &middot; <a href="{rem['link']}" target="_blank" style="color:#818cf8;">Open →</a>
  </div>
</div>""", unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"del_rem_{i}"):
                        st.session_state.ct_reminders.pop(i)
                        st.rerun()

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="ct_back"):
        st.session_state.app_mode = "chat"
        st.rerun()
