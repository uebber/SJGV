# Execution capital and optionality evidence — revised design proposal

**Status:** revised after maintainer replay; design only in this PR  
**Base:** `category-shares-and-staleness`  
**Decision requested:** implement the capital-field split for every constituent in one production change; defer the asset-evidence overlay

## 1. Revised decision

The current denominator contains a live defect. It adds a developer's
**residual funding gap** to enterprise value when the economic quantity required
is **remaining execution capital**. One field, `remaining_capex_aud_m`, currently
does both jobs even though the two quantities answer incompatible questions.

The production fix should:

1. split remaining execution capital from available project funding;
2. derive residual funding gap only for the developer Gate 2 test;
3. use `EV + remaining execution capital` as the denominator for producers and
   developers under the same rule;
4. source and classify the capital legs for every constituent before switching
   the formula; and
5. require complete data for the initial switch, then use the bounded incumbent
   carry-forward and scheduled-rejection procedure instead of either a
   favourable zero or a permanent global abort.

Do not ship a developer-only fix. A board-approved mine build inside a producer
is the same economic activity as a mine build inside a pure-play developer.
Charging Rox while leaving Havieron at zero would make the denominator less
comparable, not more.

The optionality evidence proposal should be reduced. A Mineral Resource already
embodies reasonable prospects for eventual economic extraction. Requiring a
freshly republished Table 1 package would grade issuer disclosure habits. For
now, retain the company-level category ledger and add at most a lightweight
**scheduled / unscheduled / unknown** report when a production target discloses
its category mix. Do not build a separate evidence database until there is a
specific, approved weight rule it is capable of supporting.

## 2. The arithmetic correction

### 2.1 What enterprise value already contains

```text
EV = market capitalisation + drawn debt − cash
```

Buying the company means paying market capitalisation and inheriting both the
debt and the cash. If a project still requires `C` of construction spend, its
all-in acquisition-and-build cost is:

```text
AllInCost = EV + C
```

Adding gross remaining execution capital to an EV that has netted cash is
correct. The buyer inherits the cash but must still spend the capital. Spending
cash reduces net cash; drawing a facility increases debt. Either way, funding
availability changes who supplies the money, not whether the project costs
money.

The earlier review of PR #2 was wrong to call `EV + gross capital` a cash double
count for Rox. PR #2 still should not ship: it labelled shared whole-project
capital as optionality-only capital, and its formula `EV + gap +
optionality_capital` would double count whenever the gap was positive.

### 2.2 Why the current formula is wrong

Current §7.1 uses:

```text
FundedEV = EV + residual funding gap
```

If cash is subtracted once in EV and again when deriving the residual gap from
project capital, the cash is credited twice. A fully funded project receives a
zero denominator adjustment even though construction is not free. The existing
developer inputs also use inconsistent conventions:

| Issuer | Current `remaining_capex_aud_m` convention | Result |
|---|---|---|
| AUC | Full pre-production capital; cash not sourced | Execution capital by accident |
| AAR | Pre-production capital less cash | Cash credited twice in §7.1 |
| RXL | Pre-production capital less cash and cash-drawable debt | Cash and facility credited twice in §7.1 |

The field cannot be repaired by replacing its values. Gate 2 D3 needs the gap;
the denominator needs the gross remaining execution capital. Loading Rox's
A$382.6m execution estimate into the current field would incorrectly test
A$382.6m / A$710.7m = 54% against the 30% dilution limit and reject a project
whose disclosed funding covers the spend.

### 2.3 Maintainer replay

Using the same recorded market data, the maintainer's deterministic replay found:

| Probe | Index A$/oz | RXL A$/oz | GGP A$/oz | One-way turnover |
|---|---:|---:|---:|---:|
| Current denominator | 679 | 458 | 895 | — |
| Developers only | 700 | 768 | 895 | 0.00pp |
| All names, incomplete sourcing probe | 736 | 768 | 1,070 | 1.28pp |

The zero turnover in the developer-only replay is a cap artefact, not evidence
that the defect is immaterial. Raw value moves even when final capped weights do
not. The all-name probe also makes the missing-data failure visible: RMS gains
about 0.40pp solely because its committed-capital field is unsourced. No
production formula may reward that absence.

The A$736/oz result is **not an upper bound and not the proposed answer**. GMD's
A$229m executed EPC sum is a floor for its project scope because it can omit
owner costs and other required spend; other `committed_capex_aud_m` records can
contain growth expenditure that the execution-capital definition will exclude.
The direction of error therefore differs by issuer. Read the probe only as
evidence that the denominator defect is worth roughly A$50/oz on the current
headline and is large enough to source properly.

## 3. Proposed production fields

### 3.1 Keep the three concepts separate

For every material not-yet-complete mine build, restart or growth scope `p`:

```text
RemainingExecutionCapex_p
    = sourceable spend from the as-of date to completion

AvailableProjectFunding_p
    = sourceable cash allocated or available to the project
    + committed cash-drawable facilities
    + other contracted funding

ResidualFundingGap_p
    = max(0, RemainingExecutionCapex_p − AvailableProjectFunding_p)
```

At company level:

```text
RemainingExecutionCapex_i = Σ project scopes p, counted once each

ResidualFundingGap_i = max(
    0,
    RemainingExecutionCapex_i − AvailableProjectFunding_i
)

AllInEV_i = EV_i + RemainingExecutionCapex_i

RawWeight_i ∝ ClaimedMoz_i / AllInEV_i
```

The denominator never adds both capital and gap. The residual gap remains a
Gate 2 financing-capacity input; it is not an additional cost.

### 3.2 Define materiality as a parameter

“Material” may not remain an analyst judgement because including a project
changes what was paid for the claim. The production implementation must add the
following parameters to `data/config.json` **in the same commit as their named
engine consumers**:

```json
"execution_capital": {
  "materiality_of_ev": 0.01,
  "incumbent_max_carry_forward_months": 6
}
```

| Parameter | Named consumer | Rule |
|---|---|---|
| `execution_capital.materiality_of_ev` | `build_index.execution_capital_ledger` | An issuer's unfinished initial, restart and growth scopes are summed before testing. If the aggregate is at least 1% of pre-capex EV, include every sourceable scope in that aggregate; otherwise report a sourced de minimis zero. |
| `execution_capital.incumbent_max_carry_forward_months` | `build_index.resolve_execution_capital` | Maximum age of a carried-forward incumbent value under §4.3. |

The aggregation step is mandatory: an issuer cannot split one build into several
sub-1% contracts and have them disappear. An approved scope with no sourceable
total is `unknown`, not presumed below the threshold. Materiality is tested at
the annual deep rebalance and when an event-driven project approval occurs;
quarterly price movement alone does not switch a scope in and out.

The proposed 1% starting value means an omitted aggregate changes that issuer's
pre-normalisation denominator by less than 1%. It remains a real weighting
parameter: the production replay must show the book at 0%, 0.5%, 1% and 2%, and
the committee must approve the value before it becomes live. This design-only PR
does not add it to config now because the repository correctly rejects declared
but unread parameters.

### 3.3 Schema migration

Add or rename fields as follows:

| Field | Role | Weight effect |
|---|---|---|
| `execution_capital_projects` | Structured per-project scope, as-of date, remaining total, stress-horizon committed portion, exclusions and sources | Feeds both capital totals and their reconciliation |
| `remaining_execution_capex_aud_m` | Engine-derived sum of included project records | Added once to EV for all sleeves |
| `available_project_funding_aud_m` | Cash, cash-drawable committed facilities and contracted funding available for those scopes | Developer Gate 2 only |
| `residual_funding_gap_aud_m` | Engine-derived difference between the two fields | Developer Gate 2 and reporting only |
| `committed_capex_aud_m` | Contracted/non-deferrable cash burn inside the stress horizon | Existing producer Gate 2 survival input; unchanged |

Delete `remaining_capex_aud_m` after migration. Keeping it as an alias would
preserve the ambiguity that caused the defect.

`committed_capex_aud_m` and `remaining_execution_capex_aud_m` may refer to some
of the same physical spend, but they are not added together anywhere. One is a
stress-horizon cash-burn input; the other is the all-in economic denominator.

### 3.4 Mandatory project reconciliation

The fact that the two totals are consumed in different formulas does not permit
them to disagree about the same mine. Every `execution_capital_projects` record
must bridge the two uses at one as-of date:

| Project item | Required content |
|---|---|
| `project_id` and scope | Stable identifier and issuer-defined build, restart or expansion boundary |
| `remaining_execution_capex_aud_m` | Total sourceable spend from the as-of date to completion |
| `committed_within_gate2_horizon_aud_m` | Portion contracted/non-deferrable inside the stress horizon |
| `excluded_aud_m` | Sustaining, exploration, pre-FID, post-completion or other excluded spend, itemised by reason |
| `available_project_funding_aud_m` | Funding used to derive the developer residual gap, where applicable |
| source and as-of date | Primary document for every amount and a common measurement date or an explicit roll-forward |

At company level the bridge must satisfy:

```text
remaining_execution_capex_aud_m
    = sum(included project remaining totals)

committed_capex_aud_m
    = sum(project committed-within-horizon portions)
    + other non-project non-deferrable stress burn
```

Equality between the two company totals is neither expected nor required: one
is total remaining project spend and the other is cash burn inside a fixed
horizon. But every difference must be explained by horizon, exclusions or an
identified non-project item. For the same project and as-of date,
`committed_within_gate2_horizon_aud_m` cannot exceed remaining execution capital.
GGP's Havieron record, for example, must use one project basis and show which
part of the A$1,065m total sits inside Gate 2 rather than allowing two unrelated
figures to describe the same build.

## 4. Capital sourcing and allocation rules

### 4.1 Apply the rule to all sleeves at once

The change must cover every constituent selected by the pre-weight gates,
including unfinished material projects housed inside producers. At minimum:

- Havieron's A$1,065m pre-production build cannot remain at zero because GGP is
  labelled a producer;
- Mt Gibson's A$474m build must be treated consistently with a standalone
  developer build; and
- Tower Hill's executed A$229m EPC sum is evidence of a project commitment, but
  the denominator must use the sourceable **remaining total execution cost**,
  not assume an EPC contract equals all owner and project costs.

The existing company notes already contain a bounded starting inventory: 11 of
the 12 current constituents have issuer-sourced committed-capital information.
The blocking tasks are to source RMS and to separate pre-production/growth from
sustaining and deferrable spend in every note. This is substantial but finite;
the production target should not be described as unreachable.

### 4.2 Scope rules

1. **Use economic activity, not sleeve label.** A new mine, restart, new plant,
   material expansion or pre-strip that unlocks a defined future plan is an
   execution-capital scope whether the issuer is a producer or developer.
2. **Count each scope once.** When company guidance overlaps a project total,
   reconcile the hierarchy under §3.4 and retain the larger complete scope, not
   both.
3. **Use remaining total cost, not just contracted cost.** An EPC contract may
   omit owner costs, mining fleet, pre-production mining, contingency or other
   required spend. Use the latest issuer total and roll it forward.
4. **Roll forward from sources only.** Subtract spend since the estimate only
   when cumulative or period expenditure can be reconciled to that scope.
   Otherwise preserve the estimate date and block production adoption until a
   current bound is sourceable.
5. **Exclude sustaining capital after steady state.** It supports current
   production and belongs to AISC and survival analysis, not the capital needed
   to unlock future ounces.
6. **Exclude deferrable exploration and pre-FID concepts.** They are options to
   spend, not capital the current claimed plan requires.
7. **Do not net financing from economic capital.** Cash and facilities affect
   residual gap only.
8. **Do not allocate shared capital to optionality alone.** A plant serving
   Reserves, M&I and Inferred material is whole-project capital. At company level
   it adjusts the denominator of the whole claimed-ounce ledger.
9. **Do not allocate capital pro rata by ounces.** Tonnes or ounces are not
   evidence of marginal capital causation. Use issuer-disclosed incremental
   scope or retain the whole-project total.
10. **Unknown is not zero.** Initial migration cannot switch the production
    formula until every selected constituent has a current value. Recurring
    operations follow §4.3 rather than taking the index offline or silently
    substituting zero.

### 4.3 Recurring operations

The migration completeness rule and the live-index rule are deliberately
different. A one-time formula switch may wait for a complete cross-section; an
already-live index needs a deterministic response to a late or changed filing.

| Situation | Procedure |
|---|---|
| Initial production migration | Do not activate the new denominator until every selected constituent has a current sourced value or sourced de minimis zero. |
| New entrant | No admission without current project reconciliation and execution capital. |
| Incumbent, routine disclosure delayed | Carry forward the last verified **gross** remaining execution capital unchanged for up to six months. Assume no spend-down. Flag the input `CARRY-FORWARD`. |
| Incumbent announces a new approved scope without total cost | Use the greater of the last verified company total and any newly sourceable contracted or guided minimum, flag `PROVISIONAL-LOWER-BOUND`, and open an event-driven sourcing item. Never infer the missing total. |
| Carry-forward reaches six months | Reject the constituent at the next quarterly rebalance under the ordinary data-quality rule; redistribute through normalisation. Do not abort the whole build. |
| Project completes or is cancelled | Reduce or remove capital only on a primary source. Elapsed time is not evidence of completion. |

The six-month limit is two light quarterly cycles and is controlled by
`execution_capital.incumbent_max_carry_forward_months`. The annual deep
rebalance rebuilds every scope from primary sources. Light rebalances roll
forward capital from quarterly disclosures. Board approval, cancellation,
completion, a material cost change or a Gate 2 funding breach is event-driven.

This hierarchy can temporarily preserve a conservative stale value, but it
cannot create a favourable zero. A newly disclosed lower bound is explicitly not
treated as a current point estimate, and it cannot survive beyond the carry-
forward window. Structural code/config inconsistencies still hard-abort; issuer
data absence follows this constituent lifecycle.

### 4.4 Rox example

Rox illustrates all three fields:

```text
Remaining execution capital    = A$382.6m at the DFS estimate date
Available project funding      = A$152.7m cash + A$320m cash-drawable debt
Residual funding gap           = A$0
```

Before production adoption, the execution estimate should be rolled forward for
sourceable construction spend since the DFS. The full estimate can remain a
conservative bound only if the report labels its estimate date and does not
present it as a current point value.

The economic denominator adds remaining execution capital once. Gate 2 reads
the zero residual gap. Nothing is called `optionality_capital`: the same plant
and development serve the 674 koz Reserve and the scheduled non-reserve material.

## 5. Optionality evidence — narrower decision

### 5.1 Delete E2

The prior proposal's E2 “RPEEE basis” is near-vacuous as an asset ranking. Under
JORC, reasonable prospects for eventual economic extraction are constitutive of
a Mineral Resource. Table 1 asks for cut-off, mining, metallurgical and
environmental assumptions, but ASX requires the full “if not, why not” package
on first or materially changed reporting—not annual republication for every
asset.

E2 would therefore measure whether assumptions were republished recently more
than whether the resource has a basis. It should be removed, not used as a gate,
score or evidence haircut.

### 5.2 Retain one lightweight report

Where an issuer publishes a current production target with category proportions,
report:

- confidence-weighted M&I non-reserve and Inferred ounces scheduled in the plan;
- disclosed optionality outside that schedule; and
- `unknown` where public data cannot reconcile the split.

This is a report only. Scheduled optionality does not replace the company-level
Mineral Resource ledger, and unscheduled optionality is not deleted or
haircut. The current 1.0 / 0.5 / 0.2 category weights remain the only confidence
adjustment.

Do not create a new project-evidence file, schema, reconciliation application or
coverage suite merely to support this report. The capital migration will
already require project-scoped notes. Add a separate evidence overlay only if a
future proposal identifies a production rule that needs it and demonstrates
that the required evidence is sourceable across the cohort.

### 5.3 Primary citations verified

The evidence discussion is supported by the primary rules:

- [JORC Code 2012](https://www.jorc.org/docs/JORC_code_2012.pdf) clause 12 defines
  Resources by geological confidence and makes Reserves a modified subset of
  Measured and Indicated Resources; clause 15 requires annual review and the
  effective date of each statement; Table 1 section 3 covers resource cut-off,
  mining, metallurgical and environmental assumptions.
- [ASX Listing Rules Chapter 5](https://www.asx.com.au/documents/rules/Chapter05.pdf)
  rules 5.8 and 5.9 require detailed Table 1 reporting on first or materially
  changed material-project Resources and Reserves; rule 5.16 requires production
  targets to disclose the proportions of each Reserve and Resource category;
  rule 5.21 permits annual holdings to be tabulated by material geographic area.
- [ASX Guidance Note 31](https://www.asx.com.au/documents/rules/gn31_reporting_on_mining_activities.pdf)
  explains the “if not, why not” Table 1 requirement and confirms annual
  statements may be broken down by material project or geographic area.

The distinction is deliberate: Listing Rule 5.21.2 itself says **geographic
area based on materiality**. The additional “project (if material) or
geographical area” explanation appears in Guidance Note 31, not in the rule.

## 6. Alternatives rejected — retain as institutional memory

| Alternative | Decision | Reason |
|---|---|---|
| Binary asset eligibility gate | Reject | Deletes optionality according to disclosure format and makes the book reserves-only. |
| Evidence haircut or score | Reject | Double counts geological uncertainty already represented by category weights and rewards disclosure volume. |
| Count only scheduled optionality | Reject for production; report separately | A production target is evidence of scheduling, not the definition of a Mineral Resource. |
| Attach whole-project capital to optionality only | Reject | The same plant and development commonly unlock Reserve and non-reserve material. |
| Set execution capital to zero when fully funded | Reject | Financing capacity does not remove the economic spend. |
| Add execution capital and residual gap | Reject | Counts the financing shortfall twice inside the same project cost. |
| Developer-only denominator correction | Reject | Penalises pure-play developers while identical builds inside producers remain free. |
| Impute missing producer capital | Reject | A cohort ratio would manufacture a direct denominator input. |

## 7. Production implementation sequence

### Step 1 — source and classify

- Source RMS from a current primary filing.
- For all selected constituents, identify unfinished material initial, restart
  and growth scopes.
- Apply the 1% aggregate-of-EV materiality rule; list every sub-threshold scope
  before testing the aggregate so fragmentation cannot erase a build.
- Separate pre-production/growth from sustaining, exploration and pre-FID spend.
- Build the §3.4 project bridge, roll totals forward for sourceable spend and
  reconcile overlaps with the Gate 2 committed-capex record.
- Source a defensible numeric zero when no material unfinished execution scope
  exists; silence is not zero.

### Step 2 — split the fields

- Add `execution_capital_projects` and
  `available_project_funding_aud_m` to the data schema.
- Add the two `execution_capital` config parameters and their named consumers in
  the same commit.
- Derive `remaining_execution_capex_aud_m` from the included project records.
- Derive and report `residual_funding_gap_aud_m` in the engine.
- Point developer Gate 2 D3 only at the residual gap.
- Point the weight denominator only at remaining execution capital.
- Retain `committed_capex_aud_m` only for the existing producer stress test.
- Delete the ambiguous `remaining_capex_aud_m` input.

### Step 3 — switch all names together

- For the initial switch, require a current sourceable value or sourced de
  minimis zero for every selected constituent.
- Apply `EV + remaining execution capital` to every sleeve in the same build.
- Publish old and new denominators, raw weights, cap effects and final weights in
  the transition report.
- After activation, apply the six-month incumbent carry-forward and scheduled
  rejection procedure in §4.3; do not turn issuer data absence into a permanent
  global hard abort.
- Keep the scheduled/unscheduled optionality split as a report only where it is
  directly sourceable.

### Step 4 — replay and approve

- Use one frozen market-data anchor and stub only market inputs.
- Reproduce the current book exactly before changing the denominator.
- Decompose each weight change into capital, normalisation and portfolio caps.
- Inspect raw weights even when final turnover is zero.
- Run materiality sensitivity at 0%, 0.5%, 1% and 2% of EV.
- Label the maintainer's A$736/oz result as an incomplete sourcing probe, not a
  target, bound or expected production result.
- Run missing-value fault injection for initial migration, incumbent carry-
  forward, expiry, new entrant and newly approved unsourced scope.
- Require a separate approval for the production switch after the sourced data
  table and replay are reviewed.

## 8. Required tests

- Additional cash or a committed facility reduces residual funding gap but does
  not reduce remaining execution capital.
- Remaining execution capital changes the denominator but cannot change the D3
  funding-gap verdict by itself.
- Available project funding can change D3 but cannot change the denominator.
- A fully funded project can have zero residual gap and positive execution
  capital.
- `AllInEV = EV + remaining execution capital`; neither residual gap nor
  committed stress capex is added again.
- Producer and developer records with the same project economics receive the
  same denominator treatment.
- One project referenced by company guidance and a project study adds capital
  exactly once.
- Every project has one common-as-of bridge between total remaining execution
  cost and its Gate 2 committed-within-horizon portion.
- A project committed-within-horizon amount cannot exceed its remaining
  execution total; every company-level difference is explained by horizon,
  exclusions or identified non-project stress burn.
- Sustaining capital, exploration and pre-FID spend do not enter execution
  capital.
- Individually sub-threshold scopes are aggregated before the 1% materiality
  test; fragmenting one project cannot change inclusion.
- The config audit proves both execution-capital parameters have the declared
  consumers and no duplicate or unread threshold exists.
- Missing execution capital blocks initial migration and new entry, but an
  incumbent follows carry-forward, expiry and scheduled rejection without a
  global build abort.
- Carry-forward never assumes spend-down, never lasts beyond six months and can
  be cleared only by a primary source.
- Numeric zero requires a primary-source note establishing the absence of a
  material unfinished scope.
- M&I non-reserve and Inferred remain active numerator and sensitivity inputs.
- Scheduled/unscheduled reporting cannot change claimed ounces or weights.
- The frozen replay reproduces the baseline before the formula switch.

## 9. Proposed outcome

Approve the capital definition, configured materiality rule, project
reconciliation, all-name sourcing pass, field split, recurring-operations
procedure and test plan as the next production change. Preserve the same-market-
data replay as a separate approval checkpoint before weights move.

Approve the rejected-alternatives table as institutional memory. Defer the
asset-evidence overlay; implement only the lightweight scheduled/unscheduled
report where a production target already supplies the category split.

This is narrower than the first proposal and more actionable. It corrects a
number that is wrong today, applies the same economics to producers and
developers, and refuses to turn unavailable disclosure into either a favourable
zero or an exclusion of the optionality the index exists to own.
