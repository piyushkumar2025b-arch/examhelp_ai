"""
media_hub_addon.py — 4 new Smart Reader subsections
Tab 1: 🖼️ Image Explorer   (free APIs, no AI)
Tab 2: 🤖 Mini AI Answerer  (structured answers, free LLMs)
Tab 3: 🔥 AI & OSS Trends   (GitHub trending, AI news, HuggingFace)
Tab 4: 📚 E-Book & Audio    (Gutenberg, Open Library, LibriVox)
"""
import streamlit as st
import io, zipfile, requests

# ─── shared CSS ───────────────────────────────────────────────────────────────
_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Mono&display=swap');
.mh-card{background:rgba(15,23,42,.8);border:1px solid rgba(255,255,255,.07);
 border-radius:16px;padding:18px;margin-bottom:12px;transition:.2s;}
.mh-card:hover{border-color:rgba(99,102,241,.4);transform:translateY(-2px);}
.mh-badge{display:inline-block;padding:2px 10px;border-radius:100px;font-size:10px;
 background:rgba(99,102,241,.12);border:1px solid rgba(99,102,241,.25);color:#a5b4fc;margin:2px;}
.mh-title{font-family:'Inter',sans-serif;font-size:1rem;font-weight:600;color:#fff;margin-bottom:4px;}
.mh-sub{font-size:.78rem;color:rgba(255,255,255,.45);font-family:'Space Mono',monospace;}
.mh-chip{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);
 border-radius:8px;padding:6px 10px;font-size:.75rem;color:rgba(255,255,255,.6);
 display:inline-block;margin:2px;}
.img-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin-top:12px;}
.img-item{border-radius:12px;overflow:hidden;position:relative;background:#0f172a;
 border:1px solid rgba(255,255,255,.07);}
.img-item img{width:100%;height:140px;object-fit:cover;display:block;}
.img-meta{padding:6px 8px;font-size:9px;color:rgba(255,255,255,.4);font-family:'Space Mono',monospace;}
.palette-dot{width:22px;height:22px;border-radius:50%;display:inline-block;
 margin:2px;border:2px solid rgba(255,255,255,.15);}
.book-card{display:flex;gap:14px;background:rgba(15,23,42,.7);border:1px solid rgba(255,255,255,.07);
 border-radius:14px;padding:14px;margin-bottom:10px;}
.book-cover{width:60px;min-width:60px;height:90px;border-radius:8px;object-fit:cover;
 background:#1e293b;display:flex;align-items:center;justify-content:center;font-size:1.8rem;}
.trend-card{background:rgba(15,23,42,.75);border:1px solid rgba(255,255,255,.07);
 border-radius:14px;padding:14px 18px;margin-bottom:10px;transition:.2s;}
.trend-card:hover{border-color:rgba(99,102,241,.4);}
.stars{color:#facc15;font-size:.75rem;}
</style>"""


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — IMAGE EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
def _tab_image_explorer():
    st.markdown("### 🖼️ Image Explorer")
    st.markdown('<p style="color:rgba(255,255,255,.5);font-size:.85rem;">Search & download images from Openverse, Unsplash, Pexels and Pixabay — all free.</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([4, 2, 1])
    with c1:
        query = st.text_input("🔍 Search images:", placeholder="e.g. mountain sunset, space nebula…", key="mh_img_q", label_visibility="collapsed")
    with c2:
        sources = st.multiselect("Sources:", ["Openverse","Unsplash","Pexels","Pixabay"],
                                 default=["Openverse","Unsplash"], key="mh_img_src")
    with c3:
        per_page = st.selectbox("Count:", [12,24,48], key="mh_img_n", label_visibility="collapsed")

    col_search, col_page = st.columns([3,1])
    with col_search:
        do_search = st.button("🔍 Search Images", type="primary", use_container_width=True, key="mh_img_go")
    with col_page:
        page = st.number_input("Page", min_value=1, value=1, step=1, key="mh_img_page", label_visibility="collapsed")

    if do_search and query:
        st.session_state["mh_img_results"] = None
        with st.spinner(f"Searching {len(sources)} sources…"):
            try:
                from media_hub_engine import search_images
                results = search_images(query, sources=sources or ["Openverse","Unsplash"],
                                        page=page, per_page=per_page)
                st.session_state["mh_img_results"] = results
                st.session_state["mh_img_query"]   = query
            except Exception as e:
                st.error(f"Search error: {e}")

    results = st.session_state.get("mh_img_results")
    if results is None:
        st.markdown('<div style="text-align:center;padding:40px;color:rgba(255,255,255,.2);font-family:Space Mono,monospace;font-size:.8rem;">ENTER A QUERY AND HIT SEARCH</div>', unsafe_allow_html=True)
        return

    if not results:
        st.warning("No results found. Try different keywords or sources.")
        return

    st.success(f"✅ Found **{len(results)}** images for **{st.session_state.get('mh_img_query','')}**")

    # Source badge counts
    from collections import Counter
    src_counts = Counter(r["source"] for r in results)
    badges = "".join(f'<span class="mh-badge">{s} {c}</span>' for s,c in src_counts.items())
    st.markdown(badges, unsafe_allow_html=True)

    # Bulk download
    if st.button("⬇️ Download All as ZIP", key="mh_img_zip"):
        with st.spinner("Bundling images…"):
            try:
                from media_hub_engine import bulk_download_zip
                zdata = bulk_download_zip(results)
                if zdata:
                    st.download_button("📦 Download ZIP", zdata, "images.zip", key="mh_img_zip_dl")
                else:
                    st.warning("Could not download images.")
            except Exception as e:
                st.error(str(e))

    # Image grid (4 columns)
    cols = st.columns(4)
    for i, img in enumerate(results):
        with cols[i % 4]:
            if img.get("thumb"):
                try:
                    st.image(img["thumb"], use_container_width=True)
                except Exception:
                    st.markdown(f'<div style="height:100px;background:#1e293b;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#666;">🖼️</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="mh-sub">{img.get("title","")[:35]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="mh-sub">by {img.get("author","")[:20]} · <span class="mh-badge">{img.get("source","")}</span></div>', unsafe_allow_html=True)

            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("⬇️", key=f"mh_dl_{i}", help="Download", use_container_width=True):
                    try:
                        from media_hub_engine import download_image_bytes
                        b = download_image_bytes(img["url"])
                        if b:
                            ext = "jpg"
                            st.download_button("💾 Save", b, f"image_{i}.{ext}", key=f"mh_save_{i}", use_container_width=True)
                    except Exception as e:
                        st.error(str(e))
            with c_b:
                if img.get("source_url"):
                    st.link_button("🔗", img["source_url"], use_container_width=True)

    # Color palette for first image
    st.markdown("---")
    if st.button("🎨 Extract Palette from 1st Image", key="mh_palette"):
        try:
            from media_hub_engine import download_image_bytes, extract_color_palette
            b = download_image_bytes(results[0]["url"])
            if b:
                colors = extract_color_palette(b)
                dots = "".join(f'<span class="palette-dot" style="background:{c};" title="{c}"></span>' for c in colors)
                codes = "  ".join(colors)
                st.markdown(f'<div>Dominant colors: {dots}<br><code style="font-size:.7rem;">{codes}</code></div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MINI AI ANSWERER (placeholder, filled in Step 4)
# ═══════════════════════════════════════════════════════════════════════════════
def _tab_mini_ai():
    st.markdown("### 🤖 Mini AI Answerer")
    st.markdown('<p style="color:rgba(255,255,255,.5);font-size:.85rem;">Ask anything — choose format, get structured answers with sources. Zero AI quota.</p>', unsafe_allow_html=True)

    try:
        from mini_ai_engine import FORMAT_TEMPLATES, structured_answer, wiki_search
    except ImportError as e:
        st.error(f"mini_ai_engine not found: {e}"); return

    # ── Query + format ──
    query = st.text_area("💬 Your question:", height=90, placeholder="e.g. How does photosynthesis work? What is quantum computing?", key="mh_ai_q", label_visibility="collapsed")

    c1, c2 = st.columns([2, 2])
    with c1:
        fmt = st.selectbox("📋 Reply format:", list(FORMAT_TEMPLATES.keys()), key="mh_ai_fmt")
    with c2:
        inc_wiki = st.checkbox("📖 Include Wikipedia context", value=True, key="mh_ai_wiki")

    custom_instr = ""
    if fmt == "Custom":
        custom_instr = st.text_input("✏️ Your custom format instruction:", placeholder="e.g. Answer in exactly 3 sentences with an emoji at each sentence start.", key="mh_ai_custom")

    inc_src = st.checkbox("🔗 Show sources", value=True, key="mh_ai_src")

    go = st.button("🚀 Get Answer", type="primary", use_container_width=True, key="mh_ai_go")

    # ── Also: related Wikipedia pages ──
    st.markdown("---")
    st.markdown("**🔍 Quick Wikipedia Search:**")
    wiki_q = st.text_input("Search Wikipedia:", placeholder="Type a topic…", key="mh_wiki_q", label_visibility="collapsed")
    if wiki_q:
        with st.spinner("Searching Wikipedia…"):
            pages = wiki_search(wiki_q, limit=5)
        if pages:
            for p in pages:
                st.markdown(f'• **[{p["title"]}]({p["url"]})** — {p["snippet"][:120]}…')
        else:
            st.info("No Wikipedia results found.")

    # ── Generate answer ──
    if go and query.strip():
        with st.spinner("Thinking… (this may take ~15s for AI synthesis)"):
            try:
                result = structured_answer(
                    query.strip(), fmt=fmt, custom_instruction=custom_instr,
                    include_sources=inc_src, include_wiki=inc_wiki,
                )
            except Exception as e:
                st.error(f"Error: {e}"); return

        # Show wiki image if available
        if result.get("wiki_image"):
            c_img, c_ans = st.columns([1, 3])
            with c_img:
                st.image(result["wiki_image"], use_container_width=True)
            with c_ans:
                st.markdown(result["answer"])
        else:
            st.markdown(result["answer"])

        # Sources
        if inc_src and result.get("sources"):
            st.markdown("---")
            st.markdown("**📚 Sources:**")
            for s in result["sources"]:
                st.markdown(f'• [{s["title"]}]({s["url"]})')



# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI & OSS TRENDS (placeholder, filled in Step 6)
# ═══════════════════════════════════════════════════════════════════════════════
def _tab_trends():
    st.markdown("### 🔥 AI & OSS Trends")
    st.markdown('<p style="color:rgba(255,255,255,.5);font-size:.85rem;">GitHub trending repos · AI news · HuggingFace models · Search & download open source projects.</p>', unsafe_allow_html=True)

    try:
        from trends_engine import (get_github_trending, search_github_repos,
                                   get_hf_trending, get_ai_news)
    except ImportError as e:
        st.error(f"trends_engine not found: {e}"); return

    tr1, tr2, tr3, tr4 = st.tabs(["⭐ GitHub Trending","🔍 Repo Search","🤗 HuggingFace","📰 AI News"])

    # ── GitHub Trending ──
    with tr1:
        c1, c2 = st.columns(2)
        with c1:
            lang = st.selectbox("Language:", ["","Python","JavaScript","TypeScript","Rust","Go","C++","Java","C","Swift","Kotlin"], key="tr_lang", label_visibility="collapsed")
        with c2:
            period = st.selectbox("Period:", ["daily","weekly","monthly"], key="tr_period", label_visibility="collapsed")
        if st.button("🔄 Load Trending", type="primary", use_container_width=True, key="tr_gh_go"):
            with st.spinner("Fetching GitHub trending…"):
                st.session_state["tr_gh_results"] = get_github_trending(lang, period)

        repos = st.session_state.get("tr_gh_results")
        if repos is None:
            st.info("Hit **Load Trending** to fetch repos.")
        elif not repos:
            st.warning("No trending repos found.")
        else:
            for repo in repos:
                with st.container():
                    st.markdown(f"""
<div class="trend-card">
  <div style="display:flex;align-items:center;gap:10px;">
    <img src="{repo['avatar']}" width="32" height="32" style="border-radius:50%;" />
    <a href="{repo['url']}" target="_blank" style="color:#a5b4fc;font-weight:600;font-size:.95rem;text-decoration:none;">
      {repo['name']}
    </a>
    <span class="mh-badge">{repo.get('language','')}</span>
    <span class="stars">⭐ {repo.get('stars',0):,}</span>
  </div>
  <div style="color:rgba(255,255,255,.5);font-size:.8rem;margin-top:6px;">{repo.get('description','')}</div>
</div>""", unsafe_allow_html=True)
                    ca, cb, cc = st.columns(3)
                    with ca: st.link_button("🔗 GitHub", repo["url"], use_container_width=True)
                    with cb: st.link_button("📦 Download ZIP", repo["zip_url"], use_container_width=True)
                    with cc: st.code(f"git clone {repo['clone_url']}", language=None)

    # ── Repo Search ──
    with tr2:
        q = st.text_input("🔍 Search GitHub repos:", placeholder="e.g. llm inference, image segmentation…", key="tr_search_q", label_visibility="collapsed")
        if st.button("Search Repos", type="primary", use_container_width=True, key="tr_search_go") and q:
            with st.spinner("Searching GitHub…"):
                st.session_state["tr_search_results"] = search_github_repos(q, limit=15)

        s_repos = st.session_state.get("tr_search_results")
        if s_repos:
            st.success(f"Found {len(s_repos)} repos for **{q}**")
            for repo in s_repos:
                st.markdown(f"""
<div class="trend-card">
  <div style="display:flex;align-items:center;gap:10px;">
    <img src="{repo['avatar']}" width="28" height="28" style="border-radius:50%;"/>
    <a href="{repo['url']}" target="_blank" style="color:#a5b4fc;font-weight:600;">{repo['name']}</a>
    <span class="mh-badge">{repo.get('language','')}</span>
    <span class="stars">⭐ {repo.get('stars',0):,}</span>
    <span style="font-size:.7rem;color:rgba(255,255,255,.3);">🍴 {repo.get('forks',0):,}</span>
  </div>
  <div style="color:rgba(255,255,255,.5);font-size:.78rem;margin-top:4px;">{repo.get('description','')}</div>
  <div style="margin-top:4px;">{''.join(f'<span class="mh-badge">{t}</span>' for t in repo.get('topics',[]))}</div>
</div>""", unsafe_allow_html=True)
                ca, cb = st.columns(2)
                with ca: st.link_button("📦 ZIP", repo["zip_url"], use_container_width=True)
                with cb: st.code(f"git clone {repo['clone_url']}", language=None)

    # ── HuggingFace ──
    with tr3:
        if st.button("🤗 Load Trending Models", type="primary", use_container_width=True, key="tr_hf_go"):
            with st.spinner("Fetching HuggingFace trending…"):
                st.session_state["tr_hf_results"] = get_hf_trending(limit=20)

        hf_models = st.session_state.get("tr_hf_results")
        if hf_models is None:
            st.info("Click **Load Trending Models** above.")
        elif not hf_models:
            st.warning("Could not fetch HuggingFace data.")
        else:
            for m in hf_models:
                tags = " ".join(f'<span class="mh-badge">{t}</span>' for t in m.get("tags",[])[:4])
                st.markdown(f"""
<div class="trend-card">
  <a href="{m['url']}" target="_blank" style="color:#a5b4fc;font-weight:600;">{m['name']}</a>
  <span class="mh-badge" style="margin-left:8px;">{m.get('pipeline','')}</span>
  <span style="float:right;font-size:.75rem;color:#facc15;">❤️ {m.get('likes',0):,} &nbsp; ⬇️ {m.get('downloads',0):,}</span>
  <div style="margin-top:4px;">{tags}</div>
</div>""", unsafe_allow_html=True)

    # ── AI News ──
    with tr4:
        if st.button("📰 Load AI News", type="primary", use_container_width=True, key="tr_news_go"):
            with st.spinner("Fetching AI news from RSS feeds…"):
                st.session_state["tr_news_results"] = get_ai_news(limit_per_feed=6)

        news = st.session_state.get("tr_news_results")
        if news is None:
            st.info("Click **Load AI News** above.")
        elif not news:
            st.warning("No news fetched. Check your connection.")
        else:
            st.success(f"Loaded **{len(news)}** articles from {len(set(n['source'] for n in news))} sources")
            for article in news:
                ca, cb = st.columns([1, 3])
                with ca:
                    if article.get("image"):
                        try: st.image(article["image"], use_container_width=True)
                        except: st.markdown("📰")
                    else:
                        st.markdown('<div style="height:70px;background:#1e293b;border-radius:8px;display:flex;align-items:center;justify-content:center;">📰</div>', unsafe_allow_html=True)
                with cb:
                    st.markdown(f'**[{article["title"]}]({article["url"]})** <span class="mh-badge">{article["source"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mh-sub">{article["summary"][:150]}…</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mh-sub">{article.get("date","")}</div>', unsafe_allow_html=True)
                st.markdown("---")




# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — E-BOOK & AUDIO (placeholder, filled in Steps 8-9)
# ═══════════════════════════════════════════════════════════════════════════════
def _tab_ebook():
    st.markdown("### 📚 E-Book & Audio Center")
    st.markdown('<p style="color:rgba(255,255,255,.5);font-size:.85rem;">70,000+ free books · Millions of titles · Free audiobooks — read & listen in-app.</p>', unsafe_allow_html=True)

    try:
        from ebook_engine import (search_gutenberg, get_gutenberg_text,
                                  search_open_library, search_librivox,
                                  get_librivox_chapters, search_standard_ebooks)
    except ImportError as e:
        st.error(f"ebook_engine not found: {e}"); return

    eb1, eb2, eb3, eb4 = st.tabs(["📖 Read Books","🎧 Audiobooks","🔍 Open Library","✨ Standard Ebooks"])

    # ── TAB A: E-Book Reader (Gutenberg) ──────────────────────────────────────
    with eb1:
        st.markdown("**📚 Project Gutenberg — 70,000+ free books**")
        q = st.text_input("Search by title or author:", placeholder="e.g. Sherlock Holmes, Jane Austen…", key="eb_gut_q", label_visibility="collapsed")
        c1, c2 = st.columns([3,1])
        with c1:
            do_search = st.button("🔍 Search Gutenberg", type="primary", use_container_width=True, key="eb_gut_go")
        with c2:
            gut_page = st.number_input("Page", min_value=1, value=1, step=1, key="eb_gut_page", label_visibility="collapsed")

        if do_search and q:
            with st.spinner("Searching Gutenberg…"):
                st.session_state["eb_gut_results"] = search_gutenberg(q, gut_page)

        gut_data = st.session_state.get("eb_gut_results")
        if gut_data:
            books = gut_data.get("results", [])
            if not books:
                st.warning("No books found.")
            else:
                st.success(f"**{gut_data['count']:,}** books found — showing {len(books)}")
                cols = st.columns(3)
                for i, b in enumerate(books):
                    with cols[i % 3]:
                        if b.get("cover"):
                            try: st.image(b["cover"], use_container_width=True)
                            except: pass
                        st.markdown(f'<div class="mh-title">{b["title"][:50]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="mh-sub">{b["authors"][:40]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="mh-sub">⬇️ {b.get("download_count",0):,} downloads</div>', unsafe_allow_html=True)
                        tags = " ".join(f'<span class="mh-badge">{s[:20]}</span>' for s in b.get("subjects",[])[:2])
                        st.markdown(tags, unsafe_allow_html=True)

                        ca, cb, cc = st.columns(3)
                        with ca:
                            if st.button("📖 Read", key=f"eb_read_{b['id']}", use_container_width=True):
                                with st.spinner("Loading book…"):
                                    text = get_gutenberg_text(b["id"])
                                    if text:
                                        st.session_state["eb_reading"] = {"title": b["title"], "text": text, "page": 0}
                                    else:
                                        st.warning("Text not available.")
                        with cb:
                            if b.get("download_epub"):
                                st.link_button("⬇️ EPUB", b["download_epub"], use_container_width=True)
                        with cc:
                            if b.get("download_txt"):
                                st.link_button("📄 TXT", b["download_txt"], use_container_width=True)

        # ── In-app reader ──
        reading = st.session_state.get("eb_reading")
        if reading:
            st.markdown("---")
            st.markdown(f"### 📖 Reading: *{reading['title']}*")
            text = reading["text"]
            PAGE_CHARS = 3000
            total_pages = max(1, -(-len(text) // PAGE_CHARS))

            c_prev, c_info, c_next = st.columns([1,3,1])
            with c_prev:
                if st.button("◀ Prev", key="eb_prev", disabled=(reading["page"]==0)):
                    st.session_state["eb_reading"]["page"] -= 1; st.rerun()
            with c_info:
                st.markdown(f'<div style="text-align:center;color:rgba(255,255,255,.5);">Page {reading["page"]+1} / {total_pages}</div>', unsafe_allow_html=True)
            with c_next:
                if st.button("Next ▶", key="eb_next", disabled=(reading["page"]>=total_pages-1)):
                    st.session_state["eb_reading"]["page"] += 1; st.rerun()

            chunk = text[reading["page"]*PAGE_CHARS : (reading["page"]+1)*PAGE_CHARS]

            font_sz = st.slider("Font size", 12, 22, 16, key="eb_font")
            st.markdown(
                f'<div style="background:rgba(255,255,255,.03);border-radius:12px;padding:24px;'
                f'font-size:{font_sz}px;line-height:1.8;color:rgba(255,255,255,.85);'
                f'white-space:pre-wrap;font-family:Georgia,serif;">{chunk}</div>',
                unsafe_allow_html=True
            )
            st.download_button("⬇️ Download Full TXT", text.encode("utf-8"),
                               f"{reading['title'][:30]}.txt", key="eb_dl_txt")
            if st.button("✖ Close Book", key="eb_close"):
                del st.session_state["eb_reading"]; st.rerun()

    # ── TAB B: LibriVox Audiobooks ─────────────────────────────────────────────
    with eb2:
        st.markdown("**🎧 LibriVox — Free Public Domain Audiobooks**")
        lv_q = st.text_input("Search audiobooks:", placeholder="e.g. Dracula, Mark Twain, Adventures…", key="eb_lv_q", label_visibility="collapsed")
        if st.button("🔍 Search Audiobooks", type="primary", use_container_width=True, key="eb_lv_go") and lv_q:
            with st.spinner("Searching LibriVox…"):
                st.session_state["eb_lv_results"] = search_librivox(lv_q)

        lv_books = st.session_state.get("eb_lv_results")
        if lv_books is None:
            st.info("Search for an audiobook above.")
        elif not lv_books:
            st.warning("No audiobooks found.")
        else:
            st.success(f"Found **{len(lv_books)}** audiobooks")
            for bk in lv_books:
                with st.expander(f"🎧 {bk['title']} — {bk['authors']}", expanded=False):
                    ca, cb = st.columns([1,3])
                    with ca:
                        st.markdown(f'<div style="background:#1e293b;border-radius:8px;height:80px;display:flex;align-items:center;justify-content:center;font-size:2rem;">🎧</div>', unsafe_allow_html=True)
                    with cb:
                        st.markdown(f"**{bk['title']}**")
                        st.markdown(f'<div class="mh-sub">{bk["authors"]} · {bk["language"]} · {bk["sections"]} chapters</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="mh-sub">{bk["description"]}</div>', unsafe_allow_html=True)

                    if bk.get("url_librivox"):
                        st.link_button("🔗 Open in LibriVox", bk["url_librivox"], use_container_width=True)

                    # Load chapters
                    if st.button(f"📋 Load Chapters", key=f"eb_chap_{bk['id']}", use_container_width=True):
                        with st.spinner("Loading chapters…"):
                            chapters = get_librivox_chapters(str(bk["id"]))
                            st.session_state[f"eb_chap_{bk['id']}"] = chapters

                    chapters = st.session_state.get(f"eb_chap_{bk['id']}", [])
                    if chapters:
                        st.markdown(f"**{len(chapters)} chapters:**")
                        for ch in chapters:
                            cc1, cc2 = st.columns([3,1])
                            with cc1:
                                st.markdown(f'<div class="mh-sub">🎵 {ch["title"]} ({ch.get("duration","")})</div>', unsafe_allow_html=True)
                            with cc2:
                                if ch.get("listen_url"):
                                    st.audio(ch["listen_url"])
                        if bk.get("url_rss"):
                            st.link_button("📻 RSS Feed", bk["url_rss"], use_container_width=True)

    # ── TAB C: Open Library ────────────────────────────────────────────────────
    with eb3:
        st.markdown("**📚 Open Library — Millions of Books**")
        ol_q = st.text_input("Search Open Library:", placeholder="e.g. Harry Potter, machine learning…", key="eb_ol_q", label_visibility="collapsed")
        if st.button("🔍 Search", type="primary", use_container_width=True, key="eb_ol_go") and ol_q:
            with st.spinner("Searching Open Library…"):
                st.session_state["eb_ol_results"] = search_open_library(ol_q)

        ol_books = st.session_state.get("eb_ol_results")
        if ol_books is None:
            st.info("Search for a book above.")
        elif not ol_books:
            st.warning("No results found.")
        else:
            st.success(f"Found **{len(ol_books)}** results")
            cols = st.columns(3)
            for i, bk in enumerate(ol_books):
                with cols[i % 3]:
                    if bk.get("cover"):
                        try: st.image(bk["cover"], use_container_width=True)
                        except: pass
                    st.markdown(f'<div class="mh-title">{bk["title"][:45]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mh-sub">{bk["authors"][:35]}</div>', unsafe_allow_html=True)
                    if bk.get("year"):
                        st.markdown(f'<div class="mh-sub">📅 {bk["year"]}</div>', unsafe_allow_html=True)
                    if bk.get("has_full") and bk.get("read_url"):
                        st.link_button("📖 Read Free", bk["read_url"], use_container_width=True)
                    elif bk.get("ol_key"):
                        st.link_button("🔗 Details", f"https://openlibrary.org{bk['ol_key']}", use_container_width=True)

    # ── TAB D: Standard Ebooks ────────────────────────────────────────────────
    with eb4:
        st.markdown("**✨ Standard Ebooks — Beautiful Free Ebooks**")
        se_q = st.text_input("Search Standard Ebooks:", placeholder="e.g. Dickens, Frankenstein, Hamlet…", key="eb_se_q", label_visibility="collapsed")
        if st.button("🔍 Search", type="primary", use_container_width=True, key="eb_se_go") and se_q:
            with st.spinner("Searching Standard Ebooks catalog…"):
                st.session_state["eb_se_results"] = search_standard_ebooks(se_q)

        se_books = st.session_state.get("eb_se_results")
        if se_books is None:
            st.info("Search Standard Ebooks above.")
        elif not se_books:
            st.warning("No results found.")
        else:
            st.success(f"Found **{len(se_books)}** Standard Ebooks")
            for bk in se_books:
                with st.container():
                    ca, cb = st.columns([1,4])
                    with ca:
                        if bk.get("cover"):
                            try: st.image(bk["cover"], use_container_width=True)
                            except: st.markdown("📚")
                        else:
                            st.markdown('<div style="height:80px;background:#1e293b;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2rem;">📚</div>', unsafe_allow_html=True)
                    with cb:
                        st.markdown(f'**{bk["title"]}** — {bk["authors"]}')
                        st.markdown(f'<div class="mh-sub">{bk["description"]}</div>', unsafe_allow_html=True)
                        if bk.get("epub_url"):
                            st.link_button("⬇️ Download EPUB", bk["epub_url"], use_container_width=True)
                    st.markdown("---")




# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def render_media_hub():
    st.markdown(_CSS, unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs([
        "🖼️ Image Explorer",
        "🤖 Mini Answerer",
        "🔥 AI & OSS Trends",
        "📚 E-Book & Audio",
    ])
    with t1: _tab_image_explorer()
    with t2: _tab_mini_ai()
    with t3: _tab_trends()
    with t4: _tab_ebook()
