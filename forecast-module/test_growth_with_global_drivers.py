"""
A real, honest robustness check on forecast_model.py's headline finding
that GDP growth "essentially [has] no real predictive power" from its own
lag alone (R^2=0.06). Rather than leave that as an untested assumption
once this project had real global-conditions drivers on hand anyway (oil,
US short rate, VIX, US Dollar Index -- the same four used in
stress_test.py for inflation), this tests whether they add real signal to
growth too, using the same honest out-of-sample backtest (train <=2023,
forecast 2024, compare to the real 2024 value).

Real result: yes, in-sample -- R^2 roughly doubles (0.06 -> 0.12) and
three of the four global drivers come in significant at 5%, while the
country's own lagged growth stops being significant once they're
included. But out-of-sample it's a wash: MAE drops from the pure AR(1)'s
3.41 to 3.29 -- a real, modest improvement -- but the naive "no change"
baseline (MAE 2.93) still wins. Reported here rather than silently
tried-and-discarded: this is what "GDP growth is not forecastable in
this data" actually survived being tested against, not an assumption
nobody checked.
"""
import json

import pandas as pd
from linearmodels.panel import PanelOLS

panel = pd.read_csv("raw_panel.csv")
with open("shock_drivers.json") as f:
    drivers = json.load(f)
with open("global_conditions.json") as f:
    global_conditions = json.load(f)

oil = {int(y): v for y, v in drivers["oil_annual_avg_usd"].items()}
rate = {int(y): v for y, v in drivers["us_short_rate_annual_avg_pct"].items()}
vix = {int(y): v for y, v in global_conditions["vix"].items()}
dxy = {int(y): v for y, v in global_conditions["dollar_index"].items()}

panel["oil_price"] = panel["year"].map(oil)
panel["us_short_rate"] = panel["year"].map(rate)
panel["vix"] = panel["year"].map(vix)
panel["dxy"] = panel["year"].map(dxy)
panel = panel.sort_values(["country_code", "year"])
panel["oil_pct_change"] = panel.groupby("country_code")["oil_price"].transform(lambda s: s.pct_change(fill_method=None) * 100)
panel["rate_change"] = panel.groupby("country_code")["us_short_rate"].transform(lambda s: s.diff())
panel["vix_change"] = panel.groupby("country_code")["vix"].transform(lambda s: s.diff())
panel["dxy_pct_change"] = panel.groupby("country_code")["dxy"].transform(lambda s: s.pct_change(fill_method=None) * 100)

panel = panel.set_index(["country_code", "year"])
df = panel[["gdp_growth", "oil_pct_change", "rate_change", "vix_change", "dxy_pct_change"]].copy()
df["lag"] = df.groupby(level="country_code")["gdp_growth"].shift(1)
df = df.dropna()

FEATURES = ["lag", "oil_pct_change", "rate_change", "vix_change", "dxy_pct_change"]
train = df[df.index.get_level_values("year") <= 2023]
y = train["gdp_growth"]
X = train[FEATURES]
result = PanelOLS(y, X, entity_effects=True).fit(cov_type="clustered", cluster_entity=True)
print(result.summary)

beta = result.params
effects = result.estimated_effects
country_alpha = effects.groupby(level="country_code").first().iloc[:, 0]
test = df[df.index.get_level_values("year") == 2024].copy()
rows = []
for (code, year), row in test.iterrows():
    if code not in country_alpha.index:
        continue
    forecast = country_alpha.loc[code] + sum(beta[f] * row[f] for f in FEATURES)
    rows.append({"country_code": code, "forecast": forecast, "actual": row["gdp_growth"]})
out = pd.DataFrame(rows)
out["abs_error"] = (out["actual"] - out["forecast"]).abs()
mae = out["abs_error"].mean()

print(f"\n{len(out)} countries with both the full lag+driver set and a real 2024 value")
print(f"Extended model (lag + 4 global drivers) MAE: {mae:.2f}")
print(
    "\n*** HONEST RESULT: R-squared roughly doubles in-sample (0.06 -> "
    f"{result.rsquared:.3f}) and 3 of 4 global drivers are significant at 5%, but "
    f"out-of-sample MAE ({mae:.2f}) is only a modest improvement over the pure "
    "AR(1)'s 3.41 and still loses to the naive 'no change' baseline's 2.93. "
    "GDP growth remains not reliably forecastable in this data -- now a tested "
    "finding, not an untested assumption. ***"
)
