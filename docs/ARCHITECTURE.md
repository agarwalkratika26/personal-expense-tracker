# Project Architecture

## Overview

The application accepts transactions through manual entry or CSV upload, validates and categorizes them, stores them locally in SQLite, and presents summaries in Streamlit. Pandas performs grouping and aggregation; Plotly renders the interactive dashboard charts. Monthly reports are generated as downloadable CSV files.

## Text-based architecture diagram

```text
┌────────────────────── INPUTS ──────────────────────┐
│ Manual form                         CSV upload      │
│ date, description/note, amount,     date, description,
│ category, type, payment method      amount, optional
└───────────────────────┬────────────────────────────┘
                        │
                        v
┌────────────────── INGESTION & CLEANING ─────────────┐
│ Read rows → normalize fields → validate date/amount │
│ → infer missing category → identify repeated import │
└───────────────────────┬────────────────────────────┘
                        │ valid transaction records
                        v
┌────────────────────── STORAGE ──────────────────────┐
│ SQLite                                              │
│ transactions: date, description, amount, category,  │
│ type, payment_method, notes                         │
│ budgets: category, monthly_limit                    │
└───────────────────────┬────────────────────────────┘
                        │ query selected date range/month
                        v
┌────────────────────── ANALYSIS ─────────────────────┐
│ pandas: category totals, monthly totals/trends,     │
│ payment-method totals, income/expense/net,          │
│ highest-spend category, budget vs. actual           │
└────────────┬──────────────────────┬────────────────┘
             │                      │
             v                      v
┌────────────────────┐    ┌───────────────────────────┐
│ Streamlit + Plotly │    │ Monthly report generator  │
│ dashboard/charts   │    │ downloadable CSV          │
└──────────┬─────────┘    └─────────────┬─────────────┘
           └──────────────┬──────────────┘
                          v
┌──────────────────────── OUTPUTS ────────────────────┐
│ Category spend • monthly trend • payment analysis  │
│ budget progress • income/expense/net summary       │
│ charts • downloadable monthly report               │
└─────────────────────────────────────────────────────┘
```

## Input fields

| Field | Purpose |
|---|---|
| Date | Assign the transaction to a day and reporting month. |
| Expense category | Group expenses, for example Groceries or Transport. A missing CSV category can be suggested from the description. |
| Amount | Positive transaction value. The type field determines whether it is treated as income or expense. |
| Payment method | Compare spending by card, cash, transfer, digital wallet, or another method. |
| Note/description | Identify the merchant or purpose; also used by the keyword categorizer. |
| Type | `expense` or `income`, so cash flow can be summarized separately. |

## Data flow

1. **Capture:** A person fills out the Streamlit form or selects a CSV. CSV requires `date`, `description`, and `amount`; category, type, payment method and notes are optional.
2. **Read and normalize:** Column names are made lowercase. Blank optional values receive defaults. Dates are parsed into a consistent ISO form, text is trimmed, and amounts are converted to numeric values.
3. **Validate and categorize:** Rows need a valid date, non-empty description, positive amount, and supported transaction type. Rule-based categorization suggests a category when an import omits one. Invalid import rows are reported rather than stored.
4. **Avoid repeated imports:** An imported row receives a stable fingerprint. SQLite's unique constraint prevents the same exact imported record from being added again. Manually entered records do not use this fingerprint.
5. **Persist:** The database layer saves transactions and category budget limits in SQLite. This keeps the starter project self-contained and usable without a bank connection.
6. **Analyze:** The app queries the stored rows for the selected month. Pandas groups expenses by category, month, payment method, and day; it calculates income, total spending, average daily spending, net cash flow, budget progress, and the highest-spend category.
7. **Present:** Streamlit provides filters and summary metrics; Plotly displays interactive charts. The monthly report generator writes summary, category, and transaction rows to a downloadable CSV.

## Analysis definitions

- **Category-wise spending:** Sum of expense amounts for each category within the selected month.
- **Monthly spending trend:** Sum of expense amounts for each calendar month; use this to compare months or show a time series.
- **Payment method analysis:** Sum of expense amounts by payment method for the selected month or date range.
- **Highest spending category:** The category with the greatest expense total in the selected period. If there are no expenses, report no result rather than selecting a category.
- **Spending summary:** Total expense amount for the selected period.
- **Savings/net summary:** For this tracker, net cash flow is income minus expenses. It is a simple period summary, not a complete measure of savings or assets.
- **Budget status:** Category expense total compared with that category's monthly limit; show remaining budget or amount over limit.

## Current implementation

The dashboard displays monthly income, expenses, net cash flow, average daily spending, highest-spend category, budget status, category spending, monthly trend, payment-method mix, and daily spending. The monthly report includes summary, category, payment-method, and transaction sections.

## Responsibilities by module

- `main.py`: Streamlit inputs, filters, charts, tables, and CSV download.
- `src/expense_tracker/analytics.py`: Cleaning, aggregation, and summary calculations.
- `src/expense_tracker/categorization.py`: Offline category suggestion rules.
- `src/expense_tracker/database.py`: SQLite schema, validation, persistence, and queries.
- `src/expense_tracker/reports.py`: Monthly CSV report generation.
- `src/expense_tracker/synthetic.py`: Repeatable synthetic transaction creation.
- `data/sample_transactions.csv`: Synthetic data for demonstration.
