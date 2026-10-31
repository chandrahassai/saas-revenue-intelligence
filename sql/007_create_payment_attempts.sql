CREATE TABLE payment_attempts (
    payment_attempt_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
    attempted_amount_usd NUMERIC(12, 2) NOT NULL,
    status TEXT NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,
    failure_reason TEXT,

    CHECK (attempted_amount_usd > 0),
    CHECK (status IN ('succeeded', 'failed')),
    CHECK (completed_at >= attempted_at)
);