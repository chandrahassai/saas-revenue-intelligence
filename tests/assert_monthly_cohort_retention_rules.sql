WITH retention_history AS (
    SELECT
        *,

        LAG(retained_subscriptions) OVER (
            PARTITION BY cohort_month
            ORDER BY snapshot_date
        ) AS previous_retained_subscriptions,

        LAG(cohort_subscriptions) OVER (
            PARTITION BY cohort_month
            ORDER BY snapshot_date
        ) AS previous_cohort_subscriptions

    FROM {{ ref('fct_monthly_cohort_retention') }}
)

SELECT
    cohort_month,
    snapshot_date,
    'Duplicate cohort checkpoint' AS issue

FROM retention_history

GROUP BY
    cohort_month,
    snapshot_date

HAVING COUNT(*) > 1

UNION ALL

SELECT
    cohort_month,
    snapshot_date,
    'Invalid retention counts, dates, percentage, or progression' AS issue

FROM retention_history

WHERE month_number < 1
   OR snapshot_date <> (
       cohort_month + MAKE_INTERVAL(months => month_number)
   )::date
   OR cohort_subscriptions <= 0
   OR retained_subscriptions < 0
   OR retained_subscriptions > cohort_subscriptions
   OR retention_pct < 0
   OR retention_pct > 100
   OR retention_pct IS DISTINCT FROM ROUND(
       100.0 * retained_subscriptions
       / NULLIF(cohort_subscriptions, 0),
       2
   )
   OR retained_subscriptions > previous_retained_subscriptions
   OR (
       previous_cohort_subscriptions IS NOT NULL
       AND cohort_subscriptions <> previous_cohort_subscriptions
   )