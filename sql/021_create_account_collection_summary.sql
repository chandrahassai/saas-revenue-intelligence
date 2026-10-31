CREATE OR REPLACE VIEW account_collection_summary AS
SELECT
    as_of,
    account_id,
    account_name,
    COUNT(*) AS unpaid_invoice_count,
    COUNT(*) FILTER (
        WHERE days_past_due > 0
    ) AS overdue_invoice_count,
    SUM(outstanding_balance_usd) AS total_outstanding_usd,
    COALESCE(
        SUM(outstanding_balance_usd) FILTER (
            WHERE days_past_due > 0
        ),
        0
    ) AS overdue_balance_usd,
    COALESCE(
        SUM(outstanding_balance_usd) FILTER (
            WHERE days_past_due >= 91
        ),
        0
    ) AS balance_91_plus_usd,
    MAX(days_past_due) AS oldest_unpaid_days_past_due
FROM invoice_aging_snapshot
WHERE outstanding_balance_usd > 0
GROUP BY
    as_of,
    account_id,
    account_name;

-- Confirm that grouping by account preserves our invoice totals.
SELECT
    COUNT(*) AS accounts_with_balance,
    SUM(unpaid_invoice_count) AS unpaid_invoice_count,
    SUM(overdue_invoice_count) AS overdue_invoice_count,
    SUM(total_outstanding_usd) AS total_outstanding_usd,
    SUM(overdue_balance_usd) AS overdue_balance_usd,
    SUM(balance_91_plus_usd) AS balance_91_plus_usd
FROM account_collection_summary;

-- Review the ten accounts with the largest overdue balances.
SELECT
    account_id,
    account_name,
    overdue_invoice_count,
    overdue_balance_usd,
    balance_91_plus_usd,
    oldest_unpaid_days_past_due
FROM account_collection_summary
WHERE overdue_balance_usd > 0
ORDER BY
    overdue_balance_usd DESC,
    oldest_unpaid_days_past_due DESC,
    account_id
LIMIT 10;