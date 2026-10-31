CREATE OR REPLACE VIEW monthly_plan_churn AS
WITH reporting_periods AS (
    SELECT
        snapshot_date,
        LAG(snapshot_date) OVER (
            ORDER BY snapshot_date
        ) AS period_start_date
    FROM monthly_mrr_snapshot
),
plans AS (
    SELECT DISTINCT plan_name
    FROM subscriptions
    WHERE LEFT(subscription_id, 4) = 'SYN_'
)
SELECT
    r.period_start_date,
    r.snapshot_date,
    p.plan_name,
    COUNT(s.subscription_id) AS opening_subscriptions,
    COUNT(s.subscription_id) FILTER (
        WHERE s.ended_at <= (
            r.snapshot_date::timestamp AT TIME ZONE 'UTC'
        )
    ) AS churned_subscriptions,
    ROUND(
        100.0 * COUNT(s.subscription_id) FILTER (
            WHERE s.ended_at <= (
                r.snapshot_date::timestamp AT TIME ZONE 'UTC'
            )
        ) / NULLIF(COUNT(s.subscription_id), 0),
        2
    ) AS subscription_churn_pct
FROM reporting_periods AS r
CROSS JOIN plans AS p
LEFT JOIN subscriptions AS s
    ON LEFT(s.subscription_id, 4) = 'SYN_'
    AND s.plan_name = p.plan_name
    AND s.started_at <= (
        r.period_start_date::timestamp AT TIME ZONE 'UTC'
    )
    AND (
        s.ended_at IS NULL
        OR s.ended_at > (
            r.period_start_date::timestamp AT TIME ZONE 'UTC'
        )
    )
WHERE r.period_start_date IS NOT NULL
GROUP BY
    r.period_start_date,
    r.snapshot_date,
    p.plan_name;

SELECT
    COUNT(*) AS plan_period_rows,
    COUNT(DISTINCT snapshot_date) AS periods,
    COUNT(DISTINCT plan_name) AS plans
FROM monthly_plan_churn;

SELECT *
FROM monthly_plan_churn
WHERE snapshot_date = DATE '2026-07-01'
ORDER BY subscription_churn_pct DESC NULLS LAST;