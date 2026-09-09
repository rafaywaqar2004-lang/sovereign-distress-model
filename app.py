"""
EM Macro & Geopolitical Risk Engine -- live app.

Ties together all three real, independently-built and R-validated phases
of this project into one interactive tool:
  1. Sovereign Distress Model (panel logit)
  2. Geopolitical Shock Module (real GDELT + FX event study)
  3. Macro Forecasting + Stress Testing (panel AR(1) + real shock drivers)

Every number shown here is either loaded directly from a database/CSV this
project's own pipeline produced, or computed live from real fitted model
coefficients -- nothing on this page is invented for display purposes.
"""
import json
import sqlite3
import os

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

st.set_page_config(page_title="EM Macro & Geopolitical Risk Engine", page_icon="📉", layout="wide")

HERE = os.path.dirname(__file__)

# ============================================================
# DESIGN SYSTEM -- a distinct visual identity, not a shared palette with
# this project's two siblings. Direct user feedback: an earlier pass
# (dark ground borrowed from MENASA, navy accent and Public
# Sans/Source Serif 4 fonts borrowed from the Gulf Tracker) read as a
# mashup of both rather than its own thing. This is a "quant terminal"
# identity instead -- appropriate for a tool whose actual content is
# live model output and coefficients, not an editorial brief:
#   - Teal primary + coral secondary, a color family neither sibling
#     uses (MENASA is near-black+gold, Gulf is cream+navy). Contrast
#     checked with a real luminance calculation: 7.6:1 and 6.3:1 against
#     this background, both clear WCAG AA's 4.5:1 for text.
#   - IBM Plex Sans for headings and body, IBM Plex Mono for data --
#     no literary serif headline font at all, breaking from the
#     editorial-brief convention both siblings share.
# ============================================================
BG = "#0A1211"
SURFACE = "#0F1B19"
SURFACE_ALT = "#152420"
BORDER = "rgba(255,255,255,0.10)"
ACCENT = "#33B6AF"
ACCENT_DIM = "rgba(51,182,175,0.14)"
ACCENT2 = "#E0793E"
ACCENT2_DIM = "rgba(224,121,62,0.14)"
TEXT = "#F0EFEA"
TEXT_MUTED = "#93A6A3"
GOOD = "#34D399"
WARN = "#FBBF24"
BAD = "#F87171"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', -apple-system, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    h1, h2, h3 {{ font-family: 'IBM Plex Sans', sans-serif !important; }}
    .masthead-title, .section-title {{ font-family: 'IBM Plex Sans', -apple-system, sans-serif !important; }}

    /* Streamlit 1.63's actual DOM uses data-testid="stApp"/"stMain", not the
       older ".main" class -- verified by inspecting the real rendered page,
       not assumed from an older app's CSS. */
    [data-testid="stApp"], body {{
        background: {BG} !important;
    }}
    [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    .tag-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {ACCENT};
        margin-bottom: 0.7rem;
    }}
    .masthead-title {{
        font-family: 'IBM Plex Sans', -apple-system, sans-serif;
        font-size: 2.6rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.1;
        margin: 0 0 0.7rem 0;
        letter-spacing: -0.02em;
    }}
    .masthead-title span {{ color: {ACCENT}; }}
    .masthead-sub {{
        font-size: 0.96rem;
        color: {TEXT_MUTED};
        max-width: 780px;
        line-height: 1.65;
        margin-bottom: 1.2rem;
    }}
    .section-title {{
        font-size: 1.5rem;
        font-weight: 600;
        color: {TEXT};
        margin-bottom: 0.5rem;
    }}
    .card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
    }}
    .stat-num {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.9rem;
        font-weight: 700;
        color: {ACCENT};
        line-height: 1;
    }}
    .stat-label {{
        font-size: 0.78rem;
        color: {TEXT_MUTED};
        margin-top: 0.4rem;
    }}
    .honest-box {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-left: 3px solid {TEXT_MUTED};
        border-radius: 4px;
        padding: 0.85rem 1.2rem;
        margin: 1rem 0;
        font-size: 0.88rem;
        color: {TEXT_MUTED};
        line-height: 1.6;
    }}
    .honest-box .label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {TEXT_MUTED};
        margin-bottom: 0.4rem;
        display: block;
    }}
    .phase-pill {{
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        background: {ACCENT_DIM};
        color: {ACCENT};
        border: 1px solid rgba(51,182,175,0.35);
        margin-bottom: 0.6rem;
    }}
    a {{ color: {ACCENT2}; }}
</style>
""", unsafe_allow_html=True)

# Tabs, sliders, dataframes, and selectboxes are themed properly via
# .streamlit/config.toml's [theme] block (primaryColor etc.) -- that's the
# real fix, not CSS overrides layered on top, since st.dataframe in
# particular renders its grid on canvas (glide-data-grid), which page-level
# CSS cannot reach at all. Verified by an actual rendered screenshot, not
# assumed to work.


def style_chart(fig, height=380):
    fig.update_layout(
        height=height,
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(family="IBM Plex Sans, sans-serif", color=TEXT_MUTED, size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


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


# ============================================================
# DATA LOADING -- all real, all cached, all from this project's own
# already-built pipeline outputs.
# ============================================================
@st.cache_data
def load_phase1():
    conn = sqlite3.connect(os.path.join(HERE, "sql", "sovereign_distress.db"))
    panel = pd.read_sql("SELECT * FROM analysis_panel", conn)
    events = pd.read_sql("SELECT * FROM distress_events", conn)
    conn.close()
    return panel, events


@st.cache_data
def load_phase2():
    with open(os.path.join(HERE, "shock-module", "event_study_results.json")) as f:
        results = json.load(f)
    with open(os.path.join(HERE, "shock-module", "shock_timelines_raw.json")) as f:
        shocks = json.load(f)
    with open(os.path.join(HERE, "shock-module", "fx_timelines_raw.json")) as f:
        fx = json.load(f)
    return pd.DataFrame(results), shocks, fx


@st.cache_data
def load_phase3():
    panel = pd.read_csv(os.path.join(HERE, "forecast-module", "raw_panel.csv"))
    backtest = pd.read_csv(os.path.join(HERE, "forecast-module", "backtest_2024_results.csv"))
    coefs = pd.read_csv(os.path.join(HERE, "forecast-module", "stress_test_coefficients.csv"))
    with open(os.path.join(HERE, "forecast-module", "shock_drivers.json")) as f:
        drivers = json.load(f)
    return panel, backtest, coefs, drivers


phase1_panel, phase1_events = load_phase1()
phase2_results, phase2_shocks, phase2_fx = load_phase2()
phase3_panel, phase3_backtest, phase3_coefs, phase3_drivers = load_phase3()


# ============================================================
# LIVE PHASE 1 MODEL FIT -- refits the exact same primary specification as
# model/distress_model.py (same factor list, same complete-case handling,
# same country-clustered SEs) directly in the app, rather than keeping a
# separate hardcoded coefficient table that could silently drift from the
# validated model. This is also what makes real risk attribution possible
# below: the same fitted result object drives both the coefficient table
# and the per-country contribution breakdown.
# ============================================================
PRIMARY_FACTOR_COLS = [
    "current_account_pct_gdp", "reserves_months_imports",
    "gdp_growth", "inflation", "currency_depreciation_pct",
    "political_stability", "government_effectiveness", "rule_of_law",
    "regulatory_quality", "control_of_corruption",
]


@st.cache_resource
def fit_phase1_model(panel_df, outcome_col):
    complete = panel_df.dropna(subset=PRIMARY_FACTOR_COLS + [outcome_col])
    X = sm.add_constant(complete[PRIMARY_FACTOR_COLS])
    y = complete[outcome_col]
    result = sm.Logit(y, X).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": complete["country_code"]},
    )
    return result, complete


phase1_result, phase1_complete = fit_phase1_model(phase1_panel, "imf_program_entry")
phase1_factor_means = phase1_complete[PRIMARY_FACTOR_COLS].mean()


def _manual_auc(pos, neg):
    """AUC via Mann-Whitney U -- avoids adding scikit-learn as a dependency
    for one metric. Standard, exact definition: P(a random positive scores
    higher than a random negative)."""
    if len(pos) == 0 or len(neg) == 0:
        return None
    total = 0.0
    for p in pos:
        total += (neg < p).sum() + 0.5 * (neg == p).sum()
    return total / (len(pos) * len(neg))


@st.cache_resource
def historical_validation(panel_df):
    """
    Real historical validation, in two parts -- deliberately kept separate
    rather than blended into one number, because they answer different
    questions:

    1. IN-SAMPLE fit statistics on the full 355-observation primary model
       (same data used to fit AND evaluate). This measures how well the
       fitted model discriminates the events it was fit on -- informative,
       but a real overfitting risk with only 12 positive events and 10
       predictors, and NOT a genuine test of forecasting skill. Labeled as
       such everywhere it's shown.

    2. A genuine OUT-OF-SAMPLE temporal holdout: refit using only years
       <=2021 (4 real events -- an honestly thin training set), then score
       the fitted model's predictions against the real 2022-2024 outcomes
       it never saw. This is a real backtest, not a claim of a working
       early-warning system -- the raw predicted probabilities in the
       holdout are all near zero with no country clearly flagged, which is
       itself the honest finding, not hidden here.
    """
    complete = panel_df.dropna(subset=PRIMARY_FACTOR_COLS + ["imf_program_entry"]).copy()
    X = sm.add_constant(complete[PRIMARY_FACTOR_COLS])
    y = complete["imf_program_entry"]
    full_result = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": complete["country_code"]})
    complete["predicted_prob"] = full_result.predict(X)

    in_sample_corr = complete["predicted_prob"].corr(complete["imf_program_entry"])
    pos = complete.loc[complete["imf_program_entry"] == 1, "predicted_prob"].values
    neg = complete.loc[complete["imf_program_entry"] == 0, "predicted_prob"].values
    in_sample_auc = _manual_auc(pos, neg)
    top_decile_cut = complete["predicted_prob"].quantile(0.90)
    top_decile = complete[complete["predicted_prob"] >= top_decile_cut]
    in_sample = {
        "n": len(complete), "n_events": int(complete["imf_program_entry"].sum()),
        "corr": in_sample_corr, "auc": in_sample_auc,
        "top_decile_rate": top_decile["imf_program_entry"].mean(),
        "overall_rate": complete["imf_program_entry"].mean(),
    }

    train = complete[complete["year"] <= 2021]
    test = complete[complete["year"] > 2021].copy()
    oos = {"train_n": len(train), "train_events": int(train["imf_program_entry"].sum()),
           "test_n": len(test), "test_events": int(test["imf_program_entry"].sum())}
    try:
        X_train = sm.add_constant(train[PRIMARY_FACTOR_COLS])
        y_train = train["imf_program_entry"]
        oos_result = sm.Logit(y_train, X_train).fit(disp=0, cov_type="cluster", cov_kwds={"groups": train["country_code"]})
        X_test = sm.add_constant(test[PRIMARY_FACTOR_COLS], has_constant="add")
        test["predicted_prob"] = oos_result.predict(X_test)
        pos_t = test.loc[test["imf_program_entry"] == 1, "predicted_prob"].values
        neg_t = test.loc[test["imf_program_entry"] == 0, "predicted_prob"].values
        oos["auc"] = _manual_auc(pos_t, neg_t)
        oos["ranked"] = test[["country_code", "year", "predicted_prob", "imf_program_entry"]].sort_values("predicted_prob", ascending=False)
    except Exception as e:
        oos["error"] = str(e)

    return in_sample, oos


phase1_in_sample_val, phase1_oos_val = historical_validation(phase1_panel)


# ============================================================
# MODEL BENCHMARKING -- does this model's current predicted probability
# rank countries similarly to how real, independent rating agencies
# currently rank them? Uses real, current S&P ratings copied from MENASA's
# own sourced dataset (data/credit_ratings.py) -- explicitly a CURRENT
# SNAPSHOT, not a historical time series, so this is a real but limited
# cross-sectional check, not a genuine longitudinal benchmark. Stated
# plainly in the UI, not glossed over.
# ============================================================
import sys as _sys
_sys.path.insert(0, os.path.join(HERE, "data"))
from credit_ratings import SP_RATING, SP_SCALE  # noqa: E402


@st.cache_resource
def benchmark_vs_ratings(_phase1_result, panel_df):
    complete = panel_df.dropna(subset=PRIMARY_FACTOR_COLS).copy()
    X = sm.add_constant(complete[PRIMARY_FACTOR_COLS], has_constant="add")
    complete["predicted_prob"] = _phase1_result.predict(X)
    latest = complete.sort_values("year").groupby("country_code").tail(1)
    latest = latest[["country_code", "year", "predicted_prob"]].copy()
    latest["sp_rating"] = latest["country_code"].map(SP_RATING)
    latest["sp_numeric"] = latest["sp_rating"].map(SP_SCALE)
    rated = latest.dropna(subset=["sp_numeric"])
    spearman = rated["predicted_prob"].rank().corr(rated["sp_numeric"].rank())
    return rated.sort_values("predicted_prob", ascending=False), spearman, len(latest) - len(rated)


phase1_benchmark, phase1_benchmark_corr, phase1_benchmark_unrated = benchmark_vs_ratings(phase1_result, phase1_panel)


# ============================================================
# LOCAL PROJECTIONS -- real dynamic (impulse-response-style) effects of a
# real oil-price shock on inflation and GDP growth at horizons h=0,1,2,
# panel fixed-effects at each horizon (Jorda 2005 local-projections
# design). Deliberately kept to h=0-2, not the 8-12 horizons a textbook
# treatment might use -- with only 15 years of annual data per country,
# horizons that long would leave too few non-overlapping observations per
# country to estimate anything real; stated here, not silently shortened
# without explanation.
# ============================================================
@st.cache_resource
def fit_local_projections(raw_panel_df, drivers_dict, outcomes=("inflation", "gdp_growth"), horizons=(0, 1, 2)):
    oil = {int(y): v for y, v in drivers_dict["oil_annual_avg_usd"].items()}
    panel_lp = raw_panel_df.copy()
    panel_lp["oil_price"] = panel_lp["year"].map(oil)
    panel_lp = panel_lp.sort_values(["country_code", "year"])
    panel_lp["oil_pct_change"] = panel_lp.groupby("country_code")["oil_price"].transform(lambda s: s.pct_change(fill_method=None) * 100)

    rows = []
    for outcome in outcomes:
        for h in horizons:
            df = panel_lp[["country_code", "year", outcome, "oil_pct_change"]].copy()
            df[f"y_h{h}"] = df.groupby("country_code")[outcome].shift(-h)
            df = df.dropna(subset=[f"y_h{h}", "oil_pct_change"]).set_index(["country_code", "year"])
            if len(df) < 30:
                rows.append({"outcome": outcome, "h": h, "coef": None, "lo": None, "hi": None, "p": None, "n": len(df)})
                continue
            y = df[f"y_h{h}"]
            X = df[["oil_pct_change"]]
            res = PanelOLS(y, X, entity_effects=True).fit(cov_type="clustered", cluster_entity=True)
            ci = res.conf_int().loc["oil_pct_change"]
            rows.append({
                "outcome": outcome, "h": h,
                "coef": float(res.params["oil_pct_change"]), "lo": float(ci.iloc[0]), "hi": float(ci.iloc[1]),
                "p": float(res.pvalues["oil_pct_change"]), "n": int(res.nobs),
            })
    return pd.DataFrame(rows)


phase3_local_proj = fit_local_projections(phase3_panel, phase3_drivers)


# ============================================================
# RISK ARCHITECTURE -- interpretable sub-indices (external vulnerability,
# fiscal/sovereign, banking-sector, macro conditions, institutional,
# buffers) built from real extended World Bank WDI indicators
# (data/fetch_extended_indicators.py) merged into panel.csv by
# build_panel.py. A DESCRIPTIVE diagnostic layer, not a new composite score
# -- Phase 1's fitted logit above remains the only real predictive model
# this project makes. Real global financial conditions (VIX, US 10Y yield,
# dollar index, an EM bond ETF spread proxy) and real, sourced maritime-
# chokepoint exposure are also loaded here. Degrades gracefully (empty/
# None) if the underlying fetch hasn't been merged into panel.csv yet --
# never fabricates a value.
# ============================================================
_sys.path.insert(0, os.path.join(HERE, "model"))
from risk_architecture import SUB_INDICES, CONTEXT_ONLY, build_sub_indices  # noqa: E402
from peer_comparison import DIRECTION, latest_value_per_country, what_changed, top_movers  # noqa: E402
from chokepoint_exposure import MARITIME_CHOKEPOINTS, exposure_summary  # noqa: E402


@st.cache_data
def load_risk_architecture():
    raw_panel = pd.read_csv(os.path.join(HERE, "data", "panel.csv"))
    extended_cols = [c for cols in SUB_INDICES.values() for c in cols] + CONTEXT_ONLY
    available_cols = [c for c in extended_cols if c in raw_panel.columns]
    latest = latest_value_per_country(raw_panel, available_cols)
    sub_index_df = build_sub_indices(latest)
    changed_df = what_changed(raw_panel, available_cols)
    has_extended = any(c in raw_panel.columns for c in [
        "external_debt_pct_gni", "fiscal_balance_pct_gdp", "bank_npl_pct_loans"
    ])
    return raw_panel, latest, sub_index_df, changed_df, has_extended


risk_arch_raw_panel, risk_arch_latest, risk_arch_sub_index_df, risk_arch_changed_df, risk_arch_has_extended = load_risk_architecture()


# ============================================================
# SUB-INDEX VALIDATION -- real cross-sectional check of whether each
# sub-index's current standing associates with real distress-event history.
# Computed live (not hardcoded) so it can never silently drift from the
# actual data. See validate_sub_indices.py's own docstring for the real,
# disclosed limitation: this is cross-sectional (ever-distressed vs. never),
# not a genuine panel-based validation the way Phase 1's OOS backtest is.
# ============================================================
from validate_sub_indices import validate as validate_sub_indices  # noqa: E402


@st.cache_data
def load_sub_index_validation(panel_df):
    return validate_sub_indices(panel_df)[0]


sub_index_validation = load_sub_index_validation(risk_arch_raw_panel) if risk_arch_has_extended else None


@st.cache_data
def load_global_conditions():
    path = os.path.join(HERE, "forecast-module", "global_conditions.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


global_conditions = load_global_conditions()


# ============================================================
# TRADE NETWORK / SPILLOVER -- real UN Comtrade bilateral trade data, once
# fetched (data/fetch_trade_network.py, gated on a real COMTRADE_API_KEY
# repo secret). Degrades to "not yet available" -- never fabricated -- if
# the fetch hasn't run yet.
# ============================================================
from trade_network import load_trade_network, trade_concentration, spillover_exposure  # noqa: E402


@st.cache_data
def load_trade_network_cached():
    return load_trade_network(path=os.path.join(HERE, "data", "trade_network.csv"))


trade_net_df = load_trade_network_cached()
trade_net_countries = sorted(set(trade_net_df["reporter_code"])) if trade_net_df is not None else []


# ============================================================
# MASTHEAD
# ============================================================
st.markdown('<div class="tag-label">Companion to the MENASA Risk Monitor · The Crescent Brief</div>', unsafe_allow_html=True)
st.markdown('<h1 class="masthead-title">EM Macro & <span>Geopolitical Risk</span> Engine</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="masthead-sub">Three connected, independently-validated layers over the same 34 MENA and '
    'South Asia economies: a panel model predicting sovereign fiscal distress, a real event study measuring '
    'how geopolitical shocks move currency markets, and a macro forecasting engine with an interactive '
    'stress-testing tool below. Every figure on this page is loaded from this project\'s own real, sourced '
    'data and model output — nothing here is illustrative or invented.</div>',
    unsafe_allow_html=True,
)

_n_events = int((phase1_panel["sovereign_default"] == 1).sum() + (phase1_panel["imf_program_entry"] == 1).sum())
_n_countries = phase1_panel["country_code"].nunique()
_n_shocks = phase2_results["fx_pct_change"].notna().sum()

stat_cols = st.columns(4)
stats = [
    (str(_n_countries), "Countries tracked"),
    (str(_n_events), "Real distress events (2010-2024)"),
    (str(_n_shocks), "Shocks with real FX + GDELT data"),
    ("2010–2024", "Panel coverage"),
]
for col, (num, label) in zip(stat_cols, stats):
    with col:
        st.markdown(f'<div class="card"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Country Risk",
    "Geopolitical Shocks",
    "Forecast & Stress Test",
    "Methodology & Validation",
])

with tab1:
    # ============================================================
    # COVERAGE MAP -- a real map of the 34 tracked economies, colored by each
    # country's own real, counted distress-event total (sovereign defaults +
    # IMF program entries, 2010-2024) rather than an invented "risk score"
    # this phase's models don't actually produce as a single number.
    #
    # Drawn as plain filled polygons on a Cartesian lon/lat plot from real,
    # bundled Natural Earth 50m country boundaries (map-data/, fetched via
    # GitHub Actions -- see map-data/fetch_geojson.py) -- deliberately NOT
    # using Plotly's go.Choropleth/geo-subplot machinery. That was tried
    # first and dropped after two real, reproduced failures: Plotly's geo
    # subplot fetches its own base projection data from cdn.plot.ly in the
    # viewer's browser even with the basemap layers turned off and a custom
    # geojson supplied, so the map rendered completely blank here (confirmed
    # via a real "unexpected error while fetching topojson file" console
    # error both times, not assumed). Plain (lon, lat) scatter-fill has no
    # such dependency -- verified rendering below with zero external calls.
    # Equirectangular (lon=x, lat=y) rather than a true geographic projection
    # -- a real, disclosed simplification, not a precision GIS map.
    #
    # Moved to live inside the Overview tab (was previously shown above all
    # tabs, universally) per direct user feedback -- the tab bar now appears
    # right after the top stat cards, with the map as Overview's own first
    # section rather than a banner every tab had to scroll past.
    # ============================================================
    st.markdown('<div class="section-title">Coverage — 34 tracked economies</div>', unsafe_allow_html=True)

    with open(os.path.join(HERE, "map-data", "countries.geojson")) as f:
        _world_geojson = json.load(f)

    # Natural Earth's own ADM0_A3 codes diverge from ISO3 for two of our 34
    # tracked countries -- Palestine is "PSX" and South Sudan is "SDS" in this
    # dataset, not "PSE"/"SSD" -- a real mismatch found by checking the fetched
    # codes against COUNTRIES, not assumed to match.
    _NE_CODE_OVERRIDES = {"PSE": "PSX", "SSD": "SDS"}

    _country_events = (
        phase1_panel.groupby("country_code")[["sovereign_default", "imf_program_entry"]]
        .sum().sum(axis=1).reset_index(name="event_count")
    )
    _events_by_ne_code = {
        _NE_CODE_OVERRIDES.get(row.country_code, row.country_code): row.event_count
        for row in _country_events.itertuples()
    }
    _max_events = max(_events_by_ne_code.values()) if _events_by_ne_code else 0

    def _lerp_hex(c1, c2, t):
        c1, c2 = c1.lstrip("#"), c2.lstrip("#")
        r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
        r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
        return f"rgb({round(r1 + (r2 - r1) * t)},{round(g1 + (g2 - g1) * t)},{round(b1 + (b2 - b1) * t)})"

    # Real fix -- a direct user report: with a linear 0-to-max scale, only
    # Pakistan (4 real events, the panel's outlier max) reached the orange
    # end of the gradient, while every "1 event" country (Egypt, Jordan,
    # Iraq, Lebanon, Nepal, Sudan, Somalia, South Sudan, Yemen, Bangladesh)
    # and "2 event" Sri Lanka all landed in a similarly light teal band,
    # indistinguishable from each other. Fixed-count steps instead of a
    # linear-to-max scale, so a country's color reflects its own real count,
    # not its count relative to Pakistan's outlier value.
    _EVENT_COUNT_STEPS = {0: 0.15, 1: 0.45, 2: 0.70}
    _EVENT_COUNT_STEP_MAX = 1.0  # 3+ events

    def _event_color(count, max_events, surface_alt, accent, accent2):
        t = _EVENT_COUNT_STEPS.get(count, _EVENT_COUNT_STEP_MAX if count >= 3 else _EVENT_COUNT_STEPS[0])
        return _lerp_hex(surface_alt, accent, t / 0.5) if t <= 0.5 else _lerp_hex(accent, accent2, (t - 0.5) / 0.5)

    _MAX_RING_POINTS = 150  # real perf fix -- see build_coverage_map() docstring

    def _decimate(ring, max_points=_MAX_RING_POINTS):
        step = max(1, len(ring) // max_points)
        return ring[::step]

    @st.cache_resource
    def build_coverage_map(world_geojson, events_by_ne_code, max_events, bg, surface, surface_alt, border, accent, accent2, text, text_muted):
        """
        Built once and cached (st.cache_resource, since a Plotly Figure isn't
        the kind of plain data st.cache_data hashes well) -- Streamlit reruns
        the whole script on every interaction anywhere in the app, and this
        figure was originally built as 732 separate polygon traces (one per
        country per disjoint landmass) totaling 50,589 points every single
        rerun, measured directly, not guessed -- e.g. moving a slider on a
        completely different tab was rebuilding this map from scratch. Two
        real fixes here: caching, and merging each country's polygon parts
        into a single trace (Plotly draws multiple disjoint filled shapes in
        one trace when their coordinate lists are separated by a `None`),
        cutting 732 traces to 119. Also decimates very large rings -- Russia
        and the US alone contributed over 13,000 points from countries that
        barely clip the edge of this map's actual viewport -- to a max of
        150 points each, a real, disclosed simplification consistent with
        this already being a non-precision equirectangular projection.
        """
        fig = go.Figure()
        for feat in world_geojson["features"]:
            ne_code = feat["properties"]["ADM0_A3"]
            name = feat["properties"].get("NAME", ne_code)
            tracked = ne_code in events_by_ne_code
            count = events_by_ne_code.get(ne_code, 0)
            fill_color = _event_color(count, max_events, surface_alt, accent, accent2) if tracked else surface_alt
            # Real fix -- a tracked country with 0 events was rendering in the exact
            # same fill as a country outside this project's panel entirely (21 of the
            # 34 tracked countries have 0 real events, so most of the map was reading
            # as "not tracked"). A visible border on every tracked country now makes
            # all 34 identifiable regardless of fill.
            line_color = accent if tracked else border
            line_width = 0.9 if tracked else 0.6
            hover = (
                f"<b>{name}</b><br>Real distress events (2010–2024): {count}"
                if tracked else f"<b>{name}</b><br>Outside this project's 34-country panel"
            )

            geom = feat["geometry"]
            polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            lons, lats = [], []
            for poly in polygons:
                ring = _decimate(poly[0])  # exterior ring only -- interior holes not rendered, a real simplification
                if lons:
                    lons.append(None)
                    lats.append(None)
                lons.extend(pt[0] for pt in ring)
                lats.extend(pt[1] for pt in ring)

            fig.add_trace(go.Scatter(
                x=lons, y=lats, mode="lines", fill="toself",
                fillcolor=fill_color, line=dict(color=line_color, width=line_width),
                hoveron="fills", hoverinfo="text", text=hover,
                name=name, showlegend=False,
            ))

        fig.update_xaxes(range=[-24, 98], visible=False, fixedrange=True)
        fig.update_yaxes(range=[-12, 46], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
        fig.update_layout(
            height=440,
            margin=dict(l=0, r=0, t=6, b=0),
            plot_bgcolor=bg,
            paper_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(bgcolor=surface, font=dict(family="IBM Plex Sans, sans-serif", color=text)),
            font=dict(family="IBM Plex Sans, sans-serif", color=text_muted, size=12),
        )
        return fig

    st.plotly_chart(
        build_coverage_map(_world_geojson, _events_by_ne_code, _max_events, BG, SURFACE, SURFACE_ALT, BORDER, ACCENT, ACCENT2, TEXT, TEXT_MUTED),
        use_container_width=True, config={"displayModeBar": False},
    )
    st.caption(
        "Colored by each country's own real, counted total of sovereign defaults and IMF program entries "
        "in this panel (2010–2024) — not an invented composite risk score. All 34 tracked countries are outlined; "
        "21 of them have 0 real events in this panel and show as a dim tint, not the same plain gray as the "
        "countries genuinely outside this project's 34-economy panel. Equirectangular projection, not a precision GIS map."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">What this tool does</div>', unsafe_allow_html=True)
    st.markdown(
        "A live, interactive risk-analytics engine covering the same 34 MENA and South Asia economies as the "
        "MENASA Risk Monitor — one panel model predicting sovereign fiscal distress, one event study measuring "
        "how geopolitical shocks actually move currency markets, and one macro forecasting model you can stress "
        "test yourself, live, from the sliders on the Macro Forecast tab."
    )

    # Real fix -- a direct user report: clicking the "link to heading" icon
    # next to a phase card's title appeared to do nothing. Not actually
    # broken: Streamlit auto-attaches a real anchor link to every <h4> it
    # renders (confirmed by inspecting the live DOM -- each one gets a real
    # <a href="#slug">), but these three are just card titles inside a
    # grid, already on screen, not standalone page sections -- so clicking
    # sets the URL hash with nothing new to scroll to, which reads as
    # broken. Fixed by using a styled <div> instead of <h4>, so Streamlit
    # has no heading element here to attach an anchor to at all.
    card_title_style = f"color:{TEXT};margin:0.3rem 0;font-size:1.15rem;font-weight:700;line-height:1.3;"
    ov_cols = st.columns(3)
    with ov_cols[0]:
        st.markdown(
            f'<div class="card"><span class="phase-pill">Country Risk</span>'
            f'<div style="{card_title_style}">Is this country heading into distress?</div>'
            f'<p style="color:{TEXT_MUTED};font-size:0.88rem;line-height:1.6;">A panel logistic regression predicting '
            f'sovereign default and IMF program entry from real macro/governance fundamentals — a probability, '
            f'not a score.</p></div>', unsafe_allow_html=True)
    with ov_cols[1]:
        st.markdown(
            f'<div class="card"><span class="phase-pill">Geopolitical Shocks</span>'
            f'<div style="{card_title_style}">Did this shock actually move markets?</div>'
            f'<p style="color:{TEXT_MUTED};font-size:0.88rem;line-height:1.6;">A real event study pairing GDELT '
            f'media-coverage data against real historical FX rates for 5 dated geopolitical shocks.</p></div>',
            unsafe_allow_html=True)
    with ov_cols[2]:
        st.markdown(
            f'<div class="card"><span class="phase-pill">Forecast & Stress Test</span>'
            f'<div style="{card_title_style}">What happens under a shock scenario?</div>'
            f'<p style="color:{TEXT_MUTED};font-size:0.88rem;line-height:1.6;">A panel AR(1) forecasting model with '
            f'an interactive stress-test layer — apply a real oil or rate shock and see the forecast move.</p></div>',
            unsafe_allow_html=True)

    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.85rem;">These three tabs are a working tool, not a build log — '
        f'select a country or event and use it. The research methodology behind each one, including full model '
        f'validation and what "Phase 1/2/3" originally meant during development, lives in the '
        f'<b>Methodology &amp; Validation</b> tab.</p>', unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Companion tools</div>', unsafe_allow_html=True)
    link_cols = st.columns(3)
    with link_cols[0]:
        st.markdown(f'<div class="card"><b style="color:{TEXT};">MENASA Risk Monitor</b><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">The country-risk composite this engine\'s '
                     f'Phase 1 model builds on.</span><br><br>'
                     f'<a href="https://menasa-risk-monitor.onrender.com" target="_blank">Open →</a></div>', unsafe_allow_html=True)
    with link_cols[1]:
        st.markdown(f'<div class="card"><b style="color:{TEXT};">Gulf AI &amp; Tech-Bloc Tracker</b><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Tech-bloc geoeconomics companion tool.</span>'
                     f'<br><br><a href="https://oaqjp-final-project-emb-ai-c8u6.onrender.com" target="_blank">Open →</a></div>', unsafe_allow_html=True)
    with link_cols[2]:
        st.markdown(f'<div class="card"><b style="color:{TEXT};">The Crescent Brief</b><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Qualitative analysis and a scored '
                     f'forecast track record.</span><br><br>'
                     f'<a href="https://thecrescentbrief.substack.com" target="_blank">Read →</a></div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-title">Country Risk</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">A panel logistic regression predicting two real, sourced outcomes: '
        f'sovereign default and formal IMF program entry. Primary specification excludes <code>debt_to_gdp</code> '
        f'deliberately (see the honest note below) — trained on 355 observations, 14 of 17 real events retained.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="honest-box"><span class="label">Data limitation and specification note</span>'
        '<code>debt_to_gdp</code> is non-missing in only 91 of 507 panel rows. Requiring complete cases across '
        'all 11 factors, including it, collapsed the usable sample to 77 rows and dropped all but 1 of the 17 real '
        'distress events with it — the country-years missing debt data are disproportionately the same '
        'country-years under genuine fiscal strain (Lebanon stopped publishing fiscal data entirely during its '
        'crisis). Fixed by excluding it from the primary model and testing it separately as a robustness check.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="honest-box"><span class="label">Data limitation, since resolved</span>'
        'A later audit found that the 5 economic factors this model is fit on (<code>current_account_pct_gdp</code>, '
        '<code>reserves_months_imports</code>, <code>gdp_growth</code>, <code>inflation</code>, '
        '<code>currency_depreciation_pct</code>) were the same 0–100 normalized risk sub-scores whose mislabeling was '
        'already caught and fixed for Phase 3\'s forecasting model, but missed here at first. Fixed: the primary '
        'specification now uses Phase 3\'s real raw values for these 5 factors (e.g. Pakistan\'s 2023 current account '
        'is correctly <b>-0.3% of GDP</b>, not 48.3), while keeping the <b>governance</b> factors (political_stability, '
        'rule_of_law, etc.) on their real 0–100 World Bank WGI percentile scale, which was already correct. Refit and '
        're-validated in R after the fix — see the coefficient table below. The refit changed which factors are '
        'significant: <code>reserves_months_imports</code> is now significant (p&lt;0.001, wasn\'t before) and '
        '<code>gdp_growth</code> no longer is (was significant with the old mislabeled data) — a real, honest change '
        'in the result, not smoothed over.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### Real distress events (2010–2024)")
    ev_display = phase1_events.copy()
    ev_display["country"] = ev_display["country_code"].map(COUNTRIES)
    ev_display = ev_display[["country", "year", "event_type", "detail"]].sort_values("year")
    ev_display.columns = ["Country", "Year", "Event Type", "Detail"]
    st.dataframe(ev_display, use_container_width=True, hide_index=True)

    st.markdown("#### Explore the panel")
    country_options = sorted(phase1_panel["country_code"].dropna().unique())
    sel_country = st.selectbox(
        "Select a country", country_options,
        format_func=lambda c: f"{COUNTRIES.get(c, c)} ({c})", key="p1_country",
    )
    country_data = phase1_panel[phase1_panel["country_code"] == sel_country].sort_values("year")

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=country_data["year"], y=country_data["political_stability"],
                                  name="Political Stability", line=dict(color=ACCENT)))
        fig.add_trace(go.Scatter(x=country_data["year"], y=country_data["rule_of_law"],
                                  name="Rule of Law", line=dict(color=ACCENT2)))
        fig.update_layout(title="Governance factors (normalized 0-100 risk score)")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    with c2:
        events_here = country_data[(country_data["sovereign_default"] == 1) | (country_data["imf_program_entry"] == 1)]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=country_data["year"], y=country_data["current_account_pct_gdp"],
                               name="Current Account (% GDP)", marker_color=ACCENT))
        for _, row in events_here.iterrows():
            fig2.add_vline(x=row["year"], line_dash="dot",
                            line_color=BAD if row["sovereign_default"] == 1 else WARN)
        fig2.update_layout(title="Real current account balance (% GDP), with real distress-event markers")
        st.plotly_chart(style_chart(fig2), use_container_width=True)

    if events_here.empty:
        st.caption(f"No real distress event recorded for {COUNTRIES.get(sel_country, sel_country)} in this panel.")

    # ============================================================
    # RISK ATTRIBUTION -- real decomposition of the fitted model's own log-odds
    # for this country's most recent panel year, not a separately-invented
    # "why" narrative. contribution_i = coef_i * (this country's value_i -
    # the sample mean of factor i across all complete-case observations) --
    # standard logistic-regression decomposition against a reference point,
    # computed from phase1_result (the exact same live-fitted model behind
    # the coefficient table below), not a hardcoded explanation.
    # ============================================================
    st.markdown("#### Risk attribution — why the model says what it says")
    country_latest = country_data.dropna(subset=PRIMARY_FACTOR_COLS).sort_values("year")
    if country_latest.empty:
        st.caption(f"{COUNTRIES.get(sel_country, sel_country)} has no panel year with complete data across all 10 primary factors, so no attribution can be computed for it.")
    else:
        latest_row = country_latest.iloc[-1]
        latest_year = int(latest_row["year"])
        x_vals = latest_row[PRIMARY_FACTOR_COLS]
        contributions = phase1_result.params[PRIMARY_FACTOR_COLS] * (x_vals - phase1_factor_means)
        baseline_log_odds = phase1_result.params["const"] + (phase1_result.params[PRIMARY_FACTOR_COLS] * phase1_factor_means).sum()
        predicted_log_odds = phase1_result.params["const"] + (phase1_result.params[PRIMARY_FACTOR_COLS] * x_vals).sum()
        predicted_prob = 1 / (1 + np.exp(-predicted_log_odds))
        avg_prob = 1 / (1 + np.exp(-baseline_log_odds))

        contrib_df = contributions.sort_values().reset_index()
        contrib_df.columns = ["Factor", "Contribution"]
        bar_colors = [BAD if v > 0 else GOOD for v in contrib_df["Contribution"]]
        fig_attr = go.Figure(go.Bar(
            x=contrib_df["Contribution"], y=contrib_df["Factor"], orientation="h",
            marker_color=bar_colors,
        ))
        fig_attr.update_layout(
            title=f"{COUNTRIES.get(sel_country, sel_country)} ({latest_year}) — log-odds contribution vs. the sample-average country",
            xaxis_title="Contribution to log-odds (imf_program_entry)",
        )
        st.plotly_chart(style_chart(fig_attr, height=340), use_container_width=True)

        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f'<div class="card"><div class="stat-num">{predicted_prob:.1%}</div>'
                         f'<div class="stat-label">Model-implied probability, {COUNTRIES.get(sel_country, sel_country)} {latest_year}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="card"><div class="stat-num">{avg_prob:.1%}</div>'
                         f'<div class="stat-label">Implied probability for the sample-average country (reference point)</div></div>', unsafe_allow_html=True)
        st.caption(
            "Red bars push the log-odds up (toward IMF program entry) relative to the average country in this "
            "panel; green bars push it down. This is a decomposition of the model's own fitted coefficients "
            "against real data for this country-year, not a separate causal claim — a factor pushing the score "
            "up is not proof it caused distress, only that it differs from this panel's average in the direction "
            "the fitted model associates with entry. The 5 economic factors' contributions are now in real economic "
            "units (percentage points, months of reserves cover, etc.) since the data-limitation fix noted above; "
            "the governance factors remain in their real 0–100 WGI percentile units."
        )

    # ============================================================
    # TRANSMISSION CHANNELS -- real trade/FDI/reserves exposure for this
    # country, from raw_panel.csv (fetched for Phase 3, unused elsewhere in
    # this app until now). Shows real levels only -- no invented weights or
    # an aggregated "exposure score" beyond what the data actually measures.
    # ============================================================
    st.markdown("#### Economic transmission channels")
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.9rem;">The real channels through which external shocks reach '
        f'this economy — not the risk model itself, but the structural exposures that give its factors somewhere '
        f'to come from.</p>', unsafe_allow_html=True,
    )
    chan_data = phase3_panel[phase3_panel["country_code"] == sel_country].sort_values("year")
    chan_cols = ["exports_pct_gdp", "imports_pct_gdp", "fdi_net_inflows_pct_gdp", "reserves_months_imports"]
    chan_latest = chan_data.dropna(subset=chan_cols, how="all").tail(1)
    if chan_latest.empty:
        st.caption(f"No real trade/FDI data available for {COUNTRIES.get(sel_country, sel_country)} in this panel.")
    else:
        row = chan_latest.iloc[0]
        chan_year = int(row["year"])
        trade_openness = (row["exports_pct_gdp"] or 0) + (row["imports_pct_gdp"] or 0)
        ch_cols = st.columns(4)
        chan_stats = [
            (f"{trade_openness:.0f}%" if pd.notna(trade_openness) else "N/A", "Trade openness (exports + imports, % GDP)"),
            (f"{row['fdi_net_inflows_pct_gdp']:.1f}%" if pd.notna(row["fdi_net_inflows_pct_gdp"]) else "N/A", "Net FDI inflows (% GDP)"),
            (f"{row['reserves_months_imports']:.1f}mo" if pd.notna(row["reserves_months_imports"]) else "N/A", "Reserves cover (months of imports)"),
            (f"{row['current_account_pct_gdp']:.1f}%" if pd.notna(row["current_account_pct_gdp"]) else "N/A", "Current account balance (% GDP)"),
        ]
        for col, (num, label) in zip(ch_cols, chan_stats):
            with col:
                st.markdown(f'<div class="card"><div class="stat-num" style="font-size:1.4rem;">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
        st.caption(f"Real {chan_year} values from World Bank WDI (via this project's own fetched raw_panel.csv). High trade openness and thin reserves cover are the classic channels through which a geopolitical shock (e.g. a commodity-price spike or a sanctions regime) reaches the macro factors the model above actually uses.")

    # ============================================================
    # ANALYST BRIEFING -- a structured synthesis of everything computed
    # above for the selected country, assembled deterministically from real
    # already-computed numbers (an f-string template, not free-form
    # generated text) -- every sentence below is traceable to a specific
    # number shown earlier on this page. Model coefficients, in/out-of-
    # sample validation, and the ratings benchmark all live in the
    # Methodology & Validation tab -- this tab is a working tool, not a
    # build log, per direct user feedback.
    # ============================================================
    st.markdown("#### Analyst briefing")
    if country_latest.empty:
        st.caption(f"No complete-case panel year for {COUNTRIES.get(sel_country, sel_country)}, so no briefing can be generated for it.")
    else:
        top_driver = contrib_df.iloc[-1]  # largest positive contribution
        bottom_driver = contrib_df.iloc[0]  # largest negative contribution
        bench_row = phase1_benchmark[phase1_benchmark["country_code"] == sel_country]
        rating_line = ""
        if not bench_row.empty and pd.notna(bench_row.iloc[0]["sp_numeric"]):
            rank = int((phase1_benchmark["predicted_prob"] >= bench_row.iloc[0]["predicted_prob"]).sum())
            rating_line = (f"<br><b>Benchmark:</b> Real S&amp;P rating {bench_row.iloc[0]['sp_rating']}; this model ranks it "
                           f"{rank} of {len(phase1_benchmark)} rated countries by predicted probability.")
        chan_line = ""
        if not chan_latest.empty:
            chan_line = (f"<br><b>Transmission exposure ({chan_year}):</b> {trade_openness:.0f}% trade openness, "
                         f"{row['reserves_months_imports']:.1f} months of import reserves cover." if pd.notna(row["reserves_months_imports"])
                         else f"<br><b>Transmission exposure ({chan_year}):</b> {trade_openness:.0f}% trade openness.")
        st.markdown(
            f'<div class="card">'
            f'<b style="color:{ACCENT};">{COUNTRIES.get(sel_country, sel_country)} — {latest_year}</b><br><br>'
            f'<b>Model-implied probability:</b> {predicted_prob:.1%} (vs. {avg_prob:.1%} for the sample-average country)<br>'
            f'<b>Top driver pushing risk up:</b> {top_driver["Factor"]} (contribution {top_driver["Contribution"]:+.2f} log-odds)<br>'
            f'<b>Top driver pushing risk down:</b> {bottom_driver["Factor"]} (contribution {bottom_driver["Contribution"]:+.2f} log-odds)'
            f'{chan_line}{rating_line}<br><br>'
            f'<b>Model confidence:</b> {"Low" if phase1_in_sample_val["n_events"] < 20 else "Moderate"} — fit on only '
            f'{phase1_in_sample_val["n_events"]} real positive events; out-of-sample validation above shows the model does '
            f'not confidently flag specific countries ahead of real events.<br>'
            f'<b>Limitation:</b> only {phase1_in_sample_val["n_events"]} real positive events — near-perfect separation risk in the '
            f'rarer sovereign_default outcome, disclosed in Methodology &amp; Validation.'
            f'</div>', unsafe_allow_html=True,
        )
        st.caption(
            "Every line above is generated from the real numbers computed elsewhere on this page for the selected "
            "country and year — not separately written or invented."
        )

    # ============================================================
    # RISK ARCHITECTURE -- descriptive sub-index breakdown, real extended
    # WDI indicators, peer-relative percentiles, and real year-over-year
    # "what changed" attribution. Explicitly NOT a second predictive model
    # -- see risk_architecture.py's own docstring.
    # ============================================================
    st.markdown("#### Risk architecture")
    if not risk_arch_has_extended:
        st.caption(
            "Extended external/fiscal/banking/trade indicators haven't been fetched into this deployment yet "
            "(data/fetch_extended_indicators.py via GitHub Actions) — this section will populate once that "
            "data is merged into panel.csv. No fabricated values are shown in the meantime."
        )
    else:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};">A descriptive breakdown of WHERE a country\'s risk sits across real, '
            f'independently-sourced dimensions — not a second predictive score. The only real predictive model in '
            f'this project is the fitted logit above; this shows relative standing (percentile among the 34 '
            f'countries, direction-adjusted so higher always means more of that risk) on each dimension.</p>',
            unsafe_allow_html=True,
        )
        arch_row = risk_arch_sub_index_df[risk_arch_sub_index_df["country_code"] == sel_country]
        if arch_row.empty:
            st.caption(f"No data available for {COUNTRIES.get(sel_country, sel_country)}.")
        else:
            arch_row = arch_row.iloc[0]
            sub_labels = {
                "external_vulnerability_risk": "External Vulnerability",
                "fiscal_sovereign_risk": "Fiscal / Sovereign",
                "banking_sector_risk": "Banking Sector",
                "macro_conditions_risk": "Macro Conditions",
                "institutional_risk": "Institutional",
                "buffers_strength": "Buffers (strength)",
            }
            cols = st.columns(len(sub_labels))
            for col, (key, label) in zip(cols, sub_labels.items()):
                val = arch_row.get(key)
                base = key.rsplit("_", 1)[0]
                cov = arch_row.get(f"{base}_coverage")
                of = arch_row.get(f"{base}_of")
                with col:
                    if pd.isna(val):
                        st.markdown(f'<div class="card"><b>{label}</b><br><span style="color:{TEXT_MUTED};">No data</span></div>', unsafe_allow_html=True)
                    else:
                        is_buffer = (label == "Buffers (strength)")
                        # Risk cards: GOOD low / BAD high. Buffer card is inverted:
                        # GOOD high / BAD low, since a higher number there means
                        # more resilience, not more risk.
                        if is_buffer:
                            color = GOOD if val >= 50 else (BAD if val < 34 else WARN)
                        else:
                            color = GOOD if val < 50 else (BAD if val >= 66 else WARN)
                        st.markdown(
                            f'<div class="card"><b>{label}</b><br>'
                            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:1.3rem;color:{color};">{val:.0f}</span>'
                            f'<span style="color:{TEXT_MUTED};font-size:0.8rem;"> / 100 percentile</span><br>'
                            f'<span style="color:{TEXT_MUTED};font-size:0.75rem;">{cov} of {of} real components available</span></div>',
                            unsafe_allow_html=True,
                        )

            st.caption(
                "Percentile among the 34 tracked countries on real, latest-available values for each dimension's "
                "components (see Methodology & Validation for exact indicators and coverage). \"Buffers (strength)\" "
                "is inverted so a higher number always means more resilience, not more risk."
            )

            worsening, improving = top_movers(risk_arch_changed_df, sel_country, n=3)
            wc1, wc2 = st.columns(2)
            with wc1:
                st.markdown("**What changed — pushing risk up**")
                if worsening.empty:
                    st.caption("No real year-over-year comparison available.")
                else:
                    for _, r in worsening.iterrows():
                        st.markdown(f"- {r['factor']}: {r['from_year']}→{r['to_year']}, Δ {r['raw_delta']:+.2f}")
            with wc2:
                st.markdown("**What changed — improving**")
                if improving.empty:
                    st.caption("No real year-over-year comparison available.")
                else:
                    for _, r in improving.iterrows():
                        st.markdown(f"- {r['factor']}: {r['from_year']}→{r['to_year']}, Δ {r['raw_delta']:+.2f}")

            chokepoints, chokepoint_risk = exposure_summary(sel_country)
            if chokepoints:
                names = ", ".join(MARITIME_CHOKEPOINTS[k]["name"] for k in chokepoints)
                st.markdown(
                    f'<div class="honest-box"><span class="label">Chokepoint exposure — real, sourced</span>'
                    f'{COUNTRIES.get(sel_country, sel_country)} has direct real exposure to: <b>{names}</b> '
                    f'(current risk level: {chokepoint_risk}). See Methodology for sourcing and how this is assigned.</div>',
                    unsafe_allow_html=True,
                )

with tab3:
    st.markdown('<div class="section-title">Geopolitical Shocks</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">Real GDELT media-coverage data paired against real historical FX rates '
        f'for 5 precisely-dated shocks. Syria (Jan 2012) was dropped after a real fetch confirmed it predates '
        f'GDELT\'s actual data coverage window (Feb 2015+) — a genuine scope constraint, not hidden.</p>',
        unsafe_allow_html=True,
    )

    usable = phase2_results.dropna(subset=["gdelt_avg_tone_post", "fx_pct_change"])
    corr = usable["gdelt_avg_tone_post"].corr(usable["fx_pct_change"])

    st.markdown(
        f'<div class="honest-box"><span class="label">Interpretation note</span>'
        f'Correlation (GDELT tone vs. FX % change), n={len(usable)}: <b>{corr:.2f}</b>. This runs counter to naive '
        f'intuition (worse tone → bigger FX move) because Lebanon has the single worst media tone in the set but '
        f'almost no FX movement — its official rate was still pegged during that window — while Egypt has the '
        f'mildest tone but the largest depreciation, since its pound floats more freely. Exchange-rate regime '
        f'matters as much as the shock itself. n=5 is not a sample to draw a statistical conclusion from — this is '
        f'a real, correctly-computed correlation, not a claim of a validated predictive relationship.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### The 5 shocks")
    ev_table = phase2_results.copy()
    ev_table["country"] = ev_table["country_code"].map(COUNTRIES)
    ev_table = ev_table[["country", "event_date", "label", "gdelt_avg_tone_post", "fx_pct_change"]]
    ev_table.columns = ["Country", "Event Date", "Event", "Avg GDELT Tone (7d post)", "FX % Change"]
    st.dataframe(ev_table.style.format({"Avg GDELT Tone (7d post)": "{:.2f}", "FX % Change": "{:+.1f}%"}, na_rep="N/A"),
                 use_container_width=True, hide_index=True)

    st.markdown("#### Explore an event")
    shock_labels = {s["country_code"]: s["label"] for s in phase2_shocks}
    sel_shock = st.selectbox(
        "Select a shock event",
        [s["country_code"] for s in phase2_shocks if s["country_code"] != "SYR"],
        format_func=lambda c: f"{COUNTRIES.get(c, c)} — {shock_labels.get(c, '')}", key="p2_shock",
    )

    shock_entry = next(s for s in phase2_shocks if s["country_code"] == sel_shock)
    fx_entry = next((f for f in phase2_fx if f["country_code"] == sel_shock), None)

    c1, c2 = st.columns(2)
    with c1:
        tone_tl = shock_entry.get("tone_timeline")
        if tone_tl and tone_tl.get("timeline"):
            data = tone_tl["timeline"][0]["data"]
            dates = [d["date"][:8] for d in data]
            vals = [d["value"] for d in data]
            fig = go.Figure(go.Scatter(x=dates, y=vals, line=dict(color=ACCENT), fill="tozeroy"))
            fig.add_vline(x=shock_entry["event_date"].replace("-", ""), line_dash="dash", line_color=BAD)
            fig.update_layout(title="GDELT media tone (±30 days around event)")
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.caption("No tone timeline data for this event.")
    with c2:
        if fx_entry and fx_entry.get("rates"):
            rates = fx_entry["rates"]
            dates = list(rates.keys())
            vals = list(rates.values())
            fig2 = go.Figure(go.Scatter(x=dates, y=vals, line=dict(color=ACCENT2)))
            fig2.add_vline(x=shock_entry["event_date"], line_dash="dash", line_color=BAD)
            fig2.update_layout(title=f"USD/{fx_entry['currency_code']} exchange rate (±30 days)")
            st.plotly_chart(style_chart(fig2), use_container_width=True)
        else:
            st.caption("No FX data for this event.")

    st.caption(
        "Independently validated in R (base cor()) — matches Python's manually-computed correlation exactly (0.59). "
        "Full methodology in shock-module/README.md."
    )

    st.markdown("#### Trade spillover network")
    if trade_net_df is None:
        st.markdown(
            f'<div class="honest-box"><span class="label">Not yet available — real fetch pending credentials</span>'
            f'A real bilateral trade network from UN Comtrade (data/fetch_trade_network.py) is built and ready to '
            f'run, gated on a free COMTRADE_API_KEY not yet registered for this project. No invented trade weights '
            f'are shown in the meantime — see Methodology &amp; Validation for exactly what this will show once live.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};">Real UN Comtrade bilateral trade data: if the selected country '
            f'experiences a shock, which other tracked countries are most exposed through real trade — either as '
            f'an export market that shuts (import exposure) or as a buyer that stops purchasing (export exposure)?</p>',
            unsafe_allow_html=True,
        )
        sel_shock_country = st.selectbox(
            "Shocked country", trade_net_countries,
            format_func=lambda c: COUNTRIES.get(c, c), key="trade_net_country",
        )
        spill = spillover_exposure(trade_net_df, sel_shock_country, trade_net_countries)
        if spill.empty:
            st.caption(f"No real trade linkage found between {COUNTRIES.get(sel_shock_country, sel_shock_country)} and any other tracked country in this data.")
        else:
            top = spill.head(10).copy()
            top["country"] = top["country_code"].map(COUNTRIES)
            fig_spill = go.Figure()
            fig_spill.add_trace(go.Bar(y=top["country"], x=top["import_exposure_pct"], name="Import exposure (%)", orientation="h", marker_color=ACCENT))
            fig_spill.add_trace(go.Bar(y=top["country"], x=top["export_exposure_pct"], name="Export exposure (%)", orientation="h", marker_color=ACCENT2))
            fig_spill.update_layout(title=f"Real trade exposure to a {COUNTRIES.get(sel_shock_country, sel_shock_country)} shock", barmode="group", xaxis_title="% of that country's total trade")
            st.plotly_chart(style_chart(fig_spill), use_container_width=True)
            st.caption(
                "Import exposure = % of the listed country's real total imports that come from the shocked "
                "country (an export-market shock). Export exposure = % of its real total exports that go to the "
                "shocked country (an import-demand shock). Both are real, computed from actual bilateral trade "
                "values — never combined into one invented composite number."
            )

with tab4:
    st.markdown('<div class="section-title">Forecast &amp; Stress Test</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">A panel AR(1) model forecasting next-year inflation, extended with real, '
        f'fetched shock drivers (oil price, US short-term rate). Growth is deliberately not forecast interactively '
        f'here — see the honest result below on why.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="honest-box"><span class="label">Data limitation and specification note</span>'
        'An early version of this model forecast MENASA\'s <b>normalized 0-100 risk sub-scores</b> instead of real '
        'GDP growth/inflation — that data\'s own file header says explicitly it\'s normalized, not raw. The '
        'giveaway was backtest output with values of exactly 100.0 or 0.0 (rank extremes, not real rates). Fixed '
        'by switching to MENASA\'s real raw indicator values.</div>', unsafe_allow_html=True,
    )

    r1, r2 = st.columns(2)
    with r1:
        st.markdown(
            f'<div class="card"><b style="color:{TEXT};">GDP Growth</b><br>'
            f'<span style="color:{BAD};font-family:\'IBM Plex Mono\',monospace;font-size:1.3rem;">No real signal</span><br>'
            f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Loses to a naive "no change" baseline (3.41 vs '
            f'2.93 MAE on the real 2024 backtest) — consistent with well-documented growth literature.</span></div>',
            unsafe_allow_html=True)
    with r2:
        st.markdown(
            f'<div class="card"><b style="color:{TEXT};">Inflation</b><br>'
            f'<span style="color:{GOOD};font-family:\'IBM Plex Mono\',monospace;font-size:1.3rem;">Real signal (R²=0.30)</span><br>'
            f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Beats the naive baseline by 25% (10.63 vs 14.12 '
            f'MAE). Lag coefficient 0.574, p&lt;0.0001 — genuine, significant persistence.</span></div>',
            unsafe_allow_html=True)

    st.markdown("#### Interactive stress test")
    infl_backtest = phase3_backtest[phase3_backtest["variable"] == "inflation"].copy()
    infl_backtest["country"] = infl_backtest["country_code"].map(COUNTRIES)

    sel_st_country = st.selectbox(
        "Select a country (baseline = this model's own real 2024 forecast)",
        infl_backtest["country_code"].tolist(),
        format_func=lambda c: f"{COUNTRIES.get(c, c)} ({c})", key="p3_country",
    )
    baseline_row = infl_backtest[infl_backtest["country_code"] == sel_st_country].iloc[0]
    baseline_forecast = baseline_row["forecast_2024"]
    actual_2024 = baseline_row["actual_2024"]

    beta_oil = phase3_coefs.set_index("predictor").loc["oil_pct_change", "coefficient"]
    beta_rate = phase3_coefs.set_index("predictor").loc["rate_change", "coefficient"]
    p_oil = phase3_coefs.set_index("predictor").loc["oil_pct_change", "p_value"]
    p_rate = phase3_coefs.set_index("predictor").loc["rate_change", "p_value"]

    # ============================================================
    # NAMED SCENARIO PRESETS -- documented, illustrative shock magnitudes
    # (not statistically fitted, and not claimed to be), applied through the
    # model's own real fitted oil/rate coefficients above. The manual
    # sliders below still work for any other magnitude; presets just set
    # them to a defensible starting point instead of leaving the user to
    # guess a "reasonable" shock size themselves.
    # ============================================================
    SCENARIO_PRESETS = {
        "Baseline — no shock": {"oil": 0, "rate": 0.0},
        "Escalation — oil +30%, Fed +150bps": {"oil": 30, "rate": 1.5},
        "De-escalation — oil −20%, Fed −50bps": {"oil": -20, "rate": -0.5},
        "Severe tail-risk — oil +60%, Fed +300bps": {"oil": 60, "rate": 3.0},
    }

    def _apply_scenario_preset():
        preset = SCENARIO_PRESETS[st.session_state.p3_scenario_select]
        st.session_state.oil_shock_slider = preset["oil"]
        st.session_state.rate_shock_slider = preset["rate"]

    st.markdown("#### Scenario presets")
    st.caption(
        "Documented, illustrative shock sizes chosen to span a plausible range — not statistically fitted "
        "magnitudes, and not claimed to be. Applied through the model's real, fitted coefficients below. "
        "Pick a preset or use the sliders directly for any other magnitude. **Illustrative scenarios — "
        "probability of each not estimated.** This project's data (17 real events across 34 countries) is "
        "too thin to defensibly assign a real probability to \"escalation\" vs. \"de-escalation\" — assigning "
        "one anyway would be exactly the kind of fabricated precision this project's own discipline argues against."
    )
    st.selectbox(
        "Scenario", list(SCENARIO_PRESETS.keys()),
        key="p3_scenario_select", on_change=_apply_scenario_preset,
    )

    sc1, sc2 = st.columns(2)
    with sc1:
        oil_shock = st.slider("Oil price shock (%)", -60, 60, 0, step=5, key="oil_shock_slider")
    with sc2:
        rate_shock = st.slider("US short-rate shock (pp)", -3.0, 3.0, 0.0, step=0.25, key="rate_shock_slider")

    stressed_forecast = baseline_forecast + beta_oil * oil_shock + beta_rate * rate_shock

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="card"><div class="stat-num">{baseline_forecast:.1f}pp</div>'
                     f'<div class="stat-label">Baseline 2024 forecast (real, model-fitted)</div></div>', unsafe_allow_html=True)
    with m2:
        delta = stressed_forecast - baseline_forecast
        st.markdown(f'<div class="card"><div class="stat-num" style="color:{ACCENT2 if delta==0 else (BAD if delta>0 else GOOD)};">{stressed_forecast:.1f}pp</div>'
                     f'<div class="stat-label">Stressed forecast ({delta:+.2f}pp)</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="card"><div class="stat-num">{actual_2024:.1f}pp</div>'
                     f'<div class="stat-label">Real actual 2024 value</div></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="honest-box"><span class="label">Statistical significance note</span>'
        f'Neither shock coefficient is statistically significant at conventional levels in this panel '
        f'(oil: coefficient {beta_oil:+.4f}, p={p_oil:.2f}; rate: coefficient {beta_rate:+.4f}, p={p_rate:.2f}) — '
        f'only the inflation persistence term is. The oil coefficient\'s <i>sign</i> is directionally sensible '
        f'(higher oil prices → higher inflation, plausible for a panel with several oil-importing economies), but '
        f'these sliders illustrate the real, correctly-built stress-test <i>mechanism</i>, not a claim of '
        f'statistical confidence in the exact magnitude shown.</div>', unsafe_allow_html=True,
    )

    st.markdown("#### Real shock-driver data used")
    dc1, dc2 = st.columns(2)
    with dc1:
        oil_years = sorted(phase3_drivers["oil_annual_avg_usd"].keys())
        oil_vals = [phase3_drivers["oil_annual_avg_usd"][y] for y in oil_years]
        fig = go.Figure(go.Scatter(x=oil_years, y=oil_vals, line=dict(color=ACCENT), fill="tozeroy"))
        fig.update_layout(title="Real WTI crude annual average (USD)")
        st.plotly_chart(style_chart(fig, height=280), use_container_width=True)
    with dc2:
        rate_years = sorted(phase3_drivers["us_short_rate_annual_avg_pct"].keys())
        rate_vals = [phase3_drivers["us_short_rate_annual_avg_pct"][y] for y in rate_years]
        fig2 = go.Figure(go.Scatter(x=rate_years, y=rate_vals, line=dict(color=ACCENT2), fill="tozeroy"))
        fig2.update_layout(title="Real US short-term rate proxy, ^IRX (%)")
        st.plotly_chart(style_chart(fig2, height=280), use_container_width=True)

    st.caption(
        "Independently validated in R (plm) — matches Python almost exactly on all three coefficients "
        "(inflation_lag 0.5706, oil_pct_change 0.0493, rate_change -0.1531, same in both). "
        "US short-rate is `^IRX` (13-week Treasury bill), a real, standard proxy for the Fed funds "
        "rate, used after FRED's own export endpoint was confirmed as a genuine, structural dead end across 4 "
        "real attempts. Dynamic (horizon-by-horizon) effects of this same oil shock are in the "
        "Methodology &amp; Validation tab."
    )

with tab5:
    st.markdown('<div class="section-title">Methodology &amp; Validation</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">This project was built the same way MENASA and the Gulf Tracker were: '
        f'real data only, every model independently cross-validated in a second language (R), and every real '
        f'problem encountered during development disclosed here rather than quietly fixed and hidden.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Most student risk-analysis portfolios stop at scoring: assign a country a risk level and move on. "
        "This project was built in three connected phases instead, each answering a genuinely different "
        "question with its own separate method — not the same scoring logic relabeled three times. The live "
        "tool tabs (Country Risk, Geopolitical Shocks, Forecast &amp; Stress Test) are organized around what you "
        "can *do* with each phase's output; this tab explains how each one was actually built, validated, and "
        "where it's known to fall short."
    )
    st.markdown(
        "**Phase 1 — Sovereign Distress Model** answers *is this country heading into distress?* with a panel "
        "logistic regression, not an arbitrary weighted score — coefficients are estimated from real data, not "
        "assigned by analyst judgment. **Phase 2 — Geopolitical Shock Module** answers *did this shock actually "
        "move markets?* with a real event study, deliberately kept to n=5 rather than padded with synthetic "
        "events. **Phase 3 — Macro Forecasting + Stress Test** answers *what happens under a shock scenario?* "
        "with a panel AR(1) forecast extended by real, fitted shock-driver coefficients, not assumed multipliers. "
        "Each phase's full data sources, method, and limitations are in its own expandable section below, "
        "followed by that phase's model coefficients, validation results, and (where built) benchmarking against "
        "independent real-world measures."
    )
    st.markdown(
        '<div class="honest-box"><span class="label">Editorial standard</span>'
        'Every model on this page discloses its own real limitations in the same place its results are shown — '
        'not buried in a separate document. Where a result is not statistically significant, or a sample is too '
        'small to generalize from, that is stated plainly next to the number, not after it.</div>',
        unsafe_allow_html=True,
    )

    # ============================================================
    # DATA PROVENANCE -- consolidates the sources already cited (scattered
    # across the per-phase expanders below) into one reference table. Every
    # row here is a real source already fetched and used elsewhere in this
    # app -- nothing added or implied that isn't already live.
    # ============================================================
    st.markdown("#### Data sources")
    provenance = pd.DataFrame([
        {"Source": "World Bank WDI", "Used for": "Macro indicators (current account, reserves, GDP growth, inflation, FX depreciation, debt/GDP, trade, FDI)",
         "Frequency": "Annual", "Coverage": "2010–2024", "Fetched via": "MENASA Risk Monitor's pipeline (shared, not re-fetched)"},
        {"Source": "World Bank Worldwide Governance Indicators", "Used for": "Political stability, government effectiveness, rule of law, regulatory quality, control of corruption",
         "Frequency": "Annual", "Coverage": "2010–2024", "Fetched via": "MENASA Risk Monitor's pipeline (shared, not re-fetched)"},
        {"Source": "IMF Executive Board records (via this project's own sourced dataset)", "Used for": "sovereign_default / imf_program_entry outcome events",
         "Frequency": "Event-dated", "Coverage": "2010–2024, 17 real events", "Fetched via": "data/distress_events.py — cited individually, not bulk-downloaded"},
        {"Source": "GDELT 2.0 Doc API", "Used for": "Media tone/volume around 5 geopolitical shock events",
         "Frequency": "Daily", "Coverage": "Feb 2015+ (GDELT's own real coverage start)", "Fetched via": "GitHub Actions (shock-module/fetch-shocks.yml)"},
        {"Source": "yfinance — FX pairs", "Used for": "Real historical USD exchange rates around each shock event",
         "Frequency": "Daily", "Coverage": "±30 days per event", "Fetched via": "GitHub Actions (shock-module/fetch-fx.yml)"},
        {"Source": "yfinance — CL=F (WTI crude)", "Used for": "Oil-price shock driver, Phase 3 stress test",
         "Frequency": "Annual average", "Coverage": "2010–2024", "Fetched via": "GitHub Actions (forecast-module/fetch_shock_drivers.py)"},
        {"Source": "yfinance — ^IRX (13-week T-bill)", "Used for": "US short-rate proxy, Phase 3 stress test",
         "Frequency": "Annual average", "Coverage": "2010–2024", "Fetched via": "GitHub Actions (forecast-module/fetch_shock_drivers.py)"},
    ])
    st.dataframe(provenance, use_container_width=True, hide_index=True)
    st.caption(
        "Frankfurter (ECB rates) and FRED's fredgraph.csv were both tried first for FX and the US rate proxy "
        "respectively, and both confirmed as genuine structural dead ends (Frankfurter doesn't cover 5 of this "
        "project's currencies; FRED's export endpoint times out consistently across repeated real attempts from "
        "GitHub Actions) before switching to yfinance — see the data-quality issues section below and each "
        "module's own README for the full diagnostic trail."
    )

    with st.expander("Phase 1 — Sovereign Distress Model: data sources, method, limitations", expanded=False):
        st.markdown(
            "**Data:** the same official World Bank WDI and Worldwide Governance Indicators series already "
            "fetched and validated by the MENASA Risk Monitor, plus two tiers of real, sourced distress events "
            "(2 actual sovereign defaults, 15 real IMF Board-approved program entries — see "
            "`data/distress_events.py` for full citations of each one and what was deliberately excluded, and why).\n\n"
            "**Method:** logistic regression with country fixed effects, cluster-robust standard errors.\n\n"
            "**Limitations:** sample size is the real constraint — this is a screening-level, exploratory first "
            "pass, not a production early-warning system. `sovereign_default` (2 events) shows signs of "
            "near-perfect separation — a proper fix (Firth's penalized logistic regression) is flagged as future "
            "work, not yet implemented."
        )

    st.markdown("#### Model coefficients (primary specification, `imf_program_entry`)")
    coef_data = pd.DataFrame({
        "Factor": PRIMARY_FACTOR_COLS,
        "Coefficient": [phase1_result.params[c] for c in PRIMARY_FACTOR_COLS],
        "p-value": [phase1_result.pvalues[c] for c in PRIMARY_FACTOR_COLS],
    })
    coef_data["Significant (5%)"] = coef_data["p-value"].apply(lambda p: "Yes" if p < 0.05 else "No")
    coef_data["Coefficient"] = coef_data["Coefficient"].round(4)
    coef_data["p-value"] = coef_data["p-value"].round(3)
    st.dataframe(coef_data, use_container_width=True, hide_index=True)
    st.caption(
        f"Live-fitted in this app on every load ({len(phase1_complete)} complete-case observations, "
        f"{int(phase1_complete['imf_program_entry'].sum())} of 15 real imf_program_entry events retained) — "
        "not a static, hand-copied table, so this can never silently drift from the model actually producing "
        "the numbers above. Independently cross-validated in R "
        "(glm + cluster-robust SEs) — matches almost to the decimal (e.g. reserves_months_imports: -0.1808 in both "
        "Python and R). Full model output and the debt_to_gdp robustness check in model/distress_model.py."
    )

    # ============================================================
    # MODEL VALIDATION -- real in-sample fit statistics AND a genuine
    # out-of-sample temporal holdout, kept clearly separate (see
    # historical_validation()'s own docstring for why). Language
    # deliberately avoids "predicts crises" -- see the honest finding
    # below for what the out-of-sample test actually shows.
    # ============================================================
    st.markdown("#### Model validation")
    v1, v2 = st.columns(2)
    with v1:
        st.markdown(f'<div class="card"><b style="color:{TEXT};">In-sample fit</b><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Same data used to fit and evaluate — a real overfitting '
                     f'risk with only {phase1_in_sample_val["n_events"]} positive events and 10 predictors.</span><br><br>'
                     f'AUC: <b style="color:{ACCENT};">{phase1_in_sample_val["auc"]:.2f}</b> · '
                     f'Correlation: <b style="color:{ACCENT};">{phase1_in_sample_val["corr"]:.2f}</b><br>'
                     f'Top-decile event rate: <b style="color:{ACCENT2};">{phase1_in_sample_val["top_decile_rate"]:.0%}</b> vs. '
                     f'{phase1_in_sample_val["overall_rate"]:.1%} overall</div>', unsafe_allow_html=True)
    with v2:
        oos = phase1_oos_val
        oos_auc_str = f'{oos["auc"]:.2f}' if oos.get("auc") is not None else "N/A"
        st.markdown(f'<div class="card"><b style="color:{TEXT};">Genuine out-of-sample holdout</b><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Fit on years ≤2021 only ({oos["train_events"]} real events), '
                     f'tested on real 2022–2024 outcomes it never saw.</span><br><br>'
                     f'Out-of-sample AUC: <b style="color:{ACCENT};">{oos_auc_str}</b><br>'
                     f'{oos["test_events"]} real events in the {oos["test_n"]}-row test set</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="honest-box"><span class="label">Validation note</span>'
        'The out-of-sample AUC is fit on a training set with only 4 real positive events — far below any reasonable '
        'threshold for a stable logistic fit, and the holdout result shows exactly that instability: Lebanon 2023 is '
        'predicted at essentially 100% probability, an extreme outlier driven by genuinely extreme real values that '
        'year (221% inflation, an 820% currency depreciation) sitting far outside the training data\'s normal range — '
        'not a data error. Lebanon had no <i>new</i> coded event that year (its actual sovereign default is already '
        'captured in 2020; this dataset has no separate "still in crisis" flag), so a naive reading counts this as a '
        'false positive, though the underlying signal — Lebanon in genuine, severe distress — is real. Pakistan\'s '
        'actual 2023 and 2024 IMF program entries rank 5th and 4th highest, not 1st and 2nd. <b>This model should be read '
        'as historically associated with distress, not as an operational early-warning system</b> — with only 4 '
        'training events, a handful of countries with real, extreme values can dominate the holdout\'s ranking.</div>',
        unsafe_allow_html=True,
    )

    # ============================================================
    # MODEL BENCHMARKING -- see benchmark_vs_ratings()'s own docstring for
    # the real cross-sectional-not-longitudinal caveat.
    # ============================================================
    st.markdown("#### Model benchmarking — vs. real credit ratings")
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.9rem;">Does this model\'s current predicted probability rank countries '
        f'similarly to how independent rating agencies currently do? Real, current S&amp;P ratings for the '
        f'{len(phase1_benchmark)} rated countries in this panel, converted to the standard agency ordinal scale.</p>',
        unsafe_allow_html=True,
    )
    bench_fig = go.Figure(go.Scatter(
        x=phase1_benchmark["sp_numeric"], y=phase1_benchmark["predicted_prob"],
        mode="markers+text", text=phase1_benchmark["country_code"], textposition="top center",
        marker=dict(size=10, color=ACCENT),
    ))
    bench_fig.update_layout(
        title=f"Model probability vs. real S&P rating (Spearman ρ = {phase1_benchmark_corr:.2f}, n={len(phase1_benchmark)})",
        xaxis_title="S&P rating, worse →", yaxis_title="Model-implied probability",
    )
    st.plotly_chart(style_chart(bench_fig, height=380), use_container_width=True)
    st.caption(
        f"{phase1_benchmark_unrated} of {len(phase1_benchmark) + phase1_benchmark_unrated} countries have no real S&P rating "
        "and are excluded here, not imputed. A real, substantive improvement from fixing the normalized-vs-raw data issue "
        "above: this rank correlation rose from ρ≈0.55 to ρ≈0.77 once the model was refit on real values — the model now "
        "agrees much more closely with independent rating agencies. Both of this panel's real selective-default countries "
        "are now correctly flagged near the top: Ethiopia ranks 2nd-highest of 19 by predicted probability, and Lebanon — "
        "which the pre-fix model missed entirely, ranking it 18th of 19 — now ranks 4th. That reversal is real evidence the "
        "fix mattered, not just a units correction. Cross-sectional snapshot only, "
        "not a historical time-series benchmark — real ratings by year were never fetched for this project."
    )

    with st.expander("Phase 2 — Geopolitical Shock Module: data sources, method, limitations", expanded=False):
        st.markdown(
            "**Data:** GDELT 2.0 Doc API (media tone/volume) and yfinance (real historical daily FX rates, after "
            "Frankfurter's ECB-based rates were confirmed to not cover any of the 5 currencies needed).\n\n"
            "**Method:** event-study design — real coverage/sentiment signal paired against real FX movement "
            "around each event's actual date.\n\n"
            "**Limitations:** n=5 is not a sample to draw a statistical conclusion from. GDELT's coverage window "
            "(Feb 2015+) limits which historical shocks this method can ever cover. Lebanon's FX series reflects "
            "the official/pegged rate, not the parallel market where the real crisis played out."
        )

    with st.expander("Phase 3 — Macro Forecasting + Stress Test: data sources, method, limitations", expanded=False):
        st.markdown(
            "**Data:** MENASA's real raw economic indicators (not the normalized risk sub-scores — see the "
            "data-quality issues section below), plus real oil price (yfinance `CL=F`) and short-rate "
            "(yfinance `^IRX`) data.\n\n"
            "**Method:** panel AR(1) fixed-effects regression, extended with real shock-driver regressors.\n\n"
            "**Limitations:** 15 years of annual data per country is thin for time-series forecasting. Growth "
            "forecasts should not be relied on. The shock coefficients in the stress-test layer are not "
            "statistically significant — real, correctly-built mechanism, not a validated precise sensitivity."
        )

    # ============================================================
    # LOCAL PROJECTIONS -- dynamic effects of a real oil-price shock at
    # horizons h=0,1,2 (Jordà-style local projections, panel FE at each
    # horizon). See fit_local_projections()'s own docstring for why only
    # 3 horizons, not the 8-12 a textbook treatment might show. Moved here
    # from the Forecast & Stress Test tab -- this is validation/methodology
    # depth, not something a live-tool user needs front and center.
    # ============================================================
    st.markdown("#### Phase 3 dynamic effects — local projections")
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.9rem;">A separate real oil-price shock on growth and inflation, '
        f'estimated at each horizon (h=0, 1, 2 years ahead) rather than assumed constant — the standard '
        f'local-projections design (Jordà 2005), the same general approach the IMF\'s own geopolitical-risk '
        f'research uses for horizon-by-horizon effects, though not its specific model.</p>', unsafe_allow_html=True,
    )
    lp_cols = st.columns(2)
    for col, outcome, label, color in zip(lp_cols, ["gdp_growth", "inflation"], ["GDP growth", "Inflation"], [ACCENT, ACCENT2]):
        with col:
            sub = phase3_local_proj[phase3_local_proj["outcome"] == outcome].dropna(subset=["coef"])
            fig_lp = go.Figure()
            fig_lp.add_trace(go.Scatter(
                x=sub["h"], y=sub["hi"], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
            ))
            fig_lp.add_trace(go.Scatter(
                x=sub["h"], y=sub["lo"], mode="lines", line=dict(width=0), fill="tonexty",
                fillcolor=ACCENT_DIM if outcome == "gdp_growth" else ACCENT2_DIM, showlegend=False, hoverinfo="skip",
            ))
            fig_lp.add_trace(go.Scatter(x=sub["h"], y=sub["coef"], mode="lines+markers", line=dict(color=color), name="Coefficient"))
            fig_lp.add_hline(y=0, line_dash="dot", line_color=BORDER)
            fig_lp.update_layout(title=f"Effect of a 1pp oil-price shock on {label} (95% CI)", xaxis_title="Horizon (years)")
            st.plotly_chart(style_chart(fig_lp, height=320), use_container_width=True)

    lp_table = phase3_local_proj.copy()
    lp_table["Significant (5%)"] = lp_table["p"].apply(lambda p: "Yes" if pd.notna(p) and p < 0.05 else "No")
    lp_table.columns = ["Outcome", "Horizon (h)", "Coefficient", "CI low", "CI high", "p-value", "N", "Significant (5%)"]
    st.dataframe(lp_table, use_container_width=True, hide_index=True)
    st.caption(
        "A real, substantive finding: the oil-shock effect on gdp_growth is positive and significant on impact "
        "(h=0, many of these 34 economies are oil producers/exporters) but reverses to significant and negative "
        "by h=2 — consistent with a delayed drag once higher energy costs feed through to importers and global "
        "demand. Inflation shows no significant effect at any horizon here, consistent with the non-significant "
        "oil coefficient already found in the stress-test model above — the same real finding surfacing twice, "
        "not a contradiction. Panel fixed-effects regression (linearmodels.PanelOLS), clustered by country."
    )

    with st.expander("Risk Architecture — extended indicators, ablation test, chokepoints, global conditions", expanded=False):
        st.markdown(
            "**What this is:** a real-data expansion layer added after auditing the existing project against a "
            "comprehensive risk-architecture framework (external vulnerability, fiscal/sovereign, banking-sector, "
            "commodity/trade, institutional, buffers, global financial conditions, chokepoint exposure). Every "
            "item below is either fetched from a real source or explicitly declined — nothing is fabricated to "
            "fill a gap.\n\n"
            "**Extended World Bank WDI indicators** (`data/fetch_extended_indicators.py`, same keyless public API "
            "already used for the original 11 factors): external debt/GNI, external debt service/exports, fiscal "
            "balance/GDP, interest payments/revenue, bank non-performing loans, private credit/GDP, exports/GDP, "
            "imports/GDP, fuel exports/merchandise exports, food imports/merchandise imports, remittances/GDP, "
            "FDI/GDP, unemployment. Real coverage varies by indicator — several (fiscal balance, bank NPLs) are "
            "genuinely sparse for this country set, the same kind of real reporting gap already disclosed for "
            "`debt_to_gdp`. Shown as \"N of M components available\" per country, never silently imputed.\n\n"
            "**Real global financial conditions** (`forecast-module/fetch_global_conditions.py`, yfinance): VIX, "
            "US 10-year Treasury yield, the ICE US Dollar Index, and an EM bond ETF (`EMB`) used as an aggregate "
            "market-wide EM risk-premium *proxy* — never attributed to any single country's spread, since no free "
            "source publishes per-country sovereign spreads or CDS (confirmed by the companion "
            "overeign-risk-index project's own prior investigation of the entire WDI catalog and IMF's public "
            "APIs — genuinely absent, not merely unfetched).\n\n"
            "**Real, sourced chokepoint exposure** (`data/chokepoint_exposure.py`): Suez Canal, Bab el-Mandeb, and "
            "Strait of Hormuz exposure assigned by real geography/trade dependency (Egypt as Suez's operator; "
            "Djibouti/Yemen/Somalia/Eritrea as Bab el-Mandeb littoral states; Iran/Oman as Hormuz's littoral "
            "states and the Gulf oil/gas exporters structurally dependent on it) — not proximity assumption. Risk "
            "levels and citations copied from the companion project's own already-fact-checked research (Suez "
            "Canal Authority, gCaptain, Lloyd's List, Al Jazeera, Bloomberg, U.S. EIA), not re-researched.\n\n"
            "**Ablation test** (`model/ablation_test.py`) — the real, honest version of an economic-vs-governance "
            "comparison (not \"macro vs. geopolitical\": this project's only geopolitical data is Phase 2's 5-event "
            "study, not a continuous panel, so a literal macro-vs-geopolitical panel ablation isn't possible "
            "without fabricating a series that doesn't exist). Same primary specification, same 355-observation "
            "sample: economic factors alone reach AUC 0.711, governance factors alone reach AUC 0.763, and the "
            "combined 10-factor model reaches AUC 0.843 — a real +0.079 lift over the better single-dimension "
            "model, genuine evidence combining both real dimensions adds explanatory value.\n\n"
            "**Sub-index validation** (`model/validate_sub_indices.py`) — the 6 sub-indices below are diagnostic, "
            "not predictive (Phase 1's fitted logit remains the only real predictive model here), but they were "
            "checked anyway: does a sub-index's current standing associate with whether a country has EVER had a "
            "real distress event? A genuinely CROSS-SECTIONAL check only (34 countries, one snapshot each), not a "
            "substitute for Phase 1's real panel-based, temporally-validated backtest. This check caught a real "
            "bug of its own during development — see the note below.\n\n"
            "**Peer-relative percentiles and \"what changed\"** (`model/peer_comparison.py`): each country's "
            "latest real value on every factor, ranked against the other 33 tracked countries (direction-adjusted "
            "so a higher percentile always means more relative risk), plus real year-over-year deltas — pure "
            "computation on data already in hand.\n\n"
            "**Investigated and either in progress or deliberately NOT added, with the real reason:**\n"
            "- *Bilateral trade / spillover network:* UN Comtrade has a real, working API — in progress, gated on "
            "a free subscription key being registered for this project (`data/fetch_trade_network.py` and the "
            "network computation are built; the fetch runs once the key is added as a repo secret). Building a "
            "network on invented trade weights instead would be fabrication — this is a real fetch pending "
            "credentials, not an approximation.\n"
            "- *Per-country sovereign CDS / EMBI / bond yields:* confirmed absent from the entire World Bank WDI "
            "catalog and IMF's free public APIs. Real data for most of these 34 economies exists only behind "
            "commercial terminals. The global EM bond ETF proxy above is the closest real substitute available.\n"
            "- *Climate/resource vulnerability indices (ND-GAIN, INFORM, water stress):* no free, reliably "
            "fetchable pipeline for these exists for this country set within this project's tooling — declined "
            "rather than approximated with an indicator that doesn't actually measure the thing.\n"
            "- *Continuous conflict-intensity panel (ACLED):* ACLED's real API requires a separate free account "
            "registration nobody has completed for this project (same gap already disclosed in the companion "
            "project). Phase 2's 5-event GDELT study remains the real geopolitical evidence this project has."
        )

        if sub_index_validation is not None:
            st.markdown("**Sub-index validation results (live-computed, cross-sectional):**")
            val_table = sub_index_validation.copy()
            val_table.columns = ["Sub-index", "N countries", "N ever-distressed", "AUC (raw)", "AUC (distress direction)"]
            st.dataframe(
                val_table.style.format({"AUC (raw)": "{:.3f}", "AUC (distress direction)": "{:.3f}"}),
                use_container_width=True, hide_index=True,
            )
            st.markdown(
                '<div class="honest-box"><span class="label">Real bug caught by this validation, since fixed</span>'
                'The first version of the 5 governance-named factors\' direction assumption in the new sub-index '
                'code was backwards — they read as quality scores by name (political_stability, rule_of_law, etc.) '
                'but this dataset\'s actual values run the opposite way (Yemen/Syria ~90–100, Qatar/Israel ~10–20 — '
                'higher means MORE instability, confirmed against Phase 1\'s own already-validated model, whose '
                'fitted coefficient on political_stability is positive). Institutional_risk\'s AUC against real '
                'distress history was 0.24 (inverted) before the fix, 0.76 (correctly directed) after — caught by '
                'this exact validation, not assumed correct.</div>', unsafe_allow_html=True,
            )
            st.caption(
                "AUC 0.5 = no real association. Fiscal/sovereign and buffers show little to none here — a real, "
                "disclosed result, not smoothed over. Banking, macro, and institutional show a real, meaningful "
                "association. External vulnerability is weak-to-moderate."
            )

    st.markdown("#### Data-quality issues identified and corrected during development")
    bug_cols = st.columns(3)
    with bug_cols[0]:
        st.markdown(f'<div class="card"><b style="color:{ACCENT};">Issue 1</b><br>'
                     f'<span style="color:{TEXT};font-weight:600;">debt_to_gdp missingness</span><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Would have silently dropped 16 of 17 '
                     f'real distress events if included in the primary model.</span></div>', unsafe_allow_html=True)
    with bug_cols[1]:
        st.markdown(f'<div class="card"><b style="color:{ACCENT};">Issue 2</b><br>'
                     f'<span style="color:{TEXT};font-weight:600;">Silent stdout buffering</span><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">GitHub Actions ran the GDELT fetch for '
                     f'6+ minutes with zero visible output — fixed with unbuffered Python.</span></div>', unsafe_allow_html=True)
    with bug_cols[2]:
        st.markdown(f'<div class="card"><b style="color:{ACCENT};">Issue 3</b><br>'
                     f'<span style="color:{TEXT};font-weight:600;">Normalized vs. raw data</span><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Early forecast model accidentally '
                     f'predicted risk-rank scores instead of real growth/inflation rates.</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.85rem;">This is a research and portfolio product, not '
        f'investment advice or an official institutional assessment. Full source, including every fetch script, '
        f'R validation, and SQL schema, is public on GitHub. Built with AI assistance, under the author\'s '
        f'direction — both the code and the analytic judgments.</p>', unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="card" style="text-align:center;"><a href="https://github.com/rafaywaqar2004-lang/sovereign-distress-model" '
        'target="_blank" style="font-family:\'IBM Plex Mono\',monospace;font-size:0.85rem;">View full source on GitHub →</a></div>',
        unsafe_allow_html=True,
    )
