WITH report_settings AS (
    SELECT
        TIMESTAMPTZ '2026-01-04 00:00:00+00' AS as_of
),

payments_by_invoice AS (
    SELECT
        p.invoice_id,
        SUM(p.attempted_amount_usd) AS collected_cash_usd
    FROM payment_attempts AS p
    CROSS JOIN report_settings AS r
    WHERE p.status = 'succeeded'
      AND p.completed_at <= r.as_of
    GROUP BY p.invoice_id
)

SELECT
    i.invoice_id,
    i.invoice_amount_usd,
    COALESCE(p.collected_cash_usd, 0) AS collected_cash_usd,
    i.invoice_amount_usd
        - COALESCE(p.collected_cash_usd, 0) AS outstanding_balance_usd
FROM invoices AS i
CROSS JOIN report_settings AS r
LEFT JOIN payments_by_invoice AS p
    ON i.invoice_id = p.invoice_id
WHERE i.issued_at <= r.as_of
ORDER BY i.invoice_id;