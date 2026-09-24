"""Load, audit, and clean the IBM Telco customer-level churn sample."""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


SOURCE_TO_CLEAN = {
    "customerID": "customer_id",
    "gender": "gender",
    "SeniorCitizen": "senior_citizen",
    "Partner": "partner",
    "Dependents": "dependents",
    "tenure": "tenure_months",
    "PhoneService": "phone_service",
    "MultipleLines": "multiple_lines",
    "InternetService": "internet_service",
    "OnlineSecurity": "online_security",
    "OnlineBackup": "online_backup",
    "DeviceProtection": "device_protection",
    "TechSupport": "tech_support",
    "StreamingTV": "streaming_tv",
    "StreamingMovies": "streaming_movies",
    "Contract": "contract",
    "PaperlessBilling": "paperless_billing",
    "PaymentMethod": "payment_method",
    "MonthlyCharges": "monthly_charges",
    "TotalCharges": "total_charges",
    "Churn": "churn",
}
BINARY_COLUMNS = [
    "partner",
    "dependents",
    "phone_service",
    "paperless_billing",
]
CATEGORICAL_COLUMNS = [
    "gender",
    "multiple_lines",
    "internet_service",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
    "contract",
    "payment_method",
]
SERVICE_COLUMNS = [
    "phone_service",
    "multiple_lines",
    "internet_service",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
]


def load_raw(path: Path) -> pd.DataFrame:
    """Read the source CSV while preserving IDs and blank TotalCharges values."""
    return pd.read_csv(path, dtype={"customerID": "string", "TotalCharges": "string"})


def _parse_yes_no(series: pd.Series, column: str) -> pd.Series:
    values = series.astype("string").str.strip().str.casefold()
    mapping = {"yes": True, "no": False}
    invalid = values.notna() & ~values.isin(mapping)
    if invalid.any():
        raise ValueError(f"Unexpected values in {column}: {sorted(values[invalid].unique())}")
    return values.map(mapping).astype("boolean")


def clean_customers(raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Standardize values while preserving legitimate incomplete customer rows.

    Exact duplicate records are removed. Conflicting repeated customer IDs fail
    validation rather than being silently resolved. Blank TotalCharges are
    retained as missing because they occur for zero-tenure customers.
    """
    missing_columns = sorted(set(SOURCE_TO_CLEAN) - set(raw.columns))
    if missing_columns:
        raise ValueError("Source is missing expected columns: " + ", ".join(missing_columns))

    frame = raw[list(SOURCE_TO_CLEAN)].rename(columns=SOURCE_TO_CLEAN).copy()
    frame = frame.replace(r"^\s*$", pd.NA, regex=True)
    audit: Dict[str, object] = {
        "input_rows": int(len(frame)),
        "input_columns": int(frame.shape[1]),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "missing_before_cleaning": {str(k): int(v) for k, v in frame.isna().sum().items()},
    }
    frame["customer_id"] = frame["customer_id"].astype("string").str.strip()
    frame["churn"] = frame["churn"].astype("string").str.strip().str.casefold().map(
        {"yes": True, "no": False}
    ).astype("boolean")
    if frame["customer_id"].isna().any() or frame["churn"].isna().any():
        raise ValueError("Customer ID and Churn are required; inspect source target consistency.")

    for column in CATEGORICAL_COLUMNS:
        frame[column] = frame[column].astype("string").str.strip()
        frame[column] = frame[column].replace("", pd.NA)
    for column in BINARY_COLUMNS:
        frame[column] = _parse_yes_no(frame[column], column)

    senior_citizen = pd.to_numeric(frame["senior_citizen"], errors="coerce")
    if senior_citizen.isna().any() or not senior_citizen.isin([0, 1]).all():
        raise ValueError("SeniorCitizen must contain only 0 or 1.")
    frame["senior_citizen"] = senior_citizen.astype(bool)

    numeric_errors: Dict[str, int] = {}
    for column in ("tenure_months", "monthly_charges", "total_charges"):
        source = frame[column]
        converted = pd.to_numeric(source, errors="coerce")
        invalid = source.notna() & converted.isna()
        numeric_errors[column] = int(invalid.sum())
        if invalid.any():
            raise ValueError(f"Non-numeric values found in {column}: {int(invalid.sum())}")
        frame[column] = converted
    audit["invalid_numeric_values"] = numeric_errors
    audit["blank_total_charges"] = int(frame["total_charges"].isna().sum())
    if frame["tenure_months"].isna().any() or frame["monthly_charges"].isna().any():
        raise ValueError("Tenure and MonthlyCharges must be present for every customer.")
    if ((frame["tenure_months"] < 0) | (frame["tenure_months"] > 72)).any():
        raise ValueError("Tenure must be between 0 and 72 months for this source version.")
    if (frame["monthly_charges"] < 0).any() or (frame["total_charges"].dropna() < 0).any():
        raise ValueError("Charge fields cannot be negative.")

    audit["duplicate_customer_ids_before_deduplication"] = int(frame["customer_id"].duplicated().sum())
    frame = frame.drop_duplicates().reset_index(drop=True)
    if frame["customer_id"].duplicated().any():
        raise ValueError("Conflicting duplicate customer IDs found; rows were not silently removed.")
    frame["tenure_months"] = frame["tenure_months"].astype("int64")
    frame["churn"] = frame["churn"].astype(bool)
    audit["output_rows"] = int(len(frame))
    audit["duplicate_rows_removed"] = int(audit["input_rows"] - len(frame))
    audit["missing_after_cleaning"] = {str(k): int(v) for k, v in frame.isna().sum().items()}
    audit["churn_labels"] = {
        "churned": int(frame["churn"].sum()),
        "retained": int((~frame["churn"]).sum()),
    }
    return frame, audit
