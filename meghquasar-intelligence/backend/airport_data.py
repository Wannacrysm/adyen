"""Airport coordinate resolver backed by real OurAirports data with local caching."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
AIRPORTS_CSV = DATA_DIR / "airports.csv"
OURAIRPORTS_URL = "https://ourairports.com/data/airports.csv"

# Minimal fallback only when network/cache unavailable.
FALLBACK_AIRPORTS: Dict[str, Tuple[float, float]] = {
    "KTEB": (40.8501, -74.0608),
    "KLAX": (33.9416, -118.4085),
    "EGLL": (51.47, -0.4543),
    "OMDB": (25.2532, 55.3657),
    "VABB": (19.0896, 72.8656),
}


def ensure_airports_csv() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if AIRPORTS_CSV.exists() and AIRPORTS_CSV.stat().st_size > 0:
        return AIRPORTS_CSV

    response = requests.get(OURAIRPORTS_URL, timeout=60)
    response.raise_for_status()
    AIRPORTS_CSV.write_bytes(response.content)
    return AIRPORTS_CSV


def load_airports() -> Dict[str, Tuple[float, float]]:
    airports = dict(FALLBACK_AIRPORTS)
    try:
        csv_path = ensure_airports_csv()
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                icao = (row.get("ident") or "").strip().upper()
                lat = row.get("latitude_deg")
                lon = row.get("longitude_deg")
                if not icao or not lat or not lon:
                    continue
                airports[icao] = (float(lat), float(lon))
    except Exception:
        # Keep fallback mapping available when download/parsing fails.
        pass
    return airports
