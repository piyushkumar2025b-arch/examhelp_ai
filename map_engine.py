"""
map_engine.py — Advanced Interactive Mapping Engine
Leaflet.js-based interactive maps, Geocoding (Nominatim), and Routing (OSRM).
All mapping uses free OpenStreetMap-based services.
"""
from __future__ import annotations
import math
import requests
import streamlit as st
from typing import Dict, List, Optional, Tuple

# ── PRESET DATA ─────────────────────────────────────────────

VIT_CHENNAI_LOCATIONS = {
    "🏫 Academic Blocks": [
        {"name": "Technology Tower (TT)", "lat": 12.8406, "lng": 80.1534, "desc": "Main academic building, core labs & admin", "type": "academic"},
        {"name": "Netaji Subhash Chandra Bose Block", "lat": 12.8415, "lng": 80.1538, "desc": "Administrative & Academic block", "type": "academic"},
        {"name": "Mechanical Block",       "lat": 12.8412, "lng": 80.1540, "desc": "Design and manufacturing labs", "type": "academic"},
        {"name": "Civil Block",            "lat": 12.8404, "lng": 80.1545, "desc": "Structural engineering & surveying", "type": "academic"},
        {"name": "MBA Block",              "lat": 12.8400, "lng": 80.1520, "desc": "VBS - VIT Business School", "type": "academic"},
        {"name": "Anna Auditorium",        "lat": 12.8408, "lng": 80.1528, "desc": "Seating capacity 2500+", "type": "academic"},
        {"name": "Knowledge Resource Centre (Library)", "lat": 12.8403, "lng": 80.1530, "desc": "5 Floors of books & digital resources", "type": "academic"},
    ],
    "🏠 Hostels & Residential": [
        {"name": "MH1 - Men's Hostel A",  "lat": 12.8398, "lng": 80.1510, "desc": "Standard men's block", "type": "hostel"},
        {"name": "MH2 - Men's Hostel B",  "lat": 12.8395, "lng": 80.1505, "desc": "Modern men's block", "type": "hostel"},
        {"name": "MH3 - Men's Hostel C",  "lat": 12.8392, "lng": 80.1500, "desc": "Premium men's residences", "type": "hostel"},
        {"name": "LH1 - Ladies Hostel A", "lat": 12.8430, "lng": 80.1525, "desc": "Primary ladies residence", "type": "hostel"},
        {"name": "LH2 - Ladies Hostel B", "lat": 12.8435, "lng": 80.1520, "desc": "New ladies residence", "type": "hostel"},
    ],
    "🍽️ Food & Lifestyle": [
        {"name": "Central Cafeteria",      "lat": 12.8410, "lng": 80.1522, "desc": "Multi-cuisine dining hall", "type": "food"},
        {"name": "Gazebo",                "lat": 12.8405, "lng": 80.1525, "desc": "Popular outdoor hang-out spot", "type": "food"},
        {"name": "Bypass Cafe",           "lat": 12.8420, "lng": 80.1530, "desc": "Quick snacks and coffee", "type": "food"},
        {"name": "Health Centre",          "lat": 12.8402, "lng": 80.1535, "desc": "24/7 Medical assistance", "type": "health"},
    ],
    "🏀 Sports & Fitness": [
        {"name": "Main Ground",           "lat": 12.8385, "lng": 80.1540, "desc": "Cricket/Football field", "type": "sports"},
        {"name": "Basketball Courts",     "lat": 12.8390, "lng": 80.1530, "desc": "Outdoor floodlit courts", "type": "sports"},
        {"name": "Indoor Stadium",        "lat": 12.8425, "lng": 80.1545, "desc": "Badminton, TT, Squash", "type": "sports"},
        {"name": "Tennis Courts",         "lat": 12.8428, "lng": 80.1550, "desc": "Professional grade courts", "type": "sports"},
    ],
    "🎭 Campus Lifestyle": [
        {"name": "Amphitheatre",          "lat": 12.8407, "lng": 80.1532, "desc": "Cultural performance hub", "type": "lifestyle"},
        {"name": "Open Air Theatre (OAT)", "lat": 12.8422, "lng": 80.1542, "desc": "Major events & screenings", "type": "lifestyle"},
        {"name": "Rock Plaza",             "lat": 12.8412, "lng": 80.1528, "desc": "Social meet-up zone", "type": "lifestyle"},
    ],
    "🚪 Access Points": [
        {"name": "Main Gate",             "lat": 12.8375, "lng": 80.1550, "desc": "Primary entrance (Gate 1)", "type": "gate"},
        {"name": "Back Gate",             "lat": 12.8440, "lng": 80.1515, "desc": "Service and student exit", "type": "gate"},
    ],
}

INDIA_PRESETS = {
    "🏛️ Wonders & History": [
        {"name": "Taj Mahal", "lat": 27.1751, "lng": 78.0421, "desc": "Symbol of Love, Agra", "type": "wonder"},
        {"name": "Hampi",     "lat": 15.3350, "lng": 76.4600, "desc": "Vijayanagara Ruins, Karnataka", "type": "wonder"},
        {"name": "Ajanta Caves", "lat": 20.5519, "lng": 75.7033, "desc": "Ancient Rock-cut caves, Maharashtra", "type": "wonder"},
    ],
    "🏖️ Coastal & Scenic": [
        {"name": "Marina Beach", "lat": 13.0418, "lng": 80.2824, "desc": "Longest beach in India, Chennai", "type": "beach"},
        {"name": "Goa (Baga)",    "lat": 15.5553, "lng": 73.7517, "desc": "Beach paradise", "type": "beach"},
        {"name": "Varkala Cliff","lat": 8.7337,  "lng": 76.7059, "desc": "Stunning Kerala coastline", "type": "beach"},
    ],
    "🏔️ Hill Stations": [
        {"name": "Ooty",      "lat": 11.4102, "lng": 76.6950, "desc": "Queen of Hill Stations, Tamil Nadu", "type": "nature"},
        {"name": "Manali",    "lat": 32.2432, "lng": 77.1892, "desc": "Adventure Hub, Himachal", "type": "nature"},
        {"name": "Munnar",    "lat": 10.0889, "lng": 77.0595, "desc": "Tea Gardens, Kerala", "type": "nature"},
    ],
    "🚆 Transport Hubs (Chennai)": [
        {"name": "Chennai International Airport", "lat": 12.9941, "lng": 80.1709, "desc": "Main air gateway (MAA)", "type": "transport"},
        {"name": "Chennai Central Railway Station", "lat": 13.0827, "lng": 80.2707, "desc": "Major rail hub", "type": "transport"},
        {"name": "Vandalur Zoo (CMBT Hub)", "lat": 12.8788, "lng": 80.0817, "desc": "Nearest major bus hub", "type": "transport"},
        {"name": "Kelambakkam Junction", "lat": 12.7845, "lng": 80.2220, "desc": "Local transit junction", "type": "transport"},
    ],
    "💻 Tech Hubs": [
        {"name": "Bangalore - Electronic City", "lat": 12.8448, "lng": 77.6632, "desc": "Silicon Valley of India", "type": "tech"},
        {"name": "Hyderabad - HITEC City",     "lat": 17.4435, "lng": 78.3772, "desc": "Cyberabad IT corridor", "type": "tech"},
    ],
}

MAP_THEMES = {
    "Standard": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "Dark Mode (Premium)": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    "Light Mode (Sleek)": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    "Terrain": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
}

# ── GEOCODING & ROUTING (FREE APIs) ──────────────────────────

def geocode_address(query: str) -> Optional[Dict]:
    """Search for a location using OSM Nominatim."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 1}
        headers = {"User-Agent": "ExamHelpAI/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.json():
            data = resp.json()[0]
            return {
                "name": data.get("display_name"),
                "lat": float(data.get("lat")),
                "lng": float(data.get("lon")),
                "desc": f"Found via Search: {query}"
            }
    except Exception as e:
        st.error(f"Geocoding error: {e}")
    return None

def get_route(start: Tuple[float, float], end: Tuple[float, float]) -> Optional[Dict]:
    """Fetch routing data from OSRM."""
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
        params = {"overview": "full", "geometries": "geojson", "steps": "true"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

# ── MAP GENERATORS ───────────────────────────────────────────

def get_leaflet_map_html(
    locations: List[Dict],
    center_lat: float = 20.5937,
    center_lng: float = 78.9629,
    zoom: int = 5,
    height: str = "550px",
    theme_url: str = MAP_THEMES["Dark Mode (Premium)"],
    route_geojson: Optional[Dict] = None,
) -> str:
    """Generate a self-contained premium Leaflet.js map."""
    map_id = f"map_{abs(hash(str(locations) + str(center_lat) + str(zoom)))}"
    
    markers_js = ""
    for loc in locations:
        lat, lng = loc.get("lat", 0), loc.get("lng", 0)
        name = loc.get("name", "Pin").replace("'", "\\'")
        desc = loc.get("desc", "").replace("'", "\\'")
        markers_js += f"""
        L.marker([{lat}, {lng}]).addTo(map).bindPopup('<b>{name}</b><br><small>{desc}</small>');
        """

    route_js = ""
    if route_geojson:
        import json
        route_str = json.dumps(route_geojson)
        route_js = f"""
        var routeData = {route_str};
        L.geoJSON(routeData, {{
            style: {{ color: '#00f2ff', weight: 5, opacity: 0.75 }}
        }}).addTo(map);
        map.fitBounds(L.geoJSON(routeData).getBounds());
        """

    return f"""
<div id="{map_id}" style="height:{height};width:100%;border-radius:18px;overflow:hidden;box-shadow: 0 10px 30px rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('{map_id}', {{
        zoomControl: true,
        scrollWheelZoom: true
    }}).setView([{center_lat}, {center_lng}], {zoom});
    
    L.tileLayer('{theme_url}', {{
        attribution: '© OpenStreetMap | © CARTO',
        maxZoom: 20
    }}).addTo(map);
    
    {markers_js}
    {route_js}
</script>
"""

# ── UI COMPONENTS ───────────────────────────────────────────

def render_advanced_map():
    """Main UI module for the maps feature."""
    st.markdown("""
<div style="background:linear-gradient(90deg, #1e1b4b, #312e81); padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);">
  <h2 style="margin:0; color:white; font-size: 1.8rem; letter-spacing: -0.02em;">🗺️ Voyager Map Studio</h2>
  <p style="margin:5px 0 0; color:rgba(255,255,255,0.7); font-size: 0.9rem;">Elite Geospatial Intelligence · Campus Navigation · India Explorer</p>
</div>""", unsafe_allow_html=True)
    
    selected_tab = st.sidebar.radio("Navigation Perspective", ["🏫 VIT Campus", "🇮🇳 Explore India", "🔍 Global Search", "🚀 Path Finder"], key="map_view_selector")

    if selected_tab == "🏫 VIT Campus":
        st.subheader("VIT Chennai Interactive Guard")
        all_locs = []
        for group_name, loc_list in VIT_CHENNAI_LOCATIONS.items():
            all_locs.extend(loc_list)
        
        c1, c2 = st.columns([3, 1])
        with c2:
            st.markdown("### Filter")
            categories = list(VIT_CHENNAI_LOCATIONS.keys())
            sel_cat = st.multiselect("Category", categories, default=categories[:2])
            theme_vit = st.selectbox("Style", list(MAP_THEMES.keys()), index=1)
            
            filtered_locs = []
            if sel_cat:
                for cat in sel_cat:
                    filtered_locs.extend(VIT_CHENNAI_LOCATIONS[cat])
            else:
                filtered_locs = all_locs

        with c1:
            html = get_leaflet_map_html(
                filtered_locs,
                center_lat=12.8410, center_lng=80.1530,
                zoom=17, height="580px",
                theme_url=MAP_THEMES[theme_vit]
            )
            st.components.v1.html(html, height=600)
            
        st.markdown("---")
        st.markdown("### 🏛️ Campus Directory")
        for cat, items in VIT_CHENNAI_LOCATIONS.items():
            with st.expander(cat):
                for item in items:
                    st.write(f"**{item['name']}** — {item['desc']}")

    elif selected_tab == "🇮🇳 Explore India":
        st.subheader("Discover the Indian Subcontinent")
        all_india = []
        for group in INDIA_PRESETS.values():
            all_india.extend(group)

        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown("### Destinations")
            india_cat = st.selectbox("Category", list(INDIA_PRESETS.keys()))
            theme_india = st.selectbox("Map Style", list(MAP_THEMES.keys()), index=3)
            
            dest_list = INDIA_PRESETS[india_cat]
            selected_dest = st.selectbox("Select Spot", [d['name'] for d in dest_list])
            
            dest_data = next(d for d in dest_list if d['name'] == selected_dest)
            st.info(f"📍 **{dest_data['name']}**\n\n{dest_data['desc']}")
            
        with c2:
            html = get_leaflet_map_html(
                [dest_data],
                center_lat=dest_data['lat'], center_lng=dest_data['lng'],
                zoom=12, height="580px",
                theme_url=MAP_THEMES[theme_india]
            )
            st.components.v1.html(html, height=600)

    elif selected_tab == "🔍 Global Search":
        st.subheader("Search Any Location")
        col1, col2 = st.columns([3, 1])
        with col1:
            q = st.text_input("Coordinates or Name", placeholder="e.g. Statue of Liberty, Tokyo, 12.84, 80.15", key="map_glb_q")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            search_btn = st.button("Locate", use_container_width=True)
            
        theme = st.selectbox("Atmosphere", list(MAP_THEMES.keys()), index=1)
        
        if q and search_btn:
            with st.spinner("Analyzing world coordinates..."):
                result = geocode_address(q)
                if result:
                    st.success(f"Confirmed: {result['name']}")
                    html = get_leaflet_map_html([result], center_lat=result['lat'], center_lng=result['lng'], zoom=15, theme_url=MAP_THEMES[theme])
                    st.components.v1.html(html, height=560)
                else:
                    st.error("Target missing. Verify location name.")
        else:
            html = get_leaflet_map_html([], theme_url=MAP_THEMES[theme])
            st.components.v1.html(html, height=560)

    elif selected_tab == "🚀 Path Finder":
        st.subheader("Intelligence Path Mapping")
        st.markdown("Optimize travel routes with AI-assisted geocoding.")
        c1, c2 = st.columns(2)
        with c1: start_q = st.text_input("Origin Point", "VIT Chennai Gate 1")
        with c2: end_q = st.text_input("Destination Point", "Technology Tower VIT")
            
        if st.button("Calculate Vector 🚀", use_container_width=True):
            with st.spinner("Plotting trajectory..."):
                s_res = geocode_address(start_q) if "VIT" not in start_q else {"lat":12.8375,"lng":80.1550,"name":"Campus Gate 1"}
                e_res = geocode_address(end_q) if "Technology Tower" not in end_q else {"lat":12.8406,"lng":80.1534,"name":"Technology Tower"}
                
                if s_res and e_res:
                    route_data = get_route((s_res['lat'], s_res['lng']), (e_res['lat'], e_res['lng']))
                    if route_data and 'routes' in route_data:
                        geometry = route_data['routes'][0]['geometry']
                        distance = route_data['routes'][0]['distance'] / 1000
                        duration = route_data['routes'][0]['duration'] / 3600
                        
                        st.success(f"✅ Route Optimized: **{distance:.2f} km** | ETA: **{duration:.1f} hours**")
                        html = get_leaflet_map_html([s_res, e_res], route_geojson=geometry, theme_url=MAP_THEMES["Dark Mode (Premium)"])
                        st.components.v1.html(html, height=580)
                    else: st.error("Route calculation failed.")
                else: st.error("Coordinate lookup failed.")

    if st.button("💬 Back to Intelligence Hub", use_container_width=True):
        st.session_state.app_mode = "chat"; st.rerun()
