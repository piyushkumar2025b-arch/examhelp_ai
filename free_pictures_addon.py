"""
free_pictures_addon.py — Premium Free Photo Browser UI v1.0
============================================================
Multi-source photo browser with search, categories, trending,
lightbox preview, and one-click download. Zero API keys needed.
"""
import streamlit as st
import streamlit.components.v1 as components

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;500;600;700&family=Space+Mono&display=swap');

/* ── Header ── */
.fp-header {
    background: linear-gradient(135deg,#0a0014 0%,#0d001f 40%,#001428 100%);
    border: 1px solid rgba(99,102,241,0.35); border-radius: 24px;
    padding: 28px 36px; margin-bottom: 20px; position: relative; overflow: hidden;
}
.fp-header::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(ellipse 60% 80% at 80% 20%,rgba(99,102,241,0.18) 0%,transparent 60%),
                radial-gradient(ellipse 40% 60% at 10% 80%,rgba(6,182,212,0.1) 0%,transparent 60%);
}
.fp-title {
    font-family:'Orbitron',monospace; font-size:clamp(18px,3vw,30px); font-weight:900;
    background:linear-gradient(90deg,#fff 0%,#a5b4fc 40%,#67e8f9 80%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    position:relative; margin:0 0 6px;
}
.fp-subtitle {
    font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px;
    color:rgba(165,180,252,0.55); text-transform:uppercase; position:relative;
}
.fp-badge {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3);
    border-radius:100px; padding:4px 14px; margin-bottom:12px;
    font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px; color:#a5b4fc;
}
.fp-dot { width:6px;height:6px;border-radius:50%;background:#818cf8;
    animation:fppulse 1.5s ease-in-out infinite; }
@keyframes fppulse{0%,100%{opacity:1}50%{opacity:.3}}

/* ── Source chips ── */
.src-row { display:flex; gap:6px; flex-wrap:wrap; margin:8px 0; }
.src-chip {
    display:inline-flex; align-items:center; gap:4px;
    background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2);
    border-radius:100px; padding:3px 10px;
    font-family:'Space Mono',monospace; font-size:9px; color:rgba(165,180,252,0.7);
}

/* ── Photo grid ── */
.fp-grid {
    display:grid;
    grid-template-columns: repeat(auto-fill,minmax(220px,1fr));
    gap:14px; padding:4px 0;
}
.fp-card {
    border-radius:16px; overflow:hidden; position:relative;
    border:1px solid rgba(255,255,255,0.06);
    background:rgba(13,13,22,0.6);
    transition: all 0.28s cubic-bezier(0.16,1,0.3,1);
    cursor:pointer;
}
.fp-card:hover {
    transform:translateY(-5px) scale(1.02);
    border-color:rgba(99,102,241,0.45);
    box-shadow: 0 16px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(99,102,241,0.2);
}
.fp-img {
    width:100%; aspect-ratio:4/3; object-fit:cover; display:block;
    background:rgba(13,13,22,0.8);
    transition: transform 0.4s ease;
}
.fp-card:hover .fp-img { transform:scale(1.05); }
.fp-overlay {
    position:absolute; bottom:0; left:0; right:0;
    background:linear-gradient(transparent,rgba(0,0,0,0.82));
    padding:28px 12px 12px;
    opacity:0; transition:opacity 0.25s ease;
}
.fp-card:hover .fp-overlay { opacity:1; }
.fp-card-title {
    font-family:'Inter',sans-serif; font-size:11px; font-weight:600;
    color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    margin-bottom:2px;
}
.fp-card-meta {
    font-family:'Space Mono',monospace; font-size:8px;
    color:rgba(255,255,255,0.45); letter-spacing:1px;
}
.fp-source-tag {
    position:absolute; top:8px; right:8px;
    background:rgba(0,0,0,0.65); border-radius:100px; padding:2px 8px;
    font-family:'Space Mono',monospace; font-size:8px; color:rgba(255,255,255,0.5);
    backdrop-filter:blur(8px); letter-spacing:1px;
}
.fp-license-tag {
    position:absolute; top:8px; left:8px;
    background:rgba(52,211,153,0.15); border:1px solid rgba(52,211,153,0.3);
    border-radius:100px; padding:2px 8px;
    font-family:'Space Mono',monospace; font-size:8px; color:#6ee7b7;
    backdrop-filter:blur(8px);
}

/* ── Lightbox ── */
.fp-lightbox {
    background:rgba(13,13,22,0.95); border:1px solid rgba(99,102,241,0.3);
    border-radius:20px; padding:20px; margin:16px 0;
    backdrop-filter:blur(20px);
}
.fp-lb-img { width:100%; border-radius:14px; max-height:500px; object-fit:contain; }
.fp-lb-meta { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
.fp-lb-chip {
    background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2);
    border-radius:100px; padding:3px 12px;
    font-family:'Space Mono',monospace; font-size:9px; color:rgba(165,180,252,0.7);
}

/* ── Stats bar ── */
.fp-stats { display:flex; gap:10px; flex-wrap:wrap; margin:10px 0; }
.fp-stat {
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
    border-radius:100px; padding:4px 14px;
    font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,0.4);
}
.fp-stat b { color:#a5b4fc; }

/* ── Category pills ── */
.cat-pill {
    display:inline-block; padding:5px 14px; border-radius:100px; cursor:pointer;
    border:1px solid rgba(99,102,241,0.2); background:rgba(99,102,241,0.06);
    font-family:'Inter',sans-serif; font-size:11px; font-weight:500;
    color:rgba(165,180,252,0.75); margin:3px; transition:all 0.2s ease;
}
.cat-pill:hover, .cat-pill.active {
    background:rgba(99,102,241,0.18); border-color:rgba(99,102,241,0.5);
    color:#a5b4fc; transform:translateY(-1px);
}

/* ── Empty state ── */
.fp-empty {
    text-align:center; padding:60px 20px;
    color:rgba(255,255,255,0.2);
    font-family:'Space Mono',monospace; font-size:11px; letter-spacing:2px;
}
.fp-empty-icon { font-size:56px; display:block; margin-bottom:14px; opacity:0.2; }
</style>
"""


def _header():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="fp-header">
        <div class="fp-badge"><div class="fp-dot"></div>
        7 FREE SOURCES · NO KEY NEEDED · CC-LICENSED</div>
        <div class="fp-title">🖼️ Free Photo Browser</div>
        <div class="fp-subtitle">Unsplash · Wikimedia · Openverse · NASA · Met Museum · Picsum</div>
    </div>
    """, unsafe_allow_html=True)


def _render_photo_grid(photos: list[dict], key_prefix: str = "fp"):
    """Render photos in a responsive CSS grid with click-to-expand lightbox."""
    if not photos:
        st.markdown("""
        <div class="fp-empty">
            <span class="fp-empty-icon">🖼️</span>
            NO PHOTOS FOUND<br>
            <span style="font-size:9px;opacity:.5;">Try a different search term or category</span>
        </div>
        """, unsafe_allow_html=True)
        return

    # Build the grid HTML
    grid_html = '<div class="fp-grid">'
    for i, p in enumerate(photos):
        thumb = p.get("thumb") or p.get("url", "")
        title = p.get("title", "Photo")[:50]
        source = p.get("source", "Free")
        license_label = p.get("license", "Free")[:12]
        idx = i
        grid_html += f"""
        <div class="fp-card" onclick="
          var el = document.getElementById('fp_expand_{key_prefix}_{idx}');
          if(el) el.style.display = el.style.display==='none' ? 'block' : 'none';
        ">
          <img class="fp-img" src="{thumb}"
               onerror="this.src='https://picsum.photos/400/300?random={idx}'"
               loading="lazy" alt="{title}" />
          <div class="fp-source-tag">{source[:15]}</div>
          <div class="fp-license-tag">🆓 {license_label}</div>
          <div class="fp-overlay">
            <div class="fp-card-title">{title}</div>
            <div class="fp-card-meta">by {p.get('author','Unknown')[:30]}</div>
          </div>
        </div>
        """
    grid_html += '</div>'

    components.html(
        f"<html><head><style>*{{margin:0;box-sizing:border-box;}} body{{background:transparent;}}</style></head>"
        f"<body>{grid_html}</body></html>",
        height=min(900, ((len(photos) // 3) + 1) * 280 + 20),
        scrolling=False,
    )

    # Streamlit expand buttons below the grid
    cols_per_row = 3
    for row_start in range(0, len(photos), cols_per_row):
        row_photos = photos[row_start:row_start + cols_per_row]
        cols = st.columns(len(row_photos))
        for j, (col, p) in enumerate(zip(cols, row_photos)):
            idx = row_start + j
            with col:
                if st.button(f"🔍 View", key=f"{key_prefix}_view_{idx}", use_container_width=True):
                    st.session_state[f"fp_lightbox_{key_prefix}"] = idx
                    st.session_state[f"fp_photos_{key_prefix}"] = photos

    # Lightbox
    lb_idx = st.session_state.get(f"fp_lightbox_{key_prefix}", None)
    lb_photos = st.session_state.get(f"fp_photos_{key_prefix}", [])
    if lb_idx is not None and lb_photos and lb_idx < len(lb_photos):
        p = lb_photos[lb_idx]
        full_url = p.get("full") or p.get("url", "")
        thumb = p.get("thumb") or full_url
        st.markdown(f"""
        <div class="fp-lightbox">
          <img class="fp-lb-img" src="{full_url}"
               onerror="this.src='{thumb}'"
               alt="{p.get('title','Photo')}" />
          <div style="margin-top:12px;">
            <div style="font-family:'Inter',sans-serif;font-size:14px;font-weight:600;color:#fff;margin-bottom:6px;">
              {p.get('title','Photo')}
            </div>
            <div style="font-family:'Inter',sans-serif;font-size:12px;color:rgba(255,255,255,0.5);margin-bottom:10px;">
              {p.get('description','')[:120]}
            </div>
          </div>
          <div class="fp-lb-meta">
            <span class="fp-lb-chip">📸 {p.get('author','Unknown')[:30]}</span>
            <span class="fp-lb-chip">🌐 {p.get('source','Free')}</span>
            <span class="fp-lb-chip">🆓 {p.get('license','Free')[:20]}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        lbc1, lbc2, lbc3 = st.columns(3)
        with lbc1:
            st.markdown(
                f'<a href="{full_url}" target="_blank" style="display:block;text-align:center;'
                f'padding:8px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);'
                f'border-radius:10px;color:#a5b4fc;font-size:12px;text-decoration:none;">'
                f'⬇️ Open Full Size</a>',
                unsafe_allow_html=True
            )
        with lbc2:
            src_url = p.get("source_url", "")
            if src_url:
                st.markdown(
                    f'<a href="{src_url}" target="_blank" style="display:block;text-align:center;'
                    f'padding:8px;background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.25);'
                    f'border-radius:10px;color:#67e8f9;font-size:12px;text-decoration:none;">'
                    f'🔗 Source Page</a>',
                    unsafe_allow_html=True
                )
        with lbc3:
            if st.button("✖ Close", key=f"{key_prefix}_lb_close", use_container_width=True):
                del st.session_state[f"fp_lightbox_{key_prefix}"]
                st.rerun()


def render_free_pictures():
    """Main entry point — renders the full Free Photo Browser."""
    from free_pictures_engine import (
        search_free_pictures, get_category_pack, get_all_categories,
        get_trending_photos, CATEGORY_PACKS,
    )

    _header()

    # Init session state
    defaults = {
        "fp_query": "",
        "fp_results": [],
        "fp_active_tab": "🔥 Trending",
        "fp_active_cat": list(CATEGORY_PACKS.keys())[0],
        "fp_sources": ["unsplash", "wikimedia", "openverse", "picsum"],
        "fp_count": 24,
        "fp_loading": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Source filter ─────────────────────────────────────────────────────────
    with st.expander("⚙️ Source Filters & Options", expanded=False):
        all_src_opts = ["unsplash", "wikimedia", "openverse", "nasa", "met", "picsum"]
        sel_sources = st.multiselect(
            "Photo Sources",
            all_src_opts,
            default=st.session_state.fp_sources,
            key="fp_src_select",
            format_func=lambda x: {
                "unsplash": "📷 Unsplash",
                "wikimedia": "🌍 Wikimedia Commons",
                "openverse": "🆓 Openverse (CC)",
                "nasa": "🚀 NASA Gallery",
                "met": "🏛️ Met Museum",
                "picsum": "🎨 Picsum Photos",
            }.get(x, x),
        )
        st.session_state.fp_sources = sel_sources or ["unsplash", "picsum"]

        count_opts = [12, 24, 36, 48]
        sel_count = st.select_slider("Photos per page", count_opts, value=24, key="fp_count_sel")
        st.session_state.fp_count = sel_count

        # Source description
        st.markdown("""
        <div class="src-row">
          <span class="src-chip">📷 Unsplash — Professional photography</span>
          <span class="src-chip">🌍 Wikimedia — CC-licensed real photos</span>
          <span class="src-chip">🆓 Openverse — Creative Commons</span>
          <span class="src-chip">🚀 NASA — Space & science imagery</span>
          <span class="src-chip">🏛️ Met Museum — Art & artifacts</span>
          <span class="src-chip">🎨 Picsum — Curated HD photos</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_trend, tab_search, tab_cats = st.tabs(["🔥 Trending", "🔍 Search", "🗂️ Categories"])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — TRENDING
    # ══════════════════════════════════════════════════════════
    with tab_trend:
        st.markdown("#### ✨ Curated High-Quality Free Photos")
        if st.button("🔄 Refresh Trending", key="fp_refresh_trending"):
            st.cache_data.clear()
            st.rerun()

        with st.spinner("Loading beautiful photos…"):
            trending = get_trending_photos(st.session_state.fp_count)

        st.markdown(f"""
        <div class="fp-stats">
          <div class="fp-stat">Showing <b>{len(trending)}</b> photos</div>
          <div class="fp-stat">Source <b>Picsum HD</b></div>
          <div class="fp-stat">License <b>Free to use</b></div>
        </div>
        """, unsafe_allow_html=True)

        _render_photo_grid(trending, key_prefix="trend")

    # ══════════════════════════════════════════════════════════
    # TAB 2 — SEARCH
    # ══════════════════════════════════════════════════════════
    with tab_search:
        st.markdown("#### 🔍 Search Millions of Free Photos")

        sc1, sc2 = st.columns([5, 1])
        with sc1:
            query = st.text_input(
                "Search",
                value=st.session_state.fp_query,
                placeholder="mountains, ocean sunset, abstract art, cats…",
                key="fp_search_input",
                label_visibility="collapsed",
            )
        with sc2:
            search_btn = st.button("🔍 Go", use_container_width=True, key="fp_search_go", type="primary")

        # Quick topic pills
        quick_topics = ["🌅 Sunset", "🌊 Ocean", "🏔️ Mountains", "🌸 Flowers",
                        "🦁 Animals", "🏙️ City", "🚀 Space", "🎨 Abstract",
                        "🍜 Food", "🌿 Nature", "🦋 Macro", "❄️ Winter"]
        st.markdown('<div style="margin:8px 0;">', unsafe_allow_html=True)
        pill_cols = st.columns(6)
        for i, topic in enumerate(quick_topics):
            with pill_cols[i % 6]:
                if st.button(topic, key=f"fp_pill_{i}", use_container_width=True):
                    st.session_state.fp_query = topic.split(" ", 1)[-1]
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if search_btn or query != st.session_state.fp_query:
            st.session_state.fp_query = query

        if st.session_state.fp_query.strip():
            with st.spinner(f"Searching across {len(st.session_state.fp_sources)} sources…"):
                result = search_free_pictures(
                    st.session_state.fp_query,
                    count=st.session_state.fp_count,
                    sources=st.session_state.fp_sources,
                )
            photos = result["results"]
            sources_used = result["sources_used"]

            st.markdown(f"""
            <div class="fp-stats">
              <div class="fp-stat">Found <b>{len(photos)}</b> photos</div>
              <div class="fp-stat">Query <b>{st.session_state.fp_query[:20]}</b></div>
              {''.join(f'<div class="fp-stat"><b>{s}</b></div>' for s in sources_used)}
            </div>
            """, unsafe_allow_html=True)

            _render_photo_grid(photos, key_prefix="search")
        else:
            st.info("🔍 Enter a search term above to find free photos from 6+ sources")

    # ══════════════════════════════════════════════════════════
    # TAB 3 — CATEGORIES
    # ══════════════════════════════════════════════════════════
    with tab_cats:
        st.markdown("#### 🗂️ Browse by Category")
        cats = get_all_categories()

        # Category selector
        cat_cols = st.columns(4)
        for i, cat in enumerate(cats):
            with cat_cols[i % 4]:
                pack_info = CATEGORY_PACKS.get(cat, {})
                desc = pack_info.get("description", "")[:40]
                is_active = st.session_state.fp_active_cat == cat
                btn_style = "primary" if is_active else "secondary"
                if st.button(f"{cat}", key=f"fp_cat_{i}", use_container_width=True, type=btn_style):
                    st.session_state.fp_active_cat = cat
                    st.rerun()

        st.divider()

        active_cat = st.session_state.fp_active_cat
        pack_info = CATEGORY_PACKS.get(active_cat, {})
        st.markdown(f"**{active_cat}** — {pack_info.get('description', '')}")

        with st.spinner(f"Loading {active_cat} photos…"):
            cat_photos = get_category_pack(active_cat, st.session_state.fp_count)

        st.markdown(f"""
        <div class="fp-stats">
          <div class="fp-stat">Category <b>{active_cat}</b></div>
          <div class="fp-stat">Loaded <b>{len(cat_photos)}</b> photos</div>
          <div class="fp-stat">License <b>Free / CC</b></div>
        </div>
        """, unsafe_allow_html=True)

        _render_photo_grid(cat_photos, key_prefix=f"cat_{active_cat[:10].replace(' ', '_')}")

    if st.button("← Back to Chat", key="fp_back_chat", use_container_width=True):
        st.session_state.app_mode = "chat"
        st.rerun()
