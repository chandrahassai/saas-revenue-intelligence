-- Counts must partition the population and decrease through stages.
SELECT
    acquisition_channel

FROM {{ ref('mart_conversion_funnel') }}

WHERE total_prospects
        <> eligible_prospects + pending_prospects

   OR LEAST(
       total_prospects,
       eligible_prospects,
       pending_prospects,
       trial_prospects,
       subscribed_prospects,
       paying_prospects
   ) < 0

   OR trial_prospects > eligible_prospects
   OR subscribed_prospects > trial_prospects
   OR paying_prospects > subscribed_prospects

UNION ALL

-- Rates must be null exactly when the denominator is zero.
-- Otherwise, each percentage must be between zero and 100.
SELECT
    f.acquisition_channel

FROM {{ ref('mart_conversion_funnel') }} AS f

CROSS JOIN LATERAL (
    VALUES
        (f.prospect_to_trial_pct, f.eligible_prospects),
        (f.trial_to_subscription_pct, f.trial_prospects),
        (f.subscription_to_payment_pct, f.subscribed_prospects),
        (f.prospect_to_payment_pct, f.eligible_prospects)
) AS r(rate_pct, denominator)

WHERE (
    r.denominator = 0
    AND r.rate_pct IS NOT NULL
)

OR (
    r.denominator > 0
    AND (
        r.rate_pct IS NULL
        OR r.rate_pct NOT BETWEEN 0 AND 100
    )
)