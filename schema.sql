-- ============================================================
-- schema.sql
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- Day 2: Star Schema DDL for SQLite
-- ============================================================
-- Architecture: Star Schema
--   Dimensions : dim_fund, dim_date
--   Facts      : fact_nav, fact_transactions, fact_performance,
--                fact_portfolio, fact_aum, fact_sip_industry
-- ============================================================

PRAGMA foreign_keys = ON;

-- ──────────────────────────────────────────────────────────────
-- DIMENSION TABLES
-- ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           TEXT PRIMARY KEY,
    scheme_name         TEXT NOT NULL,
    fund_house          TEXT NOT NULL,
    category            TEXT NOT NULL,           -- Equity / Debt / Hybrid / Other
    sub_category        TEXT,                    -- Large Cap / Mid Cap / Liquid / etc.
    plan                TEXT DEFAULT 'Direct',   -- Direct / Regular
    benchmark           TEXT,
    expense_ratio_pct   REAL,                    -- e.g. 0.57
    exit_load_pct       REAL DEFAULT 0.0,
    fund_manager        TEXT,
    risk_category       TEXT,                    -- Low / Moderate / High / Very High
    sebi_category_code  TEXT,                    -- EC01, DC01, HC03, etc.
    launch_date         DATE
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id     TEXT PRIMARY KEY,   -- YYYY-MM-DD
    date        DATE NOT NULL,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,   -- 1-12
    quarter     INTEGER NOT NULL,   -- 1-4
    month_name  TEXT NOT NULL,      -- January … December
    week_number INTEGER NOT NULL,
    is_weekday  INTEGER NOT NULL,   -- 1 = weekday, 0 = weekend
    is_monthend INTEGER NOT NULL,   -- 1 if last business day of month
    fiscal_year TEXT,               -- e.g. FY2024-25
    fiscal_quarter TEXT             -- e.g. Q1FY25
);

-- ──────────────────────────────────────────────────────────────
-- FACT TABLES
-- ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    date_id             TEXT NOT NULL REFERENCES dim_date(date_id),
    nav                 REAL NOT NULL CHECK (nav > 0),
    daily_return_pct    REAL,
    UNIQUE(amfi_code, date_id)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    tx_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT NOT NULL,
    amfi_code           TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    date_id             TEXT NOT NULL REFERENCES dim_date(date_id),
    transaction_type    TEXT NOT NULL CHECK (transaction_type IN ('SIP','Lumpsum','Redemption')),
    amount_inr          INTEGER NOT NULL CHECK (amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT CHECK (city_tier IN ('T30','B30')),
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT DEFAULT 'Verified'
);

CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    as_of_date          DATE NOT NULL,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    sharpe_flag         INTEGER DEFAULT 0,
    UNIQUE(amfi_code, as_of_date)
);

CREATE TABLE IF NOT EXISTS fact_portfolio (
    hold_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    stock_symbol        TEXT NOT NULL,
    sector              TEXT,
    weight_pct          REAL NOT NULL CHECK (weight_pct >= 0),
    as_of_date          DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house          TEXT NOT NULL,
    period_end          DATE NOT NULL,
    aum_crore           REAL NOT NULL,
    num_schemes         INTEGER,
    UNIQUE(fund_house, period_end)
);

CREATE TABLE IF NOT EXISTS fact_sip_industry (
    sip_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    month               TEXT NOT NULL UNIQUE,       -- YYYY-MM
    sip_inflow_crore    REAL NOT NULL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore  REAL,
    yoy_growth_pct      REAL
);

CREATE TABLE IF NOT EXISTS fact_category_inflows (
    inflow_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    month               TEXT NOT NULL,
    category            TEXT NOT NULL,
    net_inflow_crore    REAL,
    gross_purchase_crore REAL,
    gross_redemption_crore REAL,
    UNIQUE(month, category)
);

-- ──────────────────────────────────────────────────────────────
-- INDEXES for query performance
-- ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_nav_fund_date    ON fact_nav(amfi_code, date_id);
CREATE INDEX IF NOT EXISTS idx_nav_date         ON fact_nav(date_id);
CREATE INDEX IF NOT EXISTS idx_tx_fund          ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_tx_investor      ON fact_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_tx_date          ON fact_transactions(date_id);
CREATE INDEX IF NOT EXISTS idx_tx_state         ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_perf_fund        ON fact_performance(amfi_code);
CREATE INDEX IF NOT EXISTS idx_portfolio_fund   ON fact_portfolio(amfi_code);
CREATE INDEX IF NOT EXISTS idx_aum_house        ON fact_aum(fund_house);
CREATE INDEX IF NOT EXISTS idx_fund_house       ON dim_fund(fund_house);
CREATE INDEX IF NOT EXISTS idx_fund_category    ON dim_fund(category);

-- End of schema.sql
