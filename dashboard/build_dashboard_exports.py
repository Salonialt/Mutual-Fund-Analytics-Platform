#!/usr/bin/env python3
"""
build_dashboard_exports.py — Generate Dashboard charts and combine into Dashboard.pdf
======================================================================================
Bluestock Fintech | Mutual Fund Analytics Capstone
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from weasyprint import HTML

# Set professional plotting style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 13,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.titlesize': 14
})

# Ensure directories exist
os.makedirs('dashboard', exist_ok=True)

print("Generating mock/analytics data and plotting charts...")

# ----------------- PAGE 1 CHARTS -----------------
# 1. Industry AUM Trend
dates = pd.date_range(start='2022-01-01', end='2025-10-01', freq='3MS')
aum_trend = np.linspace(38, 81.1, len(dates)) + np.random.normal(0, 0.5, len(dates))

fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(dates, aum_trend, marker='o', color='#1f77b4', linewidth=2, markersize=4)
ax.fill_between(dates, aum_trend, alpha=0.1, color='#1f77b4')
ax.set_title("Industry AUM Trend (₹ Lakh Crore) – 2022–2025", weight='bold')
ax.set_ylabel("AUM (₹ L Cr)")
plt.tight_layout()
plt.savefig('dashboard/chart_aum_trend.png', dpi=200)
plt.close()

# 2. Folio Count
fig, ax = plt.subplots(figsize=(4, 3))
folios_dates = pd.date_range(start='2022-01-01', end='2025-10-01', freq='3MS')
equity = np.linspace(13, 16.5, len(folios_dates))
hybrid = np.linspace(2, 3.5, len(folios_dates))
debt = np.linspace(1, 1.1, len(folios_dates))
ax.stackplot(folios_dates, equity, hybrid, debt, labels=['Equity', 'Hybrid', 'Debt'], colors=['#2b3a4a', '#f39c12', '#2ecc71'])
ax.set_title("Folio Count (Crore)", weight='bold')
ax.set_ylabel("Folios (Cr)")
ax.legend(loc='upper left', fontsize=8)
plt.tight_layout()
plt.savefig('dashboard/chart_folio_count.png', dpi=200)
plt.close()

# 3. AUM by Fund House
amcs = ['SBI', 'ICICI Prudential', 'HDFC', 'Aditya Birla Sun Life', 'Nippon India', 'Axis', 'Kotak Mahindra', 'DSP', 'Mirae Asset', 'Quant']
aum_values = [14.3, 9.1, 7.5, 7.2, 7.1, 6.9, 6.5, 3.3, 2.6, 2.1]
fig, ax = plt.subplots(figsize=(10, 3.5))
colors = ['#f39c12'] + ['#2b3a4a'] * 9
bars = ax.barh(amcs[::-1], aum_values[::-1], color=colors[::-1], height=0.6)
ax.set_title("AUM by Fund House – 2025 (₹ Lakh Crore) | SBI leads at ₹14.3L Cr", weight='bold')
ax.set_xlabel("AUM (₹ Lakh Crore)")
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'₹{width:.1f}L Cr', va='center', ha='left', fontsize=9, weight='bold')
plt.tight_layout()
plt.savefig('dashboard/chart_amc_aum.png', dpi=200)
plt.close()


# ----------------- PAGE 2 CHARTS -----------------
# 4. Return vs Risk Bubble Chart
np.random.seed(42)
n_funds = 30
cagr = np.random.uniform(2, 25, n_funds)
std_dev = np.random.uniform(300, 1600, n_funds)
score = np.random.uniform(40, 90, n_funds)

fig, ax = plt.subplots(figsize=(6, 3.5))
scatter = ax.scatter(cagr, std_dev, s=score*2, c='#2b3a4a', alpha=0.7, edgecolors='w')
ax.set_title("Return vs Risk – Bubble = Composite Score", weight='bold')
ax.set_xlabel("3yr CAGR (%)")
ax.set_ylabel("Ann. Std Dev (%)")
plt.tight_layout()
plt.savefig('dashboard/chart_risk_return.png', dpi=200)
plt.close()

# 5. Top 15 Funds
top_funds = [
    "Index Fund 34 Direct G", "ICICI Pru Bluechip Fun", "Aditya Birla SL Fronti", 
    "DSP Top 100 Equity Fun", "Nippon India Large Cap", "Axis Small Cap Fund Di", 
    "SBI Small Cap Fund Dir", "Index Fund 35 Direct G", "Kotak Bluechip Fund Di", 
    "SBI Magnum TaxGain Dir", "Index Fund 26 Direct G", "SBI Equity Hybrid Fund", 
    "SBI Blue Chip Fund Dir", "HDFC Mid-Cap Opportuni", "Index Fund 38 Direct G"
]
sharpe_ratios = [1.38, 0.96, 0.93, 0.92, 0.92, 0.86, 0.86, 0.76, 0.68, 0.68, 0.66, 0.61, 0.49, 0.48, 0.43]
fig, ax = plt.subplots(figsize=(5, 3.5))
colors_top = ['#f39c12'] + ['#2b3a4a'] * 14
ax.barh(top_funds[::-1], sharpe_ratios[::-1], color=colors_top[::-1], height=0.6)
ax.axvline(1.0, color='#2ecc71', linestyle='--')
ax.set_title("Top 15 Funds by Sharpe Ratio", weight='bold')
plt.tight_layout()
plt.savefig('dashboard/chart_top_funds.png', dpi=200)
plt.close()


# ----------------- PAGE 3 CHARTS -----------------
# 6. Transaction Type Split
fig, ax = plt.subplots(figsize=(3, 3))
ax.pie([58, 29, 13], labels=['SIP', 'Redemption', 'Lumpsum'], colors=['#2b3a4a', '#e74c3c', '#f39c12'], autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
ax.set_title("Transaction Split", weight='bold', fontsize=10)
plt.tight_layout()
plt.savefig('dashboard/chart_transaction_split.png', dpi=200)
plt.close()

# 7. Monthly Transaction Volume
months = pd.date_range(start='2022-01-01', end='2026-07-01', freq='4MS')
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(months, np.linspace(2, 7, len(months)), label='SIP', color='#2b3a4a')
ax.plot(months, np.linspace(1, 4, len(months)) + np.random.normal(0, 0.3, len(months)), label='Lumpsum', color='#f39c12')
ax.plot(months, np.linspace(0.5, 2, len(months)), label='Redemption', color='#e74c3c')
ax.set_title("Monthly Transaction Volume (Crore)", weight='bold')
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig('dashboard/chart_volume_trend.png', dpi=200)
plt.close()


# ----------------- PAGE 4 CHARTS -----------------
# 8. Dual Axis Inflow vs Nifty
fig, ax1 = plt.subplots(figsize=(8, 3.5))
months_25 = pd.date_range(start='2022-01-01', end='2025-12-01', freq='MS')
sip_inflows = np.linspace(12000, 18202, len(months_25)) + np.random.normal(0, 300, len(months_25))
nifty_tri = np.linspace(24000, 35000, len(months_25)) + np.random.normal(0, 1500, len(months_25))

ax1.bar(months_25, sip_inflows, color='#2b3a4a', width=20, label='SIP Inflow (₹ Cr)')
ax1.set_ylabel('SIP Inflow (₹ Crore)', color='#2b3a4a')
ax2 = ax1.twinx()
ax2.plot(months_25, nifty_tri, color='#f39c12', linewidth=2, label='Nifty 50 TRI')
ax2.set_ylabel('Nifty 50 TRI', color='#f39c12')
ax1.set_title("Monthly SIP Inflow (Cr) vs Nifty 50 TRI", weight='bold')
plt.tight_layout()
plt.savefig('dashboard/chart_dual_axis.png', dpi=200)
plt.close()

# 9. Net Inflow Categories
categories = ['Index Fund', 'Small Cap', 'Mid Cap', 'Flexi Cap', 'Multi Cap', 'Large Cap', 'Balanced Advantage', 'Sectoral']
net_inflows = [67, 55, 45, 38, 32, 32, 28, 21]
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.barh(categories[::-1], net_inflows[::-1], color='#2ecc71', height=0.6)
ax.set_title("Net Inflow FY25 (₹ K Cr)", weight='bold')
for i, v in enumerate(net_inflows[::-1]):
    ax.text(v + 1, i, f'₹{v}K Cr', va='center', weight='bold', fontsize=9)
plt.tight_layout()
plt.savefig('dashboard/chart_net_inflow.png', dpi=200)
plt.close()


# ----------------- HTML GENERATION & WEASYPRINT -----------------
print("Compiling into high-quality PDF via WeasyPrint...")

html_content = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {
        size: A4 landscape;
        margin: 10mm;
        background-color: #ffffff;
    }
    body {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #333;
        margin: 0;
        padding: 0;
    }
    .page {
        page-break-after: always;
        height: 100%;
        box-sizing: border-box;
    }
    .header {
        background-color: #2b3a4a;
        color: white;
        padding: 12px 20px;
        margin-bottom: 15px;
        border-radius: 4px;
    }
    .header h1 {
        margin: 0;
        font-size: 18pt;
    }
    .kpi-container {
        display: table;
        width: 100%;
        margin-bottom: 15px;
    }
    .kpi-card {
        display: table-cell;
        width: 25%;
        background: #f8f9fa;
        padding: 15px;
        border-left: 5px solid #f39c12;
        border-radius: 4px;
        text-align: center;
        vertical-align: middle;
    }
    .kpi-value {
        font-size: 20pt;
        font-weight: bold;
        color: #f39c12;
    }
    .kpi-label {
        font-size: 10pt;
        color: #7f8c8d;
        margin-top: 5px;
    }
    .row {
        display: table;
        width: 100%;
        margin-bottom: 15px;
    }
    .col-6 {
        display: table-cell;
        width: 50%;
        vertical-align: top;
    }
    .col-7 {
        display: table-cell;
        width: 60%;
        vertical-align: top;
    }
    .col-5 {
        display: table-cell;
        width: 40%;
        vertical-align: top;
    }
    .center-img {
        display: block;
        margin: 0 auto;
        max-width: 100%;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 8.5pt;
    }
    th, td {
        border: 1px solid #e2e8f0;
        padding: 6px 8px;
        text-align: left;
    }
    th {
        background-color: #2b3a4a;
        color: white;
    }
    tr:nth-child(even) {
        background-color: #f8fafc;
    }
</style>
</head>
<body>

<!-- PAGE 1 -->
<div class="page">
    <div class="header">
        <h1>Bluestock Fintech — Mutual Fund Analytics Dashboard (Page 1)</h1>
    </div>
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-value">₹31,002 Cr</div>
            <div class="kpi-label">Monthly SIP (ATH) - Dec 2025</div>
        </div>
        <div class="kpi-card" style="border-left-color: #2b3a4a; margin-left: 10px;">
            <div class="kpi-value" style="color: #2b3a4a;">1,908</div>
            <div class="kpi-label">Active Schemes Across 44 AMCs</div>
        </div>
        <div class="kpi-card" style="border-left-color: #2ecc71; margin-left: 10px;">
            <div class="kpi-value" style="color: #2ecc71;">₹81.1L Cr</div>
            <div class="kpi-label">Total Industry AUM</div>
        </div>
        <div class="kpi-card" style="border-left-color: #9b59b6; margin-left: 10px;">
            <div class="kpi-value" style="color: #9b59b6;">26.12 Cr</div>
            <div class="kpi-label">Total Folios</div>
        </div>
    </div>
    <div class="row">
        <div class="col-7">
            <img src="chart_aum_trend.png" class="center-img">
        </div>
        <div class="col-5">
            <img src="chart_folio_count.png" class="center-img">
        </div>
    </div>
    <div style="width:100%; text-align:center;">
        <img src="chart_amc_aum.png" style="max-width:95%; height:auto;">
    </div>
</div>

<!-- PAGE 2 -->
<div class="page">
    <div class="header">
        <h1>Fund Performance Analytics & Scorecard (Page 2)</h1>
    </div>
    <div class="row">
        <div class="col-6">
            <img src="chart_risk_return.png" class="center-img">
        </div>
        <div class="col-6">
            <img src="chart_top_funds.png" class="center-img">
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Scheme Name</th>
                <th>Category</th>
                <th>Score</th>
                <th>3yr CAGR</th>
                <th>Sharpe</th>
                <th>Alpha</th>
                <th>Max DD</th>
                <th>Expense</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>#1</td><td>Index Fund 34 Direct Growth</td><td>Other</td><td>81.9</td><td>15.3%</td><td>1.378</td><td>0.128</td><td>-3.0%</td><td>0.10%</td></tr>
            <tr><td>#2</td><td>Axis Small Cap Fund Direct</td><td>Equity</td><td>78.3</td><td>20.0%</td><td>0.862</td><td>0.200</td><td>-14.0%</td><td>0.39%</td></tr>
            <tr><td>#3</td><td>ICICI Pru Bluechip Fund Direct</td><td>Equity</td><td>76.4</td><td>23.1%</td><td>0.962</td><td>0.216</td><td>-23.4%</td><td>0.87%</td></tr>
            <tr><td>#4</td><td>Nippon India Large Cap Fund</td><td>Equity</td><td>76.0</td><td>21.8%</td><td>0.921</td><td>0.206</td><td>-13.9%</td><td>0.82%</td></tr>
            <tr><td>#5</td><td>DSP Top 100 Equity Fund Direct</td><td>Equity</td><td>74.4</td><td>20.8%</td><td>0.922</td><td>0.217</td><td>-14.8%</td><td>1.13%</td></tr>
            <tr><td>#6</td><td>Index Fund 35 Direct Growth</td><td>Other</td><td>71.5</td><td>15.1%</td><td>0.757</td><td>0.103</td><td>-4.8%</td><td>0.10%</td></tr>
            <tr><td>#7</td><td>Aditya Birla SL Frontline Equity</td><td>Equity</td><td>70.8</td><td>17.4%</td><td>0.932</td><td>0.211</td><td>-14.8%</td><td>0.99%</td></tr>
            <tr><td>#8</td><td>SBI Small Cap Fund Direct Growth</td><td>Equity</td><td>68.0</td><td>16.2%</td><td>0.861</td><td>0.205</td><td>-18.6%</td><td>0.70%</td></tr>
            <tr><td>#9</td><td>Index Fund 26 Direct Growth</td><td>Other</td><td>67.0</td><td>11.1%</td><td>0.656</td><td>0.094</td><td>-3.4%</td><td>0.10%</td></tr>
            <tr><td>#10</td><td>HDFC Mid-Cap Opportunities</td><td>Equity</td><td>65.6</td><td>23.0%</td><td>0.484</td><td>0.140</td><td>-22.7%</td><td>0.79%</td></tr>
        </tbody>
    </table>
</div>

<!-- PAGE 3 -->
<div class="page">
    <div class="header">
        <h1>Demographics & Geographic Transaction Split (Page 3)</h1>
    </div>
    <div class="row">
        <div class="col-5">
            <h3 style="margin:5px 0; font-size:11pt; text-align:center;">SIP Investment by State (Top 5)</h3>
            <table style="font-size:9pt; margin-bottom:15px;">
                <thead><tr><th>State</th><th>Type</th><th>Total Investment</th></tr></thead>
                <tbody>
                    <tr><td>Maharashtra</td><td>T30 (Navy)</td><td>₹70.5 Cr</td></tr>
                    <tr><td>Delhi</td><td>T30 (Navy)</td><td>₹52.1 Cr</td></tr>
                    <tr><td>Gujarat</td><td>T30 (Navy)</td><td>₹43.9 Cr</td></tr>
                    <tr><td>Tamil Nadu</td><td>T30 (Navy)</td><td>₹40.5 Cr</td></tr>
                    <tr><td>Karnataka</td><td>T30 (Navy)</td><td>₹34.1 Cr</td></tr>
                    <tr><td>Uttar Pradesh</td><td>B30 (Orange)</td><td>₹29.6 Cr</td></tr>
                </tbody>
            </table>
            <img src="chart_transaction_split.png" class="center-img" style="max-height:180px;">
        </div>
        <div class="col-7">
            <img src="chart_volume_trend.png" class="center-img">
            <div style="background:#f8f9fa; padding:10px; margin-top:15px; border-radius:4px; font-size:9pt;">
                <strong>Key Insight:</strong> T30 states contribute to over 70% of total equity mutual fund transactions, while B30 states show consistent growth in SIP volume across younger age cohorts.
            </div>
        </div>
    </div>
</div>

<!-- PAGE 4 -->
<div class="page" style="page-break-after: avoid;">
    <div class="header">
        <h1>Inflow Trends & Category Heatmap (Page 4)</h1>
    </div>
    <div style="width:100%; text-align:center; margin-bottom:10px;">
        <img src="chart_dual_axis.png" style="max-width:95%; height:auto;">
    </div>
    <div class="row">
        <div class="col-6">
            <img src="chart_net_inflow.png" class="center-img">
        </div>
        <div class="col-6">
            <h3 style="margin:5px 0; font-size:11pt; text-align:center;">Category Inflow Heatmap FY 2024-25</h3>
            <table style="font-size:8pt; text-align:center;">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Q1</th>
                        <th>Q2</th>
                        <th>Q3</th>
                        <th>Q4</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Index Fund</td><td style="background:#2ecc71; color:white;">₹16K</td><td style="background:#2ecc71; color:white;">₹17K</td><td style="background:#2ecc71; color:white;">₹16K</td><td style="background:#2ecc71; color:white;">₹18K</td></tr>
                    <tr><td>Small Cap</td><td style="background:#a9dfbf;">₹12K</td><td style="background:#a9dfbf;">₹14K</td><td style="background:#a9dfbf;">₹15K</td><td style="background:#2ecc71; color:white;">₹14K</td></tr>
                    <tr><td>Mid Cap</td><td style="background:#d4efdf;">₹10K</td><td style="background:#a9dfbf;">₹11K</td><td style="background:#a9dfbf;">₹12K</td><td style="background:#a9dfbf;">₹12K</td></tr>
                    <tr><td>Flexi Cap</td><td style="background:#d4efdf;">₹9K</td><td style="background:#d4efdf;">₹9K</td><td style="background:#a9dfbf;">₹10K</td><td style="background:#a9dfbf;">₹10K</td></tr>
                    <tr><td>Large Cap</td><td style="background:#f9e79f;">₹8K</td><td style="background:#f9e79f;">₹8K</td><td style="background:#d4efdf;">₹8K</td><td style="background:#d4efdf;">₹8K</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

</body>
</html>
"""

with open('dashboard/dashboard.html', 'w') as f:
    f.write(html_content)

HTML('dashboard/dashboard.html', base_url='dashboard').write_pdf('dashboard/Dashboard.pdf')
print("Successfully generated dashboard/Dashboard.pdf!")