# Major issues remediation plan

**Created:** 21 August 2026  
**Status:** in progress — issues 1–3 completed 21 August 2026. Issue 3 implements
the schema and engine split; generated weights remain the frozen baseline until
the coordinated replay in issue 5.

## Purpose

Remediate the major issues identified in the 21 August 2026 audit of the fresh
TWS build. A finding is major where it is a live construction defect, can
plausibly move a final weight by more than 0.5 percentage points, or can make a
Gate 2 conclusion unsound.

## Scope and baseline

The starting point is the TWS build generated at `2026-08-21T12:03:47Z`, with
eleven constituents. Preserve its generated outputs as the before-state for
every replay; do not snapshot it merely for code checking.

The issue-3 defect was the capital denominator: `remaining_capex_aud_m` served
both the developer funding-gap test and the all-in economic-cost denominator.
The approved target design is recorded in
`docs/asset-evidence-capital-proposal.md` and
`docs/capital-gate2-production-decision.md`.

## Plan

1. **Establish regression evidence — COMPLETE (21 August 2026).**
   - Capture the current per-name capital inputs, Gate 2 bridges, raw weights,
     cap effects, final weights, and exclusions as test fixtures.
   - Add regression checks for the current rejected-name reasons and for the
     current single-asset cap classifications.
   - Acceptance: a later replay can decompose every change into source-data,
     capital-model, Gate 2, normalisation, or cap effect.
   - Evidence: `tests/fixtures/2026-08-21-capital-baseline.json` freezes the
     `2026-08-21T12:03:47Z` build without creating a snapshot.
     `tools/regression.py --strict` verifies the fixture and reports later drift
     under the five acceptance categories above.

2. **Refresh the unresolved, load-bearing primary disclosures — COMPLETE
   (21 August 2026).**
   - Source Ramelius (RMS) FY26 commitments from its annual result.
   - Source Westgold (WGX) FY26 result / Strategic Outlook: complete execution
     capital, project scope, funding, and coverage period.
   - Recheck Northern Star (NST) and Greatland (GGP) qualifying facility terms
     and availability, because both currently depend on an undrawn facility in
     Gate 2.
   - Acceptance: every accepted value has primary provenance and an explicit
     evidence state; an unavailable value remains absent, not estimated.
   - Evidence: RMS Note 27 supplies a `POINT` A$79.218m of capital commitments
     within one year; it does not make the separate A$381m execution programme
     exact. NST's audited report confirms a `POINT` A$1.75bn undrawn through at
     least March 2030. GGP's executed facility announcement and June quarterly
     confirm a `POINT` A$475m undrawn, with the shorter tranche conservatively
     dated from 1 April 2031. WGX's result and Strategic Outlook had not been
     filed when rechecked; the superseded A$145m lower bound is removed, the
     capital amount and period remain `UNRESOLVED`, and its A$600m facility is
     explicitly `CARRY_FORWARD` with no term date and therefore no Gate 2 credit.

3. **Implement the capital-field split — COMPLETE (21 August 2026).**
   - Add schema and engine support for remaining execution capital, available
     project funding, and derived residual funding gap.
   - Use `EV + remaining execution capital` in the weight denominator for both
     producers and developers.
   - Use residual funding gap only in the developer Gate 2 test.
   - Validate `POINT`, `UPPER_BOUND`, `LOWER_BOUND`, `CARRY_FORWARD`, and
     `UNRESOLVED` evidence states. A lower bound must never reduce a
     denominator, and an unresolved field must never raise a weight.
   - Acceptance: the double-crediting of cash for developers is impossible and
     producer execution capital is treated under the same rule.
   - Evidence: `data/companies.json` now separates remaining execution capital
     from developer project funding and deletes `remaining_capex_aud_m`;
     `build_index.py` derives the residual gap for Gate 2 and adds only execution
     capital to all-in EV. Directional states fail closed, the two declared
     execution-capital parameters have named consumers, and
     `tests/test_execution_capital.py` covers the split and both sleeves.

4. **Make Gate 2 capital coverage explicit.**
   - Add per-project Gate 2 horizon start/end, coverage start/end, and
     committed-within-horizon capital records.
   - Implement the interval Gate 2 evaluator and reconcile its capital to the
     execution-capital record.
   - Require a load-bearing unresolved capital input to return `UNRESOLVED` and
     exclude the name rather than treating it as zero.
   - WGX remains ineligible unless its primary disclosure resolves both the
     execution-capital scope and within-horizon evidence.
   - Acceptance: under-coverage and over-coverage are detected, and a Gate 2
     pass cannot rely on a favourable missing amount.

5. **Replay and audit before activation.**
   - Fetch fresh TWS market data and run old-versus-new builds from the same
     inputs where possible.
   - Publish per-name old/new denominator, Gate 2 result, raw weight, cap
     effect, final weight, and reason for each move.
   - Investigate and document every final-weight move above 0.5 percentage
     points.
   - Run `tools/sensitivity.py`, `tools/gaps.py`, `tools/provenance.py`, and
     `tools/config_audit.py --strict`.
   - Acceptance: all configuration reads are observed; provenance and
     missing-data results meet repository rules; no unresolved input can
     favour a constituent.

6. **Reconcile documentation and obtain activation approval.**
   - Correct the obsolete statement in `index-methodology.md` that says the
     engine does not read facility term dates.
   - Correct the stale statement in `docs/execution-capital-inventory.md` that
     identifies EVN rather than WGX as the migration blocker.
   - Update the methodology amendment record, open-item register, and the
     capital decision document to match the approved implementation.
   - Obtain explicit approval for the coordinated methodology, engine, and data
     change before freezing a successful rebalance with `tools/snapshot.py`.

## Decision gates

- Do not invent an execution-capital total, spend-down, coverage period, or
  refinancing assumption.
- Do not activate a partial migration that treats one sleeve more favourably
  than another.
- Do not create a snapshot for a normal implementation check.
- The facility policy is a declared methodology choice. Reassess it only as an
  explicit policy decision, not as an ad hoc response to a constituent.
