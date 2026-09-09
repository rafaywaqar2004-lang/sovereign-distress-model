"""
Real, precisely-dated geopolitical shock events for the event-study design
this module runs. Each has a specific date (not a multi-year span), since
an event study needs a real "event day" to window around -- reusing the
same real events already established across this project and MENASA
(the distress defaults, the Syria/Sri Lanka/Afghanistan/Egypt/Pakistan
crisis cases from MENASA's own historical-validation section), plus each
event's precise date sourced independently where MENASA's own case only
carried a calendar year.
"""

SHOCK_EVENTS = [
    {
        "country_code": "LBN", "event_date": "2020-03-09",
        "label": "Lebanon sovereign default",
        "source": "Government announcement of non-payment on a $1.2bn Eurobond due Mar 9, 2020 -- widely reported (Reuters, Bloomberg, AP) at the time.",
    },
    {
        "country_code": "LKA", "event_date": "2022-04-12",
        "label": "Sri Lanka pre-emptive default",
        "source": "Formal announcement of suspension of external debt payments, April 12, 2022 -- same event as MENASA's own LKA validation case.",
    },
    {
        "country_code": "AFG", "event_date": "2021-08-15",
        "label": "Fall of Kabul / Taliban takeover",
        "source": "Widely documented date the Taliban entered Kabul -- same event as MENASA's own AFG validation case, dated precisely here.",
    },
    {
        "country_code": "EGY", "event_date": "2022-03-21",
        "label": "Egyptian pound devaluation",
        "source": "Central Bank of Egypt allowed a sharp EGP depreciation as part of IMF-linked reforms, March 2022 -- same episode as MENASA's own EGY validation case.",
    },
    {
        "country_code": "PAK", "event_date": "2023-07-12",
        "label": "Pakistan Stand-By Arrangement approved",
        "source": "IMF Executive Board approval date, per this project's own distress_events.py / MENASA's FINANCING_ARRANGEMENTS.",
    },
]

# Syria's civil war escalation (2011->2012, MENASA's own validation case) was
# originally included here at an approximate 2012-01-01 marker. Removed after
# the first real GDELT fetch run confirmed it structurally cannot work: the
# GDELT 2.0 Doc API only indexes data from FEBRUARY 2015 onward. A January
# 2012 event is entirely outside that coverage window -- the fetch script
# correctly returned zero data for it (not a bug, a real API limitation), and
# no amount of retrying changes that. Kept here as a documented exclusion
# rather than silently dropped, since it's a genuine scope constraint worth
# knowing about for any future event added to SHOCK_EVENTS: GDELT-based event
# studies in this module are only valid for events from 2015 onward.
SYRIA_EXCLUDED = {
    "country_code": "SYR", "event_date": "2012-01-01",
    "label": "Syria civil war escalation (approximate marker)",
    "reason": "Predates GDELT 2.0 Doc API's coverage window (data starts February 2015). Confirmed by a real fetch attempt returning zero data on all retries, not assumed.",
}
