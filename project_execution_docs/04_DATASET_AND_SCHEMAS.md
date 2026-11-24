# 04 - Dataset and Data Schemas

This document details the datasets utilized in the project, the synthetic data generation engine, and the formal database schemas and validation constraints.

---

## 1. Dataset Overview

The project accommodates three sources of transaction data:
1. **Curated Sample Dataset:** `data/sample_transactions.csv` (used for out-of-the-box demonstration).
2. **Synthetic Data Engine:** Procedurally generated transactions simulating 6 months of financial activity with realistic spending patterns.
3. **User-Provided Statement CSVs:** Real-world bank or credit card statements parsed and normalized at runtime.

---

## 2. Sample Dataset (`data/sample_transactions.csv`)

### Schema & Fields

| Field Name | Data Type | Nullable | Description / Value Range |
| :--- | :--- | :--- | :--- |
| `date` | `ISO Date (YYYY-MM-DD)` | No | Transaction date |
| `description` | `String` | No | Merchant name or description (e.g., "Whole Foods", "Electric bill") |
| `amount` | `Float` | No | Transaction magnitude (positive scalar, e.g., `45.50`) |
| `category` | `String` | Yes | Category tag (e.g., `Groceries`, `Utilities`, `Income`) |
| `type` | `String` | No | Either `expense` or `income` |
| `payment_method`| `String` | Yes | e.g., `Card`, `Cash`, `Bank transfer`, `Digital wallet` |
| `notes` | `String` | Yes | Optional user annotations |

---

## 3. Synthetic Data Generation Engine (`synthetic.py`)

To evaluate the system without requiring personal financial records, `generate_synthetic_transactions` produces deterministic, realistic transaction logs.

### Generation Parameters & Distribution
- **Transaction Count:** Configurable (default: 120).
- **Time Horizon:** Spans 180 days backwards from the run date.
- **Random Seed:** Default `seed=42` ensures identical distributions across test runs.
- **Income Generation:**
  - Probability: ~6% of records generated are income events.
  - Amount Distribution: Uniform random between $\$1,800$ and $\$3,200$.
  - Description: "Monthly salary", Method: "Bank transfer".
- **Expense Generation:**
  - Categories: Uniform selection across 8 core categories (`Groceries`, `Food & Dining`, `Transport`, `Utilities`, `Healthcare`, `Shopping`, `Entertainment`, `Education`).
  - Merchants: Realistic name pools (e.g., "City transit", "Campus cafe", "Fresh market").
  - Amount Distribution: Uniform random between $\$4.00$ and $\$180.00$.
  - Payment Methods: Randomly chosen from `Card`, `Cash`, `Bank transfer`, `Digital wallet`.

---

## 4. SQLite Storage Schema

### Table: `transactions`
```sql
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    category TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
    payment_method TEXT NOT NULL DEFAULT 'Other',
    notes TEXT DEFAULT '',
    import_hash TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
```

### Table: `budgets`
```sql
CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY,
    monthly_limit REAL NOT NULL CHECK(monthly_limit >= 0)
);
```

---

## 5. Data Validation & Integrity Rules

1. **Date Validation:**
   Must conform to ISO-8601 (`YYYY-MM-DD`). Invalid dates are rejected before insertion.
2. **Amount Positive Constraint:**
   Amounts must be strictly positive floats (`amount > 0`). Cash flow direction is exclusively governed by the `type` column (`expense` or `income`).
3. **Deduplication Constraint:**
   The `import_hash` column is generated using SHA-256:
   $$\text{import\_hash} = \text{hash}(\text{date} + \text{description} + \text{str}(amount) + \text{payment\_method})$$
   Enforcing `UNIQUE(import_hash)` ensures that importing the same CSV multiple times does not produce duplicate financial entries.
