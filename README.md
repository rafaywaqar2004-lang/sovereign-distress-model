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

## Phase 2: geopolitical shock module — done

Real event study pairing GDELT media-coverage data against real historical
FX rates for 5 precisely-dated shocks. Full writeup, including a genuinely
counter-intuitive finding about exchange-rate regimes, in `shock-module/README.md`.

## Phase 3: macro forecasting + stress testing — done

Real panel AR(1) forecasting for GDP growth and inflation (a real bug
caught along the way: an early version accidentally forecasted normalized
risk-rank scores instead of actual economic values), plus a stress-test
layer letting a real oil-price or US-rate shock flow through the model's
own fitted coefficients. Full writeup, including the honest result that
the shock coefficients aren't statistically significant here, in
`forecast-module/README.md`.

## All 3 phases complete

The EM Macro & Geopolitical Risk Engine is now fully built: sovereign
distress prediction, a real geopolitical-shock event study, and macro
forecasting with stress testing — all independently validated in R,
backed by real SQLite databases, and built entirely on real or
directly-fetched data.

## Research summary

This section mirrors the structure of an empirical research paper, so the
project's actual methodology and findings are legible without opening the
live app. Every number below is real and reproducible from this repo's own
code — nothing here is a separate, hand-written claim.

**1. Research question.** Does a panel of real macro/governance factors
contain information about which of 34 MENA/South Asia economies enter real
sovereign distress (default or IMF program entry), and do real geopolitical
and macro shocks propagate through this panel in economically sensible ways?

**2. Data.** World Bank WDI + Worldwide Governance Indicators (2010–2024,
34 countries), real sourced distress events (`data/distress_events.py`),
GDELT 2.0 Doc API + yfinance for the shock module, yfinance (`CL=F`, `^IRX`)
for macro forecasting. Full source table in the live app's Methodology tab.

**3. Risk-index construction.** Not a weighted composite score — a fitted
logistic regression (`model/distress_model.py`), so "weights" are the
model's own estimated coefficients, not arbitrary analyst judgment.
**A real limitation found in a later audit, disclosed rather than fixed
quietly**: the 5 economic factors this model is fit on are the same 0–100
normalized risk sub-scores whose mislabeling was already caught for Phase 3
— never caught here until this pass. Coefficients should be read in
normalized risk-rank units, not literal percentage points; refitting on
Phase 3's real raw values is the clear next step, not yet done.

**4. Econometric methodology.** Panel logistic regression with
country-clustered standard errors (Phase 1); panel fixed-effects AR(1)
regression (Phase 3 forecasting); local projections at h=0,1,2 for a real
oil-price shock on growth/inflation (Phase 3, Jordà-style, panel FE at each
horizon); an event-study correlation, n=5, explicitly not treated as a
statistical test (Phase 2). All independently cross-validated in R.

**5. Empirical results.** political_stability and gdp_growth are the only
factors significant at 5% in the primary distress specification. The
oil-shock local projection shows a real, substantive pattern: a
significant positive effect on GDP growth on impact (h=0, many of these
economies are oil producers/exporters) that reverses to significant and
negative by h=2 — inflation shows no significant effect at any horizon,
consistent with the stress-test model's own finding.

**6. Backtesting.** In-sample AUC 0.85 (12 events, 10 predictors — a real
overfitting risk, disclosed). A genuine out-of-sample temporal holdout
(train ≤2021, 4 events; test 2022–2024, 8 events) gives AUC 0.74, but the
raw predicted probabilities in the holdout never exceed 0.5% and do not
cleanly separate real events from non-events — **read as historically
associated with distress, not as a working early-warning system.**

**7. Model benchmarking.** A real, current-snapshot cross-sectional check
against S&P sovereign ratings (`data/credit_ratings.py`, copied from
MENASA's own sourced dataset) gives a moderate positive rank correlation
(Spearman ρ≈0.55, n=19). Ethiopia — in real selective default — is
independently ranked 2nd-highest by the model, a real point in its favor.
Lebanon — also in real selective default — ranks 18th of 19, a genuine,
disclosed divergence.

**8. Scenario analysis.** Named presets (Baseline/Escalation/
De-escalation/Severe tail-risk) apply real, fitted oil/rate coefficients
through documented, illustrative shock magnitudes. Explicitly labeled
"probability not estimated" — 17 real events is too thin to defensibly
assign a probability to each scenario, and this project does not fabricate
one.

**9. Limitations.** Rare-event data (17 real events total); near-perfect
separation risk in the 2-event `sovereign_default` outcome; normalized-vs-
raw factor mislabeling (§3); a cross-sectional-only ratings benchmark, not
a historical time series; no bilateral trade/spillover-network data
fetched, so cross-country contagion channels are not modeled here; no
formal probability calibration beyond the logit's own fitted probabilities.

**10. What was deliberately not attempted, and why.** Formal
macro-vs-geopolitical "ablation" testing at panel scale — the only real
geopolitical shock data is 5 discrete event-study observations, not an
annual series across all 34 countries, so a combined panel regression
would mismatch sample structures rather than genuinely compare information
content. Spillover/network analysis — would require real bilateral trade
and commodity-exposure matrices this project has not fetched; flagged as
future work rather than approximated with invented weights.
