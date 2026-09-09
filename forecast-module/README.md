# Macro Forecasting + Stress Testing (Phase 3)

Real panel forecasting for GDP growth and inflation, plus a real
stress-test layer letting a shock (oil price, US short-term rate) flow
through the model's own fitted coefficients rather than an assumed
multiplier.

## Part 1: base forecasting model (`forecast_model.py`)

A panel AR(1) fixed-effects model, fit on MENASA's real raw economic data.

**A real bug caught and fixed during development:** the first version used
`driver_history.csv` from the MENASA repo, whose factors looked like raw
economic values (column names like `gdp_growth`, `inflation`) but are
actually **normalized 0-100 risk sub-scores** — that file's own header
comment says so explicitly. Forecasting a country's cross-sectional *rank*
relative to its peers that year is a fundamentally different, much less
economically meaningful target than forecasting its actual growth rate.
The tell: backtest output containing values of exactly `100.0` or `0.0`
(rank extremes, not real percentages). Fixed by pivoting MENASA's real raw
indicator values (`raw_data_long.csv` → `raw_panel.csv`) instead.

**Real, honest findings**, backtested the honest way (trained on
2010-2023, forecast 2024, compared to the real 2024 value already in the
data):

- **GDP growth**: essentially no real predictive power (R²=0.06, lag
  coefficient not significant); the naive "no change" baseline actually
  beats it (2.93 vs 3.41 MAE). Consistent with well-documented growth
  literature — annual growth is close to a random walk at the country
  level — reported honestly, not hidden.
- **Inflation**: real, significant persistence (lag coefficient 0.574,
  p<0.0001, R²=0.298), genuinely beats the naive baseline (10.63 vs 14.12
  MAE). Independently confirmed in R (`forecast_validation.R`), matching
  Python almost exactly.

## Part 2: stress-test layer (`stress_test.py`)

Extends the inflation model (the one with real signal) with two real,
fetched shock drivers:

- **Oil price** (`fetch_shock_drivers.py`, via yfinance's WTI futures
  ticker `CL=F`) — ties directly to the same Gulf-economy oil dependence
  theme as the published "The Last Barrel" piece.
- **US short-term rate** (`^IRX`, 13-week Treasury bill) — a real,
  standard proxy for the Fed funds rate, used after FRED's own
  `fredgraph.csv` "quick export" endpoint was confirmed, across 4 real
  attempts spanning 2 separate workflow runs, to consistently time out —
  a real, structural block on that specific endpoint (built for browser
  use, not automated requests), not a transient fluke. FRED's real API
  would work but needs a free API key; `^IRX` doesn't and was already
  proven reliable in this project twice over.

**Real, honest result:** neither shock coefficient is statistically
significant at conventional levels in this panel (oil: p=0.28; rate:
p=0.90) — only the inflation persistence term is (p<0.0001). The oil
coefficient's *sign* is directionally sensible (higher oil prices →
higher inflation, plausible for a panel with several oil-importing
economies), but it's a rough, unreliable point estimate, not a validated
sensitivity. Reported plainly in the script's own output rather than
dressed up — the example stress scenarios illustrate the mechanism, not
a claim of statistical confidence.

Independently validated in R (`stress_test_validation.R`): matches
Python almost exactly (inflation_lag 0.5706 both, oil_pct_change 0.0493
both, rate_change -0.1531 both).

## Running it

```bash
python3 forecast_model.py          # base AR(1) models + real 2024 backtest
Rscript forecast_validation.R      # independent cross-check
python3 stress_test.py             # stress-test regression + example scenarios
Rscript stress_test_validation.R   # independent cross-check
python3 load_db.py                 # builds forecast_module.db
```

The two fetch scripts (`fetch_shock_drivers.py`) run via GitHub Actions,
not locally — both source domains are unreachable from the sandbox this
project is developed in.

## Limitations

- 15 years of annual data per country is thin for time-series
  forecasting; a simple AR(1) is the defensible ceiling this data
  actually supports, not a limitation of the modeling choice.
- Growth forecasts should not be relied on — the model itself, honestly,
  doesn't beat guessing "no change."
- The shock coefficients are not statistically significant — the
  stress-test mechanism is real and correctly built, but the specific
  sensitivities it currently estimates shouldn't be relied on for a
  precise magnitude, only a directional illustration.
- `^IRX` is a real, standard proxy for the Fed funds rate, not the literal
  FEDFUNDS series — documented explicitly, not silently substituted.
- This is a research/portfolio product, not investment advice.

## This completes the EM Macro & Geopolitical Risk Engine's 3 phases

1. Sovereign distress model (panel logit)
2. Geopolitical shock module (GDELT + real FX event study)
3. Macro forecasting + stress testing (this module)

All three phases are independently R-validated, backed by real SQLite
databases, and built entirely on real, sourced, or directly-fetched data —
no invented numbers anywhere in the pipeline.
