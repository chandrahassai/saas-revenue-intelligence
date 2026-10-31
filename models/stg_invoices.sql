SELECT
    invoice_id,
    subscription_id,
    invoice_amount_usd,
    issued_at,
    due_at,
    service_period_start,
    service_period_end
FROM {{ source('saas_raw', 'invoices') }}