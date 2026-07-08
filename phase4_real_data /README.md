# Phase 4 — Real-Data Validation

**The question this phase answers:** *"Your Phase 2 model predicted labels you generated
yourself — does the methodology survive contact with reality?"*

Same pipeline (audit → feature engineering → logistic regression + isolation forest →
decile flagging → honest evaluation), validated on **two independent real datasets**.

## Results across three environments

| | Synthetic (Phase 2) | Crunchbase US | Crunchbase Global |
|---|---|---|---|
| Startups | 110 | 923 | 8,181 |
| Labels | generated archetypes | real acquired/closed | real closed vs acquired/IPO |
| ROC-AUC | 0.957 | 0.798 | 0.811 |
| Flag precision (lift) | 73% | 88% (2.49×) | 91% (2.27×) |
| Top failure driver | churn rate | low total funding | low total funding |

**Honest headline:** AUC drops from 0.96 (synthetic) to ~0.80 (real) — because real startup
failure has drivers no dataset captures. Consistent across both real datasets: capital access
dominates. Performance degrades gracefully as features get sparser, tracking information
content rather than overfitting artifacts.

## Data provenance & limitations
- `crunchbase_startups.csv` — 923 US startups (2005–2013 era), public "Startup Success
  Prediction" Kaggle dataset, originally compiled from Crunchbase. Caveats: acquisition
  used as a success proxy; US/VC-backed skew.
- `crunchbase_66k.csv` — 2015 Crunchbase snapshot (66K companies, global), via
  github.com/notpeter/crunchbase-data. Filtered to resolved outcomes (~8K usable).
  Caveats: pre-2015 era; "operating" companies excluded, which removes slow failures.

## Files
- `real_data_validation.ipynb` — full analysis, executed with outputs
