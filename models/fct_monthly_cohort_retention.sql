WITH reporting_cutoff AS (
    SELECT
        CAST(
            '{{ var("reporting_as_of", "2026-10-01T00:00:00+00:00") }}'
            AS TIMESTAMPTZ
        ) AS as_of
),

cohort_subscriptions AS (
    SELECT
        s.subscription_id,
        DATE_TRUNC(
            'month',
            s.started_at AT TIME ZONE 'UTC'
        )::date AS cohort_month,
        s.started_at,
        s.ended_at
    FROM {{ ref('stg_subscriptions') }} AS s
    CROSS JOIN reporting_cutoff AS c
    WHERE LEFT(s.subscription_id, 4) = 'SYN_'
      AND s.started_at < c.as_of
),

reporting_dates AS (
    SELECT
        m.snapshot_date,
        m.snapshot_date::timestamp AT TIME ZONE 'UTC' AS as_of
    FROM {{ ref('fct_monthly_mrr_snapshot') }} AS m
    CROSS JOIN reporting_cutoff AS c
    WHERE (
        m.snapshot_date::timestamp AT TIME ZONE 'UTC'
    ) <= c.as_of
),

cohort_counts AS (
    SELECT
        s.cohort_month,
        r.snapshot_date,

        (
            12 * (
                EXTRACT(YEAR FROM r.snapshot_date)::integer
                - EXTRACT(YEAR FROM s.cohort_month)::integer
            )
            + EXTRACT(MONTH FROM r.snapshot_date)::integer
            - EXTRACT(MONTH FROM s.cohort_month)::integer
        ) AS month_number,

        COUNT(*) AS cohort_subscriptions,

        COUNT(*) FILTER (
            WHERE s.started_at <= r.as_of
              AND (
                  s.ended_at IS NULL
                  OR s.ended_at > r.as_of
              )
        ) AS retained_subscriptions

    FROM cohort_subscriptions AS s
    JOIN reporting_dates AS r
        ON r.snapshot_date > s.cohort_month

    GROUP BY
        s.cohort_month,
        r.snapshot_date
)

SELECT
    cohort_month,
    snapshot_date,
    month_number,
    cohort_subscriptions,
    retained_subscriptions,

    ROUND(
        100.0 * retained_subscriptions
        / NULLIF(cohort_subscriptions, 0),
        2
    ) AS retention_pct

FROM cohort_counts