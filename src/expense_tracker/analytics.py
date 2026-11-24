"""Cleaning and summary calculations for transaction data."""

from __future__ import annotations

import calendar
from typing import Any

import numpy as np
import pandas as pd

from .categorization import suggest_category

REQUIRED_COLUMNS = {"date", "description", "amount"}


def clean_transaction_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Normalize a CSV-like frame and return (valid rows, rejected-row messages)."""
    cleaned = frame.copy()
    cleaned.columns = [str(column).strip().lower() for column in cleaned.columns]
    missing = REQUIRED_COLUMNS - set(cleaned.columns)
    if missing:
        raise ValueError("Missing required column(s): " + ", ".join(sorted(missing)))

    for column, default in {
        "category": "", "type": "expense", "payment_method": "Other", "notes": ""
    }.items():
        if column not in cleaned.columns:
            cleaned[column] = default

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")
    cleaned["description"] = cleaned["description"].fillna("").astype(str).str.strip()
    cleaned["category"] = cleaned["category"].fillna("").astype(str).str.strip()
    cleaned["type"] = cleaned["type"].fillna("expense").astype(str).str.strip().str.lower()
    cleaned["payment_method"] = cleaned["payment_method"].fillna("Other").astype(str).str.strip()
    cleaned["notes"] = cleaned["notes"].fillna("").astype(str).str.strip()
    cleaned["type"] = cleaned["type"].replace("", "expense")
    cleaned["payment_method"] = cleaned["payment_method"].replace("", "Other")

    errors: list[str] = []
    keep: list[bool] = []
    for index, row in cleaned.iterrows():
        issues: list[str] = []
        if pd.isna(row["date"]):
            issues.append("invalid date")
        if not row["description"]:
            issues.append("empty description")
        if pd.isna(row["amount"]) or row["amount"] <= 0:
            issues.append("amount must be a positive number")
        if row["type"] not in {"expense", "income"}:
            issues.append("type must be expense or income")
        keep.append(not issues)
        if issues:
            errors.append(f"Row {index + 2}: " + ", ".join(issues))

    cleaned = cleaned.loc[keep].copy()
    missing_category = cleaned["category"].eq("")
    cleaned.loc[missing_category, "category"] = cleaned.loc[missing_category].apply(
        lambda row: suggest_category(row["description"], row["type"]), axis=1
    )
    cleaned["category"] = cleaned["category"].replace("", "Other")
    cleaned["payment_method"] = cleaned["payment_method"].replace("", "Other")
    cleaned["date"] = pd.to_datetime(cleaned["date"]).dt.normalize()
    cleaned["amount"] = cleaned["amount"].astype(float).round(2)
    return cleaned[["date", "description", "amount", "category", "type", "payment_method", "notes"]].reset_index(drop=True), errors


def get_category_spending(expenses: pd.DataFrame) -> pd.DataFrame:
    """Group expenses by category and sort descending by amount.
    
    Tie behavior: If amounts are equal, sort alphabetically by category ascending.
    """
    if expenses.empty:
        return pd.DataFrame(columns=["category", "amount"])
    grouped = (
        expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values(by=["amount", "category"], ascending=[False, True])
        .reset_index(drop=True)
    )
    grouped["amount"] = np.round(grouped["amount"].to_numpy(dtype=float), 2)
    return grouped


def get_monthly_spending(expenses: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly total expenses."""
    if expenses.empty:
        return pd.DataFrame(columns=["month", "amount"])
    expenses_copy = expenses.copy()
    expenses_copy["month"] = expenses_copy["date"].dt.to_period("M").astype(str)
    monthly = (
        expenses_copy.groupby("month", as_index=False)["amount"]
        .sum()
        .sort_values("month")
        .reset_index(drop=True)
    )
    monthly["amount"] = np.round(monthly["amount"].to_numpy(dtype=float), 2)
    return monthly


def get_payment_method_spending(expenses: pd.DataFrame) -> pd.DataFrame:
    """Calculate total expenses per payment method."""
    if expenses.empty:
        return pd.DataFrame(columns=["payment_method", "amount"])
    payment = (
        expenses.groupby("payment_method", as_index=False)["amount"]
        .sum()
        .sort_values(by=["amount", "payment_method"], ascending=[False, True])
        .reset_index(drop=True)
    )
    payment["amount"] = np.round(payment["amount"].to_numpy(dtype=float), 2)
    return payment


def get_daily_spending(expenses: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily expense totals."""
    if expenses.empty:
        return pd.DataFrame(columns=["date", "amount"])
    daily = (
        expenses.groupby("date", as_index=False)["amount"]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )
    daily["amount"] = np.round(daily["amount"].to_numpy(dtype=float), 2)
    return daily


def get_highest_spending_category(category_spending: pd.DataFrame) -> str | None:
    """Return the highest spending category.
    
    Defined tie behavior: When multiple categories share the same maximum spend,
    the category appearing first alphabetically is selected.
    """
    if category_spending.empty:
        return None
    max_amount = category_spending["amount"].max()
    top_candidates = category_spending[category_spending["amount"] == max_amount]
    # Sort alphabetically by category name to ensure deterministic tie-breaking
    sorted_top = top_candidates.sort_values("category")
    return str(sorted_top.iloc[0]["category"])


def get_average_daily_spending(expenses: pd.DataFrame, month_str: str | None = None) -> float:
    """Calculate average daily spending: monthly expenses / calendar days in month.
    
    If month_str (YYYY-MM) is provided, uses that specific month's calendar days.
    Otherwise, computes weighted or average across available months.
    """
    if expenses.empty:
        return 0.0

    if month_str:
        year, month_num = map(int, month_str.split("-"))
        days_in_month = calendar.monthrange(year, month_num)[1]
        total_expense = float(np.sum(expenses["amount"].to_numpy(dtype=float)))
        return round(total_expense / days_in_month, 2)

    monthly_spending = get_monthly_spending(expenses)
    if monthly_spending.empty:
        return 0.0

    month_rates: list[float] = []
    for month, amount in monthly_spending.itertuples(index=False, name=None):
        year, month_num = map(int, month.split("-"))
        days = calendar.monthrange(year, month_num)[1]
        month_rates.append(float(amount) / days)

    return round(float(np.mean(month_rates)), 2)


def get_budget_status(expenses: pd.DataFrame, budgets: dict[str, float]) -> list[dict[str, Any]]:
    """Compare category spending against monthly budgets and detect overspending."""
    status_list: list[dict[str, Any]] = []
    if not budgets:
        return status_list

    category_spending = get_category_spending(expenses)
    spend_map = dict(zip(category_spending["category"], category_spending["amount"]))

    for category, limit in budgets.items():
        actual = float(spend_map.get(category, 0.0))
        remaining = limit - actual
        used_ratio = actual / limit if limit > 0 else (1.0 if actual > 0 else 0.0)
        is_over = actual > limit
        over_by = max(0.0, actual - limit)

        status_list.append({
            "category": category,
            "spent": round(actual, 2),
            "budget": round(limit, 2),
            "remaining": round(remaining, 2),
            "used_ratio": min(used_ratio, 1.0),
            "is_over": is_over,
            "over_by": round(over_by, 2),
        })
    return sorted(status_list, key=lambda x: (not x["is_over"], -x["spent"]))


def analyze_transactions(transactions: pd.DataFrame, selected_month: str | None = None) -> dict[str, object]:
    """Calculate complete expense & income summaries with defensive handling of empty datasets."""
    empty_cat = pd.DataFrame(columns=["category", "amount"])
    empty_month = pd.DataFrame(columns=["month", "amount"])
    empty_pay = pd.DataFrame(columns=["payment_method", "amount"])
    empty_daily = pd.DataFrame(columns=["date", "amount"])

    if transactions.empty:
        return {
            "income": 0.0,
            "expenses": 0.0,
            "net": 0.0,
            "total_spending": 0.0,
            "category_spending": empty_cat,
            "monthly_spending": empty_month,
            "payment_method_spending": empty_pay,
            "daily_spending": empty_daily,
            "highest_spending_category": None,
            "average_daily_spending": 0.0,
        }

    expenses = transactions[transactions["type"].eq("expense")].copy()
    income = transactions[transactions["type"].eq("income")].copy()

    total_expense = round(float(np.sum(expenses["amount"].to_numpy(dtype=float))), 2) if not expenses.empty else 0.0
    total_income = round(float(np.sum(income["amount"].to_numpy(dtype=float))), 2) if not income.empty else 0.0
    net_cash_flow = round(total_income - total_expense, 2)

    cat_spending = get_category_spending(expenses)
    monthly_spending = get_monthly_spending(expenses)
    pay_spending = get_payment_method_spending(expenses)
    daily_spending = get_daily_spending(expenses)

    top_cat = get_highest_spending_category(cat_spending)
    avg_daily = get_average_daily_spending(expenses, month_str=selected_month)

    return {
        "income": total_income,
        "expenses": total_expense,
        "net": net_cash_flow,
        "total_spending": total_expense,
        "category_spending": cat_spending,
        "monthly_spending": monthly_spending,
        "payment_method_spending": pay_spending,
        "daily_spending": daily_spending,
        "highest_spending_category": top_cat,
        "average_daily_spending": avg_daily,
    }
