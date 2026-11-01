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
- Seven dbt views with 56 passing data tests, including invoice coverage,
  balance rules, and account-to-invoice reconciliation.
  - Ten dbt views with 84 passing data tests covering staging,
  collections, overdue payment diagnostics, and monthly MRR reconciliation.

## Technology

Python 3.12, PostgreSQL, SQL, pandas, psycopg, Matplotlib, Jupyter Notebook,
dbt Core 1.12.6, dbt-postgres 1.11.0, Git, and GitHub.

Analysis dependencies are recorded in `requirements.txt`.
dbt dependencies are recorded separately in `requirements-dbt.txt`.

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
- models/: dbt staging and analytical models with YAML documentation and tests.
- tests/: SQL checks for invoice coverage, balance rules, and reconciliation.
- dbt_project.yml: dbt project configuration.
- profiles.yml: PostgreSQL connection configuration using environment variables.
- requirements-dbt.txt: dbt environment dependencies.

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

The dbt staging layer and analytical models for invoice balances,
invoice aging, and account collections are implemented and tested.
Migration of the remaining SQL analytics into dbt, dashboarding,
and workflow orchestration remain future work.

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

## dbt staging layer

Four staging views are built in the PostgreSQL `analytics` schema:

- `stg_accounts`
- `stg_subscriptions`
- `stg_invoices`
- `stg_payment_attempts`

The staging layer preserves the source records, including synthetic data
and teaching examples. It has 29 passing data tests covering unique IDs,
required fields, accepted values, and relationships between tables.

Development uses the separate `saas-dbt` conda environment. Package
versions are recorded in `requirements-dbt.txt`.

The project profile reads `DBT_USER` from the environment and defaults
to the `saas_analytics` database.

Run from the project directory with `DBT_USER` set:

`DBT_ENGINE_MANAGE_STATE=0 dbt build --profiles-dir .`

The environment prefix disables dbt State for this local build.
The staging layer contains four views and 29 data tests.
The full build, including analytical models, is documented below.

## ## dbt analytical models

Four staging views feed six analytical views:

- `fct_invoice_balances`: invoice balances at the reporting cutoff.
- `fct_invoice_aging`: UTC calendar-day aging and overdue flags.
- `mart_account_collections`: unpaid and overdue balances by account.
- `fct_overdue_payment_diagnostics`: completed payment activity behind
  each overdue invoice.
- `fct_monthly_mrr_snapshot`: active accounts, subscriptions, and MRR
  at monthly UTC reporting instants.
- `fct_monthly_mrr_movements`: new and churned MRR between snapshots,
  reconciled to closing MRR.

Collections models include generated records and teaching examples.
MRR models include only generated subscriptions whose IDs begin with SYN_.

The default collections reporting cutoff is October 1, 2026 at 00:00 UTC.
MRR snapshots span January 1, 2025 through October 1, 2026.

The verified full build contains ten views and 84 passing data tests.

| Metric | Verified result |
|---|---:|
| Accounts with a balance | 154 |
| Unpaid invoices | 327 |
| Overdue invoices | 291 |
| Total outstanding (USD) | 97,920 |
| Overdue balance (USD) | 89,620 |
| Balance 91+ days past due (USD) | 64,700 |
| Monthly MRR snapshots | 22 |
| Latest active generated accounts | 216 |
| Latest MRR (USD) | 56,400 |
| MRR movement periods | 21 |
| MRR reconciliation mismatches | 0 |

Account collections reconcile against invoice-level counts and balances.
Overdue diagnostics reconcile invoice IDs, reporting cutoffs, and balances
against invoice aging. Monthly MRR movements must reconcile to closing MRR
with zero difference in every period.

Local builds use one thread after concurrent view replacement encountered
a PostgreSQL deadlock. The single-thread full build passed all ten models
and 84 tests.