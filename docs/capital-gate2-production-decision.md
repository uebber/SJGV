# Capital denominator and Gate 2 horizon — production decision

**Status:** **superseded in part by methodology v1.7, 21 August 2026.** The capital-denominator
decisions in §3 were implemented on 21 August 2026. **§1 decision 3 — making
horizon coverage a binding Gate 2 limb — is NOT accepted**, and the reason is
in the box below. The explicit per-project interval evaluator remains issue 4;
it was implemented before the issue-5 replay and remains as the v1.7 evidence
layer. The activated result is frozen in
`snapshots/2026-08-21-v1.7-health`.
**Origin:** PR #5, `agent/capital-gate2-fail-unfavourably`.
**Evidence cut-off:** 21 August 2026.
**Decision rule:** unavailable evidence may hold or reduce a constituent's
weight; it may never increase it.

> **v1.7 outcome.** The three-name interval replay demonstrated that complete
> two-year capital coverage was functioning as a disclosure gate rather than a
> health check. Directional evidence remains binding in the economic
> denominator. Producer Gate 2 now uses GREEN/AMBER/RED damage states and only
> RED excludes; incomplete commitment evidence is AMBER. Amendment 7 in the
> binding methodology controls wherever this historical decision differs.

---

> ### Why decision 3 was not accepted as written
>
> The directional state machine in §2 is the right idea and is better than the
> probe-based framing methodology §3.2 shipped with: an `UPPER_BOUND` can prove a
> pass, a `LOWER_BOUND` can only prove a failure, and neither requires inventing
> a burn rate. The problem is that **§4.1 applies it to one name and not to four
> others holding identical evidence.**
>
> §2 says a single guided year "is a `LOWER_BOUND` when further in-window spend
> may exist", and a `LOWER_BOUND` cannot prove a pass. **Seven constituents are in
> exactly that position.** The §4.1 table names WGX, GGP, EVN, CMM, RXL and GMD
> and is silent on NST, RRL, VAU and CYL — 40.5% of the book — whose committed
> capex is a single FY27 guidance figure charged against a two-year window.
>
> | Applying §2's rule | Result |
> |---|---|
> | As §4.1 tabulates it (WGX only) | 10 names, A$786/oz, 13.90pp |
> | **As §2 states it, applied evenly** | **4 names — EVN, GMD, RMS, RXL — Eff N 3.6, A$919/oz, 71.3pp** |
>
> Neither number is defensible on the strength of a table that does not mention
> the four names it decides. The horizon shortfall therefore remains **reported
> and not gated** under methodology §3.2, which prints it per name, and the
> decision is open rather than closed. What would settle it is disclosure, not
> argument: FY28 guidance from RRL, VAU, NST and CYL, and a scope total from WGX.
>
>
> **RESOLVED 20 August 2026 — methodology §3.2, amendment 5.** The limb binds, but
> on **materiality rather than coverage**. The guided annual leg is continued
> across the unsourced remainder of the window and the pass must survive it
> (`gate2.horizon_continuation_cover` = 1.0). That gates without grading
> disclosure format and without inventing a burn rate, because it uses only
> figures the issuer already published. Cover across the book runs 2.0× to 18.8×,
> so it binds on nobody today; it would have rejected PNR independently at 0.51×.
>
> WGX is reported `UNTESTED` — no established period means no leg to continue —
> and is routed to §12.2 item 6, where its trigger is the early-September
> Strategic Outlook. That is where the question always belonged: A$145m is not a
> short-period figure, it is an unresolved *scope*.
>
> §2's directional state machine stands as the design for the capital migration.
> §4.1 still needs re-tabling across all eleven constituents before any
> coverage-based version of it is revisited.

## 1. Decision

Ship the execution-capital denominator and the Gate 2 horizon correction as one
production change.

1. Replace `EV + residual funding gap` with
   `EV + remaining execution capital` for every sleeve.
2. Keep residual funding gap only in the developer survival test.
3. Make horizon coverage a Gate 2 evidence limb, not a report-only warning.
4. Interpret capital evidence by direction. A conservative upper bound can
   prove a denominator or a survival pass. A lower bound can prove a survival
   failure, but it cannot prove a pass and cannot enter the denominator.
5. Exclude a constituent when a load-bearing capital input is unresolved.
   Do not let one unresolved name block a correction for the rest of the book.
6. Count undrawn facilities according to the existing declared parameter and
   publish the dependency; do not change that parameter ad hoc for one name.

On the 20 August reviewer replay, the capital switch moves the headline from
**A$739 to A$775 per claimed ounce**, causes **1.40pp one-way turnover**, moves
GGP **-0.93pp**, and moves WGX **+0.53pp** if WGX is incorrectly entered at
zero. The last move is forbidden by decision 5.

Making the horizon limb binding leaves WGX `UNRESOLVED`, removes its **13.90pp**
position and produces the reviewer's **A$786/oz** headline before today's full
Westgold ledger is replayed. Those are transition diagnostics, not values to
hard-code in the engine or methodology.

## 2. One directional state machine for both defects

Capital is subtractive in Gate 2 and additive in the denominator. That gives
each evidence state a deterministic meaning.

| Evidence for capital | Denominator | Gate 2 conclusion |
|---|---|---|
| `POINT` | use | pass or fail |
| `UPPER_BOUND` | use; it can only reduce weight | a pass is proven; a failure is `UNRESOLVED` unless the exact value is sourced |
| `LOWER_BOUND` | forbidden | a failure is proven; a pass is `UNRESOLVED` |
| `CARRY_FORWARD` | use unchanged within the approved age limit | evaluate in its recorded direction; assume no spend-down |
| `UNRESOLVED` | forbidden | `UNRESOLVED` |

This handles under-coverage and over-coverage without extrapolation:

- a whole-project total extending beyond the two-year window is an
  `UPPER_BOUND` on within-horizon burn;
- a single year, one contract, one project leg, or a deferred smaller scope is a
  `LOWER_BOUND` when further in-window spend may exist; and
- calendar proration, cohort imputation and analyst phasing remain forbidden.

For a binary gate, `UNRESOLVED` is not a pass. The name is ineligible until a
primary source proves the required side of the test.

## 3. Capital denominator decisions

### 3.1 Correct the blocker

EVN is not the blocker. Its A$1,210m of gross board-approved project totals is a
poor but admissible `UPPER_BOUND`: treating all approved capital as remaining
omits no spend and can only raise the denominator. The initial capital switch
blocks on WGX among otherwise eligible constituents.

Once the Gate 2 horizon limb is binding, WGX is not eligible and therefore no
longer blocks the denominator migration for the names that pass. WGX may re-enter
only when both its execution-capital total and within-horizon burn resolve.

### 3.2 Capricorn

Use **A$593m** as `UPPER_BOUND`, being the issuer's own A$474m estimate at the
upper end of its disclosed ±25% accuracy range. Record `contingency_included =
false`; do not relabel A$474m as a point estimate when the same source says no
contingency is included.

This costs CMM about **0.3pp** in the reviewer replay and introduces no external
escalation or contingency assumption.

### 3.3 Greatland

The 29 July 2026 June-quarter/FY26 operating report reaffirms Havieron
pre-production capital at **A$1,065m** and explicitly repeats the **June 2025
cost-estimate base date**. It does not disclose escalation.

Use A$1,065m unchanged for the migration, with the cost-base date visible and no
assumed spend-down. Re-source the audited FY26 result when filed. A later filing
may hold or raise the amount; absence of an update may not lower it.

Primary source: [Greatland June 2026 Quarterly Activities Report](https://company-announcements.afr.com/asx/ggp/cbe83fbc-8ad3-11f1-a7a9-262857e3edca.pdf).

### 3.4 Westgold

Do not enter WGX at zero and do not retain A$145m as execution capital. The
approved 2.6 Mtpa Higginsville stage is under review in favour of a larger,
uncosted 4 Mtpa case, while additional Murchison milling capacity is described
as committed or planned without a disclosed total. A$145m is therefore a
`LOWER_BOUND`, not a conservative carry-forward.

The FY26 financial result and Strategic Outlook are event-driven sourcing
triggers. The ASX feed was rechecked on 21 August 2026 and neither had been filed;
the 18 August Fletcher announcement points to the Strategic Outlook in early
September. The stale A$145m Gate 2 field has therefore been removed rather than
carried as a favourable lower bound. Until the filings provide a complete total,
funding and coverage, WGX remains `UNRESOLVED`.

## 4. Gate 2 horizon decision

Add these fields to every producer project record:

```text
gate2_horizon_start
gate2_horizon_end
committed_within_gate2_horizon_aud_m
committed_capex_state
coverage_start
coverage_end
coverage_note
```

The engine must reject a claimed `POINT` whose coverage does not span the whole
Gate 2 window. It must also reconcile the horizon amount to the same project
record used for remaining execution capital.

Evaluation is interval-based, not imputed:

```text
ending_liquidity(capex)
    = opening_liquidity
    + stressed_free_cash_flow
    + counted_undrawn_facilities
    - capex

POINT:        evaluate at capex
UPPER_BOUND:  PASS only if ending_liquidity(upper) >= 0
LOWER_BOUND:  FAIL only if ending_liquidity(lower) < 0
otherwise:    UNRESOLVED
```

### 4.1 Current name-level consequences

| Name | Current horizon evidence | Decision |
|---|---|---|
| WGX | A$145m has no period and is superseded by larger uncosted scopes | `UNRESOLVED`; exclude |
| GGP | whole-project total includes roughly A$200m beyond the window | `UPPER_BOUND`; a pass remains valid, but source exact phasing |
| EVN | A$1,210m includes long-dated Cowal and E22 spend | `UPPER_BOUND`; a pass with facilities remains valid, but cash-only status is not exact |
| CMM / RXL / GMD | completion lies inside the window | `POINT`, subject to project reconciliation |

For EVN, the strict current bridge is about **-A$102m**; removing only the
sourceable out-of-window Cowal portion gives about **+A$202m** before undrawn
facilities. This is why `gate2.count_undrawn_facilities` appears to decide EVN
under the over-covered record. The parameter remains real, but its current
4.47pp effect must be published as contingent on horizon input quality.

## 5. Westgold data update on 20 August

Westgold's complete FY26 group Mineral Resource and Ore Reserve statement was
filed on 20 August. It closes the Fletcher supersession gap without splicing one
deposit into a stale group total.

| Ledger field | FY25 record | FY26 group statement |
|---|---:|---:|
| P&P | 3.500 Moz | 4.068 Moz |
| M&I non-reserve | 5.700 Moz | 4.926 Moz |
| Inferred | 7.100 Moz | 5.362 Moz |
| Claimed ounces at 1.0 / 0.5 / 0.2 | 7.770 Moz | 7.603 Moz |
| Reserve price ceiling | A$3,800/oz | A$4,800/oz |

Claimed ounces fall **2.14%**. At a 13.90% starting weight, the isolated
normalisation effect is approximately **-0.26pp**, before caps and the other
changes in this proposal. The earlier Fletcher-only `+1.10pp` indication is
superseded: it assumed the rest of the group stood still across a year of
depletion and divestments.

Primary source: [Westgold 2026 Mineral Resource Estimate and Ore Reserves](https://company-announcements.afr.com/asx/wgx/4d1d9bf5-9c19-11f1-a8a8-8a2df0d88e09.pdf).

This filing closes only the resource-ledger unknown. It does not supply the
missing capital totals, project phasing, or cash/bullion/liquid-investment split.

## 6. Correlated unknowns

Add a per-constituent data-quality report that groups every load-bearing unknown
by direction. It is a diagnostic, not a score or haircut.

```text
ticker
field
state
direction_if_missing   # flatters / penalises / neutral
gate_or_formula_consumer
next_primary_source
deadline
```

If any unresolved field can flatter the same constituent in a gate or weight,
the constituent cannot enter or increase at the rebalance. Multiple favourable
unknowns are not assumed independent and do not cancel a conservative field.

For WGX, the current set is:

- execution capital: unresolved and flattering;
- Gate 2 horizon burn: unresolved and flattering;
- treasury composition: unresolved and flattering;
- 4 Mtpa / Murchison replacement scope: unresolved and flattering.

The FY26 group resource statement is now closed and should be removed from that
list.

## 7. EVN facility parameter

Keep `gate2.count_undrawn_facilities` as the declared methodology decision. Add
two outputs for every producer:

- verdict and ending liquidity with facilities; and
- verdict and ending liquidity on cash alone.

Flag a constituent as `PARAMETER_DEPENDENT` when those verdicts differ. Do not
change the parameter because one constituent is large, and do not describe a
parameter-dependent pass as unconditional. Recompute EVN after the horizon
bridge is corrected.

## 8. Implementation order

1. Land the Westgold FY26 group ledger from the 20 August primary filing.
2. Add the project capital schema and directional state validation.
3. Add horizon coverage fields and the interval Gate 2 evaluator.
4. Re-source the WGX financial result and Strategic Outlook; re-source GGP at
   the audited FY26 result.
5. Run one frozen replay with old and new denominators, Gate 2 states, raw
   weights, cap effects and final weights.
6. Activate the horizon limb and capital denominator together. WGX is excluded
   if it remains unresolved; absence never becomes zero.

## 9. Required tests

- A missing execution-capital total cannot increase a raw or final weight.
- A lower bound cannot enter the denominator.
- A Gate 2 pass on a lower-bound capex input returns `UNRESOLVED`.
- A Gate 2 pass on an upper-bound capex input remains `PASS`.
- A Gate 2 failure on an upper bound returns `UNRESOLVED`, not `FAIL`.
- Under-coverage and over-coverage are both detected from explicit dates.
- Whole-project and within-horizon capital reconcile to one project record.
- WGX at zero is rejected by schema validation.
- EVN A$1,210m is accepted as an upper bound, not recorded as a blocker.
- CMM A$593m is accepted as the issuer-derived upper bound; A$474m cannot be
  labelled `POINT` while `contingency_included` is false.
- GGP's cost-base date is mandatory and cannot be silently advanced.
- A current group statement supersedes every old group ledger tranche together;
  a single-deposit splice fails validation.
- Facility-dependent Gate 2 passes are printed explicitly.

## 10. Approval requested

Approve the directional evidence rule, make horizon coverage binding, exclude
WGX while its load-bearing capital inputs remain unresolved, admit EVN's gross
upper bound, use CMM's A$593m issuer bound, and migrate the capital denominator
for the remaining eligible book.

This is the smallest rule set that fixes both directions of the horizon defect,
ships the largest denominator correction, and guarantees that missing data can
never make a position larger.
