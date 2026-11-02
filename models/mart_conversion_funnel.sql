WITH stage_counts AS (
    SELECT
        as_of,
        acquisition_channel,

        COUNT(*) AS total_prospects,

        COUNT(*) FILTER (
            WHERE is_mature
        ) AS eligible_prospects,

        COUNT(*) FILTER (
            WHERE NOT is_mature
        ) AS pending_prospects,

        COUNT(*) FILTER (
            WHERE is_mature
              AND trial_within_30_days
        ) AS trial_prospects,

        COUNT(*) FILTER (
            WHERE is_mature
              AND subscription_within_30_days
        ) AS subscribed_prospects,

        COUNT(*) FILTER (
            WHERE is_mature
              AND payment_within_30_days
        ) AS paying_prospects

    FROM {{ ref('fct_prospect_conversion') }}

    GROUP BY
        as_of,
        acquisition_channel
)

SELECT
    as_of,
    acquisition_channel,
    total_prospects,
    eligible_prospects,
    pending_prospects,
    trial_prospects,
    subscribed_prospects,
    paying_prospects,

    ROUND(
        100.0 * trial_prospects
        / NULLIF(eligible_prospects, 0),
        2
    ) AS prospect_to_trial_pct,

    ROUND(
        100.0 * subscribed_prospects
        / NULLIF(trial_prospects, 0),
        2
    ) AS trial_to_subscription_pct,

    ROUND(
        100.0 * paying_prospects
        / NULLIF(subscribed_prospects, 0),
        2
    ) AS subscription_to_payment_pct,

    ROUND(
        100.0 * paying_prospects
        / NULLIF(eligible_prospects, 0),
        2
    ) AS prospect_to_payment_pct

FROM stage_counts