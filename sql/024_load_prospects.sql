BEGIN;

CREATE TEMP TABLE prospects_import (
    LIKE public.prospects INCLUDING ALL
) ON COMMIT DROP;

-- Keep this entire \copy command on one line.
\copy prospects_import (prospect_id, acquisition_channel, created_at, trial_started_at, account_id) FROM 'data/generated/prospects.csv' WITH (FORMAT csv, HEADER true)

INSERT INTO public.prospects (
    prospect_id,
    acquisition_channel,
    created_at,
    trial_started_at,
    account_id
)
SELECT
    prospect_id,
    acquisition_channel,
    created_at,
    trial_started_at,
    account_id
FROM prospects_import
WHERE TRUE
ON CONFLICT (prospect_id)
DO UPDATE SET
    acquisition_channel = EXCLUDED.acquisition_channel,
    created_at = EXCLUDED.created_at,
    trial_started_at = EXCLUDED.trial_started_at,
    account_id = EXCLUDED.account_id;

COMMIT;

-- 720 hours represents an exact 30-day observation window.
SELECT
    COUNT(*) AS prospects,

    COUNT(trial_started_at) AS trial_starts,

    COUNT(account_id) AS linked_accounts,

    COUNT(*) FILTER (
        WHERE created_at + INTERVAL '720 hours'
            <= TIMESTAMPTZ '2026-10-01 00:00:00+00'
    ) AS full_observation_window,

    COUNT(*) FILTER (
        WHERE created_at + INTERVAL '720 hours'
            > TIMESTAMPTZ '2026-10-01 00:00:00+00'
    ) AS still_pending

FROM public.prospects

WHERE created_at
    < TIMESTAMPTZ '2026-10-01 00:00:00+00';