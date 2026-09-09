"""
ISO 4217 currency codes for the 5 real shock events with confirmed GDELT
data (shock_events.py). Standard, well-established codes -- the real
uncertainty here isn't the code itself, it's whether Frankfurter's
underlying ECB reference-rate data actually covers each one (some of these
are thin, non-major-market currencies), verified against real fetched
output, not assumed.
"""

EVENT_CURRENCIES = {
    "LBN": "LBP",  # Lebanese Pound
    "LKA": "LKR",  # Sri Lankan Rupee
    "AFG": "AFN",  # Afghan Afghani
    "EGY": "EGP",  # Egyptian Pound
    "PAK": "PKR",  # Pakistani Rupee
}
