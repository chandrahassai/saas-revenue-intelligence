"""Generate synthetic prospects linked to existing synthetic accounts.

Prospect creation and trial events are simulated for demonstration.
Subscription and payment milestones are derived separately from the
existing billing records.
"""

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


SEED = 45
EXPECTED_ACCOUNT_COUNT = 250
ADDITIONAL_PROSPECT_COUNT = 750
ADDITIONAL_TRIAL_COUNT = 350
CONVERSION_WINDOW_DAYS = 30

AS_OF = datetime(2026, 10, 1, tzinfo=timezone.utc)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"

CHANNELS = [
    "Organic search",
    "Paid search",
    "Referral",
    "Partner",
    "Direct",
]

FIELDS = [
    "prospect_id",
    "acquisition_channel",
    "created_at",
    "trial_started_at",
    "account_id",
]


def load_accounts():
    path = OUTPUT_DIR / "accounts.csv"

    if not path.is_file():
        raise FileNotFoundError(
            f"Existing account CSV not found: {path}"
        )

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)

        required = {"account_id", "signed_up_at"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                "accounts.csv requires account_id and signed_up_at."
            )

        accounts = list(reader)

    if len(accounts) != EXPECTED_ACCOUNT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ACCOUNT_COUNT} synthetic accounts, "
            f"found {len(accounts)}."
        )

    account_ids = [row["account_id"] for row in accounts]

    if len(set(account_ids)) != len(account_ids):
        raise ValueError("Duplicate account IDs found.")

    for account in accounts:
        if not account["account_id"].startswith("SYN_ACC"):
            raise ValueError("Expected synthetic account IDs only.")

        signup = datetime.fromisoformat(account["signed_up_at"])

        if signup.utcoffset() is None:
            raise ValueError("Signup timestamps must include a timezone.")

        if signup >= AS_OF:
            raise ValueError("Account signup must precede the cutoff.")

    return accounts


def generate_prospects(accounts):
    rng = random.Random(SEED)
    records = []

    def add_record(created_at, trial_started_at, account_id=None):
        records.append({
            "prospect_id": f"SYN_PRO{len(records) + 1:04d}",
            "acquisition_channel": rng.choice(CHANNELS),
            "created_at": created_at.isoformat(),
            "trial_started_at": (
                trial_started_at.isoformat()
                if trial_started_at is not None
                else None
            ),
            "account_id": account_id,
        })

    # Simulate earlier prospect activity for existing accounts.
    # Their trial starts at the recorded account signup timestamp.
    for account in sorted(
        accounts,
        key=lambda row: row["account_id"],
    ):
        signup = datetime.fromisoformat(
            account["signed_up_at"]
        ).astimezone(timezone.utc)

        created_at = signup - timedelta(
            days=rng.randint(1, 7)
        )

        add_record(
            created_at,
            signup,
            account["account_id"],
        )

    trial_numbers = set(
        rng.sample(
            range(ADDITIONAL_PROSPECT_COUNT),
            ADDITIONAL_TRIAL_COUNT,
        )
    )

    created_start = datetime(
        2025, 1, 1, tzinfo=timezone.utc
    )

    # Leave enough time for all generated trial events to occur
    # before the cutoff. Some prospects still have fewer than
    # 30 days of observation and will be reported separately.
    created_end = AS_OF - timedelta(days=15)
    span_seconds = int(
        (created_end - created_start).total_seconds()
    )

    for number in range(ADDITIONAL_PROSPECT_COUNT):
        created_at = created_start + timedelta(
            seconds=rng.randrange(span_seconds)
        )

        trial_started_at = None

        if number in trial_numbers:
            trial_started_at = created_at + timedelta(
                days=rng.randint(1, 14),
                hours=rng.randrange(24),
            )

        add_record(created_at, trial_started_at)

    return records


def main():
    accounts = load_accounts()
    prospects = generate_prospects(accounts)

    output_path = OUTPUT_DIR / "prospects.csv"

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=FIELDS,
        )
        writer.writeheader()
        writer.writerows(prospects)

    mature_count = sum(
        datetime.fromisoformat(row["created_at"])
        + timedelta(days=CONVERSION_WINDOW_DAYS)
        <= AS_OF
        for row in prospects
    )

    print(f"Prospects generated: {len(prospects)}")
    print(
        "Trial starts:",
        sum(row["trial_started_at"] is not None for row in prospects),
    )
    print(
        "Linked existing accounts:",
        sum(row["account_id"] is not None for row in prospects),
    )
    print(f"Full 30-day observation window: {mature_count}")
    print(
        "Still within observation window:",
        len(prospects) - mature_count,
    )
    print(f"Reporting cutoff: {AS_OF.isoformat()}")
    print(f"CSV saved to: {output_path}")


if __name__ == "__main__":
    main()