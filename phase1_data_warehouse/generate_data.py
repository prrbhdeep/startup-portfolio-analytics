"""
Synthetic Startup Portfolio Data Generator
Generates realistic data for 110 startups with 24 months of metrics each.
Mimics an incubator portfolio: mix of healthy, struggling, and at-risk startups.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

N_STARTUPS = 110
N_MONTHS = 24

SECTORS = ["SaaS", "FinTech", "HealthTech", "EdTech", "AgriTech",
           "DeepTech", "D2C", "CleanTech", "Logistics", "AI/ML"]
STAGES = ["Pre-Seed", "Seed", "Pre-Series A", "Series A"]

# --- Startup master table ---
startups = pd.DataFrame({
    "startup_id": [f"S{i:03d}" for i in range(1, N_STARTUPS + 1)],
    "name": [f"Startup_{i:03d}" for i in range(1, N_STARTUPS + 1)],
    "sector": np.random.choice(SECTORS, N_STARTUPS),
    "stage": np.random.choice(STAGES, N_STARTUPS, p=[0.35, 0.35, 0.20, 0.10]),
    "founded_year": np.random.choice(range(2019, 2025), N_STARTUPS),
    "team_size": np.random.randint(2, 45, N_STARTUPS),
    "total_funding_inr_lakhs": np.round(np.random.lognormal(4.5, 1.1, N_STARTUPS), 1),
})

# Assign each startup a hidden "health archetype" that drives its metrics
# 60% healthy, 25% struggling, 15% at-risk
archetypes = np.random.choice(["healthy", "struggling", "at_risk"],
                              N_STARTUPS, p=[0.60, 0.25, 0.15])
startups["_archetype"] = archetypes  # hidden; used for generation & validation

# --- Monthly metrics table ---
rows = []
months = pd.date_range("2024-07-01", periods=N_MONTHS, freq="MS")

for _, s in startups.iterrows():
    arch = s["_archetype"]
    if arch == "healthy":
        base_growth, growth_sd = 0.06, 0.06
        churn_base, burn_trend = 0.05, -0.003   # burn improving
    elif arch == "struggling":
        base_growth, growth_sd = 0.02, 0.07
        churn_base, burn_trend = 0.07, 0.002
    else:  # at_risk
        base_growth, growth_sd = -0.01, 0.08
        churn_base, burn_trend = 0.10, 0.005    # burn worsening

    # Real portfolios are messy: startup-level idiosyncrasy blurs archetypes.
    # Some healthy startups look shaky; some at-risk ones mask their decline.
    base_growth += np.random.normal(0, 0.035)
    churn_base = max(churn_base + np.random.normal(0, 0.03), 0.005)

    revenue = np.random.lognormal(2.5, 0.8)          # INR lakhs / month
    burn = revenue * np.random.uniform(1.2, 3.0)     # burning more than earning
    cash = s["total_funding_inr_lakhs"] * np.random.uniform(0.4, 0.9)
    users = int(np.random.lognormal(6, 1.2))

    for m in months:
        growth = np.random.normal(base_growth, growth_sd)
        revenue = max(revenue * (1 + growth), 0.1)
        burn = max(burn * (1 + burn_trend + np.random.normal(0, 0.02)), 0.5)
        churn = np.clip(np.random.normal(churn_base, 0.02), 0.001, 0.5)
        users = max(int(users * (1 + growth - churn + np.random.normal(0.01, 0.02))), 10)
        net_burn = burn - revenue
        cash = max(cash - max(net_burn, 0), 0)
        runway = round(cash / net_burn, 1) if net_burn > 0 else 99.0

        rows.append({
            "startup_id": s["startup_id"],
            "month": m.strftime("%Y-%m"),
            "revenue_inr_lakhs": round(revenue, 2),
            "burn_inr_lakhs": round(burn, 2),
            "cash_balance_inr_lakhs": round(cash, 2),
            "runway_months": min(runway, 99.0),
            "active_users": users,
            "monthly_churn_rate": round(churn, 4),
            "mom_growth_rate": round(growth, 4),
        })

metrics = pd.DataFrame(rows)

# --- Realistic data-quality issues (startups self-report inconsistently) ---
rng = np.random.default_rng(7)
# ~4% of churn and growth values missing (startups skip reporting)
for col in ["monthly_churn_rate", "mom_growth_rate"]:
    mask = rng.random(len(metrics)) < 0.04
    metrics.loc[mask, col] = np.nan
# ~2% of revenue figures have reporting noise (rounded/estimated by founders)
mask = rng.random(len(metrics)) < 0.02
metrics.loc[mask, "revenue_inr_lakhs"] = (
    metrics.loc[mask, "revenue_inr_lakhs"] * rng.uniform(0.85, 1.15, mask.sum())
).round(0)

# Save
startups.drop(columns="_archetype").to_csv("../data/startups.csv", index=False)
startups[["startup_id", "_archetype"]].to_csv("../data/_ground_truth.csv", index=False)
metrics.to_csv("../data/monthly_metrics.csv", index=False)

print(f"Generated {len(startups)} startups, {len(metrics)} monthly records")
print("\nArchetype distribution:")
print(startups["_archetype"].value_counts())
print("\nSample metrics:")
print(metrics.head(3).to_string())
