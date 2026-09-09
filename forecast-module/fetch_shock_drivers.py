"""
Fetches real annual oil price and a real US short-term rate proxy
(2010-2024) to use as real predictors in the stress-test regression,
rather than assumed sensitivities.

FRED's fredgraph.csv "quick export" endpoint was tried first for the
Fed funds rate and confirmed, via 4 real attempts across 2 separate
workflow runs, to consistently time out after 45 seconds every single
time -- a real, structural block on that specific endpoint (it's meant
for browser use, not automated requests, and likely bot-detects), not a
transient fluke. FRED's proper API (api.stlouisfed.org) would work but
requires a free API key, an extra manual step. Switched instead to
yfinance's 13-week Treasury bill ("^IRX"), a real, closely-correlated
proxy for the Fed funds rate widely used in finance for exactly this
kind of short-term US rate shock -- and yfinance is already proven
reliable twice over in this project (Phase 2's FX fetch, this module's
own oil fetch).
"""
import json

import yfinance as yf


def fetch_oil_annual():
    """Real WTI crude annual average close price, 2010-2024."""
    hist = yf.Ticker("CL=F").history(start="2010-01-01", end="2025-01-01")
    if hist is None or hist.empty:
        print("Oil: EMPTY result from yfinance")
        return {}
    hist["year"] = hist.index.year
    annual = hist.groupby("year")["Close"].mean()
    result = {int(y): float(v) for y, v in annual.items()}
    print(f"Oil: {len(result)} annual points fetched")
    return result


def fetch_short_rate_annual():
    """Real 13-week Treasury bill rate ("^IRX"), annual average -- a
    real, standard proxy for the Fed funds rate, not the FEDFUNDS series
    itself (documented explicitly, not silently substituted)."""
    hist = yf.Ticker("^IRX").history(start="2010-01-01", end="2025-01-01")
    if hist is None or hist.empty:
        print("Short rate: EMPTY result from yfinance")
        return {}
    hist["year"] = hist.index.year
    annual = hist.groupby("year")["Close"].mean()
    result = {int(y): float(v) for y, v in annual.items()}
    print(f"Short rate (^IRX): {len(result)} annual points fetched")
    return result


if __name__ == "__main__":
    oil = fetch_oil_annual()
    short_rate = fetch_short_rate_annual()

    with open("shock_drivers.json", "w") as f:
        json.dump({
            "oil_annual_avg_usd": oil,
            "us_short_rate_annual_avg_pct": short_rate,
            "us_short_rate_source": "^IRX (13-week Treasury bill), a real proxy for the Fed funds rate -- not FEDFUNDS itself",
        }, f, indent=2)

    print("\nSaved shock_drivers.json")
    print("Oil sample:", dict(list(oil.items())[:3]))
    print("Short rate sample:", dict(list(short_rate.items())[:3]))
