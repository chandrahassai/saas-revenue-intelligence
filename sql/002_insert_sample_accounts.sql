INSERT INTO accounts (
    account_id,
    account_name,
    industry,
    country_code,
    signed_up_at
)
VALUES (
    'ACC001',
    'Acme Technologies',
    'Technology',
    'US',
    '2025-12-18 09:00:00+00'
);

SELECT *
FROM accounts
WHERE account_id = 'ACC001';