# Issue 5 replay and activation audit

**Date:** 21 August 2026
**Status:** complete — v1.7 activated and snapshotted.

> This report preserves the rejected v1.6 capital-coverage replay. Its
> three-name, cap-infeasible result triggered the first-principles review that
> produced v1.7. It is historical evidence, not the current target build.

## v1.7 activation replay

The definitive TWS session ran from `2026-08-21T18:15:55Z` to
`18:16:51Z`. The
approved health formulation restores a feasible twelve-name book with effective
N 11.1, portfolio beta 1.76, and A$826 per claimed ounce. Every declared
configuration read was observed and no final weight breaches its cap. The exact
build and €1m basket are frozen in
`snapshots/2026-08-21-v1.7-health`; its market-data integrity check passes.

| Ticker | Health | Rescue A$m | Rescue / mcap | Recovery years | Final weight |
|---|---|---:|---:|---:|---:|
| NST | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 11.82% |
| EVN | GREEN | 0 | 0.0% | 0.0 | 4.48% |
| CMM | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 7.50% |
| GGP | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 8.39% |
| GMD | GREEN | 0 | 0.0% | 0.0 | 9.75% |
| RMS | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 9.25% |
| RRL | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 9.81% |
| VAU | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 9.61% |
| OBM | AMBER — bounded rescue | 167 | 5.3% | 0.61 | 4.41% |
| CYL | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 10.00% |
| PNR | AMBER — incomplete commitments | 0 | 0.0% | 0.0 | 10.00% |
| RXL | Developer D1–D3 pass | — | — | — | 5.00% |

No producer is RED. WGX and BGL remain excluded because their economic
execution-capital denominator is unresolved; BC8 lacks both AISC and a safe
execution-capital value. AAR and AUC fail the existing developer test. These
five exclusions are independent of incomplete two-year producer guidance.

Final verification passed 17 focused tests, compilation, strict configuration
audit (58 of 58 reads observed), and deterministic replay with zero weight
difference. Provenance is 376 of 377 fields primary, with no non-primary field
on a weighted name. The gap audit reports 5 clean, 8 partial and 4 blocked;
the eight partial names are explicitly AMBER rather than silently complete.

Relative to the v1.6 snapshot, one-way turnover is 14.86%. Every move above
0.5pp is explained:

| Ticker | v1.6 | v1.7 | Move | Explanation |
|---|---:|---:|---:|---|
| WGX | 13.66% | — | −13.66pp | Exits because economic execution capital remains unresolved; this is a denominator failure, not a health-gate failure |
| PNR | — | 10.00% | +10.00pp | Returns because both ends of its published AISC range are AMBER rather than existential under the health test; the single-asset cap binds |
| OBM | — | 4.41% | +4.41pp | Returns because its A$167m rescue need is manageable at 5.3% of market cap and 0.61 recovery years |
| GGP | 9.20% | 8.39% | −0.81pp | Capital enters its denominator and the two entries change normalisation |

## Rejected v1.6 replay inputs and limitation

The rejected v1.6 TWS build completed at `2026-08-21T13:45:32Z` and had three
survivors. Those temporary root artifacts have since been replaced by the
activated v1.7 build. The preceding 12:03:47Z build is frozen in the regression
fixture.
`tools/replay.py` additionally reconstructs a build from a recorded bundle and
bars without contacting TWS, so formula/data changes can be checked on exactly
identical market inputs. No snapshot was created for the rejected result.

## v1.6 baseline versus rejected strict replay, identical market inputs

Amounts are A$m; weights are final weights. `—` means the name is not in the
respective weighted book. The old output is the frozen 12:03:47Z fixture; the
strict output is the rejected 13:45:32Z build. All Gate 2 changes below are the
interval evaluator failing closed on a lower-bound or unresolved adverse
capital amount. The regression output contains the full raw-score and cap
bridge; for the survivors it is EVN `0.000496 → 0.000477`, cap effect `+0.72pp
→ +25.93pp`; GMD `0.001069 → 0.001038`, `+1.56pp → +6.02pp`; and RXL
`0.001967 → 0.001303`, `−9.98pp → −31.96pp`.

| Ticker | Old denominator | New denominator | Old final | New final | New Gate 2 / move reason |
|---|---:|---:|---:|---:|---|
| AAR | — | — | — | — | Still rejected: D2 and D3 fail |
| AUC | — | — | — | — | Still rejected: D2; D3 interval is unresolved |
| BC8 | — | — | — | — | UNRESOLVED: no usable within-horizon capital |
| BGL | — | — | — | — | Fails at A$90m lower capital edge |
| CMM | 7,523 | — | 7.81% | — | UNRESOLVED: A$426m is only a lower bound |
| CYL | 1,462 | — | 10.00% | — | UNRESOLVED: A$22m is only a lower bound |
| EVN | 31,158 | 32,368 | 4.50% | 42.86% | Execution capital adds A$1,210m; only three survivors remain |
| GGP | 7,829 | — | 9.21% | — | UNRESOLVED: A$315m is only a lower bound |
| GMD | 9,371 | 9,651 | 9.70% | 42.86% | Execution capital adds A$280m; only three survivors remain |
| NST | 33,589 | — | 11.58% | — | UNRESOLVED: A$350m is only a lower bound |
| OBM | — | — | — | — | Still fails, now proved at A$455m lower edge |
| PNR | — | — | — | — | UNRESOLVED: A$101m is only a lower bound |
| RMS | 6,869 | — | 9.43% | — | UNRESOLVED: A$79m is only a lower bound |
| RRL | 5,314 | — | 9.48% | — | UNRESOLVED: A$250m is only a lower bound |
| RXL | 628 | 947 | 5.00% | 14.29% | Execution capital adds A$320m; only three survivors remain |
| VAU | 6,111 | — | 9.43% | — | UNRESOLVED: A$173m is only a lower bound |
| WGX | 4,982 | — | 13.85% | — | UNRESOLVED: no usable within-horizon capital |

Every final-weight movement exceeds 0.5pp because eight former constituents
are excluded by the required fail-closed Gate 2 treatment. It is not an
unexplained normalisation or cap effect. Among the three survivors, the new
raw weights are EVN 47.70%, GMD 103.80%, and RXL 130.31%; the 42.86% / 42.86% /
14.29% final weights are the existing 15% name / 10% single-asset caps and
redistribution. This concentrated, incomplete book is evidence against
activation, not a candidate rebalance.

## Audit results

- `tools/config_audit.py --strict`: pass; all 55 configuration parameters
  were observed in the deterministic replay.
- `tools/gaps.py`: 5 clean, 12 blocked. The blocked names correspond to the
  unresolved Gate 2 capital coverage above; no absent capital was treated as
  zero.
- `tools/provenance.py`: 376 of 377 values primary; the sole secondary field is
  AUC approvals/land on an unweighted name. There are no non-primary gate
  inputs on weighted names.
- `tools/sensitivity.py --threshold 0.2`: no parameterised missing-data gap
  moves this three-name replay; the live single-asset classification effect is
  9.524pp for EVN or GMD if misclassified, so this remains a material sourced
  control rather than a closed gap.

## Historical disposition

`tools/regression.py --strict` intentionally exits non-zero: it records 260
explained changes, including the documented rejected-name reasons above. The
strict build, sensitivity, gaps, provenance, and config audit were completed.
The result was correctly not snapshotted. The subsequent v1.7 amendment and
activation replaced it with the health-check result documented at the top.
