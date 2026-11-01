WITH reporting_cutoff AS (
    SELECT
        CAST(
            '{{ var("reporting_as_of", "2026-10-01T00:00:00+00:00") }}'
            AS TIMESTAMPTZ
        ) AS as_of
),

successful_payments AS (
    SELECT
        p.invoice_id,
        SUM(p.attempted_amount_usd) AS collected_cash_usd
    FROM {{ ref('stg_payment_attempts') }} AS p
    CROSS JOIN reporting_cutoff AS c
    WHERE p.status = 'succeeded'
      AND p.completed_at < c.as_of
    GROUP BY p.invoice_id
)

SELECT
    i.invoice_id,
    i.subscription_id,
    i.invoice_amount_usd,
    i.issued_at,
    i.due_at,
    i.service_period_start,
    i.service_period_end,
    c.as_of,
    COALESCE(
        p.collected_cash_usd,
        0::NUMERIC
    ) AS collected_cash_usd,
    i.invoice_amount_usd - COALESCE(
        p.collected_cash_usd,
        0::NUMERIC
    ) AS outstanding_balance_usd
FROM {{ ref('stg_invoices') }} AS i
CROSS JOIN reporting_cutoff AS c
LEFT JOIN successful_payments AS p
    ON i.invoice_id = p.invoice_id
WHERE i.issued_at < c.as_of