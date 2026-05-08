"""
youtube_player_addon.py — YouTube Search & Player (wired to yt_search.py)
Bug #12: replaced Coming Soon stub with functional UI.
"""
import streamlit as st


def render_youtube_player():
    st.markdown("""
<style>
.yt-header{background:linear-gradient(135deg,rgba(9,9,15,.9),rgba(17,17,40,.9));
  border:1px solid rgba(124,110,247,.25);border-radius:20px;
  padding:24px 32px;margin-bottom:24px}
.yt-title{font-size:24px;font-weight:800;
  background:linear-gradient(90deg,#7c6ef7,#f76e6e);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.yt-card{background:rgba(15,23,42,.6);border:1px solid rgba(255,255,255,.07);
  border-radius:12px;padding:12px;margin-bottom:10px;
  transition:border-color .2s}
.yt-card:hover{border-color:rgba(124,110,247,.4)}
.yt-meta{font-size:12px;color:#6a6a8a;margin-top:4px}
</style>
<div class="yt-header">
  <div class="yt-title">🎵 YouTube Finder</div>
  <div style="color:#94a3b8;font-size:13px;margin-top:4px">
    Search and watch YouTube videos directly — no API key required.
  </div>
</div>
""", unsafe_allow_html=True)

    # Search bar
    col_q, col_btn = st.columns([4, 1])
    with col_q:
        query = st.text_input("Search YouTube", placeholder="e.g. Lo-Fi study beats, quantum mechanics lecture…",
                              label_visibility="collapsed", key="yt_query")
    with col_btn:
        search_clicked = st.button("🔍 Search", use_container_width=True, key="yt_search_btn")

    # Category shortcuts
    st.markdown("**Quick categories:**")
    cats = ["📚 Study Music", "🎵 Lo-Fi Hip Hop", "🎸 Pop", "🎧 EDM", "🎼 Classical", "🎤 Bollywood"]
    cat_cols = st.columns(len(cats))
    for i, cat in enumerate(cats):
        with cat_cols[i]:
            if st.button(cat, key=f"yt_cat_{i}", use_container_width=True):
                st.session_state["yt_query"] = cat.split(" ", 1)[1]
                search_clicked = True

    # Perform search
    search_term = st.session_state.get("yt_query", "") or query
    if (search_clicked or st.session_state.get("yt_last_query") != search_term) and search_term.strip():
        st.session_state["yt_last_query"] = search_term
        with st.spinner(f"Searching YouTube for '{search_term}'…"):
            try:
                from yt_search import search_youtube
                results = search_youtube(search_term, max_results=12)
                st.session_state["yt_results"] = results
            except Exception as e:
                st.error(f"Search error: {e}")
                st.session_state["yt_results"] = []

    results = st.session_state.get("yt_results", [])

    if results:
        st.markdown(f"**{len(results)} results for '{st.session_state.get('yt_last_query', '')}'**")

        # Show embedded player if a video is selected
        if st.session_state.get("yt_playing"):
            vid_id = st.session_state["yt_playing"]
            st.markdown(f"""
<div style="border-radius:12px;overflow:hidden;margin-bottom:20px">
  <iframe width="100%" height="400" src="https://www.youtube.com/embed/{vid_id}?autoplay=1"
    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
    allowfullscreen></iframe>
</div>""", unsafe_allow_html=True)
            if st.button("✖ Close Player", key="yt_close"):
                st.session_state["yt_playing"] = None
                st.rerun()

        # Result grid (3 columns)
        for row_start in range(0, len(results), 3):
            row = results[row_start:row_start + 3]
            cols = st.columns(3)
            for col, video in zip(cols, row):
                with col:
                    st.image(video["thumb"], use_container_width=True)
                    st.markdown(f"**{video['title'][:55]}{'…' if len(video['title']) > 55 else ''}**")
                    st.markdown(f"<div class='yt-meta'>📺 {video['channel']} &nbsp;·&nbsp; ⏱ {video['duration']}</div>",
                                unsafe_allow_html=True)
                    play_col, link_col = st.columns(2)
                    with play_col:
                        if st.button("▶ Play", key=f"yt_play_{video['id']}", use_container_width=True):
                            st.session_state["yt_playing"] = video["id"]
                            st.rerun()
                    with link_col:
                        st.link_button("🔗 Open", video["url"], use_container_width=True)
    elif st.session_state.get("yt_last_query"):
        st.info("No results found. Try a different search term.")
    else:
        st.markdown("""
<div style="text-align:center;padding:40px 0;color:#6a6a8a">
  🎵 Search for a song, artist, or topic above to get started
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="yt_back"):
        st.session_state.app_mode = "chat"
        st.rerun()
