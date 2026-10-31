# SaaS Revenue Intelligence & Customer Retention Analytics

A SQL and Python analytics project that examines recurring revenue,
subscription churn, unpaid invoices, and collection review priorities
using synthetic SaaS billing data.

## Current implementation

- PostgreSQL tables for accounts, subscriptions, invoices, and payment attempts.
- Python scripts that generate reproducible synthetic datasets.
- SQL views for MRR snapshots, MRR movements, plan-level churn,
  invoice aging, account balances, and overdue payment diagnostics.
- A Jupyter notebook containing charts, analysis, and documented findings.

## Technology

Python 3.12, PostgreSQL, SQL, pandas, psycopg, Matplotlib, Jupyter Notebook,
and Git.

Direct Python package versions are recorded in requirements.txt.

## Dataset

The database contains 250 generated accounts and subscriptions,
plus two original teaching examples.

| Table | Records |
|---|---:|
| Accounts | 252 |
| Subscriptions | 252 |
| Invoices | 1,995 |
| Payment attempts | 2,145 |

Generated CSV files are excluded from Git. Their generation scripts
are included.

## Selected findings

At the October 1, 2026 UTC reporting cutoff:

- Generated subscriptions contributed USD 56,400 in MRR across
  216 active accounts.
- All 21 monthly MRR movement periods reconciled.
- Pooled monthly subscription churn was 1.78% for Growth,
  1.61% for Starter, and 1.08% for Enterprise.

Billing and collection results include the generated records and
the two original examples:

- Total billed: USD 685,400.
- Collected cash: USD 587,480.
- Outstanding balance: USD 97,920.
- Overdue balance: USD 89,620 across 291 invoices.
- Balances at least 91 days overdue: USD 64,700.
- The ten accounts with the largest overdue balances held USD 31,200,
  or 34.81% of overdue dollars.

Overdue balances were classified as:

| Recorded payment activity | Invoices | Overdue balance (USD) |
|---|---:|---:|
| Failed attempts only | 142 | 41,400 |
| No completed attempts | 88 | 34,900 |
| Partially paid | 61 | 13,320 |

## Project organization

- sql/: numbered schema, loading, validation, and analysis scripts.
- scripts/: Python database access and synthetic data generators.
- notebooks/01_revenue_analysis.ipynb: analysis and visualizations.
- requirements.txt: direct Python dependencies.
- data/generated/: locally generated CSV files, excluded from Git.

## Running the analysis

The notebook expects a populated local PostgreSQL database named
saas_analytics on localhost:5432, with the analytical views already created.

Use the project's Python environment and open
notebooks/01_revenue_analysis.ipynb in Jupyter. The notebook has been
rerun from a restarted kernel against the existing project database.

## Metric definitions and limitations

MRR normalizes subscription prices to monthly amounts and is separate
from collected cash.

Pooled monthly churn divides total churn events by total opening
subscription counts across periods. It is not cumulative customer churn.

Historical invoice balances include only invoices issued and successful
payments completed before the reporting cutoff. Aging uses UTC calendar dates.

The data is synthetic. Findings demonstrate analytical methods rather
than measured business impact. Outstanding balances are not confirmed
losses or guaranteed recoveries.

The subscription model uses fixed prices and covers starts and churn.
Generated signup dates end before September 1, 2026, limiting interpretation
of acquisition activity in the final reporting interval.

Dashboarding, dbt transformations, and workflow orchestration remain
future work.

## Verified database rebuild

The database was rebuilt successfully in a separate database named
saas_analytics_rebuild using regenerated CSV files and the saved SQL scripts.

### Prerequisites

- A running local PostgreSQL server.
- psql and createdb available on PATH.
- Python 3.12 with the dependencies from requirements.txt installed.

Run all commands below from the project root.

### Generate the CSV files

```bash
python scripts/02_generate_synthetic_data.py
python scripts/03_generate_invoices.py
python scripts/04_generate_payment_attempts.py
```

These regenerate the local CSV files using fixed seeds and an
October 1, 2026 UTC reporting cutoff.

### Build a fresh verification database

```bash
createdb -h localhost -p 5432 saas_analytics_rebuild
psql -X -h localhost -p 5432 -d saas_analytics_rebuild -P pager=off -v ON_ERROR_STOP=1 -f sql/000_build_demo.sql
```

Run the build after database creation succeeds. The build requires
the exact database name above and an empty public schema. It stops
at the first SQL error and does not clear an existing populated database.

### Verified results

| Check | Result |
|---|---:|
| Accounts | 252 |
| Subscriptions | 252 |
| Invoices | 1,995 |
| Payment attempts | 2,145 |
| Data-quality checks passed | 6 of 6 |
| Total billed (USD) | 685,400 |
| Total collected (USD) | 587,480 |
| Total outstanding (USD) | 97,920 |
| MRR movement periods | 21 |
| MRR reconciliation mismatches | 0 |

This procedure verifies the database build. The existing analysis notebook
connects to saas_analytics; it does not automatically switch to
saas_analytics_rebuild.