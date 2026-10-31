SELECT
    subscription_id,
    account_id,
    plan_name,
    billing_amount_usd,
    billing_interval_months,
    started_at,
    ended_at
FROM {{ source('saas_raw', 'subscriptions') }}