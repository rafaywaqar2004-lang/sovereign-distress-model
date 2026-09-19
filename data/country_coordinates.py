"""Real capital-city coordinates for this project's 34 tracked countries.

Copied from the companion overeign-risk-index project's own
geoeconomic_data.py (COUNTRY_CAPITAL_COORDS) rather than re-researched --
same precedent already established in this project's own
data/chokepoint_exposure.py (which copies MARITIME_CHOKEPOINTS from the
same source, "to avoid drifting from an already-validated source"). These
are standard, uncontroversial capital-city coordinates, not a disputed or
research-grade fact.

Used by generate_qgis_geodata.py to build real geodesic (great-circle)
trade-route geometry for the Trade & Infrastructure tab's spillover-network
map -- a capital-city point stands in for each country on that map, the
same simplification the sibling MENASA Risk Monitor's own Trade Map uses.
"""

COUNTRY_CAPITAL_COORDS = {
    "DZA": (36.75, 3.06), "BHR": (26.23, 50.59), "EGY": (30.04, 31.24),
    "IRN": (35.69, 51.39), "IRQ": (33.31, 44.36), "ISR": (31.78, 35.22),
    "JOR": (31.95, 35.93), "KWT": (29.38, 47.99), "LBN": (33.89, 35.50),
    "LBY": (32.89, 13.19), "MAR": (34.02, -6.83), "OMN": (23.59, 58.41),
    "PSE": (31.90, 35.20), "QAT": (25.29, 51.53), "SAU": (24.71, 46.68),
    "SYR": (33.51, 36.29), "TUN": (36.81, 10.18), "ARE": (24.45, 54.38),
    "YEM": (15.37, 44.19), "AFG": (34.56, 69.21), "BGD": (23.81, 90.41),
    "BTN": (27.47, 89.64), "IND": (28.61, 77.21), "MDV": (4.17, 73.51),
    "NPL": (27.72, 85.32), "PAK": (33.68, 73.05), "LKA": (6.93, 79.85),
    "TUR": (39.9334, 32.8597), "SDN": (15.6, 32.5), "SSD": (4.8517, 31.5825),
    "ETH": (9.0359, 38.7525), "SOM": (2.03917, 45.34194), "DJI": (11.5944, 43.1480),
    "ERI": (15.33583, 38.94111),
}
