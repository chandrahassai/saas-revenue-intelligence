BEGIN;

INSERT INTO accounts (
    account_id,
    account_name,
    industry,
    country_code,
    signed_up_at
)
VALUES (
    'ACC002',
    'Northstar Analytics',
    'Professional Services',
    'US',
    '2025-12-20 09:00:00+00'
);

INSERT INTO subscriptions (
    subscription_id,
    account_id,
    plan_name,
    billing_amount_usd,
    billing_interval_months,
    started_at,
    ended_at
)
VALUES (
    'SUB002',
    'ACC002',
    'Growth',
    200.00,
    1,
    '2026-01-01 09:00:00+00',
    NULL
);

INSERT INTO invoices (
    invoice_id,
    subscription_id,
    invoice_amount_usd,
    issued_at,
    due_at,
    service_period_start,
    service_period_end
)
VALUES (
    'INV002',
    'SUB002',
    200.00,
    '2026-01-01 09:00:00+00',
    '2026-01-08 09:00:00+00',
    '2026-01-01 09:00:00+00',
    '2026-02-01 09:00:00+00'
);

COMMIT;