"""Calculate reproducible churn metrics and business-facing segment tables."""

import json
from pathlib import Path
from typing import Dict

import pandas as pd

from src.data_cleaning import SERVICE_COLUMNS
from src.visualisation import create_charts


TENURE_BINS = [0, 12, 24, 48, 73]
TENURE_LABELS = ["0–11 months", "12–23 months", "24–47 months", "48–72 months"]
CHARGE_BINS = [0, 30, 60, 90, 121]
CHARGE_LABELS = ["0–<30", "30–<60", "60–<90", "90+"]
DEMOGRAPHIC_COLUMNS = ["gender", "senior_citizen", "partner", "dependents"]


def _display_values(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.map({True: "Yes", False: "No"}).astype("string").fillna("Unknown")
    return series.astype("string").fillna("Unknown")


def summarize_churn(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return customer count, churn count, and churn rate for one segment field."""
    work = frame[[column, "churn"]].copy()
    work[column] = _display_values(work[column])
    result = (
        work.groupby(column, dropna=False, observed=True)["churn"]
        .agg(customers="size", churned_customers="sum", churn_rate="mean")
        .reset_index()
    )
    result["retained_customers"] = result["customers"] - result["churned_customers"]
    return result


def build_analysis(frame: pd.DataFrame, output_dir: Path) -> Dict[str, object]:
    """Write summary tables and charts from the cleaned customer-grain data."""
    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = output_dir.parent / "charts"
    frame = frame.copy()
    frame["tenure_group"] = pd.cut(
        frame["tenure_months"], bins=TENURE_BINS, labels=TENURE_LABELS, right=False
    )
    frame["monthly_charge_group"] = pd.cut(
        frame["monthly_charges"], bins=CHARGE_BINS, labels=CHARGE_LABELS, right=False
    )
    if frame[["tenure_group", "monthly_charge_group"]].isna().any().any():
        raise ValueError("Tenure or monthly charge fell outside the documented analysis bands.")

    tables: Dict[str, pd.DataFrame] = {}
    tables["churn_by_contract"] = summarize_churn(frame, "contract")
    tables["churn_by_tenure_group"] = summarize_churn(frame, "tenure_group")
    tables["churn_by_monthly_charge_group"] = summarize_churn(frame, "monthly_charge_group")
    tables["churn_by_payment_method"] = summarize_churn(frame, "payment_method")
    tables["churn_by_demographics"] = pd.concat(
        [summarize_churn(frame, column).assign(demographic=column) for column in DEMOGRAPHIC_COLUMNS],
        ignore_index=True,
    )
    service_parts = []
    for column in SERVICE_COLUMNS:
        part = summarize_churn(frame, column).rename(columns={column: "service_value"})
        part["service"] = column
        service_parts.append(part)
    tables["churn_by_service"] = pd.concat(service_parts, ignore_index=True)[
        ["service", "service_value", "customers", "churned_customers", "churn_rate", "retained_customers"]
    ]
    churned = frame.loc[frame["churn"]]
    characteristics = []
    for column in ["contract", "payment_method", "internet_service", "gender", "senior_citizen"]:
        values = _display_values(churned[column])
        counts = values.value_counts(dropna=False)
        characteristics.extend(
            {
                "characteristic": column,
                "category": str(value),
                "churned_customers": int(count),
                "share_of_churned_customers": float(count / max(len(churned), 1)),
            }
            for value, count in counts.items()
        )
    tables["churned_customer_characteristics"] = pd.DataFrame(characteristics)
    tables["churn_by_contract_tenure"] = (
        frame.assign(contract=frame["contract"].astype("string"))
        .groupby(["contract", "tenure_group"], observed=True)["churn"]
        .agg(customers="size", churned_customers="sum", churn_rate="mean")
        .reset_index()
        .query("customers >= 30")
        .sort_values(["churn_rate", "customers"], ascending=[False, False])
        .reset_index(drop=True)
    )
    numeric_columns = ["tenure_months", "monthly_charges", "total_charges"]
    tables["customer_profile_by_churn"] = (
        frame.groupby("churn")[numeric_columns]
        .agg(["count", "mean", "median"])
        .round(2)
    )

    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)

    total_customers = int(len(frame))
    churned_customers = int(frame["churn"].sum())
    churn_rate = float(frame["churn"].mean())
    contract_table = tables["churn_by_contract"].sort_values("churn_rate", ascending=False)
    tenure_table = tables["churn_by_tenure_group"].sort_values("churn_rate", ascending=False)
    payment_table = tables["churn_by_payment_method"].sort_values("churn_rate", ascending=False)
    summary: Dict[str, object] = {
        "customers": total_customers,
        "churned_customers": churned_customers,
        "retained_customers": total_customers - churned_customers,
        "churn_rate": round(churn_rate, 6),
        "churn_rate_percent": round(churn_rate * 100, 2),
        "median_tenure_months": round(float(frame["tenure_months"].median()), 2),
        "median_monthly_charges": round(float(frame["monthly_charges"].median()), 2),
        "median_total_charges": round(float(frame["total_charges"].median()), 2),
        "highest_churn_contract": str(contract_table.iloc[0]["contract"]),
        "highest_churn_contract_rate": round(float(contract_table.iloc[0]["churn_rate"]), 6),
        "highest_churn_tenure_group": str(tenure_table.iloc[0]["tenure_group"]),
        "highest_churn_tenure_group_rate": round(float(tenure_table.iloc[0]["churn_rate"]), 6),
        "highest_churn_payment_method": str(payment_table.iloc[0]["payment_method"]),
        "highest_churn_payment_method_rate": round(float(payment_table.iloc[0]["churn_rate"]), 6),
        "definitions": {
            "churn_rate": "Churned customers divided by customers in the stated group.",
            "tenure_groups": TENURE_LABELS,
            "monthly_charge_groups_source_units": CHARGE_LABELS,
            "association_caveat": "Descriptive association; does not establish cause or future behavior.",
        },
    }
    (output_dir / "churn_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    create_charts(frame, tables, charts_dir)
    return summary
