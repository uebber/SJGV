# Agent job — three-year producer guidance-delivery research

## Objective

Build an auditable, cohort-wide record of original annual production and AISC
guidance versus actual outcomes for the last three completed financial years.
The research will determine whether a future SJGV amendment can apply a 5%
execution-risk cap after two material miss-years. Do not change index eligibility,
weights, methodology, configuration or accepted company fields in this task.

## Universe and periods

Read `data/companies.json` at the task's starting commit. Cover every candidate
classified `producer` or `near_producer`, including companies currently excluded
by another gate. Use each issuer's last three completed financial years as of the
research date; do not assume every issuer uses a June year-end. Record fewer years
only where the company or relevant operation genuinely lacks three completed
years, and label the result `INSUFFICIENT_HISTORY`.

## Required evidence for each company-year

Establish from primary documents:

1. the earliest formal full-year production guidance issued for that financial
   year, including lower and upper bounds;
2. the earliest formal full-year AISC guidance issued for that financial year,
   including lower and upper bounds, currency and unit;
3. the final full-year production actual;
4. the final full-year AISC actual; and
5. every formal withdrawal or revision between original guidance and the actual.

Preserve group versus asset scope, attributable basis, gold versus gold-equivalent
ounces, produced versus sold ounces, continuing versus discontinued operations,
and treatment of by-product credits. Guidance and actuals are comparable only
when these bases match or the issuer publishes an exact reconciliation. Never
construct an analyst bridge.

## Candidate rule to evaluate

Calculate, without adopting the rule:

```text
production_miss = actual_production < 0.95 × original_guidance_lower
aisc_miss       = actual_AISC > 1.05 × original_guidance_upper
miss_year       = production_miss OR aisc_miss
trigger         = at least 2 miss_years among the last 3 completed years
```

A year counts once even when both limbs miss. A point estimate is a range with
equal endpoints. Compare against original guidance; separately report performance
against final revised guidance so goalpost-moving remains visible. Do not decide
from percentage statements in prose when the source values permit direct
arithmetic.

Use these states where a Boolean result is not supportable:

- `MISSING_GUIDANCE`
- `MISSING_ACTUAL`
- `NOT_COMPARABLE` — scope or basis changed without an issuer reconciliation
- `INSUFFICIENT_HISTORY`

None of these states is a pass. Report them separately; do not infer a value or
recommend how the future engine should cap an untested name.

## Source protocol

Follow `source-knowledge-base.md` and `data/README.md` before discovery. Query the
retained knowledge store first with `tools/kb.py plan` and the generated views.
During migration also search `data/companies.json`, `data/SOURCES.md`,
`tools/sources.json` and `.cache/` before fetching.

Prefer lodged ASX announcements and audited annual reports. Search results,
snippets, aggregators and news reports are discovery aids only. For every fact
established by reading a source, archive it and use `tools/kb.py register-claim`
with the complete §6.2 record: artifact, exact page/table locator, verbatim
excerpt, publication date and distinct as-of period. Respect booked retry dates;
do not fetch around a refusal.

## Deliverables

Create `docs/guidance-delivery-study-YYYY-MM-DD.md` containing:

1. a coverage table for every company and year;
2. the four source values, bases and exact citations for every comparable year;
3. production- and AISC-miss percentages calculated from the source bounds;
4. original-guidance and final-guidance results shown separately;
5. each company's three-year miss count and candidate-rule result;
6. all missing or non-comparable observations and the precise reason;
7. a sensitivity table at 0%, 5% and 10% materiality thresholds;
8. the names that would receive a 5% cap, with no portfolio implementation; and
9. an explicit assessment of whether the evidence is sufficiently complete and
   comparable to support a binding methodology amendment.

Include a machine-readable appendix in the report or a separate candidate JSON
under `docs/`; it must contain document/claim identifiers rather than uncited
values. Do not write candidate values into `data/companies.json` and do not alter
the engine.

## Validation and stopping conditions

Run:

```sh
.venv/bin/python tools/kb.py audit --strict
```

If any company lacks a primary source after the permitted acquisition sequence,
retain the gap and report it. Do not substitute a secondary estimate merely to
complete the matrix. Finish with the exact coverage count: comparable
company-years divided by required company-years, plus the number of companies
for which the proposed trigger can be determined without assumption.
