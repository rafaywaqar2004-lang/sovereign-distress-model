"""
Real bilateral trade network for this project's 34 tracked countries --
the mega-prompt's Section 23 (spillover/contagion engine), Section 11
(trade concentration), and Section 13 (geopolitical exposure network).

Data source: UN Comtrade's real API (comtradeapi.un.org/data/v1), the same
one overeign-risk-index/market_signals.py already validated the request
mechanics for (reporter codes, auth header/query-param pattern, retry
logic) -- reused here, not reinvented. Requires a real, free subscription
key (COMTRADE_API_KEY), passed as an environment variable by the GitHub
Actions workflow. Never fabricates a value if the key is missing or a
request fails -- the fetch just produces fewer real rows.

For each of the 34 countries as REPORTER, fetches its own real import (M)
and export (X) partner breakdown for the latest available year (falling
back one or two years if Comtrade's real reporting lag means the most
recent year isn't populated yet, exactly like fetch_trade_hhi already
does). That gives a real DIRECTED bilateral trade matrix: for every
(reporter, partner) pair where partner is also one of the 34 tracked
countries, how much reporter actually imports from / exports to partner,
in real USD.

68 real API calls total (34 countries x 2 flows), one call each returning
that reporter's full partner breakdown -- not a call per country-pair.
"""
import json
import os
import subprocess
import time
from datetime import datetime, timezone

import pandas as pd

COUNTRIES = [
    "DZA", "BHR", "EGY", "IRN", "IRQ", "ISR", "JOR", "KWT", "LBN", "LBY",
    "MAR", "OMN", "PSE", "QAT", "SAU", "SYR", "TUN", "ARE", "YEM", "AFG",
    "BGD", "BTN", "IND", "MDV", "NPL", "PAK", "LKA", "TUR", "SDN", "SSD",
    "ETH", "SOM", "DJI", "ERI",
]

# UN Comtrade's own current numeric reporter codes -- copied verbatim from
# overeign-risk-index/market_signals.py's COMTRADE_REPORTER_CODES (already
# confirmed against Comtrade's own reference file, including the Sudan/
# Ethiopia superseded-code disambiguation), not re-derived.
COMTRADE_REPORTER_CODES = {
    "DZA": 12, "BHR": 48, "EGY": 818, "IRN": 364, "IRQ": 368, "ISR": 376,
    "JOR": 400, "KWT": 414, "LBN": 422, "LBY": 434, "MAR": 504, "OMN": 512,
    "PSE": 275, "QAT": 634, "SAU": 682, "SYR": 760, "TUN": 788, "ARE": 784,
    "YEM": 887, "AFG": 4, "BGD": 50, "BTN": 64, "IND": 699, "MDV": 462,
    "NPL": 524, "PAK": 586, "LKA": 144, "TUR": 792, "SDN": 729, "SSD": 728,
    "ETH": 231, "SOM": 706, "DJI": 262, "ERI": 232,
}
# Inverse, for mapping a partner's Comtrade numeric code back to our own
# country_code -- only populated for the 34 tracked countries, so any
# partner outside this set is correctly treated as "rest of world" (a real
# category, not a gap) rather than silently dropped.
COMTRADE_CODE_TO_COUNTRY = {v: k for k, v in COMTRADE_REPORTER_CODES.items()}

CURRENT_YEAR = datetime.now(timezone.utc).year
API_KEY = os.environ.get("COMTRADE_API_KEY")
# Optional: restrict to a subset for a fast diagnostic re-run without
# re-fetching all 34 countries again (comma-separated country codes).
_debug_subset = os.environ.get("FETCH_TRADE_NETWORK_COUNTRIES")
if _debug_subset:
    COUNTRIES = [c.strip() for c in _debug_subset.split(",") if c.strip()]


def fetch_reporter_flow(country_code, flow_code, retries=2):
    """Real partner-level annual trade data for one reporter/flow. Tries
    the latest year, then up to 2 years back (Comtrade's real reporting lag
    is commonly 12-24 months) -- same fallback pattern already proven in
    fetch_trade_hhi. Returns (year, list of {partner_code_num, value_usd})
    or (None, []) if nothing real was found."""
    reporter = COMTRADE_REPORTER_CODES[country_code]
    for year in (CURRENT_YEAR - 1, CURRENT_YEAR - 2, CURRENT_YEAR - 3):
        url = (
            "https://comtradeapi.un.org/data/v1/get/C/A/HS"
            f"?reporterCode={reporter}&period={year}&cmdCode=TOTAL&flowCode={flow_code}"
            "&partnerCode=&partner2Code=0&customsCode=C00&motCode=0&includeDesc=false"
            f"&subscription-key={API_KEY}"
        )
        result = None
        for _ in range(retries):
            result = subprocess.run(
                ["curl", "-s", "-m", "20", "-H", f"Ocp-Apim-Subscription-Key: {API_KEY}", url],
                capture_output=True, text=True, timeout=25,
            )
            if result.returncode == 0 and result.stdout:
                break
            time.sleep(1)

        if result is None or result.returncode != 0 or not result.stdout:
            continue
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            continue

        if isinstance(payload, dict) and payload.get("statusCode") and payload.get("statusCode") != 200:
            print(f"  {country_code} {flow_code} {year}: rejected -- {payload.get('message', 'unknown error')}")
            continue

        rows = payload.get("data", []) if isinstance(payload, dict) else []
        print(f"  {country_code} {flow_code} {year}: raw response had {len(rows)} rows before filtering "
              f"(payload keys: {list(payload.keys()) if isinstance(payload, dict) else type(payload)})")
        partner_rows = [
            {"partner_comtrade_code": r["partnerCode"], "value_usd": r["primaryValue"]}
            for r in rows if r.get("partnerCode", 0) != 0 and r.get("primaryValue")
        ]
        if partner_rows:
            return year, partner_rows
    return None, []


def main():
    if not API_KEY:
        print("COMTRADE_API_KEY not set -- cannot fetch real trade data. Exiting without writing any file "
              "(never fabricating trade values to fill the gap).")
        return

    rows = []
    for code in COUNTRIES:
        for flow in ("M", "X"):
            year, partner_rows = fetch_reporter_flow(code, flow)
            if year is None:
                print(f"{code} {flow}: no real data found in the last 3 reporting years")
                continue
            for pr in partner_rows:
                partner_country = COMTRADE_CODE_TO_COUNTRY.get(pr["partner_comtrade_code"])
                rows.append({
                    "reporter_code": code, "flow": flow, "year": year,
                    "partner_comtrade_code": pr["partner_comtrade_code"],
                    "partner_code": partner_country,  # None = a real partner outside this project's 34-country set
                    "value_usd": pr["value_usd"],
                })
            print(f"{code} {flow} {year}: {len(partner_rows)} real partner rows")
            time.sleep(0.3)

    if not rows:
        print("No real trade data fetched at all -- not writing an empty/placeholder file.")
        return

    df = pd.DataFrame(rows)
    out_path = "trade_network_debug.csv" if _debug_subset else "trade_network.csv"
    df.to_csv(out_path, index=False)
    n_within_set = df["partner_code"].notna().sum()
    print(f"\nSaved {out_path}: {len(df)} real reporter-partner rows "
          f"({n_within_set} between two of this project's 34 tracked countries, "
          f"{len(df) - n_within_set} to real partners outside this set -- both are real, kept, not dropped).")


if __name__ == "__main__":
    main()
