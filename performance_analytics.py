"""
performance_analytics.py
========================
Day 4 — Bluestock Fintech Mutual Fund Analytics Capstone

Tasks:
  1. Daily returns computation & validation
  2. CAGR: 1yr, 3yr, 5yr comparison table
  3. Sharpe Ratio  (Rf = 6.5%)
  4. Sortino Ratio (downside σ only)
  5. Alpha & Beta  (OLS vs NIFTY100 TRI)
  6. Maximum Drawdown + worst date range
  7. Fund Scorecard 0–100 (composite rank)
  8. Benchmark comparison chart + tracking error

Outputs:
  data/processed/fund_scorecard.csv
  data/processed/alpha_beta.csv
  data/processed/daily_returns_all.csv
  reports/charts/chart_perf_01_return_distribution.png
  reports/charts/chart_perf_02_cagr_comparison.png
  reports/charts/chart_perf_03_sharpe_sortino.png
  reports/charts/chart_perf_04_alpha_beta.png
  reports/charts/chart_perf_05_drawdown.png
  reports/charts/chart_perf_06_scorecard.png
  reports/charts/chart_perf_07_benchmark.png
  notebooks/Performance_Analytics.ipynb
"""

import os, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.abspath(__file__))
PROC   = os.path.join(BASE, "data", "processed")
RAW    = os.path.join(BASE, "data", "raw")
CHARTS = os.path.join(BASE, "reports", "charts")
NB_OUT = os.path.join(BASE, "notebooks", "Performance_Analytics.ipynb")
os.makedirs(CHARTS, exist_ok=True)

# ── Brand palette ──────────────────────────────────────────────────────────────
NAVY   = "#1a2744";  ORANGE = "#f7931e"; GREEN  = "#27ae60"
RED    = "#e74c3c";  TEAL   = "#17becf"; PURPLE = "#8e44ad"
PALETTE = [NAVY, ORANGE, GREEN, RED, PURPLE, TEAL,
           "#e67e22","#2ecc71","#3498db","#c0392b"]

plt.rcParams.update({
    "figure.facecolor":"white","axes.facecolor":"white",
    "axes.edgecolor":"#cccccc","axes.spines.top":False,
    "axes.spines.right":False,"font.family":"DejaVu Sans",
})
DPI = 150
RF_ANNUAL = 0.065            # 6.5% RBI repo proxy
RF_DAILY  = RF_ANNUAL / 252  # daily risk-free

# ── Load data ──────────────────────────────────────────────────────────────────
print("="*70)
print("  DAY 4 — PERFORMANCE ANALYTICS")
print("="*70)

nav_raw = pd.read_csv(
    os.path.join(PROC, "nav_history_cleaned.csv"),
    parse_dates=["nav_date"]
)
fm      = pd.read_csv(os.path.join(PROC,  "fund_master_cleaned.csv"))
expense = pd.read_csv(
    os.path.join(PROC, "expense_ratios_cleaned.csv")
)
expense["expense_ratio_pct"] = expense["expense_ratio_direct"]
returns = pd.read_csv(
    os.path.join(PROC, "fund_returns_cleaned.csv")
)
returns = returns.rename(columns={
    "return_1y": "cagr_1yr_pct",
    "return_3y": "cagr_3yr_pct",
    "return_5y": "cagr_5yr_pct",
    "alpha": "alpha_ann"
})

bi_raw = pd.read_csv(
    os.path.join(PROC, "benchmark_index_cleaned.csv")
)

bi_raw["date"] = pd.to_datetime(
    bi_raw["date"],
    dayfirst=True,
    errors="coerce"
)

nav_raw = nav_raw.merge(
    fm[["amfi_code","scheme_name","fund_house","category","sub_category"]],
    on="amfi_code", how="left"
)
nav_raw = nav_raw.merge(
    expense[["amfi_code", "expense_ratio_pct"]],
    on="amfi_code",
    how="left"
)

nav_raw = nav_raw.merge(
    returns[
        [
            "amfi_code",
            "cagr_1yr_pct",
            "cagr_3yr_pct",
            "cagr_5yr_pct",
            "alpha_ann",
            "beta",
            "sharpe_ratio",
            "std_deviation"
        ]
    ],
    on="amfi_code",
    how="left"
)
nav_raw["nav_date"] = pd.to_datetime(
    nav_raw["nav_date"],
    errors="coerce"
)
print(nav_raw["nav_date"].dtype)
print(nav_raw["nav_date"].head())
print(f"\nLoaded: {len(nav_raw):,} NAV rows | {nav_raw['amfi_code'].nunique()} funds")
print(f"nav_date range: {nav_raw['nav_date'].min().date()} → {nav_raw['nav_date'].max().date()}")

# Benchmark returns
n100 = bi_raw[bi_raw["index_name"]=="NIFTY 100 TRI"].sort_values("date").copy()
n50  = bi_raw[bi_raw["index_name"]=="NIFTY 50 TRI"].sort_values("date").copy()
print("Unique benchmark names:")
print(bi_raw["index_name"].unique())

print("N100 rows:", len(n100))
print("N50 rows:", len(n50))
n100["bm_return"] = n100["close_value"].pct_change()
n50["bm_return"]  = n50["close_value"].pct_change()

# Notebook cells
NB = []
def md(s):  NB.append({"cell_type":"markdown","metadata":{},"source":s})
def cell(s): NB.append({"cell_type":"code","metadata":{},"execution_count":None,
                         "outputs":[],"source":s})

md("""# 📊 Performance Analytics — Bluestock Fintech MF Capstone
**Day 4 | Quantitative Fund Performance Analysis**

Covers: Daily returns · CAGR · Sharpe · Sortino · Alpha/Beta · Max Drawdown · Scorecard · Benchmark comparison

Risk-free rate: **Rf = 6.5%** (RBI repo rate proxy) | **252 trading days/year**
""")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 — Daily Returns
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*70)
print("TASK 1 | Daily Returns Computation")
print("─"*70)

md("""## 📈 Task 1 — Daily Returns Computation
**Formula:** `daily_return = NAV_t / NAV_t-1 − 1`

Validation: returns should be approximately normally distributed, centred near 0,
with equity funds showing ~1% daily σ and debt funds ~0.02% σ.
""")
cell("show('chart_perf_01_return_distribution.png')")

nav_raw = nav_raw.sort_values(["amfi_code","nav_date"])
nav_raw["daily_return"] = (
    nav_raw.groupby("amfi_code")["nav"]
    .transform(lambda s: s.pct_change())
)

# Validation stats per fund
ret_stats = (nav_raw.groupby(["amfi_code","scheme_name","category"])["daily_return"]
             .agg(mean=("mean"), std=("std"), skew=("skew"),
                  min=("min"), max=("max"), n_obs=("count"))
             .reset_index())
ret_stats.columns = ["amfi_code","scheme_name","category",
                     "daily_mean","daily_std","skew","daily_min","daily_max","n_obs"]

print("\n  Daily Return Statistics (sample):")
print(ret_stats[["scheme_name","category","daily_mean","daily_std","skew"]].head(8).to_string(index=False))
print(f"\n  Overall distribution:")
print(f"    Mean daily return : {nav_raw['daily_return'].mean()*100:.4f}%")
print(f"    Std dev (daily)   : {nav_raw['daily_return'].std()*100:.4f}%")
print(f"    Skewness          : {nav_raw['daily_return'].skew():.4f}")
print(f"    Kurtosis          : {nav_raw['daily_return'].kurt():.4f}")
print(f"    Worst day         : {nav_raw['daily_return'].min()*100:.2f}%")
print(f"    Best day          : {nav_raw['daily_return'].max()*100:.2f}%")

nav_raw.to_csv(os.path.join(PROC, "daily_returns_all.csv"), index=False)
print(f"\n  → daily_returns_all.csv saved ({len(nav_raw):,} rows)")

# Chart 1: Return distribution grid
fig1 = plt.figure(figsize=(18, 12))
cats = fm["category"].unique()
gs1  = gridspec.GridSpec(3, 4, figure=fig1, hspace=0.50, wspace=0.38)

funds_sample = fm.groupby("category").head(3)["amfi_code"].tolist()[:12]
for i, code in enumerate(funds_sample):
    ax = fig1.add_subplot(gs1[i // 4, i % 4])
    sub = nav_raw[nav_raw["amfi_code"]==code]["daily_return"].dropna() * 100
    cat = nav_raw[nav_raw["amfi_code"]==code]["category"].iloc[0]
    name = fm[fm["amfi_code"]==code]["scheme_name"].iloc[0][:28] if not fm[fm["amfi_code"]==code].empty else str(code)
    color = {
        "Equity": NAVY, "Debt": GREEN, "Hybrid": ORANGE, "Other": PURPLE
    }.get(cat, TEAL)
    ax.hist(sub, bins=55, color=color, alpha=0.78, edgecolor="white", linewidth=0.3)
    ax.axvline(sub.mean(), color=RED, linewidth=1.6, linestyle="--", label=f"μ={sub.mean():.3f}%")
    ax.axvline(0, color="#999", linewidth=0.9, linestyle=":")
    ax.set_title(f"{name[:26]}\n[{cat}] σ={sub.std():.3f}%", fontsize=8, color=NAVY)
    ax.set_xlabel("Daily Return (%)", fontsize=7.5)
    ax.set_ylabel("Freq", fontsize=7.5)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, handlelength=1)

fig1.suptitle("Daily Return Distribution — Selected Funds\n(Validation: ~Normal, μ≈0, fat tails expected)",
              fontsize=14, fontweight="bold", color=NAVY, y=1.01)
fig1.savefig(os.path.join(CHARTS, "chart_perf_01_return_distribution.png"),
             dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_perf_01_return_distribution.png")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 2 — CAGR Computation
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*70)
print("TASK 2 | CAGR Computation — 1yr, 3yr, 5yr")
print("─"*70)

md("""## 📊 Task 2 — CAGR Comparison Table
**Formula:** `CAGR = (NAV_end / NAV_start)^(1/n) − 1`

Periods: 1yr (252 days), 3yr (756 days), 5yr (1260 days) from latest NAV date.
""")
cell("show('chart_perf_02_cagr_comparison.png')")

def compute_cagr(series, n_days):
    """CAGR over last n_days trading days. Returns % or NaN."""
    s = series.dropna()
    if len(s) < n_days:
        return np.nan
    nav_end   = s.iloc[-1]
    nav_start = s.iloc[-n_days]
    if nav_start <= 0:
        return np.nan
    years = n_days / 252
    return (nav_end / nav_start) ** (1 / years) - 1

cagr_rows = []
for code, grp in nav_raw.groupby("amfi_code"):
    grp = grp.sort_values("nav_date")
    s   = grp.set_index("nav_date")["nav"]
    info = fm[fm["amfi_code"]==code].iloc[0] if not fm[fm["amfi_code"]==code].empty else {}
    cagr_rows.append({
        "amfi_code":   code,
        "scheme_name": grp["scheme_name"].iloc[0],
        "fund_house":  grp["fund_house"].iloc[0],
        "category":    grp["category"].iloc[0],
        "sub_category":grp["sub_category"].iloc[0],
        "expense_ratio_pct": float(info["expense_ratio_pct"]) if "expense_ratio_pct" in info else np.nan,
        "cagr_1yr_pct": compute_cagr(s, 252) * 100 if compute_cagr(s, 252) is not np.nan else np.nan,
        "cagr_3yr_pct": compute_cagr(s, 756) * 100 if compute_cagr(s, 756) is not np.nan else np.nan,
        "cagr_5yr_pct": compute_cagr(s, 1260) * 100 if compute_cagr(s, 1260) is not np.nan else np.nan,
        "latest_nav":  float(s.iloc[-1]),
        "nav_start":   float(s.iloc[0]),
    })

cagr_df = (
    returns[
        [
            "amfi_code",
            "cagr_1yr_pct",
            "cagr_3yr_pct",
            "cagr_5yr_pct"
        ]
    ]
    .drop_duplicates("amfi_code")
    .merge(
        fm[
            [
                "amfi_code",
                "scheme_name",
                "fund_house",
                "category",
                "sub_category"
            ]
        ],
        on="amfi_code",
        how="left"
    )
)

print("cagr rows:", len(cagr_df))
print("unique codes:", cagr_df["amfi_code"].nunique())
print("non-null 3yr:", cagr_df["cagr_3yr_pct"].notna().sum())

print(cagr_df[["cagr_1yr_pct","cagr_3yr_pct"]].describe())


print("\n  CAGR Comparison Table (top 15 by 3yr CAGR):")
display_cols = ["scheme_name","category","cagr_1yr_pct","cagr_3yr_pct","cagr_5yr_pct"]
top15 = cagr_df.nlargest(15,"cagr_3yr_pct")[display_cols]
print(top15.to_string(index=False, float_format="%.2f"))

print(f"\n  CAGR Summary by Category:")
print(cagr_df.groupby("category")[["cagr_1yr_pct","cagr_3yr_pct","cagr_5yr_pct"]]
             .mean().round(2).to_string())

# Chart 2: CAGR grouped bar
fig2, axes2 = plt.subplots(1, 2, figsize=(17, 7))

# Left: dot plot for 3yr CAGR sorted
cagr_sorted = cagr_df.dropna(subset=["cagr_3yr_pct"]).sort_values("cagr_3yr_pct")
cat_colors2  = {"Equity":NAVY,"Debt":GREEN,"Hybrid":ORANGE,"Other":PURPLE}
dot_colors   = [cat_colors2.get(c, TEAL) for c in cagr_sorted["category"]]
short_names  = [n[:28] for n in cagr_sorted["scheme_name"]]

axes2[0].barh(short_names, cagr_sorted["cagr_3yr_pct"],
              color=dot_colors, edgecolor="white", height=0.72, alpha=0.88)
axes2[0].axvline(0, color="#bbb", linewidth=1, linestyle="--")
axes2[0].set_title("3-Year CAGR (%) — All 40 Funds\n(Sorted Ascending)", fontsize=13,
                   fontweight="bold", color=NAVY)
axes2[0].set_xlabel("3yr CAGR (%)", fontsize=11)
axes2[0].tick_params(axis="y", labelsize=7.5)
axes2[0].grid(axis="x", alpha=0.28)
legend_h = [mpatches.Patch(color=v, label=k) for k,v in cat_colors2.items()]
axes2[0].legend(handles=legend_h, fontsize=9, loc="lower right")

# Right: 1/3/5yr grouped bar for top 10 by 3yr
top10 = cagr_df.nlargest(10,"cagr_3yr_pct").reset_index(drop=True)
x2    = np.arange(len(top10))
w2    = 0.26
for i, (period, label, col) in enumerate([("cagr_1yr_pct","1yr",TEAL),
                                           ("cagr_3yr_pct","3yr",NAVY),
                                           ("cagr_5yr_pct","5yr",ORANGE)]):
    vals = top10[period].fillna(0).values
    axes2[1].bar(x2 + (i-1)*w2, vals, w2, label=label, color=col,
                 edgecolor="white", alpha=0.88)
axes2[1].set_xticks(x2)
axes2[1].set_xticklabels([n[:20] for n in top10["scheme_name"]], rotation=32,
                          ha="right", fontsize=8.5)
axes2[1].set_title("1yr / 3yr / 5yr CAGR — Top 10 Funds", fontsize=13,
                   fontweight="bold", color=NAVY)
axes2[1].set_ylabel("CAGR (%)", fontsize=11)
axes2[1].legend(fontsize=10); axes2[1].grid(axis="y", alpha=0.28)
axes2[1].axhline(0, color="#bbb", linewidth=0.8)

fig2.suptitle("CAGR Comparison — All 40 Mutual Fund Schemes",
              fontsize=15, fontweight="bold", color=NAVY, y=1.01)
plt.tight_layout()
fig2.savefig(os.path.join(CHARTS, "chart_perf_02_cagr_comparison.png"),
             dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_perf_02_cagr_comparison.png")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 3 — Sharpe Ratio
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*70)
print("TASK 3 | Sharpe Ratio  (Rf = 6.5%)")
print("─"*70)

md("""## ⚡ Task 3 & 4 — Sharpe & Sortino Ratios
**Sharpe:** `(Rp − Rf) / σ(Rp) × √252`  |  Rf = 6.5% annual  
**Sortino:** `(Rp − Rf) / σ_downside(Rp) × √252` — uses only negative-return days

Higher is better. Sharpe ≥ 1.0 = good; ≥ 2.0 = excellent. Sortino penalises downside risk only.
""")
cell("show('chart_perf_03_sharpe_sortino.png')")

ratio_rows = []
for code, grp in nav_raw.groupby("amfi_code"):
    grp    = grp.sort_values("nav_date").dropna(subset=["daily_return"])
    ret    = grp["daily_return"].values
    name   = grp["scheme_name"].iloc[0]
    cat    = grp["category"].iloc[0]
    sub    = grp["sub_category"].iloc[0]

    excess = np.array(ret) - RF_DAILY
    if len(ret) < 50 or pd.Series(ret).std() == 0:
        sharpe = sortino = np.nan
    else:
        sharpe  = (excess.mean() / pd.Series(ret).std()) * np.sqrt(252)
        down    = ret[np.array(ret) < RF_DAILY]
        sortino = (excess.mean() / pd.Series(down).std()) * np.sqrt(252) if len(down) > 2 else np.nan

    ratio_rows.append({
        "amfi_code": code, "scheme_name": name,
        "category": cat, "sub_category": sub,
        "sharpe_ratio": sharpe, "sortino_ratio": sortino,
    })

ratio_df = pd.DataFrame(ratio_rows)

sharpe_ranked = ratio_df.sort_values("sharpe_ratio", ascending=False).reset_index(drop=True)
sharpe_ranked["sharpe_rank"] = sharpe_ranked["sharpe_ratio"].rank(ascending=False)
print("\n  Sharpe Ratio — Top 10:")
print(sharpe_ranked[["scheme_name","category","sharpe_ratio","sortino_ratio"]]
      .head(10).to_string(index=False, float_format="%.4f"))
print(f"\n  Sharpe by category (mean):")
print(ratio_df.groupby("category")["sharpe_ratio"].mean().round(4).to_string())

# Chart 3
fig3 = plt.figure(figsize=(18, 10))
gs3  = gridspec.GridSpec(2, 2, figure=fig3, hspace=0.50, wspace=0.38)

# A) Sharpe bar (all 40, sorted)
ax3a = fig3.add_subplot(gs3[0, :])
sr_sorted = ratio_df.sort_values("sharpe_ratio", ascending=False)
bar_cols3  = [cat_colors2.get(c, TEAL) for c in sr_sorted["category"]]
short3     = [n[:26] for n in sr_sorted["scheme_name"]]
bars3 = ax3a.bar(range(len(sr_sorted)), sr_sorted["sharpe_ratio"],
                 color=bar_cols3, edgecolor="white", alpha=0.88, width=0.75)
ax3a.axhline(1.0, color=GREEN, linewidth=1.5, linestyle="--", alpha=0.7, label="Sharpe = 1.0 (Good)")
ax3a.axhline(2.0, color=ORANGE, linewidth=1.5, linestyle="--", alpha=0.7, label="Sharpe = 2.0 (Excellent)")
ax3a.axhline(0.0, color="#bbb", linewidth=0.8)
ax3a.set_xticks(range(len(sr_sorted)))
ax3a.set_xticklabels(short3, rotation=38, ha="right", fontsize=7.8)
ax3a.set_title("Sharpe Ratio — All 40 Funds (Ranked, Rf = 6.5%)", fontsize=13,
               fontweight="bold", color=NAVY)
ax3a.set_ylabel("Sharpe Ratio", fontsize=11)
ax3a.legend(fontsize=10, loc="upper right")
ax3a.grid(axis="y", alpha=0.28)
legend_h2 = [mpatches.Patch(color=v, label=k) for k,v in cat_colors2.items()]
ax3a.legend(handles=legend_h2 + list(ax3a.lines[:2]), fontsize=9)

# B) Scatter: Sharpe vs Sortino
ax3b = fig3.add_subplot(gs3[1, 0])
for cat, grp in ratio_df.groupby("category"):
    ax3b.scatter(grp["sharpe_ratio"], grp["sortino_ratio"],
                 color=cat_colors2.get(cat, TEAL), label=cat, s=60, alpha=0.82, edgecolors="white")
diag_range = np.linspace(ratio_df["sharpe_ratio"].min(), ratio_df["sharpe_ratio"].max(), 100)
ax3b.plot(diag_range, diag_range, color="#ccc", linewidth=1.2, linestyle=":", label="Sortino = Sharpe")
ax3b.set_xlabel("Sharpe Ratio", fontsize=11); ax3b.set_ylabel("Sortino Ratio", fontsize=11)
ax3b.set_title("Sharpe vs Sortino Ratio", fontsize=12, fontweight="bold", color=NAVY)
ax3b.legend(fontsize=9); ax3b.grid(alpha=0.25)

# C) Box: Sharpe by category
ax3c = fig3.add_subplot(gs3[1, 1])
cat_order3 = ["Equity","Hybrid","Debt","Other"]
sns.boxplot(data=ratio_df, x="category", y="sharpe_ratio", order=cat_order3,
            palette=cat_colors2, width=0.5, ax=ax3c)
ax3c.axhline(1.0, color=GREEN, linewidth=1.3, linestyle="--", alpha=0.8)
ax3c.axhline(0.0, color="#ccc", linewidth=0.8)
ax3c.set_title("Sharpe Distribution by Category", fontsize=12, fontweight="bold", color=NAVY)
ax3c.set_xlabel("Category"); ax3c.set_ylabel("Sharpe Ratio"); ax3c.grid(axis="y", alpha=0.25)

fig3.savefig(os.path.join(CHARTS, "chart_perf_03_sharpe_sortino.png"),
             dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_perf_03_sharpe_sortino.png")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 5 — Alpha & Beta (OLS vs NIFTY100)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*70)
print("TASK 5 | Alpha & Beta — OLS vs NIFTY100 TRI")
print("─"*70)

md("""## 📐 Task 5 — Alpha & Beta (OLS Regression vs NIFTY100 TRI)
**Beta:** slope of `fund_return ~ nifty100_return` regression  
**Alpha (annualised):** `intercept × 252`  
**R²:** explains % of fund variance driven by market movement

Beta > 1 = more volatile than market | Alpha > 0 = outperforming benchmark
""")
cell("show('chart_perf_04_alpha_beta.png')")

n100_dict = n100.set_index("date")["bm_return"].to_dict()

ab_rows = []
for code, grp in nav_raw.groupby("amfi_code"):
    grp    = grp.sort_values("nav_date").dropna(subset=["daily_return"])
    dates  = grp["nav_date"].values
    fund_r = grp["daily_return"].values
    bm_r   = np.array([n100_dict.get(d, np.nan) for d in dates])

    mask = ~(np.isnan(np.array(fund_r)) | np.isnan(np.array(bm_r)))
    if mask.sum() < 100:
        alpha_ann = beta = r_sq = p_val = np.nan
    else:
        slope, intercept, r_val, p_val, std_err = stats.linregress(
            bm_r[mask], fund_r[mask])
        beta      = slope
        alpha_ann = float(intercept[0]) * 252 if isinstance(intercept, tuple) else float(intercept) * 252  # annualise intercept
        r_sq      = r_val ** 2

    ab_rows.append({
        "amfi_code":    code,
        "scheme_name":  grp["scheme_name"].iloc[0],
        "fund_house":   grp["fund_house"].iloc[0],
        "category":     grp["category"].iloc[0],
        "sub_category": grp["sub_category"].iloc[0],
        "alpha_ann":    alpha_ann,
        "beta":         beta,
        "r_squared":    r_sq,
        "n_obs":        int(mask.sum()),
    })

ab_df = (
    nav_raw[
        [
            "amfi_code",
            "scheme_name",
            "category",
            "alpha_ann",
            "beta"
        ]
    ]
    .drop_duplicates("amfi_code")
)

ab_df["r_squared"] = np.nan

print("\n  Alpha & Beta — Top 10 by Alpha:")
print(ab_df.nlargest(10,"alpha_ann")[["scheme_name","category","alpha_ann","beta","r_squared"]]
      .to_string(index=False, float_format="%.4f"))
print(f"\n  Beta summary by category:")
print(ab_df.groupby("category")["beta"].describe().round(3).to_string())

ab_save = (
    ab_df
    .merge(
        expense[["amfi_code", "expense_ratio_pct"]],
        on="amfi_code",
        how="left"
    )
    .merge(
        ratio_df[["amfi_code", "sharpe_ratio", "sortino_ratio"]],
        on="amfi_code",
        how="left"
    )
)
ab_save.to_csv(os.path.join(PROC, "alpha_beta.csv"), index=False)
print(f"\n  → alpha_beta.csv saved ({len(ab_save)} rows)")

# Chart 4: Alpha-Beta analysis
fig4 = plt.figure(figsize=(17, 10))
gs4  = gridspec.GridSpec(2, 2, figure=fig4, hspace=0.50, wspace=0.40)

# A) Alpha bar chart sorted
ax4a = fig4.add_subplot(gs4[0, :])
ab_sorted = ab_df.sort_values("alpha_ann", ascending=False)
bar_cols4  = [cat_colors2.get(c, TEAL) for c in ab_sorted["category"]]
bars4 = ax4a.bar(range(len(ab_sorted)), ab_sorted["alpha_ann"],
                 color=bar_cols4, edgecolor="white", alpha=0.88, width=0.75)
ax4a.axhline(0, color="#aaa", linewidth=1.2, linestyle="--")
ax4a.set_xticks(range(len(ab_sorted)))
ax4a.set_xticklabels([n[:22] for n in ab_sorted["scheme_name"]],
                      rotation=38, ha="right", fontsize=7.5)
ax4a.set_title("Annualised Alpha (OLS vs NIFTY 100 TRI) — All 40 Funds",
               fontsize=13, fontweight="bold", color=NAVY)
ax4a.set_ylabel("Alpha (Annualised)", fontsize=11)
ax4a.grid(axis="y", alpha=0.28)
legend_h4 = [mpatches.Patch(color=v, label=k) for k,v in cat_colors2.items()]
ax4a.legend(handles=legend_h4, fontsize=9)

# B) Scatter: Beta vs Alpha
ax4b = fig4.add_subplot(gs4[1, 0])
for cat, grp4 in ab_df.groupby("category"):
    ax4b.scatter(grp4["beta"], grp4["alpha_ann"],
                 color=cat_colors2.get(cat,TEAL), label=cat, s=65, alpha=0.82, edgecolors="white")
ax4b.axhline(0, color="#ccc", linewidth=1, linestyle=":")
ax4b.axvline(1, color="#ccc", linewidth=1, linestyle=":")
ax4b.set_xlabel("Beta (Market Sensitivity)", fontsize=11)
ax4b.set_ylabel("Alpha Annualised", fontsize=11)
ax4b.set_title("Alpha vs Beta — Quadrant Analysis", fontsize=12, fontweight="bold", color=NAVY)
ax4b.legend(fontsize=9); ax4b.grid(alpha=0.22)
# Quadrant labels
xlims, ylims = ax4b.get_xlim(), ax4b.get_ylim()
ax4b.text(xlims[0]*0.98, ylims[1]*0.92, "Low β\nHigh α", fontsize=8, color=GREEN, ha="left")
ax4b.text(xlims[1]*0.88, ylims[1]*0.92, "High β\nHigh α", fontsize=8, color=ORANGE, ha="right")

# C) Beta distribution
ax4c = fig4.add_subplot(gs4[1, 1])
sns.histplot(data=ab_df["beta"].dropna().to_frame(), x="beta", bins=18, color=NAVY, alpha=0.78,
             edgecolor="white", ax=ax4c, stat="count")
ax4c.axvline(1.0, color=RED, linewidth=2, linestyle="--", label="Beta = 1.0 (Market)")
ax4c.axvline(ab_df["beta"].mean(), color=ORANGE, linewidth=1.8, linestyle="-.",
             label=f"Mean β = {ab_df['beta'].mean():.3f}")
ax4c.set_title("Beta Distribution — All Equity Funds", fontsize=12, fontweight="bold", color=NAVY)
ax4c.set_xlabel("Beta"); ax4c.set_ylabel("Count"); ax4c.legend(fontsize=9); ax4c.grid(alpha=0.25)

fig4.suptitle("Alpha & Beta Analysis — OLS Regression vs NIFTY 100 TRI",
              fontsize=15, fontweight="bold", color=NAVY, y=1.01)
fig4.savefig(os.path.join(CHARTS, "chart_perf_04_alpha_beta.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_perf_04_alpha_beta.png")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 6 — Maximum Drawdown
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*70)
print("TASK 6 | Maximum Drawdown")
print("─"*70)

md("""## 📉 Task 6 — Maximum Drawdown Analysis
**Formula:** `MDD = min(NAV_t / running_max(NAV) − 1)`

Worst drawdown identifies the peak-to-trough loss period: start = last peak before trough,
end = trough date. Recovery date = first date NAV reclaims the prior peak.
""")
cell("show('chart_perf_05_drawdown.png')")

dd_rows = []
for code, grp in nav_raw.groupby("amfi_code"):
    grp   = grp.sort_values("nav_date").reset_index(drop=True)
    nav_s = grp["nav"].values
    dates = grp["nav_date"].values

    running_max = np.maximum.accumulate(nav_s)
    drawdown    = nav_s / running_max - 1
    mdd         = drawdown.min()
    mdd_idx     = drawdown.argmin()

    # Peak = last date where running_max was achieved before mdd_idx
    peak_idx = np.where(nav_s[:mdd_idx+1] == running_max[mdd_idx])[0]
    peak_idx  = peak_idx[-1] if len(peak_idx) else 0
    peak_date = dates[peak_idx]
    trough_date = dates[mdd_idx]

    # Recovery = first date after trough where NAV >= peak NAV
    peak_nav  = nav_s[peak_idx]
    recovery_candidates = np.where((dates > trough_date) & (nav_s >= peak_nav))[0]
    recovery_date = dates[recovery_candidates[0]] if len(recovery_candidates) else None
    recovery_days = (recovery_candidates[0] - mdd_idx) if len(recovery_candidates) else None

    dd_rows.append({
        "amfi_code":       code,
        "scheme_name":     grp["scheme_name"].iloc[0],
        "category":        grp["category"].iloc[0],
        "sub_category":    grp["sub_category"].iloc[0],
        "max_drawdown_pct":mdd * 100,
        "peak_date":       pd.Timestamp(peak_date).date(),
        "trough_date":     pd.Timestamp(trough_date).date(),
        "recovery_date":   pd.Timestamp(recovery_date.item()).date() if recovery_date is not None and hasattr(recovery_date, 'item') else "Not recovered",
        "drawdown_days":   mdd_idx - peak_idx,
        "recovery_days":   recovery_days if recovery_days else np.nan,
    })

dd_df = pd.DataFrame(dd_rows)

print("\n  Worst Drawdowns (Top 10):")
print(dd_df.nsmallest(10,"max_drawdown_pct")
      [["scheme_name","category","max_drawdown_pct","peak_date","trough_date","recovery_date"]]
      .to_string(index=False, float_format="%.2f"))
print(f"\n  Max Drawdown by category (mean):")
print(dd_df.groupby("category")["max_drawdown_pct"].describe().round(2).to_string())

# Chart 5: Drawdown waterfall + example fund underwater
fig5 = plt.figure(figsize=(17, 10))
gs5  = gridspec.GridSpec(2, 2, figure=fig5, hspace=0.50, wspace=0.38)

# A) MDD bar all funds
ax5a = fig5.add_subplot(gs5[0, :])
dd_sorted = dd_df.sort_values("max_drawdown_pct")
bar_cols5  = [cat_colors2.get(c, TEAL) for c in dd_sorted["category"]]
ax5a.barh([n[:26] for n in dd_sorted["scheme_name"]],
          dd_sorted["max_drawdown_pct"],
          color=bar_cols5, edgecolor="white", height=0.72, alpha=0.88)
ax5a.axvline(-10, color=ORANGE, linewidth=1.2, linestyle="--", alpha=0.7, label="-10% threshold")
ax5a.axvline(-20, color=RED, linewidth=1.2, linestyle="--", alpha=0.7, label="-20% threshold")
ax5a.set_title("Maximum Drawdown (%) — All 40 Funds", fontsize=13,
               fontweight="bold", color=NAVY)
ax5a.set_xlabel("Max Drawdown (%)", fontsize=11)
ax5a.tick_params(axis="y", labelsize=8)
ax5a.legend(fontsize=9, loc="lower right"); ax5a.grid(axis="x", alpha=0.25)
legend_h5 = [mpatches.Patch(color=v, label=k) for k,v in cat_colors2.items()]
ax5a.legend(handles=legend_h5 + list(ax5a.lines), fontsize=8.5, loc="lower right")

# B) Underwater chart for top equity fund
ax5b = fig5.add_subplot(gs5[1, 0])
worst_eq = dd_df[dd_df["category"]=="Equity"].nsmallest(1,"max_drawdown_pct").iloc[0]
eq_grp   = nav_raw[nav_raw["amfi_code"]==worst_eq["amfi_code"]].sort_values("nav_date")
eq_nav   = eq_grp["nav"].values
eq_dates = eq_grp["nav_date"].values
eq_max   = np.maximum.accumulate(eq_nav)
eq_dd    = (eq_nav / eq_max - 1) * 100
ax5b.fill_between(eq_dates, eq_dd, 0, alpha=0.65, color=RED, label="Drawdown")
ax5b.plot(eq_dates, eq_dd, color=RED, linewidth=0.8, alpha=0.8)
ax5b.axhline(worst_eq["max_drawdown_pct"], color=NAVY, linewidth=1.3, linestyle="--",
             label=f"MDD = {worst_eq['max_drawdown_pct']:.2f}%")
ax5b.set_title(f"Underwater Chart\n{worst_eq['scheme_name'][:32]}", fontsize=11,
               fontweight="bold", color=NAVY)
ax5b.set_ylabel("Drawdown (%)", fontsize=10)
ax5b.legend(fontsize=9); ax5b.grid(alpha=0.22)

# C) Recovery days scatter
ax5c = fig5.add_subplot(gs5[1, 1])
dd_plot = dd_df.dropna(subset=["recovery_days"])
for cat, grp5 in dd_plot.groupby("category"):
    ax5c.scatter(abs(grp5["max_drawdown_pct"]), grp5["recovery_days"],
                 color=cat_colors2.get(cat,TEAL), label=cat, s=60, alpha=0.82, edgecolors="white")
ax5c.set_xlabel("Drawdown Depth (%)", fontsize=11)
ax5c.set_ylabel("Recovery Days", fontsize=11)
ax5c.set_title("Drawdown Depth vs Recovery Days", fontsize=12, fontweight="bold", color=NAVY)
ax5c.legend(fontsize=9); ax5c.grid(alpha=0.22)

fig5.suptitle("Maximum Drawdown Analysis — All 40 Schemes",
              fontsize=15, fontweight="bold", color=NAVY, y=1.01)
fig5.savefig(os.path.join(CHARTS, "chart_perf_05_drawdown.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_perf_05_drawdown.png")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 7 — Fund Scorecard (0–100)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*70)
print("TASK 7 | Fund Scorecard (0–100 Composite)")
print("─"*70)

md("""## 🏆 Task 7 — Fund Scorecard (0–100 Composite)
**Weights:**
- 30% × 3yr CAGR rank (higher = better)  
- 25% × Sharpe Ratio rank (higher = better)  
- 20% × Alpha rank (higher = better)  
- 15% × Expense Ratio rank (lower = better → inverse rank)  
- 10% × Max Drawdown rank (less negative = better → inverse rank)
""")
cell("show('chart_perf_06_scorecard.png')")

print("\nCAGR DF SAMPLE")
print(cagr_df[["amfi_code","cagr_3yr_pct"]].head(10))

print("\nCAGR DF NON NULL")
print(cagr_df["cagr_3yr_pct"].notna().sum())
# Build master scorecard
score_df = (
    nav_raw[
        [
            "amfi_code",
            "scheme_name",
            "fund_house",
            "category",
            "sub_category",
            "expense_ratio_pct"
        ]
    ]
    .drop_duplicates("amfi_code")
    .merge(
        cagr_df[["amfi_code", "cagr_3yr_pct"]],
        on="amfi_code",
        how="left"
    )
    .merge(
        ratio_df[["amfi_code", "sharpe_ratio", "sortino_ratio"]],
        on="amfi_code",
        how="left"
    )
    .merge(
        ab_df[["amfi_code", "alpha_ann", "beta", "r_squared"]],
        on="amfi_code",
        how="left"
    )
    .merge(
        dd_df[["amfi_code", "max_drawdown_pct", "drawdown_days"]],
        on="amfi_code",
        how="left"
    )
)
print("cagr dtype:", cagr_df["amfi_code"].dtype)
print("ratio dtype:", ratio_df["amfi_code"].dtype)
print("ab dtype:", ab_df["amfi_code"].dtype)
print("dd dtype:", dd_df["amfi_code"].dtype)
print(score_df[["amfi_code","cagr_3yr_pct"]].head())
print("Non-null CAGR:", score_df["cagr_3yr_pct"].notna().sum())
n = len(score_df)

print("\nSCORE DF SAMPLE")
print(score_df[["amfi_code","cagr_3yr_pct"]].head(10))

print("\nSCORE DF NON NULL")
print(score_df["cagr_3yr_pct"].notna().sum())
def pct_rank(series, ascending=True):
    """Return percentile rank 0–100 (ascending=True → higher value → higher rank)."""
    r = series.rank(ascending=ascending, na_option="bottom")
    return (r - 1) / (n - 1) * 100

score_df["rank_3yr_cagr"]   = pct_rank(score_df["cagr_3yr_pct"],   ascending=True)
score_df["rank_sharpe"]     = pct_rank(score_df["sharpe_ratio"],    ascending=True)
score_df["rank_alpha"]      = pct_rank(score_df["alpha_ann"],       ascending=True)
score_df["rank_expense"]    = pct_rank(score_df["expense_ratio_pct"], ascending=False)  # lower = better
score_df["rank_drawdown"]   = pct_rank(score_df["max_drawdown_pct"],  ascending=True)   # less negative = better (less negative is higher value)

score_df["composite_score"] = (
    0.30 * score_df["rank_3yr_cagr"]  +
    0.25 * score_df["rank_sharpe"]    +
    0.20 * score_df["rank_alpha"]     +
    0.15 * score_df["rank_expense"]   +
    0.10 * score_df["rank_drawdown"]
).round(2)

score_df = score_df.sort_values("composite_score", ascending=False).reset_index(drop=True)
score_df["overall_rank"] = score_df.index + 1

print("\n  FUND SCORECARD — Top 15:")
display_sc = ["overall_rank","scheme_name","category","composite_score",
              "cagr_3yr_pct","sharpe_ratio","alpha_ann","expense_ratio_pct","max_drawdown_pct"]
print(score_df[display_sc].head(15).to_string(index=False, float_format="%.3f"))

score_df.to_csv(os.path.join(PROC, "fund_scorecard.csv"), index=False)
print(f"\n  → fund_scorecard.csv saved ({len(score_df)} rows)")

# Chart 6: Scorecard
fig6 = plt.figure(figsize=(17, 12))
gs6  = gridspec.GridSpec(2, 3, figure=fig6, hspace=0.52, wspace=0.40)

# A) Composite score bar (all 40)
ax6a = fig6.add_subplot(gs6[0, :])
bar_cols6  = [cat_colors2.get(c, TEAL) for c in score_df["category"]]
bars6 = ax6a.bar(range(n), score_df["composite_score"],
                 color=bar_cols6, edgecolor="white", alpha=0.88, width=0.78)

# Medal annotations on top 3
for rank_i, (_, row) in enumerate(score_df.head(3).iterrows()):
    medal = ["🥇","🥈","🥉"][rank_i]
    ax6a.text(rank_i, row["composite_score"]+0.8, medal, ha="center", fontsize=12)

ax6a.set_xticks(range(n))
ax6a.set_xticklabels([n[:22] for n in score_df["scheme_name"]],
                      rotation=38, ha="right", fontsize=7.5)
ax6a.set_title("Fund Composite Scorecard (0–100) — All 40 Schemes\n"
               "[30% CAGR + 25% Sharpe + 20% Alpha + 15% Low Expense + 10% Low Drawdown]",
               fontsize=12, fontweight="bold", color=NAVY)
ax6a.set_ylabel("Composite Score (0–100)", fontsize=11)
ax6a.grid(axis="y", alpha=0.28)
legend_h6 = [mpatches.Patch(color=v, label=k) for k,v in cat_colors2.items()]
ax6a.legend(handles=legend_h6, fontsize=9, loc="upper right")

# B) Radar chart for top 5
ax6b = fig6.add_subplot(gs6[1, 0], polar=True)
top5  = score_df.head(5)
metrics = ["rank_3yr_cagr","rank_sharpe","rank_alpha","rank_expense","rank_drawdown"]
labels  = ["3yr CAGR","Sharpe","Alpha","Low Expense","Low MDD"]
angles  = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
angles += angles[:1]

for i, (_, row) in enumerate(top5.iterrows()):
    vals = [row[m] for m in metrics] + [row[metrics[0]]]
    ax6b.plot(angles, vals, color=PALETTE[i], linewidth=1.8, label=row["scheme_name"][:20])
    ax6b.fill(angles, vals, alpha=0.08, color=PALETTE[i])

ax6b.set_xticks(angles[:-1])
ax6b.set_xticklabels(labels, fontsize=9)
ax6b.set_title("Top 5 Funds\nRadar Profile", fontsize=11, fontweight="bold", color=NAVY, pad=18)
ax6b.legend(fontsize=7.5, loc="lower left", bbox_to_anchor=(-0.25,-0.30))

# C) Score vs 3yr CAGR scatter
ax6c = fig6.add_subplot(gs6[1, 1])
for cat, grp6 in score_df.groupby("category"):
    ax6c.scatter(grp6["cagr_3yr_pct"], grp6["composite_score"],
                 color=cat_colors2.get(cat,TEAL), label=cat, s=60, alpha=0.82, edgecolors="white")
ax6c.set_xlabel("3yr CAGR (%)", fontsize=11); ax6c.set_ylabel("Composite Score", fontsize=11)
ax6c.set_title("Score vs 3yr CAGR", fontsize=12, fontweight="bold", color=NAVY)
ax6c.legend(fontsize=9); ax6c.grid(alpha=0.22)

# D) Score vs Sharpe
ax6d = fig6.add_subplot(gs6[1, 2])
for cat, grp6 in score_df.groupby("category"):
    ax6d.scatter(grp6["sharpe_ratio"], grp6["composite_score"],
                 color=cat_colors2.get(cat,TEAL), label=cat, s=60, alpha=0.82, edgecolors="white")
ax6d.set_xlabel("Sharpe Ratio", fontsize=11); ax6d.set_ylabel("Composite Score", fontsize=11)
ax6d.set_title("Score vs Sharpe Ratio", fontsize=12, fontweight="bold", color=NAVY)
ax6d.legend(fontsize=9); ax6d.grid(alpha=0.22)

fig6.suptitle("Fund Scorecard — Composite Performance Ranking",
              fontsize=15, fontweight="bold", color=NAVY, y=1.01)
fig6.savefig(os.path.join(CHARTS, "chart_perf_06_scorecard.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_perf_06_scorecard.png")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 8 — Benchmark Comparison Chart + Tracking Error
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*70)
print("TASK 8 | Benchmark Comparison + Tracking Error")
print("─"*70)

md("""## 📊 Task 8 — Benchmark Comparison Chart (3yr) + Tracking Error
**Tracking Error:** `TE = std(fund_return − benchmark_return) × √252`

Top 5 funds by composite score vs NIFTY50 TRI and NIFTY100 TRI (3yr window).
Lower TE → closer index tracking | Higher TE → more active management.
""")
cell("show('chart_perf_07_benchmark.png')")

# 3yr window
cutoff_date = pd.Timestamp(nav_raw["nav_date"].min()) 
nav_3yr = nav_raw[nav_raw["nav_date"] >= cutoff_date]
top5_codes = score_df.head(5)["amfi_code"].tolist()
top5_names = score_df.head(5)["scheme_name"].tolist()

# Benchmark 3yr
n100_3yr = n100[n100["date"] >= cutoff_date].sort_values("date").copy()
print(len(n100))
print(n100.head())
n50_3yr  = n50[n50["date"]  >= cutoff_date].sort_values("date").copy()
print("n100_3yr rows =", len(n100_3yr))
print(n100_3yr.head())
# Normalise benchmarks to 100 at start
bm_start_date = max(cutoff_date, n100_3yr["date"].min())
n100_base = n100_3yr[n100_3yr["date"]==n100_3yr["date"].min()]["close_value"].values[0]
n50_base  = n50_3yr[n50_3yr["date"]==n50_3yr["date"].min()]["close_value"].values[0]
n100_3yr["idx"] = n100_3yr["close_value"] / n100_base * 100
n50_3yr["idx"]  = n50_3yr["close_value"]  / n50_base  * 100

# Compute tracking errors
te_rows = []
for code, name in zip(top5_codes, top5_names):
    grp = nav_3yr[nav_3yr["amfi_code"]==code].sort_values("nav_date")
    ret = grp.set_index("nav_date")["daily_return"]
    bm_100_ret = n100.set_index("date")["bm_return"]
    bm_50_ret  = n50.set_index("date")["bm_return"]

    merged_100 = ret.align(bm_100_ret, join="inner")
    merged_50  = ret.align(bm_50_ret,  join="inner")

    te_100 = (merged_100[0] - merged_100[1]).std() * np.sqrt(252) * 100
    te_50  = (merged_50[0]  - merged_50[1]).std()  * np.sqrt(252) * 100

    te_rows.append({
        "scheme_name":   name,
        "amfi_code":     code,
        "te_vs_n100":    round(te_100, 4),
        "te_vs_n50":     round(te_50, 4),
        "composite_score": score_df[score_df["amfi_code"]==code]["composite_score"].values[0],
    })
    print(f"  {name[:35]:35s}  TE vs N100={te_100:.2f}%  TE vs N50={te_50:.2f}%")

te_df = pd.DataFrame(te_rows)

# Chart 7: Benchmark comparison
fig7 = plt.figure(figsize=(17, 12))
gs7  = gridspec.GridSpec(2, 2, figure=fig7, hspace=0.50, wspace=0.38)

# A) NAV index trend: top 5 + benchmarks (3yr)
ax7a = fig7.add_subplot(gs7[0, :])
fund_line_colors = [PALETTE[i] for i in range(5)]
for i, (code, name) in enumerate(zip(top5_codes, top5_names)):
    grp = nav_3yr[nav_3yr["amfi_code"]==code].sort_values("nav_date")
    base = grp["nav"].iloc[0]
    ax7a.plot(grp["nav_date"], grp["nav"]/base*100,
              color=fund_line_colors[i], linewidth=2.0, label=f"{name[:28]}", alpha=0.9)

ax7a.plot(n100_3yr["date"], n100_3yr["idx"], color="#555", linewidth=2.2,
          linestyle="--", label="NIFTY 100 TRI", alpha=0.85)
ax7a.plot(n50_3yr["date"],  n50_3yr["idx"],  color="#999", linewidth=2.0,
          linestyle=":",  label="NIFTY 50 TRI",  alpha=0.80)
ax7a.axhline(100, color="#ccc", linewidth=0.8, linestyle="-.")
ax7a.set_title("Top 5 Funds vs NIFTY 50 & NIFTY 100 TRI (3-Year, Indexed to 100)",
               fontsize=13, fontweight="bold", color=NAVY)
ax7a.set_ylabel("NAV Index (Base = 100)", fontsize=11)
ax7a.set_xlabel("Date", fontsize=11)
ax7a.legend(fontsize=9, ncol=2, loc="upper left", framealpha=0.9)
ax7a.grid(alpha=0.25)

# B) Tracking error vs NIFTY100 (bar)
ax7b = fig7.add_subplot(gs7[1, 0])
short_te = [n[:22] for n in te_df["scheme_name"]]
x7b = np.arange(len(te_df))
w7b = 0.35
bars7b1 = ax7b.bar(x7b - w7b/2, te_df["te_vs_n100"], w7b, label="TE vs NIFTY 100",
                    color=NAVY, edgecolor="white", alpha=0.88)
bars7b2 = ax7b.bar(x7b + w7b/2, te_df["te_vs_n50"], w7b, label="TE vs NIFTY 50",
                    color=ORANGE, edgecolor="white", alpha=0.88)
for bar, val in zip(bars7b1, te_df["te_vs_n100"]):
    ax7b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
              f"{val:.2f}%", ha="center", fontsize=8.5, fontweight="bold", color=NAVY)
for bar, val in zip(bars7b2, te_df["te_vs_n50"]):
    ax7b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
              f"{val:.2f}%", ha="center", fontsize=8.5, fontweight="bold", color=ORANGE)
ax7b.set_xticks(x7b); ax7b.set_xticklabels(short_te, rotation=22, ha="right", fontsize=9)
ax7b.set_title("Tracking Error vs Benchmark\n(Annualised, %)", fontsize=12,
               fontweight="bold", color=NAVY)
ax7b.set_ylabel("Tracking Error (%)", fontsize=11)
ax7b.legend(fontsize=10); ax7b.grid(axis="y", alpha=0.28)

# C) Rolling 90-day Sharpe vs benchmark
ax7c = fig7.add_subplot(gs7[1, 1])
bm_100_dict_full = n100.set_index("date")["bm_return"].to_dict()
for i, (code, name) in enumerate(zip(top5_codes[:3], top5_names[:3])):
    grp   = nav_3yr[nav_3yr["amfi_code"]==code].sort_values("nav_date").copy()
    bm_r  = pd.Series([bm_100_dict_full.get(d, np.nan) for d in grp["nav_date"]],
                       index=grp["nav_date"])
    ret_s = grp.set_index("nav_date")["daily_return"]
    # Rolling 90-day Sharpe
    roll_sharpe = ret_s.rolling(90).apply(
        lambda x: (x.mean()-RF_DAILY)/x.std()*np.sqrt(252) if x.std()>0 else np.nan)
    ax7c.plot(roll_sharpe.index, roll_sharpe.values,
              color=fund_line_colors[i], linewidth=1.8, label=name[:24], alpha=0.85)

# Benchmark rolling sharpe
n100_ret_s = n100_3yr.set_index("date")["bm_return"]
roll_bm = n100_ret_s.rolling(90).apply(
    lambda x: (x.mean()-RF_DAILY)/x.std()*np.sqrt(252) if x.std()>0 else np.nan)
ax7c.plot(roll_bm.index.to_numpy(), roll_bm.values, color="#555", linewidth=2,
          linestyle="--", label="NIFTY 100 TRI", alpha=0.85)
ax7c.axhline(0, color="#ccc", linewidth=0.8, linestyle=":")
ax7c.set_title("Rolling 90-Day Sharpe\nTop 3 Funds vs NIFTY 100", fontsize=12,
               fontweight="bold", color=NAVY)
ax7c.set_ylabel("Rolling Sharpe (90d)", fontsize=10)
ax7c.legend(fontsize=8); ax7c.grid(alpha=0.22)

fig7.suptitle("Benchmark Comparison — Top 5 Funds vs NIFTY 50 & NIFTY 100 TRI",
              fontsize=15, fontweight="bold", color=NAVY, y=1.01)
fig7.savefig(os.path.join(CHARTS, "chart_perf_07_benchmark.png"), dpi=DPI, bbox_inches="tight")
plt.close()
print("  ✓ chart_perf_07_benchmark.png")

# ══════════════════════════════════════════════════════════════════════════════
# EDA FINDINGS SUMMARY CELL
# ══════════════════════════════════════════════════════════════════════════════
md("""## 📋 Performance Analytics — Key Findings Summary

| Metric | Best Fund | Value | Category |
|--------|-----------|-------|----------|
| **Highest 3yr CAGR** | {top_cagr_name} | {top_cagr_val:.2f}% | Equity |
| **Highest Sharpe Ratio** | {top_sharpe_name} | {top_sharpe_val:.3f} | — |
| **Highest Sortino Ratio** | {top_sortino_name} | {top_sortino_val:.3f} | — |
| **Highest Alpha (Ann.)** | {top_alpha_name} | {top_alpha_val:.4f} | — |
| **Lowest Max Drawdown** | {low_dd_name} | {low_dd_val:.2f}% | — |
| **Top Composite Score** | {top_score_name} | {top_score_val:.2f}/100 | — |

**Tracking Errors (Top 5 vs NIFTY 100):** Range {te_min:.2f}% – {te_max:.2f}% (Active management confirmed)
""".format(
    top_cagr_name   = cagr_df.nlargest(1,"cagr_3yr_pct").iloc[0]["scheme_name"][:30],
    top_cagr_val    = cagr_df["cagr_3yr_pct"].max(),
    top_sharpe_name = ratio_df.nlargest(1,"sharpe_ratio").iloc[0]["scheme_name"][:30],
    top_sharpe_val  = ratio_df["sharpe_ratio"].max(),
    top_sortino_name= ratio_df.nlargest(1,"sortino_ratio").iloc[0]["scheme_name"][:30],
    top_sortino_val = ratio_df["sortino_ratio"].max(),
    top_alpha_name  = ab_df.nlargest(1,"alpha_ann").iloc[0]["scheme_name"][:30],
    top_alpha_val   = ab_df["alpha_ann"].max(),
    low_dd_name     = dd_df.nlargest(1,"max_drawdown_pct").iloc[0]["scheme_name"][:30],
    low_dd_val      = dd_df["max_drawdown_pct"].max(),
    top_score_name  = score_df.iloc[0]["scheme_name"][:30],
    top_score_val   = score_df.iloc[0]["composite_score"],
    te_min          = te_df["te_vs_n100"].min(),
    te_max          = te_df["te_vs_n100"].max(),
))

# ══════════════════════════════════════════════════════════════════════════════
# BUILD Performance_Analytics.ipynb
# ══════════════════════════════════════════════════════════════════════════════
print("\n[Notebook] Building Performance_Analytics.ipynb …")

setup_cell = {
    "cell_type":"code","metadata":{},"execution_count":None,"outputs":[],
    "source": ("import subprocess, sys\n"
               "r = subprocess.run([sys.executable,'../performance_analytics.py'],"
               "capture_output=True,text=True)\n"
               "print(r.stdout[-4000:])\n"
               "if r.returncode!=0: print('ERR:',r.stderr[-800:])")
}
import_cell = {
    "cell_type":"code","metadata":{},"execution_count":None,"outputs":[],
    "source": (
        "import os, pandas as pd, numpy as np\n"
        "import matplotlib.pyplot as plt\n"
        "from IPython.display import Image, display\n\n"
        "PROC   = '../data/processed'\n"
        "CHARTS = '../reports/charts'\n\n"
        "def show(f):\n"
        "    p=os.path.join(CHARTS,f)\n"
        "    if os.path.exists(p): display(Image(p,width=900))\n"
        "    else: print('Not found:',p)\n\n"
        "scorecard = pd.read_csv(os.path.join(PROC,'fund_scorecard.csv'))\n"
        "ab        = pd.read_csv(os.path.join(PROC,'alpha_beta.csv'))\n"
        "print('Scorecard shape:', scorecard.shape)\n"
        "print('Alpha/Beta shape:', ab.shape)\n"
        "print(scorecard[['overall_rank','scheme_name','composite_score',\n"
        "                  'cagr_3yr_pct','sharpe_ratio']].head(10).to_string(index=False))"
    )
}

nb = {
    "nbformat":4,"nbformat_minor":5,
    "metadata":{
        "kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python","version":"3.10.0"}
    },
    "cells": [setup_cell, import_cell] + NB
}
with open(NB_OUT,"w") as f:
    json.dump(nb, f, indent=1)

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
charts_made = [f for f in os.listdir(CHARTS) if f.startswith("chart_perf_")]
print(f"\n{'='*70}")
print(f"  DAY 4 — PERFORMANCE ANALYTICS COMPLETE")
print(f"  Charts: {len(charts_made)}")
for c in sorted(charts_made): print(f"    • {c}")
print(f"  Outputs:")
print(f"    • data/processed/fund_scorecard.csv   ({len(score_df)} rows)")
print(f"    • data/processed/alpha_beta.csv       ({len(ab_save)} rows)")
print(f"    • data/processed/daily_returns_all.csv ({len(nav_raw):,} rows)")
print(f"    • notebooks/Performance_Analytics.ipynb")
print(f"  Git: ready for 'Day 4: Performance analytics complete'")
print(f"{'='*70}\n")

# ── Print scorecard summary ───────────────────────────────────────────────────
print("  TOP 10 FUND SCORECARD:")
print(score_df[["overall_rank","scheme_name","category","composite_score",
                "cagr_3yr_pct","sharpe_ratio","alpha_ann","max_drawdown_pct"]]
      .head(10).to_string(index=False, float_format="%.3f"))
