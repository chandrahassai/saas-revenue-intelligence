SELECT
    account_id,
    account_name,
    industry,
    country_code,
    signed_up_at
FROM {{ source('saas_raw', 'accounts') }}