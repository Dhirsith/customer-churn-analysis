-- Assumptions: one cleaned row per customer; churn is stored as BOOLEAN.
-- Churn rate = churned customers / all customers in each group.
-- Segment differences are descriptive associations, not causal effects.

-- Overall customer count, churn count, and churn rate.
SELECT COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE churn) AS churned_customers,
       COUNT(*) FILTER (WHERE NOT churn) AS retained_customers,
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate
FROM churn_analysis.customers;

-- Churn by contract type.
SELECT contract, COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE churn) AS churned_customers,
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate
FROM churn_analysis.customers
GROUP BY contract
ORDER BY churn_rate DESC;

-- Tenure groups use the same left-closed month bands as the Python analysis.
WITH tenure_segments AS (
    SELECT customer_id, churn,
           CASE
               WHEN tenure_months < 12 THEN '0–11 months'
               WHEN tenure_months < 24 THEN '12–23 months'
               WHEN tenure_months < 48 THEN '24–47 months'
               ELSE '48–72 months'
           END AS tenure_group
    FROM churn_analysis.customers
)
SELECT tenure_group, COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE churn) AS churned_customers,
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate
FROM tenure_segments
GROUP BY tenure_group
ORDER BY MIN(CASE tenure_group
    WHEN '0–11 months' THEN 1
    WHEN '12–23 months' THEN 2
    WHEN '24–47 months' THEN 3
    ELSE 4
END);

-- Monthly charge bands align with src/analysis.py.
SELECT CASE
           WHEN monthly_charges < 30 THEN '0–<30'
           WHEN monthly_charges < 60 THEN '30–<60'
           WHEN monthly_charges < 90 THEN '60–<90'
           ELSE '90+'
       END AS monthly_charge_group,
       COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE churn) AS churned_customers,
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate,
       AVG(monthly_charges) AS mean_monthly_charges
FROM churn_analysis.customers
GROUP BY monthly_charge_group
ORDER BY MIN(monthly_charges);

-- Churn by payment method.
SELECT payment_method, COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE churn) AS churned_customers,
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate
FROM churn_analysis.customers
GROUP BY payment_method
ORDER BY churn_rate DESC;

-- Service-category comparisons; "No internet service" stays a distinct category.
SELECT 'internet_service' AS service, internet_service AS service_value,
       COUNT(*) AS customers, COUNT(*) FILTER (WHERE churn) AS churned_customers,
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate
FROM churn_analysis.customers
GROUP BY internet_service
UNION ALL
SELECT 'online_security', online_security,
       COUNT(*), COUNT(*) FILTER (WHERE churn),
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0)
FROM churn_analysis.customers
GROUP BY online_security
UNION ALL
SELECT 'tech_support', tech_support,
       COUNT(*), COUNT(*) FILTER (WHERE churn),
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0)
FROM churn_analysis.customers
GROUP BY tech_support
ORDER BY churn_rate DESC;

-- Customer segments by contract and tenure; RANK highlights groups with higher observed churn rates.
WITH segment_counts AS (
    SELECT contract,
           CASE
               WHEN tenure_months < 12 THEN '0–11 months'
               WHEN tenure_months < 24 THEN '12–23 months'
               WHEN tenure_months < 48 THEN '24–47 months'
               ELSE '48–72 months'
           END AS tenure_group,
           COUNT(*) AS customers,
           COUNT(*) FILTER (WHERE churn) AS churned_customers,
           COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate
    FROM churn_analysis.customers
    GROUP BY contract, tenure_group
    HAVING COUNT(*) >= 30
)
SELECT *, RANK() OVER (ORDER BY churn_rate DESC) AS churn_rate_rank
FROM segment_counts
ORDER BY churn_rate_rank, customers DESC;

-- Churn characteristics by demographic segments supported by the source.
SELECT gender, senior_citizen, partner, dependents,
       COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE churn) AS churned_customers,
       COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0) AS churn_rate
FROM churn_analysis.customers
GROUP BY gender, senior_citizen, partner, dependents
HAVING COUNT(*) >= 30
ORDER BY churn_rate DESC, customers DESC;
