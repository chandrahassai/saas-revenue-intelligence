SELECT
    payment_attempt_id,
    invoice_id,
    attempted_amount_usd,
    status,
    attempted_at,
    completed_at,
    failure_reason
FROM {{ source('saas_raw', 'payment_attempts') }}