-- Startup Portfolio Data Warehouse Schema
-- Centralized warehouse consolidating growth, financial, and PMF indicators

CREATE TABLE startups (
    startup_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    sector          TEXT,
    stage           TEXT,
    founded_year    INTEGER,
    team_size       INTEGER,
    total_funding_inr_lakhs REAL
);

CREATE TABLE monthly_metrics (
    startup_id      TEXT REFERENCES startups(startup_id),
    month           TEXT,               -- YYYY-MM
    revenue_inr_lakhs       REAL,
    burn_inr_lakhs          REAL,
    cash_balance_inr_lakhs  REAL,
    runway_months           REAL,
    active_users            INTEGER,
    monthly_churn_rate      REAL,
    mom_growth_rate         REAL,
    PRIMARY KEY (startup_id, month)
);

-- Derived view: latest health snapshot per startup
CREATE VIEW latest_health AS
SELECT m.*
FROM monthly_metrics m
JOIN (
    SELECT startup_id, MAX(month) AS latest_month
    FROM monthly_metrics
    GROUP BY startup_id
) x ON m.startup_id = x.startup_id AND m.month = x.latest_month;

-- Derived view: burn efficiency (revenue per rupee burned)
CREATE VIEW burn_efficiency AS
SELECT startup_id, month,
       ROUND(revenue_inr_lakhs / NULLIF(burn_inr_lakhs, 0), 3) AS efficiency
FROM monthly_metrics;
