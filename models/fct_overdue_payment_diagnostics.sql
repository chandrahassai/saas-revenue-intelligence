WITH overdue_invoices AS (
    SELECT *
    FROM {{ ref('fct_invoice_aging') }}
    WHERE is_overdue
),

attempt_history AS (
    SELECT
        i.invoice_id,
        COUNT(
            p.payment_attempt_id
        ) AS completed_attempt_count,
        COUNT(p.payment_attempt_id) FILTER (
            WHERE p.status = 'failed'
        ) AS failed_attempt_count,
        COUNT(p.payment_attempt_id) FILTER (
            WHERE p.status = 'succeeded'
        ) AS successful_attempt_count,
        MAX(
            p.completed_at
        ) AS latest_completed_attempt_at
    FROM overdue_invoices AS i
    LEFT JOIN {{ ref('stg_payment_attempts') }} AS p
        ON i.invoice_id = p.invoice_id
       AND p.completed_at < i.as_of
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
FROM overdue_invoices AS i
INNER JOIN attempt_history AS h
    ON i.invoice_id = h.invoice_id