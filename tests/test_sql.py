from pathlib import Path

from pglast import parse_sql


ROOT = Path(__file__).resolve().parents[1]


def test_postgresql_schema_and_analysis_queries_parse():
    for name in ("schema.sql", "churn_analysis.sql"):
        content = (ROOT / "sql" / name).read_text(encoding="utf-8")
        assert parse_sql(content)


def test_sql_uses_the_documented_churn_rate_and_segment_definitions():
    sql = (ROOT / "sql" / "churn_analysis.sql").read_text(encoding="utf-8")
    assert "COUNT(*) FILTER (WHERE churn)::NUMERIC / NULLIF(COUNT(*), 0)" in sql
    assert "WHEN tenure_months < 12 THEN '0–11 months'" in sql
    assert "WHEN monthly_charges < 60 THEN '30–<60'" in sql
    assert "HAVING COUNT(*) >= 30" in sql
    assert "RANK() OVER (ORDER BY churn_rate DESC)" in sql
