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


def fetch_timeline(fips_code, center_date, mode="timelinetone", window_days=WINDOW_DAYS, retries=4):
    """Real GDELT Doc API call. mode='timelinetone' returns average daily
    sentiment of news coverage; mode='timelinevol' returns coverage volume
    as a % of all monitored news that day. Both are real, documented Doc API
    modes -- see https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/.

    GDELT rate-limits aggressively (HTTP 429) -- confirmed by the first real
    run of this script, which also showed successful responses taking
    11-13 seconds even when they succeed. Backoff here is sized off that
    real observed behavior, not guessed: 10s between retries (not 2s), and
    a 25s per-request timeout (not 15s, which was cutting it close against
    the observed 11-13s successful-response time)."""
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
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read().decode("utf-8")
                print(f"  [{mode}] got {len(raw)} bytes back", flush=True)
                return json.loads(raw)
        except Exception as e:
            print(f"  [{mode}] attempt {attempt+1}/{retries} failed for {fips_code}: {e}", flush=True)
            if attempt < retries - 1:
                time.sleep(10)
    return None


def main():
    results = []
    validation_notes = []

    # Save incrementally after each event -- a real, expensive lesson from
    # this exact script: GDELT's real rate-limiting got aggressive enough
    # with 12 events that a run legitimately timed out mid-way, and since
    # results were only written at the very end, 10 of 12 already-fetched
    # real events were silently lost. Now every event's real result is
    # written to disk as soon as it's fetched, so a timeout never discards
    # real work already done.
    def save():
        with open("shock_timelines_raw.json", "w") as f:
            json.dump(results, f, indent=2)

    for event in SHOCK_EVENTS:
        code = event["country_code"]
        fips = ISO3_TO_FIPS.get(code)
        if fips is None:
            print(f"SKIP {code}: no FIPS mapping (see fips_codes.py)")
            continue

        center = datetime.strptime(event["event_date"], "%Y-%m-%d")
        print(f"\nFetching {code} ({fips}) around {event['event_date']} -- {event['label']}")

        tone_data = fetch_timeline(fips, center, mode="timelinetone")
        time.sleep(8)  # space out calls proactively -- GDELT rate-limits back-to-back requests (confirmed 429s)
        vol_data = fetch_timeline(fips, center, mode="timelinevol")
        time.sleep(8)  # same spacing before the next country's first call

        n_tone_points = len(tone_data["timeline"][0]["data"]) if tone_data and tone_data.get("timeline") else 0
        n_vol_points = len(vol_data["timeline"][0]["data"]) if vol_data and vol_data.get("timeline") else 0

        print(f"  tone timeline points: {n_tone_points}, volume timeline points: {n_vol_points}")

        if code in CONFIDENCE_FLAGGED:
            # Judge on EITHER mode returning real data, not tone alone -- the
            # first real run showed a false alarm here: LKA's tone call
            # failed on rate-limiting (429) while its volume call succeeded
            # with 61 real points, which the old tone-only check misread as
            # "this FIPS code is wrong" when the code was actually fine.
            got_real_data = n_tone_points > 0 or n_vol_points > 0
            note = (
                f"{code} ({fips}) is a CONFIDENCE_FLAGGED FIPS mapping -- "
                f"got {n_tone_points} tone / {n_vol_points} volume points back. "
                f"{'At least one mode returned real data -- mapping looks correct.' if got_real_data else 'ZERO points back on BOTH modes -- this FIPS code is likely WRONG and needs fixing, not trusting.'}"
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
        save()
        print(f"  (saved progress: {len(results)} of {len(SHOCK_EVENTS)} events so far)")

    print(f"\nSaved shock_timelines_raw.json ({len(results)} events)")
    if validation_notes:
        print("\n=== FIPS mapping validation notes (check these before trusting the flagged codes) ===")
        for n in validation_notes:
            print(f"- {n}")


if __name__ == "__main__":
    main()
