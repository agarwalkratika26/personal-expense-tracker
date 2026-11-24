"""Rule-based transaction categorization that works offline."""

from __future__ import annotations

import re

CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "Groceries": ("grocery", "groceries", "supermarket", "market", "produce", "whole foods"),
    "Food & Dining": ("restaurant", "cafe", "coffee", "pizza", "takeaway", "dining", "food delivery"),
    "Transport": ("uber", "taxi", "transit", "bus", "train", "metro", "fuel", "gas station", "parking"),
    "Housing": ("rent", "mortgage", "landlord"),
    "Utilities": ("electric", "electricity", "water bill", "internet", "utility", "gas bill"),
    "Healthcare": ("pharmacy", "doctor", "hospital", "clinic", "medical", "dentist"),
    "Shopping": ("amazon", "bookstore", "clothing", "mall", "shopping", "store"),
    "Entertainment": ("movie", "cinema", "streaming", "spotify", "concert", "game"),
    "Education": ("course", "tuition", "school", "university", "udemy", "textbook"),
    "Travel": ("hotel", "flight", "airbnb", "airline", "vacation"),
    "Income": ("salary", "payroll", "paycheck", "freelance", "refund", "interest"),
}

DEFAULT_CATEGORIES = tuple(CATEGORY_RULES) + ("Personal Care", "Other")


def suggest_category(description: str, transaction_type: str = "expense") -> str:
    """Return a category suggestion based on the description; no external API used."""
    if transaction_type.lower() == "income":
        return "Income"
    text = re.sub(r"\s+", " ", description.lower()).strip()
    for category, keywords in CATEGORY_RULES.items():
        if category == "Income":
            continue
        if any(keyword.strip().lower() in text for keyword in keywords):
            return category
    return "Other"

