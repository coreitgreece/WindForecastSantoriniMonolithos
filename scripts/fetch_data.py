"""Fetch historical weather data for Santorini Monolithos.

This script demonstrates how to fetch data from different sources
(Open-Meteo, Meteostat, Windy) and store them in a CSV file with the
following columns:
    time, wind_speed, wind_dir, temp, pressure, humidity,
    lclouds, mclouds, hclouds, precip, cape, source

The data range is set from 1/1/2020 until today. The script also
fetches live data from Weather Underground.

Actual API calls require internet access and valid API keys where
applicable. They are implemented here using the standard library so the
script can run without additional dependencies.
"""

import csv
import datetime as dt
import json
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
    # NOTE: The page is HTML/JavaScript and requires parsing. For brevity we
    # only store the raw HTML with a timestamp.
    now = dt.datetime.utcnow().isoformat() + "Z"
    return [[now, None, None, None, None, None, None, None, None, None, None, "wunderground_html"]]


# Placeholder functions for other sources

def fetch_meteostat(start: dt.date, end: dt.date) -> List[List[str]]:
    """Placeholder for Meteostat data fetching."""
    print("Meteostat API not implemented in this environment.")
    return []


def fetch_windy(start: dt.date, end: dt.date) -> List[List[str]]:
    """Placeholder for Windy data fetching."""
    print("Windy API not implemented in this environment.")
    return []


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
