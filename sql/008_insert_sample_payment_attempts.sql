INSERT INTO payment_attempts (
    payment_attempt_id,
    invoice_id,
    attempted_amount_usd,
    status,
    attempted_at,
    completed_at,
    failure_reason
)
VALUES
(
    'PAY001',
    'INV001',
    1200.00,
    'failed',
    '2026-01-01 09:00:00+00',
    '2026-01-01 09:00:05+00',
    'card_declined'
),
(
    'PAY002',
    'INV001',
    1200.00,
    'succeeded',
    '2026-01-03 09:00:00+00',
    '2026-01-03 09:00:05+00',
    NULL
);

SELECT
    invoice_id,
    COUNT(*) AS attempt_count,
    SUM(attempted_amount_usd) AS total_attempted_usd,
    SUM(
        CASE
            WHEN status = 'succeeded'
                THEN attempted_amount_usd
            ELSE 0
        END
    ) AS collected_cash_usd
FROM payment_attempts
WHERE invoice_id = 'INV001'
GROUP BY invoice_id;