"""
new_features.py — New Feature Renderers for ExamHelp v4.0
Includes: AI News Hub, VIT Map, India Trip Planner, Enhanced Tools UI
"""
import streamlit as st
import time
import json
import re

# ═══════════════════════════════════════════════════════════════
# AI NEWS HUB
# ═══════════════════════════════════════════════════════════════

def render_news_hub():
    """Render the AI News Hub with live news, fullscreen, and AI recommendations."""
    
    st.markdown("""
<style>
.news-header{background:linear-gradient(135deg,#0a0020 0%,#050010 100%);border:1px solid #3d1a6b;border-radius:16px;padding:28px 32px;margin-bottom:20px;position:relative;overflow:hidden;}
.news-header::before{content:'';position:absolute;top:-40px;right:-40px;width:200px;height:200px;background:radial-gradient(circle,rgba(167,139,250,0.12),transparent 70%);border-radius:50%;}
.news-title{font-size:2rem;font-weight:900;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0 0 4px;}
.news-sub{font-size:.9rem;color:#9090b8;}
.news-card{background:var(--bg2-glass);border:1px solid var(--bd-glass);border-radius:14px;padding:16px 18px;margin:8px 0;transition:all 0.25s ease;cursor:pointer;backdrop-filter:blur(12px);}
.news-card:hover{border-color:var(--accent-bd);transform:translateX(4px);box-shadow:0 4px 24px var(--accent-glow);}
.news-source{font-size:.72rem;color:var(--accent);font-weight:600;text-transform:uppercase;letter-spacing:.05em;}
.news-title-text{font-size:.95rem;font-weight:600;color:var(--text);line-height:1.4;margin:4px 0;}
.news-desc{font-size:.8rem;color:var(--text2);line-height:1.5;}
.news-meta{font-size:.7rem;color:var(--text3);margin-top:8px;}
.live-dot{display:inline-block;width:8px;height:8px;background:#4ade80;border-radius:50%;animation:pulse-dot 2s ease-in-out infinite;margin-right:6px;}
@keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.5;transform:scale(.8);}}
.ai-rec-box{background:linear-gradient(135deg,rgba(124,106,247,0.08),rgba(167,139,250,0.04));border:1px solid rgba(124,106,247,0.25);border-radius:12px;padding:16px;margin:12px 0;}
.trend-chip{display:inline-flex;align-items:center;gap:5px;background:var(--bg3-glass);border:1px solid var(--bd-glass);border-radius:99px;padding:4px 12px;font-size:.75rem;color:var(--accent);margin:3px;cursor:pointer;transition:all .2s;}
.trend-chip:hover{background:var(--accent-bg);border-color:var(--accent-bd);}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="news-header">
  <div class="news-title">📡 AI News Hub</div>
  <div class="news-sub"><span class="live-dot"></span>Live AI news · Best AI tool finder · Trend analysis · Auto-updated</div>
</div>
""", unsafe_allow_html=True)

    # Fullscreen toggle
    col_fs, col_refresh, col_filter = st.columns([1,1,4])
    with col_fs:
        if st.button("⛶ Fullscreen", use_container_width=True, key="news_fs"):
            st.session_state["news_fullscreen"] = not st.session_state.get("news_fullscreen", False)
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True, key="news_refresh"):
            if "cached_news" in st.session_state:
                del st.session_state["cached_news"]
            st.rerun()

    if st.session_state.get("news_fullscreen"):
        st.markdown("""<style>.main .block-container{max-width:100% !important;padding-left:0.5rem !important;padding-right:0.5rem !important;}</style>""", unsafe_allow_html=True)

    # Tabs
    tab_news, tab_tools, tab_trends, tab_search = st.tabs([
        "📰 Latest AI News", "🏆 Best AI for Task", "📊 AI Trends", "🔍 Search News"
    ])

    with tab_news:
        from news_engine import fetch_all_ai_news, TOPIC_CATEGORIES
        
        # Category filter
        selected_cat = st.selectbox(
            "Category",
            list(TOPIC_CATEGORIES.keys()),
            label_visibility="collapsed",
            key="news_cat"
        )
        query = TOPIC_CATEGORIES.get(selected_cat, "artificial intelligence")
        
        # Fetch with caching
        cache_key = f"cached_news_{selected_cat}"
        if cache_key not in st.session_state or st.session_state.get(f"{cache_key}_time", 0) < time.time() - 600:
            with st.spinner("🔄 Fetching latest AI news..."):
                articles = fetch_all_ai_news(query, max_per_source=5)
                st.session_state[cache_key] = articles
                st.session_state[f"{cache_key}_time"] = time.time()
        else:
            articles = st.session_state[cache_key]
        
        if articles:
            st.markdown(f'<div style="color:var(--text3);font-size:.8rem;margin-bottom:12px;">📰 {len(articles)} articles found</div>', unsafe_allow_html=True)
            
            # Layout: 2 columns for fullscreen, 1 for normal
            use_cols = st.session_state.get("news_fullscreen", False)
            
            if use_cols:
                cols = st.columns(2)
                for i, article in enumerate(articles[:30]):
                    with cols[i % 2]:
                        _render_article_card(article, i)
            else:
                for i, article in enumerate(articles[:20]):
                    _render_article_card(article, i)
        else:
            st.warning("⚠️ Could not fetch news. Check internet connection or try refreshing.")
            st.markdown("""
**📌 Latest AI News (Curated)**

Stay updated with these top sources:
- [TechCrunch AI](https://techcrunch.com/category/artificial-intelligence/)
- [VentureBeat AI](https://venturebeat.com/category/ai/)
- [The Verge AI](https://www.theverge.com/ai-artificial-intelligence)
- [MIT Technology Review](https://www.technologyreview.com/)
- [arXiv CS.AI](https://arxiv.org/list/cs.AI/recent)
""")

    with tab_tools:
        st.markdown("### 🏆 Find the Best AI for Any Task")
        st.markdown("Tell me what you want to do, and I'll recommend the best AI tool available right now.")
        
        use_case = st.text_input(
            "What do you want to do?",
            placeholder="e.g., write code, generate images, summarize documents, make videos, voice clone...",
            key="ai_use_case"
        )
        
        # Quick suggestions
        st.markdown("**Quick picks:**")
        quick_cases = [
            "Writing code & debugging", "Generating realistic images", "Creating videos from text",
            "Voice cloning & TTS", "Data analysis & charts", "Writing & editing text",
            "Research & summarization", "Making presentations", "SEO & marketing",
            "Customer service chatbots", "Medical diagnosis support", "Legal document review"
        ]
        cols = st.columns(3)
        for i, case in enumerate(quick_cases):
            with cols[i % 3]:
                if st.button(case, key=f"quick_{i}", use_container_width=True):
                    st.session_state["ai_use_case_val"] = case
                    st.session_state["show_ai_rec"] = True
        
        if use_case or st.session_state.get("ai_use_case_val"):
            task = use_case or st.session_state.get("ai_use_case_val", "")
            if st.button("🔍 Find Best AI Tool", type="primary", use_container_width=True, key="find_ai"):
                with st.spinner(f"Finding the best AI for '{task}'..."):
                    from news_engine import get_ai_tool_recommendations
                    rec = get_ai_tool_recommendations(task)
                    st.session_state["ai_rec_result"] = rec
            
            if "ai_rec_result" in st.session_state:
                st.markdown('<div class="ai-rec-box">', unsafe_allow_html=True)
                st.markdown(st.session_state["ai_rec_result"])
                st.markdown('</div>', unsafe_allow_html=True)

    with tab_trends:
        st.markdown("### 📊 AI Landscape & Trends")
        
        if st.button("🔄 Analyze Current AI Trends", type="primary", use_container_width=True, key="get_trends"):
            with st.spinner("Analyzing the AI landscape..."):
                from news_engine import get_ai_trend_analysis
                trends = get_ai_trend_analysis()
                st.session_state["ai_trends"] = trends
        
        if "ai_trends" in st.session_state:
            st.markdown(st.session_state["ai_trends"])
        else:
            st.info("Click 'Analyze Current AI Trends' to get a comprehensive overview of the current AI landscape, model rankings, and emerging technologies.")

    with tab_search:
        st.markdown("### 🔍 Search Specific AI News")
        custom_query = st.text_input("Search topic", placeholder="e.g., GPT-5, Sora video, OpenAI, robotics...", key="news_search_q")
        if custom_query and st.button("Search News", type="primary", key="do_news_search"):
            with st.spinner(f"Searching for '{custom_query}'..."):
                from news_engine import fetch_all_ai_news
                results = fetch_all_ai_news(custom_query, max_per_source=8)
                st.session_state["search_news_results"] = results
        
        if "search_news_results" in st.session_state:
            for i, article in enumerate(st.session_state["search_news_results"][:15]):
                _render_article_card(article, f"s_{i}")

    if st.button("💬 Back to Chat", use_container_width=True, key="news_back"):
        st.session_state.app_mode = "chat"
        st.session_state["news_fullscreen"] = False
        st.rerun()


def _render_article_card(article: dict, idx):
    """Render a news article card."""
    title = article.get("title","")
    desc = article.get("description","")[:200]
    url = article.get("url","")
    source = article.get("source","")
    published = article.get("published","")
    
    if not title:
        return
    
    # Format date
    date_str = ""
    if published:
        try:
            from datetime import datetime
            if "T" in published:
                dt = datetime.fromisoformat(published.replace("Z","+00:00"))
                date_str = dt.strftime("%b %d, %Y")
            else:
                date_str = published[:16]
        except Exception:
            date_str = published[:16]
    
    with st.expander(f"**{title[:90]}{'...' if len(title) > 90 else ''}**", expanded=False):
        if source: st.markdown(f'<span class="news-source">📰 {source}</span>', unsafe_allow_html=True)
        if date_str: st.markdown(f'<span class="news-meta">🕐 {date_str}</span>', unsafe_allow_html=True)
        if desc: st.markdown(f'<p class="news-desc">{desc}...</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if url: st.markdown(f'<a href="{url}" target="_blank" style="color:var(--accent);font-size:.8rem;">🔗 Read Full Article →</a>', unsafe_allow_html=True)
        with col2:
            if st.button("🤖 AI Summary", key=f"sum_{idx}", use_container_width=True):
                with st.spinner("Summarizing..."):
                    from news_engine import summarize_article_with_ai
                    summary = summarize_article_with_ai(article)
                    st.info(summary)


# ═══════════════════════════════════════════════════════════════
# VIT CHENNAI MAP
# ═══════════════════════════════════════════════════════════════

def render_vit_map():
    """Render VIT Chennai campus interactive map with Leaflet markers."""
    import streamlit.components.v1 as components
    from map_engine import (
        VIT_CHENNAI_LOCATIONS, VIT_CENTER_LAT, VIT_CENTER_LNG,
        GOOGLE_MAPS_EMBED_KEY, get_vit_map_html, get_directions_url,
        haversine_km, get_walk_time, NEARBY_FROM_VIT,
    )

    st.markdown("""
<style>
.map-header{background:linear-gradient(135deg,#001a10 0%,#000d08 100%);border:1px solid #1a5a30;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.map-title{font-size:2rem;font-weight:900;color:#34d399;margin:0 0 4px;}
.map-sub{font-size:.9rem;color:#9090b8;}
.loc-card{background:rgba(14,14,26,0.8);border:1px solid rgba(52,211,153,0.15);border-radius:12px;padding:12px;margin:4px 0;transition:border-color .2s;}
.loc-card:hover{border-color:rgba(52,211,153,0.4);}
.loc-highlight{border-color:#34d399 !important;background:rgba(52,211,153,0.08) !important;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="map-header">
  <div class="map-title">🗺️ VIT Chennai Campus</div>
  <div class="map-sub">Interactive campus map · Colored markers per category · Find facilities · Distance calculator</div>
</div>
""", unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_map, tab_locations, tab_distance, tab_directions, tab_nearby = st.tabs([
        "🗺️ Live Map", "📋 All Locations", "📏 Distance", "🧭 Directions", "🏕️ Weekend Trips"
    ])

    # ── TAB 1: LIVE MAP ───────────────────────────────────────────────────────
    with tab_map:
        all_cats = list(VIT_CHENNAI_LOCATIONS.keys())
        selected_cats = st.multiselect(
            "Show categories on map",
            all_cats,
            default=all_cats,
            key="vit_map_cats"
        )

        # Search box — now actually does something
        search_loc = st.text_input(
            "🔍 Search location",
            placeholder="e.g. Library, MH1, canteen...",
            key="vit_search"
        )

        # Render Leaflet map with selected categories
        map_html = get_vit_map_html(selected_categories=selected_cats)
        components.html(map_html, height=560, scrolling=False)

        # Search results — shown below the map
        if search_loc.strip():
            q = search_loc.strip().lower()
            found = []
            for cat, locs in VIT_CHENNAI_LOCATIONS.items():
                for loc in locs:
                    if q in loc["name"].lower() or q in loc["desc"].lower():
                        found.append((cat, loc))

            if found:
                st.success(f"Found {len(found)} location(s) matching **{search_loc}**")
                for cat, loc in found:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={loc['lat']},{loc['lng']}"
                    st.markdown(f"""
<div class="loc-card loc-highlight">
  <div style="font-weight:600;font-size:.9rem;color:#34d399">{loc['name']}</div>
  <div style="font-size:.78rem;color:#9090b8;margin:3px 0">{cat} · {loc['desc']}</div>
  <a href="{maps_url}" target="_blank" style="font-size:.75rem;color:#7c6af7">📍 Open in Google Maps →</a>
</div>
""", unsafe_allow_html=True)
            else:
                st.warning(f"No location found matching '{search_loc}'. Try: Library, MH1, Canteen, Sports...")

        # Colour legend
        color_legend = {
            "🟣 Academic": "#7c6af7", "🟢 Hostels": "#34d399", "🟡 Food": "#f59e0b",
            "🔵 Library": "#60a5fa",  "🔴 Sports": "#f87171", "🟤 Services": "#c084fc",
            "🟨 Transport": "#fbbf24"
        }
        st.markdown(
            " &nbsp; ".join(
                f'<span style="background:{c};color:#000;border-radius:4px;padding:2px 8px;font-size:.72rem;font-weight:600">{k}</span>'
                for k, c in color_legend.items()
            ),
            unsafe_allow_html=True
        )

    # ── TAB 2: ALL LOCATIONS ──────────────────────────────────────────────────
    with tab_locations:
        for cat in list(VIT_CHENNAI_LOCATIONS.keys()):
            locations = VIT_CHENNAI_LOCATIONS[cat]
            st.markdown(f"### {cat}")
            cols = st.columns(3)
            for i, loc in enumerate(locations):
                with cols[i % 3]:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={loc['lat']},{loc['lng']}"
                    st.markdown(f"""
<div class="loc-card">
  <div style="font-weight:600;font-size:.88rem;color:#f0f0ff">{loc['name']}</div>
  <div style="font-size:.75rem;color:#9090b8;margin:4px 0">{loc['desc']}</div>
  <a href="{maps_url}" target="_blank" style="font-size:.72rem;color:#7c6af7">📍 Open in Maps →</a>
</div>
""", unsafe_allow_html=True)

    # ── TAB 3: DISTANCE CALCULATOR ────────────────────────────────────────────
    with tab_distance:
        st.markdown("### 📏 Distance Between Campus Locations")
        st.caption("Straight-line distance + estimated walking time between any two points on campus.")

        # Build flat list of all locations for selectors
        all_locs_flat = [
            (loc["name"], loc["lat"], loc["lng"])
            for locs in VIT_CHENNAI_LOCATIONS.values()
            for loc in locs
        ]
        loc_names = [l[0] for l in all_locs_flat]
        loc_coord_map = {l[0]: (l[1], l[2]) for l in all_locs_flat}

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            loc_a = st.selectbox("From location", loc_names, index=0, key="dist_from")
        with d_col2:
            loc_b = st.selectbox("To location", loc_names, index=4, key="dist_to")

        if loc_a and loc_b and loc_a != loc_b:
            la, loa = loc_coord_map[loc_a]
            lb, lob = loc_coord_map[loc_b]
            km = haversine_km(la, loa, lb, lob)
            walk = get_walk_time(km)
            meters = int(km * 1000)

            c1, c2, c3 = st.columns(3)
            c1.metric("Straight-line distance", f"{meters} m")
            c2.metric("Walking time", walk)
            c3.metric("By campus shuttle", "~5–10 min")

            gm_url = f"https://www.google.com/maps/dir/{la},{loa}/{lb},{lob}"
            st.markdown(
                f'<a href="{gm_url}" target="_blank" style="color:#34d399;font-size:.85rem;">'
                f'🗺️ View walking route on Google Maps →</a>',
                unsafe_allow_html=True
            )
        elif loc_a == loc_b:
            st.info("Select two different locations to calculate distance.")

        # Quick reference table for common routes
        st.markdown("---")
        st.markdown("#### Common Routes")
        common_routes = [
            ("Main Gate", "Technology Tower (TT)"),
            ("MH1 - Men's Hostel 1", "Central Library"),
            ("Main Cafeteria", "Technology Tower (TT)"),
            ("LH1 - Ladies Hostel 1", "Anna Auditorium"),
            ("Bus Stand", "Central Library"),
        ]
        for a, b in common_routes:
            if a in loc_coord_map and b in loc_coord_map:
                la, loa = loc_coord_map[a]
                lb, lob = loc_coord_map[b]
                km = haversine_km(la, loa, lb, lob)
                wt = get_walk_time(km)
                st.markdown(
                    f"**{a}** → **{b}** &nbsp; `{int(km*1000)} m` &nbsp; {wt}"
                )

    # ── TAB 4: DIRECTIONS ─────────────────────────────────────────────────────
    with tab_directions:
        st.markdown("### 🧭 Get Directions to VIT Campus")
        st.caption("Enter where you are coming from — the app builds a direct Google Maps directions link.")

        from_loc = st.text_input(
            "Your starting location",
            placeholder="e.g. Chennai Central Station, Tambaram, T. Nagar...",
            key="vit_from"
        )

        to_options = ["VIT Chennai Main Gate"] + [
            loc["name"]
            for locs in VIT_CHENNAI_LOCATIONS.values()
            for loc in locs
        ]
        to_loc = st.selectbox("Destination on campus", to_options, key="vit_to")

        if from_loc.strip() and st.button("🗺️ Get Directions", type="primary", use_container_width=True, key="vit_dir"):
            # Resolve destination coordinates
            dest_lat, dest_lng = VIT_CENTER_LAT, VIT_CENTER_LNG
            for locs in VIT_CHENNAI_LOCATIONS.values():
                for loc in locs:
                    if loc["name"] == to_loc:
                        dest_lat, dest_lng = loc["lat"], loc["lng"]
                        break

            dir_url = get_directions_url(from_loc.strip(), dest_lat, dest_lng)
            st.success(f"Directions from **{from_loc}** → **{to_loc}** ready!")
            st.markdown(
                f'<a href="{dir_url}" target="_blank">'
                f'<button style="background:linear-gradient(135deg,#34d399,#059669);color:white;'
                f'border:none;padding:12px 28px;border-radius:10px;cursor:pointer;font-size:.95rem;font-weight:600;">'
                f'🗺️ Open Directions in Google Maps →</button></a>',
                unsafe_allow_html=True
            )
            st.caption("Tip: Google Maps will auto-detect your live location if you allow it.")

        st.markdown("---")
        st.markdown("#### 🚌 Common Ways to Reach VIT Chennai")
        routes_info = [
            ("🚆 From Chennai Central", "Train to Vandalur / Guduvanchery → Auto to VIT (~₹80-120)", "~1.5 hr"),
            ("🚌 From Tambaram",        "Bus 19C or 19D toward Kelambakkam → alight at VIT stop (~₹15)", "~45 min"),
            ("🚕 From Chennai Airport", "Cab via OMR (~₹400-600) or Suburban train + auto", "~45 min"),
            ("🚌 From T. Nagar",        "Bus 19B toward Kelambakkam — direct to VIT gate (~₹20)", "~1.5 hr"),
            ("🚗 Self-drive",           "ECR → Kelambakkam junction → Vandalur-Kelambakkam Road", "~45 min from city"),
        ]
        for icon_route, detail, time_est in routes_info:
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1: st.markdown(f"**{icon_route}**")
            with col2: st.markdown(detail)
            with col3: st.markdown(f"`{time_est}`")

    # ── TAB 5: WEEKEND TRIPS ──────────────────────────────────────────────────
    with tab_nearby:
        st.markdown("### 🏕️ Weekend Trips from VIT Chennai")
        st.caption("Student-friendly destinations reachable by public transport. No car needed.")

        for dest in NEARBY_FROM_VIT:
            with st.expander(f"📍 {dest['name']} — {dest['km']} km away"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{dest['desc']}**")
                    st.markdown(f"🚌 **How to get there:** {dest['transport']}")
                with c2:
                    gm_dir = f"https://www.google.com/maps/dir/{VIT_CENTER_LAT},{VIT_CENTER_LNG}/{dest['lat']},{dest['lng']}"
                    gm_view = f"https://www.google.com/maps/search/?api=1&query={dest['lat']},{dest['lng']}"
                    st.markdown(f"[🗺️ Directions]({gm_dir})")
                    st.markdown(f"[📍 View on Map]({gm_view})")

    if st.button("💬 Back to Chat", use_container_width=True, key="vit_back"):
        st.session_state.app_mode = "chat"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# INDIA TRIP PLANNER
# ═══════════════════════════════════════════════════════════════

def render_trip_planner():
    """Render India Trip Planner with maps and AI."""
    import streamlit.components.v1 as components
    
    st.markdown("""
<style>
.trip-header{background:linear-gradient(135deg,#1a0a00 0%,#100500 100%);border:1px solid #5a3000;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.trip-title{font-size:2rem;font-weight:900;color:#f59e0b;margin:0 0 4px;}
.trip-sub{font-size:.9rem;color:#9090b8;}
.dest-card{background:var(--bg3-glass);border:1px solid var(--bd-glass);border-radius:12px;padding:12px;margin:4px;transition:all .2s;cursor:pointer;}
.dest-card:hover{border-color:rgba(245,158,11,.4);transform:translateY(-2px);}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="trip-header">
  <div class="trip-title">✈️ India Trip Planner</div>
  <div class="trip-sub">AI-powered travel plans · Interactive maps · Real-time info · All of India</div>
</div>
""", unsafe_allow_html=True)

    from map_engine import INDIA_DESTINATIONS, GOOGLE_MAPS_EMBED_KEY, get_india_trip_plan, answer_travel_question

    tab_plan, tab_explore, tab_ask, tab_map = st.tabs([
        "📅 Plan My Trip", "🗺️ Explore India", "❓ Ask About Travel", "📍 Interactive Map"
    ])

    with tab_plan:
        st.markdown("### 📅 Generate AI Trip Plan")
        pc1, pc2 = st.columns(2)
        with pc1:
            origin = st.text_input("Starting From", placeholder="e.g., Chennai, Mumbai, Delhi", key="trip_origin")
            days = st.slider("Duration (Days)", 1, 30, 5, key="trip_days")
            budget = st.selectbox("Budget", ["Budget (₹1,000-3,000/day)", "Mid-range (₹3,000-8,000/day)", "Comfort (₹8,000-20,000/day)", "Luxury (₹20,000+/day)"], key="trip_budget")
        with pc2:
            # Destination picker
            dest_cat = st.selectbox("Destination Type", list(INDIA_DESTINATIONS.keys()), key="trip_dest_cat")
            dest_places = INDIA_DESTINATIONS.get(dest_cat, [])
            destination = st.selectbox("Destination", [p["name"] + f", {p['state']}" for p in dest_places] + ["Other (type below)"], key="trip_dest")
            if destination == "Other (type below)":
                destination = st.text_input("Enter destination", key="trip_dest_custom")
        
        interests = st.multiselect(
            "Interests",
            ["🏛️ History & Heritage", "🌿 Nature & Wildlife", "🏖️ Beaches", "🍽️ Food & Cuisine",
             "🧘 Yoga & Wellness", "🎨 Art & Culture", "🏔️ Adventure & Trekking", "💒 Spiritual & Temples",
             "📸 Photography", "🛍️ Shopping", "🎭 Festivals & Events", "🦁 Wildlife Safari"],
            key="trip_interests"
        )
        
        plan_key = f"trip_plan__{origin}__{destination}__{days}"

        btn_col, clr_col = st.columns([4, 1])
        with btn_col:
            gen_btn = st.button(
                "🚀 Generate Trip Plan", type="primary", use_container_width=True,
                key="gen_trip", disabled=not (origin and destination)
            )
        with clr_col:
            if st.button("🗑️ Clear", use_container_width=True, key="clear_trip"):
                for k in list(st.session_state.keys()):
                    if k.startswith("trip_plan__"):
                        del st.session_state[k]
                st.rerun()

        if gen_btn:
            with st.spinner(f"Creating your {days}-day trip plan to {destination}..."):
                plan = get_india_trip_plan(
                    origin=origin, destination=destination,
                    days=days, budget=budget,
                    interests=[i.split(" ", 1)[1] if " " in i else i for i in interests]
                )
                st.session_state[plan_key] = plan

        if plan_key in st.session_state:
            st.markdown(st.session_state[plan_key])
            st.download_button(
                "📥 Download Trip Plan",
                st.session_state[plan_key],
                file_name=f"trip_{destination.split(',')[0].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
                key="trip_dl"
            )

    with tab_explore:
        st.markdown("### 🗺️ Explore India's Destinations")

        # Use selectbox + radio instead of buttons — stable across reruns
        exp_cat = st.selectbox(
            "Destination category",
            list(INDIA_DESTINATIONS.keys()),
            key="explore_cat"
        )
        places_in_cat = INDIA_DESTINATIONS[exp_cat]
        place_labels = [f"{p['name']} — {p['state']}" for p in places_in_cat]

        chosen_label = st.radio(
            "Pick a destination",
            place_labels,
            key="explore_place",
            horizontal=True
        )

        chosen = next(
            (p for p in places_in_cat
             if f"{p['name']} — {p['state']}" == chosen_label),
            None
        )

        if chosen:
            st.markdown(f"**{chosen['name']}, {chosen['state']}**")
            st.caption(chosen["desc"])

            embed_url = (
                f"https://www.google.com/maps/embed/v1/view"
                f"?key={GOOGLE_MAPS_EMBED_KEY}"
                f"&center={chosen['lat']},{chosen['lng']}"
                f"&zoom=12&maptype=roadmap"
            )
            components.html(f"""
<div style="border-radius:12px;overflow:hidden;border:1px solid rgba(245,158,11,0.3);">
<iframe width="100%" height="380" frameborder="0" style="border:0;display:block;"
  src="{embed_url}" allowfullscreen></iframe>
</div>""", height=400)

            gm_url = f"https://www.google.com/maps/search/?api=1&query={chosen['lat']},{chosen['lng']}"
            st.markdown(
                f'[🗺️ Open in Google Maps →]({gm_url})',
                unsafe_allow_html=False
            )

    with tab_ask:
        st.markdown("### ❓ Ask Your Travel Expert")
        st.markdown("Ask anything about traveling in India — itineraries, costs, safety, best time to visit, transport, food, culture...")
        
        # Chat interface for travel Q&A
        if "travel_chat" not in st.session_state:
            st.session_state.travel_chat = []
        
        for msg in st.session_state.travel_chat:
            icon = "🧑" if msg["role"] == "user" else "✈️"
            bg = "rgba(124,106,247,0.08)" if msg["role"] == "user" else "rgba(245,158,11,0.06)"
            st.markdown(f'<div style="background:{bg};border-radius:10px;padding:10px 14px;margin:6px 0;font-size:.9rem;">{icon} {msg["content"]}</div>', unsafe_allow_html=True)
        
        travel_q = st.text_input("Your question", placeholder="e.g., Is it safe to travel to Rajasthan solo? Best time for Kerala backwaters?", key="travel_q")
        if st.button("Ask Travel Expert", type="primary", use_container_width=True, key="ask_travel"):
            if travel_q.strip():
                st.session_state.travel_chat.append({"role": "user", "content": travel_q})
                with st.spinner("Travel expert thinking..."):
                    ctx = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.travel_chat[-6:]])
                    answer = answer_travel_question(travel_q, ctx)
                    st.session_state.travel_chat.append({"role": "assistant", "content": answer})
                st.rerun()
        
        if st.button("🗑️ Clear Chat", key="clear_travel_chat"):
            st.session_state.travel_chat = []
            st.rerun()

    with tab_map:
        st.markdown("### 📍 India Interactive Map")
        
        map_region = st.selectbox(
            "Focus Region",
            ["Full India", "South India", "North India", "West India", "East India", "Northeast India", "Central India"],
            key="india_map_region"
        )
        
        region_coords = {
            "Full India": (20.5937, 78.9629, 5),
            "South India": (12.0, 78.0, 6),
            "North India": (28.7041, 77.1025, 6),
            "West India": (22.2587, 71.1924, 6),
            "East India": (22.9868, 87.8550, 6),
            "Northeast India": (26.2006, 92.9376, 6),
            "Central India": (23.4732, 78.2098, 6),
        }
        
        lat, lng, zoom = region_coords.get(map_region, (20.5937, 78.9629, 5))
        embed_url = f"https://www.google.com/maps/embed/v1/view?key={GOOGLE_MAPS_EMBED_KEY}&center={lat},{lng}&zoom={zoom}&maptype=roadmap"
        
        components.html(f"""
<div style="border-radius:16px;overflow:hidden;border:1px solid rgba(245,158,11,0.3);box-shadow:0 8px 32px rgba(0,0,0,0.4);">
<iframe width="100%" height="600" frameborder="0" style="border:0;display:block;" src="{embed_url}" allowfullscreen></iframe>
</div>""", height=620)

    if st.button("💬 Back to Chat", use_container_width=True, key="trip_back"):
        st.session_state.app_mode = "chat"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# ENHANCED CONVERTER UI
# ═══════════════════════════════════════════════════════════════

def render_universal_converter():
    """Render the massively upgraded universal converter."""
    from converter_engine import get_supported_formats, convert_file, UNIT_CATEGORIES, convert_units, get_live_currency_rates
    
    st.markdown("""
<style>
.conv-header{background:linear-gradient(135deg,#0a1020 0%,#050810 100%);border:1px solid #2a3a6b;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.conv-title{font-size:2rem;font-weight:900;color:#60a5fa;margin:0 0 4px;}
.conv-sub{font-size:.9rem;color:#9090b8;}
.unit-result{background:linear-gradient(135deg,rgba(96,165,250,0.1),rgba(124,106,247,0.05));border:1px solid rgba(96,165,250,0.3);border-radius:12px;padding:16px;margin:12px 0;text-align:center;}
.unit-result-val{font-size:2rem;font-weight:900;color:#60a5fa;}
.unit-result-label{font-size:.85rem;color:#9090b8;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="conv-header">
  <div class="conv-title">🔄 Universal Converter</div>
  <div class="conv-sub">File conversion · Unit conversion · Currency · Number bases · 100+ conversion types</div>
</div>
""", unsafe_allow_html=True)

    tab_file, tab_units, tab_currency, tab_color = st.tabs([
        "📁 File Converter", "📏 Unit Converter", "💰 Live Currency", "🎨 Color Converter"
    ])

    with tab_file:
        supported = get_supported_formats()
        fmt_list = sorted(supported.keys())
        col1, col2 = st.columns(2)
        with col1:
            from_fmt = st.selectbox("From format", fmt_list, key="conv_from")
        with col2:
            to_fmts = supported.get(from_fmt, [])
            to_fmt = st.selectbox("To format", to_fmts, key="conv_to")
        
        # Show format info
        format_info = {
            "pdf": "📄 Portable Document Format", "docx": "📝 Microsoft Word",
            "txt": "📃 Plain Text", "csv": "📊 Comma Separated Values",
            "json": "🔧 JavaScript Object Notation", "xlsx": "📊 Excel Spreadsheet",
            "md": "📝 Markdown", "html": "🌐 HTML Web Page",
            "xml": "📋 Extensible Markup Language", "yaml": "⚙️ YAML Config",
            "pptx": "📊 PowerPoint", "png": "🖼️ PNG Image",
        }
        st.markdown(f'<div style="font-size:.8rem;color:var(--text3);margin-bottom:12px;">'
                    f'{format_info.get(from_fmt,"")}{" → " if from_fmt and to_fmt else ""}{format_info.get(to_fmt,"")}</div>',
                    unsafe_allow_html=True)
        
        uploaded = st.file_uploader(f"Upload {from_fmt.upper()} file", type=[from_fmt], key="conv_upload")
        
        if uploaded and st.button("⚡ Convert Now", type="primary", use_container_width=True, key="do_convert"):
            with st.spinner(f"Converting {from_fmt} → {to_fmt}..."):
                data = uploaded.read()
                result, mime, ext, err = convert_file(data, from_fmt, to_fmt, uploaded.name)
            
            if err:
                st.error(f"❌ {err}")
            else:
                st.success(f"✅ Conversion complete! {len(result):,} bytes")
                out_name = uploaded.name.rsplit(".", 1)[0] + "." + ext
                st.download_button(f"⬇️ Download {out_name}", result, file_name=out_name, mime=mime, use_container_width=True, key="conv_dl")
                
                # Preview for text formats
                if ext in ("txt","md","html","json","csv","xml","yaml") and len(result) < 50000:
                    with st.expander("👁️ Preview Output"):
                        preview = result.decode("utf-8", errors="replace")[:3000]
                        st.code(preview, language=ext if ext in ("json","html","xml","yaml") else "text")

    with tab_units:
        cat_names = list(UNIT_CATEGORIES.keys())
        selected_cat = st.selectbox("Category", cat_names, key="unit_cat")
        
        cat_data = UNIT_CATEGORIES.get(selected_cat, {})
        units = cat_data.get("units", [])
        
        if units:
            uc1, uc2, uc3 = st.columns([2,2,1])
            with uc1:
                from_unit = st.selectbox("From", units, key="unit_from")
            with uc2:
                # Default to a different unit than from
                default_to_idx = 1 if len(units) > 1 else 0
                to_unit = st.selectbox("To", units, index=default_to_idx, key="unit_to")
            with uc3:
                value = st.number_input("Value", value=1.0, format="%.6g", key="unit_val")
            
            if from_unit != to_unit or selected_cat == "🔢 Number Base":
                try:
                    result, result_str = convert_units(float(value), from_unit, to_unit, selected_cat)
                    st.markdown(f"""
<div class="unit-result">
  <div class="unit-result-val">{result:.10g}</div>
  <div class="unit-result-label">{result_str}</div>
</div>""", unsafe_allow_html=True)
                    
                    # Show multiple conversions at once
                    if len(units) > 2:
                        with st.expander("📊 Convert to all units"):
                            rows = []
                            for u in units:
                                if u != from_unit:
                                    try:
                                        r, r_str = convert_units(float(value), from_unit, u, selected_cat)
                                        rows.append(f"| **{u}** | `{r:.10g}` |")
                                    except Exception:
                                        pass
                            if rows:
                                st.markdown("| Unit | Value |\n|------|-------|\n" + "\n".join(rows))
                except Exception as e:
                    st.error(f"Conversion error: {e}")
        
        # Special: Number base converter
        if selected_cat == "🔢 Number Base":
            st.markdown("---")
            nb_val = st.text_input("Enter number", placeholder="e.g., 255 or FF or 11111111", key="nb_val")
            nb_from = st.selectbox("From base", units, index=2, key="nb_from")
            if nb_val:
                base_map = {"Binary (base 2)":2,"Octal (base 8)":8,"Decimal (base 10)":10,"Hexadecimal (base 16)":16}
                try:
                    n = int(nb_val.strip(), base_map[nb_from])
                    st.markdown(f"""
| Base | Value |
|------|-------|
| Binary | `{bin(n)[2:]}` |
| Octal | `{oct(n)[2:]}` |
| Decimal | `{n}` |
| Hexadecimal | `{hex(n)[2:].upper()}` |
""")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_currency:
        st.markdown("### 💰 Live Currency Converter")
        st.caption("Rates updated in real-time from open.er-api.com")
        
        currencies = ["USD","EUR","GBP","JPY","INR","CAD","AUD","CHF","CNY","HKD","SGD","KRW","MXN","BRL","RUB","TRY","ZAR","AED","SAR","THB","IDR","MYR","PHP","VND","NGN","EGP","PKR","BDT","LKR","NPR"]
        
        curr_col1, curr_col2, curr_col3 = st.columns([2,2,1])
        with curr_col1:
            from_curr = st.selectbox("From", currencies, key="curr_from")
        with curr_col2:
            to_curr = st.selectbox("To", currencies, index=4, key="curr_to")  # Default to INR
        with curr_col3:
            amount = st.number_input("Amount", value=1.0, min_value=0.0, key="curr_amount")
        
        if st.button("Get Live Rate", type="primary", use_container_width=True, key="get_rate"):
            with st.spinner("Fetching live rates..."):
                rates = get_live_currency_rates(from_curr)
                st.session_state["curr_rates"] = rates
                st.session_state["curr_base"] = from_curr
        
        if "curr_rates" in st.session_state and st.session_state.get("curr_base") == from_curr:
            rates = st.session_state["curr_rates"]
            if to_curr in rates:
                result = amount * rates[to_curr]
                st.markdown(f"""
<div class="unit-result">
  <div class="unit-result-val">{result:,.4f} {to_curr}</div>
  <div class="unit-result-label">{amount} {from_curr} = {result:,.4f} {to_curr} · Rate: 1 {from_curr} = {rates[to_curr]:.6f} {to_curr}</div>
</div>""", unsafe_allow_html=True)
                
                # Major currencies comparison
                major = ["USD","EUR","GBP","JPY","INR","CNY","AUD","CAD"]
                st.markdown("#### Quick Compare")
                comp_cols = st.columns(4)
                for i, curr in enumerate([c for c in major if c != from_curr and c in rates]):
                    with comp_cols[i % 4]:
                        val = amount * rates[curr]
                        st.metric(curr, f"{val:,.2f}")
            else:
                st.warning(f"Rate for {to_curr} not available. Try refreshing.")

    with tab_color:
        st.markdown("### 🎨 Color Format Converter")
        
        color_input = st.color_picker("Pick a color", "#7c6af7", key="color_pick")
        
        # Parse hex to RGB
        hex_val = color_input.lstrip("#")
        r, g, b = int(hex_val[0:2],16), int(hex_val[2:4],16), int(hex_val[4:6],16)
        
        # Convert to various formats
        h_normalized, s_normalized, l_normalized = 0, 0, 0
        try:
            import colorsys
            r_n, g_n, b_n = r/255, g/255, b/255
            h, l, s = colorsys.rgb_to_hls(r_n, g_n, b_n)
            h_normalized = round(h * 360)
            s_normalized = round(s * 100)
            l_normalized = round(l * 100)
        except Exception:
            pass
        
        cmyk_k = 1 - max(r/255, g/255, b/255)
        if cmyk_k < 1:
            cmyk_c = round((1 - r/255 - cmyk_k) / (1 - cmyk_k) * 100)
            cmyk_m = round((1 - g/255 - cmyk_k) / (1 - cmyk_k) * 100)
            cmyk_y = round((1 - b/255 - cmyk_k) / (1 - cmyk_k) * 100)
        else:
            cmyk_c, cmyk_m, cmyk_y = 0, 0, 0
        cmyk_k = round(cmyk_k * 100)
        
        st.markdown(f"""
| Format | Value |
|--------|-------|
| **HEX** | `{color_input.upper()}` |
| **RGB** | `rgb({r}, {g}, {b})` |
| **RGBA** | `rgba({r}, {g}, {b}, 1)` |
| **HSL** | `hsl({h_normalized}, {s_normalized}%, {l_normalized}%)` |
| **CMYK** | `cmyk({cmyk_c}%, {cmyk_m}%, {cmyk_y}%, {cmyk_k}%)` |
| **Binary R** | `{r:08b}` |
| **Binary G** | `{g:08b}` |
| **Binary B** | `{b:08b}` |
""")
        
        st.markdown(f'<div style="width:100%;height:80px;background:{color_input};border-radius:12px;border:1px solid var(--border);"></div>', unsafe_allow_html=True)

    if st.button("💬 Back to Chat", use_container_width=True, key="conv_back"):
        st.session_state.app_mode = "chat"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# ENHANCED AI HUMANISER UI
# ═══════════════════════════════════════════════════════════════

def render_ai_humaniser():
    """Render the next-level AI Text Humaniser."""
    from humaniser_engine import humanise_text, ai_detection_score, compare_versions, ADVANCED_TONES
    
    st.markdown("""
<style>
.hum-header{background:linear-gradient(135deg,#100a20 0%,#080510 100%);border:1px solid #4a2a8b;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.hum-title{font-size:2rem;font-weight:900;background:linear-gradient(135deg,#c084fc,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0 0 4px;}
.hum-sub{font-size:.9rem;color:#9090b8;}
.score-box{background:rgba(192,132,252,0.08);border:1px solid rgba(192,132,252,0.25);border-radius:12px;padding:16px;text-align:center;}
.score-val{font-size:2.5rem;font-weight:900;}
.compare-row{display:flex;gap:12px;margin:12px 0;}
.compare-box{flex:1;background:var(--bg3-glass);border:1px solid var(--bd-glass);border-radius:10px;padding:12px;text-align:center;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="hum-header">
  <div class="hum-title">✨ AI Text Humaniser</div>
  <div class="hum-sub">Next-level AI detection bypass · Passes GPTZero, Turnitin, Winston AI · 10+ tones · Before/after comparison</div>
</div>
""", unsafe_allow_html=True)

    tab_humanise, tab_detect, tab_batch = st.tabs(["✨ Humanise Text", "🔍 AI Detection Score", "📦 Batch Humanise"])

    with tab_humanise:
        text_in = st.text_area("Paste AI-generated text here", height=200, placeholder="Paste ChatGPT, Claude, Gemini or any AI text here...", key="hum_input")
        
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            tone = st.selectbox("Target Tone", list(ADVANCED_TONES.keys()), key="hum_tone")
        with hc2:
            strength = st.selectbox("Strength", ["Light Touch","Standard","Maximum","Academic Safe"], index=1, key="hum_strength")
        with hc3:
            preserve = st.checkbox("Preserve structure", value=True, key="hum_preserve")
        
        target_audience = st.text_input("Target audience (optional)", placeholder="e.g., University students, Business executives, Teenagers", key="hum_audience")
        extra_inst = st.text_input("Extra instructions (optional)", placeholder="e.g., Add British spellings, Include personal anecdotes", key="hum_extra")
        
        if text_in.strip():
            # Quick pre-score
            quick_score = ai_detection_score(text_in)
            score = quick_score["score"]
            color = "#f87171" if score >= 75 else "#fbbf24" if score >= 50 else "#34d399"
            st.markdown(f'<div style="font-size:.8rem;color:{color};padding:6px;border-radius:6px;background:rgba(0,0,0,.2);">⚡ Pre-humanise AI score: <b>{score}/100</b> — {quick_score["label"]}</div>', unsafe_allow_html=True)
        
        hb1, hb2 = st.columns([3,1])
        with hb1:
            humanise_btn = st.button("✨ Humanise Now", type="primary", use_container_width=True, disabled=not text_in.strip(), key="do_humanise")
        with hb2:
            if st.button("📊 Score Only", use_container_width=True, disabled=not text_in.strip(), key="score_only"):
                st.session_state["det_text"] = text_in
                st.session_state["run_detection"] = True
        
        if humanise_btn and text_in.strip():
            with st.spinner("✨ Humanising your text... (this may take 15-30 seconds for long texts)"):
                result = humanise_text(
                    text_in, tone=tone, preserve_structure=preserve,
                    strength=strength, extra_instructions=extra_inst,
                    target_audience=target_audience
                )
                st.session_state["hum_result"] = result
                st.session_state["hum_original"] = text_in
        
        if "hum_result" in st.session_state:
            st.markdown("---")
            st.markdown("### ✅ Humanised Output")
            
            # Comparison stats
            if "hum_original" in st.session_state:
                comp = compare_versions(st.session_state["hum_original"], st.session_state["hum_result"])
                cols = st.columns(4)
                metrics = [
                    ("Original AI Score", f"{comp['original_score']}/100", comp["original_label"]),
                    ("After Score", f"{comp['humanised_score']}/100", comp["humanised_label"]),
                    ("Improvement", f"-{comp['score_reduction']} pts", "✅ Better" if comp['score_reduction'] > 0 else "Same"),
                    ("Vocab Richness", f"{comp['humanised_vocab_richness']}%", f"Was {comp['original_vocab_richness']}%"),
                ]
                for i, (label, val, delta) in enumerate(metrics):
                    with cols[i]:
                        st.metric(label, val, delta)
            
            result_text = st.text_area("Result", value=st.session_state["hum_result"], height=280, key="hum_result_area")
            
            dc1, dc2 = st.columns(2)
            with dc1:
                st.download_button("⬇️ Download TXT", result_text.encode(), file_name="humanised.txt", mime="text/plain", use_container_width=True, key="hum_dl_txt")
            with dc2:
                st.download_button("⬇️ Download DOCX", _text_to_docx_bytes(result_text), file_name="humanised.docx", use_container_width=True, key="hum_dl_docx")
            
            if st.button("🔄 Humanise Again (Different Style)", use_container_width=True, key="hum_again"):
                del st.session_state["hum_result"]
                st.rerun()

    with tab_detect:
        det_text = st.text_area("Text to analyze", height=200, placeholder="Paste any text to check its AI detection score...", key="det_input",
                                value=st.session_state.get("det_text",""))
        
        if st.button("🔍 Analyze AI Detection Risk", type="primary", use_container_width=True, disabled=not det_text.strip(), key="run_det") or st.session_state.get("run_detection"):
            st.session_state["run_detection"] = False
            if det_text.strip():
                score_data = ai_detection_score(det_text)
                score = score_data["score"]
                color = "#f87171" if score >= 75 else "#fbbf24" if score >= 50 else "#4ade80"
                
                st.markdown(f'<div class="score-box"><div class="score-val" style="color:{color};">{score}/100</div><div style="color:var(--text2);margin-top:6px;">{score_data["label"]}</div></div>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("Words", score_data["word_count"])
                with col2: st.metric("Passive Voice", score_data["passive_instances"])
                with col3: st.metric("Contractions", score_data["contraction_count"])
                
                if score_data["flags"]:
                    st.markdown("#### ⚠️ Issues Found")
                    for flag in score_data["flags"]:
                        st.markdown(f"- {flag}")
                
                if score >= 30:
                    st.warning("💡 This text may be detected as AI-generated. Use the Humanise tab to reduce the risk.")

    with tab_batch:
        st.markdown("### 📦 Batch Humanise Multiple Texts")
        st.markdown("Enter multiple texts separated by `---` (three dashes on a line by itself)")
        
        batch_text = st.text_area("Multiple texts (separated by ---)", height=300, placeholder="First text here\n---\nSecond text here\n---\nThird text here", key="batch_input")
        batch_tone = st.selectbox("Tone for all", list(ADVANCED_TONES.keys()), key="batch_tone")
        
        if batch_text.strip() and st.button("✨ Humanise All", type="primary", use_container_width=True, key="do_batch"):
            texts = [t.strip() for t in batch_text.split("\n---\n") if t.strip()]
            results = []
            progress = st.progress(0)
            for i, text in enumerate(texts):
                with st.spinner(f"Humanising text {i+1}/{len(texts)}..."):
                    result = humanise_text(text, tone=batch_tone)
                    results.append(result)
                    progress.progress((i+1)/len(texts))
            
            combined = "\n\n---\n\n".join(results)
            st.success(f"✅ Humanised {len(results)} texts!")
            st.text_area("All Results", value=combined, height=400, key="batch_result")
            st.download_button("⬇️ Download All", combined.encode(), file_name="humanised_batch.txt", mime="text/plain", use_container_width=True, key="batch_dl")

    if st.button("💬 Back to Chat", use_container_width=True, key="hum_back"):
        st.session_state.app_mode = "chat"
        st.rerun()


def _text_to_docx_bytes(text: str) -> bytes:
    try:
        from docx import Document
        import io
        doc = Document()
        for line in text.splitlines():
            doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except Exception:
        return text.encode()


# ═══════════════════════════════════════════════════════════════
# ENHANCED HTML GENERATOR UI
# ═══════════════════════════════════════════════════════════════

def render_html_generator():
    """Render the enhanced HTML generator that creates real websites."""
    from html_generator_engine import generate_html_page, generate_html_from_file, PAGE_TYPES, COLOR_THEMES
    import streamlit.components.v1 as components
    
    st.markdown("""
<style>
.html-header{background:linear-gradient(135deg,#001020 0%,#000810 100%);border:1px solid #1a4a8b;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.html-title{font-size:2rem;font-weight:900;color:#38bdf8;margin:0 0 4px;}
.html-sub{font-size:.9rem;color:#9090b8;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="html-header">
  <div class="html-title">🌐 AI HTML Generator</div>
  <div class="html-sub">Create real, production-ready websites · Live preview · Download instantly · 15+ page types</div>
</div>
""", unsafe_allow_html=True)

    tab_text, tab_file, tab_preview = st.tabs(["✍️ From Text/Content", "📁 From Uploaded File", "👁️ Live Preview"])

    with tab_text:
        title = st.text_input("Page Title", value="My Awesome Page", key="html_title")
        content = st.text_area("Content / Brief / Data", height=200, placeholder="Describe what you want on the page, or paste any content to convert...", key="html_content")
        
        hc1, hc2 = st.columns(2)
        with hc1:
            ptype = st.selectbox("Page Type", list(PAGE_TYPES.keys()), key="html_ptype")
        with hc2:
            theme = st.selectbox("Color Theme", list(COLOR_THEMES.keys()), key="html_theme")
        
        hc3, hc4, hc5 = st.columns(3)
        with hc3:
            charts = st.checkbox("📊 Include Charts (Chart.js)", key="html_charts")
        with hc4:
            animations = st.checkbox("✨ Animations", value=True, key="html_anims")
        with hc5:
            dark_toggle = st.checkbox("🌙 Dark/Light Toggle", key="html_dark")
        
        extra = st.text_input("Extra instructions (optional)", placeholder="e.g., Include a contact form, Add a pricing table, Make it bilingual...", key="html_extra")
        
        if content.strip() and st.button("⚡ Generate Website", type="primary", use_container_width=True, key="gen_html"):
            with st.spinner("🎨 Creating your website... (10-30 seconds)"):
                html_out = generate_html_page(
                    content, ptype, title, theme, charts, extra, animations, dark_toggle
                )
                st.session_state["html_output"] = html_out
                st.session_state["html_output_title"] = title
        
        if "html_output" in st.session_state:
            html_out = st.session_state["html_output"]
            st.success(f"✅ Website generated! ({len(html_out):,} chars)")
            
            hb1, hb2 = st.columns(2)
            with hb1:
                st.download_button(
                    "⬇️ Download HTML",
                    html_out.encode(),
                    file_name=f"{title.replace(' ','_').lower()}.html",
                    mime="text/html",
                    use_container_width=True,
                    key="html_dl"
                )
            with hb2:
                if st.button("👁️ Preview in App", use_container_width=True, key="preview_btn"):
                    st.session_state["show_preview"] = True
            
            if st.session_state.get("show_preview"):
                st.markdown("#### 👁️ Live Preview")
                components.html(html_out, height=600, scrolling=True)
            
            with st.expander("📄 View HTML Source"):
                st.code(html_out[:5000] + ("..." if len(html_out) > 5000 else ""), language="html")

    with tab_file:
        upl = st.file_uploader("Upload file to convert to HTML", type=["pdf","txt","csv","json","md","docx","xlsx"], key="html_file_up")
        ptype2 = st.selectbox("Page Layout", list(PAGE_TYPES.keys()), key="html_ftype2")
        theme2 = st.selectbox("Theme", list(COLOR_THEMES.keys()), key="html_theme2")
        
        if upl and st.button("🌐 Convert to Website", type="primary", use_container_width=True, key="conv_to_html"):
            raw = upl.read()
            ext = upl.name.rsplit(".",1)[-1].lower()
            
            with st.spinner(f"Converting {upl.name} to a beautiful website..."):
                # Extract content
                try:
                    from converter_engine import _pdf_to_text, _docx_to_text, _csv_to_text, _excel_to_text
                    if ext == "pdf": fc = _pdf_to_text(raw)
                    elif ext == "docx": fc = _docx_to_text(raw)
                    elif ext == "csv": fc = _csv_to_text(raw)
                    elif ext == "xlsx": fc = _excel_to_text(raw)
                    else: fc = raw.decode("utf-8", errors="replace")
                except Exception as e:
                    fc = raw.decode("utf-8", errors="replace")
                
                html_out = generate_html_from_file(fc, ext, upl.name, ptype2)
                st.session_state["html_file_output"] = html_out
                st.session_state["html_file_name"] = upl.name
        
        if "html_file_output" in st.session_state:
            html_out = st.session_state["html_file_output"]
            fname = st.session_state.get("html_file_name","file")
            st.success("✅ Converted!")
            st.download_button("⬇️ Download HTML", html_out.encode(), file_name=fname.rsplit(".",1)[0]+".html", mime="text/html", use_container_width=True, key="html_file_dl")
            with st.expander("👁️ Live Preview"):
                components.html(html_out, height=500, scrolling=True)

    with tab_preview:
        st.markdown("### 👁️ Preview Custom HTML")
        custom_html = st.text_area("Paste HTML to preview", height=250, placeholder="Paste any HTML code here to preview it live...", key="preview_html")
        if custom_html.strip():
            st.markdown("**Live Preview:**")
            components.html(custom_html, height=500, scrolling=True)

    if st.button("💬 Back to Chat", use_container_width=True, key="html_back"):
        st.session_state.app_mode = "chat"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# PLACEHOLDER FEATURES (COMING SOON)
# ═══════════════════════════════════════════════════════════════

def render_coming_soon(feature_name):
    st.markdown(f"""
    <div style="background:rgba(124,106,247,0.05);border:1px solid rgba(124,106,247,0.2);border-radius:16px;padding:60px 20px;text-align:center;margin-top:40px;">
        <h1 style="font-size:3rem;margin-bottom:10px;">🚧</h1>
        <h2 style="color:var(--text);">{feature_name}</h2>
        <p style="color:var(--text2);max-width:500px;margin:0 auto 24px;">We're working hard to bring this feature to ExamHelp v4.0. Stay tuned for the update!</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("← Back to Chat", key=f"back_{feature_name}"):
        st.session_state.app_mode = "chat"
        st.rerun()

def render_citation_generator():
    from advanced_features import render_citation_generator_v2
    render_citation_generator_v2()

def render_regex_tester():
    from advanced_features import render_regex_tester_v2
    render_regex_tester_v2()

def render_vit_academics():
    from advanced_features import render_vit_academics_v2
    render_vit_academics_v2()

def render_study_toolkit():
    from advanced_features import render_study_toolkit_v2
    render_study_toolkit_v2()
# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: CIRCUIT SOLVER
# ═══════════════════════════════════════════════════════════════

def render_circuit_solver():
    """Render the AI Powered Circuit Analysis engine."""
    from circuit_solver_engine import CircuitSolver, get_solver_output_html
    
    st.markdown("""
<style>
.expert-header{background:linear-gradient(135deg,#0a1a2e 0%,#0a3a4e 100%);border:1px solid #1a5a70;border-radius:16px;padding:28px 32px;margin-bottom:24px;}
.expert-title{font-size:2rem;font-weight:900;color:#60a5fa;margin:0 0 4px;}
.expert-sub{font-size:.9rem;color:#90b0d8;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="expert-header">
  <div class="expert-title">⚡ Circuit Solver Pro</div>
  <div class="expert-sub">AI Vision-based analysis · KVL/KCL Solvers · Step-by-step logic · Multimeter accuracy</div>
</div>
""", unsafe_allow_html=True)

    uploaded_circuit = st.file_uploader("📸 Upload circuit diagram (PNG/JPG)", type=["png","jpg","jpeg"], key="circ_upload")
    contrast_val = st.slider("Enhance Image Contrast", 1.0, 3.0, 1.2, 0.1, key="circ_contrast")
    
    if uploaded_circuit and st.button("🚀 Analyze & Solve Circuit", type="primary", use_container_width=True, key="do_circ"):
        with st.spinner("🔍 Gemini Vision analyzing topography..."):
            img_bytes = uploaded_circuit.read()
            if contrast_val > 1.0:
                try:
                    from PIL import Image, ImageEnhance
                    import io
                    img = Image.open(io.BytesIO(img_bytes))
                    enhancer = ImageEnhance.Contrast(img)
                    enhanced_img = enhancer.enhance(contrast_val)
                    out_io = io.BytesIO()
                    enhanced_img.save(out_io, format=img.format or 'PNG')
                    img_bytes = out_io.getvalue()
                except Exception as e:
                    st.warning(f"Could not enhance image: {e}")
            res = CircuitSolver.solve_from_image(img_bytes)
            
            # LaTeX output representation mapping
            st.latex(r"I_{total} = \sum_{i=1}^n \frac{V_i}{R_i} \quad \text{(Generic Reference)}")
            
            html = get_solver_output_html(res)
            st.markdown(html, unsafe_allow_html=True)
            
    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="circ_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: MATH SOLVER
# ═══════════════════════════════════════════════════════════════

def render_math_solver():
    """Render the Advanced Math Solver."""
    from math_solver_engine import MathSolver, get_math_output_html
    
    st.markdown("""
<div class="expert-header" style="background:linear-gradient(135deg,#1a0a2e 0%,#3d1a6b 100%);border-color:#5b2a9e;">
  <div class="expert-title" style="color:#a78bfa;">🎯 Advanced Math Solver</div>
  <div class="expert-sub" style="color:#c4b5fd;">Symbolic Parsing · LaTeX Rendering · Calculus · Algebra · Logic · Hand-written OCR</div>
</div>
""", unsafe_allow_html=True)

    tab_img, tab_txt = st.tabs(["📸 Use Image", "📝 Type Problem"])
    
    with tab_img:
        uploaded_math = st.file_uploader("📸 Upload math problem image", type=["png","jpg","jpeg"], key="math_img")
        if uploaded_math and st.button("🚀 Solve from Image", type="primary", use_container_width=True, key="do_math_img"):
            with st.spinner("🔍 Extracting math from image..."):
                res = MathSolver.solve(image_bytes=uploaded_math.read())
                html = get_math_output_html(res)
                st.markdown(html, unsafe_allow_html=True)
                
    with tab_txt:
        math_q = st.text_area("📝 Problem / Expression", placeholder="e.g. Integrate sin(x)*exp(-x) from 0 to infinity, or x**2 - 4 = 0", key="math_q")
        if math_q and st.button("🚀 Solve Typed Problem", type="primary", use_container_width=True, key="do_math_txt"):
            with st.spinner("🧮 Solving..."):
                res = MathSolver.solve(query_text=math_q)
                html = get_math_output_html(res)
                st.markdown(html, unsafe_allow_html=True)
                
                # Sympy parsing and Plotly graphing for single-var equations
                try:
                    import sympy as sp
                    import numpy as np
                    import plotly.graph_objects as go
                    
                    if 'x' in math_q.lower() and ('=' in math_q or '**' in math_q or '^' in math_q):
                        # Extract the expression (naive single-variable approximation)
                        expr_str = math_q.split('=')[1].strip() if '=' in math_q else math_q.strip()
                        expr_str = expr_str.replace('^', '**')
                        
                        x = sp.Symbol('x')
                        expr = sp.sympify(expr_str)
                        f = sp.lambdify(x, expr, 'numpy')
                        
                        x_vals = np.linspace(-10, 10, 400)
                        y_vals = f(x_vals)
                        
                        fig = go.Figure(data=go.Scatter(x=x_vals, y=y_vals, line=dict(color='#a78bfa', width=3)))
                        fig.update_layout(
                            title=f"Graph of {expr_str}",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#e0e0ff",
                            xaxis_title="x",
                            yaxis_title="y",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    pass

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="math_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: AI DICTIONARY
# ═══════════════════════════════════════════════════════════════

def render_dictionary():
    """Render the AI Dictionary."""
    from dictionary_engine import AIDictionary
    
    st.markdown("""
<div class="expert-header" style="background:linear-gradient(135deg,#0a1a0f 0%,#1a3a2a 100%);border-color:#2a5e3e;">
  <div class="expert-title" style="color:#34d399;">📚 AI Multi-Lang Dictionary</div>
  <div class="expert-sub" style="color:#86efac;">100+ Languages · Etymology · Idioms · Real-world Examples · Cultural Nuance</div>
</div>
""", unsafe_allow_html=True)

    word = st.text_input("🔍 Enter Word or Phrase", placeholder="e.g., Epiphany, Jugaad, Schadenfreude...", key="dict_word")
    lang_choice = st.session_state.get("selected_language", "English")
    
    if word and st.button("🔎 Lookup Word", type="primary", use_container_width=True, key="do_word"):
        with st.spinner(f"AI Linguist analyzing '{word}'..."):
            lookup = AIDictionary.lookup(word, lang_choice)
            st.markdown(lookup)
            
            with st.expander("✨ Historical Etymology"):
                st.markdown(AIDictionary.get_etymology(word))
            with st.expander("🌶️ Cultural Idioms & Metaphors"):
                st.markdown(AIDictionary.get_idioms(word))
                
    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="dict_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: STOCKS DASHBOARD
# ═══════════════════════════════════════════════════════════════

def render_stocks_dashboard():
    """Render the AI Stocks Dashboard."""
    from stocks_engine import get_stock_data, get_ai_market_analysis, get_market_overview, MOCK_STOCKS
    
    st.markdown("""
<div class="expert-header" style="background:linear-gradient(135deg,#1f1f2e 0%,#10101a 100%);border-color:#4a4a6a;">
  <div class="expert-title" style="color:#60a5fa;">💹 AI Market Dashboard</div>
  <div class="expert-sub" style="color:#9090b8;">Track Global Stocks · Real-time AI Sentinel · Sentiment Analysis · Pro Insights</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="background-color: #7f1d1d; color: #fecaca; border: 1px solid #ef4444; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: bold;">
  🚨 PERMANENT WARNING: EDUCATIONAL PURPOSES ONLY. This platform is NOT providing financial advice. All data and analysis provided here is for academic research and simulation contexts. A.I. analysis is prone to hallucination and should NEVER be used for real trading.
</div>
""", unsafe_allow_html=True)

    col_sum, col_search = st.columns([2, 1])
    
    with col_sum:
        st.info(get_market_overview())
        
    with col_search:
        symbol = st.selectbox("🎯 Track specific stock", list(MOCK_STOCKS.keys()), key="stock_search")
        if st.button("📈 Analyze " + symbol, use_container_width=True, key="do_stock"):
            data = get_stock_data(symbol)
            if data:
                st.markdown(f"### {symbol} - {data['name']}")
                color = "green" if data['change'] >= 0 else "red"
                st.markdown(f'Price: **${data["price"]:.2f}** (<span style="color:{color};">{data["change"]}%</span>)', unsafe_allow_html=True)
                
                qual_cols = st.columns(2)
                qual_cols[0].metric("Market Sentiment", "Optimistic", "1.2%")
                qual_cols[1].metric("Earnings Call Tone", "Confident", "Growth-oriented")
                
                with st.spinner("AI analyzing technicals..."):
                    st.markdown(get_ai_market_analysis(symbol, data))

    st.markdown("---")
    # Show Top watchlist
    st.markdown("### 📡 Top Watchlist")
    wcols = st.columns(3)
    for i, sym in enumerate(list(MOCK_STOCKS.keys())[:9]):
        with wcols[i % 3]:
            d = MOCK_STOCKS[sym]
            color = "green" if d['change'] >= 0 else "red"
            st.markdown(f'**{sym}**: ${d["price"]:.0f} (<span style="color:{color};">{d["change"]}%</span>)', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="stocks_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: LEGAL EXPERT
# ═══════════════════════════════════════════════════════════════

def render_legal_expert():
    """Render the AI Legal Analysis engine."""
    from utils.legal_engine import analyze_legal_case, generate_legal_document_template
    
    st.markdown("""
<div class="expert-header" style="background:linear-gradient(135deg,#2e1a0a 0%,#1a0a05 100%);border-color:#5a3000;">
  <div class="expert-title" style="color:#f59e0b;">🏛️ Legal Case Analyser</div>
  <div class="expert-sub" style="color:#92400e;">Professional Legal Reasoning · IRAC Framework Enforcement · Jurisdiction Scoping</div>
</div>
""", unsafe_allow_html=True)

    tab_case, tab_doc = st.tabs(["⚖️ Case Analyzer", "📄 Document Template"])

    with tab_case:
        facts = st.text_area("📄 Enter Case Facts or Scenario", placeholder="Describe the material facts of the legal scenario...", key="legal_facts")
        jurisdiction = st.selectbox("🌍 Jurisdiction Filter", ["Common Law", "International", "Indian Penal Code (IPC)", "US Federal/State", "UK English Law"], key="legal_juris")
        irac_mode = st.checkbox("Strict IRAC Framework", value=True, key="legal_irac")
        
        if facts and st.button("⚖️ Analyze Case via Senior Counsel", type="primary", use_container_width=True, key="do_legal"):
            with st.spinner("Senior Counsel reviewing facts applying IRAC framework..."):
                st.markdown(analyze_legal_case(facts, jurisdiction))
                
    with tab_doc:
        doc_type = st.text_input("Document Type", placeholder="e.g. Non-Disclosure Agreement (NDA)", key="legal_doctype")
        parties = st.text_input("Parties Involved (comma separated)", placeholder="e.g. Acme Corp, John Doe", key="legal_parties")
        doc_jurisdiction = st.selectbox("🌍 Jurisdiction", ["Common Law", "International", "India", "US", "UK"], key="legal_doc_juris")
        
        if doc_type and parties and st.button("📄 Generate Template", type="primary", use_container_width=True, key="do_legal_doc"):
            with st.spinner("Generating boilerplate template..."):
                st.markdown(generate_legal_document_template(doc_type, parties.split(","), doc_jurisdiction))
            
    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="legal_back"):
        st.session_state.app_mode = "chat"; st.rerun()



# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: MEDICAL EXPERT
# ═══════════════════════════════════════════════════════════════

def render_medical_expert():
    """Render the AI Medical Researcher engine."""
    from utils.medical_engine import analyze_medical_condition, analyze_drug_interaction
    
    st.markdown("""
<div class="expert-header" style="background:linear-gradient(135deg,#0a1a1a 0%,#000 100%);border-color:#0891b2;">
  <div class="expert-title" style="color:#06b6d4;">🩺 Medical Research Guide</div>
  <div class="expert-sub" style="color:#0891b2;">Clinical Scenario Analysis · Epidemiology & Pathophysiology · ICD Integration</div>
</div>
""", unsafe_allow_html=True)

    st.error("🚨 PERMANENT DISCLAIMER: EDUCATIONAL RESEARCH MODE ONLY. This analysis is NOT intended for medical diagnosis, treatment, or clinical decision-making. Always consult a licensed healthcare professional.")
    
    tab_cond, tab_drugs = st.tabs(["🔬 Condition Analysis", "💊 Drug Interaction"])

    with tab_cond:
        condition = st.text_input("📋 Enter Medical Condition or Symptoms", placeholder="e.g. Type 2 Diabetes Mellitus, or progressive dyspnea...", key="med_cond")
        if condition and st.button("🔗 Run Deep Clinical Reasoning", type="primary", use_container_width=True, key="do_med_cond"):
            with st.spinner("Clinical Advisor analyzing epidemiology and pathophysiology..."):
                st.markdown(analyze_medical_condition(condition))
                
    with tab_drugs:
        drugs = st.text_input("💊 Enter Drugs (comma separated)", placeholder="e.g. Warfarin, Aspirin, St. John's Wort", key="med_drugs")
        if drugs and st.button("🧪 Analyze Interactions", type="primary", use_container_width=True, key="do_med_drugs"):
            with st.spinner("Checking pharmacological interactions..."):
                st.markdown(analyze_drug_interaction(drugs.split(",")))
            
    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="med_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: ADVANCED RESEARCH PRO
# ═══════════════════════════════════════════════════════════════

def render_research_pro():
    """Render the Advanced Research Tools engine."""
    from research_tools_engine import ResearchTools
    
    st.markdown("""
<div class="expert-header" style="background:linear-gradient(135deg,#1a1a1a 0%,#000 100%);border-color:#71717a;">
  <div class="expert-title" style="color:#e4e4e7;">🔬 Advanced Research Pro</div>
  <div class="expert-sub" style="color:#a1a1aa;">Peer-Review Critique · Lit-Review Mapper · Research Gap Identification · Academic Depth</div>
</div>
""", unsafe_allow_html=True)

    tab_crit, tab_lit = st.tabs(["📑 Paper Critique", "📚 Lit-Review Mapper"])
    
    with tab_crit:
        abstract = st.text_area("📝 Enter Abstract or Section for Critique", placeholder="Paste scientific text here for rigorous peer review...", key="crit_text")
        if abstract and st.button("🔍 Run Peer Review Critique", type="primary", use_container_width=True, key="do_crit"):
            with st.spinner("Research Scientist performing peer review..."):
                st.markdown(ResearchTools.critique_paper(abstract))
                
    with tab_lit:
        topics = st.text_input("🔑 Focus Topics (comma separated)", key="lit_topics")
        focus = st.selectbox("🎯 Academic Focus", ["Systematic Review", "Phenomenological", "Case Study", "Technical/Algorithm"], key="lit_focus")
        if topics and st.button("🛠️ Map Literature Opening", type="primary", use_container_width=True, key="do_lit"):
            with st.spinner("Building literature structure..."):
                st.markdown(ResearchTools.generate_lit_review(topics.split(","), focus))

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="res_back"):
        st.session_state.app_mode = "chat"; st.rerun()


# ═══════════════════════════════════════════════════════════════
# EXPERT ENGINES: PROJECT ARCHITECT
# ═══════════════════════════════════════════════════════════════

def render_project_architect():
    """Render the Technical Project Architect engine."""
    from project_blueprint_engine import ProjectArchitect
    
    st.markdown("""
<div class="expert-header" style="background:linear-gradient(135deg,#0a1a2e 0%,#020617 100%);border-color:#1e40af;">
  <div class="expert-title" style="color:#3b82f6;">🏗️ Technical Project Architect</div>
  <div class="expert-sub" style="color:#60a5fa;">Full Stack Blueprints · System Architecture · Mermaid Diagrams · Tech-Stack Optimizer</div>
</div>
""", unsafe_allow_html=True)

    name = st.text_input("🛠️ Project Name", placeholder="e.g., Real-time Collaboration App...", key="proj_name")
    stack = st.text_input("💻 Preferred Tech Stack", placeholder="e.g., Next.js, FastAPI, PostgreSQL...", key="proj_stack")
    desc = st.text_area("📝 Detailed Description / Requirements", key="proj_desc")
    
    if name and desc and st.button("🚀 Generate Full Architectural Blueprint", type="primary", use_container_width=True, key="do_proj"):
        with st.spinner("Principal Architect drafting blueprints..."):
            st.markdown(ProjectArchitect.generate_blueprint(name, stack, desc))
            
            with st.expander("📊 System Architecture Diagram (Mermaid)"):
                code = ProjectArchitect.generate_architecture_diagram_code(desc)
                st.code(code, language="mermaid")

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="proj_back"):
        st.session_state.app_mode = "chat"; st.rerun()
