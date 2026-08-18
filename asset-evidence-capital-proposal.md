# Asset evidence and capital allocation — design proposal

**Status:** proposal only — no production weight, gate, parameter or data change  
**Base:** `category-shares-and-staleness`  
**Decision requested:** approve a shadow evidence register and capital report; do not approve a new weighting term

## 1. Decision summary

SJGV should preserve the current company-level ounce ledger as the production
numerator. A current, Competent-Person-backed Mineral Resource is already a
claim with a defined geological confidence category. Requiring reserve-level
metallurgy, processing, permitting and capital evidence before M&I or Inferred
ounces can count would turn the product into the reserves-only index it exists
not to be.

Asset evidence should instead be captured in a **non-weighting evidence
overlay** with four observable levels. It should answer how much of the
optional claim is asset-attributed, supported by resource-level assumptions,
scheduled in a published production target, and attached to an executable
capital plan. Missing evidence remains `unknown`; it is never silently treated
as a failed asset or zero capital.

Capital must be split into two different facts:

1. **Residual funding gap** asks whether the company can finance the plan. It
   remains a Gate 2 survival input and the current production denominator term.
2. **Remaining execution capital** asks what must still be spent to deliver a
   defined project plan. It may be reported in a shadow all-in denominator, but
   it must be counted once at project scope, never labelled as capital belonging
   only to the non-reserve ounces in that plan.

No evidence level or execution-capital figure should affect production weights
until the required data exists for every eligible constituent and a same-market-
data replay is separately approved.

## 2. Why the binary asset gate failed

The rejected design asked each non-reserve asset to prove all of the following:
a current resource, category-specific jurisdiction and ownership, metallurgy
and recovery, a processing route, land and permitting, a disclosed capital
path, and complete encumbrances. An asset missing any item contributed no
optionality.

That combined three different questions:

- **Does the mineral inventory exist at the stated confidence?**
- **Has some of it entered an issuer-backed mine plan?**
- **Is that plan executable and what remains to be spent?**

JORC and ASX do not require the same disclosure depth for all three. The JORC
Code requires a Mineral Resource to have reasonable prospects for eventual
economic extraction and Table 1 asks for cut-off, mining, metallurgical and
environmental assumptions. It also says resource-stage mining and metallurgy
assumptions may not be rigorous, provided their basis and limitations are
reported. Reserve conversion requires at least a PFS-level technically
achievable and economically viable mine plan with the Modifying Factors
considered.

ASX Listing Rule 5.8 requires Table 1 disclosure for a material project's first
or materially changed Resource. Annual statements may then aggregate holdings
by material project or geographic area. A producer can therefore comply fully
without republishing current asset-by-asset recoveries, processing routes,
permits and capital paths for every non-reserve ounce each year.

Production targets are the useful dividing line. Listing Rule 5.16 requires the
material assumptions and the proportions of Reserves, Measured, Indicated and
Inferred material underpinning a target. That evidence supports a separate
statement that some optionality is **scheduled**. It does not invalidate the
rest of the disclosed Resource.

Primary references:

- [JORC Code 2012](https://www.jorc.org/docs/JORC_code_2012.pdf), especially clauses 12, 15 and Table 1 sections 3–4
- [ASX Listing Rules Chapter 5](https://www.asx.com.au/documents/rules/Chapter05.pdf), especially rules 5.8, 5.9, 5.16 and 5.21
- [ASX Guidance Note 31](https://www.asx.com.au/documents/rules/gn31_reporting_on_mining_activities.pdf), especially sections 2.4 and 10.2

## 3. Proposed evidence model

### 3.1 Keep one canonical claim

`data/companies.json` remains the only source of production ledger ounces:

```text
ClaimedMoz = eligible P&P
           + 0.5 × eligible M&I non-reserve
           + 0.2 × eligible Inferred
           − forward-sold ounces
```

The category-specific Gate 1 shares and the 18-month statement-currency gate
apply exactly as they do on `category-shares-and-staleness`. The evidence
overlay may reconcile to that claim and describe it, but may not mutate it.

### 3.2 Store evidence separately

If implemented, use `data/project_evidence.json`, keyed by ticker and issuer-
defined project or geographic scope. Do not duplicate the canonical company
totals without a reconciliation record. Each company receives an explicit
`unallocated` scope for ounces that are validly reported at group or geographic
level but cannot be mapped further from public disclosure.

Illustrative shape:

```json
{
  "ticker": "RXL",
  "scope_id": "youanmi-dfs-2025",
  "scope_type": "material_project",
  "resource": {
    "document": "youanmi_dfs_2025",
    "effective_date": "2025-11-13",
    "attributable_moz": {
      "pp": 0.674,
      "mi_non_reserve": 0.048,
      "inferred": 0.178
    }
  },
  "resource_assumptions": {
    "cut_off": "disclosed",
    "mining": "disclosed",
    "metallurgy": "disclosed",
    "environment": "disclosed"
  },
  "production_target": {
    "status": "current",
    "category_mix_disclosed": true
  },
  "execution": {
    "study_stage": "DFS",
    "approvals": "disclosed",
    "processing_route": "disclosed"
  },
  "capital": {
    "remaining_execution_capex_aud_m": 382.6,
    "spent_since_estimate_aud_m": "unknown",
    "available_project_funding_aud_m": 472.7,
    "residual_funding_gap_aud_m": 0.0,
    "scope": "whole DFS production target"
  }
}
```

The numbers above illustrate the rejected PR's Rox source record. Before a
shadow calculation, the pre-production estimate must be rolled forward for any
sourceable spend since the DFS; if it cannot be rolled forward it is reported
as an estimate-date figure, not current remaining capital.

### 3.3 Four evidence levels, all reports

| Level | Name | Minimum public evidence | Meaning |
|---|---|---|---|
| E1 | Attributed Resource | Current primary Resource statement, category, ownership/economic interest and location | The optional ounces can be mapped below group level. |
| E2 | RPEEE basis | E1 plus disclosed cut-off and resource-level mining, metallurgical and environmental assumptions, including an “if not, why not” explanation where applicable | The issuer has stated the basis for reasonable prospects of eventual economic extraction. This is not a mine plan. |
| E3 | Scheduled optionality | E2 plus a current production target or study disclosing the category mix underpinning the plan | A stated subset of M&I or Inferred material appears in an issuer-backed schedule. |
| E4 | Execution evidenced | E3 plus study stage, material approvals/tenure, processing route and remaining execution capital | The scheduled plan has a sourceable delivery path. This is still not certainty. |

These are ordinal disclosure states, not scores. An E1 ounce is not multiplied
by a smaller number than an E4 ounce. The existing 1.0 / 0.5 / 0.2 confidence
weights already distinguish the geological categories; another evidence
haircut would double count uncertainty and systematically favour issuers that
repeat more project detail.

### 3.4 Reports produced

At issuer and index level, report:

- `asset_attributed_share_of_optional_claim`
- `rpeee_evidenced_share_of_optional_claim`
- `scheduled_share_of_optional_claim`
- `execution_evidenced_share_of_optional_claim`
- `capital_paired_share_of_scheduled_claim`
- optional claim in an explicit `unallocated` scope
- source date and age for every evidence record

Use **evidenced**, **scheduled** and **unallocated**, not **qualified** and
**failed**. The overlay measures disclosure coverage; it does not purport to
re-estimate the Competent Person's Resource.

### 3.5 Encumbrances

Record streams, royalties, joint ventures and third-party interests when the
issuer identifies them as material to the scope. Treat them according to their
economics:

- ownership and economic interests determine attributable ounces;
- a gold stream or forward that transfers a quantifiable volume at a fixed or
  formula price belongs in the existing sold-ounce treatment;
- a royalty is an economic burden, not a transfer of geological ounces, and
  must not be converted into an invented ounce haircut;
- an undisclosed or unquantifiable encumbrance is `unknown`, not zero.

## 4. Capital: definitions before arithmetic

### 4.1 Rename the current field

The current `remaining_capex_aud_m` behaves as a **residual funding gap**: Rox
is zero because disclosed cash and drawable debt cover its project capital.
The name should eventually be migrated to `residual_funding_gap_aud_m` so that
funding capacity cannot be mistaken for economic capital still to be spent.

For a project `p`:

```text
RemainingExecutionCapex_p
    = latest disclosed spend from the as-of date to completion

AvailableProjectFunding_p
    = sourceable cash allocated to the project
    + committed undrawn facilities
    + other contracted funding

ResidualFundingGap_p
    = max(0, RemainingExecutionCapex_p − AvailableProjectFunding_p)
```

Only the last term belongs in Gate 2. Funding sources answer whether the plan
can be paid for; they do not make construction free.

### 4.2 Economic capital is project-wide, not optionality-only

If a DFS plant and mine plan process 674 koz of Reserves plus scheduled M&I and
Inferred material, the plant's capital does not belong only to the scheduled
non-reserve ounces. Labelling the whole project estimate as
`optionality_capital` creates a false attribution even when the denominator
eventually applies to the company's total claim.

The shadow measure should therefore be:

```text
ExecutionAdjustedEV_i
    = EV_i + Σ RemainingExecutionCapex_p

ExecutionAdjustedAUDPerClaimedOz_i
    = ExecutionAdjustedEV_i / ClaimedMoz_i
```

where the sum contains each material, not-yet-complete project scope once.
Do **not** add both remaining execution capital and residual funding gap. The gap
is a subset of the financing question, not additional construction spend.

For Rox this means the A$382.6m DFS estimate may be a legitimate estimate-date
input to a **whole-project execution-adjusted company metric**. It is not
legitimate as capital attached solely to 0.0596 confidence-weighted optional
Moz. The production weight remains on the current denominator while this is a
shadow report.

### 4.3 Treatment rules

1. **Define the scope first.** Use the issuer's material project, production
   target or separately costed expansion—not an index-invented asset boundary.
2. **Count spend once.** A plant serving Reserves, M&I and Inferred material is
   one capital scope, not three category allocations.
3. **Roll forward only from disclosure.** Subtract spent capital only when a
   source gives cumulative or period spend that can be reconciled to the study
   estimate. Otherwise preserve the estimate date and flag it stale/unknown.
4. **Do not subtract financing.** Cash coverage and undrawn debt reduce the
   funding gap, not remaining execution capital. Spending cash raises post-spend
   EV by reducing net cash; drawing debt raises it by increasing debt.
5. **Exclude sustaining capital after steady state.** It is paid from operating
   production and belongs to the operating-cost/survival analysis. Include only
   initial, restart or growth capital required to deliver the defined plan.
6. **Do not allocate shared capital pro rata to optional ounces.** Tonnes or
   ounces are not evidence of marginal capital causation. Use an issuer-disclosed
   incremental expansion figure or retain the whole-project scope.
7. **Unknown is not zero.** A producer without current project-capital disclosure
   receives no execution-adjusted metric; its production weight is unchanged.
8. **Avoid false comparability.** Never rank or weight a covered issuer against
   an uncovered issuer on the shadow denominator.

## 5. What is deliberately rejected

| Alternative | Decision | Reason |
|---|---|---|
| Binary asset eligibility gate | Reject | Deletes optionality according to disclosure format and makes the book reserves-only. |
| Evidence haircut or score | Reject | Double counts geological uncertainty already represented by category weights and rewards disclosure volume. |
| Count only scheduled optionality | Reject for production; report separately | A production target is evidence of scheduling, not the definition of a Mineral Resource. |
| Attach all project capex to scheduled optionality | Reject | The same plant and development commonly unlock Reserve and non-reserve material. |
| Set capital to zero when fully funded | Reject | Financing capacity does not remove the economic spend. |
| Add execution capital and residual gap | Reject | Counts the financing shortfall twice inside the same project cost. |
| Impute producer project capital | Reject | A cohort ratio would manufacture a denominator input with direct weight impact. |

## 6. Implementation sequence

### Phase A — evidence inventory, no engine reads

- Add `data/project_evidence.json` and a schema validator.
- Add a reconciliation tool proving that mapped plus unallocated category
  ounces do not exceed the canonical company ledger.
- Record evidence levels and capital dates from primary sources.
- Emit coverage tables from a standalone report tool.
- Assert mechanically that changing the evidence file cannot change a weight.

### Phase B — shadow capital report

- Rename or alias the current developer field as residual funding gap.
- Calculate execution-adjusted EV only for issuers with complete material-
  project coverage.
- Print current and execution-adjusted A$/claimed oz side by side.
- Keep missing coverage out of rankings and portfolio aggregates.
- Replay on one frozen market-data anchor and disclose the coverage boundary.

### Phase C — separate adoption decision

No production change is eligible for consideration until:

1. every eligible constituent has either complete sourceable coverage of its
   material not-yet-complete projects or an issuer source establishing that no
   such project exists;
2. every capital scope reconciles to a defined project or production target and
   is counted once;
3. no missing field defaults to zero and no capital amount is imputed;
4. producer and developer coverage is comparable rather than structurally
   determined by reporting style;
5. a deterministic same-market-data replay separates ledger, capital, caps and
   normalisation effects; and
6. the committee explicitly chooses whether execution-adjusted EV should
   replace—not supplement—the current residual-gap denominator.

If those conditions cannot be met, the shadow report remains the answer. A
useful limitation stated honestly is better than a precise weight built from an
unobservable input.

## 7. Required tests for Phases A and B

- Missing evidence leaves `ClaimedMoz`, raw weights and final weights unchanged.
- `mapped + unallocated` ounces reconcile to each company's canonical P&P,
  M&I non-reserve and Inferred totals within disclosed rounding tolerance.
- Evidence records cannot claim a category or ownership share absent from their
  cited primary source.
- A production target's scheduled category mix cannot exceed its mapped
  Resource by category.
- `unknown` capital is distinct from numeric zero in JSON, reports and CSV.
- Additional cash or committed debt reduces residual funding gap but does not
  reduce remaining execution capital.
- One project referenced by several categories adds capital exactly once.
- Capital shared by Reserve and non-reserve material is never labelled as
  optionality-only capital.
- M&I and Inferred remain in the sensitivity register.
- The production build is byte-for-byte unchanged when only the evidence overlay
  changes.

## 8. Proposed outcome

Approve Phases A and B as reporting work. Reject any immediate change to the
ounce ledger or weights.

This preserves the product's optionality thesis, uses the strongest evidence
the disclosure regime actually supplies, and turns capital into two auditable
facts instead of one overloaded field. It also makes the future decision
falsifiable: either complete project coverage supports an execution-adjusted
denominator, or the data demonstrates why that denominator cannot be applied
fairly across the book.
