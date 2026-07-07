"""
Phase 3: Portfolio Health Dashboard
Interactive Plotly dashboard tracking ROI proxies, scalability, and sector
trends across the incubator portfolio. Outputs a standalone HTML file.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------- Load ----------
startups = pd.read_csv("../data/startups.csv")
metrics = pd.read_csv("../data/monthly_metrics.csv")
risk = pd.read_csv("../phase2_risk_model/risk_scores.csv")

df = metrics.merge(startups, on="startup_id")
latest = df.sort_values("month").groupby("startup_id").tail(1)
latest = latest.merge(risk[["startup_id", "risk_score", "flagged_bottom10"]],
                      on="startup_id")

# ---------- Aggregations ----------
# Sector trends: total revenue by sector over time
sector_rev = df.groupby(["month", "sector"])["revenue_inr_lakhs"].sum().reset_index()

# Portfolio-level monthly totals
port = df.groupby("month").agg(
    revenue=("revenue_inr_lakhs", "sum"),
    burn=("burn_inr_lakhs", "sum"),
).reset_index()
port["efficiency"] = port["revenue"] / port["burn"]

# Scalability: growth vs burn efficiency per startup (latest snapshot)
last6 = df.sort_values("month").groupby("startup_id").tail(6)
scal = last6.groupby("startup_id").agg(
    avg_growth=("mom_growth_rate", "mean"),
    avg_rev=("revenue_inr_lakhs", "mean"),
    avg_burn=("burn_inr_lakhs", "mean"),
    sector=("sector", "last"),
).reset_index()
scal["burn_efficiency"] = scal["avg_rev"] / scal["avg_burn"]
scal = scal.merge(risk[["startup_id", "risk_score"]], on="startup_id")

# ---------- Dashboard ----------
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Sector Revenue Trends (INR Lakhs)",
        "Portfolio Burn Efficiency Over Time",
        "Scalability Map: Growth vs Burn Efficiency",
        "Risk Distribution Across Portfolio",
    ),
    specs=[[{"type": "scatter"}, {"type": "scatter"}],
           [{"type": "scatter"}, {"type": "histogram"}]],
)

# 1. Sector revenue trends
for sector in sector_rev["sector"].unique():
    s = sector_rev[sector_rev["sector"] == sector]
    fig.add_trace(go.Scatter(x=s["month"], y=s["revenue_inr_lakhs"],
                             name=sector, mode="lines", legendgroup="sectors"),
                  row=1, col=1)

# 2. Portfolio burn efficiency
fig.add_trace(go.Scatter(x=port["month"], y=port["efficiency"],
                         name="Revenue / Burn", mode="lines+markers",
                         line=dict(color="#2ca02c", width=3), showlegend=False),
              row=1, col=2)
fig.add_hline(y=1.0, line_dash="dash", line_color="gray", row=1, col=2)

# 3. Scalability map (bubble = revenue, color = risk)
fig.add_trace(go.Scatter(
    x=scal["burn_efficiency"], y=scal["avg_growth"], mode="markers",
    marker=dict(size=scal["avg_rev"].clip(2, 40), color=scal["risk_score"],
                colorscale="RdYlGn_r", showscale=True,
                colorbar=dict(title="Risk", x=0.45, y=0.18, len=0.35)),
    text=scal["startup_id"] + " (" + scal["sector"] + ")",
    hovertemplate="%{text}<br>Efficiency: %{x:.2f}<br>Growth: %{y:.1%}",
    showlegend=False), row=2, col=1)

# 4. Risk score distribution
fig.add_trace(go.Histogram(x=risk["risk_score"], nbinsx=25,
                           marker_color="#d62728", showlegend=False),
              row=2, col=2)

fig.update_layout(
    title=dict(text="Startup Portfolio Health Dashboard — 110 Startups, 24 Months",
               font=dict(size=20)),
    height=850, template="plotly_white",
    legend=dict(orientation="h", y=1.08, x=0.0, font=dict(size=9)),
)
fig.update_xaxes(title_text="Burn Efficiency (Rev/Burn)", row=2, col=1)
fig.update_yaxes(title_text="Avg MoM Growth", tickformat=".0%", row=2, col=1)
fig.update_xaxes(title_text="Combined Risk Score", row=2, col=2)

fig.write_html("dashboard.html", include_plotlyjs="cdn")
print("Saved dashboard.html")

# Quick portfolio stats for README
print(f"\nPortfolio snapshot (latest month):")
print(f"  Total revenue: {latest['revenue_inr_lakhs'].sum():,.0f} INR lakhs")
print(f"  Startups burn-efficient (rev>burn): {(latest['revenue_inr_lakhs'] > latest['burn_inr_lakhs']).sum()}")
print(f"  Flagged at-risk: {latest['flagged_bottom10'].sum()}")
