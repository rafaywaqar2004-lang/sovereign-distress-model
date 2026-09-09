"""Loads raw_panel.csv + backtest_2024_results.csv + shock_drivers.json +
stress_test_coefficients.csv into a real SQLite database
(forecast_module.db), same pattern as the other two phases."""
import sqlite3
import json
import pandas as pd
import os

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "forecast_module.db")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
with open(os.path.join(HERE, "schema.sql")) as f:
    conn.executescript(f.read())

panel = pd.read_csv(os.path.join(HERE, "raw_panel.csv"))
panel[["country_code", "year", "gdp_growth", "inflation"]].to_sql(
    "raw_macro_observations", conn, if_exists="append", index=False
)

backtest = pd.read_csv(os.path.join(HERE, "backtest_2024_results.csv"))
backtest[["country_code", "variable", "forecast_2024", "actual_2024", "error", "abs_error"]].to_sql(
    "forecast_backtest_2024", conn, if_exists="append", index=False
)

with open(os.path.join(HERE, "shock_drivers.json")) as f:
    drivers = json.load(f)
oil = drivers["oil_annual_avg_usd"]
rate = drivers["us_short_rate_annual_avg_pct"]
years = sorted(set(oil.keys()) | set(rate.keys()), key=int)
conn.executemany(
    "INSERT INTO shock_drivers (year, oil_annual_avg_usd, us_short_rate_annual_avg_pct) VALUES (?, ?, ?)",
    [(int(y), oil.get(y), rate.get(y)) for y in years],
)

coefs = pd.read_csv(os.path.join(HERE, "stress_test_coefficients.csv"))
coefs.to_sql("stress_test_coefficients", conn, if_exists="append", index=False)

conn.commit()
n1 = conn.execute("SELECT COUNT(*) FROM raw_macro_observations").fetchone()[0]
n2 = conn.execute("SELECT COUNT(*) FROM forecast_backtest_2024").fetchone()[0]
n3 = conn.execute("SELECT COUNT(*) FROM shock_drivers").fetchone()[0]
n4 = conn.execute("SELECT COUNT(*) FROM stress_test_coefficients").fetchone()[0]
print(f"Database built: {DB_PATH}")
print(f"  raw_macro_observations: {n1}")
print(f"  forecast_backtest_2024: {n2}")
print(f"  shock_drivers: {n3}")
print(f"  stress_test_coefficients: {n4}")
conn.close()
