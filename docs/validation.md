# SJGV v2.0 release validation

The authoritative release is
[`../snapshots/2026-08-24-v2.0`](../snapshots/2026-08-24-v2.0). Its manifest
identifies engine commit `3398b1a3cb745b11e7b21505c1dbd7b2f812b93b`, the
recorded market session, copied inputs and output hashes.

## Frozen result

| Measure | Result |
|---|---:|
| Constituents | 11 |
| A$ per claimed ounce | 922.23 |
| Gate-1 cap-weighted A$ per claimed ounce | 1,027.57 |
| Effective N | 9.66 |
| Dimson gold beta | 1.72 |
| Weighted beta R² | 0.21 |
| Top weight | 14.50% |
| Developer sleeve | 5.00% |
| Oldest counted statement | 13.01 months |
| Reported capacity, binding estimate | A$24.10m |

The market bundle records 50 requests, 36 series and 12,005 historical-bar
rows. Prices came from the same session for the primary and comparison indices.
The snapshot contains no methodology claim about future return.

## Reproduction boundary

The snapshot reproduces the release without contacting IBKR because it retains
the point-in-time market and input artifacts. A new live build is a new
observation and need not reproduce the old weights.

There is no historical backtest. The point-in-time reserve/resource categories,
hedges, share counts, balance sheets and disclosure gaps required for a clean
simulation do not exist for prior dates. Current data must not be projected
backward.

## Repository checks

Run with the repository interpreter:

```sh
.venv/bin/python -m compileall -q build_index.py nav_model.py tools
.venv/bin/python -m unittest discover -s tests -t .
.venv/bin/python tools/gaps.py
.venv/bin/python tools/provenance.py
.venv/bin/python tools/config_audit.py --strict
.venv/bin/python tools/kb.py audit --strict
```

A normal live build additionally requires an IBKR TWS/Gateway session. It
rewrites ignored root outputs and is not a release snapshot until explicitly
frozen with `tools/snapshot.py` after review.
