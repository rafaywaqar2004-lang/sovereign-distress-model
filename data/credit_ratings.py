"""
Real, current S&P sovereign credit ratings for the 34 tracked countries --
copied directly from the MENASA Risk Monitor's own sourced CREDIT_RATINGS
dataset (overeign-risk-index/context_data.py), not re-fetched or invented.

Explicitly a CURRENT SNAPSHOT (as of that project's last update), not a
historical time series -- real ratings by year for 2010-2024 were never
fetched for this project. That means this can only support a real
CROSS-SECTIONAL benchmark (does the distress model's current predicted
probability rank countries similarly to how rating agencies currently rank
them), not a genuine historical, time-varying benchmark. Stated plainly in
the app wherever this is used, not glossed over.
"""

SP_RATING = {
    "DZA": None, "BHR": "B", "EGY": "B", "IRN": None, "IRQ": "B-",
    "ISR": "A", "JOR": "BB-", "KWT": "AA-", "LBN": "SD", "LBY": None,
    "MAR": "BBB-", "OMN": "BBB-", "PSE": None, "QAT": "AA", "SAU": "A+",
    "SYR": None, "TUN": None, "ARE": "AA", "YEM": None, "AFG": None,
    "BGD": "B+", "BTN": None, "IND": "BBB", "MDV": "B-", "NPL": None,
    "PAK": "B-", "LKA": "CCC+", "TUR": "BB-", "SDN": None, "SSD": None,
    "ETH": "SD", "SOM": None, "DJI": None, "ERI": None,
}

# Standard S&P long-term issuer scale, best (1) to worst (22) -- a real,
# widely-used agency convention, not an invented ranking. SD (selective
# default) placed alongside D as effectively the worst real category.
SP_SCALE = {
    "AAA": 1, "AA+": 2, "AA": 3, "AA-": 4, "A+": 5, "A": 6, "A-": 7,
    "BBB+": 8, "BBB": 9, "BBB-": 10, "BB+": 11, "BB": 12, "BB-": 13,
    "B+": 14, "B": 15, "B-": 16, "CCC+": 17, "CCC": 18, "CCC-": 19,
    "CC": 20, "C": 21, "SD": 22, "D": 22,
}
