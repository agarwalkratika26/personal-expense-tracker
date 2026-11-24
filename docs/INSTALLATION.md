# Installation Guide

## 1. Set up Python

Install Python 3.10 or newer. During a Windows installation, enable the option to add Python to PATH if the installer offers it. Open a new terminal after installation and check the version:

```text
python --version
```

On Windows, if `python` is not recognized but the Python launcher is available, try:

```powershell
py --version
```

On macOS/Linux, use `python3 --version` if `python` does not point to Python 3.10 or newer. Install Python from the official Python distribution or your operating system's trusted package manager.

## 2. Open the project folder

In a terminal, change directory to the folder containing `main.py` and `requirements.txt`. For example, in PowerShell:

```powershell
cd "C:\path\to\Personal-Expense-Tracker-Visualization"
```

In macOS/Linux:

```bash
cd /path/to/Personal-Expense-Tracker-Visualization
```

Use the actual location where you saved or cloned the project.

## 3. Create a virtual environment

A virtual environment keeps this app's Python packages separate from other projects.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If `py` is unavailable, use `python -m venv .venv` instead. If PowerShell blocks activation due to its execution policy, use Command Prompt activation (`.venv\Scripts\activate.bat`) or configure your local Python environment according to your organization's policy.

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, the terminal prompt usually shows `(.venv)`. When finished, leave the environment with `deactivate`.

## 4. Install the required libraries

With the environment activated, update pip and install the pinned project dependency ranges:

### Windows

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS/Linux

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The project directly uses:

- **Streamlit** for the interactive dashboard and forms.
- **Pandas** for reading CSV files and grouping transaction data.
- **Plotly** for interactive dashboard charts.

Python's built-in `sqlite3`, `csv`, and `datetime` modules provide local database and date/file support. They do not need separate installation. NumPy, Matplotlib, and Seaborn are useful optional additions for notebooks or static analysis, but are not required by the current app.

## 5. Run the app

```text
streamlit run main.py
```

Streamlit opens the dashboard in a browser. Use **Load sample transactions** to load the fictional demo data. The app creates `data/expenses.db` locally the first time it runs; the database is excluded from Git.

## Common installation issues

- **`python` or `py` is not recognized:** Reinstall or repair Python and enable PATH integration, or use the executable name provided by your installation.
- **`streamlit` is not recognized:** Activate `.venv` and run `python -m pip install -r requirements.txt`; then try `python -m streamlit run main.py`.
- **Packages install but imports fail:** Confirm that the virtual environment is active in the same terminal used to run Streamlit.
- **Permission or network errors during installation:** Check the network connection or package-index access, and install in a user-owned project environment rather than a system Python location.
