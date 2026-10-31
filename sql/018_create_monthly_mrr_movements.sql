CREATE OR REPLACE VIEW monthly_mrr_movements AS

WITH subscription_events AS (
    SELECT
        started_at AS event_at,
        'new' AS event_type,
        billing_amount_usd / billing_interval_months AS mrr_usd
    FROM subscriptions
    WHERE LEFT(subscription_id, 4) = 'SYN_'

    UNION ALL

    SELECT
        ended_at AS event_at,
        'churn' AS event_type,
        billing_amount_usd / billing_interval_months AS mrr_usd
    FROM subscriptions
    WHERE LEFT(subscription_id, 4) = 'SYN_'
      AND ended_at IS NOT NULL
),

snapshot_pairs AS (
    SELECT
        snapshot_date,

        LAG(snapshot_date) OVER (
            ORDER BY snapshot_date
        ) AS previous_snapshot_date,

        LAG(total_mrr_usd) OVER (
            ORDER BY snapshot_date
        ) AS opening_mrr_usd,

        total_mrr_usd AS closing_mrr_usd

    FROM monthly_mrr_snapshot
),

movements AS (
    SELECT
        p.snapshot_date,
        p.opening_mrr_usd,
        p.closing_mrr_usd,

        COUNT(e.event_at) FILTER (
            WHERE e.event_type = 'new'
        ) AS new_subscriptions,

        ROUND(
            COALESCE(
                SUM(e.mrr_usd) FILTER (
                    WHERE e.event_type = 'new'
                ),
                0
            ),
            2
        ) AS new_mrr_usd,

        COUNT(e.event_at) FILTER (
            WHERE e.event_type = 'churn'
        ) AS churned_subscriptions,

        ROUND(
            COALESCE(
                SUM(e.mrr_usd) FILTER (
                    WHERE e.event_type = 'churn'
                ),
                0
            ),
            2
        ) AS churned_mrr_usd

    FROM snapshot_pairs AS p

    LEFT JOIN subscription_events AS e
        ON e.event_at > (
            p.previous_snapshot_date::timestamp
            AT TIME ZONE 'UTC'
        )
       AND e.event_at <= (
            p.snapshot_date::timestamp
            AT TIME ZONE 'UTC'
        )

    WHERE p.previous_snapshot_date IS NOT NULL

    GROUP BY
        p.snapshot_date,
        p.opening_mrr_usd,
        p.closing_mrr_usd
)

SELECT
    snapshot_date,
    opening_mrr_usd,
    new_subscriptions,
    new_mrr_usd,
    churned_subscriptions,
    churned_mrr_usd,

    new_mrr_usd - churned_mrr_usd AS net_mrr_change_usd,

    closing_mrr_usd,

    closing_mrr_usd - (
        opening_mrr_usd + new_mrr_usd - churned_mrr_usd
    ) AS reconciliation_difference_usd

FROM movements;

SELECT *
FROM monthly_mrr_movements
WHERE snapshot_date = DATE '2026-07-01';