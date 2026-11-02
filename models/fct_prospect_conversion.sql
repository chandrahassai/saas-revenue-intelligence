WITH reporting_cutoff AS (
    SELECT
        CAST(
            '{{ var("reporting_as_of", "2026-10-01T00:00:00+00:00") }}'
            AS TIMESTAMPTZ
        ) AS as_of
),

observed_prospects AS (
    SELECT
        p.prospect_id,
        p.acquisition_channel,
        p.account_id,
        p.created_at,

        CASE
            WHEN p.trial_started_at < c.as_of
                THEN p.trial_started_at
        END AS trial_started_at,

        p.created_at + INTERVAL '720 hours'
            AS conversion_deadline,

        c.as_of

    FROM {{ ref('stg_prospects') }} AS p
    CROSS JOIN reporting_cutoff AS c

    WHERE p.created_at < c.as_of
),

observed_subscriptions AS (
    SELECT
        p.prospect_id,
        s.subscription_id,
        s.started_at,
        p.as_of

    FROM observed_prospects AS p

    JOIN {{ ref('stg_subscriptions') }} AS s
        ON p.account_id = s.account_id

    WHERE s.started_at >= p.trial_started_at
      AND s.started_at < p.as_of
),

subscription_milestones AS (
    SELECT
        prospect_id,
        MIN(started_at) AS first_subscription_started_at

    FROM observed_subscriptions

    GROUP BY prospect_id
),

payment_milestones AS (
    SELECT
        s.prospect_id,
        MIN(p.completed_at) AS first_successful_payment_at

    FROM observed_subscriptions AS s

    JOIN {{ ref('stg_invoices') }} AS i
        ON s.subscription_id = i.subscription_id

    JOIN {{ ref('stg_payment_attempts') }} AS p
        ON i.invoice_id = p.invoice_id

    WHERE p.status = 'succeeded'
      AND p.attempted_amount_usd > 0
      AND p.completed_at >= s.started_at
      AND p.completed_at >= i.issued_at
      AND p.completed_at < s.as_of
      AND i.issued_at < s.as_of

    GROUP BY s.prospect_id
)

SELECT
    p.prospect_id,
    p.acquisition_channel,
    p.account_id,

    DATE_TRUNC(
        'month',
        p.created_at AT TIME ZONE 'UTC'
    )::DATE AS prospect_cohort_month,

    p.created_at,
    p.trial_started_at,
    s.first_subscription_started_at,
    cash.first_successful_payment_at,
    p.conversion_deadline,
    p.as_of,

    p.conversion_deadline <= p.as_of AS is_mature,

    COALESCE(
        p.trial_started_at < p.conversion_deadline,
        FALSE
    ) AS trial_within_30_days,

    COALESCE(
        s.first_subscription_started_at < p.conversion_deadline,
        FALSE
    ) AS subscription_within_30_days,

    COALESCE(
        cash.first_successful_payment_at < p.conversion_deadline,
        FALSE
    ) AS payment_within_30_days

FROM observed_prospects AS p

LEFT JOIN subscription_milestones AS s
    ON p.prospect_id = s.prospect_id

LEFT JOIN payment_milestones AS cash
    ON p.prospect_id = cash.prospect_id