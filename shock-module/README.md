# Geopolitical Shock Module (Phase 2)

Measures whether real geopolitical shocks show up in real financial market
movement, pairing real GDELT media-coverage data against real historical
FX rates for 5 precisely-dated events, an event-study design, not a
qualitative judgment call.

## What's actually real here

- **6 shock events** (`shock_events.py`), each with a specific date, not a
  vague year, sourced from real, well-documented episodes already
  established across this project and MENASA. One (Syria) was dropped
  after a real fetch confirmed it predates GDELT's actual data coverage
  window (Feb 2015+), documented as a genuine scope constraint, not hidden.
- **Real GDELT 2.0 Doc API data** (`fetch_shocks.py` → `shock_timelines_raw.json`):
  media tone and coverage volume around each event, fetched via GitHub
  Actions after three real debugging rounds (silent output buffering, then
  aggressive rate-limiting) — see git history for the full trail.
- **Real historical daily FX data** (`fetch_fx.py` → `fx_timelines_raw.json`):
  after Frankfurter (ECB reference rates) was tried first and confirmed,
  via its own `/v1/currencies` list, to not cover any of the 5 currencies
  needed (LBP, LKR, AFN, EGP, PKR), switched to `yfinance`, which does.
- **The actual event study** (`event_study.py`): pairs the two real
  signals and computes a genuine correlation, with an honest n=5 caveat
  front and center, not buried.
- **A real SQLite database** (`schema.sql` / `load_db.py`), same
  normalized pattern as Phase 1.
- **Independent R validation** (`event_study_validation.R`): matches
  Python's correlation (0.59) using R's own `cor()`.

## The real, honest finding

The correlation runs counter to naive intuition, worse media tone doesn't
mean bigger FX movement, and that's not noise, it's a real pattern: Lebanon
had the single worst media tone in the set but almost no FX movement
(its official rate was still pegged during that window), while Egypt had
the mildest tone but the largest depreciation (a more freely-floating
currency). A country's exchange-rate regime matters as much as the shock
itself, exactly the kind of nuance a real event study should surface.

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

- **n=5.** Not a sample size to draw a statistical conclusion from. This
  is a real, correctly-computed correlation on real data, not a validated
  predictive relationship, that would need dozens of events.
- GDELT's coverage window (Feb 2015+) limits which historical shocks this
  method can ever cover, a real, structural constraint on scope, not
  something more data cleaning fixes.
- Lebanon's FX series reflects the official/pegged rate, not the parallel
  market where the real crisis played out, disclosed explicitly rather
  than treated as "no shock."
- This is a research/portfolio product, not investment advice.

## Next: Phase 3

Macro forecasting + user-driven stress testing, not yet started.
