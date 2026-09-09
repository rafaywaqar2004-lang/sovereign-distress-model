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
    "TUR": "TRY",  # Turkish Lira
    "QAT": "QAR",  # Qatari Riyal (pegged -- real yfinance coverage unconfirmed until fetched)
    "SAU": "SAR",  # Saudi Riyal (pegged -- real yfinance coverage unconfirmed until fetched)
    "SDN": "SDG",  # Sudanese Pound (thinly traded -- real yfinance coverage unconfirmed until fetched)
    "ETH": "ETB",  # Ethiopian Birr (real yfinance coverage unconfirmed until fetched)
    "ISR": "ILS",  # Israeli Shekel
    "IRN": "IRR",  # Iranian Rial (sanctions-affected -- real yfinance coverage genuinely uncertain until fetched)
}
