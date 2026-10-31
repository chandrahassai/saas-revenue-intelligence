CREATE OR REPLACE VIEW overdue_payment_diagnostics AS
WITH attempt_history AS (
    SELECT
        i.invoice_id,
        COUNT(p.payment_attempt_id) AS completed_attempt_count,
        COUNT(p.payment_attempt_id) FILTER (
            WHERE p.status = 'failed'
        ) AS failed_attempt_count,
        COUNT(p.payment_attempt_id) FILTER (
            WHERE p.status = 'succeeded'
        ) AS successful_attempt_count,
        MAX(p.completed_at) AS latest_completed_attempt_at
    FROM invoice_aging_snapshot AS i
    LEFT JOIN payment_attempts AS p
        ON i.invoice_id = p.invoice_id
        AND p.completed_at < i.as_of
    WHERE i.outstanding_balance_usd > 0
      AND i.days_past_due > 0
    GROUP BY i.invoice_id
)
SELECT
    i.*,
    h.completed_attempt_count,
    h.failed_attempt_count,
    h.successful_attempt_count,
    h.latest_completed_attempt_at,
    CASE
        WHEN h.completed_attempt_count = 0
            THEN 'No completed attempts'
        WHEN i.collected_cash_usd > 0
            THEN 'Partially paid'
        WHEN h.failed_attempt_count = h.completed_attempt_count
            THEN 'Failed attempts only'
        ELSE 'Review'
    END AS payment_activity_category
FROM invoice_aging_snapshot AS i
JOIN attempt_history AS h
    ON i.invoice_id = h.invoice_id
WHERE i.outstanding_balance_usd > 0
  AND i.days_past_due > 0;

-- Confirm that we preserved the overdue invoice population.
SELECT
    COUNT(*) AS overdue_invoice_count,
    COUNT(DISTINCT invoice_id) AS unique_invoice_count,
    SUM(outstanding_balance_usd) AS overdue_balance_usd
FROM overdue_payment_diagnostics;

-- Summarize overdue balances by recorded payment activity.
SELECT
    payment_activity_category,
    COUNT(*) AS overdue_invoice_count,
    SUM(outstanding_balance_usd) AS overdue_balance_usd,
    COALESCE(
        SUM(outstanding_balance_usd) FILTER (
            WHERE days_past_due >= 91
        ),
        0
    ) AS balance_91_plus_usd
FROM overdue_payment_diagnostics
GROUP BY payment_activity_category
ORDER BY
    overdue_balance_usd DESC,
    payment_activity_category;