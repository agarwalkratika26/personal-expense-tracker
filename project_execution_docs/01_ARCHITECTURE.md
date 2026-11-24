# 01 - System Architecture

This document outlines the architectural blueprint, design principles, component topologies, and runtime execution boundaries for the **Personal Expense Tracker with Data Visualization**.

---

## 1. High-Level Architectural Pattern

The application is structured around a **Modular Layered Architecture (Multi-Tier)** with clean separation of concerns across ingestion, persistence, domain analytics, and presentation.

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION TIER                       │
│  Streamlit Frontend (main.py) + Plotly Interactive Visuals  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION LOGIC                      │
│   Analytics Engine        Categorizer       Report Engine   │
│   (analytics.py)     (categorization.py)    (reports.py)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                      │
│             Database Interface (database.py)                │
│    Validation • SHA-256 Deduplication • SQL Abstractions    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                      │
│                 SQLite Local Store (.db)                    │
│           Tables: `transactions`, `budgets`                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Breakdown

### 2.1 Presentation Tier (`main.py`)
- **Technology:** Streamlit & Plotly Express / Graph Objects.
- **Responsibilities:**
  - Renders user input forms (single transaction entry, category budget allocation).
  - Handles CSV file upload and triggers parsing/validation.
  - Controls temporal filtering (month-year selectors, category filters, payment method filters).
  - Translates analytical metrics into responsive UI widgets (KPI stat cards, alerts for budget overspending).
  - Visualizes time-series trends, category distributions (pie/donut charts), and payment method breakdowns.
  - Provides a single-click export of structured monthly CSV reports.

### 2.2 Application / Domain Logic Tier
1. **Analytics Engine (`src/expense_tracker/analytics.py`)**:
   - Converts raw transaction records into Pandas DataFrames.
   - Computes core metrics: Total Income, Total Expenses, Net Savings (`Income - Expense`), Daily Spend Average, Highest Spending Category.
   - Aggregates spending across dimensional axes: by Category, by Month/Time-period, by Payment Method, and by Day.
   - Evaluates budget variance: compares actual expenditure against configured thresholds.
2. **Categorization Engine (`src/expense_tracker/categorization.py`)**:
   - Infers expenditure categories from merchant descriptions using regex-based keyword heuristics.
   - Operates completely offline with zero external API dependencies or latency.
3. **Report Generation Engine (`src/expense_tracker/reports.py`)**:
   - Compiles comprehensive, multi-section CSV reports with dynamic date stamping.
   - Generates summary KPIs, category distributions, payment breakdowns, and itemized transaction listings.

### 2.3 Data Access & Persistence Layer (`src/expense_tracker/database.py`)
- **Technology:** SQLite3 (standard Python library).
- **Design Philosophy:** Local-first, privacy-preserving, zero-setup, embeddable.
- **Integrity & Security:**
  - Strict input sanitization and schema-level constraints (`CHECK (type IN ('income', 'expense'))`, `amount > 0`).
  - Idempotent table creation (`CREATE TABLE IF NOT EXISTS`).
  - Cryptographic fingerprinting (`import_hash` using SHA-256 or compound key hashing) to guarantee that re-importing the same CSV prevents duplicate records.

---

## 3. Component Interaction Matrix

| Sender Module | Receiver Module | Payload / Contract | Purpose |
| :--- | :--- | :--- | :--- |
| `main.py` | `database.py` | `Transaction` dict / list | Persisting manual entry or uploaded CSV rows |
| `main.py` | `database.py` | `month: str (YYYY-MM)` | Fetching scoped transactions and budgets |
| `main.py` | `categorization.py` | `description: str, type: str` | Requesting category inference for unlabeled CSV rows |
| `main.py` | `analytics.py` | `DataFrame, budgets: dict` | Requesting statistical aggregations and budget status |
| `main.py` | `reports.py` | Aggregated metrics + records | Generating downloadable monthly summary CSV |
| `main.py` | `synthetic.py` | `count: int, seed: int` | Generating seed data for demonstration/testing |

---

## 4. Architectural Quality Attributes

- **Modularity:** Modules have zero cyclical dependencies; each can be tested independently via pytest or standalone scripts.
- **Offline Capability:** Fully operational without internet connectivity.
- **Zero Latency:** In-memory Pandas transformations and indexed SQLite queries yield sub-10ms response times.
- **Data Privacy:** Financial records never leave the local machine.
