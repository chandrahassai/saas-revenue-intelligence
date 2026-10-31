WITH report_settings AS (
    SELECT
        TIMESTAMPTZ '2026-02-01 00:00:00+00' AS as_of
)

SELECT
    COUNT(DISTINCT s.account_id) AS active_accounts,
    COUNT(*) AS active_subscriptions,
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
FROM subscriptions AS s
CROSS JOIN report_settings AS r
WHERE s.started_at <= r.as_of
  AND (
      s.ended_at IS NULL
      OR s.ended_at > r.as_of
  );