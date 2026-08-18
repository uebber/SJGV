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
5. abort the build on missing execution capital instead of allowing absence to
   flatter a name.

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
| All names, upper-bound probe | 736 | 768 | 1,070 | 1.28pp |

The zero turnover in the developer-only replay is a cap artefact, not evidence
that the defect is immaterial. Raw value moves even when final capped weights do
not. The all-name probe also makes the missing-data failure visible: RMS gains
about 0.40pp solely because its committed-capital field is unsourced. No
production formula may reward that absence.

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

### 3.2 Schema migration

Add or rename fields as follows:

| Field | Role | Weight effect |
|---|---|---|
| `remaining_execution_capex_aud_m` | Gross sourceable remaining initial, restart or growth capital for material unfinished scopes | Added once to EV for all sleeves |
| `available_project_funding_aud_m` | Cash, cash-drawable committed facilities and contracted funding available for those scopes | Developer Gate 2 only |
| `residual_funding_gap_aud_m` | Engine-derived difference between the two fields | Developer Gate 2 and reporting only |
| `committed_capex_aud_m` | Contracted/non-deferrable cash burn inside the stress horizon | Existing producer Gate 2 survival input; unchanged |

Delete `remaining_capex_aud_m` after migration. Keeping it as an alias would
preserve the ambiguity that caused the defect.

`committed_capex_aud_m` and `remaining_execution_capex_aud_m` may refer to some
of the same physical spend, but they are not added together anywhere. One is a
stress-horizon cash-burn input; the other is the all-in economic denominator.

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
   reconcile the hierarchy and retain the larger complete scope, not both.
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
10. **Unknown is not zero.** A missing value aborts the build before weights are
    calculated. It does not exclude one name and reweight the rest, and it never
    enters a sensitivity bound as a favourable zero.

### 4.3 Rox example

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
- Separate pre-production/growth from sustaining, exploration and pre-FID spend.
- Roll project totals forward for sourceable spend and reconcile overlaps.
- Source a defensible numeric zero when no material unfinished execution scope
  exists; silence is not zero.

### Step 2 — split the fields

- Add `remaining_execution_capex_aud_m` and
  `available_project_funding_aud_m`.
- Derive and report `residual_funding_gap_aud_m` in the engine.
- Point developer Gate 2 D3 only at the residual gap.
- Point the weight denominator only at remaining execution capital.
- Retain `committed_capex_aud_m` only for the existing producer stress test.
- Delete the ambiguous `remaining_capex_aud_m` input.

### Step 3 — switch all names together

- Fail the entire build if any selected constituent lacks a sourceable execution
  capital value.
- Apply `EV + remaining execution capital` to every sleeve in the same build.
- Publish old and new denominators, raw weights, cap effects and final weights in
  the transition report.
- Keep the scheduled/unscheduled optionality split as a report only where it is
  directly sourceable.

### Step 4 — replay and approve

- Use one frozen market-data anchor and stub only market inputs.
- Reproduce the current book exactly before changing the denominator.
- Decompose each weight change into capital, normalisation and portfolio caps.
- Inspect raw weights even when final turnover is zero.
- Run a missing-value fault injection proving that RMS-like absence aborts the
  build rather than improving the name.
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
- Sustaining capital, exploration and pre-FID spend do not enter execution
  capital.
- Missing execution capital for any selected constituent aborts the build.
- Numeric zero requires a primary-source note establishing the absence of a
  material unfinished scope.
- M&I non-reserve and Inferred remain active numerator and sensitivity inputs.
- Scheduled/unscheduled reporting cannot change claimed ounces or weights.
- The frozen replay reproduces the baseline before the formula switch.

## 9. Proposed outcome

Approve the capital definition, all-name sourcing pass, field split and test
plan as the next production change. Preserve the same-market-data replay as a
separate approval checkpoint before weights move.

Approve the rejected-alternatives table as institutional memory. Defer the
asset-evidence overlay; implement only the lightweight scheduled/unscheduled
report where a production target already supplies the category split.

This is narrower than the first proposal and more actionable. It corrects a
number that is wrong today, applies the same economics to producers and
developers, and refuses to turn unavailable disclosure into either a favourable
zero or an exclusion of the optionality the index exists to own.
