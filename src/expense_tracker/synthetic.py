"""Repeatable synthetic transaction data for demos and coursework."""

from __future__ import annotations

from datetime import date, timedelta
import random

import pandas as pd


MERCHANTS = {
    "Groceries": ["Fresh market", "Corner grocery", "Supermarket"],
    "Food & Dining": ["Campus cafe", "Restaurant dinner", "Food delivery"],
    "Transport": ["City transit", "Taxi ride", "Fuel station"],
    "Utilities": ["Electric bill", "Internet bill", "Water bill"],
    "Healthcare": ["Pharmacy", "Doctor visit", "Dental clinic"],
    "Shopping": ["Bookstore", "Clothing store", "Online order"],
    "Entertainment": ["Movie tickets", "Streaming subscription", "Concert ticket"],
    "Education": ["Course fee", "Textbook", "School supplies"],
}


def generate_synthetic_transactions(
    count: int = 120,
    start_date: date | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Create a reproducible synthetic dataset with expenses and monthly income."""
    if count < 1:
        raise ValueError("count must be at least 1")
    rng = random.Random(seed)
    first_day = start_date or (date.today() - timedelta(days=179))
    categories = list(MERCHANTS)
    methods = ["Card", "Cash", "Bank transfer", "Digital wallet"]
    rows: list[dict[str, object]] = []
    for _ in range(count):
        txn_date = first_day + timedelta(days=rng.randrange(180))
        if rng.random() < 0.06:
            rows.append({
                "date": txn_date.isoformat(), "description": "Monthly salary",
                "amount": round(rng.uniform(1800, 3200), 2), "category": "Income",
                "type": "income", "payment_method": "Bank transfer", "notes": "Synthetic income",
            })
            continue
        category = rng.choice(categories)
        rows.append({
            "date": txn_date.isoformat(), "description": rng.choice(MERCHANTS[category]),
            "amount": round(rng.uniform(4, 180), 2), "category": category,
            "type": "expense", "payment_method": rng.choice(methods), "notes": "Synthetic demo entry",
        })
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
