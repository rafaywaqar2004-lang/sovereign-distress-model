"""
Loads panel.csv + distress_events.py into a real SQLite database
(sovereign_distress.db) per the schema in schema.sql.
"""
import sqlite3
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
from distress_events import SOVEREIGN_DEFAULTS, IMF_PROGRAM_ENTRY  # noqa: E402

# Same 34-country set as the MENASA Risk Monitor this project shares its
# panel with (overeign-risk-index/fetch_data.py's COUNTRIES dict).
COUNTRIES = {
    "DZA": "Algeria", "BHR": "Bahrain", "EGY": "Egypt", "IRN": "Iran",
    "IRQ": "Iraq", "ISR": "Israel", "JOR": "Jordan", "KWT": "Kuwait",
    "LBN": "Lebanon", "LBY": "Libya", "MAR": "Morocco", "OMN": "Oman",
    "PSE": "Palestine", "QAT": "Qatar", "SAU": "Saudi Arabia", "SYR": "Syria",
    "TUN": "Tunisia", "ARE": "UAE", "YEM": "Yemen", "AFG": "Afghanistan",
    "BGD": "Bangladesh", "BTN": "Bhutan", "IND": "India", "MDV": "Maldives",
    "NPL": "Nepal", "PAK": "Pakistan", "LKA": "Sri Lanka", "TUR": "Turkey",
    "SDN": "Sudan", "SSD": "South Sudan", "ETH": "Ethiopia", "SOM": "Somalia",
    "DJI": "Djibouti", "ERI": "Eritrea",
}

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "sovereign_distress.db")
PANEL_CSV = os.path.join(HERE, "..", "data", "panel.csv")
SCHEMA_SQL = os.path.join(HERE, "schema.sql")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
with open(SCHEMA_SQL) as f:
    conn.executescript(f.read())

conn.executemany(
    "INSERT INTO countries (country_code, country_name) VALUES (?, ?)",
    list(COUNTRIES.items()),
)

FACTOR_COLS = [
    "debt_to_gdp", "current_account_pct_gdp", "reserves_months_imports",
    "gdp_growth", "inflation", "currency_depreciation_pct",
    "political_stability", "government_effectiveness", "rule_of_law",
    "regulatory_quality", "control_of_corruption",
]

with open(PANEL_CSV) as f:
    reader = csv.DictReader(f)
    rows = [
        (row["country_code"], int(row["year"]), *[
            (float(row[c]) if row[c] not in ("", "NA", "nan") else None)
            for c in FACTOR_COLS
        ])
        for row in reader
    ]

placeholders = ", ".join(["?"] * (2 + len(FACTOR_COLS)))
conn.executemany(
    f"INSERT INTO macro_observations (country_code, year, {', '.join(FACTOR_COLS)}) "
    f"VALUES ({placeholders})",
    rows,
)

for d in SOVEREIGN_DEFAULTS:
    conn.execute(
        "INSERT INTO distress_events (country_code, year, event_type, detail) VALUES (?, ?, ?, ?)",
        (d["country_code"], d["year"], "sovereign_default", d["event"]),
    )

for code, year, program_type, approved in IMF_PROGRAM_ENTRY:
    conn.execute(
        "INSERT INTO distress_events (country_code, year, event_type, detail) VALUES (?, ?, ?, ?)",
        (code, year, "imf_program_entry", f"{program_type}, approved {approved}"),
    )

conn.commit()

n_countries = conn.execute("SELECT COUNT(*) FROM countries").fetchone()[0]
n_obs = conn.execute("SELECT COUNT(*) FROM macro_observations").fetchone()[0]
n_events = conn.execute("SELECT COUNT(*) FROM distress_events").fetchone()[0]
n_view = conn.execute("SELECT COUNT(*) FROM analysis_panel").fetchone()[0]

print(f"Database built: {DB_PATH}")
print(f"  countries: {n_countries}")
print(f"  macro_observations: {n_obs}")
print(f"  distress_events: {n_events}")
print(f"  analysis_panel view: {n_view} rows")

conn.close()
