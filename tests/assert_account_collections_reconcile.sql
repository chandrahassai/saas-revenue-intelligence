WITH invoice_totals AS (
    SELECT
        as_of,
        COUNT(*) AS unpaid_invoice_count,
        COUNT(*) FILTER (
            WHERE is_overdue
        ) AS overdue_invoice_count,
        SUM(outstanding_balance_usd) AS total_outstanding_usd,
        COALESCE(
            SUM(outstanding_balance_usd) FILTER (
                WHERE is_overdue
            ),
            0::NUMERIC
        ) AS overdue_balance_usd,
        COALESCE(
            SUM(outstanding_balance_usd) FILTER (
                WHERE days_past_due >= 91
            ),
            0::NUMERIC
        ) AS balance_91_plus_usd
    FROM {{ ref('fct_invoice_aging') }}
    WHERE outstanding_balance_usd > 0
    GROUP BY as_of
),

account_totals AS (
    SELECT
        as_of,
        SUM(unpaid_invoice_count) AS unpaid_invoice_count,
        SUM(overdue_invoice_count) AS overdue_invoice_count,
        SUM(total_outstanding_usd) AS total_outstanding_usd,
        SUM(overdue_balance_usd) AS overdue_balance_usd,
        SUM(balance_91_plus_usd) AS balance_91_plus_usd
    FROM {{ ref('mart_account_collections') }}
    GROUP BY as_of
)

SELECT
    COALESCE(i.as_of, a.as_of) AS reporting_cutoff
FROM invoice_totals AS i
FULL OUTER JOIN account_totals AS a
    ON i.as_of = a.as_of
WHERE i.as_of IS NULL
   OR a.as_of IS NULL
   OR i.unpaid_invoice_count
        IS DISTINCT FROM a.unpaid_invoice_count
   OR i.overdue_invoice_count
        IS DISTINCT FROM a.overdue_invoice_count
   OR i.total_outstanding_usd
        IS DISTINCT FROM a.total_outstanding_usd
   OR i.overdue_balance_usd
        IS DISTINCT FROM a.overdue_balance_usd
   OR i.balance_91_plus_usd
        IS DISTINCT FROM a.balance_91_plus_usd