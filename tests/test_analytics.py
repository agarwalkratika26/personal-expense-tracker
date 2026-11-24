"""Unit tests for analytics calculations, cleaning, aggregations, tie-breaks, and budgets."""

import pandas as pd
import pytest
from src.expense_tracker.analytics import (
    analyze_transactions,
    clean_transaction_data,
    get_average_daily_spending,
    get_budget_status,
    get_category_spending,
    get_daily_spending,
    get_highest_spending_category,
    get_monthly_spending,
    get_payment_method_spending,
)


def test_clean_transaction_data_valid_and_invalid():
    raw_data = pd.DataFrame([
        {"date": "2026-06-01", "description": "Grocery store", "amount": "45.00", "type": "expense"},
        {"date": "invalid-date", "description": "Bad Date Item", "amount": "20.00", "type": "expense"},
        {"date": "2026-06-02", "description": "", "amount": "15.00", "type": "expense"},
        {"date": "2026-06-03", "description": "Zero cost item", "amount": "0.00", "type": "expense"},
        {"date": "2026-06-04", "description": "Negative amount", "amount": "-10.00", "type": "expense"},
        {"date": "2026-06-05", "description": "Salary check", "amount": "3000.00", "type": "income"},
    ])
    cleaned, errors = clean_transaction_data(raw_data)
    assert len(cleaned) == 2  # Only row 1 and row 6 are valid
    assert len(errors) == 4  # 4 rows had validation errors
    assert "invalid date" in errors[0]
    assert "empty description" in errors[1]
    assert "amount must be a positive number" in errors[2]


def test_clean_missing_required_columns_raises():
    invalid_frame = pd.DataFrame([{"desc": "No date column", "amount": 10}])
    with pytest.raises(ValueError, match="Missing required column"):
        clean_transaction_data(invalid_frame)


def test_highest_spending_category_tie_behavior():
    # Tie between "Utilities" and "Food & Dining" at 200.00 each
    cat_df = pd.DataFrame([
        {"category": "Utilities", "amount": 200.00},
        {"category": "Food & Dining", "amount": 200.00},
        {"category": "Books", "amount": 50.00},
    ])
    # Alphabetical order: "Food & Dining" comes before "Utilities"
    top = get_highest_spending_category(cat_df)
    assert top == "Food & Dining"


def test_average_daily_spending_calculation():
    # June has 30 days
    expenses = pd.DataFrame([
        {"date": pd.Timestamp("2026-06-01"), "amount": 300.0, "type": "expense"},
        {"date": pd.Timestamp("2026-06-15"), "amount": 600.0, "type": "expense"},
    ])
    # Total = 900.0, Days in June = 30 -> 900 / 30 = 30.0
    avg = get_average_daily_spending(expenses, month_str="2026-06")
    assert avg == 30.0


def test_budget_status_and_overspending():
    expenses = pd.DataFrame([
        {"category": "Groceries", "amount": 600.0, "type": "expense"},
        {"category": "Transport", "amount": 150.0, "type": "expense"},
    ])
    budgets = {"Groceries": 500.0, "Transport": 200.0}
    statuses = get_budget_status(expenses, budgets)

    groceries_status = next(s for s in statuses if s["category"] == "Groceries")
    transport_status = next(s for s in statuses if s["category"] == "Transport")

    assert groceries_status["is_over"] is True
    assert groceries_status["over_by"] == 100.0
    assert groceries_status["remaining"] == -100.0

    assert transport_status["is_over"] is False
    assert transport_status["remaining"] == 50.0


def test_empty_dataset_handling():
    empty_df = pd.DataFrame()
    analysis = analyze_transactions(empty_df)
    assert analysis["expenses"] == 0.0
    assert analysis["income"] == 0.0
    assert analysis["net"] == 0.0
    assert analysis["highest_spending_category"] is None
    assert analysis["average_daily_spending"] == 0.0
