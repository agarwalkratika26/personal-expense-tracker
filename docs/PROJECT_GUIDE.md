# Project guide

## What happens when the app runs

1. Streamlit loads `main.py` and `initialize_db()` creates the local SQLite tables if needed.
2. The user enters a transaction or uploads a CSV. The database layer validates dates, descriptions, transaction types and positive amounts.
3. Missing CSV categories are suggested from an offline keyword list. The app shows a preview before import.
4. SQLite stores the accepted rows. CSV fingerprints make repeated imports idempotent; manual entries remain independent.
5. Dashboard queries group rows by month/category/date. Budget limits are compared to expenses in the selected month.
6. The report function creates a downloadable CSV with summary values, category totals, budget references and transaction detail.

## Main files

- `main.py`: user interface and chart composition.
- `src/expense_tracker/database.py`: schema, validation, reads/writes and sample-data loading.
- `src/expense_tracker/categorization.py`: editable deterministic rules.
- `src/expense_tracker/reports.py`: report serialization.
- `data/sample_transactions.csv`: synthetic demo input.

## Manual smoke walkthrough

Use the steps in the README's “Practice walkthrough” section. For a clean demo, stop the app and remove `data/expenses.db` before starting again; the sample data and budgets will be reset. Do not commit that database if you put real entries into it.

## Suggested screenshot checklist

- Dashboard with sample data, at least one budget, both charts visible.
- Import CSV tab with a file preview before clicking Import.
- Monthly report tab with the download button visible.

Store only synthetic or redacted information in screenshots committed to a public repository.
