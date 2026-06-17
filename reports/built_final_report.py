#!/usr/bin/env python3
"""
build_final_report.py
Bluestock Fintech – Mutual Fund Analytics Platform
Generates Final_Report.pdf
"""

from pathlib import Path
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

BASE = Path(__file__).resolve().parents[1]

OUTPUT = BASE / "reports" / "Final_Report.pdf"
CHARTS = BASE / "reports" / "charts"
DASHBOARD = BASE / "dashboard"

styles = getSampleStyleSheet()

TITLE = styles["Title"]
H1 = styles["Heading1"]
BODY = styles["BodyText"]

from reportlab.lib import utils

def add_image(story, path, max_width=500, max_height=650):
    if not Path(path).exists():
        return

    img = utils.ImageReader(str(path))
    iw, ih = img.getSize()

    scale = min(
        max_width / iw,
        max_height / ih
    )

    width = iw * scale
    height = ih * scale

    story.append(Image(str(path), width=width, height=height))
    story.append(Spacer(1, 12))


def build_cover(story):
    story.append(Spacer(1, 120))
    story.append(
        Paragraph(
            "BLUESTOCK FINTECH<br/>"
            "End-to-End Data Engineering · ETL Pipeline · "
            "Interactive Dashboard<br/><br/>"
            "Mutual Fund Analytics Platform",
            TITLE,
        )
    )

    story.append(Spacer(1, 30))

    story.append(
        Paragraph(
            """
            <b>Industry AUM:</b> ₹81.1L Cr<br/>
            <b>Monthly SIP ATH:</b> ₹31,002 Cr<br/>
            <b>Total Folios:</b> 26.12 Cr<br/>
            <b>Active Schemes:</b> 1,908<br/><br/>

            Prepared by: Data Analyst — Bluestock Fintech Capstone<br/>
            Technologies: Python · SQL · Power BI · Pandas · Matplotlib · Seaborn · Plotly
            """,
            BODY,
        )
    )

    story.append(PageBreak())


def build_exec_summary(story):
    story.append(Paragraph("1. Executive Summary", H1))

    story.append(
        Paragraph(
            """
            This report presents a comprehensive end-to-end Mutual Fund
            Analytics Platform built for Bluestock Fintech.
            The platform ingests, transforms, stores, analyses and visualises
            mutual fund data from AMFI India, mfapi.in, NSE and BSE.
            """,
            BODY,
        )
    )

    data = [
        ["Day", "Focus", "Key Deliverable", "Status"],
        ["1", "Data Ingestion + ETL", "data_ingestion.py", "✓"],
        ["2", "Cleaning + SQL DB", "bluestock_mf.db", "✓"],
        ["3", "EDA Analysis", "EDA_Analysis.ipynb", "✓"],
        ["4", "Performance Analytics", "fund_scorecard.csv", "✓"],
        ["5", "Dashboard", "Dashboard.pdf", "✓"],
        ["6", "Advanced Analytics", "var_cvar_report.csv", "✓"],
        ["7", "Report + Presentation", "Final_Report.pdf", "✓"],
    ]

    tbl = Table(data, colWidths=[50, 120, 220, 60])
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b2b52")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ])
    )

    story.append(tbl)
    story.append(PageBreak())


def build_data_sources(story):
    story.append(Paragraph("2. Data Sources & ETL Architecture", H1))

    story.append(
        Paragraph(
            """
            Data originates from AMFI India, mfapi.in REST API,
            NSE and BSE public datasets.
            ETL flow:
            Extract → Transform → Load → Analyse → Visualise
            """,
            BODY,
        )
    )

    datasets = [
        ["fund_master.csv", "40"],
        ["nav_history.csv", "46,000"],
        ["aum_data.csv", "160"],
        ["sip_inflows_cleaned.csv", "48"],
        ["05_category_inflows.csv", "156"],
        ["06_industry_folio_count.csv", "30"],
        ["07_scheme_performance.csv", "40"],
        ["08_investor_transactions.csv", "55,264"],
        ["portfolio_holdings.csv", "541"],
        ["benchmark_index.csv", "6,900"],
    ]

    tbl = Table([["Dataset", "Rows"]] + datasets)
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b2b52")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ])
    )

    story.append(tbl)
    story.append(PageBreak())


def build_eda(story):
    story.append(Paragraph("3. Exploratory Data Analysis — Key Findings", H1))

    for img in sorted(CHARTS.glob("chart_0*.png")):
        add_image(story, img)

    story.append(PageBreak())


def build_performance(story):
    story.append(Paragraph("4. Fund Performance Analytics", H1))

    for img in sorted(CHARTS.glob("chart_perf_*.png")):
        add_image(story, img)

    story.append(PageBreak())


def build_dashboard(story):
    story.append(Paragraph("5. Interactive Dashboard — 4 Pages", H1))

    for img in sorted(DASHBOARD.glob("Dashboard_Page*.png")):
        add_image(story, img)

    story.append(PageBreak())


def build_advanced(story):
    story.append(Paragraph("6. Advanced Analytics", H1))

    for img in sorted(CHARTS.glob("chart_adv_*.png")):
        add_image(story, img)

    story.append(PageBreak())


def build_conclusion(story):
    story.append(Paragraph("7. Recommendations & Conclusions", H1))

    story.append(
        Paragraph(
            """
            Conservative: Liquid and Corporate Bond Funds<br/>
            Moderate: Hybrid and Balanced Advantage Funds<br/>
            Aggressive: Bluechip, Large Cap and Small Cap Funds
            """,
            BODY,
        )
    )

    story.append(PageBreak())


def build_appendix(story):
    story.append(Paragraph("8. Appendix — Deliverables Checklist", H1))

    rows = [
        ["D1", "ETL Pipeline Script"],
        ["D2", "SQLite Database"],
        ["D3", "EDA Notebook"],
        ["D4", "Performance Metrics"],
        ["D5", "Interactive Dashboard"],
        ["D6", "Advanced Analytics"],
        ["D7", "Final Report + Slides"],
    ]

    tbl = Table([["#", "Deliverable"]] + rows)
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b2b52")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ])
    )

    story.append(tbl)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(OUTPUT))
    story = []

    build_cover(story)
    build_exec_summary(story)
    build_data_sources(story)
    build_eda(story)
    build_performance(story)
    build_dashboard(story)
    build_advanced(story)
    build_conclusion(story)
    build_appendix(story)

    doc.build(story)

    print(f"✓ Report generated: {OUTPUT}")


if __name__ == "__main__":
    main()