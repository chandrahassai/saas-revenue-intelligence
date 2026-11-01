SELECT
    invoice_id,
    invoice_amount_usd,
    collected_cash_usd,
    outstanding_balance_usd,
    issued_at,
    as_of
FROM {{ ref('fct_invoice_balances') }}
WHERE invoice_amount_usd <= 0
   OR collected_cash_usd < 0
   OR outstanding_balance_usd < 0
   OR issued_at >= as_of