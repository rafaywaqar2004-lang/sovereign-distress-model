"""
GDELT's Doc API filters by FIPS 10-4 country codes, not ISO3 -- a real,
easy-to-get-wrong detail. Mapping for the 34-country panel this project
shares with the MENASA Risk Monitor.

CONFIDENCE_FLAGGED entries are ones I'm not fully certain of without a live
lookup against GDELT's own documentation/codebook -- verified against real
fetched results (see fetch_shocks.py's validation step) before being trusted,
not assumed correct just because they're in this table.
"""

ISO3_TO_FIPS = {
    "DZA": "AG",  # Algeria
    "BHR": "BA",  # Bahrain
    "EGY": "EG",  # Egypt
    "IRN": "IR",  # Iran
    "IRQ": "IZ",  # Iraq
    "ISR": "IS",  # Israel
    "JOR": "JO",  # Jordan
    "KWT": "KU",  # Kuwait
    "LBN": "LE",  # Lebanon
    "LBY": "LY",  # Libya
    "MAR": "MO",  # Morocco
    "OMN": "MU",  # Oman
    "QAT": "QA",  # Qatar
    "SAU": "SA",  # Saudi Arabia
    "SYR": "SY",  # Syria
    "TUN": "TS",  # Tunisia
    "ARE": "TC",  # UAE -- CONFIDENCE_FLAGGED (FIPS uses "TC", easy to confuse with ISO3 "ARE"/common "AE")
    "YEM": "YM",  # Yemen
    "AFG": "AF",  # Afghanistan
    "BGD": "BG",  # Bangladesh
    "BTN": "BT",  # Bhutan
    "IND": "IN",  # India
    "MDV": "MV",  # Maldives
    "NPL": "NP",  # Nepal
    "PAK": "PK",  # Pakistan
    "LKA": "CE",  # Sri Lanka -- CONFIDENCE_FLAGGED (FIPS "CE" = Ceylon, not obviously "LK")
    "TUR": "TU",  # Turkey
    "SDN": "SU",  # Sudan
    "SSD": "OD",  # South Sudan -- CONFIDENCE_FLAGGED (newer country, FIPS code less commonly seen)
    "ETH": "ET",  # Ethiopia
    "SOM": "SO",  # Somalia
    "DJI": "DJ",  # Djibouti
    "ERI": "ER",  # Eritrea
    # PSE (Palestine) deliberately omitted -- FIPS/GDELT split West Bank ("WE")
    # and Gaza ("GZ") rather than a single unified code, and this project's
    # panel treats Palestine as one row. Needs a real decision (query both and
    # combine, or pick one) before adding -- not guessed here.
}

CONFIDENCE_FLAGGED = {"ARE", "LKA", "SSD"}
