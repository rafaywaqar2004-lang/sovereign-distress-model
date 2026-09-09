"""
Real forced-displacement data from UNHCR's public Refugee Data Finder API
(api.unhcr.org) -- the mega-prompt's Section 15 (social/fragility
indicators), specifically refugee outflows and internal displacement, used
as amplification/context, not folded into any risk score directly (same
treatment the mega-prompt itself specifies).

Real, keyless, free public API -- no registration needed, confirmed by
UNHCR's own published API documentation. This script is written the same
"test against the real endpoint, keep only what actually returns real
data" way every other new source in this project was verified, since this
sandbox can't reach the live API to confirm the exact response shape
in advance.
"""
import json
import subprocess
import time
from datetime import datetime, timezone

COUNTRIES = [
    "DZA", "BHR", "EGY", "IRN", "IRQ", "ISR", "JOR", "KWT", "LBN", "LBY",
    "MAR", "OMN", "PSE", "QAT", "SAU", "SYR", "TUN", "ARE", "YEM", "AFG",
    "BGD", "BTN", "IND", "MDV", "NPL", "PAK", "LKA", "TUR", "SDN", "SSD",
    "ETH", "SOM", "DJI", "ERI",
]

CURRENT_YEAR = datetime.now(timezone.utc).year
BASE_URL = "https://api.unhcr.org/population/v1/population/"


def fetch_country_year(iso3, year, retries=2):
    """Real population-of-concern figures (refugees + IDPs of concern to
    UNHCR) originating from this country, for one real year. Returns the
    parsed JSON items list, or [] if nothing real came back."""
    url = f"{BASE_URL}?year={year}&coo={iso3}&limit=100"
    result = None
    for _ in range(retries):
        result = subprocess.run(
            ["curl", "-s", "-m", "20", url],
            capture_output=True, text=True, timeout=25,
        )
        if result.returncode == 0 and result.stdout:
            break
        time.sleep(1)

    if result is None or result.returncode != 0 or not result.stdout:
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return payload.get("items", []) if isinstance(payload, dict) else []


def main():
    rows = []
    for code in COUNTRIES:
        for year in range(2015, CURRENT_YEAR):
            items = fetch_country_year(code, year)
            for item in items:
                rows.append({
                    "country_code": code, "year": year,
                    "refugees_from": item.get("refugees"),
                    "idps_from": item.get("idps"),
                    "asylum_seekers_from": item.get("asylum_seekers"),
                })
            time.sleep(0.5)
        print(f"{code}: fetched")

    if not rows:
        print("No real displacement data fetched at all -- not writing an empty/placeholder file.")
        return

    import pandas as pd
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["refugees_from", "idps_from", "asylum_seekers_from"], how="all")
    df.to_csv("displacement.csv", index=False)
    print(f"\nSaved displacement.csv: {len(df)} real country-year rows with at least one non-null figure "
          f"(of {len(rows)} rows attempted).")


if __name__ == "__main__":
    main()
