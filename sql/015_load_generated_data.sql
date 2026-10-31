BEGIN;

\copy accounts (account_id, account_name, industry, country_code, signed_up_at) FROM 'data/generated/accounts.csv' WITH (FORMAT csv, HEADER true)

\copy subscriptions (subscription_id, account_id, plan_name, billing_amount_usd, billing_interval_months, started_at, ended_at) FROM 'data/generated/subscriptions.csv' WITH (FORMAT csv, HEADER true)

\copy invoices (invoice_id, subscription_id, invoice_amount_usd, issued_at, due_at, service_period_start, service_period_end) FROM 'data/generated/invoices.csv' WITH (FORMAT csv, HEADER true)

\copy payment_attempts (payment_attempt_id, invoice_id, attempted_amount_usd, status, attempted_at, completed_at, failure_reason) FROM 'data/generated/payment_attempts.csv' WITH (FORMAT csv, HEADER true)

SELECT 'accounts' AS table_name, COUNT(*) AS row_count
FROM accounts

UNION ALL

SELECT 'subscriptions', COUNT(*)
FROM subscriptions

UNION ALL

SELECT 'invoices', COUNT(*)
FROM invoices

UNION ALL

SELECT 'payment_attempts', COUNT(*)
FROM payment_attempts

ORDER BY table_name;

COMMIT;