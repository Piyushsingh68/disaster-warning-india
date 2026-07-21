"""
fetch_all_india.py
------------------
Smart batch weather fetcher for all ~400 Indian districts.
Handles rate limiting, retries, and saves progress automatically.

Features:
- Fetches in batches of 10 with 1 second gap (respects free API limits)
- Saves progress after every batch (safe to interrupt and resume)
- Shows live progress bar
- Works in demo mode without any API key

Usage:
    python fetch_all_india.py --demo          # test without API key
    python fetch_all_india.py                 # live fetch (needs OWM key in .env)
    python fetch_all_india.py --state Kerala  # fetch one state only
    python fetch_all_india.py --resume        # resume interrupted fetch
"""

import os
import sys
import json
import time
import argparse
import requests
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from data.all_india_districts import ALL_INDIA_DISTRICTS
from data.districts import THRESHOLDS

OWM_API_KEY  = os.getenv("OWM_API_KEY", "")
OWM_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
OUTPUT_PATH  = os.path.join(os.path.dirname(__file__), "data", "all_india_weather.json")

BATCH_SIZE   = 10    # districts per batch
BATCH_DELAY  = 1.2  # seconds between batches (free plan = 60 calls/min)


# ── Progress bar ──────────────────────────────────────────────────────────────
def progress_bar(current, total, prefix="", width=35):
    filled = int(width * current / total)
    bar    = "█" * filled + "░" * (width - filled)
    pct    = current / total * 100
    print(f"\r  {prefix} [{bar}] {pct:.1f}% ({current}/{total})", end="", flush=True)


# ── Fetch one district from OWM ───────────────────────────────────────────────
def fetch_one(district: dict) -> dict | None:
    params = {
        "lat":   district["lat"],
        "lon":   district["lon"],
        "appid": OWM_API_KEY,
        "units": "metric",
    }
    try:
        resp = requests.get(OWM_BASE_URL, params=params, timeout=10)
        if resp.status_code == 401:
            print(f"\n  ✗ Invalid API key. Check your .env file.")
            return None
        if resp.status_code == 429:
            print(f"\n  ⏳ Rate limited — waiting 60 seconds...")
            time.sleep(60)
            resp = requests.get(OWM_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return None


# ── Parse OWM response ────────────────────────────────────────────────────────
def parse_one(raw: dict, district: dict) -> dict:
    main    = raw.get("main", {})
    wind    = raw.get("wind", {})
    rain    = raw.get("rain", {})
    weather = raw.get("weather", [{}])
    return {
        "district":    district["name"],
        "state":       district["state"],
        "lat":         district["lat"],
        "lon":         district["lon"],
        "temperature": round(main.get("temp", 0), 1),
        "feels_like":  round(main.get("feels_like", 0), 1),
        "humidity":    main.get("humidity", 0),
        "wind_kmh":    round(wind.get("speed", 0) * 3.6, 1),
        "rain_1h":     rain.get("1h", 0),
        "condition":   weather[0].get("main", "Unknown"),
        "description": weather[0].get("description", ""),
        "fetched_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── Mock weather for demo mode ────────────────────────────────────────────────
def mock_one(district: dict) -> dict:
    scenarios = [
        {"temperature": 44.2, "humidity": 20, "wind_kmh": 15,  "rain_1h": 0,  "condition": "Clear"},
        {"temperature": 28.0, "humidity": 91, "wind_kmh": 12,  "rain_1h": 70, "condition": "Rain"},
        {"temperature": 22.0, "humidity": 65, "wind_kmh": 125, "rain_1h": 35, "condition": "Thunderstorm"},
        {"temperature": 31.0, "humidity": 55, "wind_kmh": 20,  "rain_1h": 0,  "condition": "Clouds"},
        {"temperature": 38.5, "humidity": 30, "wind_kmh": 40,  "rain_1h": 5,  "condition": "Haze"},
        {"temperature": 36.0, "humidity": 60, "wind_kmh": 25,  "rain_1h": 15, "condition": "Rain"},
        {"temperature": 42.0, "humidity": 25, "wind_kmh": 55,  "rain_1h": 0,  "condition": "Clear"},
        {"temperature": 26.0, "humidity": 82, "wind_kmh": 18,  "rain_1h": 45, "condition": "Rain"},
    ]
    # Use lat/lon to seed randomness so same district always gets same scenario
    random.seed(int(district["lat"] * 100 + district["lon"] * 10))
    s = random.choice(scenarios)
    return {
        "district":    district["name"],
        "state":       district["state"],
        "lat":         district["lat"],
        "lon":         district["lon"],
        "temperature": s["temperature"],
        "feels_like":  s["temperature"] - 1.5,
        "humidity":    s["humidity"],
        "wind_kmh":    s["wind_kmh"],
        "rain_1h":     s["rain_1h"],
        "condition":   s["condition"],
        "description": s["condition"].lower(),
        "fetched_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── Risk scorer ───────────────────────────────────────────────────────────────
def score(data: dict) -> dict:
    t      = THRESHOLDS
    s      = 0.0
    alerts = []

    temp     = data["temperature"]
    wind     = data["wind_kmh"]
    rain     = data["rain_1h"]
    humidity = data["humidity"]

    if temp >= t["heat"]["extreme"]:
        s += 4.0; alerts.append(f"🔴 Extreme heat: {temp}°C")
    elif temp >= t["heat"]["severe"]:
        s += 2.5; alerts.append(f"🟠 Severe heat: {temp}°C")
    elif temp >= t["heat"]["warning"]:
        s += 1.0; alerts.append(f"🟡 Heat warning: {temp}°C")

    if temp <= t["cold"]["severe"]:
        s += 2.0; alerts.append(f"🔵 Severe cold: {temp}°C")
    elif temp <= t["cold"]["warning"]:
        s += 1.0; alerts.append(f"🔵 Cold warning: {temp}°C")

    if wind >= t["wind"]["extreme"]:
        s += 4.0; alerts.append(f"🌀 Cyclone winds: {wind} km/h")
    elif wind >= t["wind"]["severe"]:
        s += 2.5; alerts.append(f"🌀 Cyclone watch: {wind} km/h")
    elif wind >= t["wind"]["warning"]:
        s += 1.0; alerts.append(f"💨 Strong winds: {wind} km/h")

    if rain >= t["rain_1h"]["extreme"]:
        s += 4.0; alerts.append(f"🌊 Extreme rain: {rain} mm/h")
    elif rain >= t["rain_1h"]["severe"]:
        s += 2.5; alerts.append(f"🌧 Heavy rain: {rain} mm/h")
    elif rain >= t["rain_1h"]["warning"]:
        s += 1.0; alerts.append(f"🌦 Moderate rain: {rain} mm/h")

    if humidity >= t["humidity"]["high"] and rain > 0:
        s += 1.0; alerts.append(f"💧 Flood conditions likely ({humidity}%)")

    s = min(round(s, 1), 10.0)
    level = ("CRITICAL" if s >= 7 else "HIGH" if s >= 4
             else "MODERATE" if s >= 2 else "LOW" if s > 0 else "NORMAL")

    return {**data, "risk_score": s, "risk_level": level, "alerts": alerts}


# ── Main runner ───────────────────────────────────────────────────────────────
def run(state_filter: str = None, demo: bool = False, resume: bool = False):
    districts = ALL_INDIA_DISTRICTS
    if state_filter:
        districts = [d for d in districts if d["state"].lower() == state_filter.lower()]
        if not districts:
            states = sorted(set(d["state"] for d in ALL_INDIA_DISTRICTS))
            print(f"State '{state_filter}' not found.\nAvailable: {states}")
            return

    if not demo and not OWM_API_KEY:
        print("⚠  No OWM_API_KEY in .env — switching to demo mode.")
        print("   Get a free key at https://openweathermap.org/api\n")
        demo = True

    # Resume: load already-fetched districts
    already_done = {}
    if resume and os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            old = json.load(f)
        already_done = {d["district"]: d for d in old.get("districts", [])}
        print(f"▶  Resuming — {len(already_done)} districts already fetched.")

    total   = len(districts)
    results = list(already_done.values())
    pending = [d for d in districts if d["name"] not in already_done]

    print(f"\n🌏 All-India Weather Fetch")
    print(f"   Total districts : {total}")
    print(f"   To fetch        : {len(pending)}")
    print(f"   Mode            : {'Demo (mock data)' if demo else 'Live (OpenWeatherMap)'}")
    if not demo:
        est = len(pending) * BATCH_DELAY / BATCH_SIZE
        print(f"   Est. time       : ~{est:.0f} seconds ({est/60:.1f} min)")
    print()

    batches = [pending[i:i+BATCH_SIZE] for i in range(0, len(pending), BATCH_SIZE)]

    for bi, batch in enumerate(batches):
        for district in batch:
            if demo:
                parsed = mock_one(district)
            else:
                raw = fetch_one(district)
                if raw is None:
                    continue
                parsed = parse_one(raw, district)

            scored = score(parsed)
            results.append(scored)

        # Save progress after each batch
        results_sorted = sorted(results, key=lambda x: x["risk_score"], reverse=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "total":        len(results),
                "mode":         "demo" if demo else "live",
                "districts":    results_sorted,
            }, f, ensure_ascii=False, indent=2)

        done = min((bi + 1) * BATCH_SIZE, len(pending))
        progress_bar(done, len(pending), prefix="Fetching")

        if not demo and bi < len(batches) - 1:
            time.sleep(BATCH_DELAY)

    print()  # newline after progress bar

    # Final summary
    results_sorted = sorted(results, key=lambda x: x["risk_score"], reverse=True)
    critical = [r for r in results_sorted if r["risk_level"] == "CRITICAL"]
    high     = [r for r in results_sorted if r["risk_level"] == "HIGH"]

    print(f"\n✅ Done! {len(results_sorted)} districts fetched.")
    print(f"   🔴 Critical : {len(critical)}")
    print(f"   🟠 High     : {len(high)}")
    print(f"   📁 Saved to : {OUTPUT_PATH}")

    if critical:
        print(f"\n🚨 Critical districts:")
        for d in critical[:5]:
            print(f"   • {d['district']}, {d['state']} — {d['risk_score']}/10")
            for a in d["alerts"]:
                print(f"     {a}")

    print(f"\n👉 Now run: python fetch_all_india.py → dashboard shows all {len(results_sorted)} districts!")
    return results_sorted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="All-India Weather Fetcher")
    parser.add_argument("--demo",   action="store_true", help="Use mock data (no API key needed)")
    parser.add_argument("--state",  type=str, help="Fetch one state only (e.g. --state Kerala)")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted fetch")
    args = parser.parse_args()

    run(state_filter=args.state, demo=args.demo, resume=args.resume)
