"""
Country trade/development profile helpers for the Trade & Infrastructure
tab -- turns the raw fetched CSVs (data/trade_commodities.csv,
data/development_indicators.csv) into per-country summaries the app can
render directly. Degrades to "not available" (never fabricated) for any
country/indicator the real fetch hasn't produced -- same discipline as
trade_network.py.
"""
import os

import pandas as pd

from hs_chapters import HS2_CHAPTERS


def load_trade_commodities(path="../data/trade_commodities.csv"):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, dtype={"hs2_code": str})


def top_commodities(df, country_code, flow, n=5):
    """Real top-N HS2 export or import categories for one country, by
    actual Comtrade USD value. Returns (year, [{code, label, value_usd,
    pct_of_total}]) or (None, []) if this country has no real commodity
    data (e.g. its Comtrade fetch failed/is a non-reporter)."""
    if df is None:
        return None, []
    sub = df[(df["reporter_code"] == country_code) & (df["flow"] == flow)]
    if sub.empty:
        return None, []
    year = int(sub["year"].iloc[0])
    total = sub["value_usd"].sum()
    top = sub.sort_values("value_usd", ascending=False).head(n)
    out = []
    for _, row in top.iterrows():
        code = str(row["hs2_code"]).zfill(2)
        out.append({
            "code": code,
            "label": HS2_CHAPTERS.get(code, f"HS chapter {code}"),
            "value_usd": float(row["value_usd"]),
            "pct_of_total": 100.0 * row["value_usd"] / total if total else None,
        })
    return year, out


def load_development_indicators(path="../data/development_indicators.csv"):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def latest_indicator(df, country_code, indicator_col):
    """Latest real non-missing (year, value) for one WDI indicator/country,
    or (None, None) if this country never reported it."""
    if df is None or indicator_col not in df.columns:
        return None, None
    sub = df.loc[df["country_code"] == country_code, ["year", indicator_col]].dropna()
    if sub.empty:
        return None, None
    row = sub.sort_values("year").iloc[-1]
    return int(row["year"]), float(row[indicator_col])


DEV_INDICATOR_LABELS = {
    "gdp_per_capita_usd": ("GDP per capita", "$"),
    "gni_per_capita_atlas_usd": ("GNI per capita (Atlas method)", "$"),
    "population": ("Population", ""),
    "life_expectancy_years": ("Life expectancy", " yrs"),
    "access_to_electricity_pct": ("Access to electricity", "%"),
    "internet_users_pct": ("Internet users", "%"),
    "urban_population_pct": ("Urban population", "%"),
}

SECTOR_INDICATOR_LABELS = {
    "agriculture_pct_gdp": "Agriculture",
    "industry_pct_gdp": "Industry",
    "manufacturing_pct_gdp": "of which: Manufacturing",
    "services_pct_gdp": "Services",
}

DEBT_COMPOSITION_LABELS = {
    "external_debt_multilateral_usd": "Multilateral institutions (IMF, World Bank, etc.)",
    "external_debt_bilateral_usd": "Bilateral (official, government-to-government)",
    "external_debt_private_creditors_usd": "Private creditors",
    "external_debt_bonds_usd": "of which: Bonds",
}
