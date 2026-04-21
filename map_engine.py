"""
map_engine.py — Enhanced Map Engine v2.0 (ExamHelp AI)
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

TYPE_COLORS = {
    "academic": "#4f8ef7", "hostel": "#7c6af7", "food": "#48c78e",
    "sports": "#f7a04f", "library": "#c8b8ff", "lab": "#4ff7e8",
    "health": "#f74f4f", "finance": "#f7e44f",
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
# NEW: FREE GEOCODING (Nominatim/OpenStreetMap)
# ─────────────────────────────────────────────────────────────────────────────
_NOM_HEADERS = {"User-Agent": "ExamHelpAI/2.0 (examhelp@ai.com)"}

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
# NEW: FREE ROUTING (OSRM)
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
# NEW: WIKIPEDIA PLACE SUMMARY
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
# NEW: AI PLACE INFO
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
# FOLIUM MAP BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def _build_folium_map(
    center_lat: float = 20.5937,
    center_lng: float = 78.9629,
    zoom: int = 5,
    tile_layer: str = "dark",
    markers: List[Dict] = None,
    route_data: dict = None,
) -> "folium.Map":
    import folium

    TILES = {
        "dark":           ("CartoDB dark_matter", None),
        "standard":       ("OpenStreetMap", None),
        "satellite":      ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                           "Esri World Imagery"),
        "light":          ("CartoDB positron", None),
    }

    tile_url, attr = TILES.get(tile_layer, TILES["dark"])
    if attr:
        m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom,
                       tiles=None)
        folium.TileLayer(tile_url, name=tile_layer.title(), attr=attr).add_to(m)
    else:
        m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom,
                       tiles=tile_url)

    # Add markers
    if markers:
        for mk in markers:
            lat, lng = mk.get("lat"), mk.get("lng")
            if lat is None or lng is None:
                continue
            color = TYPE_COLORS.get(mk.get("type", ""), "#6366f1")
            popup_html = (
                f"<b style='color:#1e293b'>{mk.get('name','')}</b><br>"
                f"<small>{mk.get('desc','')}</small>"
            )
            folium.CircleMarker(
                location=[lat, lng],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=mk.get("name", ""),
            ).add_to(m)

    # Draw route
    if route_data and not route_data.get("error"):
        folium.GeoJson(
            route_data["geojson"],
            style_function=lambda x: {
                "color": "#6366f1", "weight": 5, "opacity": 0.8
            }
        ).add_to(m)
        # Origin / Dest markers
        for coord, label, color in [
            (route_data.get("origin_coords"), "🟢 Start", "green"),
            (route_data.get("dest_coords"),   "🔴 End",   "red"),
        ]:
            if coord:
                folium.Marker(
                    coord, tooltip=label,
                    icon=folium.Icon(color=color, icon="circle")
                ).add_to(m)

    return m


# ─────────────────────────────────────────────────────────────────────────────
# FULL STREAMLIT PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_maps_panel():
    """Primary map UI — called from app.py for maps_panel mode."""
    # Try folium import
    try:
        import folium
        from streamlit_folium import st_folium
        _has_folium = True
    except ImportError:
        _has_folium = False

    # Header
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(16,185,129,0.05));
border:1px solid rgba(99,102,241,0.15);border-radius:20px;padding:22px 28px;margin-bottom:16px;">
  <div style="font-size:1.6rem;font-weight:900;color:#fff;">🗺️ Interactive Map</div>
  <div style="color:rgba(255,255,255,0.4);font-size:.85rem;">
    Search · Route Planner · AI Place Info · No API key needed
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
        st.session_state.map_tile = "dark"

    # ── Two-column layout ──────────────────────────────────────────────────
    col_map, col_panel = st.columns([3, 1])

    with col_panel:
        # Tile selector
        st.markdown("#### 🗂️ Map Style")
        tile_options = {"🌑 Dark": "dark", "🗺️ Standard": "standard",
                        "🛰️ Satellite": "satellite", "☀️ Light": "light"}
        selected_tile_label = st.radio(
            "Style", list(tile_options.keys()),
            key="map_tile_radio", label_visibility="collapsed", horizontal=False
        )
        st.session_state.map_tile = tile_options[selected_tile_label]

        st.markdown("---")

        # Search
        st.markdown("#### 🔍 Search Place")
        search_q = st.text_input("Place name:", placeholder="e.g. Eiffel Tower",
                                 key="map_search_input", label_visibility="collapsed")
        if st.button("🔍 Search", use_container_width=True, key="map_search_btn"):
            with st.spinner(f"Finding {search_q}..."):
                lat, lng = geocode(search_q)
                if lat:
                    st.session_state.map_center = (lat, lng)
                    st.session_state.map_zoom   = 14
                    # Add marker
                    details = geocode_details(search_q)
                    st.session_state.map_markers.append({
                        "name": search_q,
                        "lat": lat, "lng": lng,
                        "desc": details.get("display_name", "")[:80],
                        "type": "search"
                    })
                    st.success(f"📍 Found: {lat:.4f}, {lng:.4f}")
                    # Wiki snippet
                    wiki = get_wiki_summary(search_q)
                    if wiki:
                        st.info(wiki[:250] + ("..." if len(wiki) > 250 else ""))
                else:
                    st.error("Place not found.")

        st.markdown("---")

        # Route planner
        st.markdown("#### 🛣️ Route Planner")
        origin = st.text_input("From:", placeholder="Chennai", key="map_origin")
        dest   = st.text_input("To:",   placeholder="Bangalore", key="map_dest")
        if st.button("🗺️ Get Route", use_container_width=True, key="map_route_btn", type="primary"):
            with st.spinner("Calculating route..."):
                rd = get_route(origin, dest)
                st.session_state.map_route = rd
                if rd.get("error"):
                    st.error(rd["error"])
                else:
                    # Center on midpoint
                    olat, olng = rd["origin_coords"]
                    dlat, dlng = rd["dest_coords"]
                    st.session_state.map_center = ((olat+dlat)/2, (olng+dlng)/2)
                    st.session_state.map_zoom = 8
                    st.success(
                        f"📏 Distance: **{rd['distance_km']} km**  \n"
                        f"⏱ ETA: **~{rd['duration_min']} min** driving"
                    )

        if st.session_state.map_route and not st.session_state.map_route.get("error"):
            rd = st.session_state.map_route
            st.markdown(f"""
<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
border-radius:10px;padding:12px;">
  <div style="color:#a5b4fc;font-weight:700;">Route Info</div>
  <div style="color:#f8fafc;">📏 {rd['distance_km']} km</div>
  <div style="color:#f8fafc;">⏱ ~{rd['duration_min']} min</div>
</div>
""", unsafe_allow_html=True)
            if st.button("❌ Clear Route", key="map_clear_route"):
                st.session_state.map_route = None
                st.rerun()

        st.markdown("---")

        # Preset layers
        st.markdown("#### 📌 Quick Layers")
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
        if st.button("🗑 Clear Markers", use_container_width=True, key="map_clear"):
            st.session_state.map_markers = []
            st.session_state.map_zoom = 5
            st.session_state.map_center = (20.5937, 78.9629)
            st.rerun()

        st.caption(f"Markers: {len(st.session_state.map_markers)}")

        st.markdown("---")

        # AI Place Info
        st.markdown("#### 🤖 AI Place Info")
        ai_place = st.text_input("Ask about a place:", placeholder="Paris, France",
                                 key="map_ai_place", label_visibility="collapsed")
        if st.button("✨ Tell Me About It", use_container_width=True, key="map_ai_btn"):
            with st.spinner(f"AI researching {ai_place}..."):
                info = ai_place_info(ai_place)
            st.markdown(info)

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
        map_data = st_folium(m, use_container_width=True, height=600, key="main_map")

        # Handle map clicks to add markers
        if map_data and map_data.get("last_clicked"):
            clk = map_data["last_clicked"]
            lat, lng = clk.get("lat"), clk.get("lng")
            if lat and lng:
                # Only add if not already the last marker
                existing = st.session_state.map_markers
                if not existing or (existing[-1]["lat"] != lat or existing[-1]["lng"] != lng):
                    if len(existing) < 10:
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
                file_name="map_export.html",
                mime="text/html",
                use_container_width=True,
                key="map_export"
            )
        except Exception:
            pass


def _render_leaflet_fallback():
    """Leaflet.js fallback when folium not installed."""
    all_locs = [l for g in INDIA_DESTINATIONS.values() for l in g]
    markers_js = ""
    for loc in all_locs:
        lat, lng = loc["lat"], loc["lng"]
        name = loc.get("name", "").replace("'", "\\'")
        desc = loc.get("desc", "").replace("'", "\\'")
        markers_js += f"""
L.circleMarker([{lat},{lng}],{{radius:8,color:'#6366f1',fillColor:'#6366f1',
fillOpacity:.85,weight:2}}).addTo(map).bindPopup('<b>{name}</b><br>{desc}');
"""
    html = f"""
<div id="lmap" style="height:500px;width:100%;border-radius:12px;overflow:hidden;"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('lmap').setView([20.5937,78.9629],5);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
{{attribution:'© OSM',maxZoom:19}}).addTo(map);
{markers_js}
</script>
"""
    st.components.v1.html(html, height=520)


# ─────────────────────────────────────────────────────────────────────────────
# BACKWARD COMPAT — original leaflet functions still exported
# ─────────────────────────────────────────────────────────────────────────────
def get_leaflet_map_html(locations, center_lat=20.5937, center_lng=78.9629,
                         zoom=5, height="500px", title="Map") -> str:
    markers_js = ""
    for loc in locations:
        lat = loc.get("lat", 0); lng = loc.get("lng", 0)
        name = loc.get("name", "").replace("'", "\\'")
        desc = loc.get("desc", "").replace("'", "\\'")
        color = TYPE_COLORS.get(loc.get("type", ""), "#7c6af7")
        markers_js += f"""
L.circleMarker([{lat},{lng}],{{radius:8,color:'{color}',fillColor:'{color}',
fillOpacity:.85,weight:2}}).addTo(map).bindPopup('<b>{name}</b><br>{desc}');
"""
    uid = hash(title) % 100000
    return f"""
<div id="map_{uid}" style="height:{height};width:100%;border-radius:12px;overflow:hidden;"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map=L.map('map_{uid}').setView([{center_lat},{center_lng}],{zoom});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
{{attribution:'© OSM',maxZoom:19}}).addTo(map);
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
