"""Unit tests for offline rule-based transaction categorization."""

import pytest
from src.expense_tracker.categorization import DEFAULT_CATEGORIES, suggest_category


def test_income_categorization():
    assert suggest_category("Monthly Paycheck", transaction_type="income") == "Income"
    assert suggest_category("Freelance invoice payment", transaction_type="income") == "Income"
    assert suggest_category("Random string", transaction_type="income") == "Income"


def test_expense_categorization_keywords():
    assert suggest_category("Supermarket weekly produce") == "Groceries"
    assert suggest_category("Whole Foods Market") == "Groceries"
    assert suggest_category("Uber trip to airport") == "Transport"
    assert suggest_category("City metro subway ticket") == "Transport"
    assert suggest_category("Campus cafe latte") == "Food & Dining"
    assert suggest_category("Domino's Pizza delivery") == "Food & Dining"
    assert suggest_category("Electric bill payment") == "Utilities"
    assert suggest_category("Internet broadband invoice") == "Utilities"
    assert suggest_category("Pharmacy prescription drugs") == "Healthcare"
    assert suggest_category("Dental clinic checkup") == "Healthcare"
    assert suggest_category("Amazon online order") == "Shopping"
    assert suggest_category("Netflix streaming subscription") == "Entertainment"


def test_unknown_description_defaults_to_other():
    assert suggest_category("xyz 123 incomprehensible merchant") == "Other"
    assert suggest_category("") == "Other"


def test_case_and_whitespace_insensitivity():
    assert suggest_category("   SuPeRmArKeT   ") == "Groceries"
    assert suggest_category("UBER   RIDE") == "Transport"


def test_default_categories_structure():
    assert "Groceries" in DEFAULT_CATEGORIES
    assert "Transport" in DEFAULT_CATEGORIES
    assert "Other" in DEFAULT_CATEGORIES
