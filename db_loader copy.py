"""
db_loader.py
============
Day 2 Tasks 4-6 — Mutual Fund Analytics Capstone
Designs SQLite star schema, loads all cleaned data, and runs 10 SQL queries.

Usage:
    python db_loader.py

Outputs:
    - data/db/bluestock_mf.db   (SQLite database)
    - sql/query_results.txt     (query output)
"""

import os, sqlite3, textwrap, warnings
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROC     = os.path.join(BASE_DIR, "data", "processed")
DB_DIR   = os.path.join(BASE_DIR, "data", "db")
SQL_DIR  = os.path.join(BASE_DIR, "sql")
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH  = os.path.join(DB_DIR, "bluestock_mf.db")
SCHEMA   = os.path.join(BASE_DIR, "schema.sql")

# ─────────────────────────────────────────────────────────────────────────────
# TASK 4 — Build dim_date (calendar dimension)
# ─────────────────────────────────────────────────────────────────────────────
def build_dim_date():
    dates = pd.date_range("2022-01-01", "2026-12-31")
    month_names = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    rows = []
    for d in dates:
        fy_year = d.year + 1 if d.month >= 4 else d.year
        fy_q = ((d.month - 4) % 12) // 3 + 1
        rows.append({
            "date_id":      d.strftime("%Y-%m-%d"),
            "date":         d.strftime("%Y-%m-%d"),
            "year":         d.year,
            "month":        d.month,
            "quarter":      (d.month - 1) // 3 + 1,
            "month_name":   month_names[d.month - 1],
            "week_number":  d.isocalendar()[1],
            "is_weekday":   int(d.weekday() < 5),
            "is_monthend":  0,  # will update below
            "fiscal_year":  f"FY{fy_year-1}-{str(fy_year)[2:]}",
            "fiscal_quarter": f"Q{fy_q}FY{str(fy_year)[2:]}",
        })
    dim = pd.DataFrame(rows)
    # Mark month-ends
    month_ends = dim[dim["is_weekday"] == 1].groupby(["year","month"])["date_id"].max()
    dim.loc[dim["date_id"].isin(month_ends.values), "is_monthend"] = 1
    return dim

# ─────────────────────────────────────────────────────────────────────────────
# TASK 5 — Load all data into SQLite
# ─────────────────────────────────────────────────────────────────────────────
def load_database():
    print("=" * 65)
    print("  DAY 2 — SQLite DATABASE LOAD")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # Remove old DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # ── Apply DDL schema ───────────────────────────────────────
    print("\n  Applying schema.sql …")
    with open(SCHEMA) as f:
        ddl = f.read()
    with sqlite3.connect(DB_PATH) as con:
        # SQLite doesn't support QUALIFY — strip those queries from schema test
        for stmt in ddl.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    con.execute(stmt)
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"  DDL warning: {e}")
    print("  ✓ Schema created")

    # ── dim_date ───────────────────────────────────────────────
    print("\n  Loading dim_date …")
    dim_date = build_dim_date()
    dim_date.to_sql("dim_date", engine, if_exists="replace", index=False)
    print(f"  ✓ dim_date: {len(dim_date):,} rows")

    # ── dim_fund ───────────────────────────────────────────────
    print("\n  Loading dim_fund …")
    fm = pd.read_csv(os.path.join(PROC, "fund_master_cleaned.csv"))
    fm["amfi_code"] = fm["amfi_code"].astype(str)
    fm.to_sql("dim_fund", engine, if_exists="replace", index=False)
    print(f"  ✓ dim_fund: {len(fm):,} rows")

    # ── fact_nav ───────────────────────────────────────────────
    print("\n  Loading fact_nav …")
    nav = pd.read_csv(os.path.join(PROC, "clean_nav.csv"))
    nav["amfi_code"] = nav["amfi_code"].astype(str)
    nav["nav_date"] = pd.to_datetime(nav["nav_date"]).dt.strftime("%Y-%m-%d")
    nav = pd.read_csv(os.path.join(PROC, "clean_nav.csv"))
    nav["amfi_code"] = nav["amfi_code"].astype(str)
    nav["nav_date"] = pd.to_datetime(nav["nav_date"]).dt.strftime("%Y-%m-%d")
    nav = nav.rename(columns={"nav_date": "date_id"})
    nav.to_sql("fact_nav", engine, if_exists="replace", index=False)
    nav.to_sql("fact_nav", engine, if_exists="replace", index=False)
    print(f"  ✓ fact_nav: {len(nav):,} rows")

    # ── fact_transactions ──────────────────────────────────────
    print("\n  Loading fact_transactions …")
    tx = pd.read_csv(os.path.join(PROC, "clean_transactions.csv"))
    tx["amfi_code"] = tx["amfi_code"].astype(str)
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"]).dt.strftime("%Y-%m-%d")
    tx = tx.rename(columns={"transaction_date": "date_id"})
    tx.to_sql("fact_transactions", engine, if_exists="replace", index=False)
    print(f"  ✓ fact_transactions: {len(tx):,} rows")

    # ── fact_performance ───────────────────────────────────────
    print("\n  Loading fact_performance …")
    perf = pd.read_csv(os.path.join(PROC, "clean_performance.csv"))
    perf["amfi_code"] = perf["amfi_code"].astype(str)
    perf["as_of_date"] = "2026-05-31"
    perf.to_sql("fact_performance", engine, if_exists="replace", index=False)
    print(f"  ✓ fact_performance: {len(perf):,} rows")

    # ── fact_portfolio ─────────────────────────────────────────
    print("\n  Loading fact_portfolio …")
    ph = pd.read_csv(os.path.join(PROC, "portfolio_holdings_cleaned.csv"))
    ph["amfi_code"] = ph["amfi_code"].astype(str)
    ph.to_sql("fact_portfolio", engine, if_exists="replace", index=False)
    print(f"  ✓ fact_portfolio: {len(ph):,} rows")

    # ── fact_aum ───────────────────────────────────────────────
    print("\n  Loading fact_aum …")
    aum = pd.read_csv(os.path.join(PROC, "aum_data_cleaned.csv"))
    aum["month"] = pd.to_datetime(
    aum["month"],
    errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    aum = aum.dropna(subset=["month"])
    aum.to_sql("fact_aum", engine, if_exists="replace", index=False)
    print(f"  ✓ fact_aum: {len(aum):,} rows")

    # ── fact_sip_industry ──────────────────────────────────────
    print("\n  Loading fact_sip_industry …")
    sip = pd.read_csv(os.path.join(PROC, "clean_sip_inflows.csv"))
    sip["month"] = sip["month"].astype(str).str[:7]
    sip.to_sql("fact_sip_industry", engine, if_exists="replace", index=False)
    print(f"  ✓ fact_sip_industry: {len(sip):,} rows")

    # ── fact_category_inflows ──────────────────────────────────
    print("\n  Loading fact_category_inflows …")
    ci = pd.read_csv(os.path.join(PROC, "category_inflows_cleaned.csv"))
    ci["month"] = ci["month"].astype(str).str[:7]
    ci.to_sql("fact_category_inflows", engine, if_exists="replace", index=False)
    print(f"  ✓ fact_category_inflows: {len(ci):,} rows")

    print(f"\n  ✅ Database ready → {DB_PATH}")
    print(f"  DB size: {os.path.getsize(DB_PATH)/1e6:.1f} MB")
    return engine

# ─────────────────────────────────────────────────────────────────────────────
# TASK 6 — Run 10 SQL queries
# ─────────────────────────────────────────────────────────────────────────────
QUERIES = {
    "Q1 — Top 5 fund houses by AUM": """
        SELECT fund_house,
               ROUND(SUM(aum_crore),0)                    AS total_aum_crore,
               ROUND(SUM(aum_crore)/1e5, 2)               AS aum_lakh_crore,
               COUNT(DISTINCT fund_house)                  AS entries
        FROM fact_aum
        GROUP BY fund_house
        ORDER BY total_aum_crore DESC
        LIMIT 5
    """,

    "Q2 — Avg monthly NAV for HDFC Top 100 (2024-2025)": """
        SELECT SUBSTR(date_id,1,7) AS month,
               ROUND(AVG(nav),2)   AS avg_nav,
               ROUND(MIN(nav),2)   AS min_nav,
               ROUND(MAX(nav),2)   AS max_nav
        FROM fact_nav
        WHERE amfi_code = '125497'
          AND SUBSTR(date_id,1,4) IN ('2024','2025')
        GROUP BY month
        ORDER BY month
        LIMIT 12
    """,

    "Q3 — SIP inflow YoY by year": """
        SELECT SUBSTR(month,1,4)               AS year,
               ROUND(SUM(sip_inflow_crore),0)  AS total_sip_crore,
               ROUND(AVG(yoy_growth_pct),1)    AS avg_yoy_pct
        FROM fact_sip_industry
        GROUP BY year
        ORDER BY year
    """,

    "Q4 — Transaction amount by state (top 10)": """
        SELECT state, city_tier,
               COUNT(*)                              AS num_transactions,
               COUNT(DISTINCT investor_id)           AS unique_investors,
               ROUND(SUM(amount_inr)/1e7, 2)         AS total_invested_crore
        FROM fact_transactions
        WHERE transaction_type != 'Redemption'
        GROUP BY state
        ORDER BY total_invested_crore DESC
        LIMIT 10
    """,

    "Q5 — Funds with expense ratio < 1%": """
        SELECT f.amfi_code, f.scheme_name, f.fund_house,
               f.category, f.expense_ratio_pct,
               p.sharpe_ratio, p.return_3yr_pct
        FROM dim_fund f
        LEFT JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE f.expense_ratio_pct < 1.0
        ORDER BY f.expense_ratio_pct ASC
        LIMIT 10
    """,

    "Q6 — Top 3 funds per category by 3yr CAGR": """
        SELECT f.category, f.scheme_name, f.fund_house,
               ROUND(p.return_3yr_pct,2) AS return_3yr_pct,
               ROUND(p.sharpe_ratio,3)   AS sharpe_ratio
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        WHERE p.return_3yr_pct IS NOT NULL
        ORDER BY f.category, p.return_3yr_pct DESC
    """,

    "Q7 — SIP vs Lumpsum by age group": """
        SELECT age_group, transaction_type,
               COUNT(*)                           AS count,
               ROUND(SUM(amount_inr)/1e7, 2)      AS total_crore,
               ROUND(AVG(amount_inr), 0)           AS avg_amount_inr
        FROM fact_transactions
        GROUP BY age_group, transaction_type
        ORDER BY age_group, transaction_type
    """,

    "Q8 — NAV return volatility by category": """
        SELECT f.category,
               ROUND(AVG(ABS(n.daily_return_pct)),4)  AS avg_abs_return_pct,
               ROUND(MAX(ABS(n.daily_return_pct)),4)  AS max_swing_pct,
               COUNT(DISTINCT n.amfi_code)             AS num_funds
        FROM fact_nav n
        JOIN dim_fund f ON n.amfi_code = f.amfi_code
        WHERE n.daily_return_pct IS NOT NULL
        GROUP BY f.category
        ORDER BY avg_abs_return_pct DESC
    """,

    "Q9 — Top 10 stocks by fund coverage": """
        SELECT stock_symbol, sector,
               COUNT(DISTINCT amfi_code)       AS held_by_n_funds,
               ROUND(AVG(weight_pct),4)        AS avg_weight_pct,
               ROUND(MAX(weight_pct),4)        AS max_weight_pct
        FROM fact_portfolio
        GROUP BY stock_symbol, sector
        ORDER BY held_by_n_funds DESC, avg_weight_pct DESC
        LIMIT 10
    """,

    "Q10 — Fund composite scorecard (top 10)": """
        WITH base AS (
            SELECT p.amfi_code, f.scheme_name, f.fund_house, f.category,
                   p.return_3yr_pct, p.sharpe_ratio, p.alpha,
                   f.expense_ratio_pct, p.max_drawdown_pct
            FROM fact_performance p
            JOIN dim_fund f ON p.amfi_code = f.amfi_code
            WHERE p.return_3yr_pct IS NOT NULL
        ),
        minmax AS (
            SELECT
                MIN(return_3yr_pct) AS min_r, MAX(return_3yr_pct) AS max_r,
                MIN(sharpe_ratio)   AS min_s, MAX(sharpe_ratio)   AS max_s,
                MIN(alpha)          AS min_a, MAX(alpha)           AS max_a,
                MIN(expense_ratio_pct) AS min_e, MAX(expense_ratio_pct) AS max_e,
                MIN(max_drawdown_pct)  AS min_d, MAX(max_drawdown_pct)  AS max_d
            FROM base
        )
        SELECT b.amfi_code, b.scheme_name, b.fund_house, b.category,
               ROUND(b.return_3yr_pct, 2)   AS return_3yr,
               ROUND(b.sharpe_ratio, 3)     AS sharpe,
               ROUND(
                   CASE WHEN (m.max_r - m.min_r) > 0
                        THEN ((b.return_3yr_pct - m.min_r)/(m.max_r - m.min_r)) * 30 ELSE 0 END
                 + CASE WHEN (m.max_s - m.min_s) > 0
                        THEN ((b.sharpe_ratio - m.min_s)/(m.max_s - m.min_s)) * 25 ELSE 0 END
                 + CASE WHEN (m.max_a - m.min_a) > 0
                        THEN ((b.alpha - m.min_a)/(m.max_a - m.min_a)) * 20 ELSE 0 END
                 + CASE WHEN (m.max_e - m.min_e) > 0
                        THEN (1 - (b.expense_ratio_pct - m.min_e)/(m.max_e - m.min_e)) * 15 ELSE 0 END
                 + CASE WHEN (m.max_d - m.min_d) > 0
                        THEN (1 - (b.max_drawdown_pct - m.min_d)/(m.max_d - m.min_d)) * 10 ELSE 0 END,
               2)  AS composite_score
        FROM base b, minmax m
        ORDER BY composite_score DESC
        LIMIT 10
    """,
}

def run_queries(engine):
    print("\n" + "=" * 65)
    print("  TASK 6 | RUNNING 10 SQL QUERIES")
    print("=" * 65)

    results_log = ["SQL QUERY RESULTS", f"Run: {datetime.now()}", "=" * 65]

    with engine.connect() as con:
        for title, sql in QUERIES.items():
            print(f"\n{'─'*65}")
            print(f"  {title}")
            print(f"{'─'*65}")
            try:
                df = pd.read_sql(text(sql), con)
                print(df.to_string(index=False))
                results_log.append(f"\n{title}")
                results_log.append(df.to_string(index=False))
            except Exception as e:
                msg = f"  Query error: {e}"
                print(msg)
                results_log.append(msg)

    # Save results
    results_path = os.path.join(BASE_DIR, "query_results.txt")
    with open(results_path, "w") as f:
        f.write("\n".join(results_log))
    print(f"\n  Query results saved → {results_path}")

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = load_database()
    run_queries(engine)
    print(f"\n{'='*65}")
    print("  Day 2 database tasks complete ✅")
    print(f"{'='*65}\n")
