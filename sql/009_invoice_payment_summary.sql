WITH payments_by_invoice AS (
    SELECT
        invoice_id,
        SUM(
            CASE
                WHEN status = 'succeeded'
                    THEN attempted_amount_usd
                ELSE 0
            END
        ) AS collected_cash_usd
    FROM payment_attempts
    GROUP BY invoice_id
)

SELECT
    i.invoice_id,
    a.account_name,
    i.invoice_amount_usd,
    COALESCE(p.collected_cash_usd, 0) AS collected_cash_usd,
    i.invoice_amount_usd
        - COALESCE(p.collected_cash_usd, 0) AS outstanding_balance_usd
FROM invoices AS i
JOIN subscriptions AS s
    ON i.subscription_id = s.subscription_id
JOIN accounts AS a
    ON s.account_id = a.account_id
LEFT JOIN payments_by_invoice AS p
    ON i.invoice_id = p.invoice_id
ORDER BY i.invoice_id;