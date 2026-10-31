import pandas as pd
import psycopg


def main():
    query = """
        SELECT
            invoice_id,
            account_name,
            invoice_amount_usd,
            collected_cash_usd,
            outstanding_balance_usd
        FROM invoice_payment_summary
        ORDER BY invoice_id;
    """

    with psycopg.connect(
        host="localhost",
        port=5432,
        dbname="saas_analytics",
        connect_timeout=5,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()
            columns = [
                column.name
                for column in cursor.description
            ]

    invoice_summary = pd.DataFrame.from_records(
        rows,
        columns=columns,
    )

    print(invoice_summary.to_string(index=False))
    print(f"\nRows loaded: {len(invoice_summary)}")


if __name__ == "__main__":
    main()