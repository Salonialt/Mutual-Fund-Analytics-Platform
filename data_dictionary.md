# Data Dictionary — Bluestock Fintech MF Analytics Capstone

Generated: 2026-06-02 | Database: `data/db/bluestock_mf.db`

---

## dim_fund — Fund Master (40 rows)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| amfi_code | TEXT PK | AMFI unique scheme identifier (6-digit) | `125497` |
| scheme_name | TEXT | Full official AMFI scheme name | `HDFC Top 100 Fund Direct Growth` |
| fund_house | TEXT | Asset Management Company (AMC) name | `HDFC Mutual Fund` |
| category | TEXT | SEBI category: Equity / Debt / Hybrid / Other | `Equity` |
| sub_category | TEXT | Sub-category: Large Cap / Mid Cap / Liquid / ELSS… | `Large Cap` |
| plan | TEXT | Direct or Regular plan | `Direct` |
| benchmark | TEXT | Official benchmark index | `Nifty 100 TRI` |
| expense_ratio_pct | REAL | Annual TER in % (SEBI cap: 1.05% for Equity Direct) | `0.57` |
| exit_load_pct | REAL | Redemption charge within 1 year (0 for Liquid/Debt) | `1.0` |
| fund_manager | TEXT | Primary fund manager name | `Rahul Baijal` |
| risk_category | TEXT | SEBI risk-o-meter: Low / Moderate / High / Very High | `Very High` |
| sebi_category_code | TEXT | Internal SEBI code: EC01=LargeCap, DC01=Liquid… | `EC01` |
| launch_date | DATE | Fund NFO/launch date | `2013-01-01` |

---

## dim_date — Date Dimension (1,826 rows)

| Column | Type | Description |
|--------|------|-------------|
| date_id | TEXT PK | Primary key in YYYY-MM-DD format |
| date | DATE | Calendar date |
| year | INT | Calendar year |
| month | INT | Month number (1–12) |
| quarter | INT | Calendar quarter (1–4) |
| month_name | TEXT | Full month name |
| week_number | INT | ISO week number |
| is_weekday | INT | 1 = Mon–Fri, 0 = Sat–Sun |
| is_monthend | INT | 1 = last business day of that month |
| fiscal_year | TEXT | Indian FY: Apr–Mar, e.g. `FY2024-25` |
| fiscal_quarter | TEXT | e.g. `Q1FY25` (Apr–Jun 2024) |

---

## fact_nav — Daily NAV History (~46,000 rows)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| nav_id | INT PK | Auto-increment primary key | |
| amfi_code | TEXT FK | Links to dim_fund | |
| date_id | TEXT FK | Links to dim_date | |
| nav | REAL | NAV in ₹ per unit, CHECK > 0 | Anchored to real mfapi.in values |
| daily_return_pct | REAL | `(nav_t / nav_t-1 - 1) × 100` | Null for first row per fund |

**Quality notes:** Forward-filled for market holidays; weekends excluded; 40 funds × ~1,150 trading days.

---

## fact_transactions — Investor Transactions (~55,000 rows)

| Column | Type | Description | Values |
|--------|------|-------------|--------|
| tx_id | INT PK | Auto-increment | |
| investor_id | TEXT | Unique investor: INV000001–INV005000 | |
| amfi_code | TEXT FK | Fund invested in | |
| date_id | TEXT FK | Transaction date | |
| transaction_type | TEXT | CHECK IN (SIP, Lumpsum, Redemption) | 65% SIP / 25% Lumpsum / 10% Redemption |
| amount_inr | INT | Amount in ₹, CHECK > 0 | SIP: ₹500–₹25,000; Lumpsum: ₹5K–₹5L |
| state | TEXT | Investor's state (12 states) | Maharashtra highest (18%) |
| city | TEXT | Investor's city | |
| city_tier | TEXT | T30 (Top 30 cities) or B30 | |
| age_group | TEXT | 18-25 / 26-35 / 36-45 / 46-55 / 56+ | 26-35 most active (35%) |
| gender | TEXT | Male / Female | 58% Male |
| annual_income_lakh | REAL | Annual income in ₹ lakh | Exponential distribution, mean ₹8L |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque | UPI 45% |
| kyc_status | TEXT | Verified / Pending | 92% Verified |

---

## fact_performance — Scheme Risk-Return Metrics (40 rows)

| Column | Type | Description |
|--------|------|-------------|
| amfi_code | TEXT FK | Fund identifier |
| as_of_date | DATE | Snapshot date (2026-05-31) |
| return_1yr_pct | REAL | 1-year absolute return % |
| return_3yr_pct | REAL | 3-year CAGR % |
| return_5yr_pct | REAL | 5-year CAGR % |
| benchmark_3yr_pct | REAL | Benchmark index 3yr CAGR for alpha comparison |
| alpha | REAL | Return above benchmark (Jensen's Alpha) |
| beta | REAL | Market sensitivity (1.0 = moves with market) |
| sharpe_ratio | REAL | `(Rp - Rf) / σ × √252`, Rf = 6.5% |
| sortino_ratio | REAL | Like Sharpe but uses only downside σ |
| std_dev_ann_pct | REAL | Annualised standard deviation of daily returns |
| max_drawdown_pct | REAL | Worst peak-to-trough decline (negative value) |
| expense_ratio_pct | REAL | Joined from dim_fund |
| morningstar_rating | INT | Simulated 1–5 star based on Sharpe |
| sharpe_flag | INT | 1 = negative Sharpe (underperformer flag) |

---

## fact_portfolio — Equity Holdings (~541 rows)

| Column | Type | Description |
|--------|------|-------------|
| amfi_code | TEXT FK | Fund holding the stock |
| stock_symbol | TEXT | NSE ticker symbol (e.g. HDFCBANK) |
| sector | TEXT | Banking / IT / Energy / FMCG / Auto / Pharma / Infra / Telecom |
| weight_pct | REAL | Portfolio weight %, sums to ~100 per fund |
| as_of_date | DATE | Holdings as-of date (2025-12-31) |

---

## fact_aum — AUM by Fund House (160 rows)

| Column | Type | Description |
|--------|------|-------------|
| fund_house | TEXT | AMC name |
| period_end | DATE | Quarter end date |
| aum_crore | REAL | AUM in ₹ crore (SBI largest: ~₹12.5L crore) |
| num_schemes | INT | Number of schemes managed |

---

## fact_sip_industry — Monthly SIP Industry Data (48 rows)

| Column | Type | Description |
|--------|------|-------------|
| month | TEXT | YYYY-MM format (Jan 2022 – Dec 2025) |
| sip_inflow_crore | REAL | Monthly SIP inflow in ₹ crore |
| active_sip_accounts_crore | REAL | Active SIP mandates in crore |
| new_sip_accounts_lakh | REAL | New SIPs registered in that month |
| sip_aum_lakh_crore | REAL | Total SIP corpus in ₹ lakh crore |
| yoy_growth_pct | REAL | Year-on-year growth in SIP inflows |

---

## Relationships (Star Schema)

```
                    dim_date ──── fact_nav
                        │             │
                        │             │
dim_fund ───── fact_nav, fact_transactions, fact_performance, fact_portfolio
    │
    └── fund_house → fact_aum

fact_sip_industry      (no FK — industry-level, not fund-level)
fact_category_inflows  (no FK — category-level aggregates)
```

---

## Key Domain Notes

- **AMFI codes** are 6-digit integers assigned sequentially. Each plan variant (Direct/Regular) and option (Growth/IDCW) has a separate code.
- **NAV** is declared daily by AMCs to AMFI by 9 PM. Holidays use previous day's NAV (forward-fill).
- **T30 cities** = Top 30 cities by AUM per AMFI classification (Mumbai, Delhi, Bengaluru…).
- **B30 cities** = Beyond Top 30 — SEBI incentivises AMCs to expand here with higher TER allowance.
- **Expense ratio** for Direct plans is 0.3–0.8% lower than Regular plans (no distributor commission).
- **Risk-o-meter** is a SEBI-mandated 6-level scale evaluated monthly by each AMC.
