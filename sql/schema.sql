CREATE SCHEMA IF NOT EXISTS churn_analysis;

CREATE TABLE IF NOT EXISTS churn_analysis.customers (
    customer_id         TEXT PRIMARY KEY,
    gender              TEXT,
    senior_citizen      BOOLEAN,
    partner             BOOLEAN,
    dependents          BOOLEAN,
    tenure_months       INTEGER NOT NULL CHECK (tenure_months BETWEEN 0 AND 72),
    phone_service       BOOLEAN,
    multiple_lines      TEXT,
    internet_service    TEXT,
    online_security     TEXT,
    online_backup       TEXT,
    device_protection   TEXT,
    tech_support        TEXT,
    streaming_tv        TEXT,
    streaming_movies    TEXT,
    contract            TEXT,
    paperless_billing   BOOLEAN,
    payment_method      TEXT,
    monthly_charges     NUMERIC(10, 2) NOT NULL CHECK (monthly_charges >= 0),
    total_charges       NUMERIC(12, 2),
    churn               BOOLEAN NOT NULL
);
