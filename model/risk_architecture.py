"""
Interpretable sub-indices (mega-prompt Sections 5/6/8/19/20) -- descriptive
diagnostic breakdowns of real exposure, NOT a new composite score competing
with the actual fitted logit model. This project's own established
methodology (see README) is explicit that risk isn't a weighted composite --
it's Phase 1's fitted logistic regression. These sub-indices exist to answer
"which real dimension is this country's risk coming from," using the same
direction-aware percentile machinery as peer_comparison.py, not to produce a
second, competing probability.

Double-counting avoided by construction (Section 30): each real indicator
appears in exactly ONE sub-index below. reserves_months_imports, in
particular, is scored only under BUFFER (protective capacity), not also
under external vulnerability, since "high reserves = low vulnerability" and
"high reserves = strong buffer" are the same real fact counted once, not
twice with opposite signs.

private_credit_pct_gdp and fuel_exports_pct_merch_exports are deliberately
left OUT of every scored sub-index -- both have genuinely ambiguous risk
direction (deeper credit markets can mean either financial development or
credit-boom fragility; commodity export concentration is a risk for some
countries and irrelevant for net importers) and are shown as descriptive
context only, per the mega-prompt's own Section 10 instruction not to force
an indicator into every country's score when its relevance is conditional.
"""
import pandas as pd

from peer_comparison import DIRECTION, latest_value_per_country, peer_percentiles

SUB_INDICES = {
    "external_vulnerability": [
        "current_account_pct_gdp", "external_debt_pct_gni",
        "external_debt_service_pct_exports",
    ],
    "fiscal_sovereign": [
        "debt_to_gdp", "fiscal_balance_pct_gdp", "interest_payments_pct_revenue",
    ],
    "banking_sector": [
        "bank_npl_pct_loans",
    ],
    "macro_conditions": [
        "gdp_growth", "inflation", "currency_depreciation_pct",
    ],
    "institutional": [
        "political_stability", "government_effectiveness", "rule_of_law",
        "regulatory_quality", "control_of_corruption",
    ],
    # BUFFER factors are protective -- scored the same direction-aware way,
    # then reported as "buffer strength" (100 - risk percentile) so a higher
    # number always reads as MORE resilience, never more risk.
    "buffers": [
        "reserves_months_imports", "remittances_pct_gdp", "fdi_net_inflows_pct_gdp",
    ],
}

CONTEXT_ONLY = ["private_credit_pct_gdp", "fuel_exports_pct_merch_exports",
                "food_imports_pct_merch_imports", "unemployment_rate",
                "exports_pct_gdp", "imports_pct_gdp"]


def build_sub_indices(latest_df):
    """latest_df: one row per country_code with the raw latest-available
    value for every factor referenced in SUB_INDICES (output of
    latest_value_per_country on the merged panel). Returns a DataFrame with
    one column per sub-index (0-100, higher = more of that dimension's
    risk, except *_buffer_strength which is inverted so higher = more
    resilient), plus each sub-index's real component coverage (how many of
    its factors were actually non-missing for that country -- disclosed,
    not hidden, since thin coverage should read as thin, not confidently
    wrong)."""
    all_cols = [c for cols in SUB_INDICES.values() for c in cols]
    pctiles = peer_percentiles(latest_df, all_cols)

    out = latest_df[["country_code"]].copy()
    for name, cols in SUB_INDICES.items():
        pct_cols = [f"{c}_pctile" for c in cols if f"{c}_pctile" in pctiles.columns]
        merged = pctiles.set_index("country_code")[pct_cols]
        coverage = merged.notna().sum(axis=1)
        score = merged.mean(axis=1, skipna=True)
        if name == "buffers":
            score = 100 - score
            out[f"{name}_strength"] = out["country_code"].map(score)
        else:
            out[f"{name}_risk"] = out["country_code"].map(score)
        out[f"{name}_coverage"] = out["country_code"].map(coverage).astype("Int64")
        out[f"{name}_of"] = len(cols)
    return out


if __name__ == "__main__":
    panel = pd.read_csv("../data/panel.csv")
    try:
        ext = pd.read_csv("../data/extended_indicators.csv")
        merged = panel.merge(ext, on=["country_code", "year"], how="left")
        print(f"Merged extended indicators: {len(ext)} extended rows -> {len(merged)} panel rows")
    except FileNotFoundError:
        merged = panel
        print("extended_indicators.csv not yet fetched -- running on existing panel factors only "
              "(external_vulnerability/fiscal_sovereign/banking_sector sub-indices will show as "
              "0-coverage until the GitHub Actions fetch completes).")

    all_cols = [c for cols in SUB_INDICES.values() for c in cols]
    latest = latest_value_per_country(merged, all_cols)
    result = build_sub_indices(latest)
    print(f"\nSub-indices computed for {len(result)} countries.")
    print(result.to_string(index=False))
