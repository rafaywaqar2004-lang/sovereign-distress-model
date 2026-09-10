"""
Real top-export / top-import product categories for this project's 34
tracked countries -- "what does this country actually trade in," not just
"who does it trade with" (trade_network.py already covers the partner
side). Same real UN Comtrade API, same auth/reporter-code/rate-limit
pattern already proven in fetch_trade_network.py -- reused deliberately,
not reinvented -- but queried at the HS 2-digit "chapter" aggregation
level (Comtrade's own documented cmdCode=AG2 aggregate keyword) instead of
cmdCode=TOTAL, so the response is a real per-commodity-category breakdown
of that reporter's total imports/exports for the year.

Never fabricates a value if the key is missing or a request fails -- the
fetch just produces fewer real rows, exactly like fetch_trade_network.py.
"""
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone

import pandas as pd

from fetch_trade_network import COUNTRIES, COMTRADE_REPORTER_CODES

RATE_LIMIT_RE = re.compile(r"Try again in (\d+) second")
CURRENT_YEAR = datetime.now(timezone.utc).year
API_KEY = os.environ.get("COMTRADE_API_KEY")

_debug_subset = os.environ.get("FETCH_TRADE_COMMODITIES_COUNTRIES")
if _debug_subset:
    COUNTRIES = [c.strip() for c in _debug_subset.split(",") if c.strip()]


def _request(url):
    result = subprocess.run(
        ["curl", "-s", "-m", "20", "-H", f"Ocp-Apim-Subscription-Key: {API_KEY}", url],
        capture_output=True, text=True, timeout=25,
    )
    if result.returncode != 0 or not result.stdout:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def fetch_reporter_commodities(country_code, flow_code, max_rate_limit_waits=8):
    """Real HS2-chapter-level breakdown of one reporter's total imports or
    exports for the latest available year (falls back up to 2 years, same
    reporting-lag pattern as fetch_trade_network.py). Returns
    (year, list of {cmd_code, value_usd}) or (None, [])."""
    reporter = COMTRADE_REPORTER_CODES[country_code]
    for year in (CURRENT_YEAR - 1, CURRENT_YEAR - 2, CURRENT_YEAR - 3):
        url = (
            "https://comtradeapi.un.org/data/v1/get/C/A/HS"
            f"?reporterCode={reporter}&period={year}&cmdCode=AG2&flowCode={flow_code}"
            "&partnerCode=0&partner2Code=0&customsCode=C00&motCode=0&includeDesc=false"
            f"&subscription-key={API_KEY}"
        )
        payload = None
        for attempt in range(max_rate_limit_waits):
            payload = _request(url)
            if payload is None:
                time.sleep(2)
                continue
            if isinstance(payload, dict) and payload.get("statusCode") and payload.get("statusCode") != 200:
                message = payload.get("message", "unknown error")
                m = RATE_LIMIT_RE.search(message)
                if m:
                    wait = int(m.group(1)) + 1
                    print(f"  {country_code} {flow_code} {year}: rate-limited, waiting {wait}s (attempt {attempt + 1}/{max_rate_limit_waits})")
                    time.sleep(wait)
                    payload = None
                    continue
                print(f"  {country_code} {flow_code} {year}: rejected -- {message}")
                payload = None
                break
            break

        if payload is None:
            continue
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        cmd_rows = [
            {"cmd_code": r["cmdCode"], "value_usd": r["primaryValue"]}
            for r in rows
            if r.get("cmdCode") and len(str(r["cmdCode"])) == 2 and r.get("primaryValue")
        ]
        if cmd_rows:
            return year, cmd_rows
    return None, []


def main():
    if not API_KEY:
        print("COMTRADE_API_KEY not set -- cannot fetch real commodity data. Exiting without writing any file "
              "(never fabricating trade values to fill the gap).")
        return

    rows = []
    for code in COUNTRIES:
        for flow in ("M", "X"):
            year, cmd_rows = fetch_reporter_commodities(code, flow)
            if year is None:
                print(f"{code} {flow}: no real commodity data found in the last 3 reporting years")
                continue
            for cr in cmd_rows:
                rows.append({
                    "reporter_code": code, "flow": flow, "year": year,
                    "hs2_code": cr["cmd_code"], "value_usd": cr["value_usd"],
                })
            print(f"{code} {flow} {year}: {len(cmd_rows)} real HS2 category rows")
            time.sleep(0.3)

    if not rows:
        print("No real commodity data fetched at all -- not writing an empty/placeholder file.")
        return

    df = pd.DataFrame(rows)
    out_path = "trade_commodities_debug.csv" if _debug_subset else "trade_commodities.csv"
    df.to_csv(out_path, index=False)
    n_reporters = df["reporter_code"].nunique()
    print(f"\nSaved {out_path}: {len(df)} real reporter-commodity rows across {n_reporters} of "
          f"{len(COUNTRIES)} tracked countries.")


if __name__ == "__main__":
    main()
