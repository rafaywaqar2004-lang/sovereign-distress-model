"""
Builds the single analysis panel this project's model is fit on.

Features (X): the same 11 World Bank / WGI factors already fetched, sourced,
and validated by the MENASA Risk Monitor -- but NOT simply driver_history.csv
verbatim. Real finding from a later audit: driver_history.csv's 5 economic
factors (current_account_pct_gdp, reserves_months_imports, gdp_growth,
inflation, currency_depreciation_pct) are normalized 0-100 risk sub-scores,
not the raw economic values their names imply -- the same mislabeling
already caught and fixed for Phase 3's forecasting model, but missed here
until this fix. The 5 governance/WGI factors (political_stability,
government_effectiveness, rule_of_law, regulatory_quality,
control_of_corruption) are correctly left on driver_history.csv's 0-100
scale -- that IS the real World Bank WGI percentile convention, not a bug.

So: governance factors come from driver_history.csv (unchanged); the 5
economic factors are swapped in from forecast-module/raw_panel.csv's real
raw values instead. Verified before this swap: identical missingness
pattern in both sources for all 5 economic columns (91/96/31/44/64 missing
respectively) -- this is a pure value-scale correction, not a change to
which country-years are included.

Outcome (Y): the real, sourced distress events in distress_events.py.

Output: panel.csv, one row per country-year, features + two binary outcome
columns (sovereign_default, imf_program_entry).
"""
import pandas as pd
from distress_events import build_distress_panel

GOV_COLS = [
    "political_stability", "government_effectiveness", "rule_of_law",
    "regulatory_quality", "control_of_corruption",
]
ECON_COLS = [
    "current_account_pct_gdp", "reserves_months_imports",
    "gdp_growth", "inflation", "currency_depreciation_pct",
]

driver = pd.read_csv("driver_history.csv")
raw = pd.read_csv("../forecast-module/raw_panel.csv")

before_missing = driver[ECON_COLS].isna().sum()
after_missing_check = raw.merge(driver[["country_code", "year"]], on=["country_code", "year"], how="inner")[ECON_COLS].isna().sum()
assert (before_missing == after_missing_check).all(), (
    "Missingness pattern differs between driver_history.csv and raw_panel.csv for the 5 economic factors -- "
    "the swap below assumes they're identical (verified separately before writing this script). If this "
    "assertion ever fails, investigate before proceeding; don't silently swap in a source with different coverage."
)

driver_gov_and_ids = driver.drop(columns=ECON_COLS)
raw_econ = raw[["country_code", "year"] + ECON_COLS]
merged_factors = driver_gov_and_ids.merge(raw_econ, on=["country_code", "year"], how="left")

# Restore driver_history.csv's original column order (cosmetic, keeps panel.csv diffing cleanly comparable to the prior version)
merged_factors = merged_factors[list(driver.columns)]

# ---------- Extended risk-architecture indicators (external debt, fiscal, ----------
# ---------- banking, trade -- fetched via data/fetch_extended_indicators.py) -------
# Optional: build_panel.py must keep working before that fetch has ever run
# (e.g. a fresh clone), so this merges in only if the file exists, and never
# fabricates a row or value when it doesn't.
import os
extended_path = "extended_indicators.csv"
if os.path.exists(extended_path):
    extended = pd.read_csv(extended_path)
    before_cols = set(merged_factors.columns)
    merged_factors = merged_factors.merge(extended, on=["country_code", "year"], how="left")
    new_cols = [c for c in merged_factors.columns if c not in before_cols]
    print(f"Merged extended indicators: {len(new_cols)} new columns ({', '.join(new_cols)})")
else:
    print(f"Note: {extended_path} not found -- run data/fetch_extended_indicators.py "
          f"(via GitHub Actions) to add external/fiscal/banking/trade indicators. "
          f"Continuing with the existing 11-factor panel only.")

country_years = list(zip(merged_factors["country_code"], merged_factors["year"]))
distress_rows = build_distress_panel(country_years)
distress = pd.DataFrame(distress_rows)

panel = merged_factors.merge(distress, on=["country_code", "year"], how="left")

assert len(panel) == len(merged_factors), "merge changed row count -- distress_events has a (country, year) not in the panel"
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
