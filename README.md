# Sovereign Distress Model

**Phase 1 of the EM Macro & Geopolitical Risk Engine** — a panel-data
probability model of sovereign fiscal/balance-of-payments distress across
the same 34 MENA and South Asia economies the
[MENASA Risk Monitor](https://menasa-risk-monitor.onrender.com) already
tracks. Companion project, not a replacement: MENASA scores overall risk
level; this predicts a specific, falsifiable event.

## What this actually predicts

Two outcomes, kept separate because they're different severities:

- **`sovereign_default`** — an actual default or restructuring of external
  sovereign debt. Only 2 such events occur in this 34-country, 2010-2024
  panel (Lebanon 2020, Sri Lanka 2022) — genuinely rare by definition, and
  this model says so rather than pretending otherwise.
- **`imf_program_entry`** — the year a country's IMF Executive Board
  formally approved a new lending arrangement (EFF/ECF/SBA), a standard
  proxy for fiscal distress in the sovereign-risk literature. 15 such
  events in the panel, thin but workable.

Both outcomes are built entirely from real, dated, sourced events — see
`data/distress_events.py` for the full citation of each one and an explicit
account of what was deliberately excluded and why (precautionary facilities,
staff-level-only agreements never approved by the IMF Board, etc.).

## Data sources — official, real, already validated

The 11 macro/governance features are the **same official World Bank WDI and
Worldwide Governance Indicators series** already fetched, sourced, and
backtested by the MENASA Risk Monitor (`driver_history.csv`, copied
directly from that project rather than re-fetched, to avoid drifting from
an already-validated source). See that project's `fetch_data.py` for the
exact indicator codes (e.g. `GC.DOD.TOTL.GD.ZS` for debt-to-GDP,
`GOV_WGI_RL.EST` for Rule of Law).

## A real methodological finding, not hidden

`debt_to_gdp` is non-missing in only 91 of 507 panel rows (severe sparsity,
already flagged in MENASA's own docs). Requiring complete cases across all
11 factors collapses the usable sample
to 77 rows and drops all but 1 of the 17 real distress events with it — the
country-years missing debt data are disproportionately the same
country-years under genuine fiscal strain (Lebanon stopped publishing
fiscal data entirely during its crisis). That's a real, informative pattern,
not a coding bug.

**Fix:** the primary model excludes `debt_to_gdp` (355 observations, 14 of
17 events retained) and tests it separately as a robustness check on its
own smaller available subsample. See `model/distress_model.py` for both.

## Architecture

```
data/
  distress_events.py   -- the real, sourced outcome events
  build_panel.py        -- merges MENASA's features with the distress events
  driver_history.csv    -- copied from overeign-risk-index (same source)
  panel.csv              -- the built analysis panel (generated)
sql/
  schema.sql             -- normalized relational schema (SQLite)
  load_db.py             -- loads panel.csv into sovereign_distress.db
  sovereign_distress.db  -- the real database (generated)
model/
  distress_model.py      -- logistic regression, primary + robustness spec
r-validation/
  validation.R           -- independent reproduction of the primary model in R
```

## Running it

```bash
cd data && python3 build_panel.py
cd ../sql && python3 load_db.py
cd ../model && python3 distress_model.py
```

## Limitations (stated plainly, same discipline as MENASA)

- Sample size is the real constraint: this is a screening-level, exploratory
  first pass, not a production early-warning system. Formal sovereign
  distress is rare, and a 34-country panel only contains as many real
  events as history produced.
- `sovereign_default` (2 events) shows signs of near-perfect separation in
  the logit fit — flagged explicitly in the model's own output. A proper
  fix (Firth's penalized/bias-corrected logistic regression, the standard
  tool for rare-event logit) is the clear next step, not yet implemented.
- Expanding the country panel beyond MENA/South Asia to the full ~150-country
  IMF/World Bank universe is the most direct way to add real events without
  inventing any — flagged as future work, not attempted here so as not to
  silently widen scope beyond what this phase actually validated.
- This is a research/portfolio product, not investment advice or an
  official IMF/World Bank assessment.

## Next phases (not yet started)

- **Phase 2**: geopolitical shock module (GDELT/ACLED event data → FX/bond/
  FDI/commodity impact)
- **Phase 3**: macro forecasting + user-driven stress testing
