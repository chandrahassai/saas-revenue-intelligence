import getpass
import logging
import os

import pandas as pd
import plotly.graph_objects as go
import psycopg
import streamlit as st


def query_dataframe(connection, query):
    with connection.cursor() as cursor:
        cursor.execute(query)

        return pd.DataFrame(
            cursor.fetchall(),
            columns=[column.name for column in cursor.description],
        )


@st.cache_data(ttl=60, show_spinner=False)
def load_collections_data():
    with psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "saas_analytics"),
        user=os.getenv("PGUSER", getpass.getuser()),
        password=os.getenv("PGPASSWORD", ""),
        connect_timeout=5,
        options="-c default_transaction_read_only=on",
    ) as connection:
        invoices = query_dataframe(
            connection,
            """
            SELECT
                invoice_id,
                as_of,
                outstanding_balance_usd,
                days_past_due,
                aging_bucket,
                is_overdue
            FROM analytics.fct_invoice_aging
            WHERE outstanding_balance_usd > 0
            ORDER BY days_past_due, invoice_id;
            """,
        )

        accounts = query_dataframe(
            connection,
            """
            SELECT
                account_id,
                account_name,
                industry,
                country_code,
                as_of,
                unpaid_invoice_count,
                overdue_invoice_count,
                total_outstanding_usd,
                overdue_balance_usd,
                balance_91_plus_usd,
                oldest_unpaid_days_past_due
            FROM analytics.mart_account_collections
            ORDER BY overdue_balance_usd DESC, account_id;
            """,
        )

        diagnostics = query_dataframe(
            connection,
            """
            SELECT
                invoice_id,
                as_of,
                outstanding_balance_usd,
                days_past_due,
                payment_activity_category
            FROM analytics.fct_overdue_payment_diagnostics
            ORDER BY invoice_id;
            """,
        )

    for frame in [invoices, accounts, diagnostics]:
        frame["as_of"] = pd.to_datetime(frame["as_of"], utc=True)

    invoices["outstanding_balance_usd"] = (
        invoices["outstanding_balance_usd"].astype(float)
    )

    for column in [
        "total_outstanding_usd",
        "overdue_balance_usd",
        "balance_91_plus_usd",
    ]:
        accounts[column] = accounts[column].astype(float)

    diagnostics["outstanding_balance_usd"] = (
        diagnostics["outstanding_balance_usd"].astype(float)
    )

    return invoices, accounts, diagnostics


def display_account_table(accounts):
    columns = [
        "account_id",
        "account_name",
        "industry",
        "country_code",
        "unpaid_invoice_count",
        "overdue_invoice_count",
        "total_outstanding_usd",
        "overdue_balance_usd",
        "balance_91_plus_usd",
        "oldest_unpaid_days_past_due",
    ]

    display = accounts[columns].copy()

    for column in [
        "total_outstanding_usd",
        "overdue_balance_usd",
        "balance_91_plus_usd",
    ]:
        display[column] = display[column].round(2)

    st.dataframe(
        display.rename(
            columns={
                "account_id": "Account ID",
                "account_name": "Account",
                "industry": "Industry",
                "country_code": "Country",
                "unpaid_invoice_count": "Unpaid invoices",
                "overdue_invoice_count": "Overdue invoices",
                "total_outstanding_usd": "Outstanding (USD)",
                "overdue_balance_usd": "Overdue (USD)",
                "balance_91_plus_usd": "91+ days overdue (USD)",
                "oldest_unpaid_days_past_due": (
                    "Oldest unpaid invoice: days past due"
                ),
            }
        ),
        hide_index=True,
        width="stretch",
    )


def main():
    st.set_page_config(
        page_title="Collections | SaaS Revenue Intelligence",
        page_icon="📊",
        layout="wide",
    )

    st.sidebar.title("SaaS Revenue Intelligence")

    if st.sidebar.button("Refresh data", key="refresh_collections"):
        load_collections_data.clear()

    st.sidebar.caption(
        "This page includes generated records and the two original "
        "teaching examples. All monetary amounts are in USD."
    )

    st.title("Collections overview")

    try:
        invoices, accounts, diagnostics = load_collections_data()
    except (psycopg.Error, ValueError):
        logging.exception("Unable to load collections data")
        st.error(
            "Collections data is unavailable. Check the database "
            "connection and try refreshing. Technical details "
            "are in Terminal."
        )
        st.stop()

    if invoices.empty:
        st.info("No invoices with an outstanding balance are available.")
        st.stop()

    cutoffs = pd.concat(
        [
            invoices["as_of"],
            accounts["as_of"],
            diagnostics["as_of"],
        ],
        ignore_index=True,
    ).drop_duplicates()

    if len(cutoffs) != 1 or cutoffs.isna().any():
        st.error(
            "The collections views do not have a consistent reporting "
            "cutoff. Rebuild the collections dbt models together, "
            "then refresh."
        )
        st.stop()

    reporting_cutoff = cutoffs.iloc[0]

    overdue_invoices = invoices.loc[invoices["is_overdue"]].copy()

    total_outstanding = invoices["outstanding_balance_usd"].sum()
    total_overdue = overdue_invoices["outstanding_balance_usd"].sum()

    balance_91_plus = overdue_invoices.loc[
        overdue_invoices["days_past_due"] >= 91,
        "outstanding_balance_usd",
    ].sum()

    st.caption(
        f"As of {reporting_cutoff:%B %d, %Y at %H:%M UTC}. "
        "Balances reflect invoices issued and successful payments "
        "completed before the reporting cutoff."
    )

    cards = st.columns(4)

    cards[0].metric(
        "Outstanding balance (USD)",
        f"{total_outstanding:,.0f}",
        border=True,
    )

    cards[1].metric(
        "Overdue balance (USD)",
        f"{total_overdue:,.0f}",
        border=True,
    )

    cards[2].metric(
        "91+ days overdue (USD)",
        f"{balance_91_plus:,.0f}",
        border=True,
    )

    cards[3].metric(
        "Overdue invoices",
        f"{len(overdue_invoices):,}",
        border=True,
    )

    st.caption(
        f"{len(invoices):,} unpaid invoices across "
        f"{accounts['account_id'].nunique():,} accounts with a balance. "
        "Outstanding balance includes amounts that are not yet overdue."
    )

    aging_summary = (
        invoices.groupby("aging_bucket", as_index=False)
        .agg(
            unpaid_invoice_count=("invoice_id", "count"),
            outstanding_balance_usd=("outstanding_balance_usd", "sum"),
            first_days_past_due=("days_past_due", "min"),
        )
        .sort_values("first_days_past_due")
    )

    aging_column, activity_column = st.columns(2)

    with aging_column:
        st.subheader("Outstanding balance by age")

        aging_chart = go.Figure(
            go.Bar(
                x=aging_summary["aging_bucket"],
                y=aging_summary["outstanding_balance_usd"],
                marker_color="#2563eb",
                hovertemplate=(
                    "%{x}<br>"
                    "Outstanding: USD %{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

        aging_chart.update_layout(
            height=360,
            margin={"l": 0, "r": 0, "t": 15, "b": 70},
            xaxis_title="Invoice aging bucket",
            yaxis_title="Outstanding balance (USD)",
            yaxis_tickformat=",.0f",
        )

        aging_chart.update_xaxes(
            type="category",
            tickangle=-25,
        )

        st.plotly_chart(
            aging_chart,
            width="stretch",
            key="collections_aging",
        )

        st.caption(
            "Aging uses UTC calendar dates. Only invoices with a "
            "positive outstanding balance are included."
        )

    with activity_column:
        st.subheader("Payment activity on overdue invoices")

        if diagnostics.empty:
            st.info("No overdue payment diagnostics are available.")
        else:
            activity_summary = (
                diagnostics.groupby(
                    "payment_activity_category",
                    as_index=False,
                )
                .agg(
                    overdue_invoice_count=("invoice_id", "count"),
                    overdue_balance_usd=("outstanding_balance_usd", "sum"),
                )
                .sort_values(
                    "overdue_balance_usd",
                    ascending=False,
                )
            )

            activity_chart = go.Figure(
                go.Bar(
                    x=activity_summary["overdue_balance_usd"],
                    y=activity_summary["payment_activity_category"],
                    orientation="h",
                    marker_color="#d97706",
                    hovertemplate=(
                        "%{y}<br>"
                        "Overdue: USD %{x:,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

            activity_chart.update_layout(
                height=360,
                margin={"l": 0, "r": 10, "t": 15, "b": 40},
                xaxis_title="Overdue balance (USD)",
                yaxis_title=None,
                xaxis_tickformat=",.0f",
            )

            activity_chart.update_yaxes(autorange="reversed")
            activity_chart.update_xaxes(rangemode="tozero")

            st.plotly_chart(
                activity_chart,
                width="stretch",
                key="collections_payment_activity",
            )

            st.caption(
                "Categories describe completed payment activity "
                "recorded before the cutoff."
            )

    with st.expander("View aging totals"):
        st.dataframe(
            aging_summary.drop(
                columns="first_days_past_due"
            ).rename(
                columns={
                    "aging_bucket": "Aging bucket",
                    "unpaid_invoice_count": "Unpaid invoices",
                    "outstanding_balance_usd": (
                        "Outstanding balance (USD)"
                    ),
                }
            ),
            hide_index=True,
            width="stretch",
        )

    if not diagnostics.empty:
        with st.expander("View payment activity totals"):
            st.dataframe(
                activity_summary.rename(
                    columns={
                        "payment_activity_category": "Payment activity",
                        "overdue_invoice_count": "Overdue invoices",
                        "overdue_balance_usd": "Overdue balance (USD)",
                    }
                ),
                hide_index=True,
                width="stretch",
            )

    st.subheader("Accounts with the largest overdue balances")

    priority_accounts = (
        accounts.loc[accounts["overdue_balance_usd"] > 0]
        .sort_values(
            ["overdue_balance_usd", "account_id"],
            ascending=[False, True],
        )
        .head(10)
    )

    if priority_accounts.empty:
        st.info("No accounts have an overdue balance.")
    else:
        top_balance = priority_accounts["overdue_balance_usd"].sum()

        share = (
            100.0 * top_balance / total_overdue
            if total_overdue > 0
            else 0.0
        )

        st.write(
            f"The {len(priority_accounts)} accounts shown below hold "
            f"USD {top_balance:,.0f}, or {share:.2f}% of the total "
            "overdue balance."
        )

        st.caption(
            "Accounts are ordered by overdue balance for collection "
            "review. This ordering does not predict recoverability."
        )

        display_account_table(priority_accounts)

    with st.expander("View all accounts with a balance"):
        display_account_table(accounts)

    st.info(
        "Outstanding balances are not confirmed losses or guaranteed "
        "recoveries. Payment activity categories do not establish "
        "the cause of nonpayment. No completed attempt does not "
        "necessarily mean no attempt was initiated."
    )

    st.caption(
        "The dataset is synthetic. No payment retries or customer "
        "communications are performed by this dashboard."
    )


if __name__ == "__main__":
    main()