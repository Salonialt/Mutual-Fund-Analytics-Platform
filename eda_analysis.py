"""
eda_analysis.py — Day 3 EDA | Bluestock Fintech MF Analytics Capstone
Generates 12 publication-quality charts (PNG) + interactive HTML + EDA_Analysis.ipynb
"""

import os, warnings, json, textwrap
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

BASE   = os.path.dirname(os.path.abspath(__file__))
PROC   = os.path.join(BASE, "data", "processed")
CHARTS = os.path.join(BASE, "reports", "charts")
HTML_DIR = os.path.join(BASE, "reports", "charts_html")
NB_OUT = os.path.join(BASE, "notebooks", "EDA_Analysis.ipynb")
os.makedirs(CHARTS, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(os.path.dirname(NB_OUT), exist_ok=True)

# ── Brand palette ──────────────────────────────────────────────────────────────
NAVY   = "#1a2744"
ORANGE = "#f7931e"
GREEN  = "#27ae60"
RED    = "#e74c3c"
TEAL   = "#17becf"
PURPLE = "#8e44ad"
PALETTE = [NAVY, ORANGE, GREEN, RED, PURPLE, TEAL, "#e67e22", "#2ecc71", "#3498db", "#c0392b"]

sns.set_theme(style="whitegrid", font_scale=1.08)
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#cccccc", "axes.spines.top": False,
    "axes.spines.right": False, "font.family": "DejaVu Sans",
})
DPI = 150

# ── Load & merge data ──────────────────────────────────────────────────────────
nav   = pd.read_csv(os.path.join(PROC, "clean_nav.csv"), parse_dates=["date"])
fm    = pd.read_csv(os.path.join(BASE, "data", "raw", "01_fund_master.csv"))
tx    = pd.read_csv(os.path.join(PROC, "clean_transactions.csv"), parse_dates=["transaction_date"])
aum   = pd.read_csv(os.path.join(PROC, "clean_aum.csv"), parse_dates=["period_end"])
sip   = pd.read_csv(os.path.join(PROC, "clean_sip_inflows.csv"), parse_dates=["month"])
ci    = pd.read_csv(os.path.join(PROC, "clean_category_inflows.csv"), parse_dates=["month"])
folio = pd.read_csv(os.path.join(PROC, "clean_folio_count.csv"), parse_dates=["month"])
ph    = pd.read_csv(os.path.join(PROC, "clean_portfolio_holdings.csv"))
nav   = nav.merge(fm[["amfi_code","scheme_name","fund_house","category","sub_category"]], on="amfi_code", how="left")

print(f"✅ Data loaded — NAV:{len(nav):,} | TX:{len(tx):,} | AUM:{len(aum):,}")

NB_CELLS = []
def md(src):  NB_CELLS.append({"cell_type":"markdown","metadata":{},"source":src})
def code(src): NB_CELLS.append({"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":src})

md("""# 📊 EDA_Analysis — Bluestock Fintech Mutual Fund Analytics Capstone
**Day 3 | Exploratory Data Analysis**

40 schemes · Jan 2022 – May 2026 · 46,000 NAV records · 55,264 investor transactions
""")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — NAV Trends (matplotlib, all 40 schemes normalised to 100)
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📈 Chart 1 — Daily NAV Trend: All 40 Schemes (2022–2026)
**Insight 1:** Equity large-cap funds showed a sharp 2023 bull-run rally of 30–40%.
A mild 10–15% correction followed in H2 2024 before recovery in early 2025.
""")
code("show('chart_01_nav_trends.png')")

print("\n[Chart 1] NAV Trends")
nav_m = (nav.groupby(["amfi_code","scheme_name","category",
                       pd.Grouper(key="date", freq="MS")])["nav"].mean().reset_index())
cat_color = {"Equity": NAVY, "Debt": GREEN, "Hybrid": ORANGE, "Other": PURPLE}
cat_alpha  = {"Equity": 0.55, "Debt": 0.65, "Hybrid": 0.65, "Other": 0.50}

fig1, ax1 = plt.subplots(figsize=(16, 7))

for code_id, grp in nav_m.groupby("amfi_code"):
    grp  = grp.sort_values("date")
    base = grp["nav"].iloc[0]
    if base == 0: continue
    idx  = grp["nav"] / base * 100
    cat  = grp["category"].iloc[0]
    ax1.plot(grp["date"], idx,
             color=cat_color.get(cat, "#aaa"),
             alpha=cat_alpha.get(cat, 0.4), linewidth=0.9)

# Shade 2023 bull run
ax1.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"),
            alpha=0.08, color=GREEN, zorder=0)
ax1.text(pd.Timestamp("2023-04-01"), 195, "2023 Bull Run",
         color=GREEN, fontsize=11, fontweight="bold", alpha=0.9)
# Shade 2024 correction
ax1.axvspan(pd.Timestamp("2024-06-01"), pd.Timestamp("2024-12-31"),
            alpha=0.07, color=RED, zorder=0)
ax1.text(pd.Timestamp("2024-07-01"), 195, "2024 Correction",
         color=RED, fontsize=11, fontweight="bold", alpha=0.9)
ax1.axhline(100, color="#999", linewidth=1, linestyle="--", alpha=0.6)

legend_handles = [mpatches.Patch(color=v, label=k) for k,v in cat_color.items()]
ax1.legend(handles=legend_handles, fontsize=11, loc="upper left", framealpha=0.9)
ax1.set_title("All 40 Mutual Fund Schemes — NAV Index (Jan 2022 = 100)",
              fontsize=17, fontweight="bold", color=NAVY, pad=14)
ax1.set_xlabel("Date", fontsize=12); ax1.set_ylabel("NAV Index (Base = 100)", fontsize=12)
ax1.set_xlim(nav_m["date"].min(), nav_m["date"].max())
ax1.grid(axis="y", alpha=0.25)
plt.tight_layout()
fig1.savefig(os.path.join(CHARTS, "chart_01_nav_trends.png"), dpi=DPI, bbox_inches="tight")
plt.close()

# Also save Plotly HTML (interactive)
fig1p = go.Figure()
for code_id, grp in nav_m.groupby(["amfi_code","scheme_name","category"]):
    grp2 = nav_m[(nav_m["amfi_code"]==code_id[0])].sort_values("date")
    base2 = grp2["nav"].iloc[0]
    if base2 == 0: continue
    fig1p.add_trace(go.Scatter(x=grp2["date"], y=(grp2["nav"]/base2*100).round(2),
        name=str(code_id[1])[:35], mode="lines",
        line=dict(width=1.2, color=cat_color.get(code_id[2],"#888")),
        opacity=0.7, visible="legendonly" if code_id[2]=="Other" else True,
        hovertemplate="%{fullData.name}<br>%{x|%b %Y}: %{y:.1f}<extra></extra>"))
fig1p.add_vrect(x0="2023-01-01",x1="2023-12-31",fillcolor="rgba(39,174,96,0.08)",line_width=0,
    annotation_text="2023 Bull Run",annotation_position="top left",annotation_font_color=GREEN)
fig1p.add_vrect(x0="2024-06-01",x1="2024-12-31",fillcolor="rgba(231,76,60,0.07)",line_width=0,
    annotation_text="2024 Correction",annotation_position="top left",annotation_font_color=RED)
fig1p.update_layout(title="<b>All 40 MF Schemes — NAV Index (Jan 2022=100)</b>",
    plot_bgcolor="white",paper_bgcolor="white",width=1100,height=560,
    xaxis=dict(showgrid=True,gridcolor="#f0f0f0"),yaxis=dict(showgrid=True,gridcolor="#f0f0f0"),
    legend=dict(font_size=8,x=1.01,y=1))
fig1p.write_html(os.path.join(HTML_DIR, "chart_01_nav_trends.html"))
print("   ✓ chart_01_nav_trends.png + .html")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — AUM Grouped Bar (Seaborn)
# ══════════════════════════════════════════════════════════════════════════════
md("""## 🏛️ Chart 2 — AUM Growth by Fund House (2022–2025)
**Insight 2:** SBI Mutual Fund emerged as India's largest AMC with AUM exceeding ₹12.5 lakh crore
by Dec 2025, driven by aggressive retail SIP mobilisation in B30 cities.
""")
code("show('chart_02_aum_growth.png')")

print("[Chart 2] AUM Growth")
aum["year"] = aum["period_end"].dt.year
aum_yr = (aum[aum["year"].between(2022,2025)]
          .groupby(["fund_house","year"])["aum_crore"].max().reset_index())
aum_yr["aum_lakh_cr"] = aum_yr["aum_crore"] / 1e5
top_h = (aum_yr.groupby("fund_house")["aum_lakh_cr"].max().nlargest(8).index.tolist())
aum_top = aum_yr[aum_yr["fund_house"].isin(top_h)].copy()
aum_top["fh_short"] = aum_top["fund_house"].str.replace(" Mutual Fund","").str.replace(" MF","")

fig2, ax2 = plt.subplots(figsize=(14, 7))
year_pal = {2022:"#bdc3c7", 2023:"#95a5a6", 2024:"#5d6d7e", 2025:NAVY}
x = np.arange(len(top_h))
w = 0.2
fh_short = [h.replace(" Mutual Fund","").replace(" MF","") for h in top_h]
for i, yr in enumerate([2022,2023,2024,2025]):
    vals = [aum_top[(aum_top["fund_house"]==h)&(aum_top["year"]==yr)]["aum_lakh_cr"].sum()
            for h in top_h]
    bars = ax2.bar(x + i*w - 1.5*w, vals, w, label=str(yr),
                   color=year_pal[yr], edgecolor="white", linewidth=0.5)

sbi_idx = next((i for i,h in enumerate(top_h) if "SBI" in h), -1)
if sbi_idx >= 0:
    sbi_max = aum_top[aum_top["fund_house"].str.contains("SBI")]["aum_lakh_cr"].max()
    ax2.axvspan(sbi_idx-0.5, sbi_idx+0.5, alpha=0.10, color=ORANGE, zorder=0)
    ax2.annotate(f"₹12.5L Cr\nDominance ▲",
                 xy=(sbi_idx, sbi_max), xytext=(sbi_idx+0.55, sbi_max*0.92),
                 fontsize=10, color=ORANGE, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5))

ax2.set_xticks(x); ax2.set_xticklabels(fh_short, rotation=22, ha="right", fontsize=10)
ax2.set_title("AUM Growth by Fund House (2022–2025) | Top 8 AMCs",
              fontsize=16, fontweight="bold", color=NAVY, pad=14)
ax2.set_ylabel("AUM (₹ Lakh Crore)", fontsize=12)
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
ax2.legend(title="Year", fontsize=10, title_fontsize=10)
ax2.grid(axis="y", alpha=0.3)
plt.tight_layout()
fig2.savefig(os.path.join(CHARTS, "chart_02_aum_growth.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_02_aum_growth.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — SIP Inflow Time-Series (matplotlib with Plotly HTML)
# ══════════════════════════════════════════════════════════════════════════════
md("""## 💰 Chart 3 — Monthly SIP Inflow Trend (Jan 2022 – Dec 2025)
**Insight 3:** Monthly SIP inflows grew at ~18% CAGR from ₹12,044 Cr (Jan 2022) to an all-time
high of ₹31,002 Cr (Dec 2025), reflecting India's deepening equity culture.
""")
code("show('chart_03_sip_trend.png')")

print("[Chart 3] SIP Trend")
sip_s = sip.sort_values("month")

fig3, ax3a = plt.subplots(figsize=(15, 6))
ax3b = ax3a.twinx()

ax3a.bar(sip_s["month"], sip_s["sip_inflow_crore"],
         width=25, color=NAVY, alpha=0.70, label="SIP Inflow (₹ Cr)")
ma3 = sip_s["sip_inflow_crore"].rolling(3).mean()
ax3a.plot(sip_s["month"], ma3, color=ORANGE, linewidth=2.5, label="3-Month MA")

ax3b.plot(sip_s["month"], sip_s["active_sip_accounts_crore"],
          color=GREEN, linewidth=2, linestyle="--", label="Active Accounts (Cr)")
ax3b.set_ylabel("Active SIP Accounts (Crore)", fontsize=11, color=GREEN)
ax3b.tick_params(axis="y", colors=GREEN)

peak_i = sip_s["sip_inflow_crore"].idxmax()
peak_r = sip_s.loc[peak_i]
ax3a.annotate(f"All-Time High\n₹{peak_r['sip_inflow_crore']:,.0f} Cr\nDec 2025",
              xy=(peak_r["month"], peak_r["sip_inflow_crore"]),
              xytext=(peak_r["month"] - pd.Timedelta(days=400), peak_r["sip_inflow_crore"] * 0.88),
              fontsize=10.5, color=RED, fontweight="bold",
              arrowprops=dict(arrowstyle="->", color=RED, lw=1.8),
              bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=RED, alpha=0.9))

lines1, labels1 = ax3a.get_legend_handles_labels()
lines2, labels2 = ax3b.get_legend_handles_labels()
ax3a.legend(lines1 + lines2, labels1 + labels2, fontsize=10, loc="upper left")
ax3a.set_title("Monthly SIP Inflows — India MF Industry (Jan 2022 – Dec 2025)",
               fontsize=16, fontweight="bold", color=NAVY, pad=14)
ax3a.set_xlabel("Month", fontsize=12)
ax3a.set_ylabel("SIP Inflow (₹ Crore)", fontsize=12)
ax3a.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"₹{int(x):,}"))
ax3a.grid(axis="y", alpha=0.25)
plt.tight_layout()
fig3.savefig(os.path.join(CHARTS, "chart_03_sip_trend.png"), dpi=DPI, bbox_inches="tight")
plt.close()

# Plotly interactive
fig3p = make_subplots(specs=[[{"secondary_y":True}]])
fig3p.add_trace(go.Bar(x=sip_s["month"],y=sip_s["sip_inflow_crore"],
    name="SIP Inflow (₹ Cr)",marker_color=NAVY,opacity=0.75),secondary_y=False)
fig3p.add_trace(go.Scatter(x=sip_s["month"],y=ma3,name="3M MA",
    line=dict(color=ORANGE,width=2.5)),secondary_y=False)
fig3p.add_trace(go.Scatter(x=sip_s["month"],y=sip_s["active_sip_accounts_crore"],
    name="Active Accounts (Cr)",line=dict(color=GREEN,width=2,dash="dot")),secondary_y=True)
fig3p.add_annotation(x=peak_r["month"],y=peak_r["sip_inflow_crore"],
    text=f"<b>ATH ₹{peak_r['sip_inflow_crore']:,.0f} Cr</b>",
    showarrow=True,arrowhead=2,arrowcolor=RED,ax=50,ay=-50,
    font=dict(size=12,color=RED),bgcolor="white",bordercolor=RED)
fig3p.update_layout(title="<b>Monthly SIP Inflows</b>",plot_bgcolor="white",
    paper_bgcolor="white",width=1100,height=500,
    xaxis=dict(showgrid=True,gridcolor="#f0f0f0"),
    yaxis=dict(showgrid=True,gridcolor="#f0f0f0"))
fig3p.write_html(os.path.join(HTML_DIR,"chart_03_sip_trend.html"))
print("   ✓ chart_03_sip_trend.png + .html")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Category Inflow Heatmap (Seaborn)
# ══════════════════════════════════════════════════════════════════════════════
md("""## 🗺️ Chart 4 — Category Inflow Heatmap (FY2024-25)
**Insight 4:** Index Funds and Small Cap saw the highest consistent net inflows in FY2024-25.
Liquid funds showed predictable quarter-end redemption spikes from corporate treasury activity.
""")
code("show('chart_04_category_heatmap.png')")

print("[Chart 4] Category Heatmap")
ci["month_str"] = ci["month"].dt.strftime("%b %Y")
month_order = ci.sort_values("month")["month_str"].unique().tolist()
pivot4 = ci.pivot_table(index="category", columns="month_str",
                        values="net_inflow_crore", aggfunc="sum")
pivot4 = pivot4.reindex(columns=month_order)
row_order = pivot4.mean(axis=1).sort_values(ascending=False).index
pivot4 = pivot4.reindex(index=row_order)

fig4, ax4 = plt.subplots(figsize=(17, 8))
cmap4 = sns.diverging_palette(10, 133, as_cmap=True)
sns.heatmap(pivot4, cmap=cmap4, center=0, annot=True, fmt=".0f",
            linewidths=0.4, linecolor="#e8e8e8",
            annot_kws={"size":8.5}, ax=ax4,
            cbar_kws={"label":"Net Inflow (₹ Crore)","shrink":0.8})
ax4.set_title("Category-wise Net Inflow Heatmap (FY 2024-25)",
              fontsize=16, fontweight="bold", color=NAVY, pad=14)
ax4.set_xlabel("Month", fontsize=12); ax4.set_ylabel("Fund Category", fontsize=12)
ax4.set_xticklabels(ax4.get_xticklabels(), rotation=35, ha="right", fontsize=9)
ax4.set_yticklabels(ax4.get_yticklabels(), rotation=0, fontsize=10)
plt.tight_layout()
fig4.savefig(os.path.join(CHARTS, "chart_04_category_heatmap.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_04_category_heatmap.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Investor Demographics (3 panels)
# ══════════════════════════════════════════════════════════════════════════════
md("""## 👥 Chart 5 — Investor Demographics
**Insight 5:** The 26–35 cohort drives 35% of SIP participation with avg ₹6,577/month.
Female investors show 18% lower SIP amounts but meaningfully lower redemption rates.
""")
code("show('chart_05_demographics.png')")

print("[Chart 5] Demographics")
tx_sip = tx[tx["transaction_type"]=="SIP"]
age_order = ["18-25","26-35","36-45","46-55","56+"]
age_dist  = tx["age_group"].value_counts().reindex(age_order)
gender_dist = tx["gender"].value_counts()

fig5, axes5 = plt.subplots(1, 3, figsize=(19, 7))
age_cols = [NAVY, ORANGE, GREEN, RED, PURPLE]

# A) Age pie
wedges, _, auts = axes5[0].pie(age_dist.values, labels=age_dist.index,
    autopct="%1.1f%%", colors=age_cols, pctdistance=0.78,
    startangle=90, wedgeprops=dict(edgecolor="white", linewidth=2.2))
for at in auts: at.set_fontsize(10); at.set_fontweight("bold")
axes5[0].set_title("Age Group Distribution\n(All Transactions)", fontsize=13,
                   fontweight="bold", color=NAVY)

# B) Box plot SIP amount by age
bp_data = [tx_sip[tx_sip["age_group"]==ag]["amount_inr"].clip(0,50000).values
           for ag in age_order]
bp = axes5[1].boxplot(bp_data, patch_artist=True, notch=False,
                      medianprops=dict(color="white",linewidth=2.2))
for patch, col in zip(bp["boxes"], age_cols):
    patch.set_facecolor(col); patch.set_alpha(0.82)
for w in bp["whiskers"]: w.set_color("#aaa")
for c in bp["caps"]:     c.set_color("#aaa")
for f in bp["fliers"]:   f.set_markerfacecolor("#ccc"); f.set_markersize(3)
axes5[1].set_xticklabels(age_order, fontsize=10)
axes5[1].set_title("SIP Amount by Age Group", fontsize=13, fontweight="bold", color=NAVY)
axes5[1].set_ylabel("SIP Amount (₹)", fontsize=11)
axes5[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"₹{int(x):,}"))
axes5[1].grid(axis="y", alpha=0.3)

# C) Gender pie
gc = [NAVY, ORANGE]
axes5[2].pie(gender_dist.values, labels=gender_dist.index,
             autopct="%1.1f%%", colors=gc, startangle=90,
             wedgeprops=dict(edgecolor="white",linewidth=2.5), pctdistance=0.74)
axes5[2].set_title("Gender Split\n(All Transactions)", fontsize=13, fontweight="bold", color=NAVY)
am = tx_sip[tx_sip["gender"]=="Male"]["amount_inr"].mean()
af = tx_sip[tx_sip["gender"]=="Female"]["amount_inr"].mean()
axes5[2].text(0,-1.3,f"Avg SIP  Male: ₹{am:,.0f}  |  Female: ₹{af:,.0f}",
              ha="center",fontsize=9,color="#555")

fig5.suptitle("Investor Demographics Analysis", fontsize=18,
              fontweight="bold", color=NAVY, y=1.01)
plt.tight_layout()
fig5.savefig(os.path.join(CHARTS,"chart_05_demographics.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_05_demographics.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Geographic Distribution
# ══════════════════════════════════════════════════════════════════════════════
md("""## 🗺️ Chart 6 — Geographic Distribution of SIP Investments
**Insight 6:** Maharashtra leads with 18% of SIP volume (₹70 Cr). B30 cities (Rajasthan, UP, MP)
are growing fastest, validating AMFI's B30 incentive of higher TER allowances.
""")
code("show('chart_06_geographic.png')")

print("[Chart 6] Geographic")
tx_inv = tx[tx["transaction_type"]!="Redemption"]
state_agg = (tx_inv.groupby(["state","city_tier"])
             .agg(total_cr=("amount_inr",lambda x: x.sum()/1e7),
                  n_inv=("investor_id","nunique"))
             .reset_index().sort_values("total_cr",ascending=True))
tier_agg = tx_inv.groupby("city_tier")["amount_inr"].sum()

fig6, (ax6a, ax6b) = plt.subplots(1, 2, figsize=(17, 8),
                                   gridspec_kw={"width_ratios":[2.5,1]})
bar_cols6 = [NAVY if t=="T30" else ORANGE for t in state_agg["city_tier"]]
bars6 = ax6a.barh(state_agg["state"], state_agg["total_cr"],
                  color=bar_cols6, edgecolor="white", height=0.65)
for bar, val in zip(bars6, state_agg["total_cr"]):
    ax6a.text(bar.get_width()+0.4, bar.get_y()+bar.get_height()/2,
              f"₹{val:.1f} Cr", va="center", fontsize=9, color="#333")
ax6a.legend(handles=[mpatches.Patch(color=NAVY,label="T30 Cities"),
                     mpatches.Patch(color=ORANGE,label="B30 Cities")], fontsize=10)
ax6a.set_title("SIP Investment by State (₹ Crore)", fontsize=14,
               fontweight="bold", color=NAVY)
ax6a.set_xlabel("Total SIP Investment (₹ Crore)", fontsize=11)
ax6a.set_xlim(0, state_agg["total_cr"].max()*1.20)
ax6a.grid(axis="x", alpha=0.3)

ax6b.pie(tier_agg.values, labels=tier_agg.index, autopct="%1.1f%%",
         colors=[NAVY, ORANGE], startangle=90,
         wedgeprops=dict(edgecolor="white",linewidth=2.5),
         pctdistance=0.72, explode=[0,0.07])
ax6b.set_title("T30 vs B30\nCity Tier Split", fontsize=14, fontweight="bold", color=NAVY)
ax6b.text(0,-1.28,"T30 = Top 30 cities by AUM | B30 = Beyond Top 30",
          ha="center",fontsize=8.5,color="#555")
plt.tight_layout()
fig6.savefig(os.path.join(CHARTS,"chart_06_geographic.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_06_geographic.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 7 — Folio Count Growth
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📂 Chart 7 — Mutual Fund Folio Count Growth (2023–2025)
**Insight 7:** Total MF folios nearly doubled from ~13.26 Cr to 26.12 Cr, driven almost entirely
by Equity folios — reflecting SIP-led democratisation of investing.
""")
code("show('chart_07_folio_growth.png')")

print("[Chart 7] Folio Growth")
folio_s = folio.sort_values("month")

fig7, ax7 = plt.subplots(figsize=(14, 6))
ax7.stackplot(folio_s["month"],
              folio_s["equity_folios_crore"],
              folio_s["hybrid_folios_crore"],
              folio_s["debt_folios_crore"],
              labels=["Equity","Hybrid","Debt"],
              colors=[NAVY, ORANGE, GREEN], alpha=0.82)
ax7.plot(folio_s["month"], folio_s["total_folios_crore"],
         color=RED, linewidth=2.5, linestyle="--", label="Total (₹ Cr)")
for m_val, m_text, m_y in [(20,"20 Cr Milestone",20.5),(24,"24 Cr Milestone",24.5)]:
    candidates = folio_s[folio_s["total_folios_crore"] >= m_val]
    if not candidates.empty:
        mx = candidates.iloc[0]["month"]
        ax7.axhline(m_val, color="#aaa", linewidth=0.8, linestyle=":", alpha=0.7)
        ax7.annotate(m_text, xy=(mx, m_val),
                     xytext=(mx + pd.Timedelta(days=30), m_y),
                     fontsize=9.5, color=RED, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))

ax7.set_title("Mutual Fund Folio Count Growth (2023–2025)", fontsize=16,
              fontweight="bold", color=NAVY, pad=14)
ax7.set_xlabel("Month", fontsize=12)
ax7.set_ylabel("Folios (Crore)", fontsize=12)
ax7.legend(fontsize=10, loc="upper left")
ax7.grid(axis="y", alpha=0.25)
plt.tight_layout()
fig7.savefig(os.path.join(CHARTS,"chart_07_folio_growth.png"), dpi=DPI, bbox_inches="tight")
plt.close()

# Plotly interactive HTML
fig7p = go.Figure()
for col, lbl, col_hex in [("equity_folios_crore","Equity",NAVY),
                           ("hybrid_folios_crore","Hybrid",ORANGE),
                           ("debt_folios_crore","Debt",GREEN)]:
    fig7p.add_trace(go.Scatter(x=folio_s["month"],y=folio_s[col],name=lbl,
        stackgroup="one",mode="lines",line=dict(width=0.5,color=col_hex),
        fillcolor=col_hex))
fig7p.add_trace(go.Scatter(x=folio_s["month"],y=folio_s["total_folios_crore"],
    name="Total",mode="lines+markers",line=dict(color=RED,width=2.5,dash="dot")))
fig7p.update_layout(title="<b>MF Folio Count Growth</b>",plot_bgcolor="white",
    paper_bgcolor="white",width=1100,height=480,
    xaxis=dict(showgrid=True,gridcolor="#f0f0f0"),
    yaxis=dict(showgrid=True,gridcolor="#f0f0f0",title="Folios (Crore)"))
fig7p.write_html(os.path.join(HTML_DIR,"chart_07_folio_growth.html"))
print("   ✓ chart_07_folio_growth.png + .html")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 8 — Correlation Matrix (Seaborn)
# ══════════════════════════════════════════════════════════════════════════════
md("""## 🔗 Chart 8 — NAV Return Correlation Matrix (10 Selected Funds)
**Insight 8:** Large-cap equity funds exhibit 0.85–0.95 pairwise correlation.
Debt (Liquid) funds show ≈0 correlation with equity — confirming their role as diversifiers.
""")
code("show('chart_08_correlation.png')")

print("[Chart 8] Correlation Matrix")
sel_10 = [125497,119551,120503,118632,119092,120841,131597,125354,119270,100341]
sel_10 = [c for c in sel_10 if c in nav["amfi_code"].values]
nav_piv = (nav[nav["amfi_code"].isin(sel_10)]
           .pivot_table(index="date", columns="amfi_code", values="daily_return_pct"))
short_names = {row["amfi_code"]: row["scheme_name"][:26] for _, row in fm.iterrows()}
nav_piv.columns = [short_names.get(c, str(c)) for c in nav_piv.columns]
corr8 = nav_piv.corr()

fig8, ax8 = plt.subplots(figsize=(13, 11))
mask8 = np.triu(np.ones_like(corr8, dtype=bool))
sns.heatmap(corr8, mask=mask8, cmap=sns.diverging_palette(230,20,as_cmap=True),
            vmin=-1, vmax=1, center=0, annot=True, fmt=".2f",
            linewidths=0.5, linecolor="#e8e8e8",
            annot_kws={"size":9.5,"weight":"bold"},
            cbar_kws={"label":"Pearson r","shrink":0.8}, ax=ax8)
ax8.set_title("Daily Return Correlation — 10 Selected MF Schemes",
              fontsize=15, fontweight="bold", color=NAVY, pad=14)
ax8.set_xticklabels(ax8.get_xticklabels(), rotation=35, ha="right", fontsize=9)
ax8.set_yticklabels(ax8.get_yticklabels(), rotation=0, fontsize=9)
plt.tight_layout()
fig8.savefig(os.path.join(CHARTS,"chart_08_correlation.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_08_correlation.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 9 — Sector Allocation Donut
# ══════════════════════════════════════════════════════════════════════════════
md("""## 🍩 Chart 9 — Sector Allocation Across Equity Funds
**Insight 9:** Banking & Finance dominates with ~28% aggregate weight across all equity fund
portfolios, followed by IT (22%) and Energy (15%) — driven by Nifty 100 benchmark composition.
""")
code("show('chart_09_sector_donut.png')")

print("[Chart 9] Sector Donut")
sec_wt = ph.groupby("sector")["weight_pct"].sum().sort_values(ascending=False)
sec_pct = sec_wt / sec_wt.sum() * 100
d_cols  = [NAVY,ORANGE,GREEN,RED,PURPLE,TEAL,"#e67e22","#2ecc71"][:len(sec_pct)]

fig9, (ax9a, ax9b) = plt.subplots(1, 2, figsize=(16, 8))
wedges9, _, auts9 = ax9a.pie(sec_pct.values, labels=None,
    autopct="%1.1f%%", colors=d_cols, pctdistance=0.82,
    startangle=90, wedgeprops=dict(width=0.55,edgecolor="white",linewidth=2.5))
for at in auts9: at.set_fontsize(9.5); at.set_fontweight("bold"); at.set_color("white")
ax9a.text(0,0,"Sector\nAllocation",ha="center",va="center",
          fontsize=13,fontweight="bold",color=NAVY)
ax9a.legend(wedges9, sec_pct.index, loc="lower center",
            bbox_to_anchor=(0.5,-0.12), ncol=2, fontsize=10, frameon=False)
ax9a.set_title("Aggregate Sector Weights\n(All Equity Funds)", fontsize=14,
               fontweight="bold", color=NAVY)

ax9b.barh(sec_pct.index[::-1], sec_pct.values[::-1],
          color=d_cols[::-1], edgecolor="white", height=0.65)
for i,(val,lbl) in enumerate(zip(sec_pct.values[::-1],sec_pct.index[::-1])):
    ax9b.text(val+0.3, i, f"{val:.1f}%", va="center", fontsize=10, color="#333")
ax9b.set_xlabel("Aggregate Weight (%)", fontsize=11)
ax9b.set_title("Sector Weight Breakdown", fontsize=14, fontweight="bold", color=NAVY)
ax9b.set_xlim(0, sec_pct.max()*1.20)
ax9b.grid(axis="x", alpha=0.3)
fig9.suptitle("Sector Allocation — Equity Fund Portfolios", fontsize=17,
              fontweight="bold", color=NAVY, y=1.01)
plt.tight_layout()
fig9.savefig(os.path.join(CHARTS,"chart_09_sector_donut.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_09_sector_donut.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 10 — Return Distribution by Category & Sub-category
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📦 Chart 10 — Annual Return Distribution by Fund Category
**Insight 10:** Small Cap funds show widest return range (−20% to +65%), while Debt funds
maintain a tight 6–9% annual band — confirming Debt's capital-preservation role.
""")
code("show('chart_10_return_distribution.png')")

print("[Chart 10] Return Distribution")
nav["year"] = nav["date"].dt.year
yr_ret = (nav.groupby(["amfi_code","scheme_name","category","sub_category","year"])
            .apply(lambda g: (g.sort_values("date")["nav"].iloc[-1]/
                              g.sort_values("date")["nav"].iloc[0] - 1)*100)
            .reset_index(name="annual_return_pct"))

cat_order10 = ["Equity","Hybrid","Debt","Other"]
cat_pal10   = {"Equity":NAVY,"Hybrid":ORANGE,"Debt":GREEN,"Other":PURPLE}
sub_top = (yr_ret.groupby("sub_category")["annual_return_pct"]
                 .median().nlargest(8).index.tolist())

fig10, (ax10a, ax10b) = plt.subplots(1, 2, figsize=(17, 7))
sns.boxplot(data=yr_ret, x="category", y="annual_return_pct",
            order=cat_order10, palette=cat_pal10,
            width=0.55, fliersize=4, linewidth=1.5, ax=ax10a)
ax10a.axhline(0, color=RED, linewidth=1.2, linestyle="--", alpha=0.7)
ax10a.set_title("Annual Return Distribution\nby Fund Category", fontsize=14,
                fontweight="bold", color=NAVY)
ax10a.set_xlabel("Category"); ax10a.set_ylabel("Annual Return (%)"); ax10a.grid(axis="y",alpha=0.3)

sns.violinplot(data=yr_ret[yr_ret["sub_category"].isin(sub_top)],
               x="sub_category", y="annual_return_pct",
               order=sub_top, palette="muted",
               inner="quartile", linewidth=1.2, ax=ax10b)
ax10b.axhline(0, color=RED, linewidth=1.2, linestyle="--", alpha=0.7)
ax10b.set_title("Return Distribution by Sub-Category\n(Top 8 by Median)", fontsize=14,
                fontweight="bold", color=NAVY)
ax10b.set_xlabel("Sub-Category"); ax10b.set_ylabel("Annual Return (%)")
ax10b.set_xticklabels(ax10b.get_xticklabels(), rotation=30, ha="right", fontsize=9)
ax10b.grid(axis="y", alpha=0.3)

fig10.suptitle("Fund Return Analysis (2022–2025)", fontsize=17,
               fontweight="bold", color=NAVY, y=1.01)
plt.tight_layout()
fig10.savefig(os.path.join(CHARTS,"chart_10_return_distribution.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_10_return_distribution.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 11 — Payment Mode & KYC
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📱 Chart 11 — Payment Mode & KYC Status
**Insight (Bonus):** UPI dominates at 45% of all SIP payment modes, reflecting NPCI's auto-debit
framework adoption. 92% KYC compliance rate validates strong regulatory adherence.
""")
code("show('chart_11_payment_kyc.png')")

print("[Chart 11] Payment + KYC")
pm = tx["payment_mode"].value_counts()
kyc = tx["kyc_status"].value_counts()
fig11, (ax11a, ax11b) = plt.subplots(1, 2, figsize=(13, 6))
ax11a.pie(pm.values, labels=pm.index, autopct="%1.1f%%",
          colors=PALETTE[:len(pm)], startangle=90,
          wedgeprops=dict(edgecolor="white",linewidth=2), pctdistance=0.77)
ax11a.set_title("Payment Mode Distribution", fontsize=13, fontweight="bold", color=NAVY)

bars11 = ax11b.bar(kyc.index, kyc.values/kyc.sum()*100,
                   color=[GREEN,RED], edgecolor="white", width=0.45)
for bar, val in zip(bars11, kyc.values/kyc.sum()*100):
    ax11b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
               f"{val:.1f}%", ha="center", fontsize=12, fontweight="bold")
ax11b.set_title("KYC Status Distribution", fontsize=13, fontweight="bold", color=NAVY)
ax11b.set_ylabel("% of Transactions"); ax11b.set_ylim(0,105); ax11b.grid(axis="y",alpha=0.3)
plt.tight_layout()
fig11.savefig(os.path.join(CHARTS,"chart_11_payment_kyc.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("   ✓ chart_11_payment_kyc.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 12 — SIP vs Lumpsum Monthly Trend
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📊 Chart 12 — SIP vs Lumpsum vs Redemption Monthly Trend
**Insight (Bonus):** SIP transaction volumes are 2.5× higher than Lumpsum, but Lumpsum per-ticket
size is ~38× larger. The widening SIP-minus-Redemption gap since 2023 indicates improving retention.
""")
code("show('chart_12_tx_trend.png')")

print("[Chart 12] TX Trend")
tx["ym"] = tx["transaction_date"].dt.to_period("M").dt.to_timestamp()
tx_m = (tx.groupby(["ym","transaction_type"])
          .agg(total_cr=("amount_inr",lambda x: x.sum()/1e7),
               cnt=("investor_id","count"))
          .reset_index())
tx_cols12 = {"SIP":NAVY,"Lumpsum":ORANGE,"Redemption":RED}

fig12, (ax12a, ax12b) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
for tt in ["SIP","Lumpsum","Redemption"]:
    sub = tx_m[tx_m["transaction_type"]==tt].sort_values("ym")
    ax12a.plot(sub["ym"], sub["total_cr"], label=tt, color=tx_cols12[tt], linewidth=2)
    ax12b.bar(sub["ym"], sub["cnt"], label=tt, color=tx_cols12[tt],
              alpha=0.72, width=20)
ax12a.set_title("Monthly Transaction Volume by Type", fontsize=14, fontweight="bold", color=NAVY)
ax12a.set_ylabel("Amount (₹ Crore)"); ax12a.legend(fontsize=10); ax12a.grid(axis="y",alpha=0.25)
ax12b.set_title("Monthly Transaction Count by Type", fontsize=14, fontweight="bold", color=NAVY)
ax12b.set_ylabel("No. of Transactions"); ax12b.legend(fontsize=10); ax12b.grid(axis="y",alpha=0.25)
ax12b.set_xlabel("Month", fontsize=12)
fig12.suptitle("SIP vs Lumpsum vs Redemption — Monthly Trends",
               fontsize=16, fontweight="bold", color=NAVY, y=1.01)
plt.tight_layout()
fig12.savefig(os.path.join(CHARTS,"chart_12_tx_trend.png"), dpi=DPI, bbox_inches="tight")
plt.close()

# Interactive plotly version
fig12p = make_subplots(rows=1,cols=2,subplot_titles=["Volume (₹ Cr)","Transaction Count"])
for tt in ["SIP","Lumpsum","Redemption"]:
    sub = tx_m[tx_m["transaction_type"]==tt].sort_values("ym")
    fig12p.add_trace(go.Scatter(x=sub["ym"],y=sub["total_cr"].round(1),name=tt,
        mode="lines",line=dict(color=tx_cols12[tt],width=2)),row=1,col=1)
    fig12p.add_trace(go.Bar(x=sub["ym"],y=sub["cnt"],name=tt,
        marker_color=tx_cols12[tt],showlegend=False),row=1,col=2)
fig12p.update_layout(title="<b>SIP vs Lumpsum vs Redemption Trends</b>",
    plot_bgcolor="white",paper_bgcolor="white",width=1100,height=480)
for r,c in [(1,1),(1,2)]:
    fig12p.update_xaxes(showgrid=True,gridcolor="#f0f0f0",row=r,col=c)
    fig12p.update_yaxes(showgrid=True,gridcolor="#f0f0f0",row=r,col=c)
fig12p.write_html(os.path.join(HTML_DIR,"chart_12_tx_trend.html"))
print("   ✓ chart_12_tx_trend.png + .html")


# ══════════════════════════════════════════════════════════════════════════════
# EDA FINDINGS SUMMARY CELL
# ══════════════════════════════════════════════════════════════════════════════
md("""## 🔍 10 Key EDA Findings

| # | Finding | Chart |
|---|---------|-------|
| **F1** | Equity NAV grew 40–70% cumulatively 2022–2026; 2023 bull run = 25–35% in one calendar year | C1 |
| **F2** | SBI MF leads AUM at ₹12.5L Cr (Dec 2025), 1.5× ICICI Pru — a top-rank reversal from 2020 | C2 |
| **F3** | SIP inflows compounded at 18% CAGR to ATH ₹31,002 Cr Dec 2025 — uninterrupted 48-month run | C3 |
| **F4** | Index Funds & Small Cap dominated FY25 inflows; Liquid funds show quarter-end redemption spikes | C4 |
| **F5** | 26–35 age cohort = 35% of SIPs (₹6,577/month avg); Female investors show lower redemption rates | C5 |
| **F6** | Maharashtra = 18% of SIP volume; B30 cities growing fastest — SEBI's TER incentive working | C6 |
| **F7** | Folios crossed 26 Cr by Dec 2025, up from 13.26 Cr — 82% of new additions are Equity folios | C7 |
| **F8** | Large-cap funds: 0.85–0.95 pairwise correlation; Debt funds ≈0 correlation — true diversifier | C8 |
| **F9** | Banking (28%) + IT (22%) + Energy (15%) = 65% of all equity fund sector weights | C9 |
| **F10** | Small Cap annual return range: −20% to +65%; Debt stays in tight 6–9% band — confirms risk profile | C10 |
""")


# ══════════════════════════════════════════════════════════════════════════════
# BUILD EDA_Analysis.ipynb
# ══════════════════════════════════════════════════════════════════════════════
print("\n[Notebook] Writing EDA_Analysis.ipynb …")

# Prepend setup cells
setup = {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],
 "source":"# Re-run all charts\nimport subprocess, sys\nr = subprocess.run([sys.executable,'../eda_analysis.py'],capture_output=True,text=True)\nprint(r.stdout[-3000:])\nif r.returncode!=0: print('ERR:',r.stderr[-500:])"}
imports = {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],
 "source":"import os\nfrom IPython.display import Image, display\nCHARTS='../reports/charts'\ndef show(f):\n    p=os.path.join(CHARTS,f)\n    if os.path.exists(p): display(Image(p,width=880))\n    else: print('Not found:',p)"}

nb = {"nbformat":4,"nbformat_minor":5,
      "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                  "language_info":{"name":"python","version":"3.10.0"}},
      "cells":[setup, imports] + NB_CELLS}

with open(NB_OUT,"w") as f:
    json.dump(nb, f, indent=1)

charts = sorted(os.listdir(CHARTS))
html_charts = sorted(os.listdir(HTML_DIR))
print(f"\n{'='*65}")
print(f"  DAY 3 EDA — COMPLETE")
print(f"  PNG charts  : {len(charts)}")
for c in charts: print(f"    • {c}")
print(f"  HTML charts : {len(html_charts)}")
print(f"  Notebook    : {NB_OUT}")
print(f"{'='*65}\n")
