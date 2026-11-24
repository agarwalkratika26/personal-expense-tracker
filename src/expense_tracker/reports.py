"""Monthly report generation helpers."""

from __future__ import annotations

import calendar
import io

import pandas as pd

from .analytics import analyze_transactions


def monthly_report_csv(
    transactions: pd.DataFrame,
    month: str,
    budgets: dict[str, float],
    currency_code: str = "INR",
) -> bytes:
    """Build a comprehensive CSV report with KPIs, budget comparisons, payment methods, and transactions."""
    month_frame = (
        transactions[transactions["date"].dt.strftime("%Y-%m") == month].copy()
        if not transactions.empty
        else transactions.copy()
    )
    analysis = analyze_transactions(month_frame, selected_month=month)

    rows: list[dict[str, object]] = []

    # Metadata & Executive Summary Section
    rows.append({"section": "metadata", "month": month, "category": "Report Currency", "amount": currency_code,
                 "budget": "", "date": "", "description": "", "type": "", "payment_method": ""})
    rows.append({"section": "summary", "month": month, "category": "Total Income", "amount": analysis["income"],
                 "budget": "", "date": "", "description": "", "type": "income", "payment_method": ""})
    rows.append({"section": "summary", "month": month, "category": "Total Expenses", "amount": analysis["expenses"],
                 "budget": "", "date": "", "description": "", "type": "expense", "payment_method": ""})
    rows.append({"section": "summary", "month": month, "category": "Net Cash Flow", "amount": analysis["net"],
                 "budget": "", "date": "", "description": "", "type": "", "payment_method": ""})
    rows.append({"section": "summary", "month": month, "category": "Average Daily Spending", "amount": analysis["average_daily_spending"],
                 "budget": "", "date": "", "description": "", "type": "expense", "payment_method": ""})
    top_cat = analysis["highest_spending_category"] or "None"
    rows.append({"section": "summary", "month": month, "category": f"Highest Spending Category: {top_cat}",
                 "amount": "", "budget": "", "date": "", "description": "", "type": "expense", "payment_method": ""})

    # Category Totals & Budget Comparison Section
    cat_df: pd.DataFrame = analysis["category_spending"]  # type: ignore
    for row in cat_df.itertuples(index=False):
        budget_limit = budgets.get(row.category, "")
        rows.append({
            "section": "category_budget",
            "month": month,
            "category": row.category,
            "amount": row.amount,
            "budget": budget_limit,
            "date": "",
            "description": f"Remaining: {round(budget_limit - row.amount, 2)}" if budget_limit != "" else "",
            "type": "expense",
            "payment_method": "",
        })

    # Payment Methods Section
    pay_df: pd.DataFrame = analysis["payment_method_spending"]  # type: ignore
    for row in pay_df.itertuples(index=False):
        rows.append({
            "section": "payment_method",
            "month": month,
            "category": row.payment_method,
            "amount": row.amount,
            "budget": "",
            "date": "",
            "description": "",
            "type": "expense",
            "payment_method": row.payment_method,
        })

    # Itemized Transactions Section
    for row in month_frame.itertuples(index=False):
        rows.append({
            "section": "transaction",
            "month": month,
            "category": row.category,
            "amount": round(float(row.amount), 2),
            "budget": "",
            "date": row.date.strftime("%Y-%m-%d"),
            "description": row.description,
            "type": row.type,
            "payment_method": row.payment_method,
        })

    output = io.StringIO()
    cols = ["section", "month", "category", "amount", "budget", "date", "description", "type", "payment_method"]
    pd.DataFrame(rows, columns=cols).to_csv(output, index=False)
    return output.getvalue().encode("utf-8-sig")


def month_label(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{calendar.month_name[number]} {year}"
