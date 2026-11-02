CREATE TABLE public.prospects (
    prospect_id TEXT PRIMARY KEY,

    acquisition_channel TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,

    trial_started_at TIMESTAMPTZ,

    account_id TEXT UNIQUE
        REFERENCES public.accounts(account_id),

    CONSTRAINT prospects_channel_allowed
        CHECK (
            acquisition_channel IN (
                'Organic search',
                'Paid search',
                'Referral',
                'Partner',
                'Direct'
            )
        ),

    CONSTRAINT prospects_trial_after_creation
        CHECK (
            trial_started_at IS NULL
            OR trial_started_at >= created_at
        ),

    CONSTRAINT prospects_link_requires_trial
        CHECK (
            account_id IS NULL
            OR trial_started_at IS NOT NULL
        )
);