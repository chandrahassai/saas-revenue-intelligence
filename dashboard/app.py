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
def load_revenue_data():
    with psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "saas_analytics"),
        user=os.getenv("PGUSER", getpass.getuser()),
        password=os.getenv("PGPASSWORD", ""),
        connect_timeout=5,
        options="-c default_transaction_read_only=on",
    ) as connection:
        snapshots = query_dataframe(
            connection,
            """
            SELECT
                snapshot_date,
                active_accounts,
                active_subscriptions,
                total_mrr_usd
            FROM analytics.fct_monthly_mrr_snapshot
            ORDER BY snapshot_date;
            """,
        )

        movements = query_dataframe(
            connection,
            """
            SELECT
                snapshot_date,
                new_mrr_usd,
                churned_mrr_usd,
                net_mrr_change_usd
            FROM analytics.fct_monthly_mrr_movements
            ORDER BY snapshot_date;
            """,
        )

    snapshots["snapshot_date"] = pd.to_datetime(
        snapshots["snapshot_date"]
    )
    snapshots["total_mrr_usd"] = snapshots["total_mrr_usd"].astype(float)

    movements["snapshot_date"] = pd.to_datetime(
        movements["snapshot_date"]
    )

    for column in [
        "new_mrr_usd",
        "churned_mrr_usd",
        "net_mrr_change_usd",
    ]:
        movements[column] = movements[column].astype(float)

    return snapshots, movements


def main():
    st.set_page_config(
        page_title="SaaS Revenue Intelligence",
        page_icon="📊",
        layout="wide",
    )

    st.sidebar.title("SaaS Revenue Intelligence")

    if st.sidebar.button("Refresh data"):
        load_revenue_data.clear()

    st.title("Revenue overview")

    try:
        snapshots, movements = load_revenue_data()
    except (psycopg.Error, ValueError):
        logging.exception("Unable to load revenue data")
        st.error(
            "Revenue data is unavailable. Check the database connection "
            "and try refreshing. Technical details are in Terminal."
        )
        st.stop()

    if snapshots.empty:
        st.info("No monthly revenue snapshots are available.")
        st.stop()

    selected_date = st.sidebar.selectbox(
        "Reporting snapshot",
        options=snapshots["snapshot_date"].tolist()[::-1],
        format_func=lambda value: value.strftime("%B %d, %Y"),
    )

    st.sidebar.caption(
        "Snapshots are evaluated at 00:00 UTC. "
        "This page includes generated subscriptions only."
    )

    snapshot_history = snapshots.loc[
        snapshots["snapshot_date"] <= selected_date
    ].copy()

    movement_history = movements.loc[
        movements["snapshot_date"] <= selected_date
    ].copy()

    selected_snapshot = snapshot_history.iloc[-1]

    selected_movement = movements.loc[
        movements["snapshot_date"] == selected_date
    ]

    has_movement = not selected_movement.empty

    if has_movement:
        period = selected_movement.iloc[0]
        mrr_delta = f"{period['net_mrr_change_usd']:+,.0f}"
        new_mrr = f"{period['new_mrr_usd']:,.0f}"
        churned_mrr = f"{period['churned_mrr_usd']:,.0f}"
    else:
        mrr_delta = None
        new_mrr = "—"
        churned_mrr = "—"

    st.caption(
        f"As of {selected_date:%B %d, %Y} at 00:00 UTC. "
        "MRR measures recurring subscription value and is separate "
        "from collected cash."
    )

    cards = st.columns(4)

    cards[0].metric(
        "MRR (USD)",
        f"{selected_snapshot['total_mrr_usd']:,.0f}",
        delta=mrr_delta,
        help="The delta is net MRR change since the previous checkpoint.",
        border=True,
    )

    cards[1].metric(
        "Active accounts",
        f"{int(selected_snapshot['active_accounts']):,}",
        border=True,
    )

    cards[2].metric(
        "New MRR (USD)",
        new_mrr,
        border=True,
    )

    cards[3].metric(
        "Churned MRR (USD)",
        churned_mrr,
        border=True,
    )

    if has_movement:
        st.caption(
            "New and churned MRR cover the period since "
            "the previous monthly checkpoint."
        )
    else:
        st.info(
            "The first snapshot has no preceding checkpoint, "
            "so movement metrics are unavailable."
        )

    trend_column, movement_column = st.columns(2)

    with trend_column:
        st.subheader("MRR trend")

        trend = go.Figure(
            go.Scatter(
                x=snapshot_history["snapshot_date"],
                y=snapshot_history["total_mrr_usd"],
                mode="lines+markers",
                line={"color": "#2563eb", "width": 3},
                hovertemplate=(
                    "%{x|%b %d, %Y}<br>"
                    "MRR: USD %{y:,.2f}<extra></extra>"
                ),
            )
        )

        trend.update_layout(
            height=360,
            margin={"l": 0, "r": 0, "t": 15, "b": 0},
            xaxis_title="UTC snapshot",
            yaxis_title="MRR (USD)",
            yaxis_tickformat=",.0f",
        )

        st.plotly_chart(
            trend,
            width="stretch",
            key="revenue_trend",
        )

    with movement_column:
        st.subheader("MRR movements")

        if movement_history.empty:
            st.info("No movement periods are available for this snapshot.")
        else:
            movement_chart = go.Figure()

            movement_chart.add_bar(
                name="New MRR",
                x=movement_history["snapshot_date"],
                y=movement_history["new_mrr_usd"],
                marker_color="#059669",
            )

            movement_chart.add_bar(
                name="Churned MRR",
                x=movement_history["snapshot_date"],
                y=-movement_history["churned_mrr_usd"],
                marker_color="#dc2626",
            )

            movement_chart.update_layout(
                barmode="relative",
                height=360,
                margin={"l": 0, "r": 0, "t": 45, "b": 40},
                xaxis_title="Closing UTC snapshot",
                yaxis_title="MRR change (USD)",
                yaxis_tickformat=",.0f",
                legend={
                    "orientation": "h",
                    "x": 0,
                    "xanchor": "left",
                    "y": 1.02,
                    "yanchor": "bottom",
                },
            )

            st.plotly_chart(
                movement_chart,
                width="stretch",
                key="revenue_movements",
            )

            st.caption("Churned MRR is plotted below zero.")

    with st.expander("View monthly metrics"):
        display_history = snapshot_history.iloc[::-1].rename(
            columns={
                "snapshot_date": "Snapshot (UTC)",
                "active_accounts": "Active accounts",
                "active_subscriptions": "Active subscriptions",
                "total_mrr_usd": "MRR (USD)",
            }
        )

        display_history["Snapshot (UTC)"] = (
            display_history["Snapshot (UTC)"].dt.strftime("%Y-%m-%d")
        )

        st.dataframe(
            display_history,
            hide_index=True,
            width="stretch",
        )


if __name__ == "__main__":
    main()