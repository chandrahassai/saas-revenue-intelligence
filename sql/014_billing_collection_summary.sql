SELECT
    COUNT(*) AS invoice_count,

    COALESCE(SUM(invoice_amount_usd), 0) AS total_billed_usd,

    COALESCE(SUM(collected_cash_usd), 0) AS total_collected_usd,

    COALESCE(
        SUM(outstanding_balance_usd),
        0
    ) AS total_outstanding_usd,

    COUNT(*) FILTER (
        WHERE outstanding_balance_usd > 0
    ) AS invoices_with_balance,

    ROUND(
        100.0 * SUM(collected_cash_usd)
        / NULLIF(SUM(invoice_amount_usd), 0),
        2
    ) AS collection_rate_pct

FROM invoice_payment_summary;