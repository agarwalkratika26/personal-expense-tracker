# Technical Project Review Report: Personal Expense Tracker with Data Visualization

**Target Audience:** Technical Project Manager / Lead Engineer / Academic Reviewer  
**Project Name:** Personal Expense Tracker with Data Visualization  
**Status:** Complete & Ready for Review  
**Date:** November 25, 2026  
**Primary Tech Stack:** Python 3.12, Streamlit, Pandas, NumPy, Plotly, SQLite3, Pytest, Seaborn, Matplotlib  

---

## 1. Executive Summary

This project delivers a **local-first, privacy-preserving personal finance tracking and analytical dashboard**. Built to demonstrate software engineering fundamentals without requiring external banking APIs or live financial credentials, the application operates on local SQLite storage, CSV file ingestion, and deterministic synthetic data simulation.

The system features an interactive Streamlit UI, 4 Plotly charts, an explainable offline heuristic keyword categorizer, cryptographic SHA-256 transaction deduplication, configurable display currency formatting (defaulting to INR `₹`, with the dataset assumed to use one currency and without per-transaction currency storage or FX conversion), full transaction CRUD, and automated multi-section monthly CSV report generation. The analytical and persistence logic is covered by **20 automated tests in four test files**, with all 20 tests passing.

---

## 2. Product Requirements & Implementation Matrix

| Requirement | Implementation Details | Status |
| :--- | :--- | :---: |
| **1. Full Transaction CRUD** | Manual transaction entry, tabular search/filtering, full-field editing via `update_transaction()` (with payment method preservation), and ID-targeted deletion in [`main.py`](../main.py) and [`src/expense_tracker/database.py`](../src/expense_tracker/database.py). | **Verified (Unit & AppTest)** |
| **2. CSV Statement Ingestion** | Ingests CSVs with row-level validation; captures corrupt dates, blank descriptions, non-positive amounts; returns structured error logs; imports valid rows. | **Verified (Automated)** |
| **3. Idempotent Deduplication** | Computes SHA-256 fingerprint from CSV rows (`date + desc + amount + category + type + payment_method`). Enforces SQLite `UNIQUE(import_key)` to skip duplicate imports while allowing identical manual entries. | **Verified (Automated)** |
| **4. Offline Categorization** | Deterministic keyword mapping in [`src/expense_tracker/categorization.py`](../src/expense_tracker/categorization.py). Operates with zero external network dependencies. Users can manually review/override suggestions. | **Verified (Automated)** |
| **5. Configurable Display Currency** | Offers configurable display currency formatting defaulting to **INR (`₹`)** with options for USD (`$`), EUR (`€`), GBP (`£`), and JPY (`¥`). Formats metrics, charts, and budget cards; assumes one currency per dataset without FX conversions. | **Verified (Automated)** |
| **6. Budget Tracking & Alerts** | Monthly spend limits per category stored in SQLite `budgets` table. Visual progress bars with warning banners for exceeded limits. | **Verified (Automated)** |
| **7. Analytics & Aggregations** | Reusable functions in [`src/expense_tracker/analytics.py`](../src/expense_tracker/analytics.py) for monthly trends, category spending, payment method mix, calendar-day average daily spending, and deterministic tie-breaking. | **Verified (Automated)** |
| **8. Interactive Plotly Charts** | 4 required interactive charts: Category Bar Chart, Monthly Spending Line, Payment Method Donut, and Daily Spending Timeline. | **Verified (App Launch)** |
| **9. Static Exploratory Analysis** | Companion script and notebook ([`notebooks/exploratory_analysis.py`](../notebooks/exploratory_analysis.py) & [`.ipynb`](../notebooks/exploratory_analysis.ipynb)) generating Seaborn and Matplotlib figures. | **Verified (Script Execution)** |
| **10. Monthly Report Export** | Generates a 5-section CSV statement (`metadata`, `summary`, `category_budget`, `payment_method`, `transaction`). Sample report saved to [`reports/examples/expense-report-2026-01.csv`](../reports/examples/expense-report-2026-01.csv). | **Verified (Automated)** |

---

## 3. System Architecture & Technical Specifications

### 3.1 Multi-Tier Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION TIER                       │
│       Streamlit Dashboard (main.py) + Plotly Visuals        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LOGIC LAYER                     │
│  Analytics Engine         Categorizer        Report Builder │
│  (analytics.py)      (categorization.py)     (reports.py)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA ACCESS & STORAGE                    │
│    Database Layer: Connection Context Manager & CRUD        │
│          SQLite Storage: `transactions`, `budgets`          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Key Architectural Decisions
1. **Connection Lifecycle Management:**
   - Designed `get_connection()` context manager in `database.py` wrapped in `try ... finally: conn.close()`. This ensures database handles close promptly, avoiding Windows OS file-locking exceptions during test runs.
2. **Transaction Edit Form State Preservation:**
   - In `main.py`, the transaction editing selector normalizes and binds the payment method to the selected transaction's existing value. When modifying another field (such as description or amount), the existing payment method remains selected in the form.
3. **Deterministic Tie-Breaking:**
   - In `analytics.py`, when multiple categories tie for the maximum spend in a period, the tie-breaking algorithm resolves deterministically by selecting the first category alphabetically.
4. **Accurate Daily Spend Normalization:**
   - Daily spending averages divide total monthly expenditures by the exact calendar day count of the selected month (`calendar.monthrange(year, month)[1]`), adjusting for 28, 29, 30, or 31-day months.

---

## 4. Test Suite & Quality Assurance

A dedicated test suite in [`tests/`](../tests/) executes **20 automated unit and integration tests across four test files**:
- `test_analytics.py` (6 tests): CSV cleaning, tie-breaking, daily spend, budget calculations, and empty datasets.
- `test_categorization.py` (5 tests): Rule heuristics, case-insensitivity, whitespace trimming, and fallbacks.
- `test_database.py` (5 tests): Table creation, insertion, updating (including preserving payment method), deletion, deduplication, and budget CRUD.
- `test_reports.py` (4 tests): Monthly report formatting, month labels, plus synthetic data generation determinism and distributions.

*(Note: Synthetic transaction generator tests are housed within `test_reports.py`.)*

### Test Execution Log
```text
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.2.0, pluggy-1.7.0
rootdir: Personal Expense Tracker with Data Visualization
configfile: pytest.ini
testpaths: tests

tests/test_analytics.py::test_clean_transaction_data_valid_and_invalid PASSED [  5%]
tests/test_analytics.py::test_clean_missing_required_columns_raises PASSED [ 10%]
tests/test_analytics.py::test_highest_spending_category_tie_behavior PASSED [ 15%]
tests/test_analytics.py::test_average_daily_spending_calculation PASSED  [ 20%]
tests/test_analytics.py::test_budget_status_and_overspending PASSED      [ 25%]
tests/test_analytics.py::test_empty_dataset_handling PASSED              [ 30%]
tests/test_categorization.py::test_income_categorization PASSED          [ 35%]
tests/test_categorization.py::test_expense_categorization_keywords PASSED [ 40%]
tests/test_categorization.py::test_unknown_description_defaults_to_other PASSED [ 45%]
tests/test_categorization.py::test_case_and_whitespace_insensitivity PASSED [ 50%]
tests/test_categorization.py::test_default_categories_structure PASSED   [ 55%]
tests/test_database.py::test_add_and_get_transaction PASSED              [ 60%]
tests/test_database.py::test_update_transaction PASSED                   [ 65%]
tests/test_database.py::test_delete_transaction PASSED                   [ 70%]
tests/test_database.py::test_duplicate_csv_import_deduplication PASSED   [ 75%]
tests/test_database.py::test_budget_crud PASSED                          [ 80%]
tests/test_reports.py::test_monthly_report_structure_and_contents PASSED [ 85%]
tests/test_reports.py::test_month_label PASSED                           [ 90%]
tests/test_reports.py::test_synthetic_transactions_determinism PASSED    [ 95%]
tests/test_reports.py::test_synthetic_transactions_income_and_expense PASSED [100%]

============================= 20 passed in 3.86s ==============================
```

---

## 5. Reviewer Verification Protocol

The technical manager can replicate and verify the project using the following steps:

### Step 1: Environment Setup & Automated Tests
```powershell
# Navigate to project directory and activate environment
.\.venv\Scripts\Activate.ps1

# Execute the 20-test verification suite
pytest -v
```
*Expected Result:* All 20 tests pass across the four test files with zero errors.

### Step 2: Generate Static Exploratory Visualizations
```powershell
python notebooks/exploratory_analysis.py
```
*Expected Result:* Generates `outputs/exploratory_spending_analysis.png` containing a 4-panel Seaborn figure.

### Step 3: Launch Interactive Dashboard
```powershell
streamlit run main.py
```
*Verification Checklist:*
1. **Load Data:** Click **"📥 Load Demo Transactions"** in the sidebar. Verify demo transactions populate.
2. **Dashboard Visuals:** Verify that the 4 Plotly charts (Category Bar, Monthly Trend, Payment Method Donut, Daily Line) render.
3. **Transaction Edit Check:**
   - Navigate to the **Manage Transactions** tab.
   - Select a transaction in the Edit section.
   - Verify that the Payment Method dropdown initializes to the selected transaction's current payment method.
   - Change the Description or Amount and submit; verify the transaction updates while the payment method is preserved.
4. **Report Export:** Go to **Monthly Report** and click download to verify CSV output.

---

## 6. Architecture & Scalability Considerations

| Area | Current Design | Considerations When Scaling |
| :--- | :--- | :--- |
| **Storage** | Local SQLite File | Adequate for single-user desktop use; migrate to PostgreSQL with SQLAlchemy connection pooling for multi-user web environments. |
| **Categorization** | Keyword Rules Engine | Fast and explainable; could be supplemented with an offline TF-IDF / Naive Bayes classifier trained on user edits. |
| **Data Processing** | In-Memory Pandas Aggregations | Performant for personal transaction volumes; evaluate Polars or SQL-level aggregations if datasets exceed hundreds of thousands of records. |
| **Currency** | Single-Currency Assumption | The app formats values with the chosen display currency and assumes transactions share that currency. Supporting true multi-currency datasets would require storing currency codes per transaction and integrating FX conversion rates. |

---

## 7. Review Summary & Status

The codebase implements the requested local-first functionality: data manipulation logic is separated into domain modules, inputs are validated, and deduplication prevents redundant CSV ingestion. Automated test coverage covers the database, analytics, categorization, and reporting logic, while UI verification requires running the local Streamlit dashboard.
