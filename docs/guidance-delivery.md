# Guidance delivery in SJGV v2.1

The delivery rule asks whether management repeatedly failed to deliver the
production and cost plan on which the gold claim depends. It is not a general
management score. It produces only pass, 5% cap, or exclusion.

## Evidence base

The study covered 23 producer and near-producer candidates over their latest
three completed producing periods. Claim-level guidance, revisions and actuals
were retained in the knowledge store with exact locators and excerpts. The
machine-readable portfolio ratings are in `data/guidance_delivery.json`.

Across 69 possible company-years, 52 had a Boolean result on both original and
final bases. Fifty-three comparable years supported the threshold sensitivity
calculation. Gaps mostly reflected recent production starts, scope-changing
transactions, or verified issuer non-publication rather than arithmetic
imputation.

## What the data showed

At zero tolerance, 27 of 53 comparable company-years missed at least one
original-guidance limb and nine names had at least two misses. At the adopted 5%
tolerance, 19 years missed and five names had at least two. At 10%, nine years
missed and one name had at least two. The 5% buffer is therefore material: it
absorbs rounding and small disclosure differences without excusing broad misses.

Guidance vintage mattered even more. At 5%, five names triggered on original
guidance while none triggered on final revised guidance alone. A rule based only
on final guidance would allow repeated downward revisions to erase the evidence
of initial planning. A rule based only on original guidance would treat a
credible reset exactly like persistent failure.

The adopted rule keeps both:

- repeated original misses with any revised miss are a hard fail;
- repeated original misses with successful revised delivery receive a 5% cap;
- one original and one revised failure receives a 5% cap; and
- a 100% original failure rate over a shorter producing history is a hard fail.

Verified failure to publish full-year production or AISC guidance also counts
as failure. That conclusion is permitted only after a complete disclosure sweep
establishes non-publication. A missing local artifact or unresolved acquisition
route is never charged to the company. Pre-production years do not count.

## v2.0 consequence

In the frozen release, BGL, OBM and PNR were excluded from the otherwise live
book; CYL and WGX were capped at 5%. The rule was therefore economically
material. Its effect is visible in the snapshot's rejected list, pre-cap weights
and cap notes rather than frozen into this rationale as a permanent statistic.

## Limits

Guidance is not standardised across issuers. Portfolio changes, acquisitions,
divestments and cost definitions can make a year non-comparable. A three-year
window is short, and a new producer can be judged on one producing year. The
rule responds by requiring scope comparability and explicit evidence states,
not by filling missing years.

The rule also measures delivery against management's public plan, not asset
quality. A conservative guide can be easier to beat than an ambitious one. That
is why delivery affects admission or maximum loss, while ounces per funded EV
continues to determine the value ranking.
