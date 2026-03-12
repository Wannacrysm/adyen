"""Charter price estimation from route + repositioning requirements."""
from __future__ import annotations

from .routing_engine import get_airport_coordinates, great_circle_nm


def estimate_charter_price(
    cruise_speed_kts: float,
    hourly_cost: float,
    origin: str,
    destination: str,
    aircraft_lat: float,
    aircraft_lon: float,
    crew_buffer: float = 0.15,
    fuel_buffer: float = 0.18,
) -> dict:
    o_lat, o_lon = get_airport_coordinates(origin)
    d_lat, d_lon = get_airport_coordinates(destination)
    route_nm = great_circle_nm(o_lat, o_lon, d_lat, d_lon)
    reposition_nm = great_circle_nm(o_lat, o_lon, aircraft_lat, aircraft_lon)

    total_nm = route_nm + reposition_nm
    flight_hours = total_nm / max(cruise_speed_kts, 1)
    base_cost = flight_hours * hourly_cost
    crew_cost = base_cost * crew_buffer
    fuel_est = base_cost * fuel_buffer

    return {
        "route_nm": round(route_nm, 2),
        "reposition_nm": round(reposition_nm, 2),
        "flight_hours": round(flight_hours, 2),
        "base_cost": round(base_cost, 2),
        "crew_cost_buffer": round(crew_cost, 2),
        "fuel_burn_estimate": round(fuel_est, 2),
        "total_estimated_cost": round(base_cost + crew_cost + fuel_est, 2),
    }
