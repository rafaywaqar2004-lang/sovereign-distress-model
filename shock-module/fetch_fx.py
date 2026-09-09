"""
Fetches real historical daily FX rates around each of the 5 confirmed
shock events using yfinance -- the source that actually works for these
currencies. Frankfurter (ECB reference rates) was tried first and
confirmed, via its own /v1/currencies list, to not cover any of
LBP/LKR/AFN/EGP/PKR at all -- a real, structural limitation of that
source, not a bug (see git history for that attempt). yfinance carries
these as "{CURRENCY}=X" tickers (USD/CURRENCY) and returned real,
plausible daily data for all 5 event windows when tested.

One honest data-quality note carried forward from that test: Lebanon's
LBP=X rate reflects the official/pegged rate, which was still nominally
holding in the March 2020 default window -- the real collapse played out
on Lebanon's parallel/black market, which this official series will not
capture. Flagged here rather than silently treated as "no shock."

Same real issue confirmed for a second currency after adding more events:
Iran's IRR=X returned only 2 unique values across a 60-day window
(42000-42100) around the September 2022 protest event -- Iran's stale,
subsidized OFFICIAL rate, not the real market/black-market rate (which has
traded far higher for years under sanctions). Kept, not dropped -- this is
real data, just not the data that actually moved during the real shock --
disclosed the same way as Lebanon's, not silently treated as "no real FX
movement."
"""
import json
import time
from datetime import datetime, timedelta

import yfinance as yf

from shock_events import SHOCK_EVENTS
from fx_currencies import EVENT_CURRENCIES

WINDOW_DAYS = 30


def main():
    results = []

    for event in SHOCK_EVENTS:
        code = event["country_code"]
        currency = EVENT_CURRENCIES.get(code)
        if currency is None:
            print(f"SKIP {code}: no currency mapping")
            continue

        center = datetime.strptime(event["event_date"], "%Y-%m-%d")
        start = (center - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
        end = (center + timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
        ticker_symbol = f"{currency}=X"

        print(f"\nFetching {code} ({ticker_symbol}) around {event['event_date']} -- {event['label']}", flush=True)
        hist = yf.Ticker(ticker_symbol).history(start=start, end=end)

        if hist is None or hist.empty:
            print(f"  EMPTY -- no rows returned", flush=True)
            rates = {}
        else:
            rates = {idx.strftime("%Y-%m-%d"): float(close) for idx, close in hist["Close"].items()}
            print(f"  {len(rates)} daily rate points returned", flush=True)

        results.append({
            "country_code": code,
            "currency_code": currency,
            "ticker": ticker_symbol,
            "event_date": event["event_date"],
            "label": event["label"],
            "rates": rates,
        })
        time.sleep(1)

    with open("fx_timelines_raw.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved fx_timelines_raw.json ({len(results)} events)")


if __name__ == "__main__":
    main()
