# 03 - Modules and Components

This document details the functional specifications, internal mechanisms, inputs, outputs, and dependencies for every module in the project.

---

## 1. Module Inventory

```
src/
└── expense_tracker/
    ├── __init__.py           # Package initializer
    ├── database.py           # SQLite connection, schema definition & CRUD operations
    ├── analytics.py          # Data transformation, grouping & metric calculations
    ├── categorization.py     # Keyword-based category inference engine
    ├── reports.py            # Multi-section CSV report builder
    └── synthetic.py          # Reproducible test/demo data generation
main.py                       # Streamlit web application & UI orchestrator
```

---

## 2. Deep Dive: `src/expense_tracker/database.py`

### Purpose
Manages the SQLite database lifecycle, schema initialization, parameterized queries, transaction validation, and deduplication.

### Key Classes / Functions
- **`init_db(db_path: Path | str) -> sqlite3.Connection`**:
  Initializes tables (`transactions`, `budgets`) with appropriate indices and constraints.
- **`add_transaction(...) -> int`**:
  Validates input fields and inserts a single manual transaction record.
- **`update_transaction(transaction_id: int, item: dict[str, Any]) -> None`**:
  Validates updated fields and updates an existing transaction in SQLite.
- **`delete_transaction(transaction_id: int) -> None`**:
  Deletes an individual transaction by ID.
- **`import_transactions_from_csv(file_or_df, db_path) -> tuple[int, int]`**:
  Bulk inserts transactions while calculating unique SHA-256 hashes to prevent duplicates. Returns `(inserted_count, skipped_count)`.
- **`get_transactions(month: str | None, db_path) -> pd.DataFrame`**:
  Retrieves transactions filtered by month (`YYYY-MM`) or full dataset, returned as a Pandas DataFrame.
- **`set_budget(category: str, limit: float, db_path) -> None`**:
  Inserts or updates a monthly spend limit for a category (`INSERT OR REPLACE INTO budgets`).
- **`get_budgets(db_path) -> dict[str, float]`**:
  Retrieves all configured category budgets as a key-value dictionary.

### Database Schema Highlights
- `transactions`: `id (INTEGER PK AUTOINCREMENT)`, `date (TEXT NOT NULL)`, `description (TEXT NOT NULL)`, `amount (REAL NOT NULL)`, `category (TEXT NOT NULL)`, `type (TEXT CHECK IN ('income', 'expense'))`, `payment_method (TEXT)`, `notes (TEXT)`, `import_hash (TEXT UNIQUE)`.
- `budgets`: `category (TEXT PRIMARY KEY)`, `monthly_limit (REAL NOT NULL CHECK(monthly_limit >= 0))`.

---

## 3. Deep Dive: `src/expense_tracker/analytics.py`

### Purpose
Encapsulates all mathematical and statistical transformations on financial data using Pandas.

### Key Functions
- **`calculate_kpis(df: pd.DataFrame) -> dict`**:
  Computes high-level metrics:
  - `total_income`: Sum of all `income` transactions.
  - `total_expense`: Sum of all `expense` transactions.
  - `net_savings`: `total_income - total_expense`.
  - `daily_avg_spend`: `total_expense / days_in_period`.
  - `top_category`: Category with maximum aggregate expense.
- **`get_category_summary(df: pd.DataFrame) -> pd.DataFrame`**:
  Groups expenses by category, calculating total amount, transaction count, and percentage of overall spend.
- **`get_monthly_trend(df: pd.DataFrame) -> pd.DataFrame`**:
  Aggregates spending and income by calendar month for time-series trend lines.
- **`get_payment_method_breakdown(df: pd.DataFrame) -> pd.DataFrame`**:
  Calculates distribution across payment channels (Card, Cash, Bank Transfer, Digital Wallet).
- **`get_budget_comparison(df: pd.DataFrame, budgets: dict[str, float]) -> pd.DataFrame`**:
  Joins actual spend per category with configured budget limits; computes variance, remaining budget, and percentage utilized.

---

## 4. Deep Dive: `src/expense_tracker/categorization.py`

### Purpose
Provides offline, deterministic inference of spending categories based on transaction description strings.

### Mechanics
- **`CATEGORY_RULES`**: A dictionary mapping standard categories (`Groceries`, `Transport`, `Utilities`, `Healthcare`, `Food & Dining`, `Entertainment`, `Shopping`, `Education`, `Travel`, `Income`) to tuples of domain keywords.
- **`suggest_category(description: str, transaction_type: str = "expense") -> str`**:
  1. If `transaction_type == "income"`, returns `"Income"`.
  2. Normalizes input description (lowercase, whitespace collapse).
  3. Iterates over keywords; if any keyword is a substring of the description, immediately returns the associated category.
  4. Defaults to `"Other"` if no match is found.

---

## 5. Deep Dive: `src/expense_tracker/reports.py`

### Purpose
Exports formatted, audit-ready CSV reports for financial reviews.

### Structure of Exported CSV
1. **Section 1 - Executive Summary:** Total Income, Total Expenses, Net Cash Flow, Active Month.
2. **Section 2 - Category Spend Breakdown:** Table of categories, total spend, percentage share.
3. **Section 3 - Payment Method Analysis:** Breakdown by payment channel.
4. **Section 4 - Itemized Transaction Log:** Full detail of all transactions for the selected period.

---

## 6. Deep Dive: `src/expense_tracker/synthetic.py`

### Purpose
Enables repeatable demonstration, testing, and validation without exposing private financial data.

### Parameters
- `count` (default: 120 transactions).
- `start_date` (defaults to 180 days prior to current date).
- `seed` (default: 42, ensuring 100% deterministic reproducibility).
- Simulates realistic merchant names, variable expense amounts ($4 to $180), and monthly income injections ($1,800 to $3,200).

---

## 7. Deep Dive: `main.py`

### Purpose
The primary presentation and user interaction orchestrator powered by Streamlit.

### Responsibilities
- Sidebar navigation: Data Ingestion (Manual / CSV Upload / Synthetic Generator), Filter Controls, Budget Configurator.
- Main dashboard layout:
  - Metric Cards (Income, Expense, Net, Daily Avg).
  - Visualizations (Plotly donut chart for categories, bar charts for monthly trends, payment breakdown).
  - Budget progress bars with dynamic color-coding (Green for normal, Amber for warning, Red for budget exceeded).
  - Interactive searchable and sortable transaction data table.
  - CSV Report export button.
