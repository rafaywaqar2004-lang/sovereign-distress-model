"""
One-shot diagnostic: the real fetch script got a clean HTTP 404 (a valid
JSON error response, not a connection failure) on every single request,
across 5 different currencies -- meaning the domain is reachable but the
URL shape is wrong, not that these currencies aren't covered. Rather than
guess again through another slow GitHub Actions round-trip, this tests
several candidate endpoint shapes at once against a single, well-known
currency pair (USD->EUR, which any working FX API will have) to find the
one that's actually real.
"""
import json
import urllib.request
import urllib.error

CANDIDATES = [
    "https://api.frankfurter.dev/v1/latest?from=USD&to=EUR",
    "https://api.frankfurter.dev/v1/2024-01-15?from=USD&to=EUR",
    "https://api.frankfurter.dev/v1/2024-01-01..2024-01-31?from=USD&to=EUR",
    "https://api.frankfurter.app/latest?from=USD&to=EUR",
    "https://api.frankfurter.app/2024-01-15?from=USD&to=EUR",
    "https://api.frankfurter.app/2024-01-01..2024-01-31?from=USD&to=EUR",
]

for url in CANDIDATES:
    print(f"\n=== {url} ===", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; research-script/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            print(f"HTTP {resp.status} -- {raw[:300]}", flush=True)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        print(f"HTTP {e.code} -- {body}", flush=True)
    except Exception as e:
        print(f"FAILED: {e}", flush=True)
