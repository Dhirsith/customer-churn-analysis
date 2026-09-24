"""Create a concise set of labeled churn-analysis charts."""

from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def create_charts(frame: pd.DataFrame, tables: Dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Save the project's six business-focused charts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    palette = {"No": "#3977a8", "Yes": "#d36b55"}
    plot_frame = frame.assign(churn_label=frame["churn"].map({False: "No", True: "Yes"}))

    churn_counts = frame["churn"].map({False: "Retained", True: "Churned"}).value_counts()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.barplot(x=churn_counts.index, y=churn_counts.values, hue=churn_counts.index,
                palette={"Retained": "#3977a8", "Churned": "#d36b55"}, legend=False, ax=ax)
    ax.set(title="Customer churn distribution", xlabel="Customer outcome", ylabel="Customers")
    fig.tight_layout()
    fig.savefig(output_dir / "churn_distribution.png", dpi=150)
    plt.close(fig)

    chart_specs = [
        ("churn_by_contract", "contract", "Churn rate by contract type", "Contract type", "churn_by_contract.png"),
        ("churn_by_tenure_group", "tenure_group", "Churn rate by customer tenure", "Tenure group", "churn_by_tenure_group.png"),
        ("churn_by_payment_method", "payment_method", "Churn rate by payment method", "Payment method", "churn_by_payment_method.png"),
    ]
    for table_name, category, title, xlabel, filename in chart_specs:
        table = tables[table_name].sort_values("churn_rate", ascending=False)
        fig, ax = plt.subplots(figsize=(8, 4.8))
        sns.barplot(data=table, x=category, y="churn_rate", color="#3977a8", ax=ax)
        ax.set(title=title, xlabel=xlabel, ylabel="Churn rate")
        ax.set_ylim(0, min(1.0, float(table["churn_rate"].max()) * 1.18 + 0.03))
        ax.tick_params(axis="x", rotation=20)
        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=150)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    sns.boxplot(data=plot_frame, x="churn_label", y="monthly_charges", hue="churn_label", palette=palette,
                legend=False, ax=ax)
    ax.set(title="Monthly charges by customer outcome", xlabel="Churned",
           ylabel="Monthly charge amount (source units)")
    fig.tight_layout()
    fig.savefig(output_dir / "monthly_charges_by_churn.png", dpi=150)
    plt.close(fig)

    service_chart = tables["churn_by_service"].loc[
        tables["churn_by_service"]["service"].isin(["internet_service", "online_security", "tech_support"])
    ].copy()
    service_chart["service_label"] = (
        service_chart["service"].str.replace("_", " ").str.title()
        + ": "
        + service_chart["service_value"].astype(str)
    )
    service_chart = service_chart.sort_values("churn_rate")
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(data=service_chart, x="churn_rate", y="service_label", color="#4c956c", ax=ax)
    ax.set(title="Churn rate by selected internet services", xlabel="Churn rate", ylabel="Service group")
    ax.set_xlim(0, min(1.0, float(service_chart["churn_rate"].max()) * 1.18 + 0.03))
    fig.tight_layout()
    fig.savefig(output_dir / "churn_by_service.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.histplot(data=plot_frame, x="tenure_months", hue="churn_label", bins=24, multiple="stack",
                 palette=palette, ax=ax)
    ax.set(title="Customer tenure distribution", xlabel="Tenure (months)", ylabel="Customers")
    fig.tight_layout()
    fig.savefig(output_dir / "tenure_distribution.png", dpi=150)
    plt.close(fig)
