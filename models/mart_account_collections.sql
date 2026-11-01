WITH balances_by_account AS (
    SELECT
        s.account_id,
        i.as_of,
        COUNT(*) AS unpaid_invoice_count,
        COUNT(*) FILTER (
            WHERE i.is_overdue
        ) AS overdue_invoice_count,
        SUM(
            i.outstanding_balance_usd
        ) AS total_outstanding_usd,
        COALESCE(
            SUM(i.outstanding_balance_usd) FILTER (
                WHERE i.is_overdue
            ),
            0::NUMERIC
        ) AS overdue_balance_usd,
        COALESCE(
            SUM(i.outstanding_balance_usd) FILTER (
                WHERE i.days_past_due >= 91
            ),
            0::NUMERIC
        ) AS balance_91_plus_usd,
        MAX(
            i.days_past_due
        ) AS oldest_unpaid_days_past_due
    FROM {{ ref('fct_invoice_aging') }} AS i
    INNER JOIN {{ ref('stg_subscriptions') }} AS s
        ON i.subscription_id = s.subscription_id
    WHERE i.outstanding_balance_usd > 0
    GROUP BY
        s.account_id,
        i.as_of
)

SELECT
    b.account_id,
    a.account_name,
    a.industry,
    a.country_code,
    b.as_of,
    b.unpaid_invoice_count,
    b.overdue_invoice_count,
    b.total_outstanding_usd,
    b.overdue_balance_usd,
    b.balance_91_plus_usd,
    b.oldest_unpaid_days_past_due
FROM balances_by_account AS b
INNER JOIN {{ ref('stg_accounts') }} AS a
    ON b.account_id = a.account_id