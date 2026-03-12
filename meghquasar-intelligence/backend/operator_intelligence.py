"""Operator management; never fabricate unknown operator identities."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "meghquasar.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_operator(name: str | None, country: str | None, base_airport: str | None, source_reference: str) -> int:
    safe_name = name or "unknown"
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO operators (name, country, base_airport, source_reference) VALUES (?, ?, ?, ?)",
            (safe_name, country, base_airport, source_reference),
        )
    return int(cur.lastrowid)


def link_operator_fleet(operator_id: int, aircraft_model: str, source_reference: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO operator_fleet (operator_id, aircraft_model, source_reference)
            VALUES (?, ?, ?)
            ON CONFLICT(operator_id, aircraft_model) DO UPDATE SET source_reference=excluded.source_reference
            """,
            (operator_id, aircraft_model, source_reference),
        )


def list_operators_with_fleet() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT o.id, o.name, o.country, o.base_airport, f.aircraft_model
            FROM operators o
            LEFT JOIN operator_fleet f ON f.operator_id = o.id
            ORDER BY o.name
            """
        ).fetchall()
    return [dict(r) for r in rows]
