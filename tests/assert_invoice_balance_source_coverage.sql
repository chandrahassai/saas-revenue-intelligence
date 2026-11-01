WITH eligible_invoices AS (
    SELECT invoice_id
    FROM {{ ref('stg_invoices') }}
    WHERE issued_at < CAST(
        '{{ var("reporting_as_of", "2026-10-01T00:00:00+00:00") }}'
        AS TIMESTAMPTZ
    )
),

balance_invoices AS (
    SELECT invoice_id
    FROM {{ ref('fct_invoice_balances') }}
)

SELECT
    COALESCE(
        e.invoice_id,
        b.invoice_id
    ) AS invoice_id,
    CASE
        WHEN e.invoice_id IS NULL THEN 'Unexpected invoice'
        WHEN b.invoice_id IS NULL THEN 'Missing invoice'
    END AS issue
FROM eligible_invoices AS e
FULL OUTER JOIN balance_invoices AS b
    ON e.invoice_id = b.invoice_id
WHERE e.invoice_id IS NULL
   OR b.invoice_id IS NULL