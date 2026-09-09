"""Loads event_study_results.json into a real SQLite database
(shock_module.db) per schema.sql, same pattern as sql/load_db.py for Phase 1."""
import sqlite3
import json
import os

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "shock_module.db")
RESULTS_JSON = os.path.join(HERE, "event_study_results.json")
SCHEMA_SQL = os.path.join(HERE, "schema.sql")

FX_TICKERS = {"LBN": "LBP=X", "LKA": "LKR=X", "AFG": "AFN=X", "EGY": "EGP=X", "PAK": "PKR=X"}

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
with open(SCHEMA_SQL) as f:
    conn.executescript(f.read())

with open(RESULTS_JSON) as f:
    results = json.load(f)

for r in results:
    conn.execute(
        "INSERT INTO shock_events (country_code, event_date, label, source) VALUES (?, ?, ?, ?)",
        (r["country_code"], r["event_date"], r["label"], "shock_events.py"),
    )
    conn.execute(
        "INSERT INTO gdelt_signal (country_code, event_date, avg_tone_post_7d, peak_volume_post_7d) VALUES (?, ?, ?, ?)",
        (r["country_code"], r["event_date"], r["gdelt_avg_tone_post"], r["gdelt_peak_volume_post"]),
    )
    ticker = FX_TICKERS.get(r["country_code"])
    if ticker and r["fx_pct_change"] is not None:
        conn.execute(
            "INSERT INTO fx_reaction (country_code, event_date, ticker, fx_pct_change) VALUES (?, ?, ?, ?)",
            (r["country_code"], r["event_date"], ticker, r["fx_pct_change"]),
        )

conn.commit()
n = conn.execute("SELECT COUNT(*) FROM event_study_panel").fetchone()[0]
print(f"Database built: {DB_PATH} -- event_study_panel view: {n} rows")
conn.close()
