"""Route feasibility and nearest aircraft search."""
from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Dict, List

from .airport_data import load_airports

DB_PATH = Path(__file__).resolve().parents[1] / "meghquasar.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def great_circle_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return (2 * r_km * math.asin(math.sqrt(a))) * 0.539957


def get_airport_coordinates(icao: str) -> tuple[float, float]:
    airports = load_airports()
    key = icao.strip().upper()
    if key not in airports:
        raise KeyError(f"Unknown airport ICAO: {key}")
    return airports[key]


def find_feasible_aircraft(origin: str, destination: str, limit: int = 50) -> Dict:
    o_lat, o_lon = get_airport_coordinates(origin)
    d_lat, d_lon = get_airport_coordinates(destination)
    route_nm = great_circle_nm(o_lat, o_lon, d_lat, d_lon)

    query = """
    SELECT s.icao24, s.callsign, s.latitude, s.longitude,
           r.model, a.range_nm, a.seats, a.cruise_speed, a.hourly_cost
    FROM aircraft_states s
    JOIN global_aircraft_registry r ON r.icao24 = s.icao24
    JOIN aircraft_specs a ON a.model = r.model
    WHERE a.category IN ('business jet', 'corporate turboprop', 'private helicopter')
      AND a.range_nm >= ?
      AND s.latitude IS NOT NULL
      AND s.longitude IS NOT NULL
    """
    with get_conn() as conn:
        rows = conn.execute(query, (route_nm,)).fetchall()

    ranked = []
    for row in rows:
        dist_to_origin = great_circle_nm(o_lat, o_lon, row["latitude"], row["longitude"])
        ranked.append({**dict(row), "route_nm": route_nm, "distance_to_origin_nm": round(dist_to_origin, 2)})

    ranked.sort(key=lambda r: (r["distance_to_origin_nm"], r["hourly_cost"], -r["seats"]))
    return {"route_nm": round(route_nm, 2), "aircraft": ranked[:limit]}


def nearest_aircraft(origin: str, limit: int = 20) -> List[dict]:
    o_lat, o_lon = get_airport_coordinates(origin)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT icao24, callsign, latitude, longitude, last_seen
            FROM aircraft_states
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
        ).fetchall()

    scored = [
        {**dict(row), "distance_nm": round(great_circle_nm(o_lat, o_lon, row["latitude"], row["longitude"]), 2)}
        for row in rows
    ]
    scored.sort(key=lambda x: x["distance_nm"])
    return scored[:limit]
