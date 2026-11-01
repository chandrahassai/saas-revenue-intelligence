WITH aged_invoices AS (
    SELECT
        b.*,
        GREATEST(
            (b.as_of AT TIME ZONE 'UTC')::DATE
            - (b.due_at AT TIME ZONE 'UTC')::DATE,
            0
        ) AS days_past_due
    FROM {{ ref('fct_invoice_balances') }} AS b
)

SELECT
    *,
    CASE
        WHEN days_past_due = 0 THEN 'Not overdue'
        WHEN days_past_due <= 30 THEN '1-30 days'
        WHEN days_past_due <= 60 THEN '31-60 days'
        WHEN days_past_due <= 90 THEN '61-90 days'
        ELSE '91+ days'
    END AS aging_bucket,
    (
        outstanding_balance_usd > 0
        AND days_past_due > 0
    ) AS is_overdue
FROM aged_invoices