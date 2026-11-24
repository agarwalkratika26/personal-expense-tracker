"""Unit tests for monthly CSV report compilation and synthetic generator."""

import io
import pandas as pd
import pytest
from src.expense_tracker.reports import monthly_report_csv, month_label
from src.expense_tracker.synthetic import generate_synthetic_transactions


def test_monthly_report_structure_and_contents():
    transactions = pd.DataFrame([
        {"date": pd.Timestamp("2026-04-05"), "description": "Market", "amount": 100.0, "category": "Groceries", "type": "expense", "payment_method": "Card"},
        {"date": pd.Timestamp("2026-04-10"), "description": "Paycheck", "amount": 2000.0, "category": "Income", "type": "income", "payment_method": "Bank transfer"},
    ])
    budgets = {"Groceries": 300.0}
    csv_bytes = monthly_report_csv(transactions, month="2026-04", budgets=budgets, currency_code="INR")

    df = pd.read_csv(io.BytesIO(csv_bytes))
    sections = set(df["section"].unique())
    assert "metadata" in sections
    assert "summary" in sections
    assert "category_budget" in sections
    assert "payment_method" in sections
    assert "transaction" in sections

    # Check metadata currency
    meta_row = df[(df["section"] == "metadata") & (df["category"] == "Report Currency")]
    assert not meta_row.empty
    assert meta_row.iloc[0]["amount"] == "INR"


def test_month_label():
    assert month_label("2026-01") == "January 2026"
    assert month_label("2026-12") == "December 2026"


def test_synthetic_transactions_determinism():
    df1 = generate_synthetic_transactions(count=80, seed=42)
    df2 = generate_synthetic_transactions(count=80, seed=42)
    pd.testing.assert_frame_equal(df1, df2)


def test_synthetic_transactions_income_and_expense():
    df = generate_synthetic_transactions(count=100, seed=123)
    types = set(df["type"].unique())
    assert "expense" in types
    assert "income" in types
    assert len(df) == 100
    assert (df["amount"] > 0).all()
