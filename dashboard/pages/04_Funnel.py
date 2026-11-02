"""Display the completed-window prospect conversion funnel."""

import getpass
import logging
import os

import pandas as pd
import plotly.graph_objects as go
import psycopg
import streamlit as st


LOGGER = logging.getLogger(__name__)

COUNT_COLUMNS = [
    "total_prospects",
    "eligible_prospects",
    "pending_prospects",
    "trial_prospects",
    "subscribed_prospects",
    "paying_prospects",
]


@st.cache_data(ttl=60, show_spinner=False)
def load_funnel_data():
    with psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "saas_analytics"),
        user=os.getenv("PGUSER", getpass.getuser()),
        password=os.getenv("PGPASSWORD", ""),
        connect_timeout=5,
        options="-c default_transaction_read_only=on",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    as_of,
                    acquisition_channel,
                    total_prospects,
                    eligible_prospects,
                    pending_prospects,
                    trial_prospects,
                    subscribed_prospects,
                    paying_prospects
                FROM analytics.mart_conversion_funnel
                ORDER BY acquisition_channel
                """
            )

            data = pd.DataFrame(
                cursor.fetchall(),
                columns=[
                    column.name
                    for column in cursor.description
                ],
            )

    if data.empty:
        return data

    data["as_of"] = pd.to_datetime(data["as_of"], utc=True)

    if (
        data["as_of"].isna().any()
        or data["as_of"].nunique() != 1
    ):
        raise ValueError("Funnel reporting cutoffs are inconsistent.")

    for column in COUNT_COLUMNS:
        data[column] = pd.to_numeric(
            data[column],
            errors="raise",
        ).astype("int64")

    return data


def percentage(numerator, denominator):
    if denominator == 0:
        return None

    return 100.0 * numerator / denominator


def format_percentage(value):
    if value is None:
        return "—"

    return f"{value:.2f}%"


def main():
    st.set_page_config(
        page_title="Funnel | SaaS Revenue Intelligence",
        page_icon="📊",
        layout="wide",
    )

    st.sidebar.title("SaaS Revenue Intelligence")

    if st.sidebar.button(
        "Refresh data",
        key="funnel_refresh",
    ):
        load_funnel_data.clear()

    st.title("Conversion funnel")

    try:
        data = load_funnel_data()
    except Exception:
        LOGGER.exception("Unable to load funnel data.")
        st.error(
            "Funnel data could not be loaded. Check that PostgreSQL "
            "is running and the funnel models have been built."
        )
        st.stop()

    if data.empty:
        st.info("No prospect funnel data is available.")
        st.stop()

    channels = sorted(
        data["acquisition_channel"].unique().tolist()
    )

    channel = st.sidebar.selectbox(
        "Acquisition channel",
        ["All channels", *channels],
        key="funnel_channel",
    )

    st.sidebar.caption(
        "Conversion rates include only prospects with a full "
        "30-day observation window. Recent prospects remain pending."
    )

    if channel == "All channels":
        selected = data.copy()
    else:
        selected = data.loc[
            data["acquisition_channel"] == channel
        ].copy()

    totals = {
        column: int(selected[column].sum())
        for column in COUNT_COLUMNS
    }

    eligible = totals["eligible_prospects"]
    trials = totals["trial_prospects"]
    subscribed = totals["subscribed_prospects"]
    paid = totals["paying_prospects"]
    pending = totals["pending_prospects"]

    as_of = data["as_of"].iloc[0]

    st.caption(
        f"Cutoff: {as_of.strftime('%B %d, %Y at %H:%M UTC')}. "
        "Each conversion window starts at prospect creation and "
        "ends 720 hours later. Events at the closing boundary "
        "are excluded."
    )

    stage_metrics = [
        ("Eligible prospects", eligible),
        ("Trial starts", trials),
        ("Subscription starts", subscribed),
        ("First payments", paid),
    ]

    for column, (label, value) in zip(
        st.columns(4),
        stage_metrics,
    ):
        column.metric(
            label,
            f"{value:,}",
            border=True,
        )

    rate_metrics = [
        (
            "Prospect to trial",
            percentage(trials, eligible),
        ),
        (
            "Trial to subscription",
            percentage(subscribed, trials),
        ),
        (
            "Subscription to payment",
            percentage(paid, subscribed),
        ),
        (
            "Prospect to payment",
            percentage(paid, eligible),
        ),
    ]

    for column, (label, value) in zip(
        st.columns(4),
        rate_metrics,
    ):
        column.metric(
            label,
            format_percentage(value),
            border=True,
        )

    st.caption(
        f"{totals['total_prospects']:,} observed prospects; "
        f"{pending:,} pending prospects excluded from conversion "
        f"rates. Channel selection: {channel}. "
        "Overall rates use combined counts across selected channels."
    )

    left, right = st.columns(2)

    with left:
        st.subheader("30-day conversion funnel")

        if eligible == 0:
            st.info(
                "No prospects have completed their observation "
                "window for this selection."
            )
        else:
            funnel = go.Figure(
                go.Funnel(
                    y=[
                        "Eligible prospects",
                        "Trial started",
                        "Subscription started",
                        "First payment",
                    ],
                    x=[
                        eligible,
                        trials,
                        subscribed,
                        paid,
                    ],
                    textinfo="value+percent initial",
                    textposition="inside",
                    marker={
                        "color": [
                            "#2563EB",
                            "#3B82F6",
                            "#0D9488",
                            "#059669",
                        ]
                    },
                    hovertemplate=(
                        "%{y}<br>"
                        "%{x:,.0f} prospects"
                        "<extra></extra>"
                    ),
                )
            )

            funnel.update_layout(
                height=420,
                margin=dict(l=10, r=20, t=20, b=20),
                showlegend=False,
            )

            st.plotly_chart(
                funnel,
                width="stretch",
                key="conversion_funnel_chart",
                config={"displaylogo": False},
            )

        st.caption(
            "All stages use the same group of eligible prospects."
        )

    with right:
        st.subheader("Prospect-to-payment conversion")

        comparison = selected.loc[
            selected["eligible_prospects"] > 0
        ].copy()

        if comparison.empty:
            st.info(
                "Channel conversion rates are unavailable until "
                "prospects complete their observation windows."
            )
        else:
            comparison["conversion_pct"] = (
                100.0
                * comparison["paying_prospects"]
                / comparison["eligible_prospects"]
            )

            comparison = comparison.sort_values(
                ["conversion_pct", "acquisition_channel"]
            )

            figure = go.Figure(
                go.Bar(
                    x=comparison["conversion_pct"],
                    y=comparison["acquisition_channel"],
                    orientation="h",
                    marker_color="#2563EB",
                    text=[
                        f"{value:.2f}%"
                        for value in comparison["conversion_pct"]
                    ],
                    textposition="outside",
                    cliponaxis=False,
                    customdata=comparison[
                        ["eligible_prospects", "paying_prospects"]
                    ].to_numpy(),
                    hovertemplate=(
                        "%{y}<br>"
                        "Conversion: %{x:.2f}%<br>"
                        "Eligible prospects: %{customdata[0]:,.0f}<br>"
                        "First payments: %{customdata[1]:,.0f}"
                        "<extra></extra>"
                    ),
                )
            )

            figure.update_layout(
                height=420,
                margin=dict(l=10, r=50, t=20, b=40),
                xaxis=dict(
                    title="Conversion (%)",
                    range=[0, 100],
                    ticksuffix="%",
                ),
                yaxis=dict(title=None),
                showlegend=False,
            )

            st.plotly_chart(
                figure,
                width="stretch",
                key="channel_conversion_chart",
                config={"displaylogo": False},
            )

        st.caption(
            "Hover over a bar to see its eligible prospect count."
        )

    st.subheader("Conversion by acquisition channel")

    display = selected[
        ["acquisition_channel", *COUNT_COLUMNS]
    ].copy()

    display["Prospect to payment (%)"] = [
        format_percentage(
            percentage(
                int(row.paying_prospects),
                int(row.eligible_prospects),
            )
        )
        for row in selected.itertuples(index=False)
    ]

    display = display.rename(
        columns={
            "acquisition_channel": "Acquisition channel",
            "total_prospects": "Observed prospects",
            "eligible_prospects": "Eligible prospects",
            "pending_prospects": "Pending prospects",
            "trial_prospects": "Trial starts",
            "subscribed_prospects": "Subscription starts",
            "paying_prospects": "First payments",
        }
    )

    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
    )

    with st.expander("View stage transitions"):
        transitions = [
            ("Prospect to trial", eligible, trials),
            ("Trial to subscription", trials, subscribed),
            ("Subscription to payment", subscribed, paid),
        ]

        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Transition": label,
                        "Starting prospects": starting,
                        "Reached next stage": reached,
                        "Did not reach next stage within window": (
                            starting - reached
                        ),
                        "Conversion": format_percentage(
                            percentage(reached, starting)
                        ),
                    }
                    for label, starting, reached in transitions
                ]
            ),
            hide_index=True,
            width="stretch",
        )

    st.info(
        "The dataset is synthetic. Prospect and trial events and "
        "acquisition channels are simulated; channel differences "
        "do not establish real marketing effectiveness."
    )

    st.caption(
        "Subscription and payment milestones come from the generated "
        "billing records. First payment means a positive successful "
        "payment and does not require full invoice settlement."
    )


if __name__ == "__main__":
    main()