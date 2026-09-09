-- Phase 2 (shock module) database schema (SQLite) -- same normalized
-- pattern as sql/schema.sql for Phase 1, now covering the shock events,
-- their real GDELT signal, and the real FX reaction that followed.

CREATE TABLE shock_events (
    country_code TEXT NOT NULL,
    event_date TEXT NOT NULL,          -- ISO date, the real event day
    label TEXT NOT NULL,
    source TEXT,                       -- how the date/event was sourced
    PRIMARY KEY (country_code, event_date)
);

CREATE TABLE gdelt_signal (
    country_code TEXT NOT NULL,
    event_date TEXT NOT NULL,
    avg_tone_post_7d REAL,             -- average GDELT tone, 7 days after the event
    peak_volume_post_7d REAL,          -- peak GDELT coverage volume, 7 days after
    FOREIGN KEY (country_code, event_date) REFERENCES shock_events(country_code, event_date),
    PRIMARY KEY (country_code, event_date)
);

CREATE TABLE fx_reaction (
    country_code TEXT NOT NULL,
    event_date TEXT NOT NULL,
    ticker TEXT NOT NULL,              -- the yfinance ticker used (e.g. "LKR=X")
    fx_pct_change REAL,                -- % change, pre-event 7d avg -> post-event 21d avg
    FOREIGN KEY (country_code, event_date) REFERENCES shock_events(country_code, event_date),
    PRIMARY KEY (country_code, event_date)
);

CREATE VIEW event_study_panel AS
SELECT
    s.country_code, s.event_date, s.label,
    g.avg_tone_post_7d, g.peak_volume_post_7d,
    f.ticker, f.fx_pct_change
FROM shock_events s
LEFT JOIN gdelt_signal g ON s.country_code = g.country_code AND s.event_date = g.event_date
LEFT JOIN fx_reaction f ON s.country_code = f.country_code AND s.event_date = f.event_date;
