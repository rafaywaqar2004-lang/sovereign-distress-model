"""
Real, dated sovereign distress events for the 34-economy panel this project
shares with the MENASA Risk Monitor (2010-2024). This is the outcome
variable (Y) the distress model predicts -- built entirely from named,
citable events, not an invented or proprietary default database.

Two tiers, kept separate rather than merged into one flag, because they are
different severities of the same underlying phenomenon:

TIER 2 -- SOVEREIGN_DEFAULTS: an actual default, restructuring, or missed
payment on external sovereign debt. The most severe, least ambiguous outcome.
Only two such events fall inside this 34-country, 2010-2024 panel -- a real
and important limitation, not a gap in research: formal sovereign default is
genuinely rare, which is exactly why a model needs a second, less severe but
more frequent outcome to have enough positive-class observations to fit at
all (see TIER 1 below).

  - Lebanon, March 2020: Lebanon's government announced it would not make a
    $1.2 billion Eurobond payment due March 9, 2020 -- the country's first
    sovereign default in its history. Widely reported at the time (Reuters,
    Bloomberg, AP) and confirmed in subsequent S&P/Moody's/Fitch rating
    actions (Lebanon carries "SD"/"C"/withdrawn ratings in this project's
    own CREDIT_RATINGS data as of this panel's build date).
  - Sri Lanka, April 2022: Sri Lanka's government formally announced a
    pre-emptive default and suspension of external debt payments on
    April 12, 2022, amid the country's worst economic crisis since
    independence. This event is already the subject of the MENASA Risk
    Monitor's own historical-validation case study (see that repo's
    app.py, VALIDATION_CASES).

TIER 1 -- IMF_PROGRAM_ENTRY: the calendar year a country's IMF Executive
Board formally APPROVED a new financial lending arrangement (EFF, ECF, or
SBA) -- a standard, widely used proxy for fiscal/balance-of-payments distress
in the sovereign-risk literature, since countries seek IMF lending precisely
when they cannot meet financing needs through normal market access.

Sourced directly from this project's own FINANCING_ARRANGEMENTS dataset in
overeign-risk-index/context_data.py, filtered to genuine, Board-approved
LENDING arrangements only. Deliberately EXCLUDED, and why:
  - Morocco's Flexible Credit Line (FCL): a PRECAUTIONARY facility reserved
    for countries with very strong fundamentals -- the opposite signal from
    distress, not a weaker version of it. Including it would misrepresent
    what the FCL actually means.
  - Lebanon's 2022 EFF: explicitly a "staff-level agreement... never
    presented to or approved by the IMF Executive Board" per this project's
    own sourced data -- not a real approved arrangement.
  - Tunisia's 2022 EFF: same reason -- "agreement in principle... never
    approved by IMF Executive Board."
  - GCC-funded support packages (Bahrain), bilateral central bank swap lines
    (Turkey), World Bank-only financing, and Article IV surveillance with no
    lending component: none of these are IMF lending arrangements.
  - Resilience and Sustainability Facility (RSF) tranches are listed as
    context alongside their companion EFF/ECF in the source data, not
    counted as a separate distress event in the same year (would
    double-count the same underlying program).

This is a screening-level proxy, not a certified default database -- stated
explicitly in this project's own methodology and limitations section, the
same discipline the MENASA Risk Monitor applies to its own data.
"""

SOVEREIGN_DEFAULTS = [
    {"country_code": "LBN", "year": 2020, "event": "First sovereign default in Lebanon's history -- missed $1.2bn Eurobond payment, announced March 7-9, 2020."},
    {"country_code": "LKA", "year": 2022, "event": "Pre-emptive default and suspension of external debt payments, announced April 12, 2022."},
]

# (country_code, year, program_type, approved_date_as_sourced)
IMF_PROGRAM_ENTRY = [
    ("BGD", 2023, "ECF/EFF blended", "January 30, 2023"),
    ("EGY", 2022, "EFF", "December 2022"),
    ("IRQ", 2016, "SBA", "July 7, 2016"),
    ("JOR", 2024, "EFF", "January 10, 2024"),
    ("LKA", 2023, "EFF", "March 20, 2023"),
    ("NPL", 2022, "ECF", "January 12, 2022"),
    ("PAK", 2013, "EFF", "September 2013"),
    ("PAK", 2019, "EFF", "July 2019"),
    ("PAK", 2023, "SBA", "July 12, 2023"),
    ("PAK", 2024, "EFF", "September 25, 2024"),
    ("SDN", 2021, "ECF", "2021, post arrears clearance June 2021"),
    ("SSD", 2023, "Staff-Monitored Program w/ Board Involvement", "February 16, 2023"),
    ("ETH", 2024, "ECF", "July 29, 2024"),
    ("SOM", 2023, "ECF", "December 19, 2023"),
    ("YEM", 2014, "ECF (lapsed)", "September 2, 2014"),
]


def build_distress_panel(country_years):
    """country_years: iterable of (country_code, year) tuples covering the
    full panel. Returns a list of dicts with a binary flag for each tier,
    ready to merge into the main analysis panel."""
    default_set = {(d["country_code"], d["year"]) for d in SOVEREIGN_DEFAULTS}
    program_set = {(c, y) for c, y, _, _ in IMF_PROGRAM_ENTRY}

    rows = []
    for code, year in country_years:
        rows.append({
            "country_code": code,
            "year": year,
            "sovereign_default": 1 if (code, year) in default_set else 0,
            "imf_program_entry": 1 if (code, year) in program_set else 0,
        })
    return rows
