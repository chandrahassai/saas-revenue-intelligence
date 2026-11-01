SELECT
    snapshot_date,
    plan_name,
    'Duplicate plan-period' AS issue
FROM {{ ref('fct_monthly_plan_churn') }}
GROUP BY
    snapshot_date,
    plan_name
HAVING COUNT(*) > 1

UNION ALL

SELECT
    snapshot_date,
    plan_name,
    'Invalid period, counts, or percentage' AS issue
FROM {{ ref('fct_monthly_plan_churn') }}
WHERE snapshot_date <= period_start_date
   OR opening_subscriptions < 0
   OR churned_subscriptions < 0
   OR churned_subscriptions > opening_subscriptions
   OR (
        opening_subscriptions = 0
        AND subscription_churn_pct IS NOT NULL
   )
   OR (
        opening_subscriptions > 0
        AND (
            subscription_churn_pct IS NULL
            OR subscription_churn_pct < 0
            OR subscription_churn_pct > 100
        )
   )