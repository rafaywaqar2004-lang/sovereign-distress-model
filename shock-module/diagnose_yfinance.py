"""
Third real attempt at getting daily FX data around the 5 shock events.
Frankfurter (ECB-based) doesn't cover any of these 5 currencies at all --
confirmed by its own /v1/currencies list. This tests yfinance instead,
which MENASA's own app.py already uses successfully in production (for
stock index tickers, not FX, so this is genuinely new ground, not just
reusing a known-working call).

Yahoo Finance FX tickers use the convention "{CURRENCY}=X" for USD/CURRENCY.
Tests each of the 5 real event windows directly (not just "does the ticker
exist") since a ticker can exist but have no real data for pinned pandemic/
crisis periods for a thin currency.
"""
import sys
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed -- this diagnostic needs it added to requirements first.")
    sys.exit(1)

from shock_events import SHOCK_EVENTS
from fx_currencies import EVENT_CURRENCIES

WINDOW_DAYS = 30

for event in SHOCK_EVENTS:
    code = event["country_code"]
    currency = EVENT_CURRENCIES.get(code)
    if currency is None:
        continue

    center = datetime.strptime(event["event_date"], "%Y-%m-%d")
    start = (center - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
    end = (center + timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
    ticker_symbol = f"{currency}=X"

    print(f"\n=== {code} / {ticker_symbol} around {event['event_date']} ({start} to {end}) ===", flush=True)
    try:
        hist = yf.Ticker(ticker_symbol).history(start=start, end=end)
        if hist is None or hist.empty:
            print(f"  EMPTY -- yfinance returned no rows for this ticker/window", flush=True)
        else:
            print(f"  {len(hist)} rows returned. First: {hist.index[0].date()} = {hist['Close'].iloc[0]:.4f}, "
                  f"Last: {hist.index[-1].date()} = {hist['Close'].iloc[-1]:.4f}", flush=True)
    except Exception as e:
        print(f"  FAILED: {e}", flush=True)
