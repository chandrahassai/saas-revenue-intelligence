CREATE OR REPLACE VIEW monthly_mrr_snapshot AS

WITH reporting_dates AS (
    SELECT
        snapshot_utc AT TIME ZONE 'UTC' AS as_of
    FROM generate_series(
        TIMESTAMP '2025-01-01 00:00:00',
        TIMESTAMP '2026-10-01 00:00:00',
        INTERVAL '1 month'
    ) AS dates(snapshot_utc)
)

SELECT
    (m.as_of AT TIME ZONE 'UTC')::date AS snapshot_date,

    COUNT(DISTINCT s.account_id) AS active_accounts,

    COUNT(s.subscription_id) AS active_subscriptions,

    ROUND(
        COALESCE(
            SUM(
                s.billing_amount_usd
                / s.billing_interval_months
            ),
            0
        ),
        2
    ) AS total_mrr_usd

FROM reporting_dates AS m

LEFT JOIN subscriptions AS s
    ON LEFT(s.subscription_id, 4) = 'SYN_'
   AND s.started_at <= m.as_of
   AND (
       s.ended_at IS NULL
       OR s.ended_at > m.as_of
   )

GROUP BY m.as_of;

SELECT *
FROM monthly_mrr_snapshot
ORDER BY snapshot_date;