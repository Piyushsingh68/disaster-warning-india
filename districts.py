# Major Indian districts with lat/lon and state info
# You can add more districts from: https://simplemaps.com/data/in-cities

DISTRICTS = [
    # North India
    {"name": "Delhi",           "state": "Delhi",             "lat": 28.6139, "lon": 77.2090},
    {"name": "Lucknow",         "state": "Uttar Pradesh",     "lat": 26.8467, "lon": 80.9462},
    {"name": "Varanasi",        "state": "Uttar Pradesh",     "lat": 25.3176, "lon": 82.9739},
    {"name": "Patna",           "state": "Bihar",             "lat": 25.5941, "lon": 85.1376},
    {"name": "Jaipur",          "state": "Rajasthan",         "lat": 26.9124, "lon": 75.7873},
    {"name": "Chandigarh",      "state": "Punjab",            "lat": 30.7333, "lon": 76.7794},

    # East India
    {"name": "Kolkata",         "state": "West Bengal",       "lat": 22.5726, "lon": 88.3639},
    {"name": "Bhubaneswar",     "state": "Odisha",            "lat": 20.2961, "lon": 85.8245},
    {"name": "Guwahati",        "state": "Assam",             "lat": 26.1445, "lon": 91.7362},
    {"name": "Ranchi",          "state": "Jharkhand",         "lat": 23.3441, "lon": 85.3096},

    # West India
    {"name": "Mumbai",          "state": "Maharashtra",       "lat": 19.0760, "lon": 72.8777},
    {"name": "Pune",            "state": "Maharashtra",       "lat": 18.5204, "lon": 73.8567},
    {"name": "Ahmedabad",       "state": "Gujarat",           "lat": 23.0225, "lon": 72.5714},
    {"name": "Surat",           "state": "Gujarat",           "lat": 21.1702, "lon": 72.8311},

    # South India
    {"name": "Chennai",         "state": "Tamil Nadu",        "lat": 13.0827, "lon": 80.2707},
    {"name": "Bengaluru",       "state": "Karnataka",         "lat": 12.9716, "lon": 77.5946},
    {"name": "Hyderabad",       "state": "Telangana",         "lat": 17.3850, "lon": 78.4867},
    {"name": "Thiruvananthapuram","state": "Kerala",          "lat": 8.5241,  "lon": 76.9366},
    {"name": "Visakhapatnam",   "state": "Andhra Pradesh",    "lat": 17.6868, "lon": 83.2185},

    # Central India
    {"name": "Bhopal",          "state": "Madhya Pradesh",    "lat": 23.2599, "lon": 77.4126},
    {"name": "Nagpur",          "state": "Maharashtra",       "lat": 21.1458, "lon": 79.0882},
    {"name": "Raipur",          "state": "Chhattisgarh",      "lat": 21.2514, "lon": 81.6296},
]

# Alert thresholds — tweak these based on season
THRESHOLDS = {
    "heat": {
        "warning":  38,   # °C
        "severe":   42,   # °C
        "extreme":  46,   # °C
    },
    "cold": {
        "warning":  5,    # °C
        "severe":   2,    # °C
    },
    "wind": {
        "warning":  50,   # km/h
        "severe":   80,   # km/h (cyclone watch)
        "extreme":  120,  # km/h (cyclone)
    },
    "rain_1h": {
        "warning":  10,   # mm/h
        "severe":   30,   # mm/h (heavy rain)
        "extreme":  64,   # mm/h (very heavy — IMD standard)
    },
    "humidity": {
        "high":     90,   # % (flood risk indicator)
    }
}
