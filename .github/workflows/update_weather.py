#!/usr/bin/env python3
"""Refresh the live-weather block in README.md using the free Open-Meteo API
(no API key needed). Rewrites everything between the WEATHER:START and
WEATHER:END markers in README.md.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---- Edit these ----------------------------------------------------------
LATITUDE = 44.43
LONGITUDE = 24.37
PLACE = "Slatina"  # shown publicly in your README; set to "" to hide it
# --------------------------------------------------------------------------

README = Path("README.md")
START, END = "<!-- WEATHER:START -->", "<!-- WEATHER:END -->"
API_URL = os.environ.get("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")


def fetch():
    query = urllib.parse.urlencode({
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,weather_code",
        "timezone": "UTC",
    })
    req = urllib.request.Request(f"{API_URL}?{query}", headers={"User-Agent": "profile-readme-bot"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)["current"]


def describe(code):
    """WMO weather code -> emoji + short text."""
    if code == 0:
        return "☀️ Clear sky"
    if code == 1:
        return "🌤️ Mainly clear"
    if code == 2:
        return "⛅ Partly cloudy"
    if code == 3:
        return "☁️ Overcast"
    if code in (45, 48):
        return "🌫️ Fog"
    if 51 <= code <= 57:
        return "🌦️ Drizzle"
    if 61 <= code <= 67 or 80 <= code <= 82:
        return "🌧️ Rain"
    if 71 <= code <= 77 or code in (85, 86):
        return "❄️ Snow"
    if code >= 95:
        return "⛈️ Thunderstorm"
    return "🌡️ Weather"


def build_block(cur):
    when = datetime.fromisoformat(cur["time"]).replace(tzinfo=timezone.utc)
    where = f"{PLACE}: " if PLACE else ""
    line = (
        f"{where}{describe(int(cur['weather_code']))} · "
        f"**{cur['temperature_2m']:.1f}°C** · "
        f"**Humidity** {cur['relative_humidity_2m']:.0f}% · "
        f"**Wind** {cur['wind_speed_10m']:.1f} km/h · "
        f"**Pressure** {cur['pressure_msl']:.0f} hPa"
    )
    stamp = when.strftime("%Y-%m-%d %H:%M UTC")
    return f"{line}\n\n<sub>Updated {stamp} · Data: [Open-Meteo.com](https://open-meteo.com/)</sub>"


def main():
    try:
        block = build_block(fetch())
    except Exception as exc:  # network error, API change, bad JSON...
        # Warn but don't fail, so a hiccup doesn't send you red-run emails.
        print(f"::warning::Could not refresh weather block: {exc}")
        return

    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit("WEATHER:START / WEATHER:END markers not found in README.md")

    new_text = pattern.sub(lambda _: f"{START}\n{block}\n{END}", text, count=1)
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
