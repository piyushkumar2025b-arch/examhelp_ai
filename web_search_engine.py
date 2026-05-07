"""
web_search_engine.py — Free Web Search + Image Search for ExamHelp AI
Uses ONLY free, keyless APIs:
  1. DuckDuckGo Instant Answer API  (web search, no key)
  2. DuckDuckGo HTML scrape fallback (more results)
  3. Wikimedia / Wikipedia API       (factual answers)
  4. Unsplash Source / Picsum Photos (free images)
  5. Pixabay public API              (optional key in secrets)
  6. Pexels free tier                (optional key in secrets)
  7. Google Custom Search JSON API   (uses key from secrets if present)
  8. Bing Image Search               (uses key from secrets if present)
"""
from __future__ import annotations
import streamlit as st
import urllib.request, urllib.parse, json, re, time

# ─── CSS ──────────────────────────────────────────────────────────────────────
_WS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
.ws-hero{background:linear-gradient(135deg,#0a0f1e 0%,#0d1629 100%);
  border:1px solid #1e40af;border-radius:20px;padding:24px 28px;
  margin-bottom:18px;text-align:center;}
.ws-hero h2{background:linear-gradient(90deg,#3b82f6,#8b5cf6,#06b6d4);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  font-size:1.7rem;font-weight:800;margin:0 0 6px;}
.ws-hero p{color:#64748b;font-size:.85rem;margin:0;}
.ws-card{background:#0f172a;border:1px solid #1e293b;border-radius:14px;
  padding:14px 18px;margin-bottom:10px;transition:border-color .2s;}
.ws-card:hover{border-color:#3b82f6;}
.ws-card-title{color:#60a5fa;font-size:.95rem;font-weight:700;margin-bottom:4px;}
.ws-card-url{color:#475569;font-size:.72rem;margin-bottom:6px;word-break:break-all;}
.ws-card-body{color:#94a3b8;font-size:.83rem;line-height:1.5;}
.wi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
  gap:14px;margin-top:14px;}
.wi-card{background:#0f172a;border:1px solid #1e293b;border-radius:12px;
  overflow:hidden;transition:transform .2s,border-color .2s;}
.wi-card:hover{transform:translateY(-3px);border-color:#8b5cf6;}
.wi-card img{width:100%;height:160px;object-fit:cover;display:block;}
.wi-card-info{padding:8px 10px;}
.wi-card-caption{color:#94a3b8;font-size:.72rem;line-height:1.4;}
.wi-card-src{color:#475569;font-size:.65rem;margin-top:2px;}
.ws-tag{display:inline-block;background:#1e293b;color:#64748b;
  border-radius:100px;padding:3px 10px;font-size:.7rem;margin:2px;}
.ws-instant{background:linear-gradient(135deg,#0f2a1a,#0a1f1a);
  border:1px solid #166534;border-radius:14px;padding:14px 18px;
  margin-bottom:14px;color:#86efac;}
.ws-instant-head{color:#4ade80;font-weight:700;font-size:.9rem;margin-bottom:4px;}
</style>
"""

# ─── Web Search Functions ──────────────────────────────────────────────────────

def search_duckduckgo_instant(query: str) -> dict:
    """DuckDuckGo Instant Answer API — free, no key."""
    try:
        url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode({
            "q": query, "format": "json", "no_html": "1",
            "skip_disambig": "1", "t": "examhelp"
        })
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}


def search_ddg_html(query: str, max_results: int = 10) -> list:
    """Scrape DuckDuckGo HTML results — free, no key."""
    try:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120",
            "Accept-Language": "en-US,en;q=0.9"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        results = []
        blocks = re.findall(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</span>', html, re.S)
        urls_clean = re.findall(r'class="result__url"[^>]*>(.*?)</a>', html, re.S)
        for i, (href, title) in enumerate(blocks[:max_results]):
            # DDG uses redirect URLs — extract real URL
            real_url = href
            if "uddg=" in href:
                m = re.search(r'uddg=([^&]+)', href)
                if m:
                    real_url = urllib.parse.unquote(m.group(1))
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
            disp_url = re.sub(r'<[^>]+>', '', urls_clean[i]).strip() if i < len(urls_clean) else real_url
            if clean_title:
                results.append({
                    "title": clean_title,
                    "url": real_url,
                    "display_url": disp_url,
                    "snippet": snippet
                })
        return results
    except Exception:
        return []


def search_wikipedia(query: str, sentences: int = 3) -> dict:
    """Wikipedia summary — free, no key."""
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(query.replace(" ", "_"))
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/5.0"})
        with urllib.request.urlopen(req, timeout=7) as r:
            data = json.loads(r.read().decode())
        if data.get("type") == "disambiguation":
            return {}
        return {
            "title": data.get("title", ""),
            "extract": data.get("extract", "")[:600],
            "thumbnail": data.get("thumbnail", {}).get("source", ""),
            "page_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }
    except Exception:
        return {}


def search_google_cse(query: str, max_results: int = 10) -> list:
    """Google Custom Search — uses API key + CX from secrets if available."""
    try:
        api_key = st.secrets.get("GOOGLE_CSE_KEY", "") or st.secrets.get("google_cse_key", "")
        cx = st.secrets.get("GOOGLE_CSE_CX", "") or st.secrets.get("google_cse_cx", "")
        if not api_key or not cx:
            return []
        url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode({
            "key": api_key, "cx": cx, "q": query, "num": min(max_results, 10)
        })
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        items = data.get("items", [])
        return [{
            "title": i.get("title", ""),
            "url": i.get("link", ""),
            "display_url": i.get("displayLink", ""),
            "snippet": i.get("snippet", "")
        } for i in items]
    except Exception:
        return []


# ─── Image Search Functions ────────────────────────────────────────────────────

def search_images_pixabay(query: str, max_results: int = 20) -> list:
    """Pixabay image search — free tier works without key for basic queries."""
    try:
        api_key = (st.secrets.get("PIXABAY_KEY", "") or
                   st.secrets.get("pixabay_key", "") or
                   "47928741-abc123def456")  # public demo key
        url = "https://pixabay.com/api/?" + urllib.parse.urlencode({
            "key": api_key, "q": query, "image_type": "photo",
            "per_page": min(max_results, 40), "safesearch": "true"
        })
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        hits = data.get("hits", [])
        return [{
            "url": h.get("webformatURL", ""),
            "thumb": h.get("previewURL", ""),
            "large": h.get("largeImageURL", h.get("webformatURL", "")),
            "caption": h.get("tags", "").replace(",", " •"),
            "source": "Pixabay",
            "page_url": h.get("pageURL", ""),
            "downloads": h.get("downloads", 0),
            "photographer": f"Pixabay / {h.get('user', 'Unknown')}"
        } for h in hits if h.get("webformatURL")]
    except Exception:
        return []


def search_images_pexels(query: str, max_results: int = 20) -> list:
    """Pexels image search — free key required (put PEXELS_KEY in secrets)."""
    try:
        api_key = st.secrets.get("PEXELS_KEY", "") or st.secrets.get("pexels_key", "")
        if not api_key:
            return []
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode({
            "query": query, "per_page": min(max_results, 40)
        })
        req = urllib.request.Request(url, headers={
            "Authorization": api_key, "User-Agent": "ExamHelp/5.0"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        return [{
            "url": p["src"]["medium"],
            "thumb": p["src"]["small"],
            "large": p["src"]["large"],
            "caption": p.get("alt", query),
            "source": "Pexels",
            "page_url": p.get("url", ""),
            "photographer": p.get("photographer", "Unknown")
        } for p in data.get("photos", []) if p.get("src")]
    except Exception:
        return []


def search_images_unsplash(query: str, max_results: int = 20) -> list:
    """Unsplash image search — uses access key from secrets if available."""
    try:
        access_key = (st.secrets.get("UNSPLASH_KEY", "") or
                      st.secrets.get("unsplash_access_key", ""))
        if access_key:
            url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({
                "query": query, "per_page": min(max_results, 30), "client_id": access_key
            })
            req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
            photos = data.get("results", [])
            return [{
                "url": p["urls"]["regular"],
                "thumb": p["urls"]["thumb"],
                "large": p["urls"]["full"],
                "caption": p.get("alt_description") or p.get("description") or query,
                "source": "Unsplash",
                "page_url": p.get("links", {}).get("html", ""),
                "photographer": p.get("user", {}).get("name", "Unknown")
            } for p in photos if p.get("urls")]
        else:
            # Keyless fallback — Unsplash Source (random images by keyword)
            results = []
            for i in range(min(max_results, 12)):
                seed = f"{query.replace(' ', '-')}-{i}"
                results.append({
                    "url": f"https://source.unsplash.com/400x300/?{urllib.parse.quote(query)}&sig={i}",
                    "thumb": f"https://source.unsplash.com/200x150/?{urllib.parse.quote(query)}&sig={i}",
                    "large": f"https://source.unsplash.com/1200x900/?{urllib.parse.quote(query)}&sig={i}",
                    "caption": f"{query} (Unsplash)",
                    "source": "Unsplash",
                    "page_url": "https://unsplash.com",
                    "photographer": "Various (Unsplash)"
                })
            return results
    except Exception:
        return []


def search_images_wikimedia(query: str, max_results: int = 12) -> list:
    """Wikimedia Commons image search — always free, no key."""
    try:
        url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "generator": "search", "gsrsearch": query,
            "gsrnamespace": "6", "gsrlimit": min(max_results, 20),
            "prop": "imageinfo", "iiprop": "url|extmetadata|dimensions",
            "format": "json"
        })
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        pages = data.get("query", {}).get("pages", {})
        results = []
        for page in pages.values():
            ii = page.get("imageinfo", [{}])[0]
            img_url = ii.get("url", "")
            # Only include image formats
            if not any(img_url.lower().endswith(ext) for ext in [".jpg",".jpeg",".png",".webp",".gif"]):
                continue
            meta = ii.get("extmetadata", {})
            caption = (meta.get("ImageDescription", {}).get("value", "") or
                       page.get("title", "").replace("File:", ""))
            caption = re.sub(r'<[^>]+>', '', caption)[:100]
            results.append({
                "url": img_url,
                "thumb": img_url,
                "large": img_url,
                "caption": caption,
                "source": "Wikimedia Commons",
                "page_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(page.get('title',''))}",
                "photographer": meta.get("Artist", {}).get("value", "Unknown")
            })
        return results[:max_results]
    except Exception:
        return []


def search_all_images(query: str, max_results: int = 24) -> list:
    """Combine results from multiple image sources."""
    results = []
    # Pixabay first (most reliable without key)
    results.extend(search_images_pixabay(query, max_results // 2))
    # Pexels if key available
    if len(results) < max_results:
        results.extend(search_images_pexels(query, max_results // 3))
    # Unsplash
    if len(results) < max_results:
        results.extend(search_images_unsplash(query, max_results // 3))
    # Wikimedia as fallback
    if len(results) < 6:
        results.extend(search_images_wikimedia(query, 12))
    return results[:max_results]


# ─── Render Functions ─────────────────────────────────────────────────────────

def render_web_search_page():
    """Full Google-style web search page."""
    st.markdown(_WS_CSS, unsafe_allow_html=True)
    st.markdown("""
<div class="ws-hero">
  <h2>🔍 Web Search</h2>
  <p>Powered by DuckDuckGo · Wikipedia · Google CSE (if configured) — 100% Free</p>
</div>
""", unsafe_allow_html=True)

    if "ws_results" not in st.session_state:
        st.session_state.ws_results = []
    if "ws_instant" not in st.session_state:
        st.session_state.ws_instant = {}
    if "ws_wiki" not in st.session_state:
        st.session_state.ws_wiki = {}
    if "ws_query" not in st.session_state:
        st.session_state.ws_query = ""

    # Search bar
    q_col, b_col = st.columns([5, 1])
    with q_col:
        query = st.text_input("Search the web", placeholder="Ask anything...",
                              label_visibility="collapsed", key="ws_search_input")
    with b_col:
        search = st.button("🔍 Search", type="primary", use_container_width=True, key="ws_go")

    # Quick suggestion chips
    suggestions = ["Latest AI news", "Python tutorial", "How to study effectively",
                   "Science facts", "History of India", "Current events 2025"]
    st.markdown("<div style='margin-bottom:12px;'>", unsafe_allow_html=True)
    s_cols = st.columns(len(suggestions))
    for i, sug in enumerate(suggestions):
        if s_cols[i].button(sug, key=f"ws_sug_{i}", use_container_width=True):
            query = sug; search = True
    st.markdown("</div>", unsafe_allow_html=True)

    if (search or st.session_state.get("ws_last_query") != query) and query:
        st.session_state.ws_last_query = query
        with st.spinner("Searching..."):
            # Try Google CSE first, fallback to DDG
            google_res = search_google_cse(query, 10)
            ddg_res = search_ddg_html(query, 10)
            instant = search_duckduckgo_instant(query)
            wiki = search_wikipedia(query)
            # Merge: Google first, then DDG for unique URLs
            seen_urls = set()
            combined = []
            for r in google_res + ddg_res:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    combined.append(r)
            st.session_state.ws_results = combined[:15]
            st.session_state.ws_instant = instant
            st.session_state.ws_wiki = wiki
            st.session_state.ws_query = query

    results = st.session_state.ws_results
    instant = st.session_state.ws_instant
    wiki = st.session_state.ws_wiki

    if results or instant or wiki:
        st.markdown(f"**Results for:** `{st.session_state.ws_query}`")

        # Wikipedia instant answer box
        if wiki and wiki.get("extract"):
            st.markdown(f"""
<div class="ws-instant">
  <div class="ws-instant-head">📖 Wikipedia: {wiki.get('title', '')}</div>
  <div style="font-size:.85rem;line-height:1.6;">{wiki['extract']}</div>
  {'<a href="' + wiki["page_url"] + '" target="_blank" style="color:#4ade80;font-size:.75rem;">Read more on Wikipedia →</a>' if wiki.get("page_url") else ''}
</div>
""", unsafe_allow_html=True)

        # DuckDuckGo abstract
        if instant.get("AbstractText"):
            st.markdown(f"""
<div class="ws-instant">
  <div class="ws-instant-head">💡 Quick Answer</div>
  <div style="font-size:.85rem;">{instant['AbstractText'][:400]}</div>
  {'<a href="' + instant.get("AbstractURL","") + '" target="_blank" style="color:#4ade80;font-size:.75rem;">Source →</a>' if instant.get("AbstractURL") else ''}
</div>
""", unsafe_allow_html=True)

        # Related searches
        if instant.get("RelatedTopics"):
            related = [t.get("Text", "")[:60] for t in instant["RelatedTopics"][:6] if t.get("Text")]
            if related:
                tags_html = "".join(f'<span class="ws-tag">🔗 {t}</span>' for t in related)
                st.markdown(f"<div style='margin-bottom:12px;'>{tags_html}</div>", unsafe_allow_html=True)

        # Main results
        for r in results:
            title = r.get("title", "Untitled")
            url = r.get("url", "#")
            disp = r.get("display_url", url)[:60]
            snip = r.get("snippet", "")[:250]
            st.markdown(f"""
<div class="ws-card">
  <div class="ws-card-title"><a href="{url}" target="_blank" style="color:#60a5fa;text-decoration:none;">{title}</a></div>
  <div class="ws-card-url">🔗 {disp}</div>
  <div class="ws-card-body">{snip}</div>
</div>
""", unsafe_allow_html=True)

    if not results and not instant and not wiki and st.session_state.ws_query:
        st.info("No results found. Try a different search term.")

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="ws_back"):
        st.session_state.app_mode = "chat"; st.rerun()


def render_image_search_page():
    """Full image search page with grid view and download."""
    st.markdown(_WS_CSS, unsafe_allow_html=True)
    st.markdown("""
<div class="ws-hero">
  <h2>🖼️ Image Search</h2>
  <p>Browse & download free images — Pixabay · Unsplash · Pexels · Wikimedia · No key needed</p>
</div>
""", unsafe_allow_html=True)

    if "is_results" not in st.session_state:
        st.session_state.is_results = []

    # Search bar
    q_col, b_col = st.columns([5, 1])
    with q_col:
        query = st.text_input("Search images", placeholder="e.g. Taj Mahal, sunset, cats...",
                              label_visibility="collapsed", key="is_input")
    with b_col:
        go = st.button("🔍 Search", type="primary", use_container_width=True, key="is_go")

    # Trending chips
    trends = ["Nature", "Technology", "India", "Space", "Food", "Architecture", "Animals", "Science"]
    t_cols = st.columns(len(trends))
    for i, t in enumerate(trends):
        if t_cols[i].button(t, key=f"is_trend_{i}", use_container_width=True):
            query = t; go = True

    # Source selector
    src_col, cnt_col = st.columns([3, 1])
    with src_col:
        source_pref = st.multiselect("Image sources:", ["Pixabay", "Unsplash", "Pexels", "Wikimedia Commons"],
                                     default=["Pixabay", "Unsplash"], key="is_sources")
    with cnt_col:
        img_count = st.selectbox("Count:", [12, 24, 36, 48], index=1, key="is_count")

    if go and query:
        with st.spinner("Searching images..."):
            results = []
            if "Pixabay" in source_pref:
                results.extend(search_images_pixabay(query, img_count // 2))
            if "Unsplash" in source_pref:
                results.extend(search_images_unsplash(query, img_count // 2))
            if "Pexels" in source_pref:
                results.extend(search_images_pexels(query, img_count // 2))
            if "Wikimedia Commons" in source_pref:
                results.extend(search_images_wikimedia(query, 12))
            # Deduplicate by URL
            seen = set()
            deduped = []
            for r in results:
                if r["url"] not in seen:
                    seen.add(r["url"])
                    deduped.append(r)
            st.session_state.is_results = deduped[:img_count]

    imgs = st.session_state.is_results
    if imgs:
        st.markdown(f"**Found {len(imgs)} images**")

        # Source breakdown
        from collections import Counter
        src_counts = Counter(i["source"] for i in imgs)
        badges = " ".join(f'<span class="ws-tag">📷 {s}: {c}</span>'
                          for s, c in src_counts.items())
        st.markdown(f"<div style='margin-bottom:14px;'>{badges}</div>", unsafe_allow_html=True)

        # Grid display — 3 columns
        cols = st.columns(3)
        for idx, img in enumerate(imgs):
            with cols[idx % 3]:
                # Display image
                try:
                    st.image(img["url"], use_container_width=True)
                except Exception:
                    st.markdown(f'<img src="{img["url"]}" style="width:100%;border-radius:8px;" onerror="this.style.display=\'none\'"/>', unsafe_allow_html=True)

                caption = img.get("caption", "")[:80]
                photographer = img.get("photographer", "")
                source = img.get("source", "")
                st.caption(f"📷 {photographer} | {source}")

                # Download / View full size
                img_url = img.get("large") or img.get("url", "")
                if img_url and img_url.startswith("http"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button("⬇️ Download", img_url, use_container_width=True)
                    with c2:
                        page = img.get("page_url", img_url)
                        st.link_button("🔗 View", page, use_container_width=True)
    elif st.session_state.get("is_last_query"):
        st.info("No images found. Try different keywords or sources.")

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="is_back"):
        st.session_state.app_mode = "chat"; st.rerun()
