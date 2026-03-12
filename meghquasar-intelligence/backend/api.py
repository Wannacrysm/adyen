from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .empty_leg_detector import detect_empty_legs
from .price_engine import estimate_charter_price
from .routing_engine import find_feasible_aircraft, get_airport_coordinates, nearest_aircraft

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "meghquasar.db"

app = FastAPI(title="MeghQuasar Intelligence API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    schema = (ROOT / "database" / "schema.sql").read_text()
    with get_conn() as conn:
        conn.executescript(schema)


init_db()


@app.get("/api/aircraft/live")
def live_aircraft(limit: int = 3000):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT s.icao24, s.callsign, s.latitude, s.longitude, s.altitude, s.velocity, s.heading, s.last_seen,
                   r.model, r.registration
            FROM aircraft_states s
            LEFT JOIN global_aircraft_registry r ON r.icao24 = s.icao24
            WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
            ORDER BY s.last_seen DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/route/analyze")
def analyze_route(origin: str, destination: str):
    try:
        get_airport_coordinates(origin)
        get_airport_coordinates(destination)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    feasible = find_feasible_aircraft(origin, destination)
    nearest = nearest_aircraft(origin)
    empty_legs = detect_empty_legs()

    quote = None
    if feasible["aircraft"]:
        a = feasible["aircraft"][0]
        if a.get("cruise_speed") and a.get("hourly_cost") and a.get("latitude") is not None and a.get("longitude") is not None:
            quote = estimate_charter_price(
                cruise_speed_kts=a["cruise_speed"],
                hourly_cost=a["hourly_cost"],
                origin=origin,
                destination=destination,
                aircraft_lat=a["latitude"],
                aircraft_lon=a["longitude"],
            )

    return {
        "route": {"origin": origin.upper(), "destination": destination.upper(), "distance_nm": feasible["route_nm"]},
        "feasible_aircraft": feasible["aircraft"],
        "nearest_aircraft": nearest,
        "possible_empty_legs": empty_legs,
        "estimated_charter_price": quote,
    }


app.mount("/", StaticFiles(directory=str(ROOT / "frontend"), html=True), name="frontend")
