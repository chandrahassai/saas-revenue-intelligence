# SaaS Revenue Intelligence & Customer Retention Analytics

A SQL, Python, and dbt analytics project that examines recurring revenue,
subscription churn, cohort retention, unpaid invoices, and collection
review priorities using synthetic SaaS billing data.

## Current implementation

- PostgreSQL tables for accounts, subscriptions, invoices, and payment attempts.
- Python scripts that generate reproducible synthetic datasets.
- SQL views for MRR snapshots, MRR movements, plan-level churn,
  invoice aging, account balances, and overdue payment diagnostics.
- A Jupyter notebook containing charts, analysis, and documented findings.
- Twelve dbt views with 100 passing data tests covering staging,
  collections, overdue payment diagnostics, monthly MRR reconciliation,
  plan-level subscription churn, and cohort retention.
- Locally generated dbt documentation with model descriptions,
  column metadata, SQL, test definitions, and a dependency graph.

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

MRR, churn, and cohort retention analysis include only generated
subscriptions whose IDs begin with `SYN_`. Collections analysis includes
generated records and the two teaching examples.

## Selected findings

At the October 1, 2026 UTC reporting cutoff:

- Generated subscriptions contributed USD 56,400 in MRR across
  216 active accounts.
- All 21 monthly MRR movement periods reconciled.
- Pooled monthly subscription churn was 1.78% for Growth,
  1.61% for Starter, and 1.08% for Enterprise.
- The January 2025 subscription cohort retained five of its original
  eight subscriptions at month 21, a retention rate of 62.50%.

Billing and collection results include:

- Total billed: USD 685,400.
- Collected cash: USD 587,480.
- Outstanding balance: USD 97,920 across 327 unpaid invoices.
- Accounts with an outstanding balance: 154.
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

These categories describe recorded payment activity. They do not establish
the cause of nonpayment or predict recoverable cash.

## Project organization

- `sql/`: numbered schema, loading, validation, and analysis scripts.
- `scripts/`: Python database access and synthetic data generators.
- `notebooks/01_revenue_analysis.ipynb`: analysis and visualizations.
- `models/`: dbt staging and analytical models with YAML documentation
  and data tests.
- `tests/`: SQL checks for coverage, balance rules, reconciliation,
  plan-level churn rules, and cohort retention rules.
- `dbt_project.yml`: dbt project configuration.
- `profiles.yml`: PostgreSQL connection configuration using environment
  variables.
- `requirements.txt`: analysis environment dependencies.
- `requirements-dbt.txt`: dbt environment dependencies.
- `data/generated/`: locally generated CSV files, excluded from Git.

## Running the analysis

The notebook expects a populated local PostgreSQL database named
`saas_analytics` on `localhost:5432`, with the original SQL analytical
views already created.

Use the project's `saas-analytics` Python environment and open
`notebooks/01_revenue_analysis.ipynb` in Jupyter.

The notebook has been rerun successfully from a restarted kernel.
The dbt models are built separately in the `analytics` schema.

The notebook includes a cohort retention heatmap and interpretation
using `analytics.fct_monthly_cohort_retention`. Build the dbt models
before running that section.

## Verified database rebuild

The database was rebuilt successfully in a separate database named
`saas_analytics_rebuild` using regenerated CSV files and the saved SQL scripts.

### Prerequisites

- A running local PostgreSQL server.
- `psql` and `createdb` available on PATH.
- Python 3.12 with the dependencies from `requirements.txt` installed.

On macOS with Postgres.app, the command-line tools can be added
to the current Terminal session with:

```bash
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"
```

Run the following commands from the project root.

### Generate the CSV files

```bash
conda activate saas-analytics
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
the exact database name above and an empty `public` schema. It stops
at the first SQL error and does not clear an existing populated database.

### Verified results

| Check | Result |
|---|---:|
| Accounts | 252 |
| Subscriptions | 252 |
| Invoices | 1,995 |
| Payment attempts | 2,145 |
| SQL data-quality checks passed | 6 of 6 |
| Total billed (USD) | 685,400 |
| Total collected (USD) | 587,480 |
| Total outstanding (USD) | 97,920 |
| MRR movement periods | 21 |
| MRR reconciliation mismatches | 0 |

This procedure verifies the original SQL database build.
The existing analysis notebook connects to `saas_analytics`;
it does not automatically switch to `saas_analytics_rebuild`.

## dbt staging layer

Four staging views are built in the PostgreSQL `analytics` schema:

- `stg_accounts`
- `stg_subscriptions`
- `stg_invoices`
- `stg_payment_attempts`

The staging layer preserves the source records, including synthetic data
and teaching examples. It has 29 passing data tests covering unique IDs,
required fields, accepted values, and relationships between tables.

## dbt analytical models

The four staging views feed eight analytical views:

| Model | Purpose |
|---|---|
| `fct_invoice_balances` | Invoice balances at the reporting cutoff |
| `fct_invoice_aging` | UTC calendar-day aging and overdue flags |
| `mart_account_collections` | Unpaid and overdue balances by account |
| `fct_overdue_payment_diagnostics` | Completed payment activity behind overdue invoices |
| `fct_monthly_mrr_snapshot` | Active generated accounts, subscriptions, and monthly MRR |
| `fct_monthly_mrr_movements` | New and churned MRR reconciled to closing MRR |
| `fct_monthly_plan_churn` | Monthly churn among opening subscriptions, grouped by plan |
| `fct_monthly_cohort_retention` | Subscription retention by start-month cohort and monthly checkpoint |

Collections models include generated records and teaching examples.
MRR, churn, and cohort retention models include only generated subscriptions
whose IDs begin with `SYN_`.

The default reporting cutoff for collections and cohort retention is
October 1, 2026 at 00:00 UTC.

The MRR snapshot calendar spans January 1, 2025 through October 1, 2026.
Cohort retention uses subsequent checkpoints from that calendar,
limited to the reporting cutoff.

### Running dbt

Development uses the separate `saas-dbt` conda environment.
Package versions are recorded in `requirements-dbt.txt`.

The project profile reads `DBT_USER` from the environment and defaults
to the `saas_analytics` database. Set `DBT_USER` to your local PostgreSQL role.
The development machine uses the role shown below.

```bash
conda activate saas-dbt
export DBT_USER="chandrahassai"
DBT_ENGINE_MANAGE_STATE=0 dbt build --profiles-dir .
```

The environment prefix disables dbt State for this local build.

Local builds use one thread after concurrent view replacement encountered
a PostgreSQL deadlock.

### Verified dbt results

The full build successfully created all twelve views and passed
all 100 data tests.

dbt reported `PASS=112`, `ERROR=0`, and `SKIP=0`.

The 29 staging tests are included in the 100-test total.
The six original SQL data-quality checks are separate.

| Check | Verified result |
|---|---:|
| Monthly MRR snapshots | 22 |
| Latest active generated accounts | 216 |
| Latest MRR (USD) | 56,400 |
| MRR movement periods | 21 |
| MRR reconciliation mismatches | 0 |
| Plan-period churn rows | 63 |
| Churn reporting periods | 21 |
| Subscription plans | 3 |
| Subscription start-month cohorts | 21 |
| Cohort checkpoint rows | 231 |
| Cohort month numbers | 1–21 |

Account collections reconcile against invoice-level counts and balances.
Overdue diagnostics reconcile invoice IDs, reporting cutoffs, and balances
against invoice aging.

Monthly MRR movements must reconcile to closing MRR with zero difference
in every period.

Plan-level churn tests check plan-period uniqueness, valid reporting
periods, valid counts, and valid percentages.

Cohort retention tests check cohort-checkpoint uniqueness, valid
checkpoint dates, valid counts, percentage calculations, constant
cohort sizes, and non-increasing retained subscription counts.

### Cohort retention results

Cohorts are defined by the UTC calendar month in which subscriptions started.

Month 1 is the first monthly checkpoint after the cohort's start month.
For example, the January 2025 cohort is first observed on February 1, 2025.
These are calendar-month checkpoints, not exact subscription anniversaries.

A subscription is retained when it has started by the checkpoint and
has no end date, or its end date is after the checkpoint.
Retention measures subscription activity regardless of payment status.

No artificial month-0 baseline is added. Future observations for younger
cohorts are omitted.

The January 2025 cohort produced:

| Month number | Checkpoint | Original subscriptions | Retained subscriptions | Retention |
|---|---|---:|---:|---:|
| 1 | 2025-02-01 | 8 | 8 | 100.00% |
| 6 | 2025-07-01 | 8 | 6 | 75.00% |
| 12 | 2026-01-01 | 8 | 6 | 75.00% |
| 21 | 2026-10-01 | 8 | 5 | 62.50% |

At October 1, 2026, the cohorts contained 250 original subscriptions
and 216 retained subscriptions, or 86.40%.

That combined percentage includes cohorts of different ages.
It is not a fixed-duration retention rate such as 12-month retention.
Comparisons between cohorts should use the same month number.

### dbt documentation

With the dbt environment active and `DBT_USER` set, generate the
documentation and start its local server:

```bash
DBT_ENGINE_MANAGE_STATE=0 dbt docs generate --profiles-dir .
DBT_ENGINE_MANAGE_STATE=0 dbt docs serve --profiles-dir . --port 8080 --no-browser
```

Open `http://localhost:8080` in your browser.

The documentation includes model descriptions, column metadata,
test definitions, source and compiled SQL, and a dependency graph.

Keep the serving Terminal running while viewing the documentation.
Press Control + C in that Terminal to stop the server.

Generated documentation is stored in the ignored `target/` directory.
Regenerate it after changing model SQL or YAML documentation.

## Metric definitions and limitations

MRR normalizes subscription prices to monthly amounts and is separate
from collected cash.

MRR snapshots include subscriptions started at or before the reporting
instant and not ended at that instant.

Monthly plan churn uses subscriptions active at the opening snapshot
as its denominator. The percentage is null when the opening count is zero.

Pooled monthly churn divides total churn events by total opening
subscription counts across periods. It is not an average of monthly
percentages or cumulative customer churn.

Cohort retention measures retained subscriptions divided by the original
subscription count in each start-month cohort. The current generated
dataset has one subscription per account. The model does not measure
product usage retention or revenue retention.

Historical invoice balances include only invoices issued and successful
payments completed before the reporting cutoff. Aging uses UTC calendar dates.

The data is synthetic. Findings demonstrate analytical methods rather
than measured business impact. Outstanding balances are not confirmed
losses or guaranteed recoveries.

The subscription model uses fixed prices and covers starts and churn.
Generated signup dates end before September 1, 2026, limiting interpretation
of acquisition activity in the final reporting interval.

## Future work

- Conversion-funnel analysis with suitable event data.
- Dashboarding.
- Workflow orchestration.
- Automated CI checks.