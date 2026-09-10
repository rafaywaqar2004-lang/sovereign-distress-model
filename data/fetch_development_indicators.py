"""
Real core development indicators for this project's 34 tracked countries --
the standard "how developed/what does the economy look like" series that
weren't already fetched for the sovereign-distress model itself (which
deliberately stuck to distress-relevant macro/fiscal/governance factors).
Same 34-country set, same already-proven World Bank WDI REST API pattern
as fetch_extended_indicators.py (no key required) -- reused, not
reinvented.

Two groups:
  - DEV_INDICATORS: income level, human development, and connectivity --
    GDP per capita, GNI per capita (Atlas method, the World Bank's own
    income-classification basis), life expectancy, access to electricity,
    internet use, urbanization, population.
  - SECTOR_INDICATORS: value-added share of GDP by broad sector
    (agriculture / industry / manufacturing / services) -- the real,
    honest proxy this project uses for "main industries operating": WDI
    does not publish a literal list of companies or named industries per
    country, so sector GDP-share composition (paired in the app with each
    country's real top Comtrade export categories) is the defensible real
    substitute, not a fabricated industry list.
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

DEV_INDICATORS = {
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
    "NY.GNP.PCAP.CD": "gni_per_capita_atlas_usd",
    "SP.POP.TOTL": "population",
    "SP.DYN.LE00.IN": "life_expectancy_years",
    "EG.ELC.ACCS.ZS": "access_to_electricity_pct",
    "IT.NET.USER.ZS": "internet_users_pct",
    "SP.URB.TOTL.IN.ZS": "urban_population_pct",
}

SECTOR_INDICATORS = {
    "NV.AGR.TOTL.ZS": "agriculture_pct_gdp",
    "NV.IND.TOTL.ZS": "industry_pct_gdp",
    "NV.IND.MANF.ZS": "manufacturing_pct_gdp",
    "NV.SRV.TOTL.ZS": "services_pct_gdp",
}

# External debt STOCK composition by broad creditor category -- WDI's real
# International Debt Statistics series. This is the honest limit of what a
# live, free, no-key source actually publishes: a breakdown by creditor
# TYPE (multilateral institutions / official bilateral governments /
# private bondholders / commercial banks), not by individual creditor
# COUNTRY. WDI does not publish a "X% owed specifically to China" style
# figure -- that level of granularity lives in the World Bank's separate
# International Debt Statistics (IDS) query database (a different, more
# complex API than this project's other fetches), not attempted here.
# Disclosed explicitly in the app rather than silently only fetching the
# category breakdown and implying it's the full picture.
DEBT_COMPOSITION_INDICATORS = {
    "DT.DOD.DECT.CD": "external_debt_stock_total_usd",
    "DT.DOD.DPPG.CD": "external_debt_public_publicly_guaranteed_usd",
    "DT.DOD.DPNG.CD": "external_debt_private_nonguaranteed_usd",
    "DT.DOD.MLAT.CD": "external_debt_multilateral_usd",
    "DT.DOD.BLAT.CD": "external_debt_bilateral_usd",
    "DT.DOD.PRVT.CD": "external_debt_private_creditors_usd",
    "DT.DOD.PBND.CD": "external_debt_bonds_usd",
}

INDICATORS = {**DEV_INDICATORS, **SECTOR_INDICATORS, **DEBT_COMPOSITION_INDICATORS}

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
    long_df.to_csv("development_indicators_long.csv", index=False)

    wide = long_df.pivot_table(
        index=["country_code", "year"], columns="indicator", values="value"
    ).reset_index()
    wide.to_csv("development_indicators.csv", index=False)

    coverage = {
        col: int(wide[col].notna().sum())
        for col in INDICATORS.values() if col in wide.columns
    }
    print(f"\nSaved development_indicators.csv ({len(wide)} country-year rows)")
    print("Non-missing coverage per indicator:")
    for col, n in coverage.items():
        print(f"  {col}: {n} / {len(wide)}")


if __name__ == "__main__":
    main()
