# Gate 2 capital-resilience coverage audit — 21 August 2026

**Status:** historical Phase 1 baseline audit of the superseded continuous
design. Its coverage findings led to the simpler replacement now in
`docs/gate2-continuous-capital-resilience-plan.md`. It does not change company
data, Gate 2, weights, methodology, or the frozen v1.7 snapshot.

## Baseline controls

- Worktree at audit: `287eb60` plus the untracked implementation plan and this
  Phase 1 work.
- The frozen `2026-08-21-v1.7-health` bundle replayed exactly with
  `tools/replay.py`: sorted ticker/weight difference was empty.
- Before-change checks passed: unit tests (17), compile, gaps, provenance and
  strict configuration audit.
- The methodology/configuration divergence is recorded: methodology §3.2 still
  specifies `gate2.horizon_continuation_cover`, while neither configuration nor
  engine consumes it; eight records retain historical `annual_leg_aud_m`.
  This audit does not treat a clean configuration audit as resolving that
  divergence.

## Required pack

The live continuous score requires all of the following for an admitted
producer-path company:

1. compatible actual operating volume and AISC with machine-readable period,
   attribution and produced-versus-sold bases;
2. a common balance-sheet measurement date;
3. unrestricted cash and liquid bullion at that date;
4. a sourced debt principal-and-interest outflow schedule for the build-date
   two-year horizon;
5. a sourced contractual-capital-commitment schedule, with timing and an
   outside-AISC reconciliation; and
6. a sourced roll-forward from that common date to the build-date stress start
   where the two differ.

Facilities are only a financing-split diagnostic. Existing issuer-defined net
debt is retained for funded EV but cannot substitute for separate cash and
debt-cash-outflow inputs. The existing project ledger cannot substitute for a
contractual commitment schedule: in particular, a `LOWER_BOUND` tail is not a
finite adverse bound and cannot support a positive continuous multiplier.

## Current coverage matrix

`READY` means the current field has the proposed shape and a usable value;
`MISSING` means it is absent, unresolved, or only represented in prose/legacy
fields. The table is generated reproducibly by:

```sh
.venv/bin/python tools/gate2_coverage.py --markdown
```

| Ticker | Sleeve | Volume | AISC | Operating basis | Common balance-sheet date | Cash | Debt-outflow schedule | Commitment schedule | Roll-forward | Facility diagnostic | Core-pack result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NST | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| EVN | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| CMM | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| GGP | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| GMD | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| RMS | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| RRL | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| WGX | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| VAU | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| BGL | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | UNTESTED |
| OBM | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| CYL | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| PNR | producer | READY | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |
| BC8 | near_producer | READY | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING | READY | UNTESTED |

No producer-path candidate is admitted. BC8 also lacks an AISC and remains
outside the producer model. Existing notes state operating bases for many
companies, but the required period/attribution/ounce-basis facts are prose;
they cannot be mechanically reconciled and therefore do not meet §5.6(4).

## Existing v1.7 commitment evidence

The frozen v1.7 health snapshot demonstrates why this migration is a hard gate,
not a numerical haircut. Eight producer records had a `LOWER_BOUND` project
capital interval and comprised 76.36% of frozen final weight. Their current
v1.7 lower endpoint is diagnostic only for the new score:

| Ticker | Frozen weight | v1.7 capital state | Lower disclosed A$m | Why not a v1.8 live commitment input |
|---|---:|---|---:|---|
| NST | 11.82% | LOWER_BOUND | 350.0 | FY27 guidance leaves FY28 tail unresolved |
| CMM | 7.50% | LOWER_BOUND | 425.5 | One project tail is unresolved; known upper edge was previously discarded |
| GGP | 8.39% | LOWER_BOUND | 315.0 | Telfer lower-bound tail; aggregate also discarded Havieron's known adverse edge |
| RMS | 9.25% | LOWER_BOUND | 79.2 | One-year commitments disclosure only |
| RRL | 9.81% | LOWER_BOUND | 250.0 | One-year guidance only |
| VAU | 9.61% | LOWER_BOUND | 173.0 | One-year growth guidance tail unresolved |
| CYL | 10.00% | LOWER_BOUND | 22.0 | One-year contracted-capital disclosure only |
| PNR | 10.00% | LOWER_BOUND | 101.0 | One-year guided growth spend is not a contractual two-year schedule |

EVN's `UPPER_BOUND`, GMD's `POINT`, and OBM's `POINT` commitment intervals are
not enough to admit them: the new cash, debt, common-date and operating-basis
requirements are also absent. Under the superseded §11.2 finite-bound rule, none of the
current data can be converted into a continuous score by a fallback to net debt,
an annualised guidance leg, or terminal-only timing.

## Result and next gate

The required default ASX producer pack is not represented in the current schema,
so a §5 prototype would be wholly `UNTESTED` and would not establish a formula
or cap effect. The plan therefore stops before production-engine integration and
company-data migration.

The next authorised implementation step is a primary-document availability
audit for each candidate's annual/interim balance sheet, financial-liability
maturity note and contractual commitments note. It must establish whether a
common-date, finite conservative schedule can be sourced. If the pack is not
routinely available, the plan requires proposing the narrowest fallback before
changing `data/companies.json` or live weighting behaviour.
