# SJGV v2.1 release validation

The authoritative release is
[`../snapshots/2026-08-25-v2.1`](../snapshots/2026-08-25-v2.1). Its manifest
identifies engine commit `ca0fc26c369504bb3016bf28fb3c8e89f1ba75a2`, the
recorded market session, copied inputs and output hashes.

## Frozen result

| Measure | Result |
|---|---:|
| Constituents | 11 |
| A$ per claimed ounce | 908.66 |
| Gate-1 cap-weighted A$ per claimed ounce | 1,036.71 |
| Effective N | 8.72 |
| Dimson gold beta | 1.72 |
| Weighted beta R² | 0.21 |
| Top weight | 15.00% |
| Developer sleeve | 5.00% |
| Oldest counted statement | 13.01 months |
| Reported capacity, binding estimate | A$24.72m |

The market bundle records 50 requests, 36 series and 12,022 historical-bar
rows. All 17 candidate equity prices are `histDailyClose` observations dated
25 August 2026 from TWS-qualified ASX contracts. Quote fields were retained as
cross-checks and did not set a weight. The primary and Gate-1 comparison indices
use the same closing prices.

## Change from v2.0

Version 2.1 replaces magnitude-proportional signal weights with descending
linear rank weights. It also standardises the equity price input on the latest
ASX daily close rather than a quote-first fallback ladder. Eligibility, the
ounce ledger and the portfolio caps are unchanged.

To isolate the weighting amendment, both target columns below use the identical
v2.1 company data and 25 August TWS ASX closes. The v2.0 column is the
magnitude-proportional method reapplied to those common inputs, not the
historical 24 August v2.0 release. Rows are ordered by v2.1 target weight, then
alphabetically for ties.

| ASX | v2.0 method | v2.1 method | Change | Gold/EV |
|---|---:|---:|---:|---:|
| NST | 14.411% | 15.000% | +0.589 pp | 1,241.3 |
| RMS | 12.029% | 15.000% | +2.971 pp | 1,036.2 |
| RRL | 12.181% | 15.000% | +2.819 pp | 1,049.3 |
| GMD | 11.889% | 14.773% | +2.884 pp | 1,024.1 |
| VAU | 11.569% | 8.864% | −2.705 pp | 996.5 |
| GGP | 7.500% | 7.500% | 0.000 pp | 1,007.6 |
| CMM | 9.863% | 5.909% | −3.954 pp | 849.6 |
| CYL | 5.000% | 5.000% | 0.000 pp | 1,756.1 |
| RXL | 5.000% | 5.000% | 0.000 pp | 1,239.3 |
| WGX | 5.000% | 5.000% | 0.000 pp | 1,443.8 |
| EVN | 5.557% | 2.955% | −2.603 pp | 478.7 |

`Gold/EV` is confidence-weighted claimed unhedged ounces per A$1 million of
funded enterprise value, so higher is cheaper. It is one common input to both
methods, scaled into readable units. Neither frozen snapshot contains a sourced
earnings or EPS field, so a P/E ratio is omitted rather than retrospectively
invented.

One-way target turnover caused by the weighting amendment alone is 9.26%, with
no entries or exits.

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
v2.1 input check.
