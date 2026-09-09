"""
Fetches real annual oil price and US Fed funds rate data (2010-2024) to
use as real predictors in the stress-test regression, rather than assumed
sensitivities. Oil via yfinance (WTI futures, "CL=F" -- same tool proven
reliable in the shock-module's FX fetch). Fed funds rate via FRED's public
CSV export, which doesn't require an API key.

Runs via GitHub Actions -- same reason as every other fetch in this
project: this sandbox blocks both domains directly.
"""
import json
import time
import urllib.request
import urllib.error
import io
import csv

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


def fetch_fed_funds_annual():
    """Real US Federal Funds effective rate, FRED series FEDFUNDS, monthly
    -> annual average, via FRED's public CSV endpoint (no API key)."""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; research-script/1.0)"})
    raw = None
    for attempt in range(4):
        try:
            print(f"Fed funds: attempt {attempt+1}/4: {url}", flush=True)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read().decode("utf-8")
                print(f"Fed funds: got {len(raw)} bytes back", flush=True)
                break
        except Exception as e:
            print(f"Fed funds: attempt {attempt+1}/4 failed -- {e}", flush=True)
            if attempt < 3:
                time.sleep(5)
    if raw is None:
        print("Fed funds: FAILED after 4 attempts")
        return {}

    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    if not rows:
        print("Fed funds: empty CSV returned")
        return {}
    date_col, val_col = reader.fieldnames[0], reader.fieldnames[1]
    print(f"Fed funds: columns are {reader.fieldnames}, {len(rows)} monthly rows")

    by_year = {}
    for row in rows:
        year = int(row[date_col][:4])
        if 2010 <= year <= 2024:
            try:
                val = float(row[val_col])
            except ValueError:
                continue
            by_year.setdefault(year, []).append(val)

    result = {y: sum(vals) / len(vals) for y, vals in by_year.items()}
    print(f"Fed funds: {len(result)} annual points computed")
    return result


if __name__ == "__main__":
    oil = fetch_oil_annual()
    fed = fetch_fed_funds_annual()

    with open("shock_drivers.json", "w") as f:
        json.dump({"oil_annual_avg_usd": oil, "fed_funds_annual_avg_pct": fed}, f, indent=2)

    print("\nSaved shock_drivers.json")
    print("Oil sample:", dict(list(oil.items())[:3]))
    print("Fed funds sample:", dict(list(fed.items())[:3]))
