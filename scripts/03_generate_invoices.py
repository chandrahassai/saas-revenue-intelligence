import csv
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd


AS_OF = datetime(2026, 10, 1, tzinfo=timezone.utc)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"

INVOICE_COLUMNS = [
    "invoice_id",
    "subscription_id",
    "invoice_amount_usd",
    "issued_at",
    "due_at",
    "service_period_start",
    "service_period_end",
]


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


def generate_invoices(subscriptions):
    records = []

    for subscription in subscriptions:
        subscription_id = subscription["subscription_id"]

        started_at = datetime.fromisoformat(
            subscription["started_at"]
        )

        ended_at = (
            datetime.fromisoformat(subscription["ended_at"])
            if subscription["ended_at"]
            else None
        )

        interval = int(subscription["billing_interval_months"])
        amount = Decimal(subscription["billing_amount_usd"])

        if interval not in (1, 12) or amount <= 0:
            raise ValueError(
                f"Invalid billing terms for {subscription_id}"
            )

        cycle = 0

        while True:
            period_start = add_months(
                started_at,
                cycle * interval,
            )

            if period_start >= AS_OF:
                break

            if ended_at is not None and period_start >= ended_at:
                break

            period_end = add_months(
                started_at,
                (cycle + 1) * interval,
            )

            if ended_at is not None and period_end > ended_at:
                raise ValueError(
                    f"{subscription_id} needs partial-period billing, "
                    "which this generator does not model."
                )

            invoice_number = len(records) + 1

            records.append({
                "invoice_id": f"SYN_INV{invoice_number:06d}",
                "subscription_id": subscription_id,
                "invoice_amount_usd": amount,
                "issued_at": period_start.isoformat(),
                "due_at": (
                    period_start + timedelta(days=7)
                ).isoformat(),
                "service_period_start": period_start.isoformat(),
                "service_period_end": period_end.isoformat(),
            })

            cycle += 1

    return pd.DataFrame(records, columns=INVOICE_COLUMNS)


def main():
    source_path = OUTPUT_DIR / "subscriptions.csv"

    with source_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as source_file:
        subscriptions = list(csv.DictReader(source_file))

    invoices = generate_invoices(subscriptions)

    output_path = OUTPUT_DIR / "invoices.csv"
    invoices.to_csv(output_path, index=False)

    print(invoices.head().to_string(index=False))
    print(f"\nInvoices generated: {len(invoices)}")
    print(
        f"Total billed: "
        f"${invoices['invoice_amount_usd'].sum():,.2f}"
    )
    print(f"CSV saved to: {output_path}")


if __name__ == "__main__":
    main()