"""SQLite persistence and transaction validation."""

from __future__ import annotations

import contextlib
import hashlib
import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any, Generator

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("EXPENSE_TRACKER_DB", ROOT / "data" / "expenses.db"))


@contextlib.contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional SQLite connection that always closes cleanly."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def connect() -> sqlite3.Connection:
    """Legacy helper returning a connection directly."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'expense' CHECK(type IN ('expense', 'income')),
                payment_method TEXT NOT NULL DEFAULT 'Other',
                notes TEXT NOT NULL DEFAULT '',
                import_key TEXT UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL CHECK(monthly_limit >= 0),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def _clean_transaction(item: dict[str, Any]) -> dict[str, Any]:
    try:
        parsed_date = pd.to_datetime(item.get("date"), errors="raise").date().isoformat()
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Date must be a valid date such as 2026-04-30.") from exc
    description = str(item.get("description", "")).strip()
    if not description:
        raise ValueError("Description cannot be empty.")
    try:
        amount = round(float(item.get("amount")), 2)
    except (ValueError, TypeError) as exc:
        raise ValueError("Amount must be a number greater than zero.") from exc
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    txn_type = str(item.get("type", "expense") or "expense").strip().lower()
    if txn_type not in {"expense", "income"}:
        raise ValueError("Type must be expense or income.")
    category = str(item.get("category", "Other") or "Other").strip()
    return {
        "date": parsed_date,
        "description": description,
        "amount": amount,
        "category": category,
        "type": txn_type,
        "payment_method": str(item.get("payment_method", "Other") or "Other").strip(),
        "notes": str(item.get("notes", "") or "").strip(),
        "import_key": item.get("import_key"),
    }


def add_transaction(item: dict[str, Any]) -> int:
    row = _clean_transaction(item)
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO transactions
            (date, description, amount, category, type, payment_method, notes, import_key)
            VALUES (:date, :description, :amount, :category, :type, :payment_method, :notes, :import_key)""",
            row,
        )
        return int(cur.lastrowid)


def add_transactions(items: list[dict[str, Any]]) -> tuple[int, int, list[str]]:
    """Insert valid imported rows; duplicate imports are ignored and row errors returned."""
    inserted = skipped = 0
    errors: list[str] = []
    with get_connection() as conn:
        for index, item in enumerate(items, start=2):
            try:
                row = _clean_transaction(item)
                cur = conn.execute(
                    """INSERT OR IGNORE INTO transactions
                    (date, description, amount, category, type, payment_method, notes, import_key)
                    VALUES (:date, :description, :amount, :category, :type, :payment_method, :notes, :import_key)""",
                    row,
                )
                if cur.rowcount:
                    inserted += 1
                else:
                    skipped += 1
            except (ValueError, sqlite3.IntegrityError) as exc:
                errors.append(f"Row {index}: {exc}")
    return inserted, skipped, errors


def transaction_fingerprint(item: dict[str, Any]) -> str:
    try:
        normalized_date = pd.to_datetime(item.get("date"), errors="raise").date().isoformat()
    except (ValueError, TypeError, AttributeError):
        normalized_date = str(item.get("date", "")).strip().lower()
    try:
        normalized_amount = f"{float(item.get('amount')):.2f}"
    except (ValueError, TypeError):
        normalized_amount = str(item.get("amount", "")).strip().lower()
    fields = [
        normalized_date,
        str(item.get("description", "")).strip().lower(),
        normalized_amount,
        str(item.get("category", "")).strip().lower(),
        str(item.get("type", "expense") or "expense").strip().lower(),
        str(item.get("payment_method", "Other") or "Other").strip().lower(),
    ]
    return hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()


def get_transactions(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    query = "SELECT id, date, description, amount, category, type, payment_method, notes FROM transactions"
    clauses: list[str] = []
    params: list[str] = []
    if start:
        clauses.append("date >= ?")
        params.append(start)
    if end:
        clauses.append("date <= ?")
        params.append(end)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY date DESC, id DESC"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params, parse_dates=["date"])


def delete_transaction(transaction_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))


def update_transaction(transaction_id: int, item: dict[str, Any]) -> None:
    """Update an existing transaction after validating the updated values."""
    row = _clean_transaction(item)
    row["id"] = transaction_id
    with get_connection() as conn:
        conn.execute(
            """UPDATE transactions
            SET date = :date,
                description = :description,
                amount = :amount,
                category = :category,
                type = :type,
                payment_method = :payment_method,
                notes = :notes
            WHERE id = :id""",
            row,
        )


def get_budgets() -> dict[str, float]:
    with get_connection() as conn:
        rows = conn.execute("SELECT category, monthly_limit FROM budgets ORDER BY category").fetchall()
    return {row["category"]: float(row["monthly_limit"]) for row in rows}


def save_budget(category: str, monthly_limit: float) -> None:
    if monthly_limit < 0:
        raise ValueError("Budget must be zero or greater.")
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO budgets(category, monthly_limit) VALUES (?, ?)
            ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit,
            updated_at=CURRENT_TIMESTAMP""",
            (category, round(float(monthly_limit), 2)),
        )


def delete_budget(category: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM budgets WHERE category = ?", (category,))


def seed_sample_data(csv_path: Path) -> tuple[int, int, list[str]]:
    """Load the bundled demo CSV once; each row has a stable idempotency key."""
    frame = pd.read_csv(csv_path).fillna("")
    items = frame.to_dict(orient="records")
    for item in items:
        item["import_key"] = transaction_fingerprint(item)
    return add_transactions(items)
