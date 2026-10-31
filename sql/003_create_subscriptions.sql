CREATE TABLE subscriptions (
    subscription_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    plan_name TEXT NOT NULL,
    billing_amount_usd NUMERIC(12, 2) NOT NULL,
    billing_interval_months INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,

    CHECK (billing_amount_usd > 0),
    CHECK (billing_interval_months IN (1, 12)),
    CHECK (ended_at IS NULL OR ended_at > started_at)
);