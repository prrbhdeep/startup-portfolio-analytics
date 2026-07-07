"""
Phase 2: Multi-Model Startup Risk Assessment
- Feature engineering from monthly KPIs (runway, growth, burn efficiency, churn)
- Logistic regression: supervised risk prediction
- Isolation Forest: unsupervised anomaly detection as a second signal
- Combines both into a risk score; flags bottom 10% of portfolio each month
- Validates against hidden ground-truth health labels
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

# ---------- 1. Load ----------
metrics = pd.read_csv("../data/monthly_metrics.csv")
truth = pd.read_csv("../data/_ground_truth.csv")
truth["is_at_risk"] = (truth["_archetype"] == "at_risk").astype(int)

# ---------- 2. Feature engineering (per startup, using trailing 6 months) ----------
metrics = metrics.sort_values(["startup_id", "month"])
last6 = metrics.groupby("startup_id").tail(6)

features = last6.groupby("startup_id").agg(
    avg_growth=("mom_growth_rate", "mean"),
    growth_volatility=("mom_growth_rate", "std"),
    avg_churn=("monthly_churn_rate", "mean"),
    latest_runway=("runway_months", "last"),
    avg_burn=("burn_inr_lakhs", "mean"),
    avg_revenue=("revenue_inr_lakhs", "mean"),
    latest_cash=("cash_balance_inr_lakhs", "last"),
).reset_index()

features["burn_efficiency"] = features["avg_revenue"] / features["avg_burn"]
features["runway_capped"] = features["latest_runway"].clip(upper=36)

df = features.merge(truth[["startup_id", "is_at_risk"]], on="startup_id")

FEATURE_COLS = ["avg_growth", "growth_volatility", "avg_churn",
                "runway_capped", "burn_efficiency", "latest_cash"]

X = df[FEATURE_COLS].fillna(0)
y = df["is_at_risk"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ---------- 3. Model 1: Logistic Regression ----------
X_tr, X_te, y_tr, y_te = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42, stratify=y)

logreg = LogisticRegression(class_weight="balanced", random_state=42)
logreg.fit(X_tr, y_tr)

print("=== Logistic Regression (held-out 30%) ===")
print(classification_report(y_te, logreg.predict(X_te),
                            target_names=["healthy/struggling", "at_risk"]))
print(f"ROC-AUC: {roc_auc_score(y_te, logreg.predict_proba(X_te)[:, 1]):.3f}\n")

# Feature importances (coefficients)
coefs = pd.Series(logreg.coef_[0], index=FEATURE_COLS).sort_values()
print("Risk drivers (logistic coefficients):")
print(coefs.to_string(), "\n")

# ---------- 4. Model 2: Isolation Forest (unsupervised second signal) ----------
iso = IsolationForest(contamination=0.15, random_state=42)
iso.fit(X_scaled)
# anomaly score: lower = more anomalous -> invert to 0-1 risk
anomaly_raw = -iso.score_samples(X_scaled)
anomaly_score = (anomaly_raw - anomaly_raw.min()) / (anomaly_raw.max() - anomaly_raw.min())

# ---------- 5. Combined risk score & bottom-10% flagging ----------
df["p_risk_logreg"] = logreg.predict_proba(X_scaled)[:, 1]
df["anomaly_score"] = anomaly_score
df["risk_score"] = 0.7 * df["p_risk_logreg"] + 0.3 * df["anomaly_score"]

n_flag = max(int(len(df) * 0.10), 1)
df["flagged_bottom10"] = 0
df.loc[df["risk_score"].nlargest(n_flag).index, "flagged_bottom10"] = 1

# ---------- 6. Validation of the flagging system ----------
flagged = df[df["flagged_bottom10"] == 1]
precision_at_10 = flagged["is_at_risk"].mean()
recall_of_at_risk = flagged["is_at_risk"].sum() / df["is_at_risk"].sum()

print("=== Bottom-10% Flagging Validation ===")
print(f"Startups flagged: {n_flag}")
print(f"Precision@10%: {precision_at_10:.2f} (share of flagged that are truly at-risk)")
print(f"Recall of at-risk cohort: {recall_of_at_risk:.2f}")

df.sort_values("risk_score", ascending=False).to_csv("risk_scores.csv", index=False)
print("\nSaved risk_scores.csv — top 5 riskiest:")
print(df.nlargest(5, "risk_score")[["startup_id", "risk_score",
      "latest_runway", "avg_churn", "is_at_risk"]].to_string(index=False))
