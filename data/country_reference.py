"""
Real, well-established static reference facts for this project's 34
tracked countries: primary stock exchange, major named industries, and
major cities. Same epistemic category as trade_infrastructure.py (ports,
trade blocs) and government_structure.py -- real, uncontroversial facts
that don't change year to year and don't need a live API, NOT
independently re-verified against a primary source in this session.

MAJOR_INDUSTRIES here is a curated, named-industry description (e.g.
"Oil & gas, petrochemicals, tourism") -- the plain-language complement to
the two REAL, LIVE-FETCHED quantitative signals the app pairs it with:
sector value-added share of GDP (development_indicators.csv) and top
export product categories by real UN Comtrade value (trade_commodities.csv).
This curated list is not a substitute for those two real series, and the
app discloses that distinction rather than presenting it as fetched data.
"""

STOCK_EXCHANGES = {
    "DZA": {"name": "Algiers Stock Exchange (SGBV)", "note": "Very few listed companies; among the least active exchanges in the region."},
    "BHR": {"name": "Bahrain Bourse", "note": None},
    "EGY": {"name": "Egyptian Exchange (EGX)", "note": "One of the region's oldest and more liquid exchanges."},
    "IRN": {"name": "Tehran Stock Exchange (TSE)", "note": None},
    "IRQ": {"name": "Iraq Stock Exchange (ISX)", "note": None},
    "ISR": {"name": "Tel Aviv Stock Exchange (TASE)", "note": None},
    "JOR": {"name": "Amman Stock Exchange (ASE)", "note": None},
    "KWT": {"name": "Boursa Kuwait", "note": None},
    "LBN": {"name": "Beirut Stock Exchange (BSE)", "note": "Largely illiquid since Lebanon's 2019-2020 financial collapse."},
    "LBY": {"name": "Libyan Stock Market", "note": "Small, limited trading activity."},
    "MAR": {"name": "Casablanca Stock Exchange (BVC)", "note": "One of Africa's largest exchanges by market capitalization."},
    "OMN": {"name": "Muscat Stock Exchange (MSX)", "note": None},
    "PSE": {"name": "Palestine Exchange (PEX)", "note": None},
    "QAT": {"name": "Qatar Stock Exchange (QSE)", "note": None},
    "SAU": {"name": "Saudi Exchange (Tadawul)", "note": "Largest stock exchange in the Arab world by market capitalization."},
    "SYR": {"name": "Damascus Securities Exchange (DSE)", "note": None},
    "TUN": {"name": "Tunis Stock Exchange (BVMT)", "note": None},
    "ARE": {"name": "Dubai Financial Market (DFM) and Abu Dhabi Securities Exchange (ADX)", "note": "Two separate exchanges, one per emirate."},
    "YEM": {"name": "No functioning stock exchange", "note": None},
    "AFG": {"name": "No stock exchange", "note": None},
    "BGD": {"name": "Dhaka Stock Exchange (DSE)", "note": "Also has a smaller secondary exchange, the Chittagong Stock Exchange."},
    "BTN": {"name": "Royal Securities Exchange of Bhutan (RSEB)", "note": "Very small; few listed companies."},
    "IND": {"name": "BSE (Bombay Stock Exchange) and NSE (National Stock Exchange)", "note": "NSE is among the largest exchanges in the world by trading volume."},
    "MDV": {"name": "Maldives Stock Exchange (MSE)", "note": "Very small; few listed companies."},
    "NPL": {"name": "Nepal Stock Exchange (NEPSE)", "note": None},
    "PAK": {"name": "Pakistan Stock Exchange (PSX)", "note": None},
    "LKA": {"name": "Colombo Stock Exchange (CSE)", "note": None},
    "TUR": {"name": "Borsa Istanbul (BIST)", "note": None},
    "SDN": {"name": "Khartoum Stock Exchange (KSE)", "note": "Trading has been severely disrupted by the civil war since April 2023."},
    "SSD": {"name": "No stock exchange", "note": None},
    "ETH": {"name": "Ethiopian Securities Exchange (ESX)", "note": "Newly launched (January 2025) as part of Ethiopia's financial-sector liberalization; Ethiopia had no formal exchange before this."},
    "SOM": {"name": "No stock exchange", "note": None},
    "DJI": {"name": "No stock exchange", "note": None},
    "ERI": {"name": "No stock exchange", "note": None},
}

MAJOR_INDUSTRIES = {
    "DZA": "Oil & natural gas, petrochemicals, agriculture",
    "BHR": "Oil refining & petrochemicals, aluminum smelting, financial services",
    "EGY": "Tourism, Suez Canal transit revenue, natural gas, textiles, agriculture",
    "IRN": "Oil & gas, petrochemicals, automotive manufacturing, steel",
    "IRQ": "Oil & gas (dominant); limited other formal-sector industry",
    "ISR": "Technology & software, defense/aerospace, diamond cutting & polishing, pharmaceuticals",
    "JOR": "Phosphate & potash mining, pharmaceuticals, tourism, textiles",
    "KWT": "Oil & gas (dominant), petrochemicals, financial services",
    "LBN": "Banking & financial services (historically dominant, collapsed since the 2019-2020 crisis), tourism, agriculture",
    "LBY": "Oil & gas (dominant); limited other formal-sector industry",
    "MAR": "Automotive manufacturing, phosphate mining & fertilizers, textiles, tourism, agriculture",
    "OMN": "Oil & gas, petrochemicals, tourism, fishing",
    "PSE": "Agriculture, small-scale manufacturing, services — constrained by movement and access restrictions",
    "QAT": "Liquefied natural gas (LNG, dominant), petrochemicals, financial services",
    "SAU": "Oil & petrochemicals (dominant), mining, a growing tourism/entertainment sector under Vision 2030",
    "SYR": "Agriculture, oil (pre-war), textiles — industrial base heavily damaged by the civil war",
    "TUN": "Textiles & apparel, phosphate mining, tourism, automotive components",
    "ARE": "Oil & gas, logistics & re-export trade (Dubai), tourism, financial services, aviation",
    "YEM": "Oil & gas (pre-war), agriculture, fishing — formal economy severely disrupted by the civil war",
    "AFG": "Agriculture (including opium poppy cultivation historically), small-scale mining, carpets — minimal formal industrial base",
    "BGD": "Ready-made garments & textiles (dominant export sector), agriculture, pharmaceuticals",
    "BTN": "Hydropower (a major export, mostly to India), tourism, agriculture",
    "IND": "Information technology & IT services, pharmaceuticals, textiles, automotive, agriculture",
    "MDV": "Tourism (dominant), fishing",
    "NPL": "Agriculture, tourism, hydropower; a heavily remittance-dependent economy",
    "PAK": "Textiles & apparel, agriculture, cement; a heavily remittance-dependent economy",
    "LKA": "Tourism, textiles & apparel, tea exports, remittances",
    "TUR": "Automotive manufacturing, textiles, steel & metals, construction, tourism",
    "SDN": "Agriculture, gold mining, oil (reduced since South Sudan's 2011 secession) — economy severely disrupted by the ongoing civil war",
    "SSD": "Oil (dominant, near-total export reliance), subsistence agriculture",
    "ETH": "Agriculture (coffee is the leading export), textiles & apparel (growing), leather goods",
    "SOM": "Livestock exports, agriculture, remittances; minimal formal industrial base",
    "DJI": "Port & logistics services (a major regional transshipment/transit hub), foreign military basing revenue",
    "ERI": "Mining (gold, copper, potash), agriculture, fishing",
}
MAJOR_INDUSTRIES_SOURCE = (
    "Curated, real, well-established descriptive knowledge, not a live "
    "fetch -- paired in the app with two real, quantified series: sector "
    "value-added share of GDP (World Bank WDI, development_indicators.csv) "
    "and top export product categories by real UN Comtrade value "
    "(trade_commodities.csv). Not independently re-verified against a "
    "primary source in this session."
)

MAJOR_CITIES = {
    "DZA": [{"name": "Algiers", "role": "Capital"}, {"name": "Oran", "role": "Second-largest city"}],
    "BHR": [{"name": "Manama", "role": "Capital"}],
    "EGY": [{"name": "Cairo", "role": "Capital"}, {"name": "Alexandria", "role": "Second-largest city, principal Mediterranean port"}],
    "IRN": [{"name": "Tehran", "role": "Capital"}, {"name": "Isfahan", "role": "Major historic/industrial city"}],
    "IRQ": [{"name": "Baghdad", "role": "Capital"}, {"name": "Basra", "role": "Main port city, oil-export hub"}],
    "ISR": [{"name": "Jerusalem", "role": "Israel's declared capital; not internationally recognized as such by most states — most foreign embassies are in Tel Aviv"}, {"name": "Tel Aviv", "role": "Main economic and financial center"}],
    "JOR": [{"name": "Amman", "role": "Capital"}],
    "KWT": [{"name": "Kuwait City", "role": "Capital"}],
    "LBN": [{"name": "Beirut", "role": "Capital"}],
    "LBY": [{"name": "Tripoli", "role": "Capital, seat of the internationally-recognized government"}, {"name": "Benghazi", "role": "Largest city in the east, aligned with the rival administration"}],
    "MAR": [{"name": "Rabat", "role": "Capital"}, {"name": "Casablanca", "role": "Largest city and main economic center"}],
    "OMN": [{"name": "Muscat", "role": "Capital"}],
    "PSE": [{"name": "Ramallah", "role": "De facto administrative seat of the Palestinian Authority (West Bank)"}, {"name": "Gaza City", "role": "Largest city in Gaza"}],
    "QAT": [{"name": "Doha", "role": "Capital"}],
    "SAU": [{"name": "Riyadh", "role": "Capital"}, {"name": "Jeddah", "role": "Main commercial/port city on the Red Sea"}],
    "SYR": [{"name": "Damascus", "role": "Capital"}, {"name": "Aleppo", "role": "Largest city, historically Syria's main industrial center"}],
    "TUN": [{"name": "Tunis", "role": "Capital"}],
    "ARE": [{"name": "Abu Dhabi", "role": "Capital"}, {"name": "Dubai", "role": "Largest city and main economic/financial center"}],
    "YEM": [{"name": "Sana'a", "role": "Capital, under Houthi control"}, {"name": "Aden", "role": "Seat of the internationally-recognized government"}],
    "AFG": [{"name": "Kabul", "role": "Capital"}],
    "BGD": [{"name": "Dhaka", "role": "Capital"}, {"name": "Chattogram (Chittagong)", "role": "Main port city"}],
    "BTN": [{"name": "Thimphu", "role": "Capital"}],
    "IND": [{"name": "New Delhi", "role": "Capital"}, {"name": "Mumbai", "role": "Largest city and main financial center"}],
    "MDV": [{"name": "Malé", "role": "Capital"}],
    "NPL": [{"name": "Kathmandu", "role": "Capital"}],
    "PAK": [{"name": "Islamabad", "role": "Capital"}, {"name": "Karachi", "role": "Largest city and main economic/financial center"}],
    "LKA": [{"name": "Sri Jayawardenepura Kotte", "role": "Official capital"}, {"name": "Colombo", "role": "Commercial capital and largest city"}],
    "TUR": [{"name": "Ankara", "role": "Capital"}, {"name": "Istanbul", "role": "Largest city and main economic center"}],
    "SDN": [{"name": "Khartoum", "role": "Capital"}],
    "SSD": [{"name": "Juba", "role": "Capital"}],
    "ETH": [{"name": "Addis Ababa", "role": "Capital"}],
    "SOM": [{"name": "Mogadishu", "role": "Capital"}],
    "DJI": [{"name": "Djibouti City", "role": "Capital"}],
    "ERI": [{"name": "Asmara", "role": "Capital"}],
}
