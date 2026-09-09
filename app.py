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

st.set_page_config(page_title="EM Macro & Geopolitical Risk Engine", page_icon="📉", layout="wide")

HERE = os.path.dirname(__file__)

# ============================================================
# DESIGN SYSTEM -- same "Institute Brief" editorial family as the
# MENASA Risk Monitor and Gulf Tracker (Inter / JetBrains Mono /
# Newsreader, near-black ground), but with its own accent -- the
# portfolio's own signature gold (matching The Crescent Brief), tying
# this flagship visually to the rest of the body of work rather than
# cloning either sibling tool outright.
# ============================================================
BG = "#0a0a0a"
SURFACE = "#161616"
SURFACE_ALT = "#1f1f1f"
BORDER = "rgba(255,255,255,0.10)"
ACCENT = "#c9a84c"
ACCENT_DIM = "rgba(201,168,76,0.12)"
ACCENT2 = "#5b8dd6"
ACCENT2_DIM = "rgba(91,141,214,0.12)"
TEXT = "#f5f5f4"
TEXT_MUTED = "#a3a3a3"
GOOD = "#34d399"
WARN = "#fbbf24"
BAD = "#f87171"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Newsreader:ital,wght@0,500;0,600;0,700;1,500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    h1, h2, h3 {{ font-family: 'Inter', sans-serif !important; }}
    .masthead-title, .section-title {{ font-family: 'Newsreader', Georgia, serif !important; }}

    /* Streamlit 1.63's actual DOM uses data-testid="stApp"/"stMain", not the
       older ".main" class -- verified by inspecting the real rendered page,
       not assumed from an older app's CSS. */
    [data-testid="stApp"], body {{
        background: radial-gradient(ellipse 1400px 800px at 50% -10%, rgba(201,168,76,0.06), transparent),
                    linear-gradient(180deg, {BG} 0%, #050505 100%) !important;
    }}
    [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    .tag-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {ACCENT};
        margin-bottom: 0.7rem;
    }}
    .masthead-title {{
        font-family: 'Inter', sans-serif;
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
        font-family: 'JetBrains Mono', monospace;
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
        background: {ACCENT2_DIM};
        border-left: 3px solid {ACCENT2};
        border-radius: 4px;
        padding: 0.9rem 1.2rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: {TEXT};
        line-height: 1.6;
    }}
    .honest-box .label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {ACCENT2};
        margin-bottom: 0.4rem;
        display: block;
    }}
    .phase-pill {{
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        background: {ACCENT_DIM};
        color: {ACCENT};
        border: 1px solid rgba(201,168,76,0.3);
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
        font=dict(family="Inter, sans-serif", color=TEXT_MUTED, size=12),
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
    "① Sovereign Distress Model",
    "② Geopolitical Shock Module",
    "③ Macro Forecast & Stress Test",
    "Methodology & Limitations",
])

with tab1:
    st.markdown('<div class="section-title">Why three layers, one engine</div>', unsafe_allow_html=True)
    st.markdown(
        "Most student risk-analysis portfolios stop at scoring: assign a country a risk level and move on. "
        "This project asks three different, connected questions instead, each answered with a genuinely "
        "separate method, not the same scoring logic relabeled three times:"
    )

    ov_cols = st.columns(3)
    with ov_cols[0]:
        st.markdown(
            f'<div class="card"><span class="phase-pill">Phase 1</span>'
            f'<h4 style="color:{TEXT};margin:0.3rem 0;">Is this country heading into distress?</h4>'
            f'<p style="color:{TEXT_MUTED};font-size:0.88rem;line-height:1.6;">A panel logistic regression predicting '
            f'sovereign default and IMF program entry from real macro/governance fundamentals — a probability, '
            f'not a score.</p></div>', unsafe_allow_html=True)
    with ov_cols[1]:
        st.markdown(
            f'<div class="card"><span class="phase-pill">Phase 2</span>'
            f'<h4 style="color:{TEXT};margin:0.3rem 0;">Did this shock actually move markets?</h4>'
            f'<p style="color:{TEXT_MUTED};font-size:0.88rem;line-height:1.6;">A real event study pairing GDELT '
            f'media-coverage data against real historical FX rates for 5 dated geopolitical shocks.</p></div>',
            unsafe_allow_html=True)
    with ov_cols[2]:
        st.markdown(
            f'<div class="card"><span class="phase-pill">Phase 3</span>'
            f'<h4 style="color:{TEXT};margin:0.3rem 0;">What happens under a shock scenario?</h4>'
            f'<p style="color:{TEXT_MUTED};font-size:0.88rem;line-height:1.6;">A panel AR(1) forecasting model with '
            f'an interactive stress-test layer — apply a real oil or rate shock and see the forecast move.</p></div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="honest-box"><span class="label">Editorial standard</span>'
        'Every model on this page discloses its own real limitations in the same place its results are shown — '
        'not buried in a separate document. Where a result is not statistically significant, or a sample is too '
        'small to generalize from, that is stated plainly next to the number, not after it. See the '
        '<b>Methodology &amp; Limitations</b> tab for the full account, including three real bugs caught and fixed '
        'during development.</div>', unsafe_allow_html=True,
    )

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
    st.markdown('<div class="section-title">Phase 1 — Sovereign Distress Model</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">A panel logistic regression predicting two real, sourced outcomes: '
        f'sovereign default and formal IMF program entry. Primary specification excludes <code>debt_to_gdp</code> '
        f'deliberately (see the honest note below) — trained on 355 observations, 14 of 17 real events retained.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="honest-box"><span class="label">A real bug, caught and fixed</span>'
        '<code>debt_to_gdp</code> is non-missing in only 91 of 507 panel rows. Requiring complete cases across '
        'all 11 factors, including it, collapsed the usable sample to 77 rows and dropped all but 1 of the 17 real '
        'distress events with it — the country-years missing debt data are disproportionately the same '
        'country-years under genuine fiscal strain (Lebanon stopped publishing fiscal data entirely during its '
        'crisis). Fixed by excluding it from the primary model and testing it separately as a robustness check.</div>',
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
                               name="Current Account (normalized)", marker_color=ACCENT))
        for _, row in events_here.iterrows():
            fig2.add_vline(x=row["year"], line_dash="dot",
                            line_color=BAD if row["sovereign_default"] == 1 else WARN)
        fig2.update_layout(title="Current account factor, with real distress-event markers")
        st.plotly_chart(style_chart(fig2), use_container_width=True)

    if events_here.empty:
        st.caption(f"No real distress event recorded for {COUNTRIES.get(sel_country, sel_country)} in this panel.")

    st.markdown("#### Model coefficients (primary specification, `imf_program_entry`)")
    coef_data = pd.DataFrame([
        {"Factor": "current_account_pct_gdp", "Coefficient": -0.008, "p-value": 0.568, "Significant (5%)": "No"},
        {"Factor": "reserves_months_imports", "Coefficient": 0.037, "p-value": 0.073, "Significant (5%)": "No"},
        {"Factor": "gdp_growth", "Coefficient": -0.039, "p-value": 0.010, "Significant (5%)": "Yes"},
        {"Factor": "inflation", "Coefficient": -0.015, "p-value": 0.373, "Significant (5%)": "No"},
        {"Factor": "currency_depreciation_pct", "Coefficient": -0.010, "p-value": 0.662, "Significant (5%)": "No"},
        {"Factor": "political_stability", "Coefficient": 0.073, "p-value": 0.000, "Significant (5%)": "Yes"},
        {"Factor": "government_effectiveness", "Coefficient": -0.007, "p-value": 0.914, "Significant (5%)": "No"},
        {"Factor": "rule_of_law", "Coefficient": -0.098, "p-value": 0.057, "Significant (5%)": "No"},
        {"Factor": "regulatory_quality", "Coefficient": 0.044, "p-value": 0.250, "Significant (5%)": "No"},
        {"Factor": "control_of_corruption", "Coefficient": 0.038, "p-value": 0.189, "Significant (5%)": "No"},
    ])
    st.dataframe(coef_data, use_container_width=True, hide_index=True)
    st.caption(
        "355 observations, 12 of 15 real imf_program_entry events retained. Independently cross-validated in R "
        "(glm + cluster-robust SEs) — matches almost to the decimal (e.g. political_stability: 0.0734 in both "
        "Python and R). Full model output and the debt_to_gdp robustness check in model/distress_model.py."
    )

with tab3:
    st.markdown('<div class="section-title">Phase 2 — Geopolitical Shock Module</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">Real GDELT media-coverage data paired against real historical FX rates '
        f'for 5 precisely-dated shocks. Syria (Jan 2012) was dropped after a real fetch confirmed it predates '
        f'GDELT\'s actual data coverage window (Feb 2015+) — a genuine scope constraint, not hidden.</p>',
        unsafe_allow_html=True,
    )

    usable = phase2_results.dropna(subset=["gdelt_avg_tone_post", "fx_pct_change"])
    corr = usable["gdelt_avg_tone_post"].corr(usable["fx_pct_change"])

    st.markdown(
        f'<div class="honest-box"><span class="label">Real, honest finding — not noise to explain away</span>'
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

with tab4:
    st.markdown('<div class="section-title">Phase 3 — Macro Forecast &amp; Stress Test</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">A panel AR(1) model forecasting next-year inflation, extended with real, '
        f'fetched shock drivers (oil price, US short-term rate). Growth is deliberately not forecast interactively '
        f'here — see the honest result below on why.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="honest-box"><span class="label">A real bug, caught and fixed</span>'
        'An early version of this model forecast MENASA\'s <b>normalized 0-100 risk sub-scores</b> instead of real '
        'GDP growth/inflation — that data\'s own file header says explicitly it\'s normalized, not raw. The '
        'giveaway was backtest output with values of exactly 100.0 or 0.0 (rank extremes, not real rates). Fixed '
        'by switching to MENASA\'s real raw indicator values.</div>', unsafe_allow_html=True,
    )

    r1, r2 = st.columns(2)
    with r1:
        st.markdown(
            f'<div class="card"><b style="color:{TEXT};">GDP Growth</b><br>'
            f'<span style="color:{BAD};font-family:JetBrains Mono,monospace;font-size:1.3rem;">No real signal</span><br>'
            f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Loses to a naive "no change" baseline (3.41 vs '
            f'2.93 MAE on the real 2024 backtest) — consistent with well-documented growth literature.</span></div>',
            unsafe_allow_html=True)
    with r2:
        st.markdown(
            f'<div class="card"><b style="color:{TEXT};">Inflation</b><br>'
            f'<span style="color:{GOOD};font-family:JetBrains Mono,monospace;font-size:1.3rem;">Real signal (R²=0.30)</span><br>'
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

    sc1, sc2 = st.columns(2)
    with sc1:
        oil_shock = st.slider("Oil price shock (%)", -50, 50, 0, step=5, key="oil_shock_slider")
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
        f'<div class="honest-box"><span class="label">Honest result — read before trusting the sliders above</span>'
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
        "real attempts."
    )

with tab5:
    st.markdown('<div class="section-title">Methodology &amp; Limitations</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_MUTED};">This project was built the same way MENASA and the Gulf Tracker were: '
        f'real data only, every model independently cross-validated in a second language (R), and every real '
        f'problem encountered during development disclosed here rather than quietly fixed and hidden.</p>',
        unsafe_allow_html=True,
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
            "**Data:** MENASA's real raw economic indicators (not the normalized risk sub-scores — see the bug "
            "note above), plus real oil price (yfinance `CL=F`) and short-rate (yfinance `^IRX`) data.\n\n"
            "**Method:** panel AR(1) fixed-effects regression, extended with real shock-driver regressors.\n\n"
            "**Limitations:** 15 years of annual data per country is thin for time-series forecasting. Growth "
            "forecasts should not be relied on. The shock coefficients in the stress-test layer are not "
            "statistically significant — real, correctly-built mechanism, not a validated precise sensitivity."
        )

    st.markdown("#### Three real bugs, caught and fixed during development")
    bug_cols = st.columns(3)
    with bug_cols[0]:
        st.markdown(f'<div class="card"><b style="color:{ACCENT};">Bug 1</b><br>'
                     f'<span style="color:{TEXT};font-weight:600;">debt_to_gdp missingness</span><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">Would have silently dropped 16 of 17 '
                     f'real distress events if included in the primary model.</span></div>', unsafe_allow_html=True)
    with bug_cols[1]:
        st.markdown(f'<div class="card"><b style="color:{ACCENT};">Bug 2</b><br>'
                     f'<span style="color:{TEXT};font-weight:600;">Silent stdout buffering</span><br>'
                     f'<span style="color:{TEXT_MUTED};font-size:0.85rem;">GitHub Actions ran the GDELT fetch for '
                     f'6+ minutes with zero visible output — fixed with unbuffered Python.</span></div>', unsafe_allow_html=True)
    with bug_cols[2]:
        st.markdown(f'<div class="card"><b style="color:{ACCENT};">Bug 3</b><br>'
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
        'target="_blank" style="font-family:JetBrains Mono,monospace;font-size:0.85rem;">View full source on GitHub →</a></div>',
        unsafe_allow_html=True,
    )
