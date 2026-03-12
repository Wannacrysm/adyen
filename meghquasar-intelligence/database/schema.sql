PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS aircraft_states (
    icao24 TEXT PRIMARY KEY,
    callsign TEXT,
    latitude REAL,
    longitude REAL,
    altitude REAL,
    velocity REAL,
    heading REAL,
    last_seen INTEGER,
    source_reference TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS global_aircraft_registry (
    registration TEXT PRIMARY KEY,
    icao24 TEXT,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    country TEXT,
    source_reference TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS aircraft_specs (
    model TEXT PRIMARY KEY,
    category TEXT,
    range_nm REAL,
    seats INTEGER,
    cruise_speed REAL,
    hourly_cost REAL,
    source_reference TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT,
    base_airport TEXT,
    source_reference TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operator_fleet (
    operator_id INTEGER NOT NULL,
    aircraft_model TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (operator_id, aircraft_model),
    FOREIGN KEY (operator_id) REFERENCES operators(id),
    FOREIGN KEY (aircraft_model) REFERENCES aircraft_specs(model)
);

CREATE TABLE IF NOT EXISTS flight_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    icao24 TEXT NOT NULL,
    origin TEXT,
    destination TEXT,
    timestamp INTEGER,
    source_reference TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_states_last_seen ON aircraft_states(last_seen);
CREATE INDEX IF NOT EXISTS idx_registry_icao24 ON global_aircraft_registry(icao24);
CREATE INDEX IF NOT EXISTS idx_history_icao24_time ON flight_history(icao24, timestamp);
