WITH reporting_cutoff AS (
    SELECT
        CAST(
            '{{ var("reporting_as_of", "2026-10-01T00:00:00+00:00") }}'
            AS TIMESTAMPTZ
        ) AS as_of
)

-- Milestones must follow the funnel order and precede the cutoff.
SELECT
    f.prospect_id

FROM {{ ref('fct_prospect_conversion') }} AS f

WHERE f.created_at >= f.as_of

   OR (
       f.subscription_within_30_days
       AND NOT f.trial_within_30_days
   )

   OR (
       f.payment_within_30_days
       AND NOT f.subscription_within_30_days
   )

   OR (
       f.trial_started_at IS NOT NULL
       AND (
           f.trial_started_at < f.created_at
           OR f.trial_started_at >= f.as_of
       )
   )

   OR (
       f.first_subscription_started_at IS NOT NULL
       AND (
           f.trial_started_at IS NULL
           OR f.first_subscription_started_at < f.trial_started_at
           OR f.first_subscription_started_at >= f.as_of
       )
   )

   OR (
       f.first_successful_payment_at IS NOT NULL
       AND (
           f.first_subscription_started_at IS NULL
           OR f.first_successful_payment_at
               < f.first_subscription_started_at
           OR f.first_successful_payment_at >= f.as_of
       )
   )

UNION ALL

-- Every observed prospect must remain, including non-converters.
SELECT
    p.prospect_id

FROM {{ ref('stg_prospects') }} AS p

CROSS JOIN reporting_cutoff AS c

LEFT JOIN {{ ref('fct_prospect_conversion') }} AS f
    ON p.prospect_id = f.prospect_id

WHERE p.created_at < c.as_of
  AND f.prospect_id IS NULL