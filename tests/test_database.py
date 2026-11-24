"""Unit and integration tests for SQLite persistence, CRUD operations, and deduplication."""

import tempfile
from pathlib import Path
import os
import pytest
import pandas as pd

from src.expense_tracker.database import (
    add_transaction,
    add_transactions,
    connect,
    delete_budget,
    delete_transaction,
    get_budgets,
    get_transactions,
    initialize_db,
    save_budget,
    transaction_fingerprint,
    update_transaction,
)


@pytest.fixture(autouse=True)
def temporary_database(monkeypatch):
    """Isolate tests in a temporary SQLite database."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        tmp_db = Path(tmpdir) / "test_expenses.db"
        monkeypatch.setenv("EXPENSE_TRACKER_DB", str(tmp_db))
        monkeypatch.setattr("src.expense_tracker.database.DB_PATH", tmp_db)
        initialize_db()
        yield tmp_db


def test_add_and_get_transaction():
    tx_id = add_transaction({
        "date": "2026-05-15",
        "description": "Weekly Veggies",
        "amount": 450.50,
        "category": "Groceries",
        "type": "expense",
        "payment_method": "UPI",
        "notes": "Organic store",
    })
    assert tx_id > 0
    df = get_transactions()
    assert len(df) == 1
    assert df.iloc[0]["description"] == "Weekly Veggies"
    assert df.iloc[0]["amount"] == 450.50
    assert df.iloc[0]["category"] == "Groceries"


def test_update_transaction():
    tx_id = add_transaction({
        "date": "2026-05-15",
        "description": "Original Purchase",
        "amount": 100.0,
        "category": "Shopping",
        "type": "expense",
        "payment_method": "Card",
        "notes": "Initial",
    })
    # 1. Update description and amount while preserving payment_method ("Card")
    update_transaction(tx_id, {
        "date": "2026-05-15",
        "description": "Updated Description Only",
        "amount": 110.00,
        "category": "Shopping",
        "type": "expense",
        "payment_method": "Card",
        "notes": "Initial",
    })
    df1 = get_transactions()
    assert len(df1) == 1
    row1 = df1.iloc[0]
    assert row1["description"] == "Updated Description Only"
    assert row1["amount"] == 110.00
    assert row1["payment_method"] == "Card"

    # 2. Update with modified payment method
    update_transaction(tx_id, {
        "date": "2026-05-16",
        "description": "Updated Purchase",
        "amount": 125.50,
        "category": "Groceries",
        "type": "expense",
        "payment_method": "Cash",
        "notes": "Corrected",
    })
    df2 = get_transactions()
    assert len(df2) == 1
    row2 = df2.iloc[0]
    assert row2["description"] == "Updated Purchase"
    assert row2["amount"] == 125.50
    assert row2["category"] == "Groceries"
    assert row2["payment_method"] == "Cash"


def test_delete_transaction():
    tx_id = add_transaction({
        "date": "2026-05-15",
        "description": "To be deleted",
        "amount": 50.0,
        "category": "Other",
        "type": "expense",
    })
    assert len(get_transactions()) == 1
    delete_transaction(tx_id)
    assert len(get_transactions()) == 0


def test_duplicate_csv_import_deduplication():
    item1 = {
        "date": "2026-05-10",
        "description": "Uber ride",
        "amount": 220.0,
        "category": "Transport",
        "type": "expense",
        "payment_method": "Card",
        "notes": "",
    }
    item1["import_key"] = transaction_fingerprint(item1)

    # First import
    inserted, skipped, errors = add_transactions([item1])
    assert inserted == 1
    assert skipped == 0

    # Repeat import of the exact same record
    inserted2, skipped2, errors2 = add_transactions([item1])
    assert inserted2 == 0
    assert skipped2 == 1  # Successfully deduplicated!
    assert len(get_transactions()) == 1


def test_budget_crud():
    save_budget("Groceries", 8000.0)
    save_budget("Transport", 3000.0)
    budgets = get_budgets()
    assert budgets["Groceries"] == 8000.0
    assert budgets["Transport"] == 3000.0

    # Update budget
    save_budget("Groceries", 9500.0)
    assert get_budgets()["Groceries"] == 9500.0

    # Delete budget
    delete_budget("Transport")
    assert "Transport" not in get_budgets()
