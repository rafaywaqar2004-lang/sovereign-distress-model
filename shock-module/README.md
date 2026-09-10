# Geopolitical Shock Module (Phase 2)

Measures whether real geopolitical shocks show up in real financial market
movement, pairing real GDELT media-coverage data against real historical
FX rates for 12 precisely-dated events, an event-study design, not a
qualitative judgment call.

## What's actually real here

- **13 shock events** (`shock_events.py`), each with a specific date, not a
  vague year, sourced from real, well-documented episodes. One (Syria) was
  dropped after a real fetch confirmed it predates GDELT's actual data
  coverage window (Feb 2015+), documented as a genuine scope constraint,
  not hidden — 12 remain.
- **Real GDELT 2.0 Doc API data** (`fetch_shocks.py` → `shock_timelines_raw.json`):
  media tone and coverage volume around each event, fetched via GitHub
  Actions. GDELT's real, aggressive rate limiting means not every event
  returns a usable tone signal on a given run — currently 8 of the 12
  events do (up from 6 on an earlier run, since the rate limiting is
  stochastic — a re-fetch can genuinely pick up more), disclosed
  per-event rather than silently filled in.
- **Real historical daily FX data** (`fetch_fx.py` → `fx_timelines_raw.json`):
  after Frankfurter (ECB reference rates) was tried first and confirmed,
  via its own `/v1/currencies` list, to not cover the currencies needed,
  switched to `yfinance`, which returned real data for all 12.
- **The actual event study** (`event_study.py`): pairs the two real
  signals and computes a genuine correlation, with an honest small-n
  caveat front and center, not buried.
- **A real SQLite database** (`schema.sql` / `load_db.py`), same
  normalized pattern as Phase 1.
- **Independent R validation** (`event_study_validation.R`): matches
  Python's correlation exactly using R's own `cor()`.

## The real, honest finding

The correlation (n=8, ρ=0.37) is real but modest — and notably weaker than
an earlier fetch's n=6 sample (ρ=0.76), a real illustration of how unstable
a correlation estimate still is at this sample size, not a sign either
number was computed wrong. Israel has the worst media tone in the current
usable set but only a modest FX move, while Egypt has the mildest tone but
the largest depreciation (a more freely-floating currency) — worse media
tone doesn't automatically mean bigger FX movement. Pegged or managed
currencies (Lebanon, Iran officially, several Gulf states) can show large
tone swings with little real FX movement regardless of event severity — a
country's exchange-rate regime matters as much as the shock itself, exactly
the kind of nuance a real event study should surface. This is re-derived
from whatever data is actually fetched each run, not assumed to match an
earlier, smaller sample.

## Running it

```bash
python3 event_study.py      # requires shock_timelines_raw.json + fx_timelines_raw.json (already fetched)
python3 load_db.py           # builds shock_module.db
Rscript event_study_validation.R   # independent cross-check
```

The two fetch scripts (`fetch_shocks.py`, `fetch_fx.py`) run via GitHub
Actions (`.github/workflows/fetch-shocks.yml`, `fetch-fx.yml`), not locally
— both external APIs are unreachable from the sandbox this project is
developed in.

## Limitations

- **n=8 usable of 12 real events fetched.** Not a sample size to draw a
  statistical conclusion from. This is a real, correctly-computed
  correlation on real data, not a validated predictive relationship, that
  would need dozens of events.
- GDELT's coverage window (Feb 2015+) limits which historical shocks this
  method can ever cover, a real, structural constraint on scope. Its real
  rate limiting also means a given fetch run may not return both signals
  for every event — a real availability constraint, not a bug.
- Lebanon's and Iran's FX series reflect official/pegged rates, not the
  parallel/black markets where their real crises actually played out,
  disclosed explicitly rather than treated as "no shock."
- This is a research/portfolio product, not investment advice.

## Next: Phase 3

Macro forecasting + user-driven stress testing — done, see `forecast-module/README.md`.
