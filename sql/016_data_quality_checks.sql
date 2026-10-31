WITH checks AS (
    SELECT
        'subscriptions_before_signup' AS check_name,
        COUNT(*) AS failing_rows
    FROM subscriptions AS s
    JOIN accounts AS a
        ON s.account_id = a.account_id
    WHERE s.started_at < a.signed_up_at

    UNION ALL

    SELECT
        'invoices_before_subscription_start',
        COUNT(*)
    FROM invoices AS i
    JOIN subscriptions AS s
        ON i.subscription_id = s.subscription_id
    WHERE i.issued_at < s.started_at

    UNION ALL

    SELECT
        'invoice_service_outside_subscription',
        COUNT(*)
    FROM invoices AS i
    JOIN subscriptions AS s
        ON i.subscription_id = s.subscription_id
    WHERE i.service_period_start < s.started_at
       OR (
           s.ended_at IS NOT NULL
           AND i.service_period_end > s.ended_at
       )

    UNION ALL

    SELECT
        'payment_attempts_before_invoice',
        COUNT(*)
    FROM payment_attempts AS p
    JOIN invoices AS i
        ON p.invoice_id = i.invoice_id
    WHERE p.attempted_at < i.issued_at

    UNION ALL

    SELECT
        'successful_attempts_with_failure_reason',
        COUNT(*)
    FROM payment_attempts
    WHERE status = 'succeeded'
      AND failure_reason IS NOT NULL

    UNION ALL

    SELECT
        'overcollected_invoices',
        COUNT(*)
    FROM invoice_payment_summary
    WHERE outstanding_balance_usd < 0
)

SELECT
    check_name,
    failing_rows,
    CASE
        WHEN failing_rows = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM checks
ORDER BY check_name;