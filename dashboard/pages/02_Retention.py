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
def load_retention_data():
    with psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "saas_analytics"),
        user=os.getenv("PGUSER", getpass.getuser()),
        password=os.getenv("PGPASSWORD", ""),
        connect_timeout=5,
        options="-c default_transaction_read_only=on",
    ) as connection:
        cohorts = query_dataframe(
            connection,
            """
            SELECT
                cohort_month,
                snapshot_date,
                month_number,
                cohort_subscriptions,
                retained_subscriptions,
                retention_pct
            FROM analytics.fct_monthly_cohort_retention
            ORDER BY cohort_month, month_number;
            """,
        )

        plan_churn = query_dataframe(
            connection,
            """
            SELECT
                period_start_date,
                snapshot_date,
                plan_name,
                opening_subscriptions,
                churned_subscriptions,
                subscription_churn_pct
            FROM analytics.fct_monthly_plan_churn
            ORDER BY snapshot_date, plan_name;
            """,
        )

    for column in ["cohort_month", "snapshot_date"]:
        cohorts[column] = pd.to_datetime(cohorts[column])

    cohorts["retention_pct"] = cohorts["retention_pct"].astype(float)

    for column in ["period_start_date", "snapshot_date"]:
        plan_churn[column] = pd.to_datetime(plan_churn[column])

    plan_churn["subscription_churn_pct"] = (
        plan_churn["subscription_churn_pct"].astype(float)
    )

    return cohorts, plan_churn


def build_retention_heatmap(cohorts):
    matrix = (
        cohorts.pivot(
            index="cohort_month",
            columns="month_number",
            values="retention_pct",
        )
        .sort_index()
        .sort_index(axis=1)
    )

    cohort_sizes = (
        cohorts.groupby("cohort_month")["cohort_subscriptions"]
        .first()
    )

    row_labels = [
        f"{month:%Y-%m} (n={int(cohort_sizes.loc[month])})"
        for month in matrix.index
    ]

    figure = go.Figure(
        go.Heatmap(
            z=matrix.to_numpy(),
            x=[int(month) for month in matrix.columns],
            y=row_labels,
            zmin=0,
            zmax=100,
            colorscale="YlGnBu",
            texttemplate="%{z:.1f}",
            textfont={"size": 10},
            hoverongaps=False,
            xgap=1,
            ygap=1,
            colorbar={
                "title": {"text": "Retained (%)"},
                "ticksuffix": "%",
            },
            hovertemplate=(
                "Cohort: %{y}<br>"
                "Month number: %{x}<br>"
                "Retained: %{z:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        height=max(400, 32 * len(matrix) + 120),
        margin={"l": 0, "r": 0, "t": 20, "b": 50},
        plot_bgcolor="#eeeeee",
        xaxis_title="Months since subscription start month",
        yaxis_title="Subscription start cohort",
    )

    figure.update_xaxes(
        tickmode="linear",
        tick0=1,
        dtick=1,
        showgrid=False,
        zeroline=False,
    )

    figure.update_yaxes(
        autorange="reversed",
        showgrid=False,
        zeroline=False,
    )

    return figure


def summarize_plan_churn(plan_churn):
    summary = (
        plan_churn.groupby("plan_name", as_index=False)
        .agg(
            churn_events=("churned_subscriptions", "sum"),
            opening_subscription_periods=("opening_subscriptions", "sum"),
        )
    )

    denominator = summary["opening_subscription_periods"].replace(
        0,
        float("nan"),
    )

    summary["pooled_monthly_churn_pct"] = (
        100.0 * summary["churn_events"] / denominator
    ).round(2)

    return summary.sort_values(
        "pooled_monthly_churn_pct",
        ascending=False,
    )


def main():
    st.set_page_config(
        page_title="Retention | SaaS Revenue Intelligence",
        page_icon="📊",
        layout="wide",
    )

    st.sidebar.title("SaaS Revenue Intelligence")

    if st.sidebar.button("Refresh data", key="refresh_retention"):
        load_retention_data.clear()

    st.sidebar.caption(
        "This page includes generated subscriptions only. "
        "The reporting period comes from the existing dbt models."
    )

    st.title("Retention overview")

    try:
        cohorts, plan_churn = load_retention_data()
    except (psycopg.Error, ValueError):
        logging.exception("Unable to load retention data")
        st.error(
            "Retention data is unavailable. Check the database connection "
            "and try refreshing. Technical details are in Terminal."
        )
        st.stop()

    if cohorts.empty or plan_churn.empty:
        st.info(
            "Retention data is incomplete or unavailable. "
            "Build the cohort retention and plan churn dbt models."
        )
        st.stop()

    latest_snapshot = cohorts["snapshot_date"].max()

    plan_churn = plan_churn.loc[
        plan_churn["snapshot_date"] <= latest_snapshot
    ].copy()

    st.caption(
        f"Observed through {latest_snapshot:%B %d, %Y} at 00:00 UTC. "
        "These results measure subscription retention and churn."
    )

    cohort_sizes = (
        cohorts.groupby("cohort_month")["cohort_subscriptions"]
        .first()
    )

    cards = st.columns(3)

    cards[0].metric(
        "Subscription start cohorts",
        f"{len(cohort_sizes):,}",
        border=True,
    )

    cards[1].metric(
        "Observed cohort checkpoints",
        f"{len(cohorts):,}",
        border=True,
    )

    cards[2].metric(
        "Subscriptions in observed cohorts",
        f"{int(cohort_sizes.sum()):,}",
        border=True,
    )

    st.subheader("Cohort subscription retention")

    st.write(
        "Each row groups subscriptions that started in the same UTC "
        "calendar month. Each cell shows the percentage still active "
        "at that cohort's monthly checkpoint."
    )

    st.plotly_chart(
        build_retention_heatmap(cohorts),
        width="stretch",
        key="cohort_retention_heatmap",
    )

    st.caption(
        "Month 1 is the first monthly boundary after the start month, "
        "not an exact 30-day anniversary. Gray cells are unobserved "
        "checkpoints, not zero retention. The row labels show original "
        "cohort sizes."
    )

    st.info(
        "Compare cohorts within the same month-number column. "
        "The last observed cell in each row represents a different "
        "cohort age. Small cohorts can show large percentage changes "
        "from a single cancellation."
    )

    st.subheader("Pooled monthly churn by plan")

    st.write(
        "Pooled monthly churn divides total churn events by total "
        "opening subscription counts across the observed periods."
    )

    if plan_churn.empty:
        st.info("No plan churn periods are available.")
    else:
        summary = summarize_plan_churn(plan_churn)

        churn_chart = go.Figure(
            go.Bar(
                x=summary["pooled_monthly_churn_pct"],
                y=summary["plan_name"],
                orientation="h",
                marker_color="#2563eb",
                text=[
                    f"{value:.2f}%"
                    for value in summary["pooled_monthly_churn_pct"]
                ],
                textposition="outside",
                cliponaxis=False,
                hovertemplate=(
                    "Plan: %{y}<br>"
                    "Pooled monthly churn: %{x:.2f}%"
                    "<extra></extra>"
                ),
            )
        )

        churn_chart.update_layout(
            height=300,
            margin={"l": 0, "r": 60, "t": 15, "b": 40},
            xaxis_title="Pooled monthly subscription churn (%)",
            yaxis_title=None,
            xaxis_ticksuffix="%",
        )

        churn_chart.update_xaxes(rangemode="tozero")
        churn_chart.update_yaxes(autorange="reversed")

        st.plotly_chart(
            churn_chart,
            width="stretch",
            key="pooled_plan_churn",
        )

        st.dataframe(
            summary.rename(
                columns={
                    "plan_name": "Plan",
                    "churn_events": "Churn events",
                    "opening_subscription_periods": (
                        "Opening subscription-periods"
                    ),
                    "pooled_monthly_churn_pct": (
                        "Pooled monthly churn (%)"
                    ),
                }
            ),
            hide_index=True,
            width="stretch",
        )

        st.caption(
            f"Includes {plan_churn['snapshot_date'].nunique()} monthly "
            "periods. This is not cumulative customer churn or an "
            "unweighted average of monthly percentages."
        )

    with st.expander("View cohort checkpoint data"):
        display_cohorts = cohorts.copy()

        for column in ["cohort_month", "snapshot_date"]:
            display_cohorts[column] = (
                display_cohorts[column].dt.strftime("%Y-%m-%d")
            )

        st.dataframe(
            display_cohorts.rename(
                columns={
                    "cohort_month": "Cohort month",
                    "snapshot_date": "Snapshot (UTC)",
                    "month_number": "Month number",
                    "cohort_subscriptions": "Original subscriptions",
                    "retained_subscriptions": "Retained subscriptions",
                    "retention_pct": "Retention (%)",
                }
            ),
            hide_index=True,
            width="stretch",
        )

    st.caption(
        "The data is synthetic. These results do not establish why "
        "customers churned or measure the effect of a business intervention."
    )


if __name__ == "__main__":
    main()