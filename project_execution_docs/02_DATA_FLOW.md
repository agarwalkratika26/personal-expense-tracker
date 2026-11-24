# 02 - Data Flow & Pipeline Architecture

This document describes how data enters, travels through, transforms within, and exits the Personal Expense Tracker application.

---

## 1. End-to-End Data Pipeline Overview

The data pipeline consists of 6 discrete lifecycle stages:
1. **Ingestion (Input Sources)**
2. **Sanitization & Normalization**
3. **Categorization & Enrichment**
4. **Validation & Deduplication**
5. **Persistence (SQLite Storage)**
6. **Analytics, Aggregation & Presentation / Export**

```
 ┌──────────────────────┐         ┌──────────────────────┐
 │ Manual Entry (Form)  │         │   CSV File Upload    │
 └──────────┬───────────┘         └──────────┬───────────┘
            │                                │
            │                                ▼
            │                     ┌──────────────────────┐
            │                     │ Ingestion / Parsing  │
            │                     │ (Headers lowercase,  │
            │                     │  type casting)       │
            │                     └──────────┬───────────┘
            │                                │
            ▼                                ▼
 ┌───────────────────────────────────────────────────────┐
 │               Validation & Sanitization               │
 │  - ISO-8601 Date format verification (YYYY-MM-DD)    │
 │  - Numeric float amount validation (> 0.0)            │
 │  - Type enforcement: 'income' vs 'expense'            │
 └──────────────────────────┬────────────────────────────┘
                            │
                            ▼
 ┌───────────────────────────────────────────────────────┐
 │               Inference & Categorization              │
 │  If category is missing or 'Other', run rule-based    │
 │  keyword matching against normalized description      │
 └──────────────────────────┬────────────────────────────┘
                            │
                            ▼
 ┌───────────────────────────────────────────────────────┐
 │             Deduplication & Fingerprinting            │
 │  Compute unique SHA-256 fingerprint from CSV rows     │
 │  (date + description + amount + payment_method)       │
 └──────────────────────────┬────────────────────────────┘
                            │
                            ▼
 ┌───────────────────────────────────────────────────────┐
 │                Persistence (SQLite DB)                │
 │  `INSERT OR IGNORE` into transactions table           │
 └──────────────────────────┬────────────────────────────┘
                            │ Query by Month (YYYY-MM)
                            ▼
 ┌───────────────────────────────────────────────────────┐
 │               Pandas Analytics Pipeline               │
 │  - Group by Category: `sum(amount)`                   │
 │  - Group by Month: time-series trend                  │
 │  - Group by Payment Method: distribution              │
 │  - Compute KPIs: Total, Net, Daily Avg, Top Category  │
 │  - Budget comparison: actual vs monthly_limit         │
 └─────────────┬───────────────────────────┬─────────────┘
               │                           │
               ▼                           ▼
 ┌───────────────────────────┐ ┌─────────────────────────┐
 │ Streamlit UI & Plotly     │ │ Monthly CSV Report      │
 │ Interactive Visualizations│ │ File Export             │
 └───────────────────────────┘ └─────────────────────────┘
```

---

## 2. Detailed Pipeline Stages

### Stage 1: Ingestion
- **Manual Form Entry:** Captures `date`, `description`, `amount`, `category`, `type` (`expense`/`income`), `payment_method`, and optional `notes`.
- **Batch CSV Upload:** Expects at minimum `date`, `description`, and `amount`. Optional columns (`category`, `type`, `payment_method`, `notes`) are auto-populated with defaults if omitted.
- **Synthetic Data Generator:** Generates controlled random distributions of income and expense items using `synthetic.py` with reproducible random seeds.

### Stage 2: Normalization & Cleaning
- Column names are stripped of whitespace and converted to lowercase.
- Dates are normalized to `YYYY-MM-DD` standard ISO strings.
- Amounts are converted to absolute positive `float` values, rounded to two decimal places.
- Text strings (`description`, `notes`) are stripped of redundant whitespace and lowercased for parsing.

### Stage 3: Categorization & Enrichment
- If the incoming transaction has an explicit category provided by the user, that category is preserved.
- If the category is missing, empty, or marked as `"Other"`, the string description is processed by `suggest_category(description, transaction_type)`.
- If `transaction_type == "income"`, it is assigned `"Income"`. Otherwise, regex keyword sets evaluate the description against pre-defined category buckets (Groceries, Utilities, Transport, etc.).

### Stage 4: Deduplication & Fingerprinting
- To prevent duplicate entries when users upload overlapping monthly CSV statements:
  - An `import_hash` is computed:
    $$\text{hash} = \text{SHA256}(\text{date} \,||\, \text{description} \,||\, \text{amount} \,||\, \text{payment\_method})$$
  - The SQLite schema enforces a `UNIQUE(import_hash)` constraint.
  - Duplicate rows are silently ignored (`INSERT OR IGNORE`), and the UI reports the count of successfully inserted vs. skipped records.

### Stage 5: Persistence
- Verified records are stored in the `transactions` table.
- Monthly budgets per category are maintained in the `budgets` table.
- Reads are executed with parameterized SQL queries filtered by month (`strftime('%Y-%m', date) = :month`), ensuring fast query execution.

### Stage 6: Analytics & Aggregations
- Raw database rows are converted into a Pandas DataFrame.
- Aggregation pipelines calculate:
  - **Category Breakdown:** `df[df['type']=='expense'].groupby('category')['amount'].sum()`
  - **Monthly Trend:** `df.groupby(['month', 'type'])['amount'].sum()`
  - **Payment Method Distribution:** `df[df['type']=='expense'].groupby('payment_method')['amount'].sum()`
  - **Net Cash Flow:** `Total Income - Total Expenses`
  - **Budget Variance:** `Remaining Budget = Monthly Limit - Actual Spend`

### Stage 7: Output Delivery
- Aggregated dataframes are fed into **Plotly** to generate bar charts, pie charts, and cumulative timeline graphs.
- **Report Generator** formats the data into a standard 4-section CSV report containing Metadata, Category Breakdown, Payment Summary, and Transaction Ledger.
