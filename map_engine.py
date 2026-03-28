"""
map_engine.py — VIT Chennai Campus Map + India Trip Planner
Real maps integration with Google Maps Embed API + Places API.
"""
from __future__ import annotations
from typing import Dict, List, Optional

GOOGLE_MAPS_EMBED_KEY = "AIzaSyDC6rwwzMleiNs4H2Ds3YwUq9is57gBIP8"

VIT_CHENNAI_LOCATIONS = {
    "🏫 Academic Buildings": [
        {"name": "Technology Tower (TT)", "lat": 12.8406, "lng": 80.1534, "desc": "Main academic building with modern labs", "type": "academic"},
        {"name": "Anna Auditorium", "lat": 12.8408, "lng": 80.1528, "desc": "Main auditorium for events & convocation", "type": "academic"},
        {"name": "Mechanical Block", "lat": 12.8412, "lng": 80.1540, "desc": "Mechanical Engineering labs", "type": "academic"},
        {"name": "Civil Block", "lat": 12.8404, "lng": 80.1545, "desc": "Civil & Structural Engineering", "type": "academic"},
        {"name": "Chemistry Block", "lat": 12.8415, "lng": 80.1530, "desc": "Chemistry labs and lecture halls", "type": "academic"},
        {"name": "Physics Block", "lat": 12.8418, "lng": 80.1535, "desc": "Physics labs and research center", "type": "academic"},
        {"name": "MBA Block", "lat": 12.8400, "lng": 80.1520, "desc": "School of Business, MBA programs", "type": "academic"},
        {"name": "Architecture Block", "lat": 12.8422, "lng": 80.1542, "desc": "School of Architecture", "type": "academic"},
    ],
    "🏠 Hostels": [
        {"name": "MH1 - Men's Hostel 1", "lat": 12.8398, "lng": 80.1510, "desc": "Men's residential block", "type": "hostel"},
        {"name": "MH2 - Men's Hostel 2", "lat": 12.8395, "lng": 80.1515, "desc": "Men's residential block", "type": "hostel"},
        {"name": "LH1 - Ladies Hostel 1", "lat": 12.8430, "lng": 80.1525, "desc": "Women's residential block", "type": "hostel"},
        {"name": "LH2 - Ladies Hostel 2", "lat": 12.8432, "lng": 80.1528, "desc": "Women's residential block", "type": "hostel"},
        {"name": "LH3 - Ladies Hostel 3", "lat": 12.8435, "lng": 80.1530, "desc": "Women's residential block", "type": "hostel"},
    ],
    "🍽️ Food Courts": [
        {"name": "Main Cafeteria", "lat": 12.8408, "lng": 80.1520, "desc": "Central food court with multiple cuisine options", "type": "food"},
        {"name": "Juice Stall / Snack Corner", "lat": 12.8410, "lng": 80.1522, "desc": "Quick snacks, beverages", "type": "food"},
        {"name": "Engineering Canteen", "lat": 12.8414, "lng": 80.1538, "desc": "Near tech blocks canteen", "type": "food"},
    ],
    "📚 Library & Study": [
        {"name": "Central Library", "lat": 12.8405, "lng": 80.1532, "desc": "Main library with 3 floors, 24/7 study rooms", "type": "library"},
        {"name": "Digital Library", "lat": 12.8407, "lng": 80.1533, "desc": "E-resources, computer terminals", "type": "library"},
    ],
    "⚽ Sports & Recreation": [
        {"name": "Sports Complex", "lat": 12.8420, "lng": 80.1548, "desc": "Indoor sports, gymnasium, courts", "type": "sports"},
        {"name": "Football Ground", "lat": 12.8425, "lng": 80.1555, "desc": "Full-size football ground", "type": "sports"},
        {"name": "Cricket Ground", "lat": 12.8428, "lng": 80.1558, "desc": "Cricket pitch and practice nets", "type": "sports"},
        {"name": "Swimming Pool", "lat": 12.8418, "lng": 80.1550, "desc": "Olympic-size swimming pool", "type": "sports"},
    ],
    "🏥 Health & Services": [
        {"name": "Medical Center", "lat": 12.8402, "lng": 80.1518, "desc": "Campus health center, 24/7", "type": "services"},
        {"name": "ATM / Bank", "lat": 12.8403, "lng": 80.1516, "desc": "SBI ATM and banking services", "type": "services"},
        {"name": "Post Office", "lat": 12.8401, "lng": 80.1514, "desc": "VIT Post Office", "type": "services"},
    ],
    "🚌 Transport": [
        {"name": "Main Gate", "lat": 12.8396, "lng": 80.1505, "desc": "Main entrance and security", "type": "transport"},
        {"name": "Bus Stand", "lat": 12.8394, "lng": 80.1507, "desc": "Campus bus pickup/drop point", "type": "transport"},
        {"name": "Auto Stand", "lat": 12.8393, "lng": 80.1503, "desc": "Auto-rickshaw stand outside campus", "type": "transport"},
    ],
}

VIT_CENTER_LAT = 12.8406
VIT_CENTER_LNG = 80.1534

INDIA_DESTINATIONS = {
    "🏔️ Hill Stations": [
        {"name": "Ooty", "state": "Tamil Nadu", "lat": 11.4102, "lng": 76.6950, "desc": "Queen of Hills, tea gardens, Nilgiri railway"},
        {"name": "Munnar", "state": "Kerala", "lat": 10.0889, "lng": 77.0595, "desc": "Tea estates, misty mountains"},
        {"name": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lng": 77.1734, "desc": "Colonial hill station, Himalayan views"},
        {"name": "Darjeeling", "state": "West Bengal", "lat": 27.0360, "lng": 88.2627, "desc": "Tea gardens, Tiger Hill sunrise"},
        {"name": "Manali", "state": "Himachal Pradesh", "lat": 32.2432, "lng": 77.1892, "desc": "Adventure hub, Rohtang Pass"},
        {"name": "Kodaikanal", "state": "Tamil Nadu", "lat": 10.2381, "lng": 77.4892, "desc": "Princess of Hill Stations"},
        {"name": "Coorg", "state": "Karnataka", "lat": 12.3375, "lng": 75.8069, "desc": "Scotland of India, coffee estates"},
    ],
    "🏖️ Beaches": [
        {"name": "Goa Beaches", "state": "Goa", "lat": 15.2993, "lng": 74.1240, "desc": "Baga, Calangute, Anjuna, Palolem"},
        {"name": "Marina Beach", "state": "Tamil Nadu", "lat": 13.0500, "lng": 80.2824, "desc": "World's longest urban beach, Chennai"},
        {"name": "Kovalam", "state": "Kerala", "lat": 8.4004, "lng": 76.9788, "desc": "Lighthouse beach, backwaters"},
        {"name": "Varkala", "state": "Kerala", "lat": 8.7379, "lng": 76.7162, "desc": "Cliff beach, mineral springs"},
        {"name": "Radhanagar Beach", "state": "Andaman", "lat": 11.9750, "lng": 92.6594, "desc": "Asia's best beach, Havelock Island"},
        {"name": "Juhu Beach", "state": "Maharashtra", "lat": 19.0998, "lng": 72.8262, "desc": "Famous Mumbai beach, street food"},
    ],
    "🏛️ Heritage & History": [
        {"name": "Taj Mahal", "state": "Uttar Pradesh", "lat": 27.1751, "lng": 78.0421, "desc": "World's greatest monument of love, Agra"},
        {"name": "Hampi", "state": "Karnataka", "lat": 15.3350, "lng": 76.4600, "desc": "UNESCO ruins of Vijayanagara Empire"},
        {"name": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lng": 82.9739, "desc": "World's oldest living city, Ganga ghats"},
        {"name": "Khajuraho", "state": "Madhya Pradesh", "lat": 24.8318, "lng": 79.9199, "desc": "UNESCO temples with intricate sculptures"},
        {"name": "Mahabalipuram", "state": "Tamil Nadu", "lat": 12.6269, "lng": 80.1927, "desc": "UNESCO shore temples, rock carvings"},
        {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873, "desc": "Pink City, Amber Fort, Hawa Mahal"},
    ],
    "🌿 Nature & Wildlife": [
        {"name": "Jim Corbett National Park", "state": "Uttarakhand", "lat": 29.5300, "lng": 78.7747, "desc": "India's oldest national park, tigers"},
        {"name": "Kaziranga", "state": "Assam", "lat": 26.6851, "lng": 93.3698, "desc": "UNESCO, one-horned rhinos"},
        {"name": "Sundarbans", "state": "West Bengal", "lat": 21.9497, "lng": 89.1833, "desc": "UNESCO mangrove forests, Royal Bengal Tigers"},
        {"name": "Valley of Flowers", "state": "Uttarakhand", "lat": 30.7258, "lng": 79.6077, "desc": "UNESCO alpine meadow, wildflowers"},
        {"name": "Periyar Wildlife", "state": "Kerala", "lat": 9.4694, "lng": 77.1891, "desc": "Boat safari, elephants, tigers"},
    ],
    "🕌 Spiritual": [
        {"name": "Rishikesh", "state": "Uttarakhand", "lat": 30.0869, "lng": 78.2676, "desc": "Yoga capital, Ganga aarti, adventure"},
        {"name": "Amritsar", "state": "Punjab", "lat": 31.6340, "lng": 74.8723, "desc": "Golden Temple, Wagah Border"},
        {"name": "Tirupati", "state": "Andhra Pradesh", "lat": 13.6288, "lng": 79.4192, "desc": "Richest temple, Balaji darshan"},
        {"name": "Vrindavan", "state": "Uttar Pradesh", "lat": 27.5714, "lng": 77.6968, "desc": "Krishna birthplace, temples"},
    ],
}


def get_vit_map_html(selected_categories: List[str] = None, show_all: bool = True) -> str:
    """Generate embedded VIT Chennai campus map HTML."""
    locations = []
    categories = selected_categories or list(VIT_CHENNAI_LOCATIONS.keys())
    
    for cat in categories:
        if cat in VIT_CHENNAI_LOCATIONS:
            locations.extend(VIT_CHENNAI_LOCATIONS[cat])
    
    # Build markers JS
    markers_js = []
    for loc in locations:
        color_map = {
            "academic": "#7c6af7", "hostel": "#34d399", "food": "#f59e0b",
            "library": "#60a5fa", "sports": "#f87171", "services": "#c084fc",
            "transport": "#fbbf24"
        }
        color = color_map.get(loc.get("type","academic"), "#7c6af7")
        markers_js.append(f"""
        new google.maps.Marker({{
            position: {{lat: {loc['lat']}, lng: {loc['lng']}}},
            map: map,
            title: "{loc['name']}",
            icon: {{
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: "{color}",
                fillOpacity: 0.9,
                strokeColor: "white",
                strokeWeight: 2
            }}
        }}).addListener('click', function() {{
            document.getElementById('info').innerHTML = '<h3>{loc["name"]}</h3><p>{loc["desc"]}</p>';
        }});""")
    
    return f"""
    <div style="border-radius:12px;overflow:hidden;border:1px solid rgba(124,106,247,0.3);">
    <div id="vit-map" style="height:500px;width:100%;"></div>
    <div id="info" style="background:#13131f;padding:12px;font-size:.9rem;color:#f0f0ff;min-height:60px;">
        Click any marker to see details.
    </div>
    </div>
    <script>
    function initVITMap() {{
        const map = new google.maps.Map(document.getElementById('vit-map'), {{
            center: {{lat: {VIT_CENTER_LAT}, lng: {VIT_CENTER_LNG}}},
            zoom: 17,
            mapTypeId: 'satellite',
            styles: [{{featureType:"all",elementType:"labels.text.fill",stylers:[{{color:"#ffffff"}}]}}]
        }});
        {"".join(markers_js)}
    }}
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_EMBED_KEY}&callback=initVITMap"></script>
    """


def get_vit_embed_url(lat: float = None, lng: float = None, zoom: int = 17) -> str:
    """Get Google Maps embed URL for VIT Chennai."""
    lat = lat or VIT_CENTER_LAT
    lng = lng or VIT_CENTER_LNG
    return f"https://www.google.com/maps/embed/v1/view?key={GOOGLE_MAPS_EMBED_KEY}&center={lat},{lng}&zoom={zoom}&maptype=satellite"


def get_directions_url(from_place: str, to_name: str, to_lat: float, to_lng: float) -> str:
    """Get Google Maps directions URL."""
    dest = f"{to_lat},{to_lng}"
    return f"https://www.google.com/maps/dir/{from_place.replace(' ','+')}/{dest}"


def get_india_trip_plan(origin: str, destination: str, days: int, budget: str, interests: List[str]) -> str:
    """AI-generated India trip plan."""
    from utils.groq_client import chat_with_groq
    
    interests_str = ", ".join(interests) if interests else "general tourism"
    
    # Find destination info
    dest_info = ""
    for cat, places in INDIA_DESTINATIONS.items():
        for place in places:
            if destination.lower() in place["name"].lower() or destination.lower() in place.get("state","").lower():
                dest_info = f"{place['name']}, {place['state']} — {place['desc']}"
                break
    
    prompt = f"""Create a detailed {days}-day trip plan for India.

From: {origin}
To: {destination} {f"({dest_info})" if dest_info else ""}
Duration: {days} days
Budget: {budget}
Interests: {interests_str}

Generate a comprehensive itinerary with:

## 🗺️ {days}-Day Trip: {origin} → {destination}

### ✈️ How to Get There
[Best transport options with approximate costs, time]

### 📅 Day-by-Day Itinerary

**Day 1:** [Title]
- Morning: [Activity with timing 7:00 AM]
- Afternoon: [Activity]
- Evening: [Activity]
- Night: [Accommodation suggestion]
- 💰 Day budget: ₹XXX

[Continue for each day...]

### 🏨 Where to Stay
| Type | Name | Price/night | Why |
|------|------|-------------|-----|

### 🍽️ Must-Try Food
[5 local dishes and where to eat them]

### 💰 Total Budget Breakdown
| Category | Estimated Cost |
|----------|----------------|

### ⚠️ Important Tips
[5 practical tips specific to this destination]

### 📱 Useful Apps
[Apps for transport, booking, language, maps]

Be specific with Indian prices in INR, real restaurant/hotel names, and local transport options."""

    try:
        result = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            model="llama-4-scout-17b-16e-instruct",
        )
        if isinstance(result, tuple): result = result[0]
        return result or "Could not generate trip plan."
    except Exception as e:
        return f"Error: {e}"


def answer_travel_question(question: str, context: str = "") -> str:
    """Answer travel-related questions with AI."""
    from utils.groq_client import chat_with_groq
    
    ctx = f"\nContext: {context}" if context else ""
    
    prompt = f"""You are an expert India travel guide with deep knowledge of all Indian destinations, transport, culture, and practical travel tips.{ctx}

Question: {question}

Provide a helpful, accurate, and specific answer with:
- Practical information (costs in INR, timing, transport)
- Best season to visit
- Honest pros and cons
- Specific recommendations (not generic advice)
- Safety and local tips"""

    try:
        result = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            model="llama-4-scout-17b-16e-instruct",
        )
        if isinstance(result, tuple): result = result[0]
        return result or "Could not answer."
    except Exception as e:
        return f"Error: {e}"
