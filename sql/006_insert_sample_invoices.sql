INSERT INTO invoices (
    invoice_id,
    subscription_id,
    invoice_amount_usd,
    issued_at,
    due_at,
    service_period_start,
    service_period_end
)
VALUES (
    'INV001',
    'SUB001',
    1200.00,
    '2026-01-01 09:00:00+00',
    '2026-01-01 09:00:00+00',
    '2026-01-01 09:00:00+00',
    '2027-01-01 09:00:00+00'
);

SELECT
    i.invoice_id,
    i.subscription_id,
    i.invoice_amount_usd,
    ROUND(
        s.billing_amount_usd / s.billing_interval_months,
        2
    ) AS subscription_mrr_usd
FROM invoices AS i
JOIN subscriptions AS s
    ON i.subscription_id = s.subscription_id
WHERE i.invoice_id = 'INV001';