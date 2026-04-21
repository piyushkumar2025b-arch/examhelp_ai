"""
map_engine.py — Ultra-Colorful Map Engine v3.0 (ExamHelp AI)
Uses: Folium + streamlit-folium (no paid API needed)
Geocoding: Nominatim (OpenStreetMap, free)
Routing: OSRM (free open-source routing)
AI: Gemini place info
Preserves: VIT campus data, India travel data
"""
from __future__ import annotations
import math
import time
import urllib.parse
import streamlit as st
import requests
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# PRESERVED DATA FROM ORIGINAL
# ─────────────────────────────────────────────────────────────────────────────
VIT_CHENNAI_LOCATIONS = {
    "🏫 Academic Buildings": [
        {"name": "Technology Tower (TT)", "lat": 12.8406, "lng": 80.1534, "desc": "Main academic building with modern labs", "type": "academic"},
        {"name": "Anna Auditorium",       "lat": 12.8408, "lng": 80.1528, "desc": "Main auditorium for events & convocation", "type": "academic"},
        {"name": "Mechanical Block",      "lat": 12.8412, "lng": 80.1540, "desc": "Mechanical Engineering labs", "type": "academic"},
        {"name": "Civil Block",           "lat": 12.8404, "lng": 80.1545, "desc": "Civil & Structural Engineering", "type": "academic"},
        {"name": "Chemistry Block",       "lat": 12.8415, "lng": 80.1530, "desc": "Chemistry labs and lecture halls", "type": "academic"},
        {"name": "MBA Block",             "lat": 12.8400, "lng": 80.1520, "desc": "School of Business, MBA programs", "type": "academic"},
    ],
    "🏠 Hostels": [
        {"name": "MH1 - Men's Hostel 1",  "lat": 12.8398, "lng": 80.1510, "desc": "Men's residential block", "type": "hostel"},
        {"name": "LH1 - Ladies Hostel 1", "lat": 12.8430, "lng": 80.1525, "desc": "Women's residential block", "type": "hostel"},
    ],
    "🍽️ Food & Essentials": [
        {"name": "Central Cafeteria", "lat": 12.8410, "lng": 80.1522, "desc": "Main dining hall", "type": "food"},
        {"name": "Medical Centre",    "lat": 12.8402, "lng": 80.1535, "desc": "Campus health centre", "type": "health"},
    ],
    "🏋️ Sports": [
        {"name": "Main Sports Ground", "lat": 12.8390, "lng": 80.1520, "desc": "Cricket, football & athletics", "type": "sports"},
        {"name": "Swimming Pool",      "lat": 12.8388, "lng": 80.1530, "desc": "Olympic-size swimming pool", "type": "sports"},
    ],
    "📚 Library & Labs": [
        {"name": "Central Library",      "lat": 12.8409, "lng": 80.1532, "desc": "Main library with digital resources", "type": "library"},
        {"name": "Computer Labs (GDN)", "lat": 12.8413, "lng": 80.1536, "desc": "General computing labs", "type": "lab"},
    ],
}

INDIA_DESTINATIONS = {
    "🏔️ North India": [
        {"name": "Taj Mahal, Agra",         "lat": 27.1751, "lng": 78.0421, "desc": "UNESCO World Heritage — Mughal marble mausoleum"},
        {"name": "Jaipur City Palace",       "lat": 26.9255, "lng": 75.8237, "desc": "Pink City royal residence & museum"},
        {"name": "Varanasi Ghats",           "lat": 25.3176, "lng": 83.0062, "desc": "Oldest living city, spiritual capital of India"},
        {"name": "Golden Temple, Amritsar",  "lat": 31.6200, "lng": 74.8765, "desc": "Holiest Sikh shrine"},
    ],
    "🌊 South India": [
        {"name": "Meenakshi Temple, Madurai","lat": 9.9195,  "lng": 78.1194, "desc": "Ancient Dravidian temple — 33,000 sculptures"},
        {"name": "Hampi Ruins, Karnataka",   "lat": 15.3350, "lng": 76.4600, "desc": "UNESCO — Vijayanagara Empire ruins"},
        {"name": "Munnar Tea Gardens",       "lat": 10.0889, "lng": 77.0595, "desc": "Kerala hill station — rolling tea estates"},
        {"name": "Backwaters, Alleppey",     "lat": 9.4981,  "lng": 76.3388, "desc": "Kerala houseboat cruises & lagoons"},
    ],
    "🏖️ Coastal Gems": [
        {"name": "Goa Beaches",       "lat": 15.2993, "lng": 74.1240, "desc": "Golden beaches, Portuguese heritage, seafood"},
        {"name": "Andaman Islands",   "lat": 11.7401, "lng": 92.6586, "desc": "Pristine coral reefs & white sand beaches"},
        {"name": "Pondicherry",       "lat": 11.9416, "lng": 79.8083, "desc": "French colonial quarter & Auroville"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# VIBRANT COLOR PALETTE — neon/vivid per type
# ─────────────────────────────────────────────────────────────────────────────
TYPE_COLORS = {
    "academic": "#38bdf8",   # sky blue
    "hostel":   "#c084fc",   # vivid purple
    "food":     "#4ade80",   # neon green
    "sports":   "#fb923c",   # vivid orange
    "library":  "#f472b6",   # hot pink
    "lab":      "#22d3ee",   # cyan
    "health":   "#f87171",   # coral red
    "finance":  "#facc15",   # gold
    "search":   "#a78bfa",   # violet
    "custom":   "#34d399",   # emerald
}

# Glow/border accent per type (slightly brighter shade)
TYPE_GLOW = {
    "academic": "#7dd3fc",
    "hostel":   "#e879f9",
    "food":     "#86efac",
    "sports":   "#fdba74",
    "library":  "#f9a8d4",
    "lab":      "#67e8f9",
    "health":   "#fca5a5",
    "finance":  "#fde68a",
    "search":   "#c4b5fd",
    "custom":   "#6ee7b7",
}

# Icon emoji per type
TYPE_ICONS = {
    "academic": "🎓",
    "hostel":   "🏠",
    "food":     "🍽️",
    "sports":   "⚽",
    "library":  "📚",
    "lab":      "🔬",
    "health":   "❤️",
    "finance":  "💰",
    "search":   "📍",
    "custom":   "📌",
}

# ─────────────────────────────────────────────────────────────────────────────
# BACKWARD COMPAT: original functions still work
# ─────────────────────────────────────────────────────────────────────────────
def calculate_distance(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def get_nearest_locations(lat, lng, location_type=None, max_results=5):
    all_locs = [l for g in VIT_CHENNAI_LOCATIONS.values() for l in g]
    if location_type:
        all_locs = [l for l in all_locs if l.get("type") == location_type]
    for loc in all_locs:
        loc["distance_km"] = calculate_distance(lat, lng, loc["lat"], loc["lng"])
    return sorted(all_locs, key=lambda x: x["distance_km"])[:max_results]


# ─────────────────────────────────────────────────────────────────────────────
# FREE GEOCODING (Nominatim/OpenStreetMap)
# ─────────────────────────────────────────────────────────────────────────────
_NOM_HEADERS = {"User-Agent": "ExamHelpAI/3.0 (examhelp@ai.com)"}

def geocode(place: str) -> Tuple[Optional[float], Optional[float]]:
    """Geocode a place name using Nominatim (free, no key)."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(place)}&format=json&limit=1"
        resp = requests.get(url, headers=_NOM_HEADERS, timeout=6).json()
        if resp:
            return float(resp[0]["lat"]), float(resp[0]["lon"])
    except Exception:
        pass
    return None, None


def geocode_details(place: str) -> dict:
    """Return full details from Nominatim."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(place)}&format=json&limit=1&addressdetails=1"
        resp = requests.get(url, headers=_NOM_HEADERS, timeout=6).json()
        if resp:
            return resp[0]
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# FREE ROUTING (OSRM)
# ─────────────────────────────────────────────────────────────────────────────
def get_route(origin: str, destination: str) -> dict:
    """Get driving route using OSRM (free, no key needed)."""
    olat, olon = geocode(origin)
    dlat, dlon = geocode(destination)
    if None in (olat, olon, dlat, dlon):
        return {"error": f"Could not geocode origin or destination."}
    try:
        url = (f"http://router.project-osrm.org/route/v1/driving/"
               f"{olon},{olat};{dlon},{dlat}?overview=full&geometries=geojson")
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("code") != "Ok":
            return {"error": data.get("message", "Route not found")}
        route = data["routes"][0]
        dist_km = round(route["distance"] / 1000, 1)
        dur_min = round(route["duration"] / 60)
        return {
            "distance_km": dist_km,
            "duration_min": dur_min,
            "geojson": route["geometry"],
            "origin_coords": (olat, olon),
            "dest_coords": (dlat, dlon),
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# WIKIPEDIA PLACE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
def get_wiki_summary(place: str) -> str:
    try:
        clean = place.split(",")[0].strip().replace(" ", "_")
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean)}",
            headers=_NOM_HEADERS, timeout=5
        )
        if r.status_code == 200:
            return r.json().get("extract", "")
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# AI PLACE INFO
# ─────────────────────────────────────────────────────────────────────────────
def ai_place_info(place: str) -> str:
    try:
        from utils import ai_engine
        prompt = (
            f"Write a rich 3-paragraph summary about {place} covering: "
            f"1) History and significance, 2) Geography and culture, 3) Travel tips and must-sees. "
            f"Be vivid, informative, and engaging. About 200 words total."
        )
        return ai_engine.generate(prompt, max_tokens=400)
    except Exception as e:
        return f"AI info unavailable: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# COLORFUL FOLIUM MAP BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def _build_folium_map(
    center_lat: float = 20.5937,
    center_lng: float = 78.9629,
    zoom: int = 5,
    tile_layer: str = "voyager",
    markers: List[Dict] = None,
    route_data: dict = None,
) -> "folium.Map":
    import folium
    from folium import plugins

    TILES = {
        "dark":       ("CartoDB dark_matter", None),
        "voyager":    ("CartoDB Voyager", None),
        "standard":   ("OpenStreetMap", None),
        "satellite":  (
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Esri World Imagery"
        ),
        "terrain":    (
            "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
            'Map tiles by <a href="http://stamen.com">Stamen Design</a>, '
            'under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. '
            'Data by <a href="http://openstreetmap.org">OpenStreetMap</a>'
        ),
        "light":      ("CartoDB positron", None),
        "toner":      (
            "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
            'Map tiles by <a href="http://stamen.com">Stamen Design</a>, '
            'under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. '
            'Data by <a href="http://openstreetmap.org">OpenStreetMap</a>'
        ),
    }

    tile_url, attr = TILES.get(tile_layer, TILES["voyager"])
    if attr:
        m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom, tiles=None)
        folium.TileLayer(tile_url, name=tile_layer.title(), attr=attr).add_to(m)
    else:
        m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom, tiles=tile_url)

    # ── Add colorful markers ────────────────────────────────────────────────
    if markers:
        for mk in markers:
            lat, lng = mk.get("lat"), mk.get("lng")
            if lat is None or lng is None:
                continue

            mtype = mk.get("type", "custom")
            color = TYPE_COLORS.get(mtype, "#a78bfa")
            glow  = TYPE_GLOW.get(mtype, "#c4b5fd")
            icon_emoji = TYPE_ICONS.get(mtype, "📍")

            popup_html = f"""
<div style="
  font-family:'Segoe UI',sans-serif;
  background:linear-gradient(135deg,#1e1b4b,#312e81);
  border:2px solid {color};
  border-radius:14px;
  padding:14px 16px;
  min-width:180px;
  box-shadow:0 0 18px {color}88;
">
  <div style="font-size:1.4rem;margin-bottom:4px;">{icon_emoji}</div>
  <div style="color:{color};font-weight:800;font-size:.95rem;margin-bottom:6px;">
    {mk.get('name','')}
  </div>
  <div style="color:#c7d2fe;font-size:.78rem;line-height:1.4;">
    {mk.get('desc','')}
  </div>
</div>
"""
            # Pulsing circle marker with DivIcon for emoji label
            # Outer glow ring
            folium.CircleMarker(
                location=[lat, lng],
                radius=14,
                color=glow,
                fill=False,
                weight=2,
                opacity=0.45,
            ).add_to(m)
            # Main filled circle
            folium.CircleMarker(
                location=[lat, lng],
                radius=9,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.92,
                weight=2,
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=f"{icon_emoji} {mk.get('name', '')}",
            ).add_to(m)

    # ── Draw colorful route ─────────────────────────────────────────────────
    if route_data and not route_data.get("error"):
        # Main route line — vivid gradient-like double layer
        folium.GeoJson(
            route_data["geojson"],
            style_function=lambda x: {
                "color": "#1e1b4b", "weight": 10, "opacity": 0.5
            }
        ).add_to(m)
        folium.GeoJson(
            route_data["geojson"],
            style_function=lambda x: {
                "color": "#818cf8", "weight": 5, "opacity": 1.0,
                "dashArray": None,
            }
        ).add_to(m)

        # Origin / Dest markers with vivid colors
        for coord, label, bg, emoji in [
            (route_data.get("origin_coords"), "Start", "#22c55e", "🟢"),
            (route_data.get("dest_coords"),   "End",   "#ef4444", "🔴"),
        ]:
            if coord:
                popup_html = f"""
<div style="background:{bg};border-radius:8px;padding:8px 12px;
            color:#fff;font-weight:700;font-size:.85rem;">
  {emoji} {label}
</div>
"""
                folium.Marker(
                    coord,
                    tooltip=f"{emoji} {label}",
                    popup=folium.Popup(popup_html, max_width=150),
                    icon=folium.DivIcon(
                        html=f'<div style="font-size:1.6rem;filter:drop-shadow(0 0 6px {bg});">{emoji}</div>',
                        icon_size=(30, 30),
                        icon_anchor=(15, 15),
                    )
                ).add_to(m)

    return m


# ─────────────────────────────────────────────────────────────────────────────
# FULL STREAMLIT PAGE — vibrant UI
# ─────────────────────────────────────────────────────────────────────────────
def render_maps_panel():
    """Primary map UI — called from app.py for maps_panel mode."""
    try:
        import folium
        from streamlit_folium import st_folium
        _has_folium = True
    except ImportError:
        _has_folium = False

    # ── Vivid gradient header ──────────────────────────────────────────────
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

/* Map panel base */
.map-panel-wrap { font-family:'Inter',sans-serif; }

/* Tile option cards */
.tile-card {
    display:inline-block;
    padding:6px 12px;
    border-radius:10px;
    font-size:.78rem;
    font-weight:700;
    letter-spacing:.5px;
    margin:3px;
    cursor:pointer;
    transition:all .2s;
}

/* Legend dots */
.legend-dot {
    display:inline-block;
    width:11px; height:11px;
    border-radius:50%;
    margin-right:6px;
    box-shadow:0 0 6px currentColor;
}

/* Route info card */
.route-card {
    background:linear-gradient(135deg,#312e81,#1e1b4b);
    border:1.5px solid #818cf8;
    border-radius:14px;
    padding:14px 16px;
    margin-top:8px;
}
</style>

<div class="map-panel-wrap">
<div style="
  background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 40%,#db2777 100%);
  border-radius:20px;
  padding:24px 28px;
  margin-bottom:18px;
  box-shadow:0 8px 32px rgba(99,102,241,0.4);
  position:relative;
  overflow:hidden;
">
  <div style="position:absolute;top:-20px;right:-20px;font-size:8rem;opacity:.08;">🗺️</div>
  <div style="font-size:1.8rem;font-weight:900;color:#fff;letter-spacing:-1px;">
    🗺️ Interactive World Map
  </div>
  <div style="color:rgba(255,255,255,0.75);font-size:.88rem;margin-top:4px;">
    ✨ Colourful markers · Route planner · AI place info · 100% free
  </div>
  <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
    <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:4px 12px;font-size:.75rem;color:#fff;">📍 Click to pin</span>
    <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:4px 12px;font-size:.75rem;color:#fff;">🛣️ OSRM routing</span>
    <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:4px 12px;font-size:.75rem;color:#fff;">🌐 Nominatim geocoding</span>
  </div>
</div>
</div>
""", unsafe_allow_html=True)

    if not _has_folium:
        st.warning(
            "📦 **Folium not installed.** Run: `pip install folium streamlit-folium`\n\n"
            "Falling back to Leaflet.js embedded map below."
        )
        _render_leaflet_fallback()
        return

    # ── Session init ───────────────────────────────────────────────────────
    if "map_markers" not in st.session_state:
        st.session_state.map_markers = []
    if "map_center" not in st.session_state:
        st.session_state.map_center = (20.5937, 78.9629)
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 5
    if "map_route" not in st.session_state:
        st.session_state.map_route = None
    if "map_tile" not in st.session_state:
        st.session_state.map_tile = "voyager"

    # ── Two-column layout ──────────────────────────────────────────────────
    col_map, col_panel = st.columns([3, 1])

    with col_panel:
        # ── Tile selector with colour previews ─────────────────────────────
        st.markdown("""
<div style="background:linear-gradient(135deg,#1e1b4b,#312e81);
border:1px solid #4338ca;border-radius:14px;padding:14px 16px;margin-bottom:10px;">
  <div style="color:#a5b4fc;font-weight:800;font-size:.9rem;margin-bottom:8px;">🎨 Map Style</div>
</div>
""", unsafe_allow_html=True)

        TILE_META = {
            "🚀 Voyager (Colourful)": ("voyager",   "#818cf8"),
            "🌑 Dark Matter":         ("dark",      "#6b7280"),
            "🗺️ Street Map":          ("standard",  "#60a5fa"),
            "🛰️ Satellite":           ("satellite", "#fbbf24"),
            "⛰️ Terrain":             ("terrain",   "#34d399"),
            "☀️ Light":               ("light",     "#f472b6"),
            "🖤 Toner":               ("toner",     "#9ca3af"),
        }
        tile_labels = list(TILE_META.keys())
        selected_tile_label = st.radio(
            "Style", tile_labels,
            key="map_tile_radio", label_visibility="collapsed",
            horizontal=False
        )
        chosen_tile, chosen_color = TILE_META[selected_tile_label]
        st.session_state.map_tile = chosen_tile

        st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;margin-top:4px;
background:rgba(99,102,241,0.1);border-radius:8px;padding:6px 10px;">
  <div style="width:12px;height:12px;border-radius:50%;background:{chosen_color};
  box-shadow:0 0 8px {chosen_color};"></div>
  <span style="color:#c7d2fe;font-size:.78rem;">Active: <b>{selected_tile_label}</b></span>
</div>
""", unsafe_allow_html=True)

        st.markdown("""<hr style="border-color:rgba(99,102,241,0.2);margin:12px 0;">""", unsafe_allow_html=True)

        # ── Search ─────────────────────────────────────────────────────────
        st.markdown("""
<div style="color:#a5b4fc;font-weight:800;font-size:.9rem;margin-bottom:6px;">🔍 Search Place</div>
""", unsafe_allow_html=True)
        search_q = st.text_input("Place name:", placeholder="e.g. Eiffel Tower, Paris",
                                 key="map_search_input", label_visibility="collapsed")
        if st.button("🔍 Search on Map", use_container_width=True, key="map_search_btn", type="primary"):
            with st.spinner(f"Finding {search_q}..."):
                lat, lng = geocode(search_q)
                if lat:
                    st.session_state.map_center = (lat, lng)
                    st.session_state.map_zoom   = 14
                    details = geocode_details(search_q)
                    st.session_state.map_markers.append({
                        "name": search_q,
                        "lat": lat, "lng": lng,
                        "desc": details.get("display_name", "")[:80],
                        "type": "search"
                    })
                    st.success(f"📍 Found: {lat:.4f}, {lng:.4f}")
                    wiki = get_wiki_summary(search_q)
                    if wiki:
                        st.info(wiki[:250] + ("..." if len(wiki) > 250 else ""))
                else:
                    st.error("❌ Place not found. Try a different name.")

        st.markdown("""<hr style="border-color:rgba(99,102,241,0.2);margin:12px 0;">""", unsafe_allow_html=True)

        # ── Route planner ──────────────────────────────────────────────────
        st.markdown("""
<div style="color:#a5b4fc;font-weight:800;font-size:.9rem;margin-bottom:6px;">🛣️ Route Planner</div>
""", unsafe_allow_html=True)
        origin = st.text_input("From:", placeholder="e.g. Chennai", key="map_origin")
        dest   = st.text_input("To:",   placeholder="e.g. Bangalore", key="map_dest")
        if st.button("🗺️ Calculate Route", use_container_width=True, key="map_route_btn", type="primary"):
            with st.spinner("Calculating route..."):
                rd = get_route(origin, dest)
                st.session_state.map_route = rd
                if rd.get("error"):
                    st.error(rd["error"])
                else:
                    olat, olng = rd["origin_coords"]
                    dlat, dlng = rd["dest_coords"]
                    st.session_state.map_center = ((olat+dlat)/2, (olng+dlng)/2)
                    st.session_state.map_zoom = 8
                    st.success(
                        f"📏 **{rd['distance_km']} km**  |  ⏱ ~**{rd['duration_min']} min**"
                    )

        if st.session_state.map_route and not st.session_state.map_route.get("error"):
            rd = st.session_state.map_route
            st.markdown(f"""
<div class="route-card">
  <div style="color:#818cf8;font-weight:800;margin-bottom:8px;">📊 Route Info</div>
  <div style="display:flex;gap:14px;flex-wrap:wrap;">
    <div style="text-align:center;">
      <div style="font-size:1.3rem;color:#22d3ee;font-weight:900;">{rd['distance_km']}</div>
      <div style="color:#94a3b8;font-size:.72rem;">km</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:1.3rem;color:#f472b6;font-weight:900;">{rd['duration_min']}</div>
      <div style="color:#94a3b8;font-size:.72rem;">min drive</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
            if st.button("❌ Clear Route", key="map_clear_route", use_container_width=True):
                st.session_state.map_route = None
                st.rerun()

        st.markdown("""<hr style="border-color:rgba(99,102,241,0.2);margin:12px 0;">""", unsafe_allow_html=True)

        # ── Quick Layers ───────────────────────────────────────────────────
        st.markdown("""
<div style="color:#a5b4fc;font-weight:800;font-size:.9rem;margin-bottom:6px;">📌 Quick Layers</div>
""", unsafe_allow_html=True)
        if st.button("🏫 VIT Campus", use_container_width=True, key="map_vit"):
            st.session_state.map_markers = [l for g in VIT_CHENNAI_LOCATIONS.values() for l in g]
            st.session_state.map_center = (12.8410, 80.1530)
            st.session_state.map_zoom = 17
            st.rerun()
        if st.button("🇮🇳 India Travel", use_container_width=True, key="map_india"):
            st.session_state.map_markers = [l for g in INDIA_DESTINATIONS.values() for l in g]
            st.session_state.map_center = (20.5937, 78.9629)
            st.session_state.map_zoom = 5
            st.rerun()
        if st.button("🗑️ Clear All Markers", use_container_width=True, key="map_clear"):
            st.session_state.map_markers = []
            st.session_state.map_zoom = 5
            st.session_state.map_center = (20.5937, 78.9629)
            st.rerun()

        # Marker count badge
        n = len(st.session_state.map_markers)
        badge_color = "#22d3ee" if n > 0 else "#6b7280"
        st.markdown(f"""
<div style="text-align:center;margin-top:8px;">
  <span style="background:{badge_color}22;border:1px solid {badge_color};color:{badge_color};
  border-radius:20px;padding:4px 14px;font-size:.78rem;font-weight:700;">
    📍 {n} marker{"s" if n != 1 else ""}
  </span>
</div>
""", unsafe_allow_html=True)

        st.markdown("""<hr style="border-color:rgba(99,102,241,0.2);margin:12px 0;">""", unsafe_allow_html=True)

        # ── Colour Legend ──────────────────────────────────────────────────
        st.markdown("""
<div style="color:#a5b4fc;font-weight:800;font-size:.9rem;margin-bottom:8px;">🎨 Marker Legend</div>
""", unsafe_allow_html=True)
        legend_items = [
            ("academic", "Academic"),
            ("hostel",   "Hostel"),
            ("food",     "Food"),
            ("sports",   "Sports"),
            ("library",  "Library"),
            ("lab",      "Lab"),
            ("health",   "Health"),
            ("search",   "Search Pin"),
            ("custom",   "Custom Pin"),
        ]
        legend_html = "<div style='display:flex;flex-wrap:wrap;gap:5px;'>"
        for ltype, lname in legend_items:
            c = TYPE_COLORS.get(ltype, "#a78bfa")
            icon = TYPE_ICONS.get(ltype, "📍")
            legend_html += f"""
<div style="background:{c}1a;border:1px solid {c};border-radius:8px;
padding:3px 8px;font-size:.72rem;color:{c};font-weight:700;white-space:nowrap;">
  {icon} {lname}
</div>"""
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

        st.markdown("""<hr style="border-color:rgba(99,102,241,0.2);margin:12px 0;">""", unsafe_allow_html=True)

        # ── AI Place Info ──────────────────────────────────────────────────
        st.markdown("""
<div style="color:#a5b4fc;font-weight:800;font-size:.9rem;margin-bottom:6px;">🤖 AI Place Info</div>
""", unsafe_allow_html=True)
        ai_place = st.text_input("Ask about a place:", placeholder="Paris, France",
                                 key="map_ai_place", label_visibility="collapsed")
        if st.button("✨ Tell Me About It", use_container_width=True, key="map_ai_btn"):
            with st.spinner(f"AI researching {ai_place}..."):
                info = ai_place_info(ai_place)
            st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e1b4b,#312e81);
border:1px solid #818cf8;border-radius:12px;padding:14px;
color:#e0e7ff;font-size:.82rem;line-height:1.6;margin-top:8px;">
{info}
</div>""", unsafe_allow_html=True)

    with col_map:
        # Build and display map
        m = _build_folium_map(
            center_lat=st.session_state.map_center[0],
            center_lng=st.session_state.map_center[1],
            zoom=st.session_state.map_zoom,
            tile_layer=st.session_state.map_tile,
            markers=st.session_state.map_markers,
            route_data=st.session_state.map_route,
        )
        map_data = st_folium(m, use_container_width=True, height=620, key="main_map")

        # Handle map clicks to add markers
        if map_data and map_data.get("last_clicked"):
            clk = map_data["last_clicked"]
            lat, lng = clk.get("lat"), clk.get("lng")
            if lat and lng:
                existing = st.session_state.map_markers
                if not existing or (existing[-1]["lat"] != lat or existing[-1]["lng"] != lng):
                    if len(existing) < 20:
                        st.session_state.map_markers.append({
                            "name": f"Pin #{len(existing)+1}",
                            "lat": lat, "lng": lng,
                            "desc": f"Custom pin at {lat:.4f}, {lng:.4f}",
                            "type": "custom"
                        })

        # Export map
        try:
            import io
            html_buf = io.BytesIO()
            m.save(html_buf, close_file=False)
            st.download_button(
                "💾 Export Map as HTML",
                data=html_buf.getvalue(),
                file_name="examhelp_map.html",
                mime="text/html",
                use_container_width=True,
                key="map_export"
            )
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# COLORFUL LEAFLET FALLBACK (no folium needed)
# ─────────────────────────────────────────────────────────────────────────────
_LEAFLET_TYPE_COLORS = {
    "academic": "#38bdf8", "hostel": "#c084fc", "food": "#4ade80",
    "sports": "#fb923c", "library": "#f472b6", "lab": "#22d3ee",
    "health": "#f87171", "finance": "#facc15", "search": "#a78bfa",
    "custom": "#34d399",
}

def _render_leaflet_fallback():
    """Colorful Leaflet.js fallback when folium not installed."""
    all_locs = [l for g in INDIA_DESTINATIONS.values() for l in g]
    markers_js = ""
    for loc in all_locs:
        lat, lng = loc["lat"], loc["lng"]
        name = loc.get("name", "").replace("'", "\\'")
        desc = loc.get("desc", "").replace("'", "\\'")
        color = _LEAFLET_TYPE_COLORS.get(loc.get("type", ""), "#a78bfa")
        markers_js += f"""
var mk_{int(lat*10000)}_{int(lng*10000)} = L.circleMarker([{lat},{lng}],{{
  radius:9, color:'{color}', fillColor:'{color}', fillOpacity:.9, weight:2
}}).addTo(map);
mk_{int(lat*10000)}_{int(lng*10000)}.bindPopup(
  '<div style="background:linear-gradient(135deg,#1e1b4b,#312e81);' +
  'border:2px solid {color};border-radius:12px;padding:12px;color:#e0e7ff;">' +
  '<b style="color:{color}">{name}</b><br><small>{desc}</small></div>'
);
mk_{int(lat*10000)}_{int(lng*10000)}.bindTooltip('<b>{name}</b>');
"""
    html = f"""
<div id="lmap" style="height:560px;width:100%;border-radius:16px;overflow:hidden;
box-shadow:0 8px 32px rgba(99,102,241,0.35);"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('lmap').setView([20.5937,78.9629],5);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',
{{attribution:'© OSM | CartoDB',maxZoom:19}}).addTo(map);
{markers_js}
</script>
"""
    st.components.v1.html(html, height=580)


# ─────────────────────────────────────────────────────────────────────────────
# BACKWARD COMPAT — original leaflet functions still exported
# ─────────────────────────────────────────────────────────────────────────────
def get_leaflet_map_html(locations, center_lat=20.5937, center_lng=78.9629,
                         zoom=5, height="500px", title="Map") -> str:
    markers_js = ""
    for i, loc in enumerate(locations):
        lat = loc.get("lat", 0); lng = loc.get("lng", 0)
        name = loc.get("name", "").replace("'", "\\'")
        desc = loc.get("desc", "").replace("'", "\\'")
        color = TYPE_COLORS.get(loc.get("type", ""), "#a78bfa")
        safe_id = f"m{i}_{int(lat*1000)}_{int(lng*1000)}"
        markers_js += f"""
var {safe_id} = L.circleMarker([{lat},{lng}],{{radius:9,color:'{color}',fillColor:'{color}',
fillOpacity:.9,weight:2}}).addTo(map);
{safe_id}.bindPopup('<div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border:2px solid {color};border-radius:12px;padding:12px;color:#e0e7ff;"><b style="color:{color}">{name}</b><br><small>{desc}</small></div>');
{safe_id}.bindTooltip('<b>{name}</b>');
"""
    uid = abs(hash(title)) % 100000
    return f"""
<div id="map_{uid}" style="height:{height};width:100%;border-radius:14px;overflow:hidden;
box-shadow:0 6px 24px rgba(99,102,241,0.3);"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map=L.map('map_{uid}').setView([{center_lat},{center_lng}],{zoom});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',
{{attribution:'© OSM | CartoDB',maxZoom:19}}).addTo(map);
{markers_js}
</script>
"""


def get_vit_campus_map(height="500px") -> str:
    locs = [l for g in VIT_CHENNAI_LOCATIONS.values() for l in g]
    return get_leaflet_map_html(locs, 12.8410, 80.1530, 17, height, "VIT Chennai")


def get_india_travel_map(region=None, height="550px") -> str:
    src = INDIA_DESTINATIONS if region is None else {region: INDIA_DESTINATIONS.get(region, [])}
    locs = [l for g in src.values() for l in g]
    return get_leaflet_map_html(locs, 20.5937, 78.9629, 5, height, "India Travel")
