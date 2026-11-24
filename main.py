"""Streamlit interface for the Personal Expense Tracker with Data Visualization."""

from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from expense_tracker.analytics import (
    analyze_transactions,
    clean_transaction_data,
    get_budget_status,
)
from expense_tracker.categorization import DEFAULT_CATEGORIES, suggest_category
from expense_tracker.database import (
    add_transaction,
    add_transactions,
    delete_budget,
    delete_transaction,
    get_budgets,
    get_transactions,
    initialize_db,
    save_budget,
    seed_sample_data,
    transaction_fingerprint,
    update_transaction,
)
from expense_tracker.reports import month_label, monthly_report_csv
from expense_tracker.synthetic import generate_synthetic_transactions

st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)
initialize_db()

# Currency Configuration
SUPPORTED_CURRENCIES = {
    "INR (₹)": {"symbol": "₹", "code": "INR"},
    "USD ($)": {"symbol": "$", "code": "USD"},
    "EUR (€)": {"symbol": "€", "code": "EUR"},
    "GBP (£)": {"symbol": "£", "code": "GBP"},
    "JPY (¥)": {"symbol": "¥", "code": "JPY"},
}

with st.sidebar:
    st.header("⚙️ Configuration")
    selected_currency_label = st.selectbox(
        "Display Currency",
        options=list(SUPPORTED_CURRENCIES.keys()),
        index=0,  # Default to INR
        help="Display currency for charts, metrics, and tables. Ensure you use one currency per dataset.",
    )
    currency_meta = SUPPORTED_CURRENCIES[selected_currency_label]
    currency_symbol = currency_meta["symbol"]
    currency_code = currency_meta["code"]

    st.info(
        f"**Active Currency:** {currency_code} ({currency_symbol})\n\n"
        "💡 *Note:* The application does not perform cross-currency conversions. All records are assumed to be in this single currency."
    )

    st.divider()
    st.header("⚡ Quick Actions")
    if st.button("📥 Load Demo Transactions", use_container_width=True):
        count, skipped, errors = seed_sample_data(PROJECT_ROOT / "data" / "sample_transactions.csv")
        st.success(f"Loaded {count} new demo rows! (Skipped {skipped} duplicates)")
        if errors:
            st.warning("\n".join(errors[:5]))
        st.rerun()

    st.divider()
    st.caption("🔒 **100% Local & Private**\nStored in `data/expenses.db` with zero external calls.")

st.title(f"💰 Personal Expense Tracker ({currency_code})")
st.caption("A private, local-first personal finance tracker with interactive visualizations. No banking connection required.")

tabs = st.tabs([
    "📊 Dashboard",
    "➕ Add Transaction",
    "📁 Import CSV",
    "🎯 Budgets",
    "📑 Monthly Report",
    "📝 Manage Transactions",
])


def current_transactions() -> pd.DataFrame:
    return get_transactions()


# -----------------------------------------------------------------------------
# TAB 1: DASHBOARD
# -----------------------------------------------------------------------------
with tabs[0]:
    all_tx = current_transactions()
    if all_tx.empty:
        st.warning("### 🚀 Welcome to Your Personal Expense Tracker!")
        st.write(
            "There are currently no transactions in your local database. "
            "You can get started immediately in one of three ways:"
        )
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("#### 1. Quick Demo Data")
            if st.button("Load Bundled Sample Data", key="empty_load_btn", type="primary"):
                count, skipped, errors = seed_sample_data(PROJECT_ROOT / "data" / "sample_transactions.csv")
                st.success(f"Added {count} demo records!")
                st.rerun()
        with col_b:
            st.markdown("#### 2. Manual Entry")
            st.write("Go to the **Add Transaction** tab to record your first income or expense.")
        with col_c:
            st.markdown("#### 3. CSV File Upload")
            st.write("Go to the **Import CSV** tab to upload or download synthetic datasets.")
    else:
        all_tx["month"] = all_tx["date"].dt.strftime("%Y-%m")
        months = sorted(all_tx["month"].unique(), reverse=True)

        col_filter, col_spacer = st.columns([2, 4])
        with col_filter:
            selected_month = st.selectbox(
                "📅 Select Reporting Month",
                months,
                format_func=month_label,
                key="dash_month_select",
            )

        month_tx = all_tx[all_tx["month"] == selected_month]
        month_analysis = analyze_transactions(month_tx, selected_month=selected_month)
        full_analysis = analyze_transactions(all_tx)

        spent = float(month_analysis["expenses"])
        earned = float(month_analysis["income"])
        net = float(month_analysis["net"])
        avg_daily = float(month_analysis["average_daily_spending"])
        top_cat = month_analysis["highest_spending_category"]
        top_val = 0.0
        if top_cat and not month_analysis["category_spending"].empty:
            cat_df = month_analysis["category_spending"]
            top_val = float(cat_df[cat_df["category"] == top_cat]["amount"].iloc[0])

        # KPI Metric Cards
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Spent", f"{currency_symbol}{spent:,.2f}")
        k2.metric("Income", f"{currency_symbol}{earned:,.2f}")
        k3.metric("Net Cash Flow", f"{currency_symbol}{net:,.2f}", delta=f"{currency_symbol}{net:,.2f}")
        k4.metric("Transactions", len(month_tx))
        k5.metric("Avg Daily Spend", f"{currency_symbol}{avg_daily:,.2f}")
        k6.metric("Top Category", f"{top_cat or '—'} ({currency_symbol}{top_val:,.2f})" if top_cat else "—")

        # Budgets Section & Overspending Alerts
        budgets = get_budgets()
        if budgets:
            st.markdown("---")
            st.subheader("🎯 Monthly Budget vs. Actual")
            budget_statuses = get_budget_status(month_tx[month_tx["type"] == "expense"], budgets)
            overspent_items = [b for b in budget_statuses if b["is_over"]]
            if overspent_items:
                alert_text = " • ".join([f"**{item['category']}** (Over by {currency_symbol}{item['over_by']:,.2f})" for item in overspent_items])
                st.error(f"🚨 **Overspending Alert:** {alert_text}")

            b_cols = st.columns(min(len(budget_statuses), 4))
            for idx, item in enumerate(budget_statuses):
                with b_cols[idx % len(b_cols)]:
                    delta_label = f"{currency_symbol}{item['remaining']:,.2f} remaining" if not item["is_over"] else f"🚨 Exceeded by {currency_symbol}{item['over_by']:,.2f}"
                    st.metric(
                        item["category"],
                        f"{currency_symbol}{item['spent']:,.2f} / {currency_symbol}{item['budget']:,.2f}",
                        delta=delta_label,
                        delta_color="normal" if not item["is_over"] else "inverse",
                    )
                    st.progress(item["used_ratio"])

        st.markdown("---")

        # 4 Required Visualizations
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader(f"1. Category-Wise Spending ({currency_code})")
            cat_data: pd.DataFrame = month_analysis["category_spending"]  # type: ignore
            if cat_data.empty:
                st.info("No expenses recorded for this month.")
            else:
                fig_bar = px.bar(
                    cat_data,
                    x="category",
                    y="amount",
                    color="category",
                    labels={"category": "Expense Category", "amount": f"Amount ({currency_code})"},
                    text_auto=f".2f",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig_bar.update_layout(
                    showlegend=False,
                    xaxis_title="",
                    yaxis_title=f"Spent ({currency_symbol})",
                    margin=dict(t=20, b=20, l=10, r=10),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with chart_col2:
            st.subheader(f"2. Monthly Spending Trend ({currency_code})")
            monthly_data: pd.DataFrame = full_analysis["monthly_spending"]  # type: ignore
            if monthly_data.empty:
                st.info("No monthly expense data available.")
            else:
                fig_line = px.line(
                    monthly_data,
                    x="month",
                    y="amount",
                    markers=True,
                    labels={"month": "Month", "amount": f"Total Spent ({currency_code})"},
                    color_discrete_sequence=["#1f77b4"],
                )
                fig_line.update_layout(
                    xaxis_title="Month",
                    yaxis_title=f"Total Expenses ({currency_symbol})",
                    margin=dict(t=20, b=20, l=10, r=10),
                )
                st.plotly_chart(fig_line, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            st.subheader("3. Payment Method Distribution")
            pay_data: pd.DataFrame = month_analysis["payment_method_spending"]  # type: ignore
            if pay_data.empty:
                st.info("No expense data recorded for this month.")
            else:
                fig_pie = px.pie(
                    pay_data,
                    values="amount",
                    names="payment_method",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                fig_pie.update_layout(margin=dict(t=20, b=20, l=10, r=10), legend_title_text="Method")
                st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col4:
            st.subheader(f"4. Daily Spending Trend ({month_label(selected_month)})")
            daily_data: pd.DataFrame = month_analysis["daily_spending"]  # type: ignore
            if daily_data.empty:
                st.info("No expense activity in this month.")
            else:
                fig_daily = px.line(
                    daily_data,
                    x="date",
                    y="amount",
                    markers=True,
                    labels={"date": "Date", "amount": f"Daily Spent ({currency_code})"},
                    color_discrete_sequence=["#ff7f0e"],
                )
                year, m_num = map(int, selected_month.split("-"))
                num_days = calendar.monthrange(year, m_num)[1]
                fig_daily.update_xaxes(
                    range=[f"{selected_month}-01", f"{selected_month}-{num_days:02d}"],
                    tickformat="%b %d",
                )
                fig_daily.update_layout(
                    xaxis_title="Day of Month",
                    yaxis_title=f"Spent ({currency_symbol})",
                    margin=dict(t=20, b=20, l=10, r=10),
                )
                st.plotly_chart(fig_daily, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Recent Month Activity")
        disp_cols = ["date", "description", "category", "type", "payment_method", "amount", "notes"]
        recent_df = month_tx[disp_cols].copy()
        recent_df["amount"] = recent_df["amount"].apply(lambda a: f"{currency_symbol}{a:,.2f}")
        st.dataframe(recent_df.head(10), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# TAB 2: ADD TRANSACTION
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("➕ Add a Transaction Manually")
    with st.form("manual_tx_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            txn_date = st.date_input("Date", value=date.today())
            description = st.text_input("Description", placeholder="e.g., Reliance Fresh, Metro Pass, Amazon")
            amount = st.number_input(f"Amount ({currency_code})", min_value=0.01, value=500.00, step=50.00)
            txn_type = st.selectbox("Type", ["expense", "income"])
        with c2:
            suggested = (
                suggest_category(description, txn_type)
                if description
                else ("Income" if txn_type == "income" else "Other")
            )
            cat_choices = list(dict.fromkeys([suggested, *DEFAULT_CATEGORIES]))
            category = st.selectbox("Category (Keyword-Suggested)", cat_choices, index=0)
            payment = st.selectbox("Payment Method", ["UPI / Digital Wallet", "Card", "Cash", "Bank Transfer", "Other"])
            notes = st.text_input("Notes (Optional)", placeholder="e.g., Weekly groceries")

        submitted = st.form_submit_button("💾 Save Transaction", type="primary")
        if submitted:
            try:
                new_id = add_transaction({
                    "date": txn_date,
                    "description": description,
                    "amount": amount,
                    "category": category,
                    "type": txn_type,
                    "payment_method": payment,
                    "notes": notes,
                })
                st.success(f"✅ Transaction #{new_id} saved successfully!")
                st.rerun()
            except ValueError as exc:
                st.error(f"❌ Validation Error: {exc}")


# -----------------------------------------------------------------------------
# TAB 3: IMPORT CSV
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📁 Import Transactions from CSV")
    st.write(
        "Upload your transaction statements. "
        "**Required Columns:** `date`, `description`, `amount`. "
        "**Optional Columns:** `category`, `type`, `payment_method`, `notes`."
    )

    down_c1, down_c2 = st.columns(2)
    with down_c1:
        st.download_button(
            "📥 Download Bundled Sample CSV",
            data=(PROJECT_ROOT / "data" / "sample_transactions.csv").read_bytes(),
            file_name="sample_transactions.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with down_c2:
        synthetic_df = generate_synthetic_transactions(count=100, seed=42)
        st.download_button(
            "🎲 Download Deterministic Synthetic CSV (100 Rows)",
            data=synthetic_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="synthetic_transactions_seed42.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload CSV Statement", type=["csv"])
    if uploaded_file is not None:
        try:
            raw_csv = pd.read_csv(uploaded_file)
            cleaned_df, parse_errors = clean_transaction_data(raw_csv)
            valid_rows = cleaned_df.to_dict(orient="records")
            for row in valid_rows:
                row["import_key"] = transaction_fingerprint(row)

            st.write(f"### Ingestion Preview: {len(valid_rows)} Valid Row(s)")
            st.dataframe(cleaned_df.head(10), use_container_width=True, hide_index=True)

            if parse_errors:
                st.warning("⚠️ **Row-Level Rejection Log:** Some rows contained invalid fields and were excluded:")
                for err in parse_errors[:15]:
                    st.write(f"- `{err}`")

            if valid_rows:
                if st.button(f"📥 Import {len(valid_rows)} Valid Transactions", type="primary"):
                    inserted, skipped, db_errors = add_transactions(valid_rows)
                    st.success(f"🎉 Successfully imported {inserted} records! (Skipped {skipped} duplicate rows).")
                    if db_errors:
                        st.warning("Database row errors:\n" + "\n".join(db_errors[:10]))
                    st.rerun()

        except Exception as exc:
            st.error(f"❌ Failed to parse CSV: {exc}")


# -----------------------------------------------------------------------------
# TAB 4: BUDGETS
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("🎯 Configure Monthly Category Budgets")
    st.caption("Budgets apply to calendar months and trigger visual warnings when exceeded.")

    existing_budgets = get_budgets()
    with st.form("budget_config_form"):
        col1, col2 = st.columns(2)
        with col1:
            valid_cats = [c for c in DEFAULT_CATEGORIES if c != "Income"]
            target_category = st.selectbox("Category", valid_cats)
        with col2:
            limit_val = st.number_input(f"Monthly Limit ({currency_code})", min_value=0.0, value=5000.0, step=500.0)
        if st.form_submit_button("💾 Save Budget Target", type="primary"):
            save_budget(target_category, limit_val)
            st.success(f"Saved {currency_symbol}{limit_val:,.2f} budget for {target_category}!")
            st.rerun()

    if existing_budgets:
        st.markdown("### Active Budgets")
        budget_disp = [
            {"Category": k, f"Monthly Limit ({currency_code})": f"{currency_symbol}{v:,.2f}"}
            for k, v in existing_budgets.items()
        ]
        st.dataframe(pd.DataFrame(budget_disp), use_container_width=True, hide_index=True)

        del_cat = st.selectbox("Delete a Budget", ["(Select category to delete)", *existing_budgets.keys()])
        if del_cat != "(Select category to delete)" and st.button("🗑️ Delete Selected Budget"):
            delete_budget(del_cat)
            st.success(f"Deleted budget for {del_cat}.")
            st.rerun()
    else:
        st.info("No budgets configured yet. Add limits above to track overspending on the dashboard.")


# -----------------------------------------------------------------------------
# TAB 5: MONTHLY REPORT
# -----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("📑 Export Monthly Financial Report")
    all_data = current_transactions()
    if all_data.empty:
        st.info("Add or import transactions before generating a monthly report.")
    else:
        all_data["month"] = all_data["date"].dt.strftime("%Y-%m")
        all_months = sorted(all_data["month"].unique(), reverse=True)
        rep_month = st.selectbox("Select Report Month", all_months, format_func=month_label, key="rep_month_sel")

        sub_df = all_data[all_data["month"] == rep_month]
        rep_analysis = analyze_transactions(sub_df, selected_month=rep_month)

        st.markdown(
            f"**Report Period:** {month_label(rep_month)}  \n"
            f"**Transactions:** {len(sub_df)} | "
            f"**Total Spent:** {currency_symbol}{rep_analysis['expenses']:,.2f} | "
            f"**Total Income:** {currency_symbol}{rep_analysis['income']:,.2f} | "
            f"**Net:** {currency_symbol}{rep_analysis['net']:,.2f}"
        )

        report_csv_bytes = monthly_report_csv(
            all_data,
            month=rep_month,
            budgets=get_budgets(),
            currency_code=currency_code,
        )

        st.download_button(
            label=f"📥 Download expense-report-{rep_month}.csv",
            data=report_csv_bytes,
            file_name=f"expense-report-{rep_month}.csv",
            mime="text/csv",
            type="primary",
        )


# -----------------------------------------------------------------------------
# TAB 6: MANAGE TRANSACTIONS (VIEW, EDIT, DELETE)
# -----------------------------------------------------------------------------
with tabs[5]:
    st.subheader("📝 Transaction Ledger & Management")
    records = current_transactions()
    if records.empty:
        st.info("No transactions found.")
    else:
        search_query = st.text_input("🔍 Search transactions by description, category, or payment method")
        filtered_view = records
        if search_query.strip():
            mask = (
                records["description"].str.contains(search_query, case=False, na=False)
                | records["category"].str.contains(search_query, case=False, na=False)
                | records["payment_method"].str.contains(search_query, case=False, na=False)
            )
            filtered_view = records[mask]

        st.dataframe(
            filtered_view[["id", "date", "description", "category", "type", "payment_method", "amount", "notes"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        action_col1, action_col2 = st.columns(2)

        with action_col1:
            st.markdown("#### ✏️ Edit an Existing Transaction")
            tx_options = {
                int(row.id): f"#{row.id} | {row.date:%Y-%m-%d} | {row.description} | {currency_symbol}{row.amount:,.2f}"
                for row in filtered_view.itertuples()
            }
            if tx_options:
                selected_edit_id = st.selectbox("Select Transaction to Edit", list(tx_options.keys()), format_func=lambda x: tx_options[x])
                target_row = records[records["id"] == selected_edit_id].iloc[0]

                with st.form(f"edit_form_{selected_edit_id}"):
                    e_date = st.date_input("Date", value=target_row["date"].date())
                    e_desc = st.text_input("Description", value=target_row["description"])
                    e_amount = st.number_input(f"Amount ({currency_code})", min_value=0.01, value=float(target_row["amount"]), step=10.0)
                    e_type = st.selectbox("Type", ["expense", "income"], index=0 if target_row["type"] == "expense" else 1)
                    current_cat = target_row["category"]
                    edit_cats = list(dict.fromkeys([current_cat, *DEFAULT_CATEGORIES]))
                    e_cat = st.selectbox("Category", edit_cats, index=0)
                    current_pay = str(target_row["payment_method"] or "Other").strip()
                    standard_methods = ["UPI / Digital Wallet", "Card", "Cash", "Bank Transfer", "Other"]
                    matched_standard = next((m for m in standard_methods if m.lower() == current_pay.lower()), None)
                    effective_pay = matched_standard if matched_standard else (current_pay or "Other")
                    edit_pay_options = list(dict.fromkeys([effective_pay, *standard_methods]))
                    pay_index = edit_pay_options.index(effective_pay) if effective_pay in edit_pay_options else 0
                    e_pay = st.selectbox(
                        "Payment Method",
                        edit_pay_options,
                        index=pay_index,
                    )
                    e_notes = st.text_input("Notes", value=str(target_row["notes"] or ""))

                    if st.form_submit_button("💾 Update Transaction", type="primary"):
                        try:
                            update_transaction(selected_edit_id, {
                                "date": e_date,
                                "description": e_desc,
                                "amount": e_amount,
                                "category": e_cat,
                                "type": e_type,
                                "payment_method": e_pay,
                                "notes": e_notes,
                            })
                            st.success(f"Transaction #{selected_edit_id} updated successfully!")
                            st.rerun()
                        except ValueError as err:
                            st.error(f"Update failed: {err}")

        with action_col2:
            st.markdown("#### 🗑️ Delete a Transaction")
            if tx_options:
                selected_del_id = st.selectbox("Select Transaction to Delete", list(tx_options.keys()), format_func=lambda x: tx_options[x], key="del_select")
                if st.button("🗑️ Confirm Delete", type="secondary"):
                    delete_transaction(selected_del_id)
                    st.success(f"Transaction #{selected_del_id} deleted successfully.")
                    st.rerun()
