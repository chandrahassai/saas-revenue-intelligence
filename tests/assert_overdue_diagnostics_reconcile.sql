WITH expected_overdue AS (
    SELECT
        invoice_id,
        as_of,
        outstanding_balance_usd
    FROM {{ ref('fct_invoice_aging') }}
    WHERE is_overdue
)

SELECT
    COALESCE(
        i.invoice_id,
        d.invoice_id
    ) AS invoice_id,
    i.as_of AS expected_cutoff,
    d.as_of AS actual_cutoff,
    i.outstanding_balance_usd AS expected_balance_usd,
    d.outstanding_balance_usd AS actual_balance_usd
FROM expected_overdue AS i
FULL OUTER JOIN {{ ref('fct_overdue_payment_diagnostics') }} AS d
    ON i.invoice_id = d.invoice_id
WHERE i.invoice_id IS NULL
   OR d.invoice_id IS NULL
   OR i.as_of IS DISTINCT FROM d.as_of
   OR i.outstanding_balance_usd
        IS DISTINCT FROM d.outstanding_balance_usd