-- Phase 3 (forecast module) schema (SQLite) -- same normalized pattern as
-- the other two phases.

CREATE TABLE raw_macro_observations (
    country_code TEXT NOT NULL,
    year INTEGER NOT NULL,
    gdp_growth REAL,
    inflation REAL,
    PRIMARY KEY (country_code, year)
);

CREATE TABLE forecast_backtest_2024 (
    country_code TEXT NOT NULL,
    variable TEXT NOT NULL CHECK (variable IN ('gdp_growth', 'inflation')),
    forecast_2024 REAL,
    actual_2024 REAL,
    error REAL,
    abs_error REAL,
    PRIMARY KEY (country_code, variable)
);
