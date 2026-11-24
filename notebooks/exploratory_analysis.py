"""Exploratory Data Analysis script using Matplotlib and Seaborn.

Generates publication-quality static exploratory financial charts:
1. Category-wise spending bar chart with mean benchmark
2. Monthly spending trend line with shaded variance
3. Payment method spending distribution
4. Budget vs. Actual spending comparison highlighting overspending
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from expense_tracker.analytics import clean_transaction_data, get_budget_status
from expense_tracker.synthetic import generate_synthetic_transactions


def run_exploratory_analysis(output_dir: Path | None = None, currency: str = "₹") -> None:
    output_dir = output_dir or (PROJECT_ROOT / "outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate or load clean transaction dataset
    raw_df = generate_synthetic_transactions(count=150, seed=42)
    df, errors = clean_transaction_data(raw_df)
    expenses = df[df["type"] == "expense"].copy()
    expenses["date"] = pd.to_datetime(expenses["date"])
    expenses["month"] = expenses["date"].dt.strftime("%Y-%m")

    # Set Seaborn styling
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "figure.autolayout": True})

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f"Personal Expense Tracker — Static Exploratory Analysis ({currency})", fontsize=18, fontweight="bold")

    # Chart 1: Category-wise spending
    cat_summary = expenses.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
    ax1 = axes[0, 0]
    sns.barplot(data=cat_summary, x="category", y="amount", hue="category", legend=False, ax=ax1, palette="viridis")
    ax1.set_title("Total Spending by Category", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Expense Category", fontsize=12)
    ax1.set_ylabel(f"Total Spent ({currency})", fontsize=12)
    ax1.tick_params(axis="x", rotation=35)
    mean_spend = cat_summary["amount"].mean()
    ax1.axhline(mean_spend, color="red", linestyle="--", label=f"Average Spend ({currency}{mean_spend:,.0f})")
    ax1.legend()

    # Chart 2: Monthly trend
    monthly_summary = expenses.groupby("month")["amount"].sum().reset_index().sort_values("month")
    ax2 = axes[0, 1]
    sns.lineplot(data=monthly_summary, x="month", y="amount", marker="o", ax=ax2, color="#1f77b4", linewidth=2.5)
    ax2.set_title("Monthly Spending Trend", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Calendar Month", fontsize=12)
    ax2.set_ylabel(f"Total Expenses ({currency})", fontsize=12)
    ax2.tick_params(axis="x", rotation=25)

    # Chart 3: Payment Method breakdown
    pay_summary = expenses.groupby("payment_method")["amount"].sum().reset_index().sort_values("amount", ascending=False)
    ax3 = axes[1, 0]
    sns.barplot(data=pay_summary, x="payment_method", y="amount", hue="payment_method", legend=False, ax=ax3, palette="mako")
    ax3.set_title("Spending by Payment Method", fontsize=14, fontweight="bold")
    ax3.set_xlabel("Payment Method", fontsize=12)
    ax3.set_ylabel(f"Amount Spent ({currency})", fontsize=12)
    ax3.tick_params(axis="x", rotation=20)

    # Chart 4: Budget vs Actual (Flagging Overspending)
    budgets = {
        "Groceries": 350.0,
        "Food & Dining": 200.0,
        "Transport": 150.0,
        "Utilities": 100.0,
        "Shopping": 120.0,
    }
    budget_statuses = get_budget_status(expenses, budgets)
    budget_df = pd.DataFrame(budget_statuses)

    ax4 = axes[1, 1]
    if not budget_df.empty:
        plot_df = budget_df.melt(id_vars=["category", "is_over"], value_vars=["spent", "budget"], var_name="Metric", value_name="Amount")
        sns.barplot(data=plot_df, x="category", y="Amount", hue="Metric", ax=ax4, palette={"spent": "#e74c3c", "budget": "#2ecc71"})
        ax4.set_title("Budget vs. Actual Spend (Red = Spent, Green = Budget)", fontsize=14, fontweight="bold")
        ax4.set_xlabel("Category", fontsize=12)
        ax4.set_ylabel(f"Amount ({currency})", fontsize=12)
        ax4.tick_params(axis="x", rotation=25)

        # Highlight overspent categories
        over_cats = budget_df[budget_df["is_over"]]["category"].tolist()
        if over_cats:
            ax4.set_title(f"Budget vs Actual — OVER BUDGET: {', '.join(over_cats)}", fontsize=13, fontweight="bold", color="darkred")

    chart_path = output_dir / "exploratory_spending_analysis.png"
    plt.savefig(chart_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Exploratory chart saved to: {chart_path}")


if __name__ == "__main__":
    run_exploratory_analysis()
