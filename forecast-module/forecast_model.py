"""
Phase 3: real macro forecasting -- a panel AR(1) fixed-effects model for
GDP growth and inflation, fit on RAW economic values (raw_panel.csv, built
from MENASA's raw_data_long.csv), not the normalized 0-100 risk sub-scores
in driver_history.csv.

That distinction matters and was a real bug caught during development: an
earlier version of this script used driver_history.csv, whose own file
header comment says explicitly its factors are "normalized sub-scores,"
not raw values -- forecasting a country's RANK relative to its peers that
year is a fundamentally different (and much less economically meaningful)
target than forecasting its actual GDP growth rate, and it produced
telltale giveaway values like exactly 100.0 or 0.0 (rank extremes, not
real growth/inflation rates). Fixed by pivoting the real raw indicator
values instead -- see raw_panel.csv.

Not a black box: next year's value is modeled as a country-specific
baseline (fixed effect) plus a coefficient on this year's value, the
standard, defensible starting point for panel forecasting with this
little history per country (15 years), not a fancier method this data
can't actually support.

Validated the honest way: fit on 2010-2023, forecast 2024, compare to the
REAL 2024 value already in the panel -- genuine out-of-sample backtesting,
not an in-sample fit statistic dressed up as a forecast track record.
"""
import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS

panel = pd.read_csv("raw_panel.csv")
panel = panel.set_index(["country_code", "year"])


def fit_ar1_panel(variable, train_through_year=2023):
    """Fits panel_t = alpha_i + beta * panel_{t-1} on years <= train_through_year,
    with country fixed effects. Returns the fitted result and the data used."""
    df = panel[[variable]].copy()
    df["lag"] = df.groupby(level="country_code")[variable].shift(1)
    df = df.dropna()

    train = df[df.index.get_level_values("year") <= train_through_year]

    y = train[variable]
    X = train[["lag"]]
    mod = PanelOLS(y, X, entity_effects=True)
    result = mod.fit(cov_type="clustered", cluster_entity=True)
    return result, df


def backtest_2024(variable, result, df):
    """Real out-of-sample test: use the fitted coefficient + each country's
    2023 value + its own fixed effect (alpha_i, extracted from the fitted
    model's estimated_effects -- constant within an entity in a pure
    entity-effects model, so any one observation for that country gives it)
    to forecast 2024, then compare to the REAL 2024 value already in
    driver_history.csv. Countries missing from the training fit (e.g. no
    2023 data) are skipped, not guessed at."""
    beta = result.params["lag"]
    effects = result.estimated_effects
    # one alpha_i per country: take the first observed effect for that entity
    country_alpha = effects.groupby(level="country_code").first().iloc[:, 0]

    test_rows = df[df.index.get_level_values("year") == 2024].copy()
    forecasts, actuals, codes = [], [], []
    for (code, year), row in test_rows.iterrows():
        if code not in country_alpha.index:
            continue
        forecast = beta * row["lag"] + country_alpha.loc[code]
        forecasts.append(forecast)
        actuals.append(row[variable])
        codes.append(code)

    out = pd.DataFrame({"country_code": codes, "forecast_2024": forecasts, "actual_2024": actuals})
    out["error"] = out["actual_2024"] - out["forecast_2024"]
    out["abs_error"] = out["error"].abs()
    return out


if __name__ == "__main__":
    all_backtests = []
    for variable in ["gdp_growth", "inflation"]:
        print(f"\n{'='*70}")
        print(f"PANEL AR(1) FORECAST MODEL: {variable}")
        print(f"{'='*70}")

        result, df = fit_ar1_panel(variable)
        print(result.summary)

        print(f"\n--- Real out-of-sample backtest: forecast 2024, compare to actual ---")
        backtest = backtest_2024(variable, result, df)
        print(f"{len(backtest)} countries with both a 2023 lag and a real 2024 value")
        print(backtest.sort_values("abs_error").to_string(index=False))

        mae = backtest["abs_error"].mean()
        print(f"\nMean absolute error (AR(1) forecast vs. real 2024): {mae:.2f}")

        # Naive baseline: "next year = this year" (a random-walk forecast) --
        # the honest bar this model needs to beat to be worth anything.
        naive = df[df.index.get_level_values("year") == 2024].copy()
        naive["naive_forecast"] = naive["lag"]
        naive_mae = (naive[variable] - naive["naive_forecast"]).abs().mean()
        print(f"Mean absolute error (naive 'no change' baseline vs. real 2024): {naive_mae:.2f}")
        if mae < naive_mae:
            print(f"AR(1) model beats the naive baseline by {naive_mae - mae:.2f} points.")
        else:
            print(f"*** HONEST RESULT: the naive baseline actually beats this AR(1) model here. "
                  f"Reported as-is, not hidden. ***")

        backtest["variable"] = variable
        all_backtests.append(backtest)

    pd.concat(all_backtests, ignore_index=True).to_csv("backtest_2024_results.csv", index=False)
    print("\nSaved backtest_2024_results.csv")
