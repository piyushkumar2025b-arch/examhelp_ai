"""
youtube_player_addon.py — Free YouTube Music & Video Player
Search via Invidious API (no key) · Playback via YouTube iframe embed (free)
Queue system · Trending · Categories · Download links via yt-dlp (optional)
"""
import streamlit as st
import streamlit.components.v1 as components
import requests
import re
from typing import List, Dict, Optional

TIMEOUT = 10

# ── Multiple Invidious instances (fallback chain) ─────────────────────────────
INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.io.lol",
    "https://yt.artemislena.eu",
    "https://invidious.privacydev.net",
    "https://iv.melmac.space",
]

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@700&family=Space+Mono&display=swap');

.yt-hero {
    background: linear-gradient(135deg,#0a0014 0%,#130020 50%,#001428 100%);
    border: 1px solid rgba(255,0,0,0.2);
    border-radius: 22px; padding: 28px 36px; margin-bottom: 20px;
    position: relative; overflow: hidden;
}
.yt-hero::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(ellipse 60% 80% at 80% 20%,rgba(255,0,0,0.1) 0%,transparent 60%),
                radial-gradient(ellipse 40% 60% at 10% 80%,rgba(139,92,246,0.08) 0%,transparent 60%);
    pointer-events:none;
}
.yt-title {
    font-family:'Orbitron',monospace; font-size:clamp(18px,3vw,30px); font-weight:700;
    background:linear-gradient(90deg,#fff 0%,#ff6b6b 50%,#c4b5fd 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; margin:0 0 4px;
}
.yt-sub { font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px;
    color:rgba(255,255,255,.35); text-transform:uppercase; }
.yt-badge { display:inline-flex; align-items:center; gap:6px;
    background:rgba(255,0,0,0.1); border:1px solid rgba(255,0,0,0.3);
    border-radius:100px; padding:3px 12px; font-size:9px; letter-spacing:2px;
    font-family:'Space Mono',monospace; color:#fca5a5; }

/* Video grid card */
.vcard {
    background:rgba(15,23,42,.85); border:1px solid rgba(255,255,255,.06);
    border-radius:14px; overflow:hidden; transition:all .2s ease;
    cursor:pointer; margin-bottom:10px;
}
.vcard:hover { transform:translateY(-3px); border-color:rgba(255,0,0,.35);
    box-shadow:0 8px 30px rgba(255,0,0,.1); }
.vcard-thumb { position:relative; width:100%; aspect-ratio:16/9;
    background:#0f172a; overflow:hidden; }
.vcard-thumb img { width:100%; height:100%; object-fit:cover; display:block; }
.vcard-dur { position:absolute; bottom:5px; right:6px;
    background:rgba(0,0,0,.8); border-radius:4px; padding:1px 5px;
    font-size:10px; color:#fff; font-family:'Space Mono',monospace; }
.vcard-body { padding:9px 10px; }
.vcard-title { font-size:.82rem; font-weight:600; color:#fff; font-family:'Inter',sans-serif;
    line-height:1.3; margin-bottom:3px; }
.vcard-meta { font-size:.7rem; color:rgba(255,255,255,.38); font-family:'Space Mono',monospace; }

/* Now Playing */
.np-panel {
    background:rgba(15,23,42,.9); border:1px solid rgba(255,0,0,.15);
    border-radius:18px; padding:20px; margin-bottom:16px;
}
.np-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px;
    color:rgba(255,0,0,.5); text-transform:uppercase; margin-bottom:8px; }
.np-title { font-family:'Inter',sans-serif; font-size:1rem; font-weight:700;
    color:#fff; margin-bottom:2px; }
.np-channel { font-size:.75rem; color:rgba(255,255,255,.4);
    font-family:'Space Mono',monospace; }

/* Queue */
.q-item { display:flex; gap:10px; align-items:center;
    background:rgba(255,255,255,.03); border-radius:10px; padding:8px 10px;
    margin-bottom:6px; cursor:pointer; transition:.15s; }
.q-item:hover { background:rgba(255,0,0,.08); }
.q-item.active { background:rgba(255,0,0,.12); border:1px solid rgba(255,0,0,.25); }
.q-thumb { width:52px; height:36px; border-radius:6px; object-fit:cover;
    background:#1e293b; flex-shrink:0; }
.q-title { font-size:.75rem; font-weight:600; color:rgba(255,255,255,.85);
    font-family:'Inter',sans-serif; line-height:1.3; }
.q-meta { font-size:.65rem; color:rgba(255,255,255,.35);
    font-family:'Space Mono',monospace; }

/* Category pills */
.cat-pills { display:flex; flex-wrap:wrap; gap:6px; margin:10px 0; }
.cat-pill { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08);
    border-radius:100px; padding:4px 14px; font-size:.72rem;
    color:rgba(255,255,255,.55); cursor:pointer; transition:.15s;
    font-family:'Inter',sans-serif; }
.cat-pill:hover, .cat-pill.active { background:rgba(255,0,0,.12);
    border-color:rgba(255,0,0,.3); color:#fca5a5; }
</style>"""

CATEGORIES = [
    "🔥 Trending Music","💿 Lo-Fi","🎸 Rock","🎵 Pop","🎤 Hip-Hop",
    "🎻 Classical","🧘 Meditation","⚡ Electronic","🌊 Chillwave",
    "💃 Bollywood","🎷 Jazz","🌙 Night Drive",
]

CAT_QUERIES = {
    "🔥 Trending Music":  "trending music 2024",
    "💿 Lo-Fi":           "lofi hip hop music",
    "🎸 Rock":            "best rock songs",
    "🎵 Pop":             "top pop songs 2024",
    "🎤 Hip-Hop":         "hip hop rap music",
    "🎻 Classical":       "classical music relaxing",
    "🧘 Meditation":      "meditation music calm",
    "⚡ Electronic":      "electronic dance music",
    "🌊 Chillwave":       "chillwave synthwave music",
    "💃 Bollywood":       "bollywood songs 2024",
    "🎷 Jazz":            "smooth jazz music",
    "🌙 Night Drive":     "night drive music playlist",
}


# ─────────────────────────────────────────────────────────────────────────────
# Invidious API helpers
# ─────────────────────────────────────────────────────────────────────────────

def _invidious_get(path: str, params: dict) -> Optional[dict]:
    """Try each Invidious instance until one works."""
    for base in INVIDIOUS_INSTANCES:
        try:
            r = requests.get(f"{base}{path}", params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue
    return None


def search_youtube(query: str, page: int = 1, sort: str = "relevance") -> List[Dict]:
    """
    Search YouTube via Invidious API — no key needed.
    Returns list of video dicts.
    """
    data = _invidious_get("/api/v1/search", {
        "q": query, "type": "video", "sort_by": sort,
        "page": page, "region": "US",
    })
    if not data:
        return []
    results = []
    for v in data:
        if v.get("type") != "video":
            continue
        vid_id = v.get("videoId", "")
        thumb = f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"
        # Duration formatting
        length = v.get("lengthSeconds", 0)
        dur = f"{length//60}:{length%60:02d}" if length else ""
        results.append({
            "id":        vid_id,
            "title":     v.get("title", ""),
            "channel":   v.get("author", ""),
            "views":     v.get("viewCount", 0),
            "duration":  dur,
            "thumb":     thumb,
            "published": v.get("publishedText", ""),
        })
    return results


def get_trending_music(region: str = "US") -> List[Dict]:
    """Get trending music videos from Invidious."""
    data = _invidious_get("/api/v1/trending", {"type": "music", "region": region})
    if not data:
        return search_youtube("trending music 2024")
    results = []
    for v in (data if isinstance(data, list) else []):
        vid_id = v.get("videoId", "")
        length = v.get("lengthSeconds", 0)
        dur = f"{length//60}:{length%60:02d}" if length else ""
        results.append({
            "id":       vid_id,
            "title":    v.get("title", ""),
            "channel":  v.get("author", ""),
            "views":    v.get("viewCount", 0),
            "duration": dur,
            "thumb":    f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
            "published": v.get("publishedText", ""),
        })
    return results


def fmt_views(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.0f}K"
    return str(n)


# ─────────────────────────────────────────────────────────────────────────────
# YouTube iframe embed helper
# ─────────────────────────────────────────────────────────────────────────────

def _yt_embed_html(video_id: str, autoplay: bool = True, height: int = 430) -> str:
    """Return full HTML page with YouTube iframe — for use with components.html()."""
    auto = "1" if autoplay else "0"
    return f"""<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0014; }}
  .wrap {{
    border-radius: 16px; overflow: hidden;
    box-shadow: 0 8px 40px rgba(255,0,0,.25);
    width: 100%; height: {height}px;
  }}
  iframe {{ width:100%; height:{height}px; border:none; display:block; }}
</style>
</head>
<body>
<div class="wrap">
  <iframe
    src="https://www.youtube.com/embed/{video_id}?autoplay={auto}&rel=0&modestbranding=1&color=red&fs=1"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
    allowfullscreen>
  </iframe>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main render function
# ─────────────────────────────────────────────────────────────────────────────

def render_youtube_player():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Hero ──
    st.markdown("""
<div class="yt-hero">
  <div class="yt-badge">🎵 &nbsp;FREE YOUTUBE PLAYER &nbsp;·&nbsp; NO LOGIN NEEDED</div>
  <div class="yt-title">🎧 YouTube Music Player</div>
  <div class="yt-sub">Search · Play · Queue · Trending · All Free</div>
</div>""", unsafe_allow_html=True)

    # ── Init session state ──
    for k, v in {
        "yt_results": [], "yt_query": "", "yt_now": None,
        "yt_queue": [], "yt_page": 1,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Search bar ──
    c1, c2, c3 = st.columns([5, 1, 1])
    with c1:
        query = st.text_input("🔍 Search YouTube:", placeholder="song name, artist, playlist…",
                              key="yt_search_q", label_visibility="collapsed")
    with c2:
        sort_by = st.selectbox("Sort:", ["relevance","upload_date","view_count","rating"],
                               key="yt_sort", label_visibility="collapsed")
    with c3:
        do_search = st.button("🔍 Search", type="primary", use_container_width=True, key="yt_go")

    if do_search and query:
        with st.spinner("Searching YouTube…"):
            st.session_state["yt_results"] = search_youtube(query, sort=sort_by)
            st.session_state["yt_query"]   = query
            st.session_state["yt_page"]    = 1

    # ── Category pills ──
    st.markdown('<div class="cat-pills">', unsafe_allow_html=True)
    cat_cols = st.columns(len(CATEGORIES[:6]))
    for i, cat in enumerate(CATEGORIES[:6]):
        with cat_cols[i]:
            if st.button(cat, key=f"yt_cat_{i}", use_container_width=True):
                with st.spinner(f"Loading {cat}…"):
                    q = CAT_QUERIES[cat]
                    st.session_state["yt_results"] = search_youtube(q, sort="relevance")
                    st.session_state["yt_query"]   = q
    cat_cols2 = st.columns(len(CATEGORIES[6:]))
    for i, cat in enumerate(CATEGORIES[6:]):
        with cat_cols2[i]:
            if st.button(cat, key=f"yt_cat2_{i}", use_container_width=True):
                with st.spinner(f"Loading {cat}…"):
                    q = CAT_QUERIES[cat]
                    st.session_state["yt_results"] = search_youtube(q)
                    st.session_state["yt_query"]   = q
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Trending button ──
    if st.button("🔥 Load Trending Music", key="yt_trending"):
        with st.spinner("Fetching trending music…"):
            st.session_state["yt_results"] = get_trending_music()
            st.session_state["yt_query"]   = "🔥 Trending"

    st.markdown("---")

    # ── Main layout: Player left | Queue right ──
    results = st.session_state.get("yt_results", [])
    now     = st.session_state.get("yt_now")
    queue   = st.session_state.get("yt_queue", [])

    left, right = st.columns([2.2, 1], gap="medium")

    # ── LEFT: Now Playing + Results ──
    with left:
        # Now Playing panel
        if now:
            st.markdown(f"""
<div class="np-panel">
  <div class="np-label">▶ Now Playing</div>
  <div class="np-title">{now['title'][:70]}</div>
  <div class="np-channel">📺 {now['channel']} &nbsp;·&nbsp; ⏱ {now['duration']} &nbsp;·&nbsp; 👁 {fmt_views(now.get('views',0))}</div>
</div>""", unsafe_allow_html=True)
            components.html(_yt_embed_html(now["id"], autoplay=True, height=430), height=440, scrolling=False)

            # Controls row
            ctrl_cols = st.columns(4)
            with ctrl_cols[0]:
                if st.button("➕ Add to Queue", key="yt_addq", use_container_width=True):
                    if now not in st.session_state["yt_queue"]:
                        st.session_state["yt_queue"].append(now)
                        st.toast(f"Added: {now['title'][:30]}…", icon="✅")
            with ctrl_cols[1]:
                yt_url = f"https://youtube.com/watch?v={now['id']}"
                st.link_button("🔗 Open YouTube", yt_url, use_container_width=True)
            with ctrl_cols[2]:
                st.link_button("⬇️ Download (y2mate)", f"https://www.y2mate.com/youtube/{now['id']}", use_container_width=True)
            with ctrl_cols[3]:
                if st.button("❌ Clear", key="yt_clear_now", use_container_width=True):
                    st.session_state["yt_now"] = None; st.rerun()
        else:
            components.html("""
<!DOCTYPE html><html><head><style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0a0014; }
.empty {
  height: 240px; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  border: 1px dashed rgba(255,0,0,.18); border-radius:16px;
  background: rgba(15,23,42,.6);
}
.icon { font-size: 3.5rem; opacity:.18; margin-bottom:14px; }
.label {
  font-family: 'Space Mono', monospace; font-size: .65rem;
  letter-spacing: 3px; color: rgba(255,255,255,.15); text-transform:uppercase;
}
</style></head><body>
<div class="empty">
  <div class="icon">🎵</div>
  <div class="label">SEARCH &middot; CLICK A VIDEO TO PLAY</div>
</div>
</body></html>""", height=260, scrolling=False)

        # ── Results grid ──
        if results:
            q_label = st.session_state.get("yt_query","")
            st.markdown(f"**{len(results)} results** {'for: ' + q_label if q_label else ''}")

            cols = st.columns(3)
            for i, v in enumerate(results):
                with cols[i % 3]:
                    # Thumbnail
                    try:
                        st.image(v["thumb"], use_container_width=True)
                    except Exception:
                        st.markdown('<div style="height:90px;background:#1e293b;border-radius:8px;"></div>', unsafe_allow_html=True)

                    st.markdown(f"""
<div class="vcard-body" style="padding:0 2px 8px;">
  <div class="vcard-title">{v['title'][:55]}</div>
  <div class="vcard-meta">📺 {v['channel'][:25]} &nbsp;·&nbsp; ⏱ {v['duration']} &nbsp;·&nbsp; 👁 {fmt_views(v.get('views',0))}</div>
</div>""", unsafe_allow_html=True)

                    ca, cb = st.columns(2)
                    with ca:
                        if st.button("▶ Play", key=f"yt_play_{i}_{v['id']}", use_container_width=True):
                            st.session_state["yt_now"] = v
                            st.rerun()
                    with cb:
                        if st.button("➕ Q", key=f"yt_q_{i}_{v['id']}", use_container_width=True,
                                     help="Add to queue"):
                            if v not in st.session_state["yt_queue"]:
                                st.session_state["yt_queue"].append(v)
                                st.toast("Added to queue!", icon="✅")

    # ── RIGHT: Queue ──
    with right:
        st.markdown("### 📋 Queue")
        if not queue:
            st.markdown('<div style="text-align:center;padding:30px;color:rgba(255,255,255,.2);font-size:.75rem;font-family:Space Mono,monospace;">QUEUE IS EMPTY<br>Hit ➕ on any video</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:.75rem;color:rgba(255,255,255,.35);margin-bottom:8px;">{len(queue)} tracks</div>', unsafe_allow_html=True)

            if st.button("🗑️ Clear Queue", key="yt_clear_queue", use_container_width=True):
                st.session_state["yt_queue"] = []; st.rerun()

            for qi, qv in enumerate(queue):
                is_now = now and now["id"] == qv["id"]
                active_cls = "active" if is_now else ""
                st.markdown(f"""
<div class="q-item {active_cls}" style="{'border:1px solid rgba(255,0,0,.3);' if is_now else ''}">
  <img class="q-thumb" src="{qv['thumb']}" onerror="this.style.display='none'" />
  <div>
    <div class="q-title">{qv['title'][:40]}</div>
    <div class="q-meta">{qv['channel'][:22]} · {qv['duration']}</div>
  </div>
</div>""", unsafe_allow_html=True)

                qa, qb = st.columns(2)
                with qa:
                    if st.button("▶", key=f"yt_qplay_{qi}", use_container_width=True):
                        st.session_state["yt_now"] = qv; st.rerun()
                with qb:
                    if st.button("✕", key=f"yt_qrm_{qi}", use_container_width=True):
                        st.session_state["yt_queue"].pop(qi); st.rerun()

        # ── Mini search inside queue ──
        st.markdown("---")
        st.markdown("**🔍 Quick Add:**")
        mini_q = st.text_input("Search:", key="yt_mini_q", placeholder="song name…", label_visibility="collapsed")
        if st.button("Search & Add Top Result", key="yt_mini_go", use_container_width=True) and mini_q:
            with st.spinner("…"):
                mini_results = search_youtube(mini_q)
                if mini_results:
                    top = mini_results[0]
                    if top not in st.session_state["yt_queue"]:
                        st.session_state["yt_queue"].append(top)
                    st.session_state["yt_now"] = top
                    st.toast(f"Now playing: {top['title'][:30]}", icon="🎵")
                    st.rerun()
