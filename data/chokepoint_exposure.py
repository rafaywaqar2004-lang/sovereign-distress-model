"""
Real, sourced maritime-chokepoint exposure for this project's 34 MENA/South
Asia countries -- the mega-prompt's Section 17 (Supply-Chain & Chokepoint
Exposure), built the way that section actually asks: "Use actual trade/
shipping relationships when possible," not proximity assumptions.

This is NOT a live-fetchable pipeline (no free API publishes real-time
Suez/Hormuz/Bab-el-Mandeb transit risk) -- it is real, cited, manually
researched data, copied from the companion overeign-risk-index project's
own already-fact-checked geoeconomic_data.py (verified via live web search
against the Suez Canal Authority, gCaptain, Lloyd's List Intelligence,
Al Jazeera, CNBC, Bloomberg, CNN, and the U.S. EIA -- full citations kept
below exactly as sourced there). Copied rather than re-researched, same
precedent as this project's own driver_history.csv, to avoid drifting from
an already-validated source. See that project's geoeconomic_data.py for the
complete original citation list; only the fields this project actually uses
are reproduced here.

EXPOSURE ASSIGNMENT METHOD (real geography/trade dependency, not proximity):
- Suez Canal: Egypt is the direct operator (canal-transit-fee revenue is a
  real, material fiscal item for Egypt specifically).
- Bab el-Mandeb / southern Red Sea: the four littoral/adjacent states whose
  own coastline and regional trade directly sit on this strait --
  Djibouti, Yemen, Somalia, Eritrea.
- Strait of Hormuz: Iran and Oman are the two littoral states; Saudi Arabia,
  UAE, Qatar, Kuwait, Iraq, and Bahrain are the Gulf oil/gas exporters whose
  hydrocarbon exports must physically transit Hormuz to reach open water
  (a real, structural dependency, not an assumption -- there is no other
  sea route out of the Persian Gulf).
All other countries in the panel: no direct chokepoint exposure by this
method. That is a real finding, not a gap -- e.g. Pakistan and India trade
extensively by sea but are not geographically dependent on any one of these
three specific chokepoints the way the Gulf exporters are on Hormuz.
"""

MARITIME_CHOKEPOINTS = {
    "suez_canal": {
        "name": "Suez Canal",
        "risk_level": "High",
        "notes": (
            "Traffic collapsed after Houthi Red Sea attacks began late 2023 and has only "
            "partially recovered; 2026 reporting is contradictory on how far recovery has "
            "gone (accounts range from an 8-month traffic high in mid-August 2026 to still "
            "60% below normal). Most Asia-Europe cargo still routes via the Cape of Good Hope."
        ),
        "source": "Suez Canal Authority / gCaptain / Lloyd's List Intelligence, via overeign-risk-index/geoeconomic_data.py",
    },
    "bab_el_mandeb": {
        "name": "Bab el-Mandeb Strait",
        "risk_level": "Critical",
        "notes": (
            "Houthi attacks drove the 2023-2024 diversion crisis; renewed escalation in 2026 "
            "(a declared naval blockade of Saudi Arabia in July 2026, a fatal attack on a "
            "vessel in August 2026) compounds with the near-closure of Hormuz as the most "
            "acutely volatile of the three chokepoints as of August 2026."
        ),
        "source": "Al Jazeera / CNBC / S&P Global, via overeign-risk-index/geoeconomic_data.py",
    },
    "strait_of_hormuz": {
        "name": "Strait of Hormuz",
        "risk_level": "Critical",
        "notes": (
            "The US-Israel war on Iran (started Feb 28, 2026) triggered a collapse in transits "
            "-- effectively closed to commercial shipping by August 2026, with only a brief "
            "partial recovery during a temporary US-Iran MoU that later expired. Normally ~20% "
            "of global oil and a large share of global LNG transits here."
        ),
        "source": "Bloomberg / CNN / Al Jazeera / U.S. EIA, via overeign-risk-index/geoeconomic_data.py",
    },
}

CHOKEPOINT_EXPOSURE = {
    "EGY": ["suez_canal"],
    "DJI": ["bab_el_mandeb"],
    "YEM": ["bab_el_mandeb"],
    "SOM": ["bab_el_mandeb"],
    "ERI": ["bab_el_mandeb"],
    "IRN": ["strait_of_hormuz"],
    "OMN": ["strait_of_hormuz"],
    "SAU": ["strait_of_hormuz"],
    "ARE": ["strait_of_hormuz"],
    "QAT": ["strait_of_hormuz"],
    "KWT": ["strait_of_hormuz"],
    "IRQ": ["strait_of_hormuz"],
    "BHR": ["strait_of_hormuz"],
}


def exposure_summary(country_code):
    """Returns (list of chokepoint keys, highest risk_level among them, or
    None) for a country. None/[] means no direct exposure by this method --
    a real finding, not missing data."""
    keys = CHOKEPOINT_EXPOSURE.get(country_code, [])
    if not keys:
        return [], None
    levels = [MARITIME_CHOKEPOINTS[k]["risk_level"] for k in keys]
    rank = {"Critical": 2, "High": 1}
    worst = max(levels, key=lambda l: rank.get(l, 0))
    return keys, worst
