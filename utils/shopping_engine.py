"""
shopping_engine.py — Smart Shopping Finder with real web scraping
"""

import streamlit as st
import requests
import re
import time
import json
import hashlib
from urllib.parse import quote_plus
from utils import ai_engine

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

PRODUCT_PLATFORMS = {
    "Amazon": {"url": "https://www.amazon.in/s?k={query}", "domain": "amazon.in", "icon": "🟠"},
    "Flipkart": {"url": "https://www.flipkart.com/search?q={query}", "domain": "flipkart.com", "icon": "🔵"},
    "Meesho": {"url": "https://www.meesho.com/search?q={query}", "domain": "meesho.com", "icon": "🟣"},
    "Snapdeal": {"url": "https://www.snapdeal.com/search?keyword={query}", "domain": "snapdeal.com", "icon": "🔴"},
    "Myntra": {"url": "https://www.myntra.com/{query}", "domain": "myntra.com", "icon": "🩷"},
    "Nykaa": {"url": "https://www.nykaa.com/search/result/?q={query}", "domain": "nykaa.com", "icon": "💗"},
    "Croma": {"url": "https://www.croma.com/searchB?q={query}", "domain": "croma.com", "icon": "🟢"},
}

GROCERY_PLATFORMS = {
    "JioMart": {"url": "https://www.jiomart.com/search/{query}", "domain": "jiomart.com", "icon": "🔵"},
    "Blinkit": {"url": "https://blinkit.com/s/?q={query}", "domain": "blinkit.com", "icon": "🟡"},
    "BigBasket": {"url": "https://www.bigbasket.com/ps/?q={query}", "domain": "bigbasket.com", "icon": "🟢"},
    "Swiggy Instamart": {"url": "https://www.swiggy.com/search?query={query}", "domain": "swiggy.com", "icon": "🟠"},
}

FOOD_PLATFORMS = {
    "Swiggy": {"url": "https://www.swiggy.com/search?query={query}", "domain": "swiggy.com", "icon": "🟠"},
    "Zomato": {"url": "https://www.zomato.com/search?q={query}", "domain": "zomato.com", "icon": "🔴"},
    "EatSure": {"url": "https://www.eatsure.com/search?query={query}", "domain": "eatsure.com", "icon": "🟣"},
}


def _get_headers():
    import random
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def _cache_key(query: str, platform: str) -> str:
    return hashlib.md5(f"{query}_{platform}".encode()).hexdigest()


def _get_cached(query: str, platform: str):
    key = f"shop_cache_{_cache_key(query, platform)}"
    cached = st.session_state.get(key)
    if cached and time.time() - cached.get("time", 0) < 1800:
        return cached.get("data")
    return None


def _set_cache(query: str, platform: str, data):
    key = f"shop_cache_{_cache_key(query, platform)}"
    st.session_state[key] = {"data": data, "time": time.time()}


def _scrape_platform(query: str, platform_name: str, platform_info: dict, category: str = "product") -> list:
    cached = _get_cached(query, platform_name)
    if cached is not None:
        return cached

    encoded = quote_plus(query)
    url = platform_info["url"].format(query=encoded)
    results = []

    try:
        resp = requests.get(url, headers=_get_headers(), timeout=10, allow_redirects=True)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')

            if platform_name == "Amazon":
                items = soup.select('[data-component-type="s-search-result"]')[:8]
                for item in items:
                    try:
                        title_el = item.select_one('h2 a span')
                        price_el = item.select_one('.a-price .a-offscreen')
                        rating_el = item.select_one('.a-icon-alt')
                        img_el = item.select_one('img.s-image')
                        link_el = item.select_one('h2 a')
                        if title_el:
                            results.append({
                                "name": title_el.text.strip()[:100],
                                "price": price_el.text.strip() if price_el else "Price N/A",
                                "rating": rating_el.text.split()[0] if rating_el else "N/A",
                                "image": img_el.get("src", "") if img_el else "",
                                "url": "https://www.amazon.in" + link_el.get("href", "") if link_el else url,
                                "platform": platform_name,
                                "icon": platform_info["icon"],
                            })
                    except Exception:
                        continue

            elif platform_name == "Flipkart":
                items = soup.select('div._1AtVbE')[:8] or soup.select('div._4ddWXP')[:8]
                for item in items:
                    try:
                        title_el = item.select_one('a._1fQZEK') or item.select_one('div._4rR01T') or item.select_one('a.s1Q9rs')
                        price_el = item.select_one('div._30jeq3')
                        rating_el = item.select_one('div._3LWZlK')
                        img_el = item.select_one('img._396cs4') or item.select_one('img._2r_T1I')
                        link_el = item.select_one('a._1fQZEK') or item.select_one('a.s1Q9rs') or item.select_one('a._2rpwqI')
                        if title_el or price_el:
                            results.append({
                                "name": (title_el.text.strip() if title_el else "Product")[:100],
                                "price": price_el.text.strip() if price_el else "Price N/A",
                                "rating": rating_el.text.strip() if rating_el else "N/A",
                                "image": img_el.get("src", "") if img_el else "",
                                "url": "https://www.flipkart.com" + link_el.get("href", "") if link_el else url,
                                "platform": platform_name,
                                "icon": platform_info["icon"],
                            })
                    except Exception:
                        continue
            else:
                title_els = soup.select('h2, h3, [class*="title"], [class*="name"], [class*="product"]')[:8]
                for el in title_els:
                    text = el.get_text(strip=True)
                    if len(text) > 5 and len(text) < 200:
                        results.append({
                            "name": text[:100],
                            "price": "Visit site",
                            "rating": "N/A",
                            "image": "",
                            "url": url,
                            "platform": platform_name,
                            "icon": platform_info["icon"],
                        })
                        if len(results) >= 5:
                            break

        if not results:
            raise Exception("No results from scraping")

    except Exception:
        try:
            results = _ai_search_fallback(query, platform_name, platform_info["domain"], category)
        except Exception:
            results = [{
                "name": f"Search {platform_name} for '{query}'",
                "price": "Visit site",
                "rating": "N/A",
                "image": "",
                "url": url,
                "platform": platform_name,
                "icon": platform_info["icon"],
                "error": True,
            }]

    _set_cache(query, platform_name, results)
    return results


def _ai_search_fallback(query: str, platform: str, domain: str, category: str) -> list:
    prompt = f"""Search for "{query}" on {platform} ({domain}).
Return a JSON array of up to 5 products. Each object must have:
- "name": product name
- "price": price string with ₹ or $ symbol
- "rating": rating string like "4.2"
- "url": a real product URL on {domain} (use search URL if exact not known: https://www.{domain}/search?q={quote_plus(query)})
- "image": empty string

Return ONLY the JSON array."""

    try:
        result = ai_engine.generate(
            prompt=prompt,
            model="llama-3.1-8b-instant",
            json_mode=True,
            max_tokens=1024,
            temperature=0.1,
        )
        data = json.loads(result) if isinstance(result, str) else result
        if isinstance(data, list):
            for item in data:
                item["platform"] = platform
                item["icon"] = "🔍"
            return data[:5]
    except Exception:
        pass
    return []


def search_all_platforms(query: str, platforms: dict, category: str = "product") -> list:
    all_results = []
    for name, info in platforms.items():
        results = _scrape_platform(query, name, info, category)
        all_results.extend(results)
    return all_results


def _parse_price(price_str: str) -> float:
    try:
        cleaned = re.sub(r'[^\d.]', '', str(price_str))
        return float(cleaned) if cleaned else float('inf')
    except (ValueError, TypeError):
        return float('inf')


def render_shopping_finder():
    st.markdown("""
<style>
.shop-header{background:linear-gradient(135deg,#0a2010 0%,#051510 100%);border:1px solid #1a5a30;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.shop-title{font-size:2rem;font-weight:900;color:#4ade80;margin:0 0 4px;}
.shop-sub{font-size:.9rem;color:#9090b8;}
.product-card{background:var(--bg2-glass);border:1px solid var(--bd-glass);border-radius:14px;padding:14px;margin:6px 0;transition:all .25s;backdrop-filter:blur(12px);}
.product-card:hover{border-color:var(--accent-bd);transform:translateY(-2px);box-shadow:0 4px 16px var(--accent-glow);}
.best-deal{position:relative;border-color:#4ade80 !important;}
.best-deal::after{content:'🏆 BEST DEAL';position:absolute;top:-10px;right:10px;background:#4ade80;color:#000;font-size:.65rem;font-weight:800;padding:2px 8px;border-radius:8px;}
.platform-badge{display:inline-flex;align-items:center;gap:4px;background:var(--bg4-glass);border:1px solid var(--bd-glass);border-radius:8px;padding:2px 8px;font-size:.72rem;color:var(--text2);}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="shop-header">
  <div class="shop-title">🛒 Smart Shopping Finder</div>
  <div class="shop-sub">Compare prices across Amazon, Flipkart, Meesho, Myntra, JioMart & more · Real-time search</div>
</div>
""", unsafe_allow_html=True)

    if "shop_wishlist" not in st.session_state:
        st.session_state.shop_wishlist = []

    search_query = st.text_input("🔍 What are you looking for?",
                                 placeholder="e.g. iPhone 15, Nike shoes, Samsung TV...",
                                 key="shop_search")

    tab_products, tab_grocery, tab_food, tab_wishlist = st.tabs([
        "🛍️ Products", "🥦 Groceries", "🍕 Food Delivery", "❤️ Wishlist"
    ])

    with tab_products:
        if search_query:
            if st.button("🔍 Search Products", type="primary", use_container_width=True, key="shop_prod_btn"):
                with st.spinner("Searching across platforms..."):
                    results = search_all_platforms(search_query, PRODUCT_PLATFORMS, "product")
                    st.session_state.shop_product_results = results

            results = st.session_state.get("shop_product_results", [])
            if results:
                _render_results(results, "product", search_query)

    with tab_grocery:
        if search_query:
            if st.button("🔍 Search Groceries", type="primary", use_container_width=True, key="shop_groc_btn"):
                with st.spinner("Searching grocery platforms..."):
                    results = search_all_platforms(search_query, GROCERY_PLATFORMS, "grocery")
                    st.session_state.shop_grocery_results = results

            results = st.session_state.get("shop_grocery_results", [])
            if results:
                _render_results(results, "grocery", search_query)

    with tab_food:
        if search_query:
            if st.button("🔍 Search Food", type="primary", use_container_width=True, key="shop_food_btn"):
                with st.spinner("Searching food platforms..."):
                    results = search_all_platforms(search_query, FOOD_PLATFORMS, "food")
                    st.session_state.shop_food_results = results

            results = st.session_state.get("shop_food_results", [])
            if results:
                _render_results(results, "food", search_query)

    with tab_wishlist:
        st.markdown("### ❤️ Your Wishlist")
        if st.session_state.shop_wishlist:
            for i, item in enumerate(st.session_state.shop_wishlist):
                c1, c2, c3 = st.columns([5, 2, 1])
                with c1:
                    st.markdown(f"**{item['name'][:60]}** — {item.get('price', 'N/A')}")
                with c2:
                    st.markdown(f'<span class="platform-badge">{item.get("icon", "🛒")} {item.get("platform", "")}</span>', unsafe_allow_html=True)
                with c3:
                    if st.button("✕", key=f"wl_rm_{i}"):
                        st.session_state.shop_wishlist.pop(i)
                        st.rerun()
        else:
            st.info("Your wishlist is empty. Click ❤️ on any product to save it.")

    if st.button("💬 Back to Chat", use_container_width=True, key="shop_back"):
        st.session_state.app_mode = "chat"
        st.rerun()


def _render_results(results: list, category: str, query: str):
    valid_results = [r for r in results if not r.get("error")]
    error_platforms = [r["platform"] for r in results if r.get("error")]

    if error_platforms:
        st.warning(f"⚠️ Could not fetch from: {', '.join(error_platforms)}. Direct links provided instead.")

    if not valid_results and not error_platforms:
        st.warning("No results found. Try a different search term.")
        return

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        price_range = st.slider("Price range (₹)", 0, 200000, (0, 200000), key=f"shop_price_{category}")
    with fc2:
        min_rating = st.slider("Min rating", 0.0, 5.0, 0.0, 0.5, key=f"shop_rating_{category}")
    with fc3:
        sort_by = st.selectbox("Sort by", ["Relevance", "Price: Low to High", "Price: High to Low", "Rating"],
                               key=f"shop_sort_{category}")

    platforms_available = list(set(r.get("platform", "") for r in valid_results))
    selected_platforms = st.multiselect("Platforms", platforms_available, default=platforms_available,
                                       key=f"shop_platforms_{category}")

    filtered = []
    for r in valid_results:
        if r.get("platform") not in selected_platforms:
            continue
        p = _parse_price(r.get("price", ""))
        if p < price_range[0] or p > price_range[1]:
            continue
        try:
            if float(r.get("rating", "0").replace("N/A", "0")) < min_rating:
                continue
        except (ValueError, TypeError):
            pass
        filtered.append(r)

    if sort_by == "Price: Low to High":
        filtered.sort(key=lambda x: _parse_price(x.get("price", "")))
    elif sort_by == "Price: High to Low":
        filtered.sort(key=lambda x: -_parse_price(x.get("price", "")))
    elif sort_by == "Rating":
        filtered.sort(key=lambda x: -float(x.get("rating", "0").replace("N/A", "0") or "0"), reverse=False)

    cheapest_price = float('inf')
    cheapest_idx = -1
    for i, r in enumerate(filtered):
        p = _parse_price(r.get("price", ""))
        if p < cheapest_price:
            cheapest_price = p
            cheapest_idx = i

    st.markdown(f"**{len(filtered)} results** across {len(selected_platforms)} platforms")

    cols = st.columns(2)
    for i, r in enumerate(filtered[:20]):
        is_best = (i == cheapest_idx and cheapest_price < float('inf'))
        card_class = "product-card best-deal" if is_best else "product-card"

        with cols[i % 2]:
            st.markdown(f"""
<div class="{card_class}">
  <div style="display:flex;gap:12px;align-items:flex-start;">
    {"<img src='" + r.get('image', '') + "' style='width:60px;height:60px;object-fit:cover;border-radius:8px;' onerror=\"this.style.display='none'\"/>" if r.get('image') else ""}
    <div style="flex:1;">
      <div style="font-size:.88rem;font-weight:600;color:var(--text);line-height:1.3;">{r.get('name', '')[:80]}</div>
      <div style="display:flex;gap:8px;align-items:center;margin-top:4px;">
        <span style="font-size:1rem;font-weight:800;color:#4ade80;">{r.get('price', 'N/A')}</span>
        <span style="font-size:.75rem;color:#fbbf24;">★ {r.get('rating', 'N/A')}</span>
      </div>
      <span class="platform-badge">{r.get('icon', '🛒')} {r.get('platform', '')}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

            bc1, bc2 = st.columns(2)
            with bc1:
                st.markdown(f'<a href="{r.get("url", "#")}" target="_blank"><button style="background:linear-gradient(135deg,#4ade80,#059669);color:#000;border:none;padding:6px 12px;border-radius:8px;cursor:pointer;font-size:.8rem;font-weight:600;width:100%;">Buy Now →</button></a>', unsafe_allow_html=True)
            with bc2:
                if st.button("❤️", key=f"wl_add_{category}_{i}", use_container_width=True):
                    st.session_state.shop_wishlist.append(r)
                    st.toast(f"Added to wishlist: {r.get('name', '')[:40]}")

    if len(filtered) > 2:
        try:
            import plotly.graph_objects as go
            platform_prices = {}
            for r in filtered:
                p = _parse_price(r.get("price", ""))
                if p < float('inf'):
                    pn = r.get("platform", "Unknown")
                    if pn not in platform_prices or p < platform_prices[pn]:
                        platform_prices[pn] = p

            if platform_prices:
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(platform_prices.keys()),
                        y=list(platform_prices.values()),
                        marker_color=['#4ade80' if v == min(platform_prices.values()) else '#7c6af7'
                                      for v in platform_prices.values()],
                    )
                ])
                fig.update_layout(
                    title="Lowest Price by Platform",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#f0f0ff",
                    margin=dict(t=40, b=20, l=20, r=20),
                    height=300,
                    yaxis_title="Price (₹)",
                )
                with st.expander("📊 Price Comparison Chart"):
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except ImportError:
            pass
