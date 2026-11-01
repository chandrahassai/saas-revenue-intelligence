WITH reporting_periods AS (
    SELECT
        snapshot_date,
        LAG(snapshot_date) OVER (
            ORDER BY snapshot_date
        ) AS period_start_date
    FROM {{ ref('fct_monthly_mrr_snapshot') }}
),

plans AS (
    SELECT DISTINCT plan_name
    FROM {{ ref('stg_subscriptions') }}
    WHERE LEFT(subscription_id, 4) = 'SYN_'
),

plan_period_counts AS (
    SELECT
        r.period_start_date,
        r.snapshot_date,
        p.plan_name,
        COUNT(s.subscription_id) AS opening_subscriptions,
        COUNT(s.subscription_id) FILTER (
            WHERE s.ended_at <= (
                r.snapshot_date::TIMESTAMP AT TIME ZONE 'UTC'
            )
        ) AS churned_subscriptions
    FROM reporting_periods AS r
    CROSS JOIN plans AS p
    LEFT JOIN {{ ref('stg_subscriptions') }} AS s
        ON LEFT(s.subscription_id, 4) = 'SYN_'
       AND s.plan_name = p.plan_name
       AND s.started_at <= (
            r.period_start_date::TIMESTAMP AT TIME ZONE 'UTC'
       )
       AND (
            s.ended_at IS NULL
            OR s.ended_at > (
                r.period_start_date::TIMESTAMP AT TIME ZONE 'UTC'
            )
       )
    WHERE r.period_start_date IS NOT NULL
    GROUP BY
        r.period_start_date,
        r.snapshot_date,
        p.plan_name
)

SELECT
    period_start_date,
    snapshot_date,
    plan_name,
    opening_subscriptions,
    churned_subscriptions,
    ROUND(
        100.0 * churned_subscriptions
        / NULLIF(opening_subscriptions, 0),
        2
    ) AS subscription_churn_pct
FROM plan_period_counts