# Cleaning and Analysis Methodology

## Source and grain

The source is IBM's Telco Customer Churn sample CSV at a pinned Git commit. Each row represents one customer. The dataset is a fictional telco sample, not observed company production data.

## Cleaning decisions

- Preserve customer IDs as strings; trim whitespace in IDs and categorical labels.
- Convert Yes/No fields to booleans and validate the binary SeniorCitizen field as 0/1.
- Parse tenure, monthly charges, and total charges as numeric values. Reject nonnumeric values and impossible negative charge or out-of-range tenure values.
- Keep the 11 blank TotalCharges values as missing (the source uses blanks for zero-tenure customers). Do not impute them and do not drop those rows.
- Remove exact duplicate records. If the same customer ID has conflicting records, stop with an error instead of choosing one silently.
- Preserve all other rows. Unknown target labels, missing customer IDs, and missing required tenure/monthly-charge values fail validation so data issues are visible.

## Metrics and segments

Churn rate is churned customers divided by all customers in a segment. Denominators and churn counts are written together in every segment table. Tenure bands are 0–11, 12–23, 24–47, and 48–72 months. Monthly charge bands are 0–<30, 30–<60, 60–<90, and 90+ in the source's unlabeled charge units. Contract-by-tenure segments with fewer than 30 customers are excluded from the ranked group table to avoid emphasizing very small groups; this is a display threshold, not a statistical significance test.

## Interpretation

Results are descriptive associations in this sample. Contract type, service selections, payment method, tenure, charges, and demographics are correlated with each other; these group comparisons do not identify causal effects. This sample does not represent current or real-world telecom operations.

## SQL

SQL assumes the cleaned CSV has been loaded into churn_analysis.customers using sql/schema.sql. sql/churn_analysis.sql uses the same churn-rate denominator, tenure bands, monthly-charge bands, and 30-customer segment threshold as Python. Queries are PostgreSQL syntax-parsed in tests. They have not been executed against a live PostgreSQL server in this project run.
