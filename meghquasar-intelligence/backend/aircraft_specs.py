"""Load aircraft specs and classify business aviation capable models."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "meghquasar.db"
CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "aircraft_specs.csv"
SOURCE = "https://www.easa.europa.eu/en/domains/aircraft-products"
BUSINESS_CATEGORIES = {"business jet", "corporate turboprop", "private helicopter"}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_specs() -> int:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        records = list(csv.DictReader(f))

    rows = [
        (
            r["model"],
            r["category"].lower(),
            float(r["range_nm"]),
            int(r["seats"]),
            float(r["cruise_speed"]),
            float(r["hourly_cost"]),
            r.get("source_reference") or SOURCE,
        )
        for r in records
    ]

    with get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO aircraft_specs (model, category, range_nm, seats, cruise_speed, hourly_cost, source_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(model) DO UPDATE SET
              category=excluded.category,
              range_nm=excluded.range_nm,
              seats=excluded.seats,
              cruise_speed=excluded.cruise_speed,
              hourly_cost=excluded.hourly_cost,
              source_reference=excluded.source_reference;
            """,
            rows,
        )
    return len(rows)


def is_business_aviation(category: str | None) -> bool:
    if not category:
        return False
    return category.lower() in BUSINESS_CATEGORIES


if __name__ == "__main__":
    print(f"Loaded {load_specs()} aircraft specs")
