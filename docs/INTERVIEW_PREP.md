# Interview Preparation & Architecture Discussion Guide

This guide prepares developers and students to discuss the **Personal Expense Tracker with Data Visualization** in technical interviews, portfolio presentations, and code reviews.

---

## 1. The 60-Second Elevator Pitch

> *"I built a local-first, privacy-preserving Personal Expense Tracker in Python that eliminates reliance on fragile banking APIs. It features an interactive Streamlit dashboard with Plotly charts, an offline explainable keyword categorizer, an SQLite persistence layer with cryptographic transaction deduplication, and automated monthly reporting. It solves the cold-start problem with deterministic synthetic data generation and provides real-time overspending alerts against category budget thresholds."*

---

## 2. Core Architectural & Technical Questions

### Q1: Why build a local SQLite system instead of using Plaid or Open Banking APIs?
**Answer:**
- **Privacy & Security:** Personal financial data is highly sensitive. Keeping data on-disk with SQLite ensures zero leakage, zero external network calls, and eliminates API credential management.
- **Portability:** Banking APIs require commercial licenses, institution approvals, or sandbox accounts. A local SQLite + CSV ingestion architecture allows any student or interviewer to clone the repo and run it instantly.
- **Zero Running Costs:** No monthly API subscription or token costs.

### Q2: How does the transaction deduplication mechanism work?
**Answer:**
- Manual entries are never deduplicated, because a user can legitimately buy two identical $5 coffees on the same day.
- CSV imports, however, frequently contain overlapping date windows. Each imported row is fingerprinted with a SHA-256 hash:
  $$\text{hash} = \text{SHA256}(\text{date} \,||\, \text{description} \,||\, \text{amount} \,||\, \text{category} \,||\, \text{type} \,||\, \text{payment\_method})$$
- SQLite enforces `UNIQUE(import_key)`. When statements are re-imported, duplicate records are silently ignored (`INSERT OR IGNORE`), and the UI reports the exact count of inserted vs. skipped records.

### Q3: Why use rule-based categorization instead of calling an LLM or Cloud NLP API?
**Answer:**
- **Determinism & Explainability:** Rule-based heuristics guarantee deterministic classification that runs in sub-millisecond time.
- **Zero Latency & Cost:** No API rate limits, network latency, or recurring costs.
- **Privacy:** Descriptions and financial habits are never transmitted across the network.
- **Human-in-the-Loop:** Suggestions are pre-filled in forms and import reviews, but users retain full control to edit and correct any category.

### Q4: How is average daily spending calculated?
**Answer:**
- To avoid skewing during short months or leap years, average daily spending is calculated by taking total monthly expenses and dividing by `calendar.monthrange(year, month)[1]`.
- For multi-month views, the system computes the mean of the individual monthly daily rates rather than a naive division over arbitrary date spans.

### Q5: How are edge cases handled in the CSV cleaning pipeline?
**Answer:**
- The pipeline validates columns defensively: missing mandatory columns (`date`, `description`, `amount`) raise clear errors.
- Dates are parsed using `pd.to_datetime(..., errors="coerce")`, amounts coerced with `pd.to_numeric(..., errors="coerce")`.
- Any row with non-positive amounts ($\le 0$), blank descriptions, unsupported transaction types, or corrupt date strings is captured in a row-level error log (`Row X: <reason>`), allowing valid rows in the statement to be imported without abortion.

---

## 3. Potential Scalability & Production Evolution

| Current Architecture | Production Evolution (When Scaling) |
| :--- | :--- |
| **Storage:** SQLite file | PostgreSQL / RDS with connection pooling |
| **Categorization:** Keyword sets | Offline fine-tuned DistilBERT or TF-IDF + Logistic Regression |
| **Ingestion:** Pandas in-memory | Polars or Celery/Redis asynchronous batch processing |
| **Authentication:** Single-user local | OAuth2 / JWT authentication with multi-tenant tenancy |
