"""
Round 2: the endpoint shape is confirmed correct (all 6 candidates
returned HTTP 200 for USD/EUR). So the 404s on LBP/LKR/AFN/EGP/PKR must
be about currency coverage, not URL structure. This checks Frankfurter's
own /v1/currencies list directly -- the authoritative, real answer to
"does this free ECB-based source even carry these currencies," rather
than inferring it from repeated 404s.
"""
import json
import urllib.request
import urllib.error

from fx_currencies import EVENT_CURRENCIES

url = "https://api.frankfurter.dev/v1/currencies"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; research-script/1.0)"})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        supported = json.loads(raw)
        print(f"Frankfurter supports {len(supported)} currencies total.\n")
        for code, name in EVENT_CURRENCIES.items():
            covered = name in supported
            print(f"{code} ({name}): {'COVERED -- ' + supported.get(name, '') if covered else 'NOT COVERED'}")
        print("\nFull supported list:", json.dumps(supported, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:500]}")
except Exception as e:
    print(f"FAILED: {e}")
