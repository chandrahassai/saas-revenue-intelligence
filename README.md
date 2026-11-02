# SaaS Revenue Intelligence & Customer Retention Analytics

A SQL, Python, and dbt analytics project for recurring revenue, subscription
retention, invoice collections, and prospect conversion. It combines
reproducible synthetic data, tested PostgreSQL models, a four-page Streamlit
dashboard, local Airflow orchestration, and GitHub Actions checks.

The data is synthetic. Results demonstrate analytical and engineering methods;
they are not measured business outcomes.

## Current implementation

- Five source tables: accounts, subscriptions, invoices, payment attempts,
  and prospects.
- Fifteen dbt views: five staging views and ten analytical views.
- 127 dbt data tests and two dbt unit tests.
- Four dashboard pages: Revenue, Retention, Collections, and Funnel.
- Seven Streamlit AppTest integration checks.
- A Jupyter notebook with revenue, collections, churn, and cohort analysis.
- Local Airflow execution through Docker Compose, with three DAG validation tests.
- Separate GitHub Actions workflows for the data pipeline and Airflow validation.
- Generated dbt documentation with model descriptions, tests, SQL, and lineage.

The latest full local dbt build completed with `PASS=144`, `ERROR=0`, and
`SKIP=0`: 15 view builds, 127 data tests, and two unit tests. All seven
dashboard integration checks also passed locally.

## Technology

Python 3.12, PostgreSQL, SQL, pandas, psycopg, Matplotlib, Jupyter Notebook,
dbt Core 1.12.6, dbt-postgres 1.11.0, Streamlit 1.66.1, Plotly 7.1.0,
Apache Airflow 3.3.2, Docker Compose, Git, and GitHub Actions.

Dependencies are separated by purpose:

| File | Environment |
|---|---|
| `requirements.txt` | Data generation and notebook analysis |
| `requirements-dbt.txt` | dbt builds, tests, and documentation |
| `requirements-dashboard.txt` | Streamlit dashboard and integration checks |
| `orchestration/Dockerfile` | Airflow image with separate dbt and dashboard virtual environments |

## Dataset and reporting scope

The billing dataset contains 250 generated accounts and subscriptions plus
two original teaching examples. The prospect dataset adds simulated
acquisition and trial activity, including prospects who never subscribed.

| Source table | Records |
|---|---:|
| Accounts | 252 |
| Subscriptions | 252 |
| Invoices | 1,995 |
| Payment attempts | 2,145 |
| Prospects | 1,000 |

Generated CSV files are excluded from Git; their generation scripts are included.

The default reporting cutoff is **October 1, 2026 at 00:00 UTC**. Cutoff-based
dbt models use the `reporting_as_of` variable. Data generators use a fixed
cutoff, so changing the dbt variable does not generate additional source events.

- MRR, churn, and cohort retention include generated subscriptions whose IDs
  begin with `SYN_`.
- Collections include generated records and the two teaching examples.
- The funnel contains 1,000 synthetic prospects, including 250 links to existing
  generated accounts. Prospect creation, trial events, and acquisition channels
  are simulated. Subscription and payment milestones come from billing records.

## Selected results

At the default cutoff, generated subscriptions contributed **USD 56,400 in MRR**
across **216 active accounts**. All 21 monthly MRR movement periods reconciled
with zero difference.

Pooled monthly subscription churn was 1.78% for Growth, 1.61% for Starter,
and 1.08% for Enterprise. The January 2025 subscription cohort retained five
of its original eight subscriptions at month 21, or 62.50%.

### Billing and collections

| Measure | Result |
|---|---:|
| Total billed (USD) | 685,400 |
| Collected cash (USD) | 587,480 |
| Outstanding balance (USD) | 97,920 |
| Unpaid invoices | 327 |
| Accounts with an outstanding balance | 154 |
| Overdue balance (USD) | 89,620 |
| Overdue invoices | 291 |
| Balance at least 91 days overdue (USD) | 64,700 |

The ten accounts with the largest overdue balances held USD 31,200,
or 34.81% of overdue dollars.

| Recorded payment activity on overdue invoices | Invoices | Overdue balance (USD) |
|---|---:|---:|
| Failed attempts only | 142 | 41,400 |
| No completed attempts | 88 | 34,900 |
| Partially paid | 61 | 13,320 |

These categories describe recorded activity. They do not establish the cause
of nonpayment or predict recoverable cash.

### Prospect conversion

The source contains 600 trial starts. Sixteen prospects have not completed
their observation windows; ten of those prospects have started trials.
Completed-window conversion therefore uses the following population:

| Stage | Prospects |
|---|---:|
| Full 30-day observation window | 984 |
| Trial started within the window | 590 |
| Subscription started within the window | 250 |
| First successful payment within the window | 217 |

| Conversion measure | Result |
|---|---:|
| Prospect to trial | 59.96% |
| Trial to subscription | 42.37% |
| Subscription to payment | 86.80% |
| Prospect to payment | 22.05% |

Every stage uses the same eligible prospect population. Pending prospects
are reported separately. Channel comparisons use simulated assignments and
do not demonstrate real marketing effectiveness.

## Project organization

| Path | Purpose |
|---|---|
| `sql/` | Numbered schema, loading, validation, and analysis scripts |
| `scripts/` | Python database access and synthetic data generators |
| `notebooks/01_revenue_analysis.ipynb` | Analysis, charts, and findings |
| `models/` | dbt sources, staging and analytical models, documentation, and unit tests |
| `tests/` | SQL data tests for business rules, coverage, and reconciliation |
| `dashboard/app.py` | Revenue overview and dashboard entry point |
| `dashboard/pages/` | Retention, Collections, and Funnel pages |
| `dashboard/tests/` | Streamlit AppTest integration checks |
| `orchestration/` | Docker image, Compose configuration, Airflow DAG, profile, and tests |
| `.github/workflows/` | Data pipeline and Airflow validation workflows |
| `dbt_project.yml` | dbt project configuration |
| `profiles.yml` | Local PostgreSQL profile using environment variables |
| `data/generated/` | Generated CSV files, excluded from Git |

## Local prerequisites

The development setup uses macOS, Postgres.app, conda, and Docker Desktop
for Apple Silicon. Run commands from the repository root.

Use separate Python 3.12 environments for analysis, dbt, and the dashboard.
If the environments do not already exist, create them once:

```bash
conda create -n saas-analytics python=3.12
conda create -n saas-dbt python=3.12
conda create -n saas-dashboard python=3.12
```

Install the matching dependency files in those environments:

```bash
conda run -n saas-analytics python -m pip install -r requirements.txt
conda run -n saas-dbt python -m pip install -r requirements-dbt.txt
conda run -n saas-dashboard python -m pip install -r requirements-dashboard.txt
```

On macOS with Postgres.app, add its command-line tools to the current shell:

```bash
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"
```

## Rebuild a fresh verification database

Generate the CSV files in dependency order:

```bash
conda activate saas-analytics
python scripts/02_generate_synthetic_data.py
python scripts/03_generate_invoices.py
python scripts/04_generate_payment_attempts.py
python scripts/05_generate_prospects.py
```

Create a fresh database and run the SQL build:

```bash
createdb -h localhost -p 5432 saas_analytics_rebuild

psql -X -h localhost -p 5432 -d saas_analytics_rebuild \
  -P pager=off -v ON_ERROR_STOP=1 -f sql/000_build_demo.sql
```

Run the build after database creation succeeds. The SQL entry point requires
the exact database name `saas_analytics_rebuild` and an empty `public` schema.
It stops at the first SQL error and does not reset a populated database.

The build creates the teaching examples, imports billing records, creates
and loads prospects, runs the original SQL checks, and creates the original
SQL analytical views. It does not build the dbt `analytics` schema.

Build that schema separately. Set `DBT_USER` to your PostgreSQL role;
the development Mac uses the role shown here:

```bash
conda activate saas-dbt
export DBT_USER="chandrahassai"

DBT_ENGINE_MANAGE_STATE=0 \
DBT_DATABASE=saas_analytics_rebuild \
dbt build --profiles-dir .
```

For the existing populated development database, omit the database override:

```bash
DBT_ENGINE_MANAGE_STATE=0 dbt build --profiles-dir .
```

The local profile defaults to `saas_analytics` on `localhost:5432` and also
accepts `DBT_DATABASE` and `DBT_PASSWORD`. Builds use one thread following
a PostgreSQL deadlock encountered during concurrent view replacement.
The environment prefix disables dbt State; the current dbt version reports
a namespace deprecation notice for this setting.

`sql/023_create_prospects.sql` creates the prospect table once.
`sql/024_load_prospects.sql` loads through a temporary table and upserts
by prospect ID inside a transaction, allowing repeat prospect loads.

## dbt models and tests

The staging views are `stg_accounts`, `stg_subscriptions`, `stg_invoices`,
`stg_payment_attempts`, and `stg_prospects`. Their 36 data tests are included
in the 127-test project total.

| Analytical model | Purpose |
|---|---|
| `fct_invoice_balances` | Invoice balances at the reporting cutoff |
| `fct_invoice_aging` | UTC calendar-day aging and overdue flags |
| `mart_account_collections` | Unpaid and overdue balances by account |
| `fct_overdue_payment_diagnostics` | Completed payment activity on overdue invoices |
| `fct_monthly_mrr_snapshot` | Active generated accounts, subscriptions, and monthly MRR |
| `fct_monthly_mrr_movements` | New and churned MRR reconciled to closing MRR |
| `fct_monthly_plan_churn` | Monthly churn among opening subscriptions, grouped by plan |
| `fct_monthly_cohort_retention` | Subscription retention by start-month cohort and checkpoint |
| `fct_prospect_conversion` | Observed milestones and conversion-window flags per prospect |
| `mart_conversion_funnel` | Mature prospect stage counts and conversion rates by channel |

Data tests cover required fields, uniqueness, relationships, accepted values,
source coverage, balances, MRR reconciliation, churn, cohort retention,
funnel stage ordering, and valid counts and rates.

Two unit tests use controlled fixtures to check conversion-window boundaries,
observation cutoffs, failed payments, non-converters, pending prospect exclusion,
and zero denominators. The original six SQL data-quality checks are separate
from the dbt test count.

## Local dashboard

With PostgreSQL running and the dbt models built:

```bash
conda activate saas-dashboard

python -m streamlit run dashboard/app.py \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.headless true
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501) in Chrome and keep the
serving Terminal running. Press Control+C in that Terminal to stop it.

| Page | Features |
|---|---|
| Revenue (`app`) | Monthly snapshot selection, MRR, active accounts, new and churned MRR, net change, and trend charts |
| Retention | Cohort heatmap, original cohort sizes, pooled monthly churn by plan, and checkpoint data |
| Collections | Outstanding and overdue balances, aging, recorded payment activity, and accounts prioritized by overdue balance |
| Funnel | Channel filter, mature prospect stage counts, conversion rates, funnel chart, channel comparison, and stage transitions |

Pages use cached queries, a Refresh data button, and read-only database
connections. Defaults are `localhost:5432`, database `saas_analytics`, and
the operating-system username. Override them using `PGHOST`, `PGPORT`,
`PGDATABASE`, `PGUSER`, and `PGPASSWORD`.

To use the rebuilt verification database, prefix the launch command with
`PGDATABASE=saas_analytics_rebuild`.

Run all seven dashboard checks against the populated development database:

```bash
python -m unittest discover -s dashboard/tests -v
```

Or target the rebuilt verification database:

```bash
PGDATABASE=saas_analytics_rebuild \
python -m unittest discover -s dashboard/tests -v
```

Checks cover revenue snapshots and refresh behavior, first-snapshot handling,
retention and plan churn, collections and payment activity, top-ten balances,
overall funnel rates, and the Direct channel filter with refresh persistence.

## Notebook and dbt documentation

The notebook uses the `saas-analytics` environment and the populated local
`saas_analytics` database. It reads original SQL analytical views and uses
`analytics.fct_monthly_cohort_retention` for its cohort heatmap. Build dbt
before running that section. The notebook has been rerun from a restarted kernel;
notebook execution is not part of CI.

With the dbt environment active and `DBT_USER` set:

```bash
DBT_ENGINE_MANAGE_STATE=0 dbt docs generate --profiles-dir .
DBT_ENGINE_MANAGE_STATE=0 dbt docs serve --profiles-dir . --port 8080 --no-browser
```

Open [http://localhost:8080](http://localhost:8080). Keep the serving Terminal
running while viewing the documentation. Generated files are stored in the
ignored `target/` directory and should be regenerated after model changes.

## Local Airflow orchestration

The `saas_analytics_workflow` DAG runs three tasks in order:

1. Build dbt models and run their data and unit tests.
2. Run dashboard integration checks through unittest discovery.
3. Generate dbt documentation.

The schedule is 08:00 America/Los_Angeles, with catchup disabled and at most
one active run. Tasks require upstream success and can retry once after
a one-minute delay. Each task has a ten-minute execution timeout; a DAG run
has a thirty-minute timeout. New DAGs start paused.

Airflow runs in a Docker container using LocalExecutor and development
standalone mode. Its PostgreSQL 17 metadata database runs in another container.
Tasks reach the Mac's existing analytics database through `host.docker.internal`.
The Compose file currently uses PostgreSQL role `chandrahassai`; adjust both
`DBT_USER` and `PGUSER` for a different local role.

With Docker Desktop and Postgres.app running:

```bash
docker compose -f orchestration/compose.yml config --quiet
docker compose -f orchestration/compose.yml up -d --build
docker compose -f orchestration/compose.yml ps
```

Open [http://127.0.0.1:8081](http://127.0.0.1:8081). The development login
uses username `admin`. Retrieve its generated password locally with:

```bash
docker compose -f orchestration/compose.yml exec airflow \
  python -c "import json; print(json.load(open('/opt/airflow/state/simple_auth_manager_passwords.json'))['admin'])"
```

The project is mounted read-only. Airflow metadata, state, logs, and dbt
artifacts are stored in Docker named volumes. Container-generated dbt artifacts
are separate from the host's `target/` directory.

Run the three DAG validation checks without database access:

```bash
docker run --rm \
  --network none \
  --entrypoint python \
  -e AIRFLOW__CORE__LOAD_EXAMPLES=false \
  -e AIRFLOW__CORE__DAGS_FOLDER=/opt/project/orchestration/dags \
  --mount "type=bind,source=${PWD},target=/opt/project,readonly" \
  saas-airflow:3.3.2 \
  -m unittest discover -s /opt/project/orchestration/tests -v
```

To stop orchestration while retaining its state:

```bash
docker compose -f orchestration/compose.yml stop
```

This setup is for local development. Scheduled execution requires the Mac
to be awake and Docker, Airflow, and Postgres.app to be running. The DAG does
not reload source CSV files or advance the fixed reporting cutoff.

## Continuous integration

Both workflows run on pushes to `main`, pull requests targeting `main`,
and manual launches.

### Data pipeline CI

`.github/workflows/dbt-ci.yml` uses Ubuntu, Python 3.12, and a fresh
PostgreSQL 18 service with database `saas_analytics_rebuild`. It:

1. Installs analysis, dbt, and dashboard dependencies in separate environments.
2. Regenerates billing and prospect CSV files.
3. Rebuilds the verification database using `sql/000_build_demo.sql`.
4. Checks the dbt connection and builds all models with data and unit tests.
5. Runs the dashboard integration checks.
6. Generates dbt documentation.

### Airflow validation CI

`.github/workflows/airflow-ci.yml` validates the Compose configuration,
builds the Airflow image, and runs three tests for DAG loading, dependencies,
and failure settings. The DAG tests run with container networking disabled.
They validate orchestration configuration rather than executing a full DAG run.

## Metric definitions and limitations

- **MRR:** Subscription prices normalized to monthly amounts, separate from
  collected cash. Snapshots include subscriptions started at or before the
  reporting instant and not ended at that instant. The snapshot calendar spans
  January 1, 2025 through October 1, 2026.
- **MRR movements:** New and churned recurring value since the preceding
  checkpoint. The first snapshot has no preceding movement period.
- **Plan churn:** Churn among subscriptions active at the opening snapshot.
  Pooled monthly churn divides total churn events by total opening
  subscription-period counts; it is not an unweighted average or cumulative churn.
- **Cohort retention:** Retained subscriptions divided by original cohort size.
  Cohorts use UTC subscription start months. Month 1 is the next monthly boundary,
  not a 30-day anniversary. Future checkpoints are omitted. Compare cohorts at
  the same month number; the combined 216/250 retained proportion mixes cohort ages.
- **Invoice balances:** Invoices issued and successful payments completed before
  the cutoff. Aging uses UTC calendar dates. Outstanding balances are not confirmed
  losses or guaranteed recoveries.
- **Funnel conversion:** Each stage counts prospects within the same window:
  prospect creation, inclusive, to 720 hours later, exclusive. A mature window
  closes at or before the reporting cutoff. Events must precede the cutoff.
  Rates with zero denominators are null, and overall rates use summed counts
  rather than averages of channel percentages.
- **First payment:** A positive successful payment following a qualifying
  subscription start. It does not require full invoice settlement.

The billing dataset has one subscription per account and fixed subscription
prices. It models starts and churn rather than expansion, contraction, product
usage retention, or revenue retention. Generated billing-account signup dates
end before September 1, 2026; the separate prospect dataset includes later
unconverted prospects.

This repository demonstrates local analytics and workflow execution. It does
not connect to live customer systems, retry customer payments, send customer
communications, or provide a publicly hosted production service.
