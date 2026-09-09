"""
Fetches real historical daily FX rates around each of the 5 confirmed
shock events (see shock_events.py / shock_timelines_raw.json) from
Frankfurter (api.frankfurter.dev), a free, no-API-key historical FX rate
service built on the European Central Bank's own reference rates.

Runs via GitHub Actions -- same reason as fetch_shocks.py: this sandbox
blocks outbound requests to api.frankfurter.dev by policy. Written to be
validated against REAL returned output once the workflow runs, not
assumed correct -- Frankfurter's ECB-based rates may not cover every one
of these currencies (some are thin/non-major-market), and this script
prints exactly what came back so that can be checked for real rather than
assumed.
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

from shock_events import SHOCK_EVENTS
from fx_currencies import EVENT_CURRENCIES

FRANKFURTER_API = "https://api.frankfurter.dev/v1"
WINDOW_DAYS = 30


def fetch_range(currency_code, start_date, end_date, retries=3):
    """Real Frankfurter time-series call: /v1/START..END?from=USD&to=XXX
    Returns the parsed JSON, or None if it never succeeds."""
    url = f"{FRANKFURTER_API}/{start_date}..{end_date}?from=USD&to={currency_code}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; research-script/1.0)"})

    for attempt in range(retries):
        print(f"  attempt {attempt+1}/{retries}: {url}", flush=True)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
                print(f"  got {len(raw)} bytes back", flush=True)
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            print(f"  attempt {attempt+1}/{retries} failed: HTTP {e.code} -- {body}", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"  attempt {attempt+1}/{retries} failed: {e}", flush=True)
            time.sleep(5)
    return None


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

        print(f"\nFetching {code} ({currency}) around {event['event_date']} -- {event['label']}", flush=True)
        data = fetch_range(currency, start, end)

        n_points = len(data.get("rates", {})) if data else 0
        print(f"  {n_points} daily rate points returned", flush=True)

        if data is None:
            print(f"  *** {code}/{currency}: FRANKFURTER RETURNED NOTHING after {3} attempts -- "
                  f"this currency may not be covered by ECB reference rates, check real output before assuming a bug. ***")
        elif n_points == 0:
            print(f"  *** {code}/{currency}: valid response but ZERO rate points -- likely means "
                  f"Frankfurter doesn't carry this currency at all (check its /v1/currencies list). ***")

        results.append({
            "country_code": code,
            "currency_code": currency,
            "event_date": event["event_date"],
            "label": event["label"],
            "fx_data": data,
        })
        time.sleep(3)  # light spacing -- Frankfurter isn't known to rate-limit as aggressively as GDELT did, but no reason to hammer it

    with open("fx_timelines_raw.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved fx_timelines_raw.json ({len(results)} events)")


if __name__ == "__main__":
    main()
