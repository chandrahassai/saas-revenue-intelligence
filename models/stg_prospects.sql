SELECT
    prospect_id,
    acquisition_channel,
    created_at,
    trial_started_at,
    account_id
FROM {{ source('saas_funnel_raw', 'prospects') }}