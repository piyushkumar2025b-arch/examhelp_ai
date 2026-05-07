"""
music_player_addon.py — Multi-Source Real Music Player
APIs Used (ALL FREE, NO KEYS):
  1. iTunes Search API  — 30-sec MP3 previews, Hindi + English, any song
  2. Deezer API         — 30-sec MP3 previews, huge global catalog
  3. Internet Archive   — Full CC/Public Domain songs
  4. Radio Browser API  — Live internet radio (Hindi FM, English FM)
  5. Musopen API        — Classical music (no key)
"""
import streamlit as st
import urllib.request, urllib.parse, json

MUSIC_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600;700&family=Space+Mono&display=swap');
.mp-hero{background:linear-gradient(135deg,rgba(15,23,42,.97),rgba(30,5,40,.95));border:1px solid rgba(168,85,247,.25);border-radius:24px;padding:26px 30px;margin-bottom:18px;position:relative;overflow:hidden;}
.mp-hero::after{content:'';position:absolute;top:-1px;left:8%;right:8%;height:1px;background:linear-gradient(90deg,transparent,rgba(168,85,247,.6),rgba(236,72,153,.4),transparent);}
.mp-title{font-family:'Orbitron',monospace;font-size:1.5rem;font-weight:900;background:linear-gradient(90deg,#a855f7,#ec4899,#f97316);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.mp-sub{font-size:.85rem;color:rgba(255,255,255,.4);margin-top:4px;}
.src-badge{display:inline-block;padding:2px 10px;border-radius:100px;font-size:.68rem;font-weight:700;margin:2px;font-family:'Space Mono',monospace;}
.src-itunes{background:rgba(252,211,77,.1);border:1px solid rgba(252,211,77,.3);color:#fcd34d;}
.src-deezer{background:rgba(168,85,247,.1);border:1px solid rgba(168,85,247,.3);color:#c4b5fd;}
.src-ia{background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.3);color:#6ee7b7;}
.src-radio{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#fca5a5;}
.song-card{background:rgba(15,23,42,.8);border:1px solid rgba(168,85,247,.1);border-radius:14px;padding:12px 16px;margin-bottom:7px;transition:all .2s;}
.song-card:hover{border-color:rgba(168,85,247,.35);transform:translateX(3px);}
.song-title{font-family:'Rajdhani',sans-serif;font-size:.95rem;font-weight:700;color:#f0e7ff;margin-bottom:2px;}
.song-meta{font-size:.72rem;color:rgba(255,255,255,.35);}
.np-bar{background:linear-gradient(90deg,rgba(168,85,247,.12),rgba(236,72,153,.07));border:1px solid rgba(168,85,247,.3);border-radius:16px;padding:14px 18px;margin-bottom:14px;}
.np-title{font-family:'Rajdhani',sans-serif;font-size:1.05rem;font-weight:700;color:#e9d5ff;}
.np-artist{font-size:.72rem;color:rgba(255,255,255,.35);font-family:'Space Mono',monospace;}
.weq{display:inline-flex;align-items:center;gap:2px;margin-left:10px;}
.wb{width:3px;border-radius:2px;background:linear-gradient(180deg,#a855f7,#ec4899);animation:weqA ease-in-out infinite;}
.wb:nth-child(1){height:8px;animation-duration:.9s;}
.wb:nth-child(2){height:18px;animation-duration:.6s;animation-delay:.1s;}
.wb:nth-child(3){height:13px;animation-duration:.75s;animation-delay:.2s;}
.wb:nth-child(4){height:20px;animation-duration:.8s;animation-delay:.05s;}
.wb:nth-child(5){height:10px;animation-duration:.65s;animation-delay:.15s;}
@keyframes weqA{0%,100%{transform:scaleY(1);}50%{transform:scaleY(.3);}}
.radio-card{background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.12);border-radius:12px;padding:10px 14px;margin-bottom:6px;transition:all .2s;}
.radio-card:hover{border-color:rgba(239,68,68,.3);}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# API 1: iTunes Search (Apple) — FREE, NO KEY, real 30-sec MP3 previews
# Works for Hindi (Bollywood), English, any genre
# ─────────────────────────────────────────────────────────────────────────────
def search_itunes(query: str, limit: int = 15, country: str = "IN") -> list:
    try:
        params = urllib.parse.urlencode({
            "term": query, "media": "music", "entity": "song",
            "limit": limit, "country": country
        })
        url = f"https://itunes.apple.com/search?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        results = []
        for t in data.get("results", []):
            preview = t.get("previewUrl", "")
            if not preview:
                continue
            results.append({
                "title":      t.get("trackName", "")[:60],
                "artist":     t.get("artistName", "")[:40],
                "album":      t.get("collectionName", "")[:40],
                "preview_url": preview,       # direct playable MP3
                "artwork":    t.get("artworkUrl100", ""),
                "source":     "iTunes",
                "duration":   "30s preview",
                "track_id":   str(t.get("trackId", "")),
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# API 2: Deezer — FREE, NO KEY, real 30-sec MP3 previews
# ─────────────────────────────────────────────────────────────────────────────
def search_deezer(query: str, limit: int = 15) -> list:
    try:
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        results = []
        for t in data.get("data", []):
            preview = t.get("preview", "")
            if not preview:
                continue
            results.append({
                "title":      t.get("title", "")[:60],
                "artist":     t.get("artist", {}).get("name", "")[:40],
                "album":      t.get("album", {}).get("title", "")[:40],
                "preview_url": preview,
                "artwork":    t.get("album", {}).get("cover_medium", ""),
                "source":     "Deezer",
                "duration":   "30s preview",
                "track_id":   str(t.get("id", "")),
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# API 3: Internet Archive — FREE, FULL songs, Public Domain / CC
# ─────────────────────────────────────────────────────────────────────────────
def search_ia_music(query: str, rows: int = 10) -> list:
    try:
        params = urllib.parse.urlencode({
            "q": f"({query}) AND mediatype:audio",
            "fl[]": "identifier,title,creator,year,downloads",
            "sort[]": "downloads desc",
            "rows": rows, "page": 1, "output": "json",
        })
        url = f"https://archive.org/advancedsearch.php?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        docs = data.get("response", {}).get("docs", [])
        results = []
        for d in docs:
            ident = d.get("identifier", "")
            creator = d.get("creator", "Public Domain")
            if isinstance(creator, list): creator = creator[0]
            results.append({
                "id": ident, "title": str(d.get("title", ident))[:60],
                "artist": str(creator)[:40], "year": d.get("year", ""),
                "downloads": d.get("downloads", 0),
                "page_url": f"https://archive.org/details/{ident}",
                "source": "Internet Archive",
            })
        return results
    except Exception:
        return []


def get_ia_audio_url(identifier: str) -> str:
    """Get first playable MP3 from an IA item."""
    try:
        url = f"https://archive.org/metadata/{identifier}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        for f in data.get("files", []):
            ext = f.get("name", "").rsplit(".", 1)[-1].lower()
            if ext in ("mp3", "ogg"):
                name = urllib.parse.quote(f["name"])
                return f"https://archive.org/download/{identifier}/{name}"
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# API 4: Radio Browser — FREE live internet radio (Hindi FM, English stations)
# ─────────────────────────────────────────────────────────────────────────────
def get_radio_stations(tag: str = "hindi", limit: int = 8) -> list:
    try:
        url = f"https://de1.api.radio-browser.info/json/stations/bytag/{urllib.parse.quote(tag)}?limit={limit}&order=votes&reverse=true&hidebroken=true"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        return [{"name": s.get("name","")[:50], "url": s.get("url_resolved",""),
                 "country": s.get("countrycode",""), "votes": s.get("votes",0),
                 "favicon": s.get("favicon","")} for s in data if s.get("url_resolved")]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Combined multi-source search
# ─────────────────────────────────────────────────────────────────────────────
def multi_search(query: str, sources: list) -> list:
    results = []
    if "iTunes" in sources:
        results.extend(search_itunes(query, limit=10))
    if "Deezer" in sources:
        results.extend(search_deezer(query, limit=10))
    if "JioSaavn (Hindi/English Full)" in sources:
        results.extend(search_jiosaavn(query, limit=10))
    if "Jamendo (Indie CC)" in sources:
        results.extend(search_jamendo(query, limit=10))
    return results


def _fmt_size(n):
    if n < 1024**2: return f"{n/1024:.1f} KB"
    return f"{n/1024**2:.1f} MB"


# ─────────────────────────────────────────────────────────────────────────────
# API 5: JioSaavn (Unofficial Open API) — FREE, Hindi/Bollywood & English
# ─────────────────────────────────────────────────────────────────────────────
def search_jiosaavn(query: str, limit: int = 15) -> list:
    """Fetch real Hindi/Bollywood and English songs via public JioSaavn API."""
    try:
        url = f"https://saavn.dev/api/search/songs?query={urllib.parse.quote(query)}&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        results = []
        for t in data.get("data", {}).get("results", []):
            # Get the highest quality download URL
            dl_links = t.get("downloadUrl", [])
            preview = dl_links[-1].get("url", "") if dl_links else ""
            if not preview:
                continue
            
            # Safely get artists
            artists = t.get("artists", {})
            primary_artists = artists.get("primary", [])
            artist_name = primary_artists[0].get("name", "Unknown Artist") if primary_artists else "Unknown"
            
            # Safely get images
            images = t.get("image", [])
            artwork = images[-1].get("url", "") if images else ""

            results.append({
                "title":      t.get("name", "")[:60],
                "artist":     artist_name[:40],
                "album":      t.get("album", {}).get("name", "")[:40],
                "preview_url": preview, # High quality full song
                "artwork":    artwork,
                "source":     "JioSaavn",
                "duration":   "Full Song",
                "track_id":   str(t.get("id", "")),
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# API 6: Jamendo — FREE, Independent Artists, CC licensed
# ─────────────────────────────────────────────────────────────────────────────
def search_jamendo(query: str, limit: int = 15) -> list:
    """Fetch free independent music from Jamendo (using public client ID)."""
    try:
        # Public client ID often used for testing/open projects
        client_id = "56d30c95"
        url = f"https://api.jamendo.com/v3.0/tracks/?client_id={client_id}&format=json&limit={limit}&search={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        results = []
        for t in data.get("results", []):
            preview = t.get("audio", "")
            if not preview:
                continue
            results.append({
                "title":      t.get("name", "")[:60],
                "artist":     t.get("artist_name", "")[:40],
                "album":      t.get("album_name", "")[:40],
                "preview_url": preview, # Full playable song stream
                "artwork":    t.get("image", ""),
                "source":     "Jamendo",
                "duration":   "Full Song",
                "track_id":   str(t.get("id", "")),
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# UI AND RENDERING
# ─────────────────────────────────────────────────────────────────────────────
def render_music_player_page():
    """Full music player UI wiring all free APIs and local uploads."""
    st.markdown(MUSIC_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="mp-hero">
        <div class="mp-title">🎶 Universal Music Player</div>
        <div class="mp-sub">
            Real songs. Real streams. 100% Free. Powered by iTunes, Deezer, JioSaavn, Jamendo & Internet Archive.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # State init
    if "mp_track" not in st.session_state: st.session_state.mp_track = None
    if "mp_results" not in st.session_state: st.session_state.mp_results = []
    if "mp_radio" not in st.session_state: st.session_state.mp_radio = []
    if "mp_volume" not in st.session_state: st.session_state.mp_volume = 80

    # ── Now Playing ───────────────────────────────────────────────────────────
    track = st.session_state.mp_track
    if track:
        # Determine source badge color
        src = track.get("source", "Local")
        b_class = "src-itunes" if src=="iTunes" else "src-deezer" if src=="Deezer" else "src-ia" if src=="Internet Archive" else "src-radio"
        
        st.markdown(f"""
        <div class="np-bar">
            <div style="font-size:2.2rem;margin-right:12px;">🎵</div>
            <div style="flex:1">
                <span class="src-badge {b_class}">{src}</span>
                <div class="np-title">{track['title']}</div>
                <div class="np-artist">{track.get('artist','')}</div>
            </div>
            <div class="weq">
                <div class="wb"></div><div class="wb"></div><div class="wb"></div>
                <div class="wb"></div><div class="wb"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Audio Player — looping HTML5 player (plays until user stops)
        import streamlit.components.v1 as _comp
        _url = track.get("url", "")
        if isinstance(_url, str) and _url:
            # Stream URL — use HTML5 audio with loop=true so it plays forever
            _vol = st.session_state.get("mp_volume", 80) / 100.0
            _comp.html(f'''
            <audio id="mpAudio" autoplay loop style="width:100%;border-radius:8px;margin:6px 0;">
                <source src="{_url}" type="audio/mpeg">
                <source src="{_url}" type="audio/ogg">
                Your browser does not support the audio element.
            </audio>
            <script>
                var a = document.getElementById('mpAudio');
                if (a) {{
                    a.volume = {_vol:.2f};
                    a.play().catch(function(e){{ console.log('Autoplay blocked:', e); }});
                }}
            </script>
            ''', height=60)
        else:
            # Local file upload — st.audio handles bytes/file objects, add loop via JS
            st.audio(_url)
            _comp.html('''
            <script>
                // Find Streamlit audio element and set loop
                setTimeout(function() {
                    var audios = window.parent.document.querySelectorAll('audio');
                    audios.forEach(function(a) {{ a.loop = true; a.play(); }});
                }, 500);
            </script>
            ''', height=0)
        
        c1, c2 = st.columns(2)
        with c1:
            if src != "Radio" and isinstance(track.get("url"), str):
                st.link_button("⬇️ Direct Audio Stream", track["url"], use_container_width=True)
        with c2:
            if st.button("⏹ Stop Playing", use_container_width=True):
                st.session_state.mp_track = None
                st.rerun()
        st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_search, tab_radio, tab_upload = st.tabs(["🔍 Search Music", "📻 Live Radio", "📁 My Music"])

    # ═══════════ SEARCH MUSIC TAB ════════════════════════════════════════════
    with tab_search:
        st.markdown("**Search across multiple free APIs (Hindi, English, Global):**")
        
        # Source toggles
        cols = st.columns(5)
        use_saavn = cols[0].checkbox("JioSaavn", value=True)
        use_itunes = cols[1].checkbox("iTunes", value=True)
        use_deezer = cols[2].checkbox("Deezer", value=True)
        use_jamendo = cols[3].checkbox("Jamendo", value=True)
        use_ia = cols[4].checkbox("Archive.org", value=False)
        
        col_q, col_b = st.columns([4,1])
        with col_q:
            query = st.text_input("Song name, artist, or movie:", placeholder="e.g., Arijit Singh, Ed Sheeran, Lo-Fi...", label_visibility="collapsed")
        with col_b:
            search_btn = st.button("🔍 Search", use_container_width=True, type="primary")

        if search_btn and query:
            sources = []
            if use_itunes: sources.append("iTunes")
            if use_deezer: sources.append("Deezer")
            if use_saavn: sources.append("JioSaavn (Hindi/English Full)")
            if use_jamendo: sources.append("Jamendo (Indie CC)")
            
            with st.spinner("Searching APIs..."):
                results = multi_search(query, sources)
                if use_ia:
                    results.extend(search_ia_music(query, rows=5))
                st.session_state.mp_results = results

        res = st.session_state.mp_results
        if res:
            st.caption(f"Found {len(res)} results:")
            for i, r in enumerate(res):
                # source styling
                src = r.get("source", "")
                b_class = "src-itunes" if src=="iTunes" else "src-deezer" if src=="Deezer" else "src-ia" if src=="Internet Archive" else "src-radio"
                
                st.markdown(f"""
                <div class="song-card">
                    <div style="display:flex; justify-content:space-between;">
                        <div class="song-title">🎵 {r['title']}</div>
                        <span class="src-badge {b_class}">{src}</span>
                    </div>
                    <div class="song-meta">👤 {r['artist']} &nbsp;|&nbsp; 💿 {r.get('album','Unknown Album')} &nbsp;|&nbsp; ⏱️ {r.get('duration','Stream')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("▶ Play", key=f"play_{i}_{r['track_id']}", use_container_width=True):
                    stream_url = r["preview_url"]
                    if src == "Internet Archive":
                        with st.spinner("Resolving audio URL..."):
                            stream_url = get_ia_audio_url(r["id"])
                            
                    if stream_url:
                        st.session_state.mp_track = {
                            "title": r["title"], "artist": r["artist"],
                            "url": stream_url, "source": src
                        }
                        st.rerun()
                    else:
                        st.error("No playable URL found for this track.")
                # Download button — direct link to audio file
                _dl_url = r.get("preview_url") or ""
                if _dl_url and isinstance(_dl_url, str) and _dl_url.startswith("http"):
                    st.link_button("⬇️ Download / Open Audio", _dl_url, use_container_width=True)

    # ═══════════ LIVE RADIO TAB ══════════════════════════════════════════════
    with tab_radio:
        st.markdown("**Listen to live internet radio (Hindi, English, News, etc):**")
        r_cols = st.columns([3, 1])
        with r_cols[0]:
            r_tag = st.selectbox("Select Station Category:", [
                "hindi", "bollywood", "indian", "tamil", "telugu", "punjabi", "devotional",
                "english", "pop", "rock", "jazz", "classical", "lofi", "ambient",
                "news", "talk", "sports", "comedy",
                "electronic", "edm", "hiphop", "rnb", "reggae", "country",
                "christmas", "kids", "80s", "90s", "2000s"
            ], label_visibility="collapsed")
        with r_cols[1]:
            if st.button("📡 Load Stations", use_container_width=True):
                with st.spinner("Fetching live stations..."):
                    st.session_state.mp_radio = get_radio_stations(r_tag, limit=25)
        
        stations = st.session_state.mp_radio
        if stations:
            for i, s in enumerate(stations):
                st.markdown(f"""
                <div class="radio-card">
                    <div class="song-title">📻 {s['name']}</div>
                    <div class="song-meta">🌍 {s['country']} &nbsp;|&nbsp; 👍 {s['votes']} votes</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("▶ Tune In", key=f"radio_{i}", use_container_width=True):
                    st.session_state.mp_track = {
                        "title": s['name'], "artist": "Live Radio Stream",
                        "url": s['url'], "source": "Radio"
                    }
                    st.rerun()

    # ═══════════ LOCAL UPLOAD TAB ════════════════════════════════════════════
    with tab_upload:
        st.markdown("**Upload your own MP3/WAV files to listen offline:**")
        uploaded = st.file_uploader("Drop audio files here", type=["mp3","wav","ogg","flac","m4a"], accept_multiple_files=True, label_visibility="collapsed")
        if uploaded:
            for i, f in enumerate(uploaded):
                st.markdown(f"""
                <div class="song-card">
                    <div class="song-title">📁 {f.name}</div>
                    <div class="song-meta">📦 {_fmt_size(f.size)}</div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"▶ Play {f.name[:15]}", key=f"local_{i}", use_container_width=True):
                        st.session_state.mp_track = {
                            "title": f.name, "artist": "Local File",
                            "url": f, "source": "Local"
                        }
                        st.rerun()
                with c2:
                    st.download_button("⬇️ Download Back", f.getvalue(), file_name=f.name, use_container_width=True, key=f"dl_loc_{i}")

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True):
        st.session_state.app_mode = "chat"
        st.rerun()

