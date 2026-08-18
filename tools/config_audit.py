#!/usr/bin/env python3
"""
Cross-check data/config.json against the code that is supposed to read it.

    python tools/config_audit.py            # the register, grouped by verdict
    python tools/config_audit.py --json     # machine-readable
    python tools/config_audit.py --strict   # exit 1 on any finding

WHAT THIS EXISTS TO STOP
------------------------
A parameter declared in config.json, cited to a methodology section, and read by
no code at all. It has happened three times:

  1. producer_max_spread_pct / developer_max_spread_pct — Gate 3 had never run.
     Eight of fourteen names were carrying an untested tradability gate.
  2. min_r2_gold, max_idio_variance_contribution, max_single_asset,
     sigma_idio_basis, parameters_adopted — all since withdrawn,
     capacity_max_days_advt, capacity_max_participation — five at once, found
     17 Aug 2026. One of them (the idio cap) was breached by more than double.
  3. confidence_weights, risk.regression_window, gates.spread_window — declared
     in config AND hardcoded in the engine, holding the same values by luck.
     Editing the declared copy would have changed nothing, silently.

The failure is worse than a missing parameter, because the methodology then
states that the index enforces something it does not, and everyone downstream
believes it. tools/gaps.py already closes this hole for companies.json by
importing KNOWN_FIELDS and checking both directions. This is the same idea for
config.json, and it checks a third direction the static lists cannot:

  DECLARED   every parameter in config.json must be claimed by a consumer in
             build_index_v2.CONFIG_PARAMS.
  STALE      every claim must point at a parameter that still exists.
  OBSERVED   every claim of "engine" must show up in the reads a real build
             actually recorded (weights_v2.json → config_reads_observed).
             This is the half that cannot be faked by writing a confident list.
  UNDECLARED the engine must not read a key config.json does not define, or a
             hardcoded default is quietly deciding the answer.

Run it after every config edit and before every rebalance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_index_v2 as B  # noqa: E402

CONFIG = ROOT / "data" / "config.json"
LAST_RUN = ROOT / "weights_v2.json"

VERDICTS = {
    "unclaimed": ("BLOCK", "declared in config.json, no consumer claims it"),
    "stale": ("BLOCK", "claimed by a consumer, absent from config.json"),
    "unread": ("BLOCK", "claimed as engine-read, not read by the last build"),
    "undeclared": ("BLOCK", "read by the engine, not defined in config.json"),
    "unverified": ("WARN", "claimed as engine-read, no build output to check against"),
    "process": ("note", "no code reads it, by decision"),
}


def load_observed() -> tuple[set[str], set[str], str | None]:
    """What the last recorded build actually touched."""
    if not LAST_RUN.exists():
        return set(), set(), None
    data = json.loads(LAST_RUN.read_text())
    return (set(data.get("config_reads_observed") or []),
            set(data.get("config_keys_missing") or []),
            data.get("generated_utc"))


def audit() -> dict:
    cfg = json.loads(CONFIG.read_text())
    declared = B.config_leaves(cfg)
    observed, missed, run_at = load_observed()

    findings: list[dict] = []
    by_consumer: dict[str, list[str]] = {}

    for path in declared:
        claim = B.claimed_by(path)
        if claim is None:
            findings.append({"path": path, "verdict": "unclaimed",
                             "detail": "add it to CONFIG_PARAMS, or rename it to "
                                       "end in _note if it is rationale"})
            continue
        consumer, what = claim
        by_consumer.setdefault(consumer, []).append(path)
        if consumer != "engine":
            continue
        if not observed:
            findings.append({"path": path, "verdict": "unverified",
                             "detail": "no weights_v2.json — run a build"})
        elif path not in observed:
            findings.append({"path": path, "verdict": "unread",
                             "detail": f"claims to be read for: {what}"})

    declared_set = set(declared)
    for path, (consumer, what) in B.CONFIG_PARAMS.items():
        if path.endswith(".*"):
            prefix = path[:-1]
            if not any(d.startswith(prefix) for d in declared_set):
                findings.append({"path": path, "verdict": "stale",
                                 "detail": f"claimed by {consumer} for: {what}"})
            continue
        if path not in declared_set:
            findings.append({"path": path, "verdict": "stale",
                             "detail": f"claimed by {consumer} for: {what}"})

    for path in sorted(missed):
        findings.append({"path": path, "verdict": "undeclared",
                         "detail": "the engine's hardcoded default decided this"})

    order = {"unclaimed": 0, "undeclared": 1, "unread": 2, "stale": 3, "unverified": 4}
    findings.sort(key=lambda f: (order.get(f["verdict"], 9), f["path"]))
    return {"findings": findings, "declared": declared, "observed_at": run_at,
            "by_consumer": by_consumer, "n_observed": len(observed)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit data/config.json against the code.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    args = ap.parse_args()

    result = audit()
    if args.json:
        print(json.dumps(result, indent=2))
        return 1 if (args.strict and result["findings"]) else 0

    print(f"\nSJGV config audit — {len(result['declared'])} parameters in "
          f"data/config.json")
    if result["observed_at"]:
        print(f"  checked against the build of {result['observed_at'][:19]}Z "
              f"({result['n_observed']} config reads recorded)")
    else:
        print("  NO BUILD OUTPUT — run build_index_v2.py first; without it the "
              "engine-read claims cannot be verified, only trusted.")

    for consumer, paths in sorted(result["by_consumer"].items()):
        print(f"  {consumer:<24} {len(paths)}")

    findings = result["findings"]
    if not findings:
        print("\nClean: every parameter is claimed, every claim is live, and every "
              "claim of engine-read was observed in the last build.")
        return 0

    blocking = [f for f in findings if VERDICTS[f["verdict"]][0] == "BLOCK"]
    print(f"\n{len(findings)} finding(s), {len(blocking)} blocking")
    print("═" * 100)
    seen = set()
    for f in findings:
        if f["verdict"] not in seen:
            seen.add(f["verdict"])
            sev, why = VERDICTS[f["verdict"]]
            print(f"\n{f['verdict'].upper()} [{sev}] — {why}")
        print(f"  {f['path']:<52} {f['detail']}")

    print()
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
