"""
Real government type / political structure for this project's 34 tracked
countries -- same epistemic category as trade_infrastructure.py's trade
blocs and ports: well-established, real, static reference facts (not a
number that needs a live API), NOT independently re-verified against a
primary source in this session. Standard classification terms (the same
ones used by outlets like the CIA World Factbook, Freedom House, or the
V-Dem project), not this project's own judgment.

Several of these (Syria, Libya, Yemen, Sudan, Afghanistan) are genuinely
fluid, contested, or unrecognized situations, not stable, settled facts --
described as such below rather than flattened into a clean label the
real situation doesn't have. This is a snapshot as of the time this file
was written, not a live-tracked feed.
"""

GOVERNMENT_STRUCTURE = {
    "DZA": {"type": "Semi-presidential republic", "note": "Executive power concentrated in the presidency; a weaker, presidentially-aligned parliament."},
    "BHR": {"type": "Constitutional monarchy", "note": "Hereditary King as head of state; an elected lower house (Council of Representatives) alongside a royally-appointed upper house (Shura Council)."},
    "EGY": {"type": "Presidential republic", "note": "Strong executive presidency; parliament and judiciary have limited independent checking power in practice."},
    "IRN": {"type": "Theocratic republic", "note": "An elected president and parliament operate under the ultimate authority of an unelected Supreme Leader and clerical oversight bodies (Guardian Council)."},
    "IRQ": {"type": "Federal parliamentary republic", "note": "President is a largely ceremonial head of state; executive power sits with a Prime Minister drawn from parliament, under a post-2003 sectarian/ethnic power-sharing convention."},
    "ISR": {"type": "Parliamentary republic", "note": "No formal written constitution (governed by a set of Basic Laws); Prime Minister leads the executive, drawn from the Knesset."},
    "JOR": {"type": "Constitutional monarchy", "note": "King holds substantial executive authority, including appointing the Prime Minister; an elected lower house of parliament exists alongside a royally-appointed upper house."},
    "KWT": {"type": "Constitutional monarchy (Emirate)", "note": "Hereditary Emir appoints the Prime Minister; an elected National Assembly has real legislative and oversight power, unusually strong for the Gulf."},
    "LBN": {"type": "Parliamentary republic", "note": "Confessional power-sharing system: the presidency, premiership, and speakership are constitutionally reserved for specific religious communities (Maronite Christian, Sunni Muslim, Shia Muslim respectively)."},
    "LBY": {"type": "Contested / no unified government", "note": "Divided since 2014 between rival administrations (internationally-recognized Government of National Unity in Tripoli vs. an eastern-based administration aligned with the Libyan National Army) -- a fluid, unsettled situation, not a stable classification."},
    "MAR": {"type": "Constitutional monarchy", "note": "King retains substantial executive, religious, and military authority; an elected parliament and Prime Minister handle day-to-day governance."},
    "OMN": {"type": "Absolute monarchy (Sultanate)", "note": "Sultan holds full executive, legislative, and judicial authority; an elected Consultative Assembly has advisory, not binding, power."},
    "PSE": {"type": "Semi-presidential system (Palestinian Authority)", "note": "Governance is split in practice: the PA (Fatah-led) administers parts of the West Bank, while Hamas has governed Gaza separately since 2007 -- no single unified government in practice."},
    "QAT": {"type": "Absolute monarchy (Emirate)", "note": "Hereditary Emir holds full executive authority; an appointed/partly-elected Shura Council has limited legislative power."},
    "SAU": {"type": "Absolute monarchy", "note": "King (also Prime Minister) holds full executive authority; no elected national legislature -- the Shura Council is appointed and advisory only."},
    "SYR": {"type": "Transitional government", "note": "Following the fall of the Assad regime in December 2024, an interim transitional authority has been forming a new government structure -- an actively evolving situation, not a settled classification."},
    "TUN": {"type": "Presidential republic", "note": "Power was substantially concentrated in the presidency following the 2022 constitutional overhaul, reversing much of Tunisia's post-2011 parliamentary system."},
    "ARE": {"type": "Federal absolute monarchy", "note": "A federation of 7 emirates, each ruled by a hereditary Emir; the Abu Dhabi and Dubai rulers hold outsized federal influence. No direct national elections for the presidency."},
    "YEM": {"type": "Contested / fragmented", "note": "Civil war since 2014 between the internationally-recognized government and the Houthi movement, which controls the capital Sana'a and most of the populous north -- a fluid, unsettled situation."},
    "AFG": {"type": "De facto Islamic Emirate (Taliban)", "note": "Taliban authorities have governed since August 2021; not formally recognized as the legitimate government by most UN member states."},
    "BGD": {"type": "Parliamentary republic", "note": "Prime Minister leads the executive, drawn from an elected unicameral parliament (Jatiya Sangsad); President is a largely ceremonial head of state."},
    "BTN": {"type": "Constitutional monarchy", "note": "Transitioned to a parliamentary democracy under King Jigme Khesar Namgyel Wangchuck in 2008; the monarch retains significant informal influence."},
    "IND": {"type": "Federal parliamentary republic", "note": "Prime Minister leads the executive, drawn from an elected bicameral parliament; President is a largely ceremonial head of state."},
    "MDV": {"type": "Presidential republic", "note": "Directly-elected President serves as both head of state and government, alongside an elected unicameral legislature (People's Majlis)."},
    "NPL": {"type": "Federal parliamentary republic", "note": "Became a federal republic in 2008 after the abolition of the monarchy; Prime Minister leads the executive."},
    "PAK": {"type": "Federal parliamentary republic", "note": "Prime Minister leads the executive, drawn from an elected bicameral parliament; the military has historically wielded significant informal political influence."},
    "LKA": {"type": "Presidential republic", "note": "Directly-elected executive President operates alongside a Prime Minister and elected unicameral parliament."},
    "TUR": {"type": "Presidential republic", "note": "Executive presidential system since the 2017 constitutional referendum abolished the office of Prime Minister and concentrated executive authority in the presidency."},
    "SDN": {"type": "Civil war / no stable central authority", "note": "Fighting since April 2023 between the Sudanese Armed Forces and the paramilitary Rapid Support Forces has left no single functioning national government in practice."},
    "SSD": {"type": "Presidential republic (transitional)", "note": "Operating under a transitional government of national unity formed under the 2018/2020 peace agreement that ended the 2013-2018 civil war; elections have been repeatedly postponed."},
    "ETH": {"type": "Federal parliamentary republic", "note": "Prime Minister leads the executive; a federation of ethnically-based regional states, several of which (notably Tigray, Amhara) have seen serious internal conflict in recent years."},
    "SOM": {"type": "Federal parliamentary republic", "note": "Central authority remains fragile; federal member states retain substantial autonomy, and al-Shabaab controls or contests parts of the country outside government control."},
    "DJI": {"type": "Presidential republic", "note": "Dominant-party system; the same president/party coalition has held power continuously since independence in 1977."},
    "ERI": {"type": "One-party presidential republic", "note": "No constitution has ever been implemented and no national elections have been held since independence in 1993; widely regarded as one of the world's most closed political systems."},
}
GOVERNMENT_STRUCTURE_SOURCE = (
    "Real, well-established political-science classification (the same "
    "category of fact used by outlets like the CIA World Factbook, Freedom "
    "House, or the V-Dem project) -- not independently re-verified against "
    "a primary source in this session, and a snapshot as of when this file "
    "was written rather than a live-tracked feed. Several entries (Syria, "
    "Libya, Yemen, Sudan, Afghanistan) describe genuinely fluid or "
    "contested situations, flagged as such rather than forced into a "
    "clean label."
)
