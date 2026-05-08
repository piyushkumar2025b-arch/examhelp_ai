"""
youtube_player_addon.py
- Search YouTube via yt-dlp (server-side, no API key)
- Play live from YouTube via embed iframe
- Queue, history, categories
"""
import streamlit as st
import streamlit.components.v1 as components
from yt_search import search_youtube

# ── CSS ──────────────────────────────────────────────────────────────────────
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&display=swap');
.yt-wrap{font-family:'Syne',sans-serif;background:#09090f;color:#f0eeff;
  border-radius:16px;padding:0;overflow:hidden;border:1px solid rgba(124,110,247,.2)}
.yt-header{background:#111118;padding:14px 18px;border-bottom:1px solid rgba(124,110,247,.15);
  display:flex;align-items:center;gap:12px}
.yt-logo{font-size:18px;font-weight:800;background:linear-gradient(135deg,#7c6ef7,#f76e6e);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;white-space:nowrap}
.yt-badge{font-size:9px;background:rgba(124,110,247,.15);border:1px solid rgba(124,110,247,.3);
  color:#7c6ef7;padding:2px 8px;border-radius:100px;letter-spacing:1px}
.yt-card{background:#111118;border:1px solid rgba(124,110,247,.12);border-radius:12px;
  overflow:hidden;cursor:pointer;transition:all .2s}
.yt-card:hover{transform:translateY(-2px);border-color:rgba(124,110,247,.4);
  box-shadow:0 6px 24px rgba(124,110,247,.1)}
.yt-thumb{width:100%;aspect-ratio:16/9;object-fit:cover;background:#1a1a24;display:block}
.yt-info{padding:8px 10px}
.yt-title{font-size:12px;font-weight:700;line-height:1.4;color:#f0eeff;
  overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.yt-meta{font-size:10px;color:#6a6a8a;margin-top:4px}
.yt-dur{font-size:9px;background:rgba(0,0,0,.75);color:#fff;
  padding:1px 5px;border-radius:3px;font-weight:600}
.yt-nowplaying{background:#1a1a2e;border:1px solid rgba(124,110,247,.3);
  border-radius:12px;padding:12px 14px;display:flex;align-items:center;gap:12px}
.yt-np-thumb{width:64px;height:44px;border-radius:6px;object-fit:cover;background:#222}
.yt-np-title{font-size:13px;font-weight:700;color:#f0eeff}
.yt-np-ch{font-size:10px;color:#6a6a8a;margin-top:2px}
.yt-np-badge{font-size:9px;background:rgba(110,247,196,.1);border:1px solid rgba(110,247,196,.25);
  color:#6ef7c4;padding:2px 8px;border-radius:100px;letter-spacing:.5px;flex-shrink:0}
.cat-pill{display:inline-block;padding:5px 12px;border-radius:100px;
  background:#1a1a24;border:1px solid rgba(124,110,247,.2);color:#9090b0;
  font-size:11px;cursor:pointer;margin:2px;transition:all .15s;font-family:'Syne',sans-serif}
.cat-pill:hover{border-color:rgba(124,110,247,.5);color:#7c6ef7;background:rgba(124,110,247,.1)}
</style>
"""

# ── Categories ────────────────────────────────────────────────────────────────
CATS = [
    ("🔥 Trending", "trending music 2025"),
    ("☁️ Lo-Fi", "lofi hip hop chill beats"),
    ("🎸 Rock", "best rock songs all time"),
    ("🎤 Pop Hits", "top pop hits 2025"),
    ("🎧 EDM", "best EDM electronic 2025"),
    ("🎻 Classical", "relaxing classical music"),
    ("🌙 Night Drive", "night drive synthwave"),
    ("📚 Study", "study music focus concentration"),
    ("🎷 Jazz", "smooth jazz relaxing"),
    ("🎬 Bollywood", "latest bollywood songs 2025"),
    ("🙏 Devotional", "devotional bhajans songs"),
    ("🎵 K-Pop", "kpop hits 2025"),
]

def _state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

def render_youtube_player():
    st.markdown(STYLE, unsafe_allow_html=True)

    # Init state
    _state("yt_results", [])
    _state("yt_current", None)
    _state("yt_queue", [])
    _state("yt_history", [])
    _state("yt_searching", False)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="yt-wrap">
    <div class="yt-header">
      <div class="yt-logo">▶ YTPlayer</div>
      <div class="yt-badge">YOUTUBE INSIDE YOUR APP</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Search bar ────────────────────────────────────────────────────────────
    col_q, col_btn = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "search", label_visibility="collapsed",
            placeholder="🔍  Search any song, artist, album...",
            key="yt_search_input"
        )
    with col_btn:
        search_clicked = st.button("Search", key="yt_search_btn", use_container_width=True)

    # ── Categories ────────────────────────────────────────────────────────────
    st.markdown("**Browse Categories**")
    cat_cols = st.columns(6)
    for i, (label, cat_query) in enumerate(CATS):
        with cat_cols[i % 6]:
            if st.button(label, key=f"cat_{i}", use_container_width=True):
                st.session_state["yt_search_input"] = cat_query
                with st.spinner(f"Searching {label}..."):
                    results = search_youtube(cat_query, 20)
                st.session_state["yt_results"] = results
                st.rerun()

    # ── Trigger search ────────────────────────────────────────────────────────
    if search_clicked and query:
        with st.spinner(f'Searching YouTube for "{query}"...'):
            results = search_youtube(query, 20)
        if results:
            st.session_state["yt_results"] = results
            st.success(f"✅ Found {len(results)} results for **{query}**")
        else:
            st.error("No results found. Check if yt-dlp is installed.")

    # ── Now Playing ───────────────────────────────────────────────────────────
    cur = st.session_state.get("yt_current")
    if cur:
        st.markdown("---")
        st.markdown("**▶ Now Playing**")
        np_col1, np_col2 = st.columns([1, 3])
        with np_col1:
            st.image(cur["thumb"], use_container_width=True)
        with np_col2:
            st.markdown(f"**{cur['title']}**")
            st.caption(f"{cur['channel']}  ·  {cur['duration']}")

        # ── YouTube Embed Player ───────────────────────────────────────────────
        embed_html = f"""
        <div style="border-radius:14px;overflow:hidden;border:1px solid rgba(124,110,247,.3)">
        <iframe
          src="https://www.youtube.com/embed/{cur['id']}?autoplay=1&rel=0&modestbranding=1&playsinline=1"
          width="100%" height="420"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
          allowfullscreen
          style="display:block;border:none">
        </iframe>
        </div>
        """
        components.html(embed_html, height=440)

        # Queue controls
        ctrl1, ctrl2, ctrl3 = st.columns(3)
        with ctrl1:
            if st.button("⏮ Prev", key="yt_prev", use_container_width=True):
                _play_prev()
        with ctrl2:
            if st.button("⏭ Next", key="yt_next", use_container_width=True):
                _play_next()
        with ctrl3:
            if st.button("➕ Add to Queue", key="yt_addq", use_container_width=True):
                q = st.session_state["yt_queue"]
                if not any(x["id"] == cur["id"] for x in q):
                    q.append(cur)
                    st.success("Added to queue!")

    # ── Results Grid ──────────────────────────────────────────────────────────
    results = st.session_state.get("yt_results", [])
    if results:
        st.markdown("---")
        st.markdown(f"**Results** — {len(results)} videos")
        cols = st.columns(4)
        for i, v in enumerate(results):
            with cols[i % 4]:
                _render_card(v, i)

    # ── Queue & History sidebar ───────────────────────────────────────────────
    with st.expander(f"📋 Queue ({len(st.session_state['yt_queue'])})", expanded=False):
        q = st.session_state["yt_queue"]
        if not q:
            st.caption("Queue is empty. Add songs from results.")
        for i, v in enumerate(q):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.caption(f"**{v['title'][:45]}**  ·  {v['channel']}")
            with c2:
                if st.button("▶", key=f"qplay_{i}"):
                    _set_current(v)

    with st.expander(f"🕐 History ({len(st.session_state['yt_history'])})", expanded=False):
        h = st.session_state["yt_history"]
        if not h:
            st.caption("No history yet.")
        for i, v in enumerate(h[:15]):
            if st.button(f"▶  {v['title'][:50]}", key=f"hplay_{i}"):
                _set_current(v)


def _render_card(v, idx):
    thumb_html = f"""
    <img src="{v['thumb']}" style="width:100%;aspect-ratio:16/9;object-fit:cover;
      border-radius:8px 8px 0 0;background:#1a1a24">
    <div style="padding:6px 8px;background:#111118;border-radius:0 0 8px 8px;
      border:1px solid rgba(124,110,247,.12);border-top:none">
      <div style="font-size:11px;font-weight:700;color:#f0eeff;line-height:1.4;
        overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical">
        {v['title'][:60]}
      </div>
      <div style="font-size:9px;color:#6a6a8a;margin-top:3px">{v['channel'][:30]}  {v['duration']}</div>
    </div>
    """
    st.markdown(thumb_html, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶ Play", key=f"play_{idx}", use_container_width=True):
            _set_current(v)
    with c2:
        if st.button("+Q", key=f"addq_{idx}", use_container_width=True):
            q = st.session_state["yt_queue"]
            if not any(x["id"] == v["id"] for x in q):
                q.append(v)
                st.toast(f"Added: {v['title'][:30]}")


def _set_current(v):
    st.session_state["yt_current"] = v
    h = st.session_state["yt_history"]
    h = [x for x in h if x["id"] != v["id"]]
    h.insert(0, v)
    st.session_state["yt_history"] = h[:50]
    st.rerun()


def _play_next():
    q = st.session_state["yt_queue"]
    cur = st.session_state.get("yt_current")
    if not q:
        return
    idx = next((i for i, x in enumerate(q) if x["id"] == cur["id"]), -1) if cur else -1
    nxt = q[(idx + 1) % len(q)]
    _set_current(nxt)


def _play_prev():
    q = st.session_state["yt_queue"]
    cur = st.session_state.get("yt_current")
    if not q:
        return
    idx = next((i for i, x in enumerate(q) if x["id"] == cur["id"]), 0) if cur else 0
    prv = q[(idx - 1) % len(q)]
    _set_current(prv)
