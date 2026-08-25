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

| ASX | v2.0 | v2.1 | Change |
|---|---:|---:|---:|
| NST | 14.500% | 15.000% | +0.500 pp |
| EVN | 5.632% | 2.955% | −2.677 pp |
| CMM | 9.867% | 5.909% | −3.958 pp |
| GGP | 7.500% | 7.500% | 0.000 pp |
| GMD | 11.887% | 14.773% | +2.885 pp |
| RMS | 11.869% | 15.000% | +3.131 pp |
| RRL | 12.168% | 15.000% | +2.832 pp |
| WGX | 5.000% | 5.000% | 0.000 pp |
| VAU | 11.577% | 8.864% | −2.714 pp |
| CYL | 5.000% | 5.000% | 0.000 pp |
| RXL | 5.000% | 5.000% | 0.000 pp |

One-way target turnover is 9.35%, with no entries or exits. This is a
release-to-release comparison, so it includes both the weighting amendment and
the change from the 24 August market observations to the 25 August ASX closes.
No company-data field changed between the snapshots.

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
