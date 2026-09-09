"""
Peer-relative risk (mega-prompt Section 21) and risk attribution / "what
changed" (Section 22) -- both pure computation on real data already fetched,
no new source needed. Works on whatever wide panel is passed in (the
existing 10-factor panel today; designed to take the extended
external/fiscal/banking/trade indicators once fetched, via the same
DIRECTION dict pattern below).

DIRECTION says whether a HIGHER raw value means MORE risk (True) or LESS
risk (False) for each factor -- needed so percentile rank means the same
thing ("higher percentile = more exposed") across factors with opposite
economic signs (e.g. higher inflation is worse, higher reserves is better).
This is a real methodological choice, stated explicitly rather than left
implicit, per the mega-prompt's own repeated instruction to disclose risk
direction for every indicator.
"""
import pandas as pd

DIRECTION = {
    # Existing Phase 1 factors
    "current_account_pct_gdp": False,       # more negative (deficit) = worse -> higher value = less risk
    "reserves_months_imports": False,       # more reserves = less risk
    "gdp_growth": False,                    # more growth = less risk
    "inflation": True,                      # more inflation = more risk
    "currency_depreciation_pct": True,      # more depreciation = more risk
    # These 5 columns are named after governance QUALITY but this dataset's
    # actual values run the opposite way -- verified directly against raw
    # data: Yemen/Syria (objectively poor governance) score ~90-100, Qatar/
    # Israel (relatively strong governance) score ~10-20. Confirmed against
    # Phase 1's own already-validated model too: its fitted coefficient on
    # political_stability is POSITIVE (0.0691, p<0.0001), i.e. a higher raw
    # value here genuinely increases predicted distress risk. So HIGHER =
    # MORE risk for all 5 -- caught during sub-index validation (see
    # validate_sub_indices.py), not assumed the way an earlier version of
    # this dict had it (backwards, direction=False).
    "political_stability": True,
    "government_effectiveness": True,
    "rule_of_law": True,
    "regulatory_quality": True,
    "control_of_corruption": True,
    "debt_to_gdp": True,
    # Extended indicators (used once fetched/merged)
    "external_debt_pct_gni": True,
    "external_debt_service_pct_exports": True,
    "fiscal_balance_pct_gdp": False,        # more negative deficit = worse
    "interest_payments_pct_revenue": True,
    "bank_npl_pct_loans": True,
    "private_credit_pct_gdp": False,        # deeper credit markets = generally a buffer, not scored as pure risk
    "exports_pct_gdp": False,               # more trade openness = more buffer, all else equal
    "imports_pct_gdp": False,
    "fuel_exports_pct_merch_exports": None, # ambiguous sign (exporter concentration risk vs. importer dependence) -- context only, not percentile-scored
    "food_imports_pct_merch_imports": True,
    "remittances_pct_gdp": False,           # a real external buffer
    "fdi_net_inflows_pct_gdp": False,
    "unemployment_rate": True,
}


def latest_value_per_country(df, factor_cols, id_cols=("country_code", "year")):
    """One row per country: its most recent non-missing year, per factor
    (factors can have different latest-available years -- each is picked
    independently, same convention as overeign-risk-index's own wide table)."""
    country_col, year_col = id_cols
    rows = []
    for code, g in df.groupby(country_col):
        g = g.sort_values(year_col)
        row = {country_col: code}
        for col in factor_cols:
            sub = g.dropna(subset=[col])
            if sub.empty:
                row[col] = None
                row[f"{col}_year"] = None
            else:
                row[col] = sub.iloc[-1][col]
                row[f"{col}_year"] = int(sub.iloc[-1][year_col])
        rows.append(row)
    return pd.DataFrame(rows)


def peer_percentiles(latest_df, factor_cols):
    """Percentile rank (0-100) of each country's latest value among all
    countries with a non-missing value for that factor -- oriented so
    HIGHER percentile always means MORE relative risk, using DIRECTION.
    Factors with DIRECTION=None (ambiguous sign) are skipped."""
    out = latest_df[["country_code"]].copy()
    for col in factor_cols:
        direction = DIRECTION.get(col)
        if direction is None or col not in latest_df.columns:
            continue
        vals = latest_df[col]
        pct = vals.rank(pct=True, ascending=direction) * 100
        out[f"{col}_pctile"] = pct
    return out


def what_changed(df, factor_cols, id_cols=("country_code", "year")):
    """Real year-over-year change in each factor's latest two available
    years per country, signed so POSITIVE always means risk went UP (per
    DIRECTION). Returns long-format rows: country, factor, delta_raw,
    risk_direction_delta, from_year, to_year."""
    country_col, year_col = id_cols
    rows = []
    for code, g in df.groupby(country_col):
        g = g.sort_values(year_col)
        for col in factor_cols:
            direction = DIRECTION.get(col)
            if direction is None or col not in g.columns:
                continue
            sub = g.dropna(subset=[col])
            if len(sub) < 2:
                continue
            prev_row, last_row = sub.iloc[-2], sub.iloc[-1]
            raw_delta = last_row[col] - prev_row[col]
            risk_delta = raw_delta if direction else -raw_delta
            rows.append({
                "country_code": code, "factor": col,
                "from_year": int(prev_row[year_col]), "to_year": int(last_row[year_col]),
                "raw_delta": raw_delta, "risk_direction_delta": risk_delta,
            })
    return pd.DataFrame(rows)


def top_movers(changed_df, country_code, n=5):
    """Top N factors pushing risk UP and top N pushing risk DOWN for one
    country's most recent real year-over-year change."""
    sub = changed_df[changed_df["country_code"] == country_code]
    worsening = sub.sort_values("risk_direction_delta", ascending=False).head(n)
    improving = sub.sort_values("risk_direction_delta", ascending=True).head(n)
    return worsening, improving


if __name__ == "__main__":
    panel = pd.read_csv("../data/panel.csv")
    factor_cols = [
        "current_account_pct_gdp", "reserves_months_imports", "gdp_growth",
        "inflation", "currency_depreciation_pct", "political_stability",
        "government_effectiveness", "rule_of_law", "regulatory_quality",
        "control_of_corruption",
    ]
    latest = latest_value_per_country(panel, factor_cols)
    pctiles = peer_percentiles(latest, factor_cols)
    changed = what_changed(panel, factor_cols)

    print(f"Peer percentiles computed for {len(pctiles)} countries.")
    print(pctiles.head(3).to_string())

    print(f"\nReal year-over-year changes computed: {len(changed)} factor-country observations.")
    example_country = latest["country_code"].iloc[0]
    worsening, improving = top_movers(changed, example_country)
    print(f"\nExample -- {example_country} top worsening factors:")
    print(worsening[["factor", "from_year", "to_year", "risk_direction_delta"]].to_string(index=False))
