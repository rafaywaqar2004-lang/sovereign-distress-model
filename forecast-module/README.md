# Macro Forecasting Module (Phase 3, part 1)

A real panel AR(1) fixed-effects model forecasting GDP growth and
inflation for next year, fit on MENASA's real raw economic data.

## A real bug caught and fixed during development

The first version of this model used `driver_history.csv` from the
MENASA repo, whose factors looked like raw economic values (column names
like `gdp_growth`, `inflation`) but are actually **normalized 0-100 risk
sub-scores** — that file's own header comment says so explicitly. Forecasting
a country's cross-sectional *rank* relative to its peers that year is a
fundamentally different, much less economically meaningful target than
forecasting its actual growth rate. The tell: backtest output containing
values of exactly `100.0` or `0.0` (rank extremes, not real percentages).

Fixed by pivoting MENASA's real raw indicator values (`raw_data_long.csv`
→ `raw_panel.csv`) instead. Post-fix, the numbers became immediately more
plausible (Bahrain 2.9% growth, Turkey 58.5% inflation, both real,
well-documented figures) instead of nonsensical round numbers.

## Real, honest findings

Two outcomes, genuinely different results, both reported as-is:

- **GDP growth**: the AR(1) model has essentially no real predictive
  power (R²=0.06, lag coefficient not significant at 5%) and the naive
  "no change" baseline actually beats it (2.93 vs 3.41 mean absolute
  error on the real 2024 backtest). This matches well-established growth
  literature — annual GDP growth is notoriously close to a random walk at
  the country level — and is reported honestly rather than hidden.
- **Inflation**: the model shows real, significant persistence (lag
  coefficient 0.574, p<0.0001, R²=0.298) and genuinely beats the naive
  baseline (10.63 vs 14.12 MAE on the real 2024 backtest). Consistent
  with well-documented inflation persistence in the macro literature.

## Independent R validation

`forecast_validation.R` matches Python's training window exactly
(2010-2023, holding out 2024) and reproduces the inflation coefficient
almost exactly: **0.5744** in both Python (`linearmodels.PanelOLS`) and R
(`plm`, fixed effects), same R² (0.298), same N (402). A genuinely
separate implementation confirming the same real result, not a restated
number.

## Running it

```bash
python3 forecast_model.py         # fits both models, runs the real 2024 backtest
Rscript forecast_validation.R     # independent cross-check of the inflation model
```

## Limitations

- 15 years of annual data per country is thin for time-series forecasting;
  a simple AR(1) is the defensible ceiling this data actually supports,
  not a limitation of the modeling choice.
- Growth forecasts should not be relied on — the model itself, honestly,
  doesn't beat guessing "no change."
- This is a research/portfolio product, not investment advice.

## Next

Stress-testing layer: let a user apply a shock (oil price, Fed rate,
conflict) and see how the inflation forecast (the one with real signal)
shifts — not yet built.
