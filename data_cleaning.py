"""
data_cleaning.py
================
Day 2 Task 1-3 — Mutual Fund Analytics Capstone
Cleans all 10 datasets and saves processed versions to data/processed/.

Cleaning operations per dataset:
  nav_history        : parse dates, sort, forward-fill weekends/holidays,
                       deduplicate, validate NAV > 0
  investor_transactions: standardise tx_type, validate amount > 0,
                         fix date formats, check KYC values
  scheme_performance : validate numeric returns, flag negative Sharpe, check expense ratios
  All others         : null handling, type coercion, dedup, range checks

Usage:
    python data_cleaning.py
"""

import os, warnings
import pandas as pd
import numpy as np
from datetime import datetime

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW      = os.path.join(BASE_DIR, "data", "raw")
PROC     = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC, exist_ok=True)

LOG = []
def log(msg):
    print(msg)
    LOG.append(msg)

def save(df, name):
    path = os.path.join(PROC, name)
    df.to_csv(path, index=False)
    log(f"  → Saved {name}  ({df.shape[0]:,} rows × {df.shape[1]} cols)")
    return df

# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — Clean nav_history.csv
# ─────────────────────────────────────────────────────────────────────────────
def clean_nav_history():
    log("\n" + "━"*65)
    log("  TASK 1 | Cleaning nav_history")
    log("━"*65)

    df = pd.read_csv(os.path.join(RAW, "nav_history.csv"))
    log(f"  Raw shape       : {df.shape}")

    # Parse dates
    df["nav_date"] = pd.to_datetime(
      df["nav_date"],
      format="%d-%m-%Y",
      errors="coerce"
   )
    bad_dates = df["nav_date"].isna().sum()
    if bad_dates:
        log(f"  ⚠  Dropped {bad_dates} unparseable nav_dates")
    df = df.dropna(subset=["nav_date"])

    # Validate NAV > 0
    neg_nav = (df["nav"] <= 0).sum()
    if neg_nav:
        log(f"  ⚠  Dropped {neg_nav} rows with NAV ≤ 0")
    df = df[df["nav"] > 0]

    # Sort
    df = df.sort_values(["amfi_code", "nav_date"]).reset_index(drop=True)

    # Deduplicate (keep last)
    before = len(df)
    df = df.drop_duplicates(subset=["amfi_code","nav_date"], keep="last")
    log(f"  Duplicates removed : {before - len(df)}")

    # Forward-fill missing trading days (reindex to full business-day calendar)
    codes = df["amfi_code"].unique()
    full_range = pd.bdate_range(df["nav_date"].min(), df["nav_date"].max())
    frames = []
    for code in codes:
        sub = df[df["amfi_code"] == code].set_index("nav_date")
        sub = sub.reindex(full_range)
        sub["amfi_code"] = code
        sub["nav"] = sub["nav"].ffill()        # forward-fill holidays
        sub = sub.dropna(subset=["nav"])
        sub.index.name = "nav_date"
        frames.append(sub.reset_index())
    df_clean = pd.concat(frames, ignore_index=True)

    # Compute daily return
    df_clean = df_clean.sort_values(["amfi_code","nav_date"])
    df_clean["daily_return_pct"] = (
        df_clean.groupby("amfi_code")["nav"].pct_change() * 100
    ).round(4)

    log(f"  Final shape        : {df_clean.shape}")
    log(f"  Date range         : {df_clean['nav_date'].min().date()} to {df_clean['nav_date'].max().date()}")
    log(f"  Unique funds       : {df_clean['amfi_code'].nunique()}")
    log(f"  NAV range          : ₹{df_clean['nav'].min():.2f} – ₹{df_clean['nav'].max():.2f}")
    return save(df_clean, "clean_nav.csv")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — Clean investor_transactions.csv
# ─────────────────────────────────────────────────────────────────────────────
def clean_transactions():
    log("\n" + "━"*65)
    log("  TASK 2 | Cleaning investor_transactions")
    log("━"*65)

    df = pd.read_csv(os.path.join(RAW, "08_investor_transactions copy.csv"))
    log(f"  Raw shape : {df.shape}")

    # Standardise transaction_type
    type_map = {
        "sip": "SIP", "lumpsum": "Lumpsum", "lump sum": "Lumpsum",
        "redemption": "Redemption", "redeem": "Redemption",
        "SIP": "SIP", "Lumpsum": "Lumpsum", "Redemption": "Redemption",
    }
    df["transaction_type"] = df["transaction_type"].str.strip().map(
        lambda x: type_map.get(x, x)
    )
    invalid_types = ~df["transaction_type"].isin(["SIP","Lumpsum","Redemption"])
    if invalid_types.sum():
        log(f"  ⚠  {invalid_types.sum()} rows with invalid transaction_type dropped")
    df = df[~invalid_types]

    # Validate amount > 0
    neg_amt = (df["amount_inr"] <= 0).sum()
    if neg_amt:
        log(f"  ⚠  Dropped {neg_amt} rows with amount ≤ 0")
    df = df[df["amount_inr"] > 0]

    # Fix date format
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    bad_dt = df["transaction_date"].isna().sum()
    if bad_dt:
        log(f"  ⚠  Dropped {bad_dt} rows with unparseable dates")
    df = df.dropna(subset=["transaction_date"])

    # KYC status validation
    valid_kyc = ["Verified","Pending"]
    bad_kyc = ~df["kyc_status"].isin(valid_kyc)
    if bad_kyc.sum():
        log(f"  ⚠  {bad_kyc.sum()} rows with invalid kyc_status → set to 'Pending'")
    df.loc[bad_kyc, "kyc_status"] = "Pending"

    # Dedup
    before = len(df)
    df = df.drop_duplicates()
    log(f"  Duplicate rows removed : {before - len(df)}")

    # Sort
    df = df.sort_values("transaction_date").reset_index(drop=True)

    log(f"  Final shape     : {df.shape}")
    log(f"  Date range      : {df['transaction_date'].min().date()} – {df['transaction_date'].max().date()}")
    log(f"  TX type split   : {df['transaction_type'].value_counts().to_dict()}")
    log(f"  KYC Verified    : {(df['kyc_status']=='Verified').sum():,} ({(df['kyc_status']=='Verified').mean()*100:.1f}%)")
    log(f"  Total invested  : ₹{df[df['transaction_type']!='Redemption']['amount_inr'].sum():,.0f}")
    return save(df, "clean_transactions.csv")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 — Clean scheme_performance.csv
# ─────────────────────────────────────────────────────────────────────────────
def clean_performance():
    log("\n" + "━"*65)
    log("  TASK 3 | Cleaning scheme_performance")
    log("━"*65)

    df = pd.read_csv(os.path.join(RAW, "07_scheme_performance copy.csv"))
    log(f"  Raw shape : {df.shape}")

    numeric_cols = ["return_1yr_pct","return_3yr_pct","return_5yr_pct",
                    "alpha","beta","sharpe_ratio","sortino_ratio",
                    "std_dev_ann_pct","max_drawdown_pct"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Flag negative Sharpe ratios
    neg_sharpe = df[df["sharpe_ratio"] < 0]
    log(f"  Negative Sharpe ratios : {len(neg_sharpe)} funds")
    if len(neg_sharpe):
        log(f"    Funds: {neg_sharpe['amfi_code'].tolist()}")
    df["sharpe_flag"] = df["sharpe_ratio"] < 0

    # Expense ratio range check (merged from fund_master)
    exp = pd.read_csv(os.path.join(RAW, "expense_ratios.csv"))

    df = df.merge(
    exp[["amfi_code", "expense_ratio_direct"]],
    on="amfi_code",
    how="left"
   )
    out_of_range = df[(df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)]
    log(f"  Expense ratios out of [0.1%,2.5%] : {len(out_of_range)}")

    # Max drawdown should be negative
    pos_dd = df[df["max_drawdown_pct"] > 0]
    if len(pos_dd):
        log(f"  ⚠  {len(pos_dd)} positive max_drawdown values — negating")
        df.loc[df["max_drawdown_pct"] > 0, "max_drawdown_pct"] *= -1

    log(f"  Final shape : {df.shape}")
    log(f"  Sharpe range: {df['sharpe_ratio'].min():.3f} – {df['sharpe_ratio'].max():.3f}")
    return save(df, "clean_performance.csv")

# ─────────────────────────────────────────────────────────────────────────────
# Clean remaining datasets
# ─────────────────────────────────────────────────────────────────────────────
def clean_others():
    mappings = [
        ("fund_master.csv",        "fund_master_cleaned.csv"),
        ("aum_data.csv",  "aum_data_cleaned.csv"),
        ("sip_data.csv","clean_sip_inflows.csv"),
        ("05_category_inflows copy.csv",   "category_inflows_cleaned.csv"),
        ("06_industry_folio_count.csv","folio_count_cleaned.csv"),
        ("portfolio_holdings.csv", "portfolio_holdings_cleaned.csv"),
        ("benchmark_indexes.csv",  "benchmark_index_cleaned.csv"),
    ]
    for raw_name, clean_name in mappings:
        log(f"\n  Cleaning {raw_name}")
        path = os.path.join(RAW, raw_name)
        if not os.path.exists(path):
            log(f"  ⚠  File not found, skipping")
            continue
        df = pd.read_csv(path)
        before = len(df)

        # Date columns
        for col in df.columns:
            if "date" in col.lower() or col in ["month","quarter","period_end"]:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except:
                    pass

        # Numeric coercion
        for col in df.select_dtypes(include=["object"]).columns:
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().mean() > 0.8:
                    df[col] = converted
            except:
                pass

        # Nulls
        null_pct = df.isnull().mean()
        high_null = null_pct[null_pct > 0.3]
        if not high_null.empty:
            log(f"    ⚠  High nulls: {high_null.to_dict()}")

        # Fill numeric nulls with median
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())

        # Dedup
        df = df.drop_duplicates()
        log(f"    Rows: {before} → {len(df)}")
        save(df, clean_name)

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    log("=" * 65)
    log("  DAY 2 — DATA CLEANING")
    log(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 65)

    clean_nav_history()
    clean_transactions()
    clean_performance()
    clean_others()

    # Write cleaning log
    report_path = os.path.join(PROC, "cleaning_report.txt")
    with open(report_path, "w") as f:
        f.write("\n".join(LOG))

    log(f"\n{'='*65}")
    log(f"  Cleaning report → {report_path}")
    log(f"  All cleaned CSVs → {PROC}/")
    log(f"{'='*65}")

if __name__ == "__main__":
    main()
