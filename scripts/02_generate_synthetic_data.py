import random
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd


SEED = 42
ACCOUNT_COUNT = 250
AS_OF = datetime(2026, 10, 1, tzinfo=timezone.utc)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"


def generate_accounts():
    rng = random.Random(SEED)

    signup_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    signup_end = datetime(2026, 9, 1, tzinfo=timezone.utc)

    signup_span_seconds = int(
        (signup_end - signup_start).total_seconds()
    )

    industries = [
        "Technology",
        "Financial Services",
        "Retail",
        "Healthcare",
        "Logistics",
    ]

    countries = ["US", "CA", "GB", "DE"]
    country_weights = [60, 15, 15, 10]

    records = []

    for account_number in range(1, ACCOUNT_COUNT + 1):
        signed_up_at = signup_start + timedelta(
            seconds=rng.randrange(signup_span_seconds)
        )

        records.append({
            "account_id": f"SYN_ACC{account_number:04d}",
            "account_name": f"Synthetic Account {account_number:04d}",
            "industry": rng.choice(industries),
            "country_code": rng.choices(
                countries,
                weights=country_weights,
                k=1,
            )[0],
            "signed_up_at": signed_up_at.isoformat(),
        })

    return pd.DataFrame(records)


def add_months(timestamp, months):
    month_index = timestamp.year * 12 + timestamp.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1

    day = min(timestamp.day, monthrange(year, month)[1])

    return timestamp.replace(
        year=year,
        month=month,
        day=day,
    )


def generate_subscriptions(accounts):
    rng = random.Random(SEED + 1)

    plans = [
        ("Starter", Decimal("100.00")),
        ("Growth", Decimal("200.00")),
        ("Enterprise", Decimal("500.00")),
    ]

    records = []

    for number, account in enumerate(
        accounts.itertuples(index=False),
        start=1,
    ):
        signed_up_at = datetime.fromisoformat(
            account.signed_up_at
        )

        started_at = signed_up_at + timedelta(
            days=rng.randint(0, 14)
        )

        plan_name, monthly_price = rng.choice(plans)

        interval = rng.choices(
            [1, 12],
            weights=[80, 20],
            k=1,
        )[0]

        ended_at = None

        if rng.random() < 0.20:
            periods = rng.randint(
                1,
                12 if interval == 1 else 2,
            )

            candidate_end = add_months(
                started_at,
                periods * interval,
            )

            if candidate_end <= AS_OF:
                ended_at = candidate_end

        records.append({
            "subscription_id": f"SYN_SUB{number:04d}",
            "account_id": account.account_id,
            "plan_name": plan_name,
            "billing_amount_usd": monthly_price * interval,
            "billing_interval_months": interval,
            "started_at": started_at.isoformat(),
            "ended_at": (
                ended_at.isoformat()
                if ended_at is not None
                else None
            ),
        })

    return pd.DataFrame(records)


def main():
    accounts = generate_accounts()
    subscriptions = generate_subscriptions(accounts)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    accounts.to_csv(
        OUTPUT_DIR / "accounts.csv",
        index=False,
    )

    subscriptions.to_csv(
        OUTPUT_DIR / "subscriptions.csv",
        index=False,
    )

    print(subscriptions.head().to_string(index=False))
    print(f"\nAccounts generated: {len(accounts)}")
    print(f"Subscriptions generated: {len(subscriptions)}")
    print(
        "Subscriptions ended by cutoff:",
        subscriptions["ended_at"].notna().sum(),
    )
    print(f"CSV files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()