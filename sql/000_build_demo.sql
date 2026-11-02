\set ON_ERROR_STOP on
\pset pager off

-- Run from the project root after generating the CSV files.
-- This entry point builds a separate, empty verification database.

DO $$
BEGIN
    IF current_database() <> 'saas_analytics_rebuild' THEN
        RAISE EXCEPTION
            'Build requires database saas_analytics_rebuild; connected to %',
            current_database();
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_class AS c
        JOIN pg_namespace AS n
            ON c.relnamespace = n.oid
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
    ) THEN
        RAISE EXCEPTION
            'Build requires an empty public schema; existing objects found.';
    END IF;
END
$$;

-- Create tables and insert the original teaching examples.

\ir 001_create_accounts.sql
\ir 002_insert_sample_accounts.sql
\ir 003_create_subscriptions.sql
\ir 004_insert_sample_subscriptions.sql
\ir 005_create_invoices.sql
\ir 006_insert_sample_invoices.sql
\ir 007_create_payment_attempts.sql
\ir 008_insert_sample_payment_attempts.sql
\ir 011_insert_unpaid_customer.sql

-- Create the invoice summary and import generated records.

\ir 013_create_invoice_payment_summary_view.sql
\ir 015_load_generated_data.sql

-- Create and load the synthetic prospect source.

\ir 023_create_prospects.sql
\ir 024_load_prospects.sql

-- Check data quality and create analytical views.

\ir 016_data_quality_checks.sql
\ir 017_create_monthly_mrr_view.sql
\ir 018_create_monthly_mrr_movements.sql
\ir 019_create_monthly_plan_churn_view.sql
\ir 020_create_invoice_aging_view.sql
\ir 021_create_account_collection_summary.sql
\ir 022_create_overdue_payment_diagnostics.sql

-- Display final verification results.

SELECT current_database() AS rebuilt_database;

\ir 014_billing_collection_summary.sql

SELECT
    COUNT(*) AS periods_checked,
    COUNT(*) FILTER (
        WHERE reconciliation_difference_usd <> 0
    ) AS periods_with_mismatch
FROM monthly_mrr_movements;