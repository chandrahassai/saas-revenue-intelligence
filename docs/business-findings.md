# Business Findings and Decision Opportunities

## Context

This analysis uses synthetic SaaS billing, subscription, and prospect data
at an October 1, 2026 UTC reporting cutoff.

The findings demonstrate how a tested analytics platform can support
investigation and prioritization. They do not represent measured outcomes
from a real business.

## 1. Revenue growth and subscription retention

Generated subscriptions contributed USD 56,400 in MRR across
216 active accounts.

For the latest monthly movement period:

- New MRR was USD 1,400.
- Churned MRR was USD 900.
- Net MRR change was positive USD 500.

All 21 monthly movement periods reconciled to closing MRR.

### Decision opportunity

Review new and churned MRR together when evaluating growth.
A positive net change can coexist with meaningful subscription losses.

Reconciled movement models provide a consistent starting point for
investigating which accounts and plans contributed to those movements.

### Interpretation limits

MRR measures recurring subscription value, not collected cash.
The generated subscription model uses fixed prices and models starts
and churn; it does not model expansion, contraction, or reactivation.

## 2. Collections review priorities

Outstanding balances totaled USD 97,920 across 327 unpaid invoices.

Of that balance:

- USD 89,620 was overdue across 291 invoices.
- USD 64,700 was at least 91 days overdue.
- The 91+ day bucket represented 72.19% of overdue dollars.
- The ten accounts with the largest overdue balances held USD 31,200,
  or 34.81% of overdue dollars.

Recorded payment activity divided overdue balances into:

| Category | Overdue balance (USD) |
|---|---:|
| Failed attempts only | 41,400 |
| No completed attempts | 34,900 |
| Partially paid | 13,320 |

### Decision opportunity

Use overdue amount and age to organize a collection review queue.
Review the largest balances and older invoices, then examine the
recorded payment activity for each account.

Different activity categories suggest different investigation paths:
failed-attempt details, payment initiation and completion records,
or remaining balances after partial payments.

### Interpretation limits

The largest-balance and oldest-balance groups can overlap.

Payment activity categories do not establish the cause of nonpayment.
No completed attempt does not necessarily mean no attempt was initiated.
Outstanding balances are neither confirmed losses nor guaranteed recoveries.

## 3. Cohort retention and plan churn

Pooled monthly subscription churn was:

| Plan | Pooled monthly churn |
|---|---:|
| Growth | 1.78% |
| Starter | 1.61% |
| Enterprise | 1.08% |

The January 2025 subscription cohort retained five of its original
eight subscriptions at month 21, or 62.50%.

### Decision opportunity

Use the same cohort-age column when comparing retention across
subscription start months.

Plan-level churn can identify groups for further investigation,
provided the review also considers their opening subscription counts,
customer composition, and observation periods.

### Interpretation limits

Pooled churn divides total churn events by total opening
subscription-period counts. It is not cumulative customer churn.

Cohort checkpoints are calendar-month boundaries, not exact 30-day
anniversaries. Small cohorts can show large percentage changes from
a single cancellation.

Retention measures subscription activity, independently of payment status.
The combined 216/250 retained proportion mixes cohorts of different ages.

## 4. Conversion funnel

The source contains 1,000 synthetic prospects. Of these, 984 completed
the full 30-day observation window and 16 remained pending.

Among eligible prospects:

| Stage | Prospects | Conversion from previous stage |
|---|---:|---:|
| Eligible prospects | 984 | — |
| Trial started | 590 | 59.96% |
| Subscription started | 250 | 42.37% |
| First successful payment | 217 | 86.80% |

Overall prospect-to-payment conversion was 22.05%.

The stage transitions show:

- 394 eligible prospects did not start a trial within the window.
- 340 trial starters did not subscribe within the window.
- 33 subscribers did not record a first successful payment within the window.

The prospect-to-trial transition had the largest absolute drop.
Trial-to-subscription had the largest proportional drop:
340 of 590 trial starters, or 57.63%.

### Decision opportunity

Investigate both trial entry and the transition from trial to subscription.

Further analysis would require suitable engagement and onboarding events,
offer or pricing information, and potentially an experiment to distinguish
possible causes of drop-off.

For subscribed prospects without a payment inside the window, inspect
payment attempts and timing before deciding whether the issue is a failed
payment, a later payment, or another condition.

### Interpretation limits

Every stage uses the same window: prospect creation, inclusive,
to 720 hours later, exclusive. Recent prospects are excluded from
completed-window conversion rates.

A first payment means a positive successful payment. It does not require
an invoice to be fully settled. Missing the 30-day payment milestone does
not establish permanent nonpayment.

Prospect and trial activity are simulated, and acquisition channels are
randomly assigned. The 250 linked accounts come from the existing
generated billing dataset. Channel differences demonstrate the method;
they are not evidence of real marketing effectiveness.

## Validation and claims

The platform has passed:

- 127 dbt data tests and two dbt unit tests.
- Seven dashboard integration checks.
- Three Airflow DAG validation tests.
- A full local Airflow workflow run.
- GitHub CI using a freshly rebuilt verification database.

This work demonstrates reproducible data generation, tested SQL modeling,
metric definitions, interactive analysis, workflow orchestration, and
automated verification.

No collection recovery, conversion uplift, churn reduction, or other
real-world business impact has been measured.