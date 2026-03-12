"""Registry ingestion module.

Supports loading registry records from CSV/JSON sources with explicit source references.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).resolve().parents[1] / "meghquasar.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ingest_registry_csv(path: str, source_reference: str) -> int:
    file_path = Path(path)
    with file_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    payload = [
        (
            r.get("registration"),
            r.get("icao24"),
            r.get("manufacturer"),
            r.get("model"),
            r.get("serial_number"),
            r.get("country"),
            r.get("source_reference") or source_reference,
        )
        for r in rows
        if r.get("registration")
    ]

    with get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO global_aircraft_registry
             (registration, icao24, manufacturer, model, serial_number, country, source_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(registration) DO UPDATE SET
              icao24=excluded.icao24,
              manufacturer=excluded.manufacturer,
              model=excluded.model,
              serial_number=excluded.serial_number,
              country=excluded.country,
              source_reference=excluded.source_reference;
            """,
            payload,
        )
    return len(payload)


def bulk_insert_flight_history(records: Iterable[dict], source_reference: str) -> int:
    rows = [
        (
            r.get("icao24"),
            r.get("origin"),
            r.get("destination"),
            r.get("timestamp"),
            r.get("source_reference") or source_reference,
        )
        for r in records
        if r.get("icao24")
    ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO flight_history (icao24, origin, destination, timestamp, source_reference) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
    return len(rows)
