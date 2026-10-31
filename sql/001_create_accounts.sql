CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    industry TEXT,
    country_code TEXT,
    signed_up_at TIMESTAMPTZ NOT NULL
);