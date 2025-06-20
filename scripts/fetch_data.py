"""Fetch historical weather data for Santorini Monolithos.

This script demonstrates how to fetch data from different sources
(Open-Meteo, Meteostat, Windy) and store them in a CSV file with the
following columns:
    time, wind_speed, wind_dir, temp, pressure, humidity,
    lclouds, mclouds, hclouds, precip, cape, source

The data range is set from 1/1/2020 until today. The script also
fetches live data from Weather Underground.

Actual API calls require internet access and valid API keys where
applicable. Set ``METEOSTAT_API_KEY`` and ``WINDY_API_KEY`` in your
environment to enable those sources. The code relies only on the Python
standard library so it can run without extra dependencies.
"""

import csv
import datetime as dt
import json
import os
import re
import urllib.request
from typing import List

DATA_COLUMNS = [
    "time",
    "wind_speed",
    "wind_dir",
    "temp",
    "pressure",
    "humidity",
    "lclouds",
    "mclouds",
    "hclouds",
    "precip",
    "cape",
    "source",
]


def fetch_openmeteo(start: dt.date, end: dt.date) -> List[List[str]]:
    """Fetch hourly data from the Open-Meteo API."""
    results = []
    base_url = (
        "https://archive-api.open-meteo.com/v1/archive?latitude=36.401&longitude=25.479"
        "&hourly=windspeed_10m,winddirection_10m,temperature_2m,pressure_msl,"
        "relativehumidity_2m,cloudcover_low,cloudcover_mid,cloudcover_high,precipitation,cape"
        "&timezone=UTC"
    )
    current = start
    while current <= end:
        url = f"{base_url}&start_date={current}&end_date={current}"
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.load(resp)
        except Exception as exc:  # pragma: no cover - network required
            print(f"Failed to fetch Open-Meteo data for {current}: {exc}")
            break
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        for i, t in enumerate(times):
            row = [
                t,
                hourly.get("windspeed_10m", [None])[i],
                hourly.get("winddirection_10m", [None])[i],
                hourly.get("temperature_2m", [None])[i],
                hourly.get("pressure_msl", [None])[i],
                hourly.get("relativehumidity_2m", [None])[i],
                hourly.get("cloudcover_low", [None])[i],
                hourly.get("cloudcover_mid", [None])[i],
                hourly.get("cloudcover_high", [None])[i],
                hourly.get("precipitation", [None])[i],
                hourly.get("cape", [None])[i],
                "openmeteo",
            ]
            results.append(row)
        current += dt.timedelta(days=1)
    return results


def fetch_wunderground_live() -> List[List[str]]:
    """Fetch the latest observations from Weather Underground."""
    url = (
        "https://www.wunderground.com/history/daily/gr/santorini/LGSR"  # noqa: E501
    )
    try:
        with urllib.request.urlopen(url) as resp:
            html = resp.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - network required
        print(f"Failed to fetch Weather Underground data: {exc}")
        return []
    now = dt.datetime.utcnow().isoformat() + "Z"
    # Attempt to extract the latest observation using a simple regex
    match = re.search(r"\{\"obsTimeUtc\":\"(.*?)\".*?\"winddir\":(\d+).*?\"windspd\":(\d+).*?\"temp\":([-\d.]+).*?\"pressure\":([-\d.]+).*?\"humidity\":(\d+)", html)
    if match:
        return [[
            match.group(1),
            match.group(3),
            match.group(2),
            match.group(4),
            match.group(5),
            match.group(6),
            None,
            None,
            None,
            None,
            None,
            "wunderground",
        ]]
    # Fallback: store raw HTML timestamp
    return [[now, None, None, None, None, None, None, None, None, None, None, "wunderground_html"]]


# Placeholder functions for other sources

def fetch_meteostat(start: dt.date, end: dt.date) -> List[List[str]]:
    """Fetch data from the Meteostat API using an API key."""
    api_key = os.getenv("METEOSTAT_API_KEY")
    if not api_key:
        print("METEOSTAT_API_KEY not set. Skipping Meteostat fetch.")
        return []
    station = os.getenv("METEOSTAT_STATION", "LGSR")
    url = (
        "https://api.meteostat.net/v2/stations/hourly"
        f"?station={station}&start={start}&end={end}&tz=UTC"
    )
    req = urllib.request.Request(url, headers={"x-api-key": api_key})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except Exception as exc:  # pragma: no cover - network required
        print(f"Failed to fetch Meteostat data: {exc}")
        return []
    results = []
    for row in data.get("data", []):
        results.append([
            row.get("time"),
            row.get("wspd"),
            row.get("wdir"),
            row.get("temp"),
            row.get("pres"),
            row.get("rhum"),
            None,
            None,
            None,
            row.get("prcp"),
            None,
            "meteostat",
        ])
    return results


def fetch_windy(start: dt.date, end: dt.date) -> List[List[str]]:
    """Fetch data from the Windy API using an API key."""
    api_key = os.getenv("WINDY_API_KEY")
    if not api_key:
        print("WINDY_API_KEY not set. Skipping Windy fetch.")
        return []
    body = json.dumps(
        {
            "lat": 36.401,
            "lon": 25.479,
            "model": "gfs",
            "parameters": ["wind", "temp", "pressure", "rh"],
            "levels": ["surface"],
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.windy.com/api/point-forecast/v2",
        data=body,
        headers={"Content-Type": "application/json", "x-windy-key": api_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except Exception as exc:  # pragma: no cover - network required
        print(f"Failed to fetch Windy data: {exc}")
        return []
    results = []
    times = data.get("ts", [])
    wind = data.get("wind", [])
    temp = data.get("temp", [])
    pressure = data.get("pressure", [])
    rh = data.get("rh", [])
    for i, t in enumerate(times):
        results.append([
            dt.datetime.utcfromtimestamp(t).isoformat() + "Z",
            wind[i] if i < len(wind) else None,
            None,
            temp[i] if i < len(temp) else None,
            pressure[i] if i < len(pressure) else None,
            rh[i] if i < len(rh) else None,
            None,
            None,
            None,
            None,
            None,
            "windy",
        ])
    return results


def save_to_csv(rows: List[List[str]], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(DATA_COLUMNS)
        writer.writerows(rows)


def main() -> None:
    start_date = dt.date(2020, 1, 1)
    end_date = dt.date.today()
    rows: List[List[str]] = []
    rows.extend(fetch_openmeteo(start_date, end_date))
    rows.extend(fetch_meteostat(start_date, end_date))
    rows.extend(fetch_windy(start_date, end_date))
    rows.extend(fetch_wunderground_live())
    save_to_csv(rows, "data/data.csv")
    print(f"Saved {len(rows)} rows to data/data.csv")


if __name__ == "__main__":
    main()
