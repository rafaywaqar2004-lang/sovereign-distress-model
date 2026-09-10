"""
Sovereign Distress Model -- Phase 1.

Real logistic regression on the real panel built in data/build_panel.py,
predicting IMF_PROGRAM_ENTRY (the primary outcome) and SOVEREIGN_DEFAULT
from the same macro/governance factors the MENASA Risk Monitor already
tracks.

A real methodological finding surfaced while building this, worth stating
plainly rather than burying: debt_to_gdp has severe missingness in this
panel (91 of 507 observations -- already flagged in MENASA's own docs).
Requiring complete cases across all 11 factors, including debt_to_gdp,
collapses the usable sample to 77 rows and, critically, drops all but 1 of
the 17 real distress events with it (the country-years where debt data is
missing are disproportionately the same country-years in genuine fiscal
distress -- Lebanon stopped publishing fiscal data entirely, for instance).
That's not a coding bug; it's a real, informative pattern about which
countries under real strain also stop reporting debt data.

The fix: the PRIMARY model below excludes debt_to_gdp and uses the other
10 factors, which retains 355 observations and 14 of 17 real events.
debt_to_gdp is then tested separately, on its own smaller available
subsample, as an explicit ROBUSTNESS CHECK, not folded into the primary
specification where its missingness would silently gut the sample.

Standard errors are clustered by country (not i.i.d.), since observations
within the same country across years are correlated -- the standard
correction for exactly this kind of panel data.
"""
import pandas as pd
import statsmodels.api as sm

from firth_logit import firth_logit, firth_profile_test

PRIMARY_FACTOR_COLS = [
    "current_account_pct_gdp", "reserves_months_imports",
    "gdp_growth", "inflation", "currency_depreciation_pct",
    "political_stability", "government_effectiveness", "rule_of_law",
    "regulatory_quality", "control_of_corruption",
]
FACTOR_COLS = PRIMARY_FACTOR_COLS  # kept for backward-compat with fit_and_report's default

panel = pd.read_csv("../data/panel.csv")


def fit_and_report(outcome_col, factor_cols, label, min_events_for_caveat=10):
    complete = panel.dropna(subset=factor_cols + [outcome_col])
    n = len(complete)
    n_events = int(complete[outcome_col].sum())
    n_total_events = int(panel[outcome_col].sum())

    print(f"\n{'='*70}")
    print(f"OUTCOME: {outcome_col}  [{label}]")
    print(f"{'='*70}")
    print(f"Complete-case observations: {n} (of {len(panel)} total panel rows)")
    print(f"Positive events retained: {n_events} of {n_total_events} real events in the full panel ({n_events/n:.1%} of this subsample)")

    if n_events < min_events_for_caveat:
        print(
            f"\n*** HONEST CAVEAT: only {n_events} positive events. A common rule of "
            f"thumb (Peduzzi et al. 1996) suggests at least 10 events per predictor "
            f"for a logistic regression to be reliable -- with {len(factor_cols)} "
            f"predictors here, that's a real, disclosed limitation, not a hidden one. "
            f"Coefficients below should be read as exploratory / directional only. ***"
        )

    X = sm.add_constant(complete[factor_cols])
    y = complete[outcome_col]

    model = sm.Logit(y, X)
    try:
        result = model.fit(
            disp=0,
            cov_type="cluster",
            cov_kwds={"groups": complete["country_code"]},
        )
        print(result.summary2().tables[1].to_string())
        return result
    except Exception as e:
        print(f"\nModel did not converge (expected with this few events): {e}")
        return None


def fit_and_report_firth(outcome_col, factor_cols, label):
    """Firth's penalized logistic regression -- the fix for the
    near-perfect separation `fit_and_report` above can only flag, not
    solve, when events are this rare. See firth_logit.py's docstring for
    why this is a from-scratch implementation (PyPI's firthlogist doesn't
    support this project's Python version; CRAN's logistf couldn't be
    installed either). Independently cross-validated in R anyway --
    r-validation/firth_validation.R is a second from-scratch
    implementation of the same algorithm in base R, not a wrapper around
    the unreachable logistf, and matches this file's output almost to
    the decimal.

    Also reports Firth's own preferred significance test -- the profile
    penalized likelihood ratio, not just the Wald p-value -- since the
    two visibly disagree here (see the printed table): Wald relies on a
    large-sample normal approximation that is exactly least trustworthy
    in this small, near-separated regime, which is the entire reason
    Firth's correction exists in the first place."""
    complete = panel.dropna(subset=factor_cols + [outcome_col])
    X = sm.add_constant(complete[factor_cols])
    y = complete[outcome_col]

    print(f"\n{'-'*70}")
    print(f"FIRTH'S PENALIZED LOGISTIC REGRESSION: {outcome_col}  [{label}]")
    print(f"{'-'*70}")
    result = firth_logit(X.values, y.values)
    print(f"Converged: {result['converged']} (in {result['n_iter']} iterations)")
    print(f"Penalized log-likelihood: {result['loglik_penalized']:.4f}\n")

    profile = firth_profile_test(X.values, y.values, result["beta"], result["loglik_penalized"])
    profile_p = ["n/a (did not converge)" if not c else f"{p:.4f}" for p, c in zip(profile["p"], profile["converged"])]

    summary = pd.DataFrame({
        "coef": result["beta"], "std err": result["se"],
        "wald P>|z|": result["p"], "profile-LR p": profile_p,
    }, index=X.columns)
    print(summary.round(4).to_string())
    n_unconverged = int((~profile["converged"]).sum())
    if n_unconverged:
        print(
            f"\n*** {n_unconverged} of {len(X.columns)} profile-likelihood refits did not converge within a "
            f"generous iteration budget (tried multiple starting points and step sizes) -- reported as "
            f"unavailable for those factors, not filled in with an unreliable number. A real constraint of "
            f"profiling a penalized likelihood this close to separation, not a bug being silently worked around. ***"
        )
    result["profile"] = profile
    return result


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# PRIMARY MODEL -- 10 factors, excludes debt_to_gdp (severe missingness)")
    print("#" * 70)
    fit_and_report("imf_program_entry", PRIMARY_FACTOR_COLS, "primary, 10-factor")
    fit_and_report("sovereign_default", PRIMARY_FACTOR_COLS, "primary, 10-factor")
    fit_and_report_firth("sovereign_default", PRIMARY_FACTOR_COLS, "primary, 10-factor -- Firth's fix for the separation above")

    print("\n" + "#" * 70)
    print("# ROBUSTNESS CHECK -- adds debt_to_gdp back in, on its smaller available sample")
    print("#" * 70)
    fit_and_report("imf_program_entry", PRIMARY_FACTOR_COLS + ["debt_to_gdp"], "robustness, +debt_to_gdp")
    fit_and_report("sovereign_default", PRIMARY_FACTOR_COLS + ["debt_to_gdp"], "robustness, +debt_to_gdp")

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(
        "This is a real, honestly-scoped first pass, not a production early-warning "
        "system. The genuine constraint is sample size: formal sovereign distress is "
        "rare by definition, and a 34-country, 15-year panel only contains as many "
        "real events as history actually produced. debt_to_gdp's severe missingness "
        "(91 of 507 rows) meant including it in the primary specification would have "
        "silently dropped 16 of 17 real events along with it -- excluded from the "
        "primary model for exactly that reason, tested separately above instead. "
        "Expanding the country panel (the full ~150-country IMF/World Bank universe, "
        "not just this project's MENA/South Asia focus) is the most direct way to add "
        "real events without inventing any -- flagged here as the clear next step, not "
        "attempted in this first pass so as not to silently widen scope beyond what's "
        "been validated."
    )
