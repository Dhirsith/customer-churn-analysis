import pandas as pd

from src.analysis import build_analysis, summarize_churn
from src.data_cleaning import clean_customers


def sample_raw():
    base = {
        "gender": " Female ",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "DSL",
        "OnlineSecurity": "No",
        "OnlineBackup": "No",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "PaperlessBilling": "Yes",
    }
    rows = []
    for customer_id, tenure, monthly, total, contract, payment, churn in [
        (" C001 ", 1, 30.0, "30.0", "Month-to-month", "Electronic check", " Yes "),
        ("C002", 13, 50.0, " ", "One year", "Bank transfer (automatic)", "No"),
        ("C003", 30, 80.0, "2400.0", "Month-to-month", "Electronic check", "Yes"),
        ("C004", 60, 100.0, "6000.0", "One year", "Credit card (automatic)", "No"),
    ]:
        rows.append(
            {
                **base,
                "customerID": customer_id,
                "tenure": tenure,
                "MonthlyCharges": monthly,
                "TotalCharges": total,
                "Contract": contract,
                "PaymentMethod": payment,
                "Churn": churn,
            }
        )
    return pd.DataFrame(rows)


def test_cleaning_removes_exact_duplicates_and_preserves_expected_missing_values():
    raw = sample_raw()
    raw = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)

    cleaned, audit = clean_customers(raw)

    assert len(cleaned) == 4
    assert audit["exact_duplicate_rows"] == 1
    assert audit["duplicate_rows_removed"] == 1
    assert cleaned.loc[cleaned["customer_id"] == "C001", "gender"].iloc[0] == "Female"
    assert pd.isna(cleaned.loc[cleaned["customer_id"] == "C002", "total_charges"].iloc[0])
    assert audit["blank_total_charges"] == 1
    assert cleaned["churn"].sum() == 2


def test_conflicting_duplicate_customer_ids_are_not_silently_resolved():
    raw = sample_raw()
    duplicate = raw.iloc[[0]].copy()
    duplicate.loc[:, "MonthlyCharges"] = 99.0
    raw = pd.concat([raw, duplicate], ignore_index=True)

    try:
        clean_customers(raw)
    except ValueError as error:
        assert "Conflicting duplicate customer IDs" in str(error)
    else:
        raise AssertionError("Conflicting customer IDs should fail validation.")


def test_churn_rate_counts_and_analysis_outputs_are_consistent(tmp_path):
    cleaned, _ = clean_customers(sample_raw())
    contract_summary = summarize_churn(cleaned, "contract").set_index("contract")

    assert contract_summary.loc["Month-to-month", "customers"] == 2
    assert contract_summary.loc["Month-to-month", "churned_customers"] == 2
    assert contract_summary.loc["Month-to-month", "churn_rate"] == 1.0
    assert contract_summary.loc["One year", "churn_rate"] == 0.0

    summary = build_analysis(cleaned, tmp_path / "tables")
    assert summary["customers"] == 4
    assert summary["churned_customers"] == 2
    assert summary["churn_rate"] == 0.5
    assert summary["median_monthly_charges"] == 65.0
    assert (tmp_path / "tables/churn_by_contract.csv").is_file()
    assert (tmp_path / "charts/churn_distribution.png").is_file()
    assert (tmp_path / "charts/churn_by_service.png").is_file()
