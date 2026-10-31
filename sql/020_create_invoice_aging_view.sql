CREATE OR REPLACE VIEW invoice_aging_snapshot AS
WITH report_settings AS (
    SELECT TIMESTAMPTZ '2026-10-01 00:00:00+00' AS as_of
),
collected_cash AS (
    SELECT
        p.invoice_id,
        SUM(p.attempted_amount_usd) AS collected_cash_usd
    FROM payment_attempts AS p
    CROSS JOIN report_settings AS r
    WHERE p.status = 'succeeded'
      AND p.completed_at < r.as_of
    GROUP BY p.invoice_id
),
balances AS (
    SELECT
        r.as_of,
        i.invoice_id,
        s.account_id,
        a.account_name,
        i.issued_at,
        i.due_at,
        i.invoice_amount_usd,
        COALESCE(c.collected_cash_usd, 0) AS collected_cash_usd,
        i.invoice_amount_usd
            - COALESCE(c.collected_cash_usd, 0)
            AS outstanding_balance_usd,
        GREATEST(
            (r.as_of AT TIME ZONE 'UTC')::date
                - (i.due_at AT TIME ZONE 'UTC')::date,
            0
        ) AS days_past_due
    FROM invoices AS i
    JOIN subscriptions AS s
        ON i.subscription_id = s.subscription_id
    JOIN accounts AS a
        ON s.account_id = a.account_id
    LEFT JOIN collected_cash AS c
        ON i.invoice_id = c.invoice_id
    CROSS JOIN report_settings AS r
    WHERE i.issued_at < r.as_of
)
SELECT
    balances.*,
    CASE
        WHEN days_past_due = 0 THEN 'Not overdue'
        WHEN days_past_due <= 30 THEN '1-30 days'
        WHEN days_past_due <= 60 THEN '31-60 days'
        WHEN days_past_due <= 90 THEN '61-90 days'
        ELSE '91+ days'
    END AS aging_bucket
FROM balances;

-- Check the historical invoice and payment totals.
SELECT
    COUNT(*) AS invoice_count,
    SUM(invoice_amount_usd) AS total_billed_usd,
    SUM(collected_cash_usd) AS total_collected_usd,
    SUM(outstanding_balance_usd) AS total_outstanding_usd,
    COUNT(*) FILTER (
        WHERE outstanding_balance_usd > 0
    ) AS invoices_with_balance
FROM invoice_aging_snapshot;

-- Group invoices with remaining balances by overdue age.
SELECT
    aging_bucket,
    COUNT(*) AS unpaid_invoice_count,
    SUM(outstanding_balance_usd) AS outstanding_balance_usd
FROM invoice_aging_snapshot
WHERE outstanding_balance_usd > 0
GROUP BY aging_bucket
ORDER BY CASE aging_bucket
    WHEN 'Not overdue' THEN 1
    WHEN '1-30 days' THEN 2
    WHEN '31-60 days' THEN 3
    WHEN '61-90 days' THEN 4
    ELSE 5
END;