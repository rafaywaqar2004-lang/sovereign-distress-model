"""
Builds the single analysis panel this project's model is fit on.

Features (X): the same 11 World Bank / WGI factors already fetched, sourced,
and validated by the MENASA Risk Monitor (driver_history.csv, copied
directly from that project -- same official World Bank API pull, same 34
countries, same 2010-2024 coverage. Not re-fetched here to avoid drifting
from the already-validated source).

Outcome (Y): the real, sourced distress events in distress_events.py.

Output: panel.csv, one row per country-year, features + two binary outcome
columns (sovereign_default, imf_program_entry).
"""
import pandas as pd
from distress_events import build_distress_panel

driver = pd.read_csv("driver_history.csv")

country_years = list(zip(driver["country_code"], driver["year"]))
distress_rows = build_distress_panel(country_years)
distress = pd.DataFrame(distress_rows)

panel = driver.merge(distress, on=["country_code", "year"], how="left")

assert len(panel) == len(driver), "merge changed row count -- distress_events has a (country, year) not in the panel"
assert panel["sovereign_default"].isna().sum() == 0, "unmatched country-years in sovereign_default"

panel.to_csv("panel.csv", index=False)

n_default = int(panel["sovereign_default"].sum())
n_program = int(panel["imf_program_entry"].sum())
n_total = len(panel)

print(f"Panel built: {n_total} country-year observations")
print(f"  sovereign_default = 1 in {n_default} of {n_total} rows ({n_default/n_total:.1%})")
print(f"  imf_program_entry = 1 in {n_program} of {n_total} rows ({n_program/n_total:.1%})")
print()
print("Honest note: both outcome rates are low (rare-event data), which is a")
print("real statistical constraint on this model, not a data-quality issue --")
print("this is disclosed explicitly in the model's own README/limitations.")
