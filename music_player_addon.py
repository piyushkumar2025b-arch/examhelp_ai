"""
music_player_addon.py — Real Music Player with Free APIs
Sources: Internet Archive (archive.org) — completely free, no key needed
Features: Search songs, stream, download, upload local files, playlist
"""
import streamlit as st
import urllib.request, urllib.parse, json

MUSIC_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600;700&family=Space+Mono&display=swap');

.mp-hero {
    background: linear-gradient(135deg,rgba(15,23,42,0.97) 0%,rgba(30,5,40,0.95) 100%);
    border: 1px solid rgba(168,85,247,0.25);
    border-radius: 24px; padding: 28px 32px; margin-bottom: 20px;
    position: relative; overflow: hidden;
}
.mp-hero::after {
    content:''; position:absolute; top:-1px; left:8%; right:8%; height:1px;
    background: linear-gradient(90deg,transparent,rgba(168,85,247,0.6),rgba(236,72,153,0.4),transparent);
}
.mp-title {
    font-family:'Orbitron',monospace; font-size:1.6rem; font-weight:900;
    background: linear-gradient(90deg,#a855f7,#ec4899,#f97316);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:4px;
}
.mp-sub { font-size:.88rem; color:rgba(255,255,255,0.4); }

.song-card {
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(168,85,247,0.12);
    border-radius: 14px; padding: 14px 18px; margin-bottom: 8px;
    transition: all .2s ease;
}
.song-card:hover {
    border-color: rgba(168,85,247,0.35);
    transform: translateX(4px);
}
.song-title {
    font-family:'Rajdhani',sans-serif; font-size:1rem; font-weight:700;
    color:#f0e7ff; margin-bottom:3px;
}
.song-meta {
    font-family:'Space Mono',monospace; font-size:.68rem;
    color:rgba(255,255,255,0.3); letter-spacing:1px;
}
.now-playing-bar {
    background: linear-gradient(90deg,rgba(168,85,247,0.1),rgba(236,72,153,0.07));
    border: 1px solid rgba(168,85,247,0.3);
    border-radius: 16px; padding: 16px 20px; margin-bottom: 16px;
    display:flex; align-items:center; gap:14px;
}
.np-info { flex:1; }
.np-title { font-family:'Rajdhani',sans-serif; font-size:1.05rem; font-weight:700; color:#e9d5ff; }
.np-artist { font-family:'Space Mono',monospace; font-size:.7rem; color:rgba(255,255,255,0.35); margin-top:2px; }
.wave-eq { display:flex; align-items:center; gap:2px; }
.weq-bar {
    width:3px; border-radius:2px;
    background: linear-gradient(180deg,#a855f7,#ec4899);
    animation: weqAnim ease-in-out infinite;
}
.weq-bar:nth-child(1){height:8px;animation-duration:.9s;}
.weq-bar:nth-child(2){height:18px;animation-duration:.6s;animation-delay:.1s;}
.weq-bar:nth-child(3){height:14px;animation-duration:.75s;animation-delay:.2s;}
.weq-bar:nth-child(4){height:22px;animation-duration:.8s;animation-delay:.05s;}
.weq-bar:nth-child(5){height:10px;animation-duration:.65s;animation-delay:.15s;}
@keyframes weqAnim{0%,100%{transform:scaleY(1);}50%{transform:scaleY(.3);}}

.genre-chip {
    display:inline-block; padding:4px 12px; border-radius:100px;
    font-family:'Space Mono',monospace; font-size:.7rem;
    background:rgba(168,85,247,0.1); border:1px solid rgba(168,85,247,0.2);
    color:#c4b5fd; margin:3px; cursor:pointer; transition:all .2s;
}
.genre-chip:hover { background:rgba(168,85,247,0.25); color:#e9d5ff; }
</style>
"""

# ── Internet Archive free music search ────────────────────────────────────────

def search_ia_music(query: str, rows: int = 12) -> list:
    """Search Internet Archive for free/CC music. No API key needed."""
    try:
        params = urllib.parse.urlencode({
            "q": f"({query}) AND mediatype:audio AND subject:(music OR song)",
            "fl[]": "identifier,title,creator,year,format,downloads",
            "sort[]": "downloads desc",
            "rows": rows,
            "page": 1,
            "output": "json",
        })
        url = f"https://archive.org/advancedsearch.php?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelpMusicPlayer/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        docs = data.get("response", {}).get("docs", [])
        results = []
        for d in docs:
            ident = d.get("identifier", "")
            title = d.get("title", ident)
            creator = d.get("creator", "Unknown Artist")
            if isinstance(creator, list):
                creator = creator[0]
            results.append({
                "id": ident,
                "title": title[:60],
                "artist": str(creator)[:50],
                "year": d.get("year", ""),
                "downloads": d.get("downloads", 0),
                "page_url": f"https://archive.org/details/{ident}",
            })
        return results
    except Exception:
        return []


def get_ia_audio_files(identifier: str) -> list:
    """Get playable MP3/OGG/FLAC files for an IA item."""
    try:
        url = f"https://archive.org/metadata/{identifier}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelpMusicPlayer/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        files = data.get("files", [])
        audio = []
        for f in files:
            name = f.get("name", "")
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in ("mp3", "ogg", "flac", "opus", "wav", "m4a"):
                size = int(f.get("size", 0))
                audio.append({
                    "name": name,
                    "ext": ext,
                    "url": f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}",
                    "size": size,
                    "title": f.get("title", name),
                })
        # prefer mp3 first
        audio.sort(key=lambda x: (x["ext"] != "mp3", x["ext"] != "ogg", x["name"]))
        return audio[:8]
    except Exception:
        return []


def _fmt_size(n: int) -> str:
    if n < 1024: return f"{n} B"
    if n < 1024**2: return f"{n/1024:.1f} KB"
    return f"{n/1024**2:.1f} MB"


# ── Curated ready-to-play free playlists (Internet Archive identifiers) ───────
CURATED = {
    "🎵 Lo-Fi Beats": [
        ("LoFi-Study-Music",           "Lo-Fi Study Mix",           "Various"),
        ("lofi_chill_vibes",           "Chill Vibes",               "CC Artists"),
        ("lofi-hip-hop-study",         "Lo-Fi Hip Hop Study",       "Various"),
    ],
    "🎸 Rock / Classic": [
        ("GratefulDead",               "Grateful Dead Live",        "Grateful Dead"),
        ("etree",                      "Live Concert Archive",      "Various Artists"),
        ("PorcuFatronBand",            "Rock Session",              "Open Source"),
    ],
    "🎹 Classical": [
        ("musopen-symphony-no-5",      "Symphony No. 5",            "Beethoven"),
        ("musopen-bach-cello-suites",  "Bach Cello Suites",         "J.S. Bach"),
        ("chopin-piano-works",         "Chopin Piano Works",        "Chopin"),
    ],
    "🌿 Ambient / Focus": [
        ("ambient-study-music",        "Ambient Study",             "CC Artists"),
        ("nature-soundscapes",         "Nature Soundscapes",        "Public Domain"),
        ("deep-focus-ambient",         "Deep Focus",                "Various"),
    ],
    "🎷 Jazz": [
        ("jazz-at-the-philharmonic",   "Jazz at the Philharmonic",  "Various Jazz"),
        ("78rpm",                      "Classic Jazz 78 RPM",       "Archive"),
        ("georgeblood",                "Vintage Jazz",              "George Blood"),
    ],
}


# ── Main render ───────────────────────────────────────────────────────────────
def render_music_player_page():
    """Full music player page — real songs, free, download enabled."""
    st.markdown(MUSIC_CSS, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="mp-hero">
        <div class="mp-title">🎵 Music Player</div>
        <div class="mp-sub">
            Stream &amp; download real free music — Internet Archive · CC licensed · Upload your own.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Init state
    if "mp_track" not in st.session_state:
        st.session_state.mp_track = None   # {"title","artist","url","download_url"}
    if "mp_queue" not in st.session_state:
        st.session_state.mp_queue = []
    if "mp_results" not in st.session_state:
        st.session_state.mp_results = []

    # ── Now Playing bar ───────────────────────────────────────────────────────
    track = st.session_state.mp_track
    if track:
        st.markdown(f"""
        <div class="now-playing-bar">
            <div style="font-size:2rem;">🎵</div>
            <div class="np-info">
                <div class="np-title">{track['title']}</div>
                <div class="np-artist">{track.get('artist','')}</div>
            </div>
            <div class="wave-eq">
                <div class="weq-bar"></div><div class="weq-bar"></div>
                <div class="weq-bar"></div><div class="weq-bar"></div>
                <div class="weq-bar"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.audio(track["url"])
        col_dl, col_stop = st.columns(2)
        with col_dl:
            if track.get("download_url"):
                st.link_button("⬇️ Download Song", track["download_url"],
                               use_container_width=True)
        with col_stop:
            if st.button("⏹ Stop / Clear", use_container_width=True, key="mp_stop"):
                st.session_state.mp_track = None
                st.rerun()
        st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_search, tab_curated, tab_upload, tab_queue = st.tabs([
        "🔍 Search Songs", "🎶 Free Playlists", "📁 My Music", "📋 Queue"
    ])

    # ═══════════ SEARCH TAB ══════════════════════════════════════════════════
    with tab_search:
        st.markdown("**Search millions of free / Creative Commons songs:**")
        col_q, col_btn = st.columns([4, 1])
        with col_q:
            query = st.text_input("Search:", placeholder="e.g. jazz piano, indie rock, beethoven, lo-fi…",
                                  key="mp_search_q", label_visibility="collapsed")
        with col_btn:
            search_btn = st.button("🔍 Search", type="primary", use_container_width=True, key="mp_search_btn")

        # Genre quick-picks
        st.markdown("**Quick genres:**")
        genre_cols = st.columns(6)
        genres = ["Lo-Fi", "Jazz", "Classical", "Rock", "Ambient", "Electronic"]
        for i, g in enumerate(genres):
            with genre_cols[i]:
                if st.button(g, key=f"mp_g_{g}", use_container_width=True):
                    st.session_state.mp_results = search_ia_music(g, rows=10)
                    st.rerun()

        if search_btn and query.strip():
            with st.spinner("🔍 Searching Internet Archive…"):
                st.session_state.mp_results = search_ia_music(query.strip(), rows=12)

        results = st.session_state.mp_results
        if results:
            st.markdown(f"**{len(results)} results found** *(Internet Archive — all free & legal)*")
            for r in results:
                with st.container():
                    st.markdown(f"""
                    <div class="song-card">
                        <div class="song-title">🎵 {r['title']}</div>
                        <div class="song-meta">👤 {r['artist']} · 📅 {r.get('year','')} · ⬇️ {r.get('downloads',0):,} downloads</div>
                    </div>
                    """, unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        if st.button("▶ Load & Play", key=f"mp_play_{r['id']}", use_container_width=True):
                            with st.spinner("Loading tracks…"):
                                files = get_ia_audio_files(r["id"])
                            if files:
                                f = files[0]
                                st.session_state.mp_track = {
                                    "title": r["title"], "artist": r["artist"],
                                    "url": f["url"], "download_url": f["url"],
                                }
                                st.rerun()
                            else:
                                st.warning("No playable audio files found for this item.")
                    with c2:
                        if st.button("➕ Add to Queue", key=f"mp_q_{r['id']}", use_container_width=True):
                            st.session_state.mp_queue.append(r)
                            st.toast(f"Added: {r['title']}")
                    with c3:
                        st.link_button("🔗 View", r["page_url"], use_container_width=True)
        elif search_btn:
            st.info("No results. Try a different keyword.")

    # ═══════════ CURATED PLAYLISTS TAB ═══════════════════════════════════════
    with tab_curated:
        st.markdown("**Hand-picked free playlists — click any song to play:**")
        for playlist_name, songs in CURATED.items():
            with st.expander(playlist_name, expanded=False):
                for ident, title, artist in songs:
                    col_t, col_p, col_d = st.columns([4, 1, 1])
                    with col_t:
                        st.markdown(f"<div class='song-title'>🎵 {title}</div>"
                                    f"<div class='song-meta'>👤 {artist}</div>",
                                    unsafe_allow_html=True)
                    with col_p:
                        if st.button("▶ Play", key=f"mp_cur_{ident}", use_container_width=True):
                            with st.spinner("Loading…"):
                                files = get_ia_audio_files(ident)
                            if files:
                                f = files[0]
                                st.session_state.mp_track = {
                                    "title": title, "artist": artist,
                                    "url": f["url"], "download_url": f["url"],
                                }
                                st.rerun()
                            else:
                                st.toast("Could not load — try another track.")
                    with col_d:
                        st.link_button("📄", f"https://archive.org/details/{ident}",
                                       use_container_width=True)

    # ═══════════ UPLOAD / MY MUSIC TAB ═══════════════════════════════════════
    with tab_upload:
        st.markdown("**Upload your own downloaded songs to listen:**")
        uploaded = st.file_uploader(
            "Upload music files",
            type=["mp3", "wav", "ogg", "flac", "m4a", "opus"],
            accept_multiple_files=True,
            key="mp_upload",
            label_visibility="collapsed"
        )
        if uploaded:
            st.success(f"✅ {len(uploaded)} file(s) loaded")
            for i, f in enumerate(uploaded):
                size_str = _fmt_size(f.size)
                st.markdown(f"""
                <div class="song-card">
                    <div class="song-title">🎵 {f.name}</div>
                    <div class="song-meta">📦 {size_str}</div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"▶ Play {f.name[:25]}", key=f"mp_local_{i}", use_container_width=True):
                        st.session_state.mp_track = {
                            "title": f.name, "artist": "Local File",
                            "url": f,  # streamlit audio accepts file-like
                            "download_url": None,
                        }
                        st.rerun()
                with c2:
                    st.download_button("⬇️ Download", f.getvalue(),
                                       file_name=f.name, mime="audio/mpeg",
                                       use_container_width=True, key=f"mp_dl_local_{i}")
        else:
            st.info("Drag & drop MP3, WAV, OGG, FLAC, M4A files above to play them.")

    # ═══════════ QUEUE TAB ════════════════════════════════════════════════════
    with tab_queue:
        queue = st.session_state.mp_queue
        if not queue:
            st.info("Your queue is empty. Add songs from Search or Playlists.")
        else:
            st.markdown(f"**{len(queue)} song(s) in queue:**")
            for i, item in enumerate(queue):
                c1, c2, c3 = st.columns([5, 1, 1])
                with c1:
                    st.markdown(f"**{i+1}.** {item['title']} — *{item['artist']}*")
                with c2:
                    if st.button("▶", key=f"mp_qplay_{i}", use_container_width=True):
                        with st.spinner("Loading…"):
                            files = get_ia_audio_files(item["id"])
                        if files:
                            f = files[0]
                            st.session_state.mp_track = {
                                "title": item["title"], "artist": item["artist"],
                                "url": f["url"], "download_url": f["url"],
                            }
                            st.rerun()
                with c3:
                    if st.button("🗑", key=f"mp_qrm_{i}", use_container_width=True):
                        st.session_state.mp_queue.pop(i)
                        st.rerun()
            if st.button("🗑 Clear Queue", use_container_width=True, key="mp_clear_q"):
                st.session_state.mp_queue = []
                st.rerun()

    # Footer
    st.markdown("---")
    st.caption("🎵 Music powered by Internet Archive (archive.org) — free, open-access, CC-licensed.")
    if st.button("💬 Back to Chat", use_container_width=True, key="mp_back"):
        st.session_state.app_mode = "chat"
        st.rerun()
