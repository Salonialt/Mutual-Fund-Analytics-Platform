#!/usr/bin/env python3
"""
run_pipeline.py — Master ETL & Analytics Pipeline
==================================================
Bluestock Fintech | Mutual Fund Analytics Capstone

Runs the complete end-to-end pipeline in sequence:
  Step 1 → Data Ingestion      (data_ingestion.py)
  Step 2 → Data Cleaning       (data_cleaning.py)
  Step 3 → Database Load       (db_loader copy.py)
  Step 4 → EDA Analysis        (eda_analysis.py)
  Step 5 → Performance Metrics (performance_analytics.py)
  Step 6 → Advanced Analytics  (advanced_analytics.py)
  Step 7 → Dashboard Export    (dashboard/build_dashboard_exports.py)
  Step 8 → Final Report        (reports/build_final_report.py)

Usage:
    python run_pipeline.py              # run all steps
    python run_pipeline.py --step 3     # run from step 3
    python run_pipeline.py --only 5     # run only step 5
    python run_pipeline.py --dry-run    # print steps without executing
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

PIPELINE_STEPS = [
    {
        "step": 1,
        "name": "Data Ingestion",
        "script": "data_ingestion.py",
        "description": "Load all 10 CSVs, fetch live NAV, validate AMFI codes",
        "outputs": ["data/raw/*.csv", "data/processed/data_quality_report.txt"],
    },
    {
        "step": 2,
        "name": "Data Cleaning",
        "script": "data_cleaning.py",
        "description": "Clean NAV, transactions, performance — handle nulls, types, dedup",
        "outputs": ["data/processed/clean_*.csv", "data/processed/cleaning_report.txt"],
    },
    {
        "step": 3,
        "name": "Database Load",
        "script": "db_loader copy.py",
        "description": "Build SQLite star schema, load 8 tables, run 10 SQL queries",
        "outputs": ["data/db/bluestock_mf.db", "sql/query_results.txt"],
    },
    {
        "step": 4,
        "name": "EDA Analysis",
        "script": "eda_analysis.py",
        "description": "Generate 12 charts: NAV trends, AUM, SIP, demographics, correlation",
        "outputs": ["reports/charts/chart_0*.png", "notebooks/EDA_Analysis.ipynb"],
    },
    {
        "step": 5,
        "name": "Performance Analytics",
        "script": "performance_analytics.py",
        "description": "CAGR, Sharpe, Sortino, Alpha/Beta, Max Drawdown, Fund Scorecard",
        "outputs": ["data/processed/fund_scorecard.csv", "data/processed/alpha_beta.csv",
                    "reports/charts/chart_perf_*.png", "notebooks/Performance_Analytics.ipynb"],
    },
    {
        "step": 6,
        "name": "Advanced Analytics",
        "script": "advanced_analytics copy.py",
        "description": "VaR/CVaR, Rolling Sharpe, Cohort Analysis, Recommender, Sector HHI",
        "outputs": ["data/processed/var_cvar_report.csv", "data/processed/recommendations.csv",
                    "reports/charts/chart_adv_*.png", "notebooks/Advanced_Analytics.ipynb"],
    },
    {
        "step": 7,
        "name": "Dashboard Export",
        "script": "dashboard/build_dashboard_exports.py",
        "description": "Generate 4 PNG dashboard pages + combined Dashboard.pdf",
        "outputs": ["dashboard/Dashboard_Page*.png", "dashboard/Dashboard.pdf"],
    },
    {
        "step": 8,
        "name": "Final Report",
        "script": "reports/build_final_report.py",
        "description": "Build 18-page Final_Report.pdf using ReportLab",
        "outputs": ["reports/Final_Report copy.pdf"],
    },
]

GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
ORANGE  = "\033[38;5;208m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

def banner():
    print(f"\n{BOLD}{BLUE}{'='*65}{RESET}")
    print(f"{BOLD}  Bluestock Fintech — Mutual Fund Analytics Pipeline{RESET}")
    print(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BOLD}{BLUE}{'='*65}{RESET}\n")

def run_step(step_info, dry_run=False):
    step = step_info["step"]
    name = step_info["name"]
    script = os.path.join(BASE, step_info["script"])

    print(f"{BOLD}{ORANGE}[Step {step}/8]{RESET} {BOLD}{name}{RESET}")
    print(f"  Script : {step_info['script']}")
    print(f"  Purpose: {step_info['description']}")

    if dry_run:
        print(f"  {YELLOW}[DRY RUN — skipping execution]{RESET}\n")
        return True

    if not os.path.exists(script):
        print(f"  {RED}✗ Script not found: {script}{RESET}\n")
        return False

    t0 = time.time()
    result = subprocess.run(
        [sys.executable, script],
        cwd=BASE,
        capture_output=False,
        text=True,
    )
    elapsed = time.time() - t0

    if result.returncode == 0:
        print(f"  {GREEN}✓ Completed in {elapsed:.1f}s{RESET}\n")
        return True
    else:
        print(f"  {RED}✗ Failed (exit {result.returncode}) after {elapsed:.1f}s{RESET}\n")
        return False

def main():
    parser = argparse.ArgumentParser(description="Bluestock MF Analytics Pipeline")
    parser.add_argument("--step",     type=int, help="Start from this step number (1–8)")
    parser.add_argument("--only",     type=int, help="Run only this step number")
    parser.add_argument("--dry-run",  action="store_true", help="Print steps without executing")
    args = parser.parse_args()

    banner()

    steps = PIPELINE_STEPS
    if args.only:
        steps = [s for s in PIPELINE_STEPS if s["step"] == args.only]
        if not steps:
            print(f"{RED}Step {args.only} not found.{RESET}")
            sys.exit(1)
    elif args.step:
        steps = [s for s in PIPELINE_STEPS if s["step"] >= args.step]

    results = {}
    t_start = time.time()
    for step_info in steps:
        ok = run_step(step_info, dry_run=args.dry_run)
        results[step_info["step"]] = ok
        if not ok and not args.dry_run:
            print(f"{RED}Pipeline stopped at step {step_info['step']}.{RESET}")
            break

    total = time.time() - t_start
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    print(f"{BOLD}{BLUE}{'='*65}{RESET}")
    print(f"  {BOLD}Pipeline Summary{RESET}  |  {GREEN}{passed} passed{RESET}  {RED}{failed} failed{RESET}  |  {total:.0f}s total")
    print(f"{BOLD}{BLUE}{'='*65}{RESET}\n")

    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
