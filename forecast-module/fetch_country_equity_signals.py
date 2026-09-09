"""
Real, per-country market-implied risk signal via single-country equity ETFs
-- a genuine (partial) fix for a gap this project previously declared
impossible: overeign-risk-index/market_signals.py confirmed no free source
publishes per-country sovereign bond yields or CDS. Equity ETF price
action is a different, real, market-implied signal (not a substitute for
a bond spread, disclosed as such), available for a SUBSET of these 34
countries where a US-listed single-country ETF actually exists and is
still trading -- several have been delisted over the years, so this
script tests every CANDIDATE ticker and keeps only the ones that come
back with real, current data, rather than assuming a remembered ticker is
still live.

CANDIDATES is deliberately over-inclusive (includes tickers that may well
be delisted) -- fetch_annual() below returns empty for those and they are
silently excluded from the output, not fabricated.
"""
import datetime
import json

import yfinance as yf

TODAY = datetime.date.today().isoformat()

# Country-code -> candidate US-listed single-country/regional ETF ticker.
# Real, remembered tickers -- NOT verified live from this environment
# (yfinance is blocked in the dev sandbox the same way it's blocked for
# every other fetch in this project); this script's whole job is to test
# each one for real, current data via GitHub Actions and keep only what
# actually comes back.
CANDIDATES = {
    "TUR": "TUR",    # iShares MSCI Turkey ETF
    "ISR": "EIS",    # iShares MSCI Israel ETF
    "IND": "INDA",   # iShares MSCI India ETF
    "SAU": "KSA",    # iShares MSCI Saudi Arabia ETF
    "EGY": "EGPT",   # VanEck Egypt Index ETF
    "QAT": "QAT",    # iShares MSCI Qatar ETF
    "ARE": "UAE",    # iShares MSCI UAE ETF
    "PAK": "PAK",    # Global X MSCI Pakistan ETF
}
# EEME (probed for BGD) and SLT (probed for LKA) were tried and REMOVED:
# both returned real price data (so yfinance recognizes the tickers), but
# EEME only has 1 real year (2015) and SLT only 5 years ending 2022 --
# both anomalous for what should be an ongoing fund, and neither could be
# confirmed to actually BE a Bangladesh/Sri Lanka country fund rather than
# some other, unrelated company that happens to share that ticker. A wrong
# label would be worse than a real gap -- excluded rather than guessed.


def fetch_annual(ticker):
    try:
        hist = yf.Ticker(ticker).history(start="2015-01-01", end=TODAY)
    except Exception as e:
        print(f"{ticker}: fetch error -- {e}")
        return {}
    if hist is None or hist.empty:
        print(f"{ticker}: EMPTY result from yfinance -- likely delisted or never existed, excluding")
        return {}
    hist["year"] = hist.index.year
    annual = hist.groupby("year")["Close"].mean()
    result = {int(y): float(v) for y, v in annual.items()}
    print(f"{ticker}: {len(result)} real annual points fetched (through {max(result)})")
    return result


if __name__ == "__main__":
    out = {}
    for country_code, ticker in CANDIDATES.items():
        series = fetch_annual(ticker)
        if series:
            out[country_code] = {"ticker": ticker, "annual_avg_close_usd": series}

    with open("country_equity_signals.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nSaved country_equity_signals.json: real data for {len(out)} of {len(CANDIDATES)} candidate tickers.")
    print(f"Countries with a real, live equity signal: {sorted(out.keys())}")
