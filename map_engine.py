"""
map_engine.py — VIT Chennai Campus Map + India Trip Planner
Leaflet.js-based interactive map (no external API keys needed).
All mapping uses free OpenStreetMap / Leaflet.js only.
"""
from __future__ import annotations
import math
from typing import Dict, List, Optional

# Google Maps Embed removed — using Leaflet.js (OpenStreetMap) for all maps

VIT_CHENNAI_LOCATIONS = {
    "🏫 Academic Buildings": [
        {"name": "Technology Tower (TT)", "lat": 12.8406, "lng": 80.1534, "desc": "Main academic building with modern labs", "type": "academic"},
        {"name": "Anna Auditorium",        "lat": 12.8408, "lng": 80.1528, "desc": "Main auditorium for events & convocation", "type": "academic"},
        {"name": "Mechanical Block",       "lat": 12.8412, "lng": 80.1540, "desc": "Mechanical Engineering labs", "type": "academic"},
        {"name": "Civil Block",            "lat": 12.8404, "lng": 80.1545, "desc": "Civil & Structural Engineering", "type": "academic"},
        {"name": "Chemistry Block",        "lat": 12.8415, "lng": 80.1530, "desc": "Chemistry labs and lecture halls", "type": "academic"},
        {"name": "Physics Block",          "lat": 12.8418, "lng": 80.1535, "desc": "Physics labs and research center", "type": "academic"},
        {"name": "MBA Block",              "lat": 12.8400, "lng": 80.1520, "desc": "School of Business, MBA programs", "type": "academic"},
        {"name": "Architecture Block",     "lat": 12.8422, "lng": 80.1542, "desc": "School of Architecture", "type": "academic"},
    ],
    "🏠 Hostels": [
        {"name": "MH1 - Men's Hostel 1",  "lat": 12.8398, "lng": 80.1510, "desc": "Men's residential block", "type": "hostel"},
        {"name": "MH2 - Men's Hostel 2",  "lat": 12.8395, "lng": 80.1515, "desc": "Men's residential block", "type": "hostel"},
        {"name": "LH1 - Ladies Hostel 1", "lat": 12.8430, "lng": 80.1525, "desc": "Women's residential block", "type": "hostel"},
        {"name": "LH2 - Ladies Hostel 2", "lat": 12.8432, "lng": 80.1528, "desc": "Women's residential block", "type": "hostel"},
        {"name": "LH3 - Ladies Hostel 3", "lat": 12.8435, "lng": 80.1530, "desc": "Women's residential block", "type": "hostel"},
    ],
    "🍽️ Food & Essentials": [
        {"name": "Central Cafeteria",      "lat": 12.8410, "lng": 80.1522, "desc": "Main dining hall", "type": "food"},
        {"name": "Juice & Snack Corner",   "lat": 12.8407, "lng": 80.1518, "desc": "Quick bites & beverages", "type": "food"},
        {"name": "Medical Centre",         "lat": 12.8402, "lng": 80.1535, "desc": "Campus health centre", "type": "health"},
        {"name": "ATM / Bank",             "lat": 12.8405, "lng": 80.1527, "desc": "ATM & banking services", "type": "finance"},
    ],
    "🏋️ Sports & Recreation": [
        {"name": "Main Sports Ground",     "lat": 12.8390, "lng": 80.1520, "desc": "Cricket, football & athletics", "type": "sports"},
        {"name": "Indoor Stadium",         "lat": 12.8392, "lng": 80.1525, "desc": "Badminton, basketball, table tennis", "type": "sports"},
        {"name": "Swimming Pool",          "lat": 12.8388, "lng": 80.1530, "desc": "Olympic-size swimming pool", "type": "sports"},
    ],
    "📚 Library & Labs": [
        {"name": "Central Library",        "lat": 12.8409, "lng": 80.1532, "desc": "Main library with digital resources", "type": "library"},
        {"name": "Computer Labs (GDN)",    "lat": 12.8413, "lng": 80.1536, "desc": "General computing labs", "type": "lab"},
    ],
}

INDIA_DESTINATIONS = {
    "🏔️ North India": [
        {"name": "Taj Mahal, Agra",        "lat": 27.1751, "lng": 78.0421,  "desc": "UNESCO World Heritage — Mughal marble mausoleum"},
        {"name": "Jaipur City Palace",     "lat": 26.9255, "lng": 75.8237,  "desc": "Pink City royal residence & museum"},
        {"name": "Varanasi Ghats",         "lat": 25.3176, "lng": 83.0062,  "desc": "Oldest living city, spiritual capital of India"},
        {"name": "Golden Temple, Amritsar","lat": 31.6200, "lng": 74.8765,  "desc": "Holiest Sikh shrine"},
        {"name": "Leh Palace, Ladakh",     "lat": 34.1642, "lng": 77.5847,  "desc": "Himalayan fort & Buddhist monastery"},
    ],
    "🌊 South India": [
        {"name": "Meenakshi Temple, Madurai","lat": 9.9195, "lng": 78.1194, "desc": "Ancient Dravidian temple — 33,000 sculptures"},
        {"name": "Hampi Ruins, Karnataka", "lat": 15.3350, "lng": 76.4600,  "desc": "UNESCO — Vijayanagara Empire ruins"},
        {"name": "Munnar Tea Gardens",     "lat": 10.0889, "lng": 77.0595,  "desc": "Kerala hill station — rolling tea estates"},
        {"name": "Backwaters, Alleppey",   "lat": 9.4981,  "lng": 76.3388,  "desc": "Kerala houseboat cruises & lagoons"},
        {"name": "Coorg, Karnataka",       "lat": 12.3375, "lng": 75.8069,  "desc": "Scotland of India — coffee & spice trails"},
    ],
    "🏖️ Coastal Gems": [
        {"name": "Goa Beaches",            "lat": 15.2993, "lng": 74.1240,  "desc": "Golden beaches, Portuguese heritage, seafood"},
        {"name": "Andaman Islands",        "lat": 11.7401, "lng": 92.6586,  "desc": "Pristine coral reefs & white sand beaches"},
        {"name": "Pondicherry",            "lat": 11.9416, "lng": 79.8083,  "desc": "French colonial quarter & Auroville"},
    ],
    "🗿 Heritage & Culture": [
        {"name": "Ellora Caves, Maharashtra","lat": 20.0258,"lng": 75.1780, "desc": "UNESCO — Rock-cut Buddhist, Hindu & Jain temples"},
        {"name": "Khajuraho Temples, MP",  "lat": 24.8318, "lng": 79.9199,  "desc": "UNESCO — Medieval temple sculptures"},
        {"name": "Mysore Palace",          "lat": 12.3052, "lng": 76.6552,  "desc": "Indo-Saracenic royal palace — illuminated nightly"},
    ],
}


def get_leaflet_map_html(
    locations: List[Dict],
    center_lat: float = 20.5937,
    center_lng: float = 78.9629,
    zoom: int = 5,
    height: str = "500px",
    title: str = "Map",
) -> str:
    """Generate a self-contained Leaflet.js map (no API key needed)."""
    markers_js = ""
    for loc in locations:
        lat  = loc.get("lat", 0)
        lng  = loc.get("lng", 0)
        name = loc.get("name", "").replace("'", "\\'")
        desc = loc.get("desc", "").replace("'", "\\'")
        color = {
            "academic": "#4f8ef7",
            "hostel":   "#7c6af7",
            "food":     "#48c78e",
            "sports":   "#f7a04f",
            "library":  "#c8b8ff",
            "lab":      "#4ff7e8",
            "health":   "#f74f4f",
            "finance":  "#f7e44f",
        }.get(loc.get("type", ""), "#7c6af7")

        markers_js += f"""
        L.circleMarker([{lat}, {lng}], {{
            radius: 8, color: '{color}', fillColor: '{color}',
            fillOpacity: 0.85, weight: 2
        }}).addTo(map).bindPopup('<b>{name}</b><br>{desc}');
"""

    return f"""
<div id="map_{id(locations)}" style="height:{height};width:100%;border-radius:12px;overflow:hidden;"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map_{id(locations)}').setView([{center_lat}, {center_lng}], {zoom});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '© OpenStreetMap contributors', maxZoom: 19
}}).addTo(map);
{markers_js}
</script>
"""


def get_vit_campus_map(height: str = "500px") -> str:
    all_locs = []
    for group in VIT_CHENNAI_LOCATIONS.values():
        all_locs.extend(group)
    return get_leaflet_map_html(
        all_locs,
        center_lat=12.8410, center_lng=80.1530,
        zoom=17, height=height,
        title="VIT Chennai Campus",
    )


def get_india_travel_map(region: Optional[str] = None, height: str = "550px") -> str:
    all_locs = []
    src = INDIA_DESTINATIONS if region is None else {region: INDIA_DESTINATIONS.get(region, [])}
    for group in src.values():
        all_locs.extend(group)
    return get_leaflet_map_html(
        all_locs,
        center_lat=20.5937, center_lng=78.9629,
        zoom=5, height=height,
        title="India Travel Map",
    )


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def get_nearest_locations(
    lat: float, lng: float,
    location_type: Optional[str] = None,
    max_results: int = 5,
) -> List[Dict]:
    all_locs = []
    for group in VIT_CHENNAI_LOCATIONS.values():
        all_locs.extend(group)
    if location_type:
        all_locs = [l for l in all_locs if l.get("type") == location_type]
    for loc in all_locs:
        loc["distance_km"] = calculate_distance(lat, lng, loc["lat"], loc["lng"])
    return sorted(all_locs, key=lambda x: x["distance_km"])[:max_results]
