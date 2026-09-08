"""
Fetches real GDELT 2.0 Doc API timeline data (media tone + volume) around
each real shock event in shock_events.py, as a quantitative measure of
shock intensity -- replacing hand-coded "this was a big shock" judgment
calls with an actual event-count/tone signal from real news coverage.

Runs via GitHub Actions (.github/workflows/fetch-shocks.yml), not
interactively -- the sandbox this project is otherwise developed in blocks
outbound requests to gdeltproject.org by policy, so this script is written
carefully and validated by inspecting its REAL output once the workflow
actually runs, not assumed correct from local testing that isn't possible
here.

GDELT's Doc API filters by FIPS 10-4 country codes (see fips_codes.py),
not ISO3 -- a real, documented detail, and the mapping for a few countries
is explicitly flagged there as unverified until real fetched output confirms
it returns country-relevant results.
"""
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

from shock_events import SHOCK_EVENTS
from fips_codes import ISO3_TO_FIPS, CONFIDENCE_FLAGGED

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
WINDOW_DAYS = 30  # days before/after the event date to pull a timeline for


def fetch_timeline(fips_code, center_date, mode="timelinetone", window_days=WINDOW_DAYS, retries=3):
    """Real GDELT Doc API call. mode='timelinetone' returns average daily
    sentiment of news coverage; mode='timelinevol' returns coverage volume
    as a % of all monitored news that day. Both are real, documented Doc API
    modes -- see https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/."""
    start = (center_date - timedelta(days=window_days)).strftime("%Y%m%d000000")
    end = (center_date + timedelta(days=window_days)).strftime("%Y%m%d000000")

    query = f"sourcecountry:{fips_code}"
    params = {
        "query": query,
        "mode": mode,
        "format": "json",
        "startdatetime": start,
        "enddatetime": end,
    }
    url = f"{GDELT_DOC_API}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; research-script/1.0)"})
    for attempt in range(retries):
        print(f"  [{mode}] attempt {attempt+1}/{retries}: {url}", flush=True)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                print(f"  [{mode}] got {len(raw)} bytes back", flush=True)
                return json.loads(raw)
        except Exception as e:
            print(f"  [{mode}] attempt {attempt+1}/{retries} failed for {fips_code}: {e}", flush=True)
            time.sleep(2)
    return None


def main():
    results = []
    validation_notes = []

    for event in SHOCK_EVENTS:
        code = event["country_code"]
        fips = ISO3_TO_FIPS.get(code)
        if fips is None:
            print(f"SKIP {code}: no FIPS mapping (see fips_codes.py)")
            continue

        center = datetime.strptime(event["event_date"], "%Y-%m-%d")
        print(f"\nFetching {code} ({fips}) around {event['event_date']} -- {event['label']}")

        tone_data = fetch_timeline(fips, center, mode="timelinetone")
        vol_data = fetch_timeline(fips, center, mode="timelinevol")

        n_tone_points = len(tone_data["timeline"][0]["data"]) if tone_data and tone_data.get("timeline") else 0
        n_vol_points = len(vol_data["timeline"][0]["data"]) if vol_data and vol_data.get("timeline") else 0

        print(f"  tone timeline points: {n_tone_points}, volume timeline points: {n_vol_points}")

        if code in CONFIDENCE_FLAGGED:
            note = (
                f"{code} ({fips}) is a CONFIDENCE_FLAGGED FIPS mapping -- "
                f"got {n_tone_points} tone / {n_vol_points} volume points back. "
                f"{'Non-zero result suggests the code is at least reaching real data.' if n_tone_points else 'ZERO points back -- this FIPS code is likely WRONG and needs fixing, not trusting.'}"
            )
            print(f"  *** {note}")
            validation_notes.append(note)

        results.append({
            "country_code": code,
            "fips_code": fips,
            "event_date": event["event_date"],
            "label": event["label"],
            "tone_timeline": tone_data,
            "volume_timeline": vol_data,
        })

    with open("shock_timelines_raw.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved shock_timelines_raw.json ({len(results)} events)")
    if validation_notes:
        print("\n=== FIPS mapping validation notes (check these before trusting the flagged codes) ===")
        for n in validation_notes:
            print(f"- {n}")


if __name__ == "__main__":
    main()
