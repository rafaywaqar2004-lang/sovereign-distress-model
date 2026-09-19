"""
Generates a downloadable one-page-plus country risk brief as a PDF for the
EM Macro & Geopolitical Risk Engine, assembled from the exact same real,
already-computed numbers shown in the Country Risk tab's "Analyst briefing"
card (model-implied probability, risk attribution, transmission channels,
credit-rating benchmark, real distress events) -- nothing here is a second,
separately-invented narrative.
"""
import re
from datetime import datetime, timezone
from fpdf import FPDF

TEAL = (51, 182, 175)      # ACCENT
CORAL = (224, 121, 62)     # ACCENT2
TEXT_DARK = (25, 30, 29)
TEXT_MUTED = (100, 110, 108)
BAD = (200, 60, 60)
GOOD = (30, 140, 100)

_UNICODE_REPLACEMENTS = {
    "—": "-", "–": "-",
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "…": "...",
    "→": "->", "←": "<-",
    "↑": "^", "↓": "v",
    "▲": "^", "▼": "v",
    "•": "-", "·": "-",
    "±": "+/-", "ρ": "rho",
}


def sanitize_text(text):
    """Replaces Unicode characters outside Latin-1 (the core PDF font's
    range) with ASCII-safe equivalents, so the PDF never fails to render."""
    if text is None:
        return ""
    text = str(text)
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _strip_html(text):
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    return sanitize_text(text)


class CountryBriefPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*TEXT_MUTED)
        self.cell(0, 8, "EM Macro & Geopolitical Risk Engine - Country Risk Brief", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*TEXT_MUTED)
        self.cell(
            0, 10,
            "Screening-level research tool, not investment advice or a production early-warning system. "
            "See in-app Methodology & Validation tab for full model limitations.",
            align="C",
        )

    def section_title(self, text, x_start=None):
        x_start = self.l_margin if x_start is None else x_start
        self.set_xy(x_start, self.get_y())
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*TEAL)
        self.cell(0, 8, sanitize_text(text), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*CORAL)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(x_start, y, x_start + 30, y)
        self.ln(4)
        self.set_x(x_start)

    def body_text(self, text, size=9.5):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*TEXT_DARK)
        self.multi_cell(0, 5.2, sanitize_text(text))
        self.ln(1)

    def simple_table(self, rows, col_widths=None, x_start=None):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXT_DARK)
        if col_widths is None:
            col_widths = [55, 125]
        x_start = self.l_margin if x_start is None else x_start
        for row in rows:
            y_before = self.get_y()
            self.set_xy(x_start, y_before)
            self.set_font("Helvetica", "B", 9)
            self.multi_cell(col_widths[0], 5, sanitize_text(str(row[0])), new_x="RIGHT", new_y="TOP")
            y_after_label = self.get_y()
            self.set_xy(x_start + col_widths[0], y_before)
            self.set_font("Helvetica", "", 9)
            self.multi_cell(col_widths[1], 5, sanitize_text(str(row[1])), new_x="LMARGIN", new_y="NEXT")
            y_after_value = self.get_y()
            self.set_xy(x_start, max(y_after_label, y_after_value))
        self.ln(2)


def generate_country_pdf(
    country_name, country_code, latest_year,
    predicted_prob, avg_prob,
    top_driver, bottom_driver, contrib_rows,
    n_events, confidence_label,
    chan_year=None, trade_openness=None, reserves_months=None,
    current_account=None, fdi_pct_gdp=None,
    sp_rating=None, rating_rank=None, rating_total=None,
    events=None,
    total_countries=34,
):
    """
    Every argument is a value already computed live in app.py's Country
    Risk tab (from the fitted model / real panel data) for the selected
    country and its latest complete-case panel year -- this function only
    formats them into a PDF, it does not compute or invent anything new.
    """
    pdf = CountryBriefPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ---- Masthead ----
    pdf.set_font("Helvetica", "B", 19)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 11, "Sovereign Distress Risk Brief", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*CORAL)
    pdf.cell(0, 9, sanitize_text(f"{country_name} ({country_code})"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TEXT_MUTED)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pdf.cell(
        0, 6,
        sanitize_text(f"Generated {generated} | Panel year {latest_year} | EM Macro & Geopolitical Risk Engine"),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    # ---- Model-implied probability + benchmark, side by side ----
    summary_rows = [
        ["Model-implied probability", f"{predicted_prob:.1%}"],
        ["Sample-average country", f"{avg_prob:.1%}"],
        ["Panel year", str(latest_year)],
        ["Model confidence", confidence_label],
    ]
    col_width = (pdf.w - pdf.l_margin - pdf.r_margin) / 2 - 3
    left_x = pdf.l_margin
    right_x = pdf.l_margin + col_width + 6
    top_y = pdf.get_y()

    pdf.set_xy(left_x, top_y)
    pdf.section_title("Distress Probability", x_start=left_x)
    pdf.simple_table(summary_rows, col_widths=[48, col_width - 48], x_start=left_x)
    left_bottom_y = pdf.get_y()

    if sp_rating:
        pdf.set_xy(right_x, top_y)
        pdf.section_title("Credit Rating Benchmark", x_start=right_x)
        bench_rows = [["Real S&P rating", sp_rating]]
        if rating_rank is not None:
            bench_rows.append(["Model rank", f"{rating_rank} of {rating_total} rated countries"])
        pdf.simple_table(bench_rows, col_widths=[38, col_width - 38], x_start=right_x)
        right_bottom_y = pdf.get_y()
    else:
        right_bottom_y = top_y
    pdf.set_xy(pdf.l_margin, max(left_bottom_y, right_bottom_y))

    # ---- Risk attribution ----
    pdf.section_title("Risk Attribution")
    pdf.body_text(
        f"Top driver pushing risk up: {top_driver[0]} (contribution {top_driver[1]:+.2f} log-odds). "
        f"Top driver pushing risk down: {bottom_driver[0]} (contribution {bottom_driver[1]:+.2f} log-odds). "
        f"Decomposition of the fitted model's own log-odds for this country-year against the sample-average "
        f"country as a reference point -- not a separate causal claim."
    )
    if contrib_rows:
        pdf.simple_table(
            [[label, f"{value:+.2f} log-odds"] for label, value in contrib_rows],
            col_widths=[70, 110],
        )

    # ---- Transmission channels ----
    if chan_year is not None:
        pdf.section_title("Economic Transmission Channels")
        chan_rows = []
        if trade_openness is not None:
            chan_rows.append(["Trade openness (% GDP)", f"{trade_openness:.0f}%"])
        if fdi_pct_gdp is not None:
            chan_rows.append(["Net FDI inflows (% GDP)", f"{fdi_pct_gdp:.1f}%"])
        if reserves_months is not None:
            chan_rows.append(["Reserves cover", f"{reserves_months:.1f} months of imports"])
        if current_account is not None:
            chan_rows.append(["Current account (% GDP)", f"{current_account:.1f}%"])
        if chan_rows:
            pdf.simple_table(chan_rows)
            pdf.body_text(f"Real {chan_year} values from World Bank WDI.", size=8.5)

    # ---- Real distress events ----
    if events:
        pdf.section_title("Real Distress Events")
        for year, event_type, detail in sorted(events, key=lambda e: e[0], reverse=True):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*CORAL)
            pdf.write(5, f"{year} ({event_type}): ")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*TEXT_DARK)
            pdf.write(5, sanitize_text(detail))
            pdf.ln(7)
    else:
        pdf.section_title("Real Distress Events")
        pdf.body_text(f"No real sovereign_default or imf_program_entry event recorded for {country_name} in this panel (2010-2024).")

    return bytes(pdf.output())
