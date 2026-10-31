INSERT INTO subscriptions (
    subscription_id,
    account_id,
    plan_name,
    billing_amount_usd,
    billing_interval_months,
    started_at,
    ended_at
)
VALUES (
    'SUB001',
    'ACC001',
    'Starter',
    1200.00,
    12,
    '2026-01-01 09:00:00+00',
    NULL
);

SELECT
    subscription_id,
    account_id,
    plan_name,
    ROUND(
        billing_amount_usd / billing_interval_months,
        2
    ) AS mrr_usd
FROM subscriptions
WHERE started_at <= TIMESTAMPTZ '2026-02-01 00:00:00+00'
  AND (
      ended_at IS NULL
      OR ended_at > TIMESTAMPTZ '2026-02-01 00:00:00+00'
  );