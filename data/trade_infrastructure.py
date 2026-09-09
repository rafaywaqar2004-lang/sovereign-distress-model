"""
Real trade/geo-economic infrastructure context for this project's 34
tracked countries: multilateral trade/political blocs, major seaports,
and maritime chokepoints -- the mega-prompt's Section 11 (trade
concentration/dependency) and Section 17 (chokepoint exposure) rendered
as a dedicated reference layer, not folded into any risk score.

Not a live-fetched dataset -- these are real, stable, well-established
facts (which trade bloc a country belongs to, which port is its primary
seaport), the same epistemic category as the country-capital coordinates
already used elsewhere in this project family. Trade-bloc memberships are
copied verbatim from the companion overeign-risk-index project's own
research (geoeconomic_data.py); ports are general, uncontroversial
geographic/economic knowledge, NOT independently re-verified against a
primary source in this session and deliberately excluding specific
recent statistics (TEU throughput, rankings) that change year to year
and weren't confirmed live -- named and described only, not quantified
with a number this project can't stand behind.
"""

# Copied verbatim from overeign-risk-index/geoeconomic_data.py's
# MENASA_COUNTRY_ALLIANCES -- real, cited multilateral memberships.
TRADE_BLOCS = {
    "DZA": {"memberships": ["OPEC", "Arab League"], "primary_bloc": "OPEC"},
    "BHR": {"memberships": ["GCC", "OPEC+ (non-OPEC participant)", "Arab League"], "primary_bloc": "GCC"},
    "EGY": {"memberships": ["Arab League", "BRICS+ (2024 member)", "D-8"], "primary_bloc": "BRICS+"},
    "IRN": {"memberships": ["OPEC", "BRICS+ (2024 member)"], "primary_bloc": "OPEC"},
    "IRQ": {"memberships": ["OPEC", "Arab League"], "primary_bloc": "OPEC"},
    "ISR": {"memberships": ["OECD"], "primary_bloc": "Non-aligned / OECD"},
    "JOR": {"memberships": ["Arab League"], "primary_bloc": "Arab League"},
    "KWT": {"memberships": ["GCC", "OPEC", "Arab League"], "primary_bloc": "GCC"},
    "LBN": {"memberships": ["Arab League"], "primary_bloc": "Arab League"},
    "LBY": {"memberships": ["OPEC", "Arab League"], "primary_bloc": "OPEC"},
    "MAR": {"memberships": ["Arab League"], "primary_bloc": "Arab League"},
    "OMN": {"memberships": ["GCC", "OPEC+ (non-OPEC participant)", "Arab League"], "primary_bloc": "GCC"},
    "PSE": {"memberships": ["Arab League"], "primary_bloc": "Arab League"},
    "QAT": {"memberships": ["GCC", "Arab League"], "primary_bloc": "GCC"},
    "SAU": {"memberships": ["GCC", "OPEC", "Arab League", "BRICS+ (invited 2024, accession unconfirmed)"], "primary_bloc": "GCC"},
    "SYR": {"memberships": ["Arab League (reinstated May 2023 after 12-year suspension)"], "primary_bloc": "Arab League"},
    "TUN": {"memberships": ["Arab League"], "primary_bloc": "Arab League"},
    "ARE": {"memberships": ["GCC", "OPEC", "Arab League", "BRICS+ (2024 member)"], "primary_bloc": "GCC"},
    "YEM": {"memberships": ["Arab League"], "primary_bloc": "Arab League"},
    "AFG": {"memberships": ["SAARC (dormant since 2014)"], "primary_bloc": "SAARC"},
    "BGD": {"memberships": ["SAARC (dormant since 2014)", "D-8"], "primary_bloc": "SAARC"},
    "BTN": {"memberships": ["SAARC (dormant since 2014)"], "primary_bloc": "SAARC"},
    "IND": {"memberships": ["SAARC (dormant since 2014)", "BRICS (founding member)"], "primary_bloc": "BRICS+"},
    "MDV": {"memberships": ["SAARC (dormant since 2014)"], "primary_bloc": "SAARC"},
    "NPL": {"memberships": ["SAARC (dormant since 2014)"], "primary_bloc": "SAARC"},
    "PAK": {"memberships": ["SAARC (dormant since 2014)", "D-8"], "primary_bloc": "SAARC"},
    "LKA": {"memberships": ["SAARC (dormant since 2014)"], "primary_bloc": "SAARC"},
    "TUR": {"memberships": ["NATO (member since 1952)", "OECD (founding member, 1961)", "G20", "EU Customs Union (since 1995)", "EU accession candidate (since 1999, talks frozen since 2018)", "OIC", "Organization of Turkic States"], "primary_bloc": "NATO"},
    "SDN": {"memberships": ["Arab League", "African Union (membership suspended since October 2021 coup)"], "primary_bloc": "Arab League"},
    "SSD": {"memberships": ["African Union (since independence, 2011)", "East African Community (acceded 2016)", "IGAD (since 2011)"], "primary_bloc": "IGAD / EAC"},
    "ETH": {"memberships": ["African Union (headquarters host)", "IGAD", "BRICS+ (joined January 1, 2024)", "COMESA"], "primary_bloc": "African Union / IGAD"},
    "SOM": {"memberships": ["Arab League (joined 1974)", "African Union", "IGAD (founding member)", "East African Community (joined November 2023)"], "primary_bloc": "Arab League"},
    "DJI": {"memberships": ["Arab League", "African Union", "IGAD (headquartered in Djibouti City)", "OIC"], "primary_bloc": "Arab League / African Union"},
    "ERI": {"memberships": ["African Union", "Arab League (observer status only, since 2003)", "Not an IGAD member (withdrew December 2025)"], "primary_bloc": "African Union / Horn of Africa"},
}
TRADE_BLOCS_SOURCE = "Copied from overeign-risk-index/geoeconomic_data.py (MENASA_COUNTRY_ALLIANCES)"

# Major seaports -- real, well-established facts, named/described only
# (no unverified recent statistics). Landlocked countries correctly show
# no seaport rather than an invented one.
MAJOR_PORTS = {
    "DZA": [{"name": "Port of Algiers", "note": "Algeria's principal port"}],
    "BHR": [{"name": "Khalifa Bin Salman Port (Hidd)", "note": "Bahrain's main deep-water port"}],
    "EGY": [
        {"name": "Port Said", "note": "At the Mediterranean end of the Suez Canal"},
        {"name": "Port of Alexandria", "note": "Egypt's principal general-cargo port"},
    ],
    "IRN": [{"name": "Bandar Abbas", "note": "Iran's main port, on the Strait of Hormuz"}],
    "IRQ": [{"name": "Umm Qasr", "note": "Iraq's main deep-water port"}],
    "ISR": [
        {"name": "Port of Haifa", "note": "Israel's largest port"},
        {"name": "Port of Ashdod", "note": "Israel's other major Mediterranean port"},
    ],
    "JOR": [{"name": "Port of Aqaba", "note": "Jordan's only seaport, on the Red Sea"}],
    "KWT": [{"name": "Shuwaikh / Mina Al Ahmadi", "note": "Kuwait's main commercial and oil-export ports"}],
    "LBN": [{"name": "Port of Beirut", "note": "Lebanon's principal port (site of the August 2020 explosion)"}],
    "LBY": [{"name": "Port of Tripoli", "note": "Libya's principal port"}],
    "MAR": [{"name": "Tanger Med", "note": "One of the Mediterranean's largest container transshipment hubs"}],
    "OMN": [
        {"name": "Port of Salalah", "note": "Major container transshipment hub on the Arabian Sea"},
        {"name": "Port of Sohar", "note": "Major industrial/bulk port"},
    ],
    "PSE": [{"name": "No functioning major seaport", "note": "Gaza's port access has been constrained for years; not comparable to other tracked countries"}],
    "QAT": [{"name": "Hamad Port", "note": "Qatar's principal deep-water port"}],
    "SAU": [
        {"name": "Jeddah Islamic Port", "note": "Saudi Arabia's main Red Sea port"},
        {"name": "King Abdulaziz Port (Dammam)", "note": "Main Gulf-side port"},
    ],
    "SYR": [
        {"name": "Port of Latakia", "note": "Syria's principal port"},
        {"name": "Port of Tartus", "note": "Also hosts a Russian naval facility"},
    ],
    "TUN": [{"name": "Port of Radès", "note": "Tunisia's main container port, near Tunis"}],
    "ARE": [
        {"name": "Jebel Ali Port (Dubai)", "note": "One of the world's largest container ports and transshipment hubs"},
        {"name": "Khalifa Port (Abu Dhabi)", "note": "Abu Dhabi's principal deep-water port"},
    ],
    "YEM": [
        {"name": "Port of Aden", "note": "Yemen's principal southern port"},
        {"name": "Port of Hodeidah", "note": "Key Red Sea port, repeatedly a flashpoint in the civil war"},
    ],
    "AFG": [{"name": "Landlocked", "note": "No seaport; trade depends on transit through neighboring countries"}],
    "BGD": [{"name": "Chattogram (Chittagong) Port", "note": "Bangladesh's principal port, handles the large majority of its trade"}],
    "BTN": [{"name": "Landlocked", "note": "No seaport; trade transits via India"}],
    "IND": [
        {"name": "Jawaharlal Nehru Port (Mumbai)", "note": "India's largest container port"},
        {"name": "Mundra Port", "note": "India's largest private port"},
    ],
    "MDV": [{"name": "Malé Commercial Harbour", "note": "The Maldives' main port"}],
    "NPL": [{"name": "Landlocked", "note": "No seaport; trade transits via India"}],
    "PAK": [
        {"name": "Karachi Port / Port Qasim", "note": "Pakistan's two principal ports"},
        {"name": "Gwadar Port", "note": "Deep-water port central to the China-Pakistan Economic Corridor"},
    ],
    "LKA": [{"name": "Port of Colombo", "note": "Major Indian Ocean transshipment hub"},
            {"name": "Hambantota Port", "note": "Operated under a long-term lease by a Chinese state firm since 2017"}],
    "TUR": [
        {"name": "Port of Mersin", "note": "Turkey's largest container port on the Mediterranean"},
        {"name": "Port of Ambarlı (Istanbul)", "note": "Major container port near Istanbul"},
    ],
    "SDN": [{"name": "Port Sudan", "note": "Sudan's only major seaport, on the Red Sea"}],
    "SSD": [{"name": "Landlocked", "note": "No seaport; trade transits via Sudan or Kenya"}],
    "ETH": [{"name": "Landlocked", "note": "No seaport since Eritrea's 1993 independence; relies heavily on the Port of Djibouti"}],
    "SOM": [
        {"name": "Port of Mogadishu", "note": "Somalia's principal port"},
        {"name": "Port of Berbera", "note": "In Somaliland; undergoing expansion with UAE investment"},
    ],
    "DJI": [{"name": "Port of Djibouti", "note": "A major regional transshipment hub; also hosts foreign military bases (US, China, France, Japan)"}],
    "ERI": [
        {"name": "Port of Massawa", "note": "Eritrea's main Red Sea port"},
        {"name": "Port of Assab", "note": "Eritrea's other major port"},
    ],
}
PORTS_SOURCE = "General, well-established geographic/economic knowledge -- not independently re-verified against a primary source in this session; no unverified recent statistics included."
