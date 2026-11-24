# Phase-wise Implementation Plan

This plan follows the project's flow from an empty folder to a shareable GitHub repository. The starter project already contains the app and demo data; use the phases as a build sequence or as a way to explain how it was developed.

## Phase 1: Setup

**What to do:** Install Python 3.10 or newer. Create and activate a virtual environment, then install packages from `requirements.txt`.

**Why:** A virtual environment isolates this project's packages from other Python projects and makes setup repeatable.

**Expected output:** A working Python environment with Streamlit, pandas, and Plotly installed.

**Common beginner mistakes:** Using a different Python interpreter to install and run packages; forgetting to activate the environment; installing packages one by one without recording dependencies.

## Phase 2: Project folder creation

**What to do:** Organize the project into a `main.py` entry point, reusable modules under `src/`, a data folder, documentation, and a dependency file. This repository also includes notebooks, outputs, images, and reports folders for portfolio materials.

**Why:** Separating the interface, database, categorization, and reports makes the project easier to maintain and explain.

**Expected output:** A clear project structure with each module having a defined responsibility.

**Common beginner mistakes:** Putting all logic in one large file; using ambiguous filenames such as `new.py`; forgetting `__init__.py` when creating a Python package.

## Phase 3: Expense CSV creation

**What to do:** Create a CSV with headers such as `date`, `description`, `amount`, `category`, `type`, `payment_method`, and `notes`. Use fictional or synthetic values for a public portfolio demo.

**Why:** CSV is simple to inspect and can be created without a banking connection. It provides a repeatable way to try imports and analysis.

**Expected output:** A small dataset with consistent columns and realistic but invented transactions. The sample in `data/sample_transactions.csv` has 20 rows.

**Common beginner mistakes:** Changing column names between rows or files; mixing date formats; entering currency symbols into numeric amount cells; using real private transaction data in a public repository.

## Phase 4: Expense data loading

**What to do:** Read CSV data with pandas and collect manual entries through Streamlit. Convert the loaded records into the same fields before storing them.

**Why:** Consistent input structure means the same cleaning and analysis logic can work for both entry methods.

**Expected output:** A preview of imported rows and transaction records ready for validation and storage.

**Common beginner mistakes:** Assuming every CSV has all optional columns; not checking that required columns exist; treating blank cells as the text `nan`; importing rows before showing the user a preview.

## Phase 5: Data cleaning

**What to do:** Normalize column names, parse dates, trim text, convert amounts to numbers, fill defaults for optional values, and reject invalid rows with a clear error. Keep amounts positive and use `type` to distinguish income from expenses.

**Why:** Analysis is only reliable when the input values are valid and consistently represented.

**Expected output:** Validated transaction records suitable for storage and aggregation, with invalid CSV rows identified for the user.

**Common beginner mistakes:** Silently dropping bad rows; confusing zero with a missing amount; allowing negative expenses without defining a refund convention; validating dates only after storing records.

## Phase 6: Category-wise analysis

**What to do:** Group expense records by category and sum the amounts. Calculate the highest-spending category for the selected month or period. Suggest missing categories from the description using transparent keyword rules.

**Why:** Category totals help users identify where their money is going and compare spending with category budgets.

**Expected output:** Category totals, a highest-spend result, and data suitable for a category chart.

**Common beginner mistakes:** Including income in expense totals; grouping categories that differ only by case or extra spaces; assuming keyword suggestions are always correct instead of letting users choose a category.

## Phase 7: Monthly trend analysis

**What to do:** Convert transaction dates to a year-month period and aggregate expense totals per month. Keep income and expense totals separate, and compute net cash flow as income minus expenses.

**Why:** A monthly series reveals changes over time and supports month-to-month planning.

**Expected output:** Monthly expense totals and a time-ordered series for a trend chart or report.

**Common beginner mistakes:** Sorting month labels alphabetically (which can misorder years); grouping by month number without year; counting income as spending; treating a month with no rows as missing without deciding how it should appear.

## Phase 8: Data visualization

**What to do:** Display category spending, monthly spending trend, payment method totals, and budget progress with clear labels, units, and date context. Use Streamlit for the dashboard and Plotly for interactive charts; Matplotlib or Seaborn are options for static charts.

**Why:** Visuals make patterns and comparisons easier to scan than raw rows alone.

**Expected output:** A dashboard with summary metrics and charts that answer questions about category, month, payment method, and budget status.

**Common beginner mistakes:** Mixing currencies; using unclear axes; comparing different periods without labeling them; using a pie chart with too many categories; showing a budget percentage above 100% without making overspending clear.

## Phase 9: Report generation

**What to do:** Let the user select a month and export a CSV with summary, category, budget, and transaction details. Use a descriptive filename that includes the reporting month.

**Why:** A report can be saved, reviewed, or opened in spreadsheet software outside the app.

**Expected output:** A downloadable monthly CSV with clear columns and totals that match the selected period.

**Common beginner mistakes:** Exporting all months accidentally; omitting column headers; formatting amounts as text when numeric values are more useful; forgetting to distinguish summary rows from transaction rows.

## Phase 10: GitHub upload

**What to do:** Review `.gitignore`, add the source code and synthetic sample data, write a useful README, capture redacted or synthetic screenshots, initialize Git, commit, add the GitHub remote, and push the `main` branch.

**Why:** A public repository lets others review the code, setup instructions, design choices, and working results as proof of work.

**Expected output:** A repository with readable source, documentation, sample data, and screenshots, but no private transaction database, credentials, virtual environment, or personal exports.

**Common beginner mistakes:** Committing `.venv/` or `data/expenses.db`; pushing real financial records or secrets; forgetting to add screenshots to the README; uploading without testing the clone-and-run steps on a clean environment.

## Suggested completion checklist

- Create an environment and install the declared dependencies.
- Run the app and load the synthetic sample rows.
- Try manual entry, CSV preview/import, a budget, dashboard filters, and a monthly export.
- Verify the CSV report month and totals match the dashboard.
- Review `.gitignore` and use only synthetic or redacted data in public materials.
- Follow the GitHub instructions in the root `README.md`.

**Implementation note:** The current app covers manual/CSV input, synthetic data generation, validation, SQLite storage, category/month/payment-method/daily analyses, budgets, four dashboard charts, and monthly CSV reports.
