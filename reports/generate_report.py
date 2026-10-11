"""Build the three-page technical report for the Aiqon take-home assignment."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Add consistent headers and page counts after the document is laid out."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            if self._pageNumber > 1:
                self.drawString(54, 750, "RouteWise AI | Aiqon AI Internship")
                self.setStrokeColor(colors.HexColor("#CBD5E1"))
                self.line(54, 742, 558, 742)
            self.drawString(54, 36, "SYNTHETIC PLANNING MODEL - NOT A CARRIER QUOTE")
            self.drawRightString(558, 36, f"Page {self._pageNumber} of {page_count}")
            self.restoreState()
            super().showPage()
        super().save()


def build_pdf(filename: str = "reports/technical_report.pdf"):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=58,
        bottomMargin=54,
    )
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle", parent=base["Title"], fontName="Helvetica-Bold",
        fontSize=19, leading=23, textColor=colors.HexColor("#0F172A"),
        alignment=0, spaceAfter=5,
    )
    subtitle = ParagraphStyle(
        "ReportSubtitle", parent=base["Normal"], fontSize=9.5, leading=13,
        textColor=colors.HexColor("#475569"), spaceAfter=8,
    )
    heading = ParagraphStyle(
        "ReportHeading", parent=base["Heading2"], fontName="Helvetica-Bold",
        fontSize=11.5, leading=14, textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=6, spaceAfter=3,
    )
    body = ParagraphStyle(
        "ReportBody", parent=base["BodyText"], fontSize=8.3, leading=10.6,
        textColor=colors.HexColor("#334155"), spaceAfter=4,
    )
    small = ParagraphStyle(
        "ReportSmall", parent=body, fontSize=7.3, leading=9,
        spaceAfter=0,
    )
    formula = ParagraphStyle(
        "ReportFormula", parent=body, fontName="Courier",
        fontSize=8, leading=11, borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5, borderPadding=5,
        backColor=colors.HexColor("#F1F5F9"), spaceBefore=2, spaceAfter=5,
    )

    def p(text, style=body):
        return Paragraph(text, style)

    def data_table(rows, widths):
        table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    story = [
        p("RouteWise AI: Shipment Route Decision Support", title),
        p("<b>Aiqon AI Internship Take-Home Assignment</b> | Cost, transit time and risk", subtitle),
        p("1. Problem and decision approach", heading),
        p(
            "RouteWise AI evaluates four candidate services for a shipment and recommends an option "
            "under operator-selected priorities. Its purpose is a transparent decision-support demo, "
            "not a live booking engine. The same Python optimizer serves a React/FastAPI interface "
            "and an optional Streamlit dashboard."
        ),
        p("A route is scored relative to the other options for that shipment. Freight cost and transit "
          "time are min-max normalized; composite risk first combines the model's delay, congestion "
          "and geopolitical indicators. The weighted sum is minimized:"),
        p(
            "R = 0.40 x P(delay) + 0.30 x congestion/100 + 0.30 x geopolitical/100<br/>"
            "S = w_cost x C_norm + w_time x T_norm + w_risk x R_norm; weights sum to 1.",
            formula,
        ),
        p(
            "The default profile is 40/30/30. Cost-focused (70/15/15), time-critical "
            "(15/70/15) and risk-averse (15/15/70) profiles support sensitivity analysis. "
            "Hard budget, transit and risk limits mark routes infeasible; infeasible choices cannot "
            "beat feasible ones. If all options fail, the fallback chooses the route with the fewest "
            "failed limits, then the lowest weighted score. Pareto dominance is flagged for review; "
            "routes are not removed."
        ),
        p("2. Data, assumptions and price model", heading),
        p(
            "The reproducible synthetic benchmark contains 30 origin-destination lanes: 18 domestic "
            "India lanes and 12 international lanes. Each lane has four choices (120 rows total). "
            "Domestic options are rail parcel, surface truck, express road and priority road/air. "
            "International options are standard ocean, express ocean, resilient ocean and air. "
            "Cargo labels distinguish indicative carton/sample profiles; they do not currently change "
            "the pricing formula or optimizer weights."
        ),
        p(
            "Prices are planning estimates, not observed quotes. Domestic estimates model a 10 kg "
            "carton using a minimum handling charge plus a distance charge in INR. International "
            "estimates model a 15 kg / 0.1 CBM sample using a minimum plus distance in USD. "
            "Seeded variation is +/-6% on cost, +/-7% on domestic transit time, and +/-6% on "
            "international transit time. The display conversion is fixed "
            "at INR 84 per USD. Customs, duties, taxes, pickup surcharges, dimensional-weight rules "
            "and live carrier availability are not modeled."
        ),
        data_table([
            [p("<b>Benchmark example</b>", small), p("<b>Planning estimate</b>", small), p("<b>Model behavior</b>", small)],
            [p("SHP-001 Hyderabad-Warangal (~155 km)", small), p("INR 219-780 across four options", small), p("Rail is cheapest; priority courier is fastest", small)],
            [p("SHP-004 Mumbai-Delhi (~1,410 km)", small), p("INR 1,169-3,268 across four options", small), p("Distance and service tier drive modeled price", small)],
            [p("SHP-019 Shanghai-Rotterdam (~19,800 km)", small), p("$213 standard ocean; $463 air", small), p("Small consolidated sample; not container freight", small)],
        ], [150, 180, 184]),
        PageBreak(),
        p("RouteWise AI | Design and evaluation", title),
        p("3. Ranking, uncertainty and explainability", heading),
        p(
            "For each candidate, the optimizer computes a composite risk score from the supplied "
            "indicators, tests optional hard limits against freight cost, transit duration and "
            "composite risk, then min-max normalizes cost, time and risk across the candidate set. "
            "The weighted sum ranks feasible options first. The stored expected-delay and "
            "expected-landed-cost fields use a simple illustrative delay allowance; they are "
            "diagnostic only: neither changes the route score nor the budget-feasibility check. "
            "Consequently, the reported recommendation minimizes weighted freight/time/risk, not "
            "a validated total-cost-of-ownership measure."
        ),
        p(
            "Delay probability and risk values are deterministic synthetic inputs, not calibrated "
            "forecast distributions. The weighted risk index is a relative planning signal, not a "
            "probability of loss. Cost and time normalization is per shipment, so a score is "
            "meaningful within that lane; it is not a cross-lane service-level rating."
        ),
        p(
            "The deterministic explainer cites the selected route and runner-up trade-offs, and "
            "reports feasibility violations and Pareto flags. The React/API path uses this offline "
            "explanation. An optional Gemini explanation/Q&amp;A path is available in the Streamlit "
            "interface when configured; the recommendation itself remains optimizer-controlled."
        ),
        p("4. Evaluation and observed behavior", heading),
        p(
            "Evaluation is currently a set of reproducible unit and integration checks, not a "
            "claim of real-world predictive accuracy. The 19 passing tests cover dataset shape and "
            "ranges, price examples, weight validation, single-objective preference, hard limits, "
            "all-infeasible fallback, Pareto dominance, identical-metric stability, sensitivity "
            "output, explanation content and schematic-map behavior. No carrier quote comparison, "
            "historical-delay backtest or out-of-sample recommendation study has been performed."
        ),
        data_table([
            [p("<b>Shipment</b>", small), p("<b>Balanced (40/30/30)</b>", small), p("<b>Cost-focused</b>", small), p("<b>Time / risk profiles</b>", small)],
            [p("SHP-001 Hyderabad-Warangal", small), p("Rail, $2.61; 0.178 d", small), p("Rail, $2.61; 0.178 d", small), p("Priority road courier, $9.29; 0.103 d", small)],
            [p("SHP-019 Shanghai-Rotterdam", small), p("Resilient ocean, $239.65; 28.6 d", small), p("Resilient ocean, $239.65; 28.6 d", small), p("Air, $463.17; 4 d", small)],
        ], [140, 130, 130, 114]),
        p(
            "These examples are the current seeded benchmark output. In this data, the risk-averse "
            "profile also selects the priority service for both example lanes; that is a property of "
            "the assigned risk indicators, not evidence that air is generally the least risky real "
            "service. Synthetic inputs should not be interpreted as carrier performance evidence."
        ),
        PageBreak(),
        p("5. Limitations and next steps", heading),
        p(
            "The React and Streamlit maps show known endpoints and schematic curves to distinguish "
            "alternatives; they do not have provider route geometries or live traffic, and unknown "
            "endpoint coordinates are not guessed. The natural-language parser uses a fixed city "
            "alias list; its deterministic distance fallback for unknown cities is not geocoding. "
            "International distances, "
            "transit times and risk scores are lane archetype estimates. Domestic modeled express "
            "times are idealized. Unknown city coordinates are left unmapped rather than replaced "
            "with invented locations."
        ),
        p(
            "For operational use, replace fixed formulas and risk archetypes with carrier quotes "
            "and timestamped shipment/port data; model package weight, dimensions, service area, "
            "fuel and surcharges; calibrate delay distributions; use expected landed cost in "
            "scoring/constraints when customer delay costs are known; and validate recommendations "
            "against historical or expert-labelled decisions. Add confidence intervals and a "
            "human override/audit trail before deployment."
        ),
        p("Deliverables", heading),
        p(
            "The repository includes the source, deterministic API, React and Streamlit demos, "
            "generated benchmark CSV, tests, setup instructions and this reproducible three-page "
            "PDF report. Start the API with <font name='Courier'>python -m uvicorn api:app "
            "--reload --port 8000</font>; run the frontend from <font name='Courier'>frontend</font> "
            "with <font name='Courier'>npm run dev</font>. See README.md for the complete setup."
        ),
    ]

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Technical report generated: {filename}")


if __name__ == "__main__":
    build_pdf()
