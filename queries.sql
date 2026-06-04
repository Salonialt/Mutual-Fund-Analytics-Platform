-- ============================================================
-- queries.sql
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- Day 2: 10 Analytical SQL Queries
-- ============================================================

-- ── Q1: Top 5 funds by latest AUM ────────────────────────────
-- Shows which fund houses hold the most assets
SELECT
    f.fund_house,
    SUM(a.aum_crore)        AS total_aum_crore,
    COUNT(DISTINCT f.amfi_code) AS num_schemes,
    ROUND(SUM(a.aum_crore) / 1e5, 2) AS aum_lakh_crore
FROM fact_aum a
JOIN dim_fund f ON a.fund_house = f.fund_house
WHERE a.period_end = (SELECT MAX(period_end) FROM fact_aum)
GROUP BY f.fund_house
ORDER BY total_aum_crore DESC
LIMIT 5;


-- ── Q2: Average NAV per month for HDFC Top 100 ───────────────
-- Tracks monthly price movement of a specific scheme
SELECT
    d.year,
    d.month_name,
    ROUND(AVG(n.nav), 2)    AS avg_nav,
    ROUND(MIN(n.nav), 2)    AS min_nav,
    ROUND(MAX(n.nav), 2)    AS max_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
WHERE n.amfi_code = '125497'
  AND d.year BETWEEN 2024 AND 2025
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- ── Q3: SIP inflow year-on-year growth ───────────────────────
-- Shows compounding growth of SIP culture in India
SELECT
    SUBSTR(month, 1, 4)                AS year,
    ROUND(SUM(sip_inflow_crore), 0)    AS total_sip_crore,
    ROUND(AVG(yoy_growth_pct), 1)      AS avg_yoy_growth_pct
FROM fact_sip_industry
GROUP BY SUBSTR(month, 1, 4)
ORDER BY year;


-- ── Q4: Total transaction amount by state ────────────────────
-- Geographic distribution of investor money
SELECT
    t.state,
    t.city_tier,
    COUNT(*)                            AS num_transactions,
    COUNT(DISTINCT t.investor_id)       AS unique_investors,
    ROUND(SUM(t.amount_inr) / 1e7, 2)  AS total_invested_crore,
    ROUND(AVG(t.amount_inr), 0)         AS avg_transaction_inr
FROM fact_transactions t
WHERE t.transaction_type != 'Redemption'
GROUP BY t.state, t.city_tier
ORDER BY total_invested_crore DESC;


-- ── Q5: Funds with expense ratio < 1% ────────────────────────
-- Cost-efficient fund identification
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    f.sub_category,
    f.expense_ratio_pct,
    p.sharpe_ratio,
    p.return_3yr_pct
FROM dim_fund f
LEFT JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;


-- ── Q6: Best performing funds by 3yr CAGR per category ───────
SELECT
    f.category,
    f.scheme_name,
    f.fund_house,
    p.return_3yr_pct,
    p.sharpe_ratio,
    p.max_drawdown_pct,
    RANK() OVER (PARTITION BY f.category ORDER BY p.return_3yr_pct DESC) AS rank_in_category
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_3yr_pct IS NOT NULL
QUALIFY rank_in_category <= 3
ORDER BY f.category, rank_in_category;


-- ── Q7: SIP vs Lumpsum vs Redemption split by age group ──────
SELECT
    t.age_group,
    t.transaction_type,
    COUNT(*)                                AS count,
    ROUND(SUM(t.amount_inr) / 1e7, 2)      AS total_crore,
    ROUND(AVG(t.amount_inr), 0)             AS avg_amount_inr
FROM fact_transactions t
GROUP BY t.age_group, t.transaction_type
ORDER BY t.age_group, t.transaction_type;


-- ── Q8: Monthly NAV return volatility by fund category ───────
-- Risk comparison across fund types
SELECT
    f.category,
    ROUND(AVG(ABS(n.daily_return_pct)), 4)      AS avg_abs_daily_return_pct,
    ROUND(MAX(ABS(n.daily_return_pct)), 4)      AS max_daily_swing_pct,
    COUNT(DISTINCT n.amfi_code)                 AS num_funds
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE n.daily_return_pct IS NOT NULL
GROUP BY f.category
ORDER BY avg_abs_daily_return_pct DESC;


-- ── Q9: Top 10 stocks by weight across all equity funds ──────
-- Portfolio concentration analysis
SELECT
    p.stock_symbol,
    p.sector,
    COUNT(DISTINCT p.amfi_code)         AS held_by_n_funds,
    ROUND(AVG(p.weight_pct), 4)         AS avg_weight_pct,
    ROUND(MAX(p.weight_pct), 4)         AS max_weight_pct,
    ROUND(SUM(p.weight_pct), 2)         AS total_weight_pct
FROM fact_portfolio p
GROUP BY p.stock_symbol, p.sector
ORDER BY held_by_n_funds DESC, avg_weight_pct DESC
LIMIT 10;


-- ── Q10: Fund scorecard — composite ranking ───────────────────
-- Weighted composite score: 30% 3yr return + 25% Sharpe + 20% Alpha
--                         + 15% Expense (inverse) + 10% Max DD (inverse)
WITH ranked AS (
    SELECT
        p.amfi_code,
        f.scheme_name,
        f.fund_house,
        f.category,
        p.return_3yr_pct,
        p.sharpe_ratio,
        p.alpha,
        f.expense_ratio_pct,
        p.max_drawdown_pct,
        PERCENT_RANK() OVER (ORDER BY p.return_3yr_pct)        AS pct_return,
        PERCENT_RANK() OVER (ORDER BY p.sharpe_ratio)          AS pct_sharpe,
        PERCENT_RANK() OVER (ORDER BY p.alpha)                 AS pct_alpha,
        PERCENT_RANK() OVER (ORDER BY f.expense_ratio_pct DESC) AS pct_expense,
        PERCENT_RANK() OVER (ORDER BY p.max_drawdown_pct DESC) AS pct_maxdd
    FROM fact_performance p
    JOIN dim_fund f ON p.amfi_code = f.amfi_code
    WHERE p.return_3yr_pct IS NOT NULL
)
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    ROUND(return_3yr_pct, 2)    AS return_3yr_pct,
    ROUND(sharpe_ratio, 3)      AS sharpe_ratio,
    ROUND(
        (pct_return * 30 + pct_sharpe * 25 + pct_alpha * 20
         + pct_expense * 15 + pct_maxdd * 10), 2
    )                           AS composite_score_100
FROM ranked
ORDER BY composite_score_100 DESC
LIMIT 10;

-- End of queries.sql
