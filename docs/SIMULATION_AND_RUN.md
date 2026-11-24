# Virtual Simulation and Running the Project

## Simulate a personal finance tracker

Use the bundled fictional transactions or generate a fresh synthetic CSV from the **Import CSV** tab. No bank account or real financial information is needed.

1. **Create records:** Load the sample data from the sidebar, type a manual transaction, or download and import the generated synthetic CSV. Each row includes a date, description, amount, category, transaction type, payment method, and note.
2. **Assign categories:** Existing CSV categories are retained. If category is blank, local keyword rules infer it from the description: “Fresh market” suggests Groceries, “Taxi ride” suggests Transport, and “Cafe” suggests Food & Dining. Unmatched purchases become Other. You can choose a different category when entering a manual transaction.
3. **Group spending:** The analysis separates expenses from income, then sums expenses by category, payment method, and transaction date. Income is not included in expense totals.
4. **Calculate monthly trends:** Expense dates are converted to calendar months (`YYYY-MM`). Monthly expense sums create the trend series; the dashboard shows all months with expenses, while the monthly selector filters the other summaries.
5. **Identify overspending:** Compare selected-month spending in a category with its monthly budget. For example, a Groceries limit of $40 against $42.75 of January groceries is $2.75 over budget.
6. **Generate charts:** Plotly creates the category bar chart, multi-month spending line chart, payment-method pie chart, and selected-month daily spending trend. The dashboard also shows total spending, income, net cash flow, average daily spending, and the highest-spending category.
7. **Create insights:** Read the metrics and charts together, then download the selected month's CSV report. The report includes summary rows, category totals, payment-method totals, and transaction details.

Average daily spending is calculated as a month's total expenses divided by the number of calendar days in that month. Net cash flow is income minus expenses.

## Run the project

First create and activate a virtual environment and install `requirements.txt`. The complete Windows/macOS setup is in [`INSTALLATION.md`](INSTALLATION.md).

From the project root, with the virtual environment active:

### Windows PowerShell or macOS/Linux

```text
streamlit run main.py
```

If the `streamlit` command is not found, use:

```text
python -m streamlit run main.py
```

## Expected result

Streamlit prints a startup message similar to:

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open the local URL if it does not open automatically. Select **Load sample transactions** to populate the included 20 synthetic transactions from January through April 2026. On the dashboard, select a month to view its total spending, income, net cash flow, average daily spending, top category, budget status, category bar chart, payment-method pie chart, and daily trend. The monthly spending line chart compares months.

From the **Import CSV** tab, download a newly generated synthetic CSV, preview its cleaned rows, and import it. From **Monthly report**, choose a month and download `expense-report-YYYY-MM.csv`.

## Example insight from the bundled sample

For January 2026, the synthetic dataset contains $161.44 in expenses and $2,800.00 in income, giving net cash flow of $2,638.56. Utilities is the highest-spending category at $67.20. Average spending is about $5.21 per calendar day (31 days). If the Groceries budget is set to $40.00, January's $42.75 grocery total is $2.75 over budget.

This example is illustrative only; it is calculated from fictional sample transactions.

## Screenshots, charts, and GitHub artifacts

Capture the running app with synthetic data and save portfolio images under `images/`:

- `images/dashboard-overview.png`: overview with metrics and all four charts, using a wide browser window.
- `images/budget-warning.png`: dashboard showing at least one over-budget category.
- `images/csv-import-preview.png`: CSV tab showing generated data before import.
- `images/monthly-report.png`: report tab with the selected month and download button.

Use Windows Snipping Tool or macOS screenshot shortcuts; crop out browser tabs or unrelated personal details. The screenshots show the charts. If saving separate chart images, use Plotly's chart export control when available; otherwise take a close, readable crop of each chart. Keep chart titles, axis labels, and selected month visible.

The repository includes [`reports/examples/expense-report-2026-01.csv`](../reports/examples/expense-report-2026-01.csv), a sample report made only from the bundled fictional data. Upload synthetic or redacted examples and screenshots. Do not upload `data/expenses.db`, private transactions, or personal financial reports.
