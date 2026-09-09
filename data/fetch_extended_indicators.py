"""
Extended World Bank WDI indicators for the risk-architecture upgrade pass --
external vulnerability, fiscal/sovereign, banking-sector, trade/commodity
dependency, and buffer-side factors that were NOT already in driver_history.csv.

Same 34-country set as driver_history.csv/panel.csv (verified identical
before writing this script). Same fetch pattern as the already-proven
overeign-risk-index/fetch_data.py (World Bank's public REST API, no key
required) -- reused deliberately rather than reinvented, to stay consistent
with a source this whole project family already validates against.

Real, disclosed limitation up front: World Bank WDI does not publish
sovereign bond yields, CDS spreads, or EMBI-style market spreads for any
country (confirmed by overeign-risk-index/market_signals.py's own prior
investigation, docstring point 4 -- a full scan of the WDI catalog turned up
nothing, and IMF's free public APIs don't cover market yields either). Those
are deliberately NOT fetched here; see the app's Methodology tab for the
disclosed reason. Real "market-implied risk" for this project instead comes
from real global market instruments (yfinance, see fetch_global_conditions.py)
and the existing S&P ratings benchmark (credit_ratings.py).

Bilateral trade / bank-sovereign nexus indicators (top trading partner,
bank holdings of government securities) were also investigated and left
out: bilateral trade needs UN Comtrade, which is real and reachable but
gated on a free subscription key nobody has registered for this project
(same gap overeign-risk-index/market_signals.py already disclosed for its
own Trade Vulnerability Index); bank sovereign-debt holdings are not a WDI
series at all. Both are named explicitly in the app rather than silently
skipped.
"""
import json
import subprocess
import time
from datetime import datetime, timezone

COUNTRIES = [
    "AFG", "ARE", "BGD", "BHR", "BTN", "DJI", "DZA", "EGY", "ERI", "ETH",
    "IND", "IRN", "IRQ", "ISR", "JOR", "KWT", "LBN", "LBY", "LKA", "MAR",
    "MDV", "NPL", "OMN", "PAK", "PSE", "QAT", "SAU", "SDN", "SOM", "SSD",
    "SYR", "TUN", "TUR", "YEM",
]

# ---- External vulnerability ----
EXTERNAL_INDICATORS = {
    "DT.DOD.DECT.GN.ZS": "external_debt_pct_gni",
    "DT.TDS.DECT.EX.ZS": "external_debt_service_pct_exports",
}

# ---- Fiscal / sovereign ----
FISCAL_INDICATORS = {
    "GC.NLD.TOTL.GD.ZS": "fiscal_balance_pct_gdp",
    "GC.XPN.INTP.RV.ZS": "interest_payments_pct_revenue",
}

# ---- Banking / financial-sector ----
BANKING_INDICATORS = {
    "FB.AST.NPER.ZS": "bank_npl_pct_loans",
    "FS.AST.PRVT.GD.ZS": "private_credit_pct_gdp",
}

# ---- Trade & commodity dependency ----
TRADE_INDICATORS = {
    "NE.EXP.GNFS.ZS": "exports_pct_gdp",
    "NE.IMP.GNFS.ZS": "imports_pct_gdp",
    "TX.VAL.FUEL.ZS.UN": "fuel_exports_pct_merch_exports",
    "TM.VAL.FOOD.ZS.UN": "food_imports_pct_merch_imports",
}

# ---- Capital flows / buffers ----
FLOWS_INDICATORS = {
    "BX.TRF.PWKR.DT.GD.ZS": "remittances_pct_gdp",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_net_inflows_pct_gdp",
}

# ---- Social / fragility (used as amplification context, not scored directly) ----
SOCIAL_INDICATORS = {
    "SL.UEM.TOTL.ZS": "unemployment_rate",
}

INDICATORS = {
    **EXTERNAL_INDICATORS, **FISCAL_INDICATORS, **BANKING_INDICATORS,
    **TRADE_INDICATORS, **FLOWS_INDICATORS, **SOCIAL_INDICATORS,
}

BASE_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
CURRENT_YEAR = datetime.now(timezone.utc).year


def fetch_indicator_series(country_code, indicator_code, retries=3):
    url = BASE_URL.format(country=country_code, indicator=indicator_code)
    full_url = f"{url}?format=json&date=2010:{CURRENT_YEAR}&per_page=100"

    result = None
    for attempt in range(retries):
        result = subprocess.run(
            ["curl", "-s", "-m", "15", full_url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout:
            break
        time.sleep(1)

    if result is None or result.returncode != 0 or not result.stdout:
        return {}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

    if len(data) < 2 or data[1] is None:
        return {}

    series = {}
    for entry in data[1]:
        if entry["value"] is not None:
            series[int(entry["date"])] = entry["value"]
    return series


def main():
    rows = []
    for code in COUNTRIES:
        for indicator_code, col_name in INDICATORS.items():
            series = fetch_indicator_series(code, indicator_code)
            for year, value in series.items():
                rows.append({
                    "country_code": code, "indicator": col_name,
                    "year": year, "value": value,
                })
            time.sleep(0.15)
        print(f"Fetched: {code}")

    import pandas as pd
    long_df = pd.DataFrame(rows)
    long_df.to_csv("extended_indicators_long.csv", index=False)

    # Wide panel: one row per country-year, one column per indicator --
    # matches driver_history.csv's shape so build_panel.py can merge on
    # (country_code, year) the same way it already merges raw_panel.csv.
    wide = long_df.pivot_table(
        index=["country_code", "year"], columns="indicator", values="value"
    ).reset_index()
    wide.to_csv("extended_indicators.csv", index=False)

    coverage = {
        col: int(wide[col].notna().sum())
        for col in INDICATORS.values() if col in wide.columns
    }
    print(f"\nSaved extended_indicators.csv ({len(wide)} country-year rows)")
    print("Non-missing coverage per indicator:")
    for col, n in coverage.items():
        print(f"  {col}: {n} / {len(wide)}")


if __name__ == "__main__":
    main()
