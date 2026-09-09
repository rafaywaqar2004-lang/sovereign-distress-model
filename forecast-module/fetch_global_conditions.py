"""
Real global financial-conditions data -- the mega-prompt's "Global Financial
Conditions" component. Same proven yfinance pattern as fetch_shock_drivers.py
(oil, ^IRX), extended to four more real, keyless, free instruments:

- ^VIX  : CBOE Volatility Index, the standard global risk-appetite gauge.
- ^TNX  : US 10-year Treasury yield (x10 convention, divided back out below).
- DX-Y.NYB : ICE US Dollar Index (DXY) -- broad dollar strength.
- EMB   : iShares J.P. Morgan USD Emerging Markets Bond ETF. Used as a real,
  aggregate EM risk-premium PROXY (EMB's own dividend/price behavior implies
  a market-wide EM spread), NOT a substitute for any individual country's
  sovereign spread -- overeign-risk-index/market_signals.py already
  investigated and confirmed no free source publishes per-country EMBI/CDS
  data (see that module's docstring, point 4). This is deliberately labeled
  a market-wide proxy everywhere it's used, never attributed to one country.

All annual averages, 2010-present, through today -- consistent with this
project's existing real-time-vs-WDI-lag disclosure already documented in
fetch_shock_drivers.py.
"""
import datetime
import json

import yfinance as yf

TODAY = datetime.date.today().isoformat()

TICKERS = {
    "vix": "^VIX",
    "us_10y_yield_pct": "^TNX",
    "dollar_index": "DX-Y.NYB",
    "em_bond_etf_price_usd": "EMB",
}


def fetch_annual(ticker):
    hist = yf.Ticker(ticker).history(start="2010-01-01", end=TODAY)
    if hist is None or hist.empty:
        print(f"{ticker}: EMPTY result from yfinance")
        return {}
    hist["year"] = hist.index.year
    annual = hist.groupby("year")["Close"].mean()
    result = {int(y): float(v) for y, v in annual.items()}
    print(f"{ticker}: {len(result)} annual points fetched")
    return result


if __name__ == "__main__":
    out = {}
    for key, ticker in TICKERS.items():
        series = fetch_annual(ticker)
        if key == "us_10y_yield_pct":
            # ^TNX quotes yield * 10 (e.g. 42.5 means 4.25%) -- divide back
            # to a real percentage, a well-documented Yahoo Finance quirk.
            series = {y: v / 10 for y, v in series.items()}
        out[key] = series

    with open("global_conditions.json", "w") as f:
        json.dump(out, f, indent=2)

    print("\nSaved global_conditions.json")
    for key, series in out.items():
        sample = dict(list(series.items())[-3:])
        print(f"{key} (latest 3 years): {sample}")
