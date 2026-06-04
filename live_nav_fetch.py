"""
live_nav_fetch.py
=================
Day 1 — Mutual Fund Analytics Project
Fetches live NAV data from mfapi.in for 6 key large-cap schemes.

Usage:
    python live_nav_fetch.py

API:  https://api.mfapi.in/mf/{scheme_code}
Docs: https://www.mfapi.in/

Outputs:
    - data/raw/nav_live_{scheme_code}.csv   → raw per-scheme NAV history
    - data/raw/nav_live_all.csv             → consolidated file
    - data/processed/nav_live_summary.csv   → latest NAV + 1-day change
"""

import os
import time
import json
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(RAW_DIR,  exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

# ── Scheme registry ────────────────────────────────────────────────────────────
SCHEMES = {
    125497: {
        "name":       "HDFC Top 100 Direct Plan Growth",
        "fund_house": "HDFC Mutual Fund",
        "category":   "Large Cap",
    },
    119551: {
        "name":       "SBI Bluechip Direct Plan Growth",
        "fund_house": "SBI Mutual Fund",
        "category":   "Large Cap",
    },
    120503: {
        "name":       "ICICI Pru Bluechip Direct Plan Growth",
        "fund_house": "ICICI Prudential Mutual Fund",
        "category":   "Large Cap",
    },
    118632: {
        "name":       "Nippon India Large Cap Direct Growth",
        "fund_house": "Nippon India Mutual Fund",
        "category":   "Large Cap",
    },
    119092: {
        "name":       "Axis Bluechip Direct Plan Growth",
        "fund_house": "Axis Mutual Fund",
        "category":   "Large Cap",
    },
    120841: {
        "name":       "Kotak Bluechip Direct Plan Growth",
        "fund_house": "Kotak Mahindra Mutual Fund",
        "category":   "Large Cap",
    },
}

API_BASE    = "https://api.mfapi.in/mf"
TIMEOUT_SEC = 15
RETRY_COUNT = 3
RETRY_DELAY = 2   # seconds between retries

# ── Fetcher ────────────────────────────────────────────────────────────────────
def fetch_nav(scheme_code: int, use_mock: bool = False) -> dict:
    """
    Fetch NAV history from mfapi.in.
    Falls back to mock data if the network is unavailable (e.g. sandbox env).

    Returns a dict matching the mfapi.in JSON schema:
        {
          "meta": { "fund_house": ..., "scheme_name": ..., ... },
          "data": [ {"date": "DD-MM-YYYY", "nav": "..."}, ... ],
          "status": "SUCCESS"
        }
    """
    url = f"{API_BASE}/{scheme_code}"

    if not use_mock:
        for attempt in range(1, RETRY_COUNT + 1):
            try:
                log.info(f"  GET {url}  (attempt {attempt}/{RETRY_COUNT})")
                resp = requests.get(url, timeout=TIMEOUT_SEC)
                resp.raise_for_status()
                payload = resp.json()
                if payload.get("status") == "SUCCESS":
                    log.info(f"  ✓ {scheme_code}: {len(payload['data'])} NAV records received")
                    return payload
                else:
                    log.warning(f"  API returned non-SUCCESS status: {payload.get('status')}")
            except requests.exceptions.ConnectionError as e:
                log.warning(f"  Connection error (attempt {attempt}): {e}")
            except requests.exceptions.Timeout:
                log.warning(f"  Timeout on attempt {attempt}")
            except requests.exceptions.HTTPError as e:
                log.error(f"  HTTP error: {e}")
                break
            except json.JSONDecodeError:
                log.error("  Could not parse JSON response")
                break

            if attempt < RETRY_COUNT:
                log.info(f"  Retrying in {RETRY_DELAY}s …")
                time.sleep(RETRY_DELAY)

        log.warning(f"  Live fetch failed for {scheme_code}. Falling back to mock data.")

    # ── Mock / fallback data generator ────────────────────────────────────
    return _generate_mock_nav(scheme_code)


def _generate_mock_nav(scheme_code: int) -> dict:
    """Generate realistic synthetic NAV data matching the mfapi.in schema."""
    info = SCHEMES.get(scheme_code, {})
    np.random.seed(scheme_code % (2**31))

    base_nav = {
        125497: 892.45,   # HDFC Top 100
        119551:  78.32,   # SBI Bluechip
        120503:  98.12,   # ICICI Bluechip
        118632:  65.43,   # Nippon Large Cap
        119092:  56.78,   # Axis Bluechip
        120841:  72.15,   # Kotak Bluechip
    }.get(scheme_code, 100.0)

    nav = base_nav
    records = []
    today   = datetime.now()

    for days_back in range(730):     # ~2 years of history
        dt = today - timedelta(days=days_back)
        if dt.weekday() >= 5:        # skip weekends
            continue
        nav = max(nav * (1 + np.random.normal(0.0004, 0.008)), 5)
        records.append({
            "date": dt.strftime("%d-%m-%Y"),
            "nav":  f"{nav:.4f}",
        })

    # most-recent first (matches API convention)
    records.reverse()
    records = records[::-1]

    return {
        "meta": {
            "fund_house":       info.get("fund_house", "Unknown"),
            "scheme_type":      "Open Ended Schemes",
            "scheme_category":  f"Equity Scheme - {info.get('category', 'Large Cap')}",
            "scheme_code":      scheme_code,
            "scheme_name":      info.get("name", f"Scheme {scheme_code}"),
        },
        "data":   records,
        "status": "SUCCESS (mock)",
        "_source": "synthetic fallback — live API unavailable in this environment",
    }


# ── Parser ─────────────────────────────────────────────────────────────────────
def parse_to_dataframe(payload: dict, scheme_code: int) -> pd.DataFrame:
    """Convert mfapi.in JSON payload to a tidy DataFrame."""
    meta = payload.get("meta", {})
    rows = payload.get("data", [])

    df = pd.DataFrame(rows)
    df["nav"]       = pd.to_numeric(df["nav"], errors="coerce")
    df["nav_date"]  = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["nav_date", "nav"]).sort_values("nav_date")

    df["amfi_code"]   = scheme_code
    df["scheme_name"] = meta.get("scheme_name", "")
    df["fund_house"]  = meta.get("fund_house", "")
    df["category"]    = meta.get("scheme_category", "")

    # Derived columns
    df["change_abs"]  = df["nav"].diff().round(4)
    df["change_pct"]  = (df["nav"].pct_change() * 100).round(4)

    df = df.drop(columns=["date"], errors="ignore")
    return df[["amfi_code", "scheme_name", "fund_house", "category",
               "nav_date", "nav", "change_abs", "change_pct"]]


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  LIVE NAV FETCH — mfapi.in")
    print(f"  Run at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Schemes: {len(SCHEMES)}")
    print("=" * 70)

    all_frames   = []
    summary_rows = []

    for code, info in SCHEMES.items():
        print(f"\n{'─' * 60}")
        print(f"  Scheme  : {code}  |  {info['name']}")
        print(f"  House   : {info['fund_house']}")
        print(f"{'─' * 60}")

        # ── Fetch ──────────────────────────────────────────────────────────
        payload = fetch_nav(code)
        if payload is None:
            log.error(f"  Skipping {code} — no data received.")
            continue

        is_live = "mock" not in payload.get("status", "").lower()

        # ── Parse ──────────────────────────────────────────────────────────
        df = parse_to_dataframe(payload, code)
        log.info(f"  Parsed {len(df):,} trading-day records")

        # ── Save raw JSON response ─────────────────────────────────────────
        json_path = os.path.join(RAW_DIR, f"nav_live_{code}.json")
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2, default=str)

        # ── Save raw CSV ───────────────────────────────────────────────────
        raw_csv = os.path.join(RAW_DIR, f"nav_live_{code}.csv")
        df.to_csv(raw_csv, index=False)
        log.info(f"  Raw CSV → {raw_csv}")

        # ── Summary row ────────────────────────────────────────────────────
        latest    = df.iloc[-1]
        prev      = df.iloc[-2] if len(df) > 1 else latest
        week_ago  = df[df["nav_date"] <= (latest["nav_date"] - timedelta(days=7))]
        month_ago = df[df["nav_date"] <= (latest["nav_date"] - timedelta(days=30))]

        summary_rows.append({
            "amfi_code":     code,
            "scheme_name":   info["name"],
            "fund_house":    info["fund_house"],
            "latest_nav":    round(latest["nav"], 4),
            "nav_date":      latest["nav_date"].date(),
            "change_1d_abs": round(latest["change_abs"], 4) if pd.notna(latest["change_abs"]) else None,
            "change_1d_pct": round(latest["change_pct"], 4) if pd.notna(latest["change_pct"]) else None,
            "nav_7d_ago":    round(week_ago["nav"].iloc[-1], 4) if len(week_ago) else None,
            "nav_30d_ago":   round(month_ago["nav"].iloc[-1], 4) if len(month_ago) else None,
            "total_records": len(df),
            "data_source":   "live" if is_live else "mock",
        })

        print(f"\n  Latest NAV  : ₹ {latest['nav']:.4f}  ({latest['nav_date'].date()})")
        if pd.notna(latest["change_abs"]):
            arrow = "▲" if latest["change_abs"] >= 0 else "▼"
            color = "+" if latest["change_abs"] >= 0 else ""
            print(f"  1-day move  : {arrow} {color}{latest['change_abs']:.4f}  ({color}{latest['change_pct']:.2f}%)")
        print(f"  Records     : {len(df):,} trading days")
        print(f"  Data source : {'🌐 Live (mfapi.in)' if is_live else '🔧 Synthetic fallback'}")

        all_frames.append(df)
        time.sleep(0.3)     # polite rate-limiting for live API

    # ── Consolidated CSV ───────────────────────────────────────────────────
    if all_frames:
        combined    = pd.concat(all_frames, ignore_index=True)
        all_csv     = os.path.join(RAW_DIR, "nav_live_all.csv")
        combined.to_csv(all_csv, index=False)
        log.info(f"\n  Consolidated CSV → {all_csv}  ({len(combined):,} rows)")

    # ── Summary ────────────────────────────────────────────────────────────
    summary_df  = pd.DataFrame(summary_rows)
    summary_csv = os.path.join(PROC_DIR, "nav_live_summary.csv")
    summary_df.to_csv(summary_csv, index=False)

    print(f"\n{'=' * 70}")
    print("  NAV SUMMARY TABLE")
    print(f"{'=' * 70}")
    print(summary_df.to_string(index=False))
    print(f"\n  Summary saved → {summary_csv}")
    print(f"{'=' * 70}\n")

    return summary_df


if __name__ == "__main__":
    main()
