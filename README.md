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
- `sovereign_default` (2 events) showed severe near-perfect separation in
  the plain logit fit — fixed with Firth's penalized/bias-corrected logistic
  regression (`model/firth_logit.py`), a from-scratch implementation since
  neither PyPI's `firthlogist` (needs Python <3.11) nor CRAN's `logistf`
  (unreachable from this sandbox — egress policy blocks cloud.r-project.org)
  were available to use directly. Inference uses the standard Wald
  approximation, not Firth's preferred profile-likelihood test, which isn't
  implemented — disclosed, not hidden.
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

## Risk architecture layer — done

A descriptive diagnostic layer added after auditing the project against a
comprehensive institutional risk-architecture framework (external
vulnerability, fiscal/sovereign, banking-sector, macro, institutional,
buffers, global financial conditions, chokepoint exposure). It does **not**
introduce a second predictive score — Phase 1's fitted logit remains the
only real predictive model here — it explains *where* a country's risk
comes from, using real, newly-fetched data:

- **Extended World Bank WDI indicators** (`data/fetch_extended_indicators.py`):
  external debt/GNI, external debt service/exports, fiscal balance/GDP,
  interest payments/revenue, bank NPLs, private credit/GDP, trade openness,
  fuel/food trade dependence, remittances, FDI, unemployment — same keyless
  public API already used for the original 11 factors.
- **Real global financial conditions** (`forecast-module/fetch_global_conditions.py`,
  yfinance): VIX, US 10-year Treasury yield, the US Dollar Index, and an
  EM bond ETF used as an aggregate market-wide risk-premium proxy.
- **Real, sourced maritime-chokepoint exposure** (`data/chokepoint_exposure.py`):
  Suez Canal / Bab el-Mandeb / Strait of Hormuz, assigned by real
  geography and trade dependency, citations copied from the companion
  overeign-risk-index project's own fact-checked research.
- **A real ablation test** (`model/ablation_test.py`): economic-only vs.
  governance-only vs. combined logit on the existing panel — combining
  both real dimensions reaches AUC 0.843, a genuine +0.079 lift over the
  better single-dimension model (governance-only, 0.763).
- **Peer-relative percentiles and real "what changed" attribution**
  (`model/peer_comparison.py`).

**In progress:** a real bilateral trade/spillover network (`data/fetch_trade_network.py`,
`model/trade_network.py`) is built end-to-end against UN Comtrade's real
API — gated on a free `COMTRADE_API_KEY` repo secret not yet registered.
Shows "not yet available" in the app, never a fabricated placeholder.

**Deliberately not added, with the real reason** (see the live app's
Methodology tab for the full list): per-country sovereign CDS/EMBI/bond
yields (confirmed absent from every free API this project has access to),
climate/resource vulnerability indices (no reliable free fetchable
pipeline), and a continuous conflict-intensity panel (ACLED requires a
separate account registration). None of these are approximated with
invented data.

**A real bug caught by validating the sub-indices, since fixed:** the 5
governance-named factors' assumed risk direction was backwards in the new
sub-index code — they're named like quality scores but this dataset's
actual values run the opposite way (confirmed against raw data and against
Phase 1's own already-validated model). `institutional_risk`'s AUC against
real distress history was 0.24 (inverted) before the fix, 0.76 (correctly
directed) after. Phase 1's actual predictive model was never affected — it
never assumed a direction to begin with. See `model/validate_sub_indices.py`.

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
**A real limitation found in a later audit, since fixed**: the 5 economic
factors this model is fit on were originally the same 0–100 normalized
risk sub-scores whose mislabeling was already caught for Phase 3 — missed
here at first. Fixed by refitting on Phase 3's real raw values for those 5
factors (governance/WGI factors were already correctly on their real 0–100
percentile scale, and are unchanged) — re-validated in R after the fix; see
`data/build_panel.py` for the exact swap and the missingness check run
before it.

**4. Econometric methodology.** Panel logistic regression with
country-clustered standard errors (Phase 1); panel fixed-effects AR(1)
regression (Phase 3 forecasting); local projections at h=0,1,2 for a real
oil-price shock on growth/inflation (Phase 3, Jordà-style, panel FE at each
horizon); an event-study correlation, n=5, explicitly not treated as a
statistical test (Phase 2). All independently cross-validated in R.

**5. Empirical results.** With the corrected raw data, `reserves_months_imports`
is now the dominant significant economic predictor (p<0.001) — a real,
economically sensible result (thin import cover is a classic
balance-of-payments warning sign) that the earlier, mislabeled data
obscured. `political_stability` remains significant; `gdp_growth`, which
appeared significant under the old mislabeled data, no longer is — a real,
disclosed change in the result, not smoothed over. The oil-shock local
projection shows a separate, real pattern: a significant positive effect on
GDP growth on impact (h=0, many of these economies are oil
producers/exporters) that reverses to significant and negative by h=2 —
inflation shows no significant effect at any horizon, consistent with the
stress-test model's own finding.

**6. Backtesting.** In-sample AUC 0.84 (12 events, 10 predictors — a real
overfitting risk, disclosed). A genuine out-of-sample temporal holdout
(train ≤2021, 4 events; test 2022–2024, 8 events) gives AUC 0.69. The
holdout's own real instability shows directly: Lebanon 2023 is predicted at
essentially 100% probability, driven by genuinely extreme real values that
year (221% inflation, an 820% currency depreciation) — not an error, but a
real illustration of how few training events this model has to work with.
Pakistan's actual 2023/2024 entries rank 5th and 4th highest, not 1st and
2nd. **Read as historically associated with distress, not as a working
early-warning system.**

**7. Model benchmarking.** A real, current-snapshot cross-sectional check
against S&P sovereign ratings (`data/credit_ratings.py`, copied from
MENASA's own sourced dataset). The raw-data fix produced a real,
substantive improvement here: rank correlation rose from ρ≈0.55 to ρ≈0.77
(n=19). Ethiopia — in real selective default — ranks 2nd-highest by the
model. Lebanon — also in real selective default, and the case the pre-fix
model missed entirely (ranked 18th of 19) — now ranks 4th. That reversal is
real evidence the fix mattered, not just a units correction.

**8. Scenario analysis.** Named presets (Baseline/Escalation/
De-escalation/Severe tail-risk) apply real, fitted oil/rate coefficients
through documented, illustrative shock magnitudes. Explicitly labeled
"probability not estimated" — 17 real events is too thin to defensibly
assign a probability to each scenario, and this project does not fabricate
one.

**9. Limitations.** Rare-event data (17 real events total); near-perfect
separation risk in the 2-event `sovereign_default` outcome (worse now on
the corrected raw scale — coefficients there are large and unstable,
already flagged in the model's own output as exploratory only); a
cross-sectional-only ratings benchmark, not a historical time series; no
bilateral trade/spillover-network data fetched, so cross-country contagion
channels are not modeled here; no formal probability calibration beyond
the logit's own fitted probabilities; the out-of-sample holdout is
dominated by a single extreme observation (Lebanon 2023) given only 4
training events, a real illustration of how thin this panel's event count
still is.

**10. What was deliberately not attempted, and why.** A literal
macro-vs-geopolitical "ablation" test at panel scale is still not possible
— the only real geopolitical shock data is 5 discrete event-study
observations, not an annual series across all 34 countries, so a combined
panel regression would mismatch sample structures rather than genuinely
compare information content. The real, available analogue — economic vs.
governance factors, both continuous panel dimensions — was since built and
run (see "Risk architecture layer," above): combining them reaches AUC
0.843, a genuine +0.079 lift over the better single-dimension model.
Spillover/network analysis — would require real bilateral trade matrices
(UN Comtrade has a real API, but gated on a free subscription key not yet
registered for this project); climate/resource vulnerability indices and a
continuous ACLED conflict panel were investigated for the same layer and
declined for the same reason: no reliable free pipeline or credentials
available, not approximated with invented data. All three remain flagged
as future work, not silently dropped.
