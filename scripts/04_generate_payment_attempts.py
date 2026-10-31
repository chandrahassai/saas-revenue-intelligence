import csv
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd


SEED = 44
AS_OF = datetime(2026, 10, 1, tzinfo=timezone.utc)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"

PAYMENT_COLUMNS = [
    "payment_attempt_id",
    "invoice_id",
    "attempted_amount_usd",
    "status",
    "attempted_at",
    "completed_at",
    "failure_reason",
]


def add_attempt(
    records,
    invoice_id,
    amount,
    status,
    attempted_at,
    failure_reason=None,
):
    completed_at = attempted_at + timedelta(seconds=5)

    if completed_at >= AS_OF:
        return

    records.append({
        "payment_attempt_id": f"SYN_PAY{len(records) + 1:06d}",
        "invoice_id": invoice_id,
        "attempted_amount_usd": amount,
        "status": status,
        "attempted_at": attempted_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "failure_reason": failure_reason,
    })


def generate_payment_attempts(invoices):
    rng = random.Random(SEED)
    records = []

    for invoice in invoices:
        scenario = rng.choices(
            ["paid", "retry", "failed", "unattempted", "partial"],
            weights=[70, 15, 7, 5, 3],
            k=1,
        )[0]

        if scenario == "unattempted":
            continue

        invoice_id = invoice["invoice_id"]
        amount = Decimal(invoice["invoice_amount_usd"])
        issued_at = datetime.fromisoformat(invoice["issued_at"])

        initial_attempt_at = issued_at + timedelta(
            days=rng.randint(0, 10),
            hours=rng.randint(0, 6),
        )

        if scenario == "paid":
            add_attempt(
                records=records,
                invoice_id=invoice_id,
                amount=amount,
                status="succeeded",
                attempted_at=initial_attempt_at,
            )

        elif scenario == "partial":
            partial_amount = (
                amount * Decimal("0.40")
            ).quantize(Decimal("0.01"))

            add_attempt(
                records=records,
                invoice_id=invoice_id,
                amount=partial_amount,
                status="succeeded",
                attempted_at=initial_attempt_at,
            )

        else:
            add_attempt(
                records=records,
                invoice_id=invoice_id,
                amount=amount,
                status="failed",
                attempted_at=initial_attempt_at,
                failure_reason="card_declined",
            )

            if scenario == "retry":
                retry_at = initial_attempt_at + timedelta(
                    days=rng.randint(2, 7)
                )

                add_attempt(
                    records=records,
                    invoice_id=invoice_id,
                    amount=amount,
                    status="succeeded",
                    attempted_at=retry_at,
                )

    return pd.DataFrame(records, columns=PAYMENT_COLUMNS)


def main():
    source_path = OUTPUT_DIR / "invoices.csv"

    with source_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as source_file:
        invoices = list(csv.DictReader(source_file))

    attempts = generate_payment_attempts(invoices)

    output_path = OUTPUT_DIR / "payment_attempts.csv"
    attempts.to_csv(output_path, index=False)

    successful_attempts = attempts.loc[
        attempts["status"] == "succeeded"
    ]

    failed_attempts = attempts.loc[
        attempts["status"] == "failed"
    ]

    collected_cash = successful_attempts[
        "attempted_amount_usd"
    ].sum()

    print(attempts.head().to_string(index=False))
    print(f"\nPayment attempts generated: {len(attempts)}")
    print(f"Successful attempts: {len(successful_attempts)}")
    print(f"Failed attempts: {len(failed_attempts)}")
    print(f"Collected cash: ${collected_cash:,.2f}")
    print(f"CSV saved to: {output_path}")


if __name__ == "__main__":
    main()