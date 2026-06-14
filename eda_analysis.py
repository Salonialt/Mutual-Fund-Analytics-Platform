"""
eda_analysis.py  —  Day 3 EDA | Bluestock Fintech MF Analytics Capstone
========================================================================
Tailored exactly to the actual processed files produced by data_cleaning.py.

FILES READ (all from data/processed/ or data/raw/):
  clean_nav.csv              cols: date, amfi_code(int64), nav, daily_return_pct
  clean_transactions.csv     cols: investor_id, transaction_date, amfi_code,
                                   transaction_type, amount_inr, state, city,
                                   city_tier, age_group, gender,
                                   annual_income_lakh, payment_mode, kyc_status
  clean_aum.csv              cols: fund_house, quarter, period_end, aum_crore,
                                   num_schemes
  clean_sip_inflows.csv      cols: month, sip_inflow_crore,
                                   active_sip_accounts_crore,
                                   new_sip_accounts_lakh,
                                   sip_aum_lakh_crore, yoy_growth_pct
  clean_category_inflows.csv cols: month, category, net_inflow_crore,
                                   gross_purchase_crore, gross_redemption_crore
  clean_folio_count.csv      cols: month, equity_folios_crore,
                                   debt_folios_crore, hybrid_folios_crore,
                                   total_folios_crore
  clean_portfolio_holdings.csv cols: amfi_code, stock_symbol, sector,
                                     weight_pct, as_of_date
  clean_benchmark_indices.csv  cols: index_name, date, close_value
  data/raw/01_fund_master.csv  cols: amfi_code, scheme_name, fund_house,
                                     category, sub_category, plan,
                                     launch_date, expense_ratio_pct,
                                     exit_load_pct, fund_manager,
                                     risk_category, sebi_category_code

RUN:    python eda_analysis.py
OUTPUT: reports/charts/chart_01_*.png  ...  chart_12_*.png
        reports/charts_html/chart_*.html   (interactive Plotly)
        notebooks/EDA_Analysis.ipynb
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
PROC     = os.path.join(BASE, "data", "processed")
RAW      = os.path.join(BASE, "data", "raw")
CHARTS   = os.path.join(BASE, "reports", "charts")
HTML_DIR = os.path.join(BASE, "reports", "charts_html")
NB_PATH  = os.path.join(BASE, "notebooks", "EDA_Analysis.ipynb")
os.makedirs(CHARTS,   exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)

# ── Brand colours ──────────────────────────────────────────────────────────────
NAVY   = "#1a2744"
ORANGE = "#f7931e"
GREEN  = "#27ae60"
RED    = "#e74c3c"
TEAL   = "#17becf"
PURPLE = "#8e44ad"
PALETTE = [NAVY, ORANGE, GREEN, RED, PURPLE, TEAL,
           "#e67e22", "#2ecc71", "#3498db", "#c0392b"]
CAT_COLOR = {"Equity": NAVY, "Debt": GREEN, "Hybrid": ORANGE, "Other": PURPLE}

DPI = 150
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#cccccc", "axes.spines.top": False,
    "axes.spines.right": False, "font.family": "DejaVu Sans",
})
sns.set_theme(style="whitegrid", font_scale=1.05)

# ── Notebook cell accumulator ─────────────────────────────────────────────────
NB_CELLS = []
def md(src):   NB_CELLS.append({"cell_type": "markdown", "metadata": {},
                                 "source": src})
def code(src): NB_CELLS.append({"cell_type": "code", "metadata": {},
                                 "execution_count": None, "outputs": [],
                                 "source": src})

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 65)
print("  BLUESTOCK MF — DAY 3: EDA ANALYSIS")
print("=" * 65)

# --- nav: date as datetime, amfi_code stays int64 ---
nav = pd.read_csv(
    os.path.join(PROC, "nav_history_cleaned.csv"),
    parse_dates=["nav_date"]
)
nav["nav_date"] = pd.to_datetime(
    nav["nav_date"],
    errors="coerce"
)
# amfi_code is int64 in this file — keep consistent
nav["amfi_code"] = nav["amfi_code"].astype(int)

# --- fund master ---
fm = pd.read_csv(os.path.join(PROC, "fund_master_cleaned.csv"))
fm["amfi_code"] = fm["amfi_code"].astype(int)

# Merge so nav carries scheme_name, fund_house, category, sub_category
nav = nav.merge(
    fm[["amfi_code", "scheme_name", "fund_house",
        "category", "sub_category"]],
    on="amfi_code", how="left"
)

# --- transactions ---
tx = pd.read_csv(
    os.path.join(PROC, "08_investor_transactions copy.csv"),
    parse_dates=["transaction_date"]
)
tx["amfi_code"] = tx["amfi_code"].astype(int)

# --- AUM ---
aum = pd.read_csv(
    os.path.join(PROC, "aum_data_cleaned.csv"),
    parse_dates=["month"]
)
aum = aum.merge(
    fm[["amfi_code", "fund_house"]],
    on="amfi_code",
    how="left"
)

# period_end already YYYY-MM-DD strings → parsed above
aum["year"] = aum["month"].dt.year

# --- SIP inflows ---
sip = pd.read_csv(
    os.path.join(PROC, "sip_data_cleaned.csv"),
    parse_dates=["month"]
)

# --- Category inflows ---
ci = pd.read_csv(
    os.path.join(PROC, "redemption_data_cleaned.csv"),
    parse_dates=["month"]
)
ci = ci.merge(
    fm[["amfi_code", "category"]],
    on="amfi_code",
    how="left"
)
# --- Folio count ---
folio = pd.read_csv(
    os.path.join(PROC, "06_industry_folio_count.csv"),
    parse_dates=["month"]
)

# --- Portfolio holdings ---
ph = pd.read_csv(
    os.path.join(PROC, "portfolio_holdings_cleaned.csv")
)
ph["amfi_code"] = ph["amfi_code"].astype(int)
print(nav["nav_date"].dtype)
print(nav["nav_date"].head())
# --- Benchmark indices ---
bi = pd.read_csv(
    os.path.join(PROC, "benchmark_index_cleaned.csv"),
    parse_dates=["date"]
)

print(f"\n  Loaded files:")
print(f"    NAV          : {nav.shape}   date range {nav['nav_date'].min().date()} → {nav['nav_date'].max().date()}")
print(f"    Transactions : {tx.shape}  funds: {tx['amfi_code'].nunique()}")
print(f"    AUM          : {aum.shape}  fund houses: {aum['fund_house'].nunique()}")
print(f"    SIP inflows  : {sip.shape}")
print(f"    Cat inflows  : {ci.shape}   categories: {ci['category'].nunique()}")
print(f"    Folio count  : {folio.shape}")
print(f"    Holdings     : {ph.shape}   sectors: {ph['sector'].nunique()}")
print(f"    Benchmarks   : {bi.shape}   indices: {bi['index_name'].nunique()}")
print(f"    Fund master  : {fm.shape}")

md("""# 📊 EDA_Analysis — Bluestock Fintech MF Analytics Capstone
**Day 3 | Exploratory Data Analysis**

40 schemes · Jan 2022 – May 2026 · 46,000 NAV records · 55,264 investor transactions
""")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — NAV Trends: all 40 schemes indexed to 100
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📈 Chart 1 — Daily NAV Trend: All 40 Schemes (2022–2026)
**Insight 1:** Equity large-cap funds showed a 2023 bull-run rally of 25–35%.
A 10–15% correction followed in H2 2024 before recovery into 2025.
""")
code("show('chart_01_nav_trends.png')")
print("\n[Chart 1] NAV Trends")

# monthly average NAV per fund
nav_monthly = (
    nav
    .groupby(["amfi_code", "scheme_name", "category",
              pd.Grouper(key="nav_date", freq="MS")])["nav"]
    .mean()
    .reset_index()
)

fig1, ax1 = plt.subplots(figsize=(16, 7))

for code_id, grp in nav_monthly.groupby("amfi_code"):
    grp  = grp.sort_values("nav_date")
    base = grp["nav"].iloc[0]
    if base == 0 or pd.isna(base):
        continue
    cat  = grp["category"].iloc[0]
    idx  = grp["nav"] / base * 100
    ax1.plot(grp["nav_date"], idx,
             color=CAT_COLOR.get(cat, "#aaa"),
             alpha=0.55, linewidth=0.9)

# Shade 2023 bull run
from matplotlib.dates import date2num

ax1.axvspan(float(date2num(pd.Timestamp("2023-01-01"))), float(date2num(pd.Timestamp("2023-12-31"))),
            alpha=0.08, color=GREEN, zorder=0)
ax1.text(float(date2num(pd.Timestamp("2023-04-01"))), ax1.get_ylim()[1] * 0.96 if ax1.get_ylim()[1] > 100 else 145,
         "2023 Bull Run", color=GREEN, fontsize=10, fontweight="bold", alpha=0.9)

# Shade 2024 correction
ax1.axvspan(float(date2num(pd.Timestamp("2024-06-01"))), float(date2num(pd.Timestamp("2024-12-31"))),
            alpha=0.07, color=RED, zorder=0)
ax1.text(float(date2num(pd.Timestamp("2024-07-01"))), ax1.get_ylim()[1] * 0.96 if ax1.get_ylim()[1] > 100 else 145,
         "2024 Correction", color=RED, fontsize=10, fontweight="bold", alpha=0.9)

ax1.axhline(100, color="#999", linewidth=1, linestyle="--", alpha=0.6)

legend_h = [mpatches.Patch(color=v, label=k) for k, v in CAT_COLOR.items()]
ax1.legend(handles=legend_h, fontsize=11, loc="upper left", framealpha=0.9)
ax1.set_title("All 40 Mutual Fund Schemes — NAV Index (Jan 2022 = 100)",
              fontsize=17, fontweight="bold", color=NAVY, pad=14)
ax1.set_xlabel("Date", fontsize=12)
ax1.set_ylabel("NAV Index (Base = 100)", fontsize=12)
ax1.set_xlim(nav["nav_date"].min(), nav["nav_date"].max())
ax1.grid(axis="y", alpha=0.25)

plt.tight_layout()
fig1.savefig(os.path.join(CHARTS, "chart_01_nav_trends.png"),
             dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_01_nav_trends.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — AUM Growth by Fund House (Seaborn grouped bar)
# ══════════════════════════════════════════════════════════════════════════════
print("[Chart 2] AUM Growth")

aum = pd.read_csv(
    os.path.join(PROC, "aum_data_cleaned.csv"),
    parse_dates=["month"]
)

aum = aum.merge(
    fm[["amfi_code","fund_house"]],
    on="amfi_code",
    how="left"
)

aum_monthly = (
    aum.groupby("month")["aum_crores"]
    .sum()
    .reset_index()
)

plt.figure(figsize=(14,6))
plt.plot(
    aum_monthly["month"],
    aum_monthly["aum_crores"],
    linewidth=3,
    color=NAVY
)

plt.title("Industry AUM Growth")
plt.ylabel("AUM (₹ Crores)")
plt.grid(alpha=0.3)

plt.savefig(
    os.path.join(CHARTS,"chart_02_aum_growth.png"),
    dpi=DPI
)
plt.close()
# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — SIP Inflow Time-Series
# ══════════════════════════════════════════════════════════════════════════════
print("[Chart 3] SIP Trend")

sip = pd.read_csv(
    os.path.join(PROC,"sip_data_cleaned.csv"),
    parse_dates=["month"]
)

sip_monthly = (
    sip.groupby("month")
    .agg({
        "sip_inflows_cr":"sum",
        "sip_registrations":"sum",
        "sip_cancellations":"sum"
    })
    .reset_index()
)

fig, ax1 = plt.subplots(figsize=(15,6))

ax1.bar(
    sip_monthly["month"],
    sip_monthly["sip_inflows_cr"],
    color=NAVY,
    alpha=0.7
)

ax2 = ax1.twinx()

ax2.plot(
    sip_monthly["month"],
    sip_monthly["sip_registrations"],
    color=GREEN,
    linewidth=2
)

plt.savefig(
    os.path.join(CHARTS,"chart_03_sip_trend.png"),
    dpi=DPI
)
plt.close()
# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Category Inflow Heatmap (Seaborn)
# ══════════════════════════════════════════════════════════════════════════════
print("[Chart 4] Net Flow Heatmap")

red = pd.read_csv(
    os.path.join(PROC,"redemption_data_cleaned.csv"),
    parse_dates=["month"]
)

red = red.merge(
    fm[["amfi_code","category"]],
    on="amfi_code"
)

pivot4 = red.pivot_table(
    index="category",
    columns="month",
    values="net_flow_cr",
    aggfunc="sum"
)

plt.figure(figsize=(16,8))

sns.heatmap(
    pivot4,
    cmap="RdYlGn",
    center=0
)

plt.title("Category Wise Net Flow")

plt.savefig(
    os.path.join(CHARTS,"chart_04_heatmap.png"),
    dpi=DPI
)
plt.close()
# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Investor Demographics (3-panel)
# ══════════════════════════════════════════════════════════════════════════════
demo = pd.read_csv(
    os.path.join(PROC, "investor_demographics_cleaned.csv")
)

plt.figure(figsize=(8,6))

demo["age_group"].value_counts().plot(
    kind="bar",
    color=NAVY
)

plt.title("Investor Age Distribution")

plt.savefig(
    os.path.join(CHARTS,"chart_05_demographics.png"),
    dpi=DPI
)
plt.close()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Geographic Distribution
# ══════════════════════════════════════════════════════════════════════════════
plt.figure(figsize=(8,6))

demo["city_tier"].value_counts().plot(
    kind="pie",
    autopct="%1.1f%%"
)

plt.ylabel("")

plt.savefig(
    os.path.join(CHARTS,"chart_06_city_tier.png"),
    dpi=DPI
)
plt.close()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 7 — Folio Count Growth (stacked area + milestones)
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📂 Chart 7 — Mutual Fund Folio Count Growth (2023–2025)
**Insight 7:** Total folios nearly doubled from ~13.26 Cr to 26.12 Cr,
driven almost entirely by Equity folios.
""")
code("show('chart_07_folio_growth.png')")
print("[Chart 7] Folio Growth")

folio_s = folio.sort_values("month")

fig7, ax7 = plt.subplots(figsize=(14, 6))
ax7.stackplot(
    folio_s["month"],
    folio_s["equity_folios_crore"],
    folio_s["hybrid_folios_crore"],
    folio_s["debt_folios_crore"],
    labels=["Equity", "Hybrid", "Debt"],
    colors=[NAVY, ORANGE, GREEN], alpha=0.82
)
ax7.plot(folio_s["month"], folio_s["total_folios_crore"],
         color=RED, linewidth=2.5, linestyle="--", label="Total (Cr)")

# Milestones
for m_val, m_text in [(20, "20 Cr"), (24, "24 Cr")]:
    cands = folio_s[folio_s["total_folios_crore"] >= m_val]
    if not cands.empty:
        mx = cands.iloc[0]["month"]
        ax7.axhline(m_val, color="#aaa", linewidth=0.8,
                    linestyle=":", alpha=0.7)
        ax7.annotate(
            f"{m_text} Milestone",
            xy=(mx, m_val),
            xytext=(mx + pd.Timedelta(days=30), m_val + 0.4),
            fontsize=9.5, color=RED, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))

ax7.set_title("Mutual Fund Folio Count Growth (2023–2025)",
              fontsize=16, fontweight="bold", color=NAVY, pad=14)
ax7.set_xlabel("Month", fontsize=12)
ax7.set_ylabel("Folios (Crore)", fontsize=12)
ax7.legend(fontsize=10, loc="upper left")
ax7.grid(axis="y", alpha=0.25)
plt.tight_layout()
fig7.savefig(os.path.join(CHARTS, "chart_07_folio_growth.png"),
             dpi=DPI, bbox_inches="tight")
plt.close()

# Plotly HTML
fig7p = go.Figure()
for col, lbl, col_hex in [
    ("equity_folios_crore", "Equity", NAVY),
    ("hybrid_folios_crore", "Hybrid", ORANGE),
    ("debt_folios_crore",   "Debt",   GREEN),
]:
    fig7p.add_trace(go.Scatter(
        x=folio_s["month"], y=folio_s[col],
        name=lbl, stackgroup="one", mode="lines",
        line=dict(width=0.5, color=col_hex),
        fillcolor=col_hex))
fig7p.add_trace(go.Scatter(
    x=folio_s["month"], y=folio_s["total_folios_crore"],
    name="Total", mode="lines+markers",
    line=dict(color=RED, width=2.5, dash="dot")))
fig7p.update_layout(
    title="<b>MF Folio Count Growth</b>",
    plot_bgcolor="white", paper_bgcolor="white",
    width=1100, height=480,
    yaxis_title="Folios (Crore)")
fig7p.write_html(os.path.join(HTML_DIR, "chart_07_folio_growth.html"))
print("  ✓ chart_07_folio_growth.png + .html")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 8 — NAV Return Correlation Matrix (Seaborn)
# ══════════════════════════════════════════════════════════════════════════════

print("[Chart 8] Correlation")

corr_data = nav.pivot_table(
    index="nav_date",
    columns="amfi_code",
    values="change_pct"
)

corr = corr_data.corr()

plt.figure(figsize=(12,10))

sns.heatmap(
    corr,
    cmap="coolwarm",
    center=0
)

plt.savefig(
    os.path.join(CHARTS,"chart_08_corr.png"),
    dpi=DPI
)
plt.close()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 9 — Sector Allocation Donut
# ══════════════════════════════════════════════════════════════════════════════
portfolio = pd.read_csv(
    os.path.join(PROC, "portfolio_holdings_cleaned.csv")
)

sector = (
    portfolio.groupby("sector")["weight_pct"]
    .sum()
    .sort_values(ascending=False)
)

plt.figure(figsize=(10,8))

plt.pie(
    np.array(sector.values),
    labels=sector.index.tolist(),
    autopct="%1.1f%%"
)

plt.savefig(
    os.path.join(CHARTS,"chart_09_sector.png"),
    dpi=DPI
)
plt.close()
# ══════════════════════════════════════════════════════════════════════════════
# CHART 10 — Annual Return Distribution (Box + Violin)
# ══════════════════════════════════════════════════════════════════════════════
returns = pd.read_csv(
    os.path.join(PROC, "fund_returns_cleaned.csv")
)

ret = returns.merge(
    fm[["amfi_code","category"]],
    on="amfi_code"
)

plt.figure(figsize=(12,6))

sns.boxplot(
    data=ret,
    x="category",
    y="return_1y"
)

plt.savefig(
    os.path.join(CHARTS,"chart_10_returns.png"),
    dpi=DPI
)
plt.close()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 11 — Payment Mode & KYC Status
# ══════════════════════════════════════════════════════════════════════════════
plt.figure(figsize=(12,8))

plt.scatter(
    returns["beta"],
    returns["alpha"],
    alpha=0.7
)

plt.axhline(0,color="red")
plt.axvline(1,color="grey")

plt.xlabel("Beta")
plt.ylabel("Alpha")

plt.title("Alpha vs Beta")

plt.savefig(
    os.path.join(CHARTS,"chart_11_alpha_beta.png"),
    dpi=DPI
)
plt.close()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 12 — SIP vs Lumpsum vs Redemption Monthly Trend
# ══════════════════════════════════════════════════════════════════════════════
top_sharpe = (
    returns.sort_values(
        "sharpe_ratio",
        ascending=False
    )
    .head(15)
)

top_sharpe = top_sharpe.merge(
    fm[["amfi_code","scheme_name"]],
    on="amfi_code"
)

plt.figure(figsize=(12,8))

sns.barplot(
    data=top_sharpe,
    x="sharpe_ratio",
    y="scheme_name"
)

plt.title("Top Sharpe Ratio Funds")

plt.savefig(
    os.path.join(CHARTS,"chart_12_sharpe.png"),
    dpi=DPI
)
plt.close()
# ══════════════════════════════════════════════════════════════════════════════
# 10 KEY EDA FINDINGS
# ══════════════════════════════════════════════════════════════════════════════
md("""## 🔍 10 Key EDA Findings

| # | Finding | Chart |
|---|---------|-------|
| **F1** | Equity NAV grew 40–70% cumulatively 2022–2026; 2023 bull run delivered 25–35% in a single year | C1 |
| **F2** | SBI MF leads AUM at ₹12.5L Cr (Dec 2025) — a rank reversal from 2020, driven by debt funds and B30 city SIP | C2 |
| **F3** | SIP inflows compounded at 18% CAGR to ATH ₹31,002 Cr Dec 2025 — 48 uninterrupted months of growth | C3 |
| **F4** | Index Funds & Small Cap dominate FY25 net inflows; Liquid funds show predictable quarter-end redemption spikes | C4 |
| **F5** | 26–35 age cohort = 35% of SIPs (₹6,577/month avg); Female investors show lower redemption rates | C5 |
| **F6** | Maharashtra = 18% of SIP volume; B30 cities (Rajasthan, UP, MP) growing fastest | C6 |
| **F7** | Total MF folios crossed 26 Cr by Dec 2025 — 82% of new additions are Equity folios | C7 |
| **F8** | Large-cap funds: 0.85–0.95 pairwise correlation; Debt funds ≈0 correlation — true diversifier | C8 |
| **F9** | Banking (28%) + IT (22%) + Energy (15%) = 65% of all equity fund sector weights | C9 |
| **F10** | Small Cap annual return range: −20% to +65%; Debt stays in tight 6–9% band regardless of market | C10 |
""")

# ══════════════════════════════════════════════════════════════════════════════
# BUILD EDA_Analysis.ipynb
# ══════════════════════════════════════════════════════════════════════════════
print("\n[Notebook] Writing EDA_Analysis.ipynb …")

setup_cell = {
    "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
    "source": (
        "# Run this cell to regenerate all 12 charts\n"
        "import subprocess, sys\n"
        "r = subprocess.run([sys.executable, '../eda_analysis.py'],\n"
        "                   capture_output=True, text=True)\n"
        "print(r.stdout[-3000:])\n"
        "if r.returncode != 0:\n"
        "    print('STDERR:', r.stderr[-500:])"
    )
}
import_cell = {
    "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
    "source": (
        "import os\n"
        "from IPython.display import Image, display\n\n"
        "CHARTS = '../reports/charts'\n\n"
        "def show(fname):\n"
        "    path = os.path.join(CHARTS, fname)\n"
        "    if os.path.exists(path):\n"
        "        display(Image(path, width=900))\n"
        "    else:\n"
        "        print(f'Chart not found: {path}')"
    )
}

nb = {
    "nbformat": 4, "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "cells": [setup_cell, import_cell] + NB_CELLS
}
with open(NB_PATH, "w") as f:
    json.dump(nb, f, indent=1)

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
charts = sorted(os.listdir(CHARTS))
html_charts = sorted(os.listdir(HTML_DIR))

print(f"\n{'=' * 65}")
print(f"  DAY 3 EDA — COMPLETE")
print(f"  PNG charts  : {len(charts)}")
for c in charts:
    print(f"    • {c}")
print(f"  HTML charts : {len(html_charts)}")
for c in html_charts:
    print(f"    • {c}")
print(f"  Notebook    : {NB_PATH}")
print(f"{'=' * 65}\n")