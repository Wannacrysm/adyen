"""Global telemetry ingestion using OpenSky Network states endpoint."""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Iterable, List

import requests

DB_PATH = Path(__file__).resolve().parents[1] / "meghquasar.db"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
OPENSKY_URL = "https://opensky-network.org/api/states/all"
SOURCE = OPENSKY_URL


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


def fetch_states() -> List[list]:
    user = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")
    auth = (user, password) if user and password else None
    response = requests.get(OPENSKY_URL, auth=auth, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("states", [])


def upsert_states(states: Iterable[list]) -> int:
    rows = []
    for state in states:
        icao24 = state[0]
        if not icao24:
            continue
        rows.append(
            (
                icao24.strip(),
                (state[1] or "").strip() or None,
                state[6],
                state[5],
                state[7],
                state[9],
                state[10],
                state[4],
                SOURCE,
            )
        )

    query = """
    INSERT INTO aircraft_states
      (icao24, callsign, latitude, longitude, altitude, velocity, heading, last_seen, source_reference, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(icao24) DO UPDATE SET
      callsign=excluded.callsign,
      latitude=excluded.latitude,
      longitude=excluded.longitude,
      altitude=excluded.altitude,
      velocity=excluded.velocity,
      heading=excluded.heading,
      last_seen=excluded.last_seen,
      source_reference=excluded.source_reference,
      updated_at=CURRENT_TIMESTAMP;
    """
    with get_conn() as conn:
        conn.executemany(query, rows)
    return len(rows)


def run_poll(interval_seconds: int = 30) -> None:
    init_db()
    while True:
        try:
            states = fetch_states()
            ingested = upsert_states(states)
            print(f"Ingested/updated {ingested} aircraft states")
        except Exception as exc:  # noqa: BLE001
            print(f"Telemetry poll failed: {exc}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_poll()
