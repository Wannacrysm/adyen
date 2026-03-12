"""Detect potential empty legs from flight history patterns."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .routing_engine import get_airport_coordinates, great_circle_nm

DB_PATH = Path(__file__).resolve().parents[1] / "meghquasar.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def detect_empty_legs() -> list[dict]:
    query = """
    WITH ordered AS (
        SELECT fh.icao24, fh.origin, fh.destination, fh.timestamp,
               LEAD(fh.origin) OVER (PARTITION BY fh.icao24 ORDER BY fh.timestamp) AS next_origin,
               LEAD(fh.destination) OVER (PARTITION BY fh.icao24 ORDER BY fh.timestamp) AS next_destination,
               LEAD(fh.timestamp) OVER (PARTITION BY fh.icao24 ORDER BY fh.timestamp) AS next_timestamp,
               o.base_airport
        FROM flight_history fh
        LEFT JOIN global_aircraft_registry r ON r.icao24 = fh.icao24
        LEFT JOIN operator_fleet ofl ON ofl.aircraft_model = r.model
        LEFT JOIN operators o ON o.id = ofl.operator_id
    )
    SELECT * FROM ordered WHERE destination = next_origin AND next_destination IS NOT NULL;
    """
    with get_conn() as conn:
        candidates = conn.execute(query).fetchall()

    out = []
    for c in candidates:
        if c["base_airport"] and c["destination"] == c["base_airport"]:
            continue

        gap_hours = max((c["next_timestamp"] - c["timestamp"]) / 3600.0, 0.1)
        distance_factor = 1.0
        try:
            b_lat, b_lon = get_airport_coordinates(c["base_airport"]) if c["base_airport"] else (None, None)
            d_lat, d_lon = get_airport_coordinates(c["destination"])
            if b_lat is not None:
                distance_factor = min(great_circle_nm(b_lat, b_lon, d_lat, d_lon) / 1000.0, 1.5)
        except Exception:
            pass

        probability = max(0.1, min(0.95, (1 / gap_hours) * 0.6 + distance_factor * 0.4))
        out.append(
            {
                "icao24": c["icao24"],
                "leg": f"{c['next_origin']}->{c['next_destination']}",
                "probability": round(probability, 3),
                "reason": "quick reposition after non-base stop",
            }
        )
    return out
