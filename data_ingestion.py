"""
data_ingestion.py
=================
Day 1 — Mutual Fund Analytics Project
Loads all CSV datasets, inspects schemas, and reports anomalies.

Usage:
    python data_ingestion.py

Outputs:
    - Console report with .shape, .dtypes, .head() for each dataset
    - data/processed/data_quality_report.txt
    - data/processed/<name>_cleaned.csv for each dataset
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from datetime import datetime

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RAW_DIR     = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR    = os.path.join(BASE_DIR, "data", "processed")
REPORT_PATH = os.path.join(PROC_DIR, "data_quality_report.txt")

os.makedirs(RAW_DIR,  exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

# ── Expected datasets ──────────────────────────────────────────────────────────
# If real CSVs exist in data/raw/ they will be loaded; otherwise synthetic
# data is generated so the pipeline runs end-to-end from Day 1.
EXPECTED_DATASETS = [
    "fund_master",
    "nav_history",
    "fund_returns",
    "portfolio_holdings",
    "aum_data",
    "expense_ratios",
    "benchmark_index",
    "sip_data",
    "redemption_data",
    "investor_demographics",
]

# ── Synthetic data generators ──────────────────────────────────────────────────
def _make_fund_master(n=200):
    np.random.seed(0)
    fund_houses   = ["HDFC", "SBI", "ICICI Prudential", "Nippon India",
                     "Axis", "Kotak Mahindra", "Mirae Asset", "DSP", "Aditya Birla", "UTI"]
    categories    = ["Equity", "Debt", "Hybrid", "Solution Oriented", "Other"]
    sub_cats      = {"Equity": ["Large Cap", "Mid Cap", "Small Cap", "Multi Cap", "ELSS", "Sectoral"],
                     "Debt":   ["Liquid", "Ultra Short", "Short Duration", "Corporate Bond", "Gilt"],
                     "Hybrid": ["Aggressive", "Conservative", "Balanced Advantage"],
                     "Solution Oriented": ["Retirement", "Children's"],
                     "Other": ["Index Fund", "ETF", "FoF"]}
    risk_grades   = ["Low", "Moderately Low", "Moderate", "Moderately High", "High", "Very High"]

    rows = []
    for i in range(n):
        cat  = np.random.choice(categories)
        scat = np.random.choice(sub_cats[cat])
        fh   = np.random.choice(fund_houses)
        code = 100000 + i * 100 + np.random.randint(0, 99)
        rows.append({
            "amfi_code":       code,
            "scheme_name":     f"{fh} {scat} Direct Plan Growth",
            "fund_house":      fh,
            "category":        cat,
            "sub_category":    scat,
            "risk_grade":      np.random.choice(risk_grades),
            "launch_date":     pd.Timestamp("2010-01-01") + pd.Timedelta(days=int(np.random.randint(0, 3650))),
            "benchmark":       f"NIFTY {scat.split()[0]} 100 TRI",
            "aum_crores":      round(np.random.exponential(2000), 2),
            "exit_load_pct":   round(np.random.choice([0.0, 0.5, 1.0, 1.5]), 2),
            "lock_in_days":    int(np.random.choice([0, 0, 0, 365, 1095])),
        })
    df = pd.DataFrame(rows)
    # Intentional anomaly: a few duplicate amfi_codes
    df.loc[df.index[-3:], "amfi_code"] = df["amfi_code"].iloc[0]
    return df

def _make_nav_history(fund_master):
    np.random.seed(1)
    from datetime import timedelta
    rows = []
    codes = fund_master["amfi_code"].unique()[:50]          # 50 funds × 365 days
    base_date = datetime(2024, 1, 1)
    for code in codes:
        nav = np.random.uniform(20, 1000)
        for d in range(365):
            nav = max(nav * (1 + np.random.normal(0.0004, 0.009)), 5)
            dt  = base_date + timedelta(days=d)
            if dt.weekday() < 5:                            # weekdays only
                rows.append({"amfi_code": code,
                              "nav_date":  dt.strftime("%d-%m-%Y"),
                              "nav":       round(nav, 4),
                              "change_pct": round(np.random.normal(0.04, 0.9), 4)})
    return pd.DataFrame(rows)

def _make_fund_returns(fund_master):
    np.random.seed(2)
    codes = fund_master["amfi_code"].unique()
    rows  = []
    for code in codes:
        rows.append({
            "amfi_code":        code,
            "return_1m":        round(np.random.normal(1.2, 3.0), 2),
            "return_3m":        round(np.random.normal(3.5, 5.0), 2),
            "return_6m":        round(np.random.normal(6.0, 7.0), 2),
            "return_1y":        round(np.random.normal(12.0, 12.0), 2),
            "return_3y":        round(np.random.normal(11.0, 6.0), 2),
            "return_5y":        round(np.random.normal(13.0, 5.0), 2),
            "alpha":            round(np.random.normal(0.5, 2.0), 4),
            "beta":             round(np.random.uniform(0.6, 1.4), 4),
            "sharpe_ratio":     round(np.random.normal(0.8, 0.5), 4),
            "std_deviation":    round(np.random.uniform(5, 25), 4),
        })
    return pd.DataFrame(rows)

def _make_portfolio_holdings(fund_master):
    np.random.seed(3)
    stocks = ["Reliance Industries", "TCS", "HDFC Bank", "Infosys", "ICICI Bank",
              "Kotak Bank", "L&T", "ITC", "Bharti Airtel", "HUL"]
    rows = []
    for code in fund_master["amfi_code"].unique()[:30]:
        n_stocks = np.random.randint(10, 30)
        weights  = np.random.dirichlet(np.ones(n_stocks)) * 100
        selected = np.random.choice(stocks + [f"Stock_{i}" for i in range(50)], n_stocks, replace=False)
        for s, w in zip(selected, weights):
            rows.append({"amfi_code": code, "stock_name": s, "weight_pct": round(w, 4),
                          "sector": np.random.choice(["IT", "Banking", "Energy", "FMCG", "Auto"])})
    return pd.DataFrame(rows)

def _make_aum_data(fund_master):
    np.random.seed(4)
    months = pd.date_range("2023-01-01", periods=18, freq="MS")
    rows   = []
    for code in fund_master["amfi_code"].unique():
        aum = np.random.exponential(2000)
        for m in months:
            aum = max(aum * (1 + np.random.normal(0.015, 0.05)), 1)
            rows.append({"amfi_code": code, "month": m.strftime("%Y-%m"),
                          "aum_crores": round(aum, 2), "folio_count": int(np.random.randint(500, 500000))})
    return pd.DataFrame(rows)

def _make_expense_ratios(fund_master):
    np.random.seed(5)
    rows = []
    for code in fund_master["amfi_code"].unique():
        cat = fund_master.loc[fund_master["amfi_code"] == code, "category"].values[0]
        base = {"Equity": 1.0, "Debt": 0.6, "Hybrid": 0.9, "Solution Oriented": 1.2, "Other": 0.4}.get(cat, 0.8)
        rows.append({"amfi_code": code,
                      "expense_ratio_direct": round(base + np.random.uniform(-0.3, 0.5), 4),
                      "expense_ratio_regular": round(base + np.random.uniform(0.5, 1.5), 4),
                      "tter": round(np.random.uniform(0.01, 0.15), 4),
                      "as_of_date": "2024-12-31"})
    return pd.DataFrame(rows)

def _make_benchmark_index():
    np.random.seed(6)
    from datetime import timedelta
    indices = ["NIFTY 50 TRI", "NIFTY 100 TRI", "NIFTY Midcap 150 TRI",
               "BSE Sensex TRI", "NIFTY IT TRI", "CRISIL Short Duration"]
    rows    = []
    base    = datetime(2024, 1, 1)
    for idx in indices:
        val = np.random.uniform(5000, 25000)
        for d in range(365):
            val = max(val * (1 + np.random.normal(0.0003, 0.008)), 1000)
            dt  = base + timedelta(days=d)
            if dt.weekday() < 5:
                rows.append({"index_name": idx, "date": dt.strftime("%d-%m-%Y"),
                              "close_value": round(val, 2),
                              "daily_return": round(np.random.normal(0.03, 0.8), 4)})
    return pd.DataFrame(rows)

def _make_sip_data(fund_master):
    np.random.seed(7)
    rows = []
    for code in fund_master["amfi_code"].unique()[:80]:
        for month in pd.date_range("2023-01-01", periods=18, freq="MS"):
            rows.append({"amfi_code": code, "month": month.strftime("%Y-%m"),
                          "sip_inflows_cr": round(np.random.exponential(10), 2),
                          "sip_registrations": int(np.random.randint(100, 50000)),
                          "sip_cancellations": int(np.random.randint(10, 5000))})
    return pd.DataFrame(rows)

def _make_redemption_data(fund_master):
    np.random.seed(8)
    rows = []
    for code in fund_master["amfi_code"].unique()[:80]:
        for month in pd.date_range("2023-01-01", periods=18, freq="MS"):
            rows.append({"amfi_code": code, "month": month.strftime("%Y-%m"),
                          "redemption_cr": round(np.random.exponential(8), 2),
                          "lumpsum_inflow_cr": round(np.random.exponential(15), 2),
                          "net_flow_cr": round(np.random.normal(5, 20), 2)})
    return pd.DataFrame(rows)

def _make_investor_demographics():
    np.random.seed(9)
    n = 5000
    return pd.DataFrame({
        "investor_id":   range(1, n + 1),
        "age_group":     np.random.choice(["18-25", "26-35", "36-45", "46-55", "55+"], n),
        "city_tier":     np.random.choice(["Tier 1", "Tier 2", "Tier 3"], n, p=[0.5, 0.3, 0.2]),
        "risk_appetite": np.random.choice(["Conservative", "Moderate", "Aggressive"], n),
        "investment_cr": np.round(np.random.exponential(0.5, n), 4),
        "tenure_years":  np.round(np.random.exponential(3, n), 1),
        "channel":       np.random.choice(["Direct", "Distributor", "Bank", "Online"], n),
        "gender":        np.random.choice(["M", "F", "None"], n, p=[0.58, 0.40, 0.02]),
    })

GENERATORS = {
    "fund_master":          _make_fund_master,
    "nav_history":          lambda: _make_nav_history(_datasets.get("fund_master")),
    "fund_returns":         lambda: _make_fund_returns(_datasets.get("fund_master")),
    "portfolio_holdings":   lambda: _make_portfolio_holdings(_datasets.get("fund_master")),
    "aum_data":             lambda: _make_aum_data(_datasets.get("fund_master")),
    "expense_ratios":       lambda: _make_expense_ratios(_datasets.get("fund_master")),
    "benchmark_index":      _make_benchmark_index,
    "sip_data":             lambda: _make_sip_data(_datasets.get("fund_master")),
    "redemption_data":      lambda: _make_redemption_data(_datasets.get("fund_master")),
    "investor_demographics": _make_investor_demographics,
}

_datasets = {}   # filled during load phase

# ── Anomaly detector ───────────────────────────────────────────────────────────
def detect_anomalies(name: str, df: pd.DataFrame) -> list[str]:
    issues = []

    null_pct = df.isnull().mean() * 100
    high_null = null_pct[null_pct > 5]
    if not high_null.empty:
        for col, pct in high_null.items():
            issues.append(f"  ⚠  High nulls: '{col}' has {pct:.1f}% missing values")

    for col in df.select_dtypes(include=[np.number]).columns:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        outliers = ((s < q1 - 3 * iqr) | (s > q3 + 3 * iqr)).sum()
        if outliers > 0:
            issues.append(f"  ⚠  Outliers: '{col}' has {outliers} extreme values (3×IQR)")

    dup_rows = df.duplicated().sum()
    if dup_rows:
        issues.append(f"  ⚠  {dup_rows} fully duplicate rows found")

    if "amfi_code" in df.columns:
        dups = df["amfi_code"].duplicated().sum()
        if dups:
            issues.append(f"  ⚠  {dups} duplicate amfi_code values")

    neg_num = []
    for col in ["nav", "aum_crores", "expense_ratio_direct", "expense_ratio_regular"]:
        if col in df.columns:
            n_neg = (df[col] < 0).sum()
            if n_neg:
                neg_num.append(f"'{col}': {n_neg} negatives")
    if neg_num:
        issues.append(f"  ⚠  Unexpected negatives: {', '.join(neg_num)}")

    if not issues:
        issues.append("  ✓  No critical anomalies detected")
    return issues

# ── Main ingestion routine ─────────────────────────────────────────────────────
def load_datasets() -> dict[str, pd.DataFrame]:
    print("=" * 70)
    print("  MUTUAL FUND ANALYTICS — DAY 1: DATA INGESTION")
    print(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    report_lines = [
        "DATA QUALITY REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
    ]

    datasets = {}

    for name in EXPECTED_DATASETS:
        csv_path = os.path.join(RAW_DIR, f"{name}.csv")

        # ── Load (real CSV if present, else synthesise) ────────────────────
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            source = "CSV (provided)"
        else:
            gen = GENERATORS.get(name)
            if gen is None:
                print(f"\n[SKIP] No generator for '{name}' and no CSV found.\n")
                continue
            df = gen()
            df.to_csv(csv_path, index=False)
            source = "Synthetic (generated)"

        datasets[name] = df
        _datasets[name] = df

        # ── Console report ─────────────────────────────────────────────────
        sep = "-" * 70
        print(f"\n{'━' * 70}")
        print(f"  Dataset : {name.upper()}")
        print(f"  Source  : {source}")
        print(f"  Path    : {csv_path}")
        print(f"{'━' * 70}")
        print(f"\n  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns\n")

        print("  dtypes:")
        for col, dtype in df.dtypes.items():
            null_info = f"  ({df[col].isnull().sum():,} nulls)" if df[col].isnull().any() else ""
            print(f"    {col:<35} {str(dtype):<12}{null_info}")

        print(f"\n  head(3):\n{df.head(3).to_string(index=False)}\n")

        anomalies = detect_anomalies(name, df)
        print("  Anomaly scan:")
        for a in anomalies:
            print(a)

        # ── Write cleaned copy ─────────────────────────────────────────────
        clean_path = os.path.join(PROC_DIR, f"{name}_cleaned.csv")
        df_clean   = df.drop_duplicates()
        df_clean.to_csv(clean_path, index=False)

        # ── Accumulate report ──────────────────────────────────────────────
        report_lines += [
            "",
            f"DATASET: {name}",
            f"  Source  : {source}",
            f"  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns",
            f"  Columns : {', '.join(df.columns.tolist())}",
            "  Anomalies:",
        ] + anomalies

    # ── AMFI code validation ───────────────────────────────────────────────
    print(f"\n{'━' * 70}")
    print("  AMFI CODE VALIDATION")
    print(f"{'━' * 70}")

    fm  = datasets.get("fund_master")
    nav = datasets.get("nav_history")

    if fm is not None and nav is not None:
        master_codes = set(fm["amfi_code"].unique())
        nav_codes    = set(nav["amfi_code"].unique())
        matched      = master_codes & nav_codes
        unmatched    = master_codes - nav_codes
        extra_in_nav = nav_codes - master_codes

        print(f"\n  Fund master codes : {len(master_codes):,}")
        print(f"  NAV history codes : {len(nav_codes):,}")
        print(f"  Matched           : {len(matched):,}")
        print(f"  In master, NOT nav: {len(unmatched):,}")
        print(f"  In nav, NOT master: {len(extra_in_nav):,}")

        if unmatched:
            sample = list(unmatched)[:5]
            print(f"  Sample unmatched  : {sample}")

        report_lines += [
            "",
            "AMFI CODE VALIDATION",
            f"  Fund master codes : {len(master_codes)}",
            f"  NAV history codes : {len(nav_codes)}",
            f"  Matched           : {len(matched)}",
            f"  In master, NOT nav: {len(unmatched)} (coverage gap)",
            f"  In nav, NOT master: {len(extra_in_nav)} (orphan NAV records)",
        ]

    # ── Fund master exploration (Step 6) ───────────────────────────────────
    if fm is not None:
        print(f"\n{'━' * 70}")
        print("  FUND MASTER — EXPLORATION")
        print(f"{'━' * 70}")
        print(f"\n  Unique fund houses  : {fm['fund_house'].nunique()}")
        print(f"  Fund houses         : {sorted(fm['fund_house'].unique())}")
        print(f"\n  Categories          : {sorted(fm['category'].unique())}")
        print(f"\n  Sub-categories      : {sorted(fm['sub_category'].unique())}")
        print(f"\n  Risk grades         : {sorted(fm['risk_grade'].unique())}")

        print(f"\n  Category distribution:")
        for cat, cnt in fm["category"].value_counts().items():
            print(f"    {cat:<30} {cnt:>4} schemes")

        print(f"\n  AMFI code range     : {fm['amfi_code'].min()} – {fm['amfi_code'].max()}")
        print(f"  AMFI code note      : 6-digit codes assigned sequentially by AMFI")
        print(f"                        each Direct / Regular / Growth / Dividend variant")
        print(f"                        gets its own unique code.")

    # ── Save report ────────────────────────────────────────────────────────
    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\n{'=' * 70}")
    print(f"  Data quality report saved → {REPORT_PATH}")
    print(f"  Cleaned CSVs saved        → {PROC_DIR}/")
    print(f"{'=' * 70}\n")

    return datasets


if __name__ == "__main__":
    load_datasets()
