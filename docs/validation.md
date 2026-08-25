# SJGV v2.2 release validation

The authoritative release is
[`../snapshots/2026-08-25-v2.2`](../snapshots/2026-08-25-v2.2). Its manifest
identifies engine tree `68d707cc1f8e8569ab43805760a9ba60c9630e57-dirty`,
the recorded market session, copied inputs and output hashes. The `-dirty`
suffix records that the v2.2 implementation had not yet been committed when
the release was frozen; it must not be mistaken for a clean reproducible commit.

## Frozen result

| Measure | Result |
|---|---:|
| Eligible constituents / positive weights | 11 / 10 |
| A$ per claimed ounce | 874.30 |
| Claimed ounces per A$1m funded EV | 1,143.78 |
| Gate-1 cap-weighted A$ per claimed ounce | 1,036.71 |
| Effective N | 7.15 |
| Required effective N | 7.15 (65% × 11) |
| Dimson gold beta | 1.70 |
| Weighted beta R² | 0.21 |
| Top weight | 25.04% |
| Developer sleeve | 5.00% |
| Modelled gamma | approximately zero |
| Oldest counted statement | 13.01 months |
| Reported capacity, binding estimate | A$24.72m |

The market bundle records 50 requests, 36 series and 12,022 historical-bar
rows. All 17 candidate equity prices are `histDailyClose` observations dated
25 August 2026 from TWS-qualified ASX contracts. Quote fields were retained as
cross-checks and did not set a weight. The primary and Gate-1 comparison indices
use the same closing prices.

## Change from v2.1

Version 2.2 replaces descending-linear-rank sizing and the general 15% company
cap with a convex optimisation:

```text
maximise sum(weight_i × claimed_ounces_i / funded_EV_i)
subject to effective N >= 65% × eligible N
           and the 7.5% single-asset, 5% delivery/developer,
           and 15% aggregate developer caps
```

The comparison below holds company data and 25 August TWS ASX closes constant,
so only the weighting amendment moves target weights. `Gold/EV` is claimed
unhedged ounces per A$1 million of funded enterprise value; higher is cheaper.

| ASX | v2.1 weight | v2.2 weight | Change | Gold/EV |
|---|---:|---:|---:|---:|
| NST | 15.000% | 25.042% | +10.042 pp | 1,241.3 |
| RRL | 15.000% | 13.873% | −1.127 pp | 1,049.3 |
| RMS | 15.000% | 13.112% | −1.888 pp | 1,036.2 |
| GMD | 14.773% | 12.409% | −2.363 pp | 1,024.1 |
| VAU | 8.864% | 10.806% | +1.942 pp | 996.5 |
| GGP | 7.500% | 7.500% | 0.000 pp | 1,007.6 |
| CYL | 5.000% | 5.000% | 0.000 pp | 1,756.1 |
| WGX | 5.000% | 5.000% | 0.000 pp | 1,443.8 |
| RXL | 5.000% | 5.000% | 0.000 pp | 1,239.3 |
| CMM | 5.909% | 2.258% | −3.652 pp | 849.6 |
| EVN | 2.955% | 0.000% | −2.955 pp | 478.7 |

The amendment increases portfolio Gold/EV from 1,100.52 to 1,143.78 ounces per
A$1 million, a 3.93% improvement. A$ per claimed ounce falls from 908.66 to
874.30. Effective N moves from 8.72 to the binding 7.15 floor. One-way target
turnover is 11.98%, with no eligibility entries or exits; EVN remains an
eligible constituent but receives zero optimal weight.

Company and portfolio gamma are economically zero under the fixed-mine-plan NAV
model. The reported values are floating-point noise, not evidence that real
mine equity has no convexity; the disclosed inputs cannot model price-dependent
cut-off grades or reserve conversion.

## Reproduction boundary

The snapshot retains the point-in-time company data, guidance ratings, config,
TWS market bundle, daily bars, weights and sized baskets. `tools/replay.py` can
apply a later engine to those recorded observations without contacting TWS, but
such a replay is a diagnostic and not a new live release.

There is no historical backtest. The point-in-time reserve/resource categories,
hedges, share counts, balance sheets and disclosure gaps required for a clean
simulation do not exist for prior dates. Current data must not be projected
backward.

## Repository checks

The release passed:

```sh
.venv/bin/python -m compileall -q build_index.py nav_model.py tools
.venv/bin/python -m unittest discover -s tests -t .
.venv/bin/python tools/gaps.py
.venv/bin/python tools/provenance.py
.venv/bin/python tools/config_audit.py --strict
.venv/bin/python tools/kb.py audit --strict
```

The strict knowledge-store audit reported no errors. Its warnings describe the
document store's recorded operating boundary, chiefly local-only source bytes
and grandfathered legacy citation granularity; they do not indicate a failed
v2.2 input check.
