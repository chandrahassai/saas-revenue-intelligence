CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    subscription_id TEXT NOT NULL
        REFERENCES subscriptions(subscription_id),
    invoice_amount_usd NUMERIC(12, 2) NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    service_period_start TIMESTAMPTZ NOT NULL,
    service_period_end TIMESTAMPTZ NOT NULL,

    CHECK (invoice_amount_usd > 0),
    CHECK (due_at >= issued_at),
    CHECK (service_period_end > service_period_start)
);