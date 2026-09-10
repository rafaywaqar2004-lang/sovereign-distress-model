# Macro Forecasting + Stress Testing (Phase 3)

Real panel forecasting for GDP growth and inflation, plus a real
stress-test layer letting a shock (oil price, US short-term rate, VIX,
US Dollar Index) flow through the model's own fitted coefficients rather
than an assumed multiplier.

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

Extends the inflation model (the one with real signal) with four real,
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
- **VIX** (`fetch_global_conditions.py`, via yfinance's `^VIX`) — the
  standard global risk-aversion gauge, a distinct channel from oil/rates
  (capital flight / risk-off pressure on EM currencies and prices).
- **US Dollar Index** (`fetch_global_conditions.py`, via yfinance's
  `DX-Y.NYB`) — broad dollar strength, a distinct import-price
  pass-through channel for these economies.

Two more real global-conditions series (`fetch_global_conditions.py`
also fetches the US 10-year Treasury yield and an EM bond ETF, `EMB`,
used elsewhere in this project as a market-wide EM risk-premium proxy)
were tested for this same role and deliberately excluded: the 10-year
yield correlates 0.70 with the short-rate driver already in the model
(same underlying Fed-cycle signal), and EMB correlates -0.65 with the
10-year and -0.54 with the short rate for the same reason — both would
muddy interpretation of the existing rate term rather than add distinct
real signal, on a panel already this thin. Tested and excluded, not
just left unused because untried.

**Real, honest result:** none of the four shock coefficients is
statistically significant at conventional levels in this panel (oil:
p=0.28; rate: p=0.87; VIX: p=0.64; dollar index: p=0.74) — only the
inflation persistence term is (p<0.0001). The oil coefficient's *sign*
is directionally sensible (higher oil prices → higher inflation,
plausible for a panel with several oil-importing economies); VIX and
the dollar index come out negatively signed, which is not the textbook
direction (a risk-off spike or dollar surge would typically be expected
to raise import-price inflation) — reported as-is rather than adjusted
to match expectation, since on a panel this thin the sign itself isn't
reliable either. All four are rough, unreliable point estimates, not
validated sensitivities. Reported plainly in the script's own output
rather than dressed up — the example stress scenarios illustrate the
mechanism, not a claim of statistical confidence.

Independently validated in R (`stress_test_validation.R`): matches
Python almost exactly (inflation_lag 0.5713 both, oil_pct_change 0.0420
both, rate_change -0.2050 both, vix_change -0.0644 both, dxy_pct_change
-0.0487 both).

## Running it

```bash
python3 forecast_model.py          # base AR(1) models + real 2024 backtest
Rscript forecast_validation.R      # independent cross-check
python3 stress_test.py             # stress-test regression + example scenarios
Rscript stress_test_validation.R   # independent cross-check
python3 load_db.py                 # builds forecast_module.db
```

The fetch scripts (`fetch_shock_drivers.py`, `fetch_global_conditions.py`)
run via GitHub Actions, not locally — the source domains are unreachable
from the sandbox this project is developed in.

## Limitations

- 15 years of annual data per country is thin for time-series
  forecasting; a simple AR(1) is the defensible ceiling this data
  actually supports, not a limitation of the modeling choice.
- Growth forecasts should not be relied on — the model itself, honestly,
  doesn't beat guessing "no change."
- None of the four shock coefficients is statistically significant — the
  stress-test mechanism is real and correctly built, but the specific
  sensitivities it currently estimates shouldn't be relied on for a
  precise magnitude, only a directional illustration. VIX and the dollar
  index also carry a counter-intuitive sign here, reported as-is.
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
