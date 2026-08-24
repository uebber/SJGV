#!/usr/bin/env python3
"""
Freeze the state of a rebalance so that a point-in-time series can start.

    python tools/snapshot.py                    # snapshot today's build
    python tools/snapshot.py --tag deep-2026H2  # label it
    python tools/snapshot.py --list
    python tools/snapshot.py --diff 2026-08-17 2026-11-15
    python tools/snapshot.py --diff-latest      # last two, whatever they are

WHY
---
Nothing in this project has ever been rebalanced. One snapshot exists — today's —
so there is no turnover, no realised trading cost and no constituent transition
in the record. That is the single largest gap between "a methodology" and "an
index", and unlike the others it cannot be closed by working harder: the history
does not exist and cannot be reconstructed, because point-in-time reserves and
price decks are not published anywhere, so the gates cannot be re-run on a past
date.

What CAN be done is start accumulating from now, which costs one command per
rebalance. Every cycle that goes by without this is a cycle of history
permanently lost.

WHAT A SNAPSHOT IS
------------------
Everything needed to explain a weight after the fact, and nothing that can be
recomputed from it:

    companies.json   the company data layer as it stood — every field and citation
    guidance_delivery.json  the period verdicts behind the execution treatment
    config.json      the parameters as they stood; a weight change caused by a
                     committee decision must be separable from one caused by the
                     market, and only this makes that possible
    weights.json  the primary output, including gate verdicts and NAV detail
    gate1_cap_weights.json  the parallel Gate-1-only market-cap variant
    gate1_cap_basket.json   its sized basket, when the build was sized
    market_bundle.json  the raw TWS session behind the prices, spreads and beta:
                     request parameters, contract identifiers, quote fields,
                     market-data type, timestamps and the engine commit
    market_bars.csv  every historical bar that session returned
    manifest.json    git commit, gold price, FX, and a digest of the weights

The git commit matters: it identifies the ENGINE. Data, parameters and code are
the three things that can move a weight, and a snapshot that pins only the first
two would leave the most confusing of the three unrecorded.

The market bundle matters for the same reason one layer down. Every other input
carries the document it was read from; the market leg used to carry only the
number. A price that moved between two snapshots could have moved because the
market moved, because the quote came back delayed instead of frozen, because
IBKR resolved the symbol to a different conId, or because the window in config
changed — and the record could not tell those apart. Now it can.

WHAT --diff MEASURES
--------------------
One-way turnover (½Σ|Δw|), entries, exits, and — because a weight change is only
interesting once you know why — which of the underlying fields moved between the
two dates. §11.3 asks for turnover and realised trading cost in basis points;
this gives the first, and the second follows once the spread at each rebalance is
applied to the turnover it caused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "snapshots"
ARTEFACTS = ("data/companies.json", "data/guidance_delivery.json",
             "data/config.json", "weights.json",
             "basket.json", "gate1_cap_weights.json", "gate1_cap_basket.json",
             "market_bundle.json", "market_bars.csv")


def git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                               capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return None
        sha = out.stdout.strip()
        return sha + ("-dirty" if dirty.stdout.strip() else "")
    except Exception:
        return None


def short(commit: str | None) -> str:
    """Twelve characters of sha, and the dirty flag intact.

    Slicing the raw string would silently drop the "-dirty" suffix, which is the
    part that says the snapshot does not correspond to any commit anyone else
    can check out.
    """
    if not commit:
        return "—"
    sha, _, flag = commit.partition("-")
    return sha[:12] + (f"-{flag}" if flag else "")


def market_integrity(dest: Path, market: dict) -> dict:
    """Check the frozen bundle is the one that produced these weights.

    weights.json records the sha256 of market_bundle.json and market_bars.csv at
    the instant the build wrote them. This re-hashes the copies that just landed
    in the snapshot and says whether they still match. The failure it catches is
    mundane and would be invisible: a second build runs between the first build
    and the snapshot, the root artefacts are overwritten, and the directory then
    pairs one run's weights with another run's market data. Both files look
    fine. The digests do not.

    A build from before this record existed reports `unrecorded` rather than a
    failure — the old snapshots are not retroactively wrong, they simply never
    pinned their session.
    """
    if not market:
        return {"status": "unrecorded",
                "note": "build predates the market bundle; no session frozen"}

    out = {
        "status": "ok",
        "engine_commit": market.get("engine_commit"),
        "session_started_utc": market.get("session_started_utc"),
        "market_data_type_requested": market.get("market_data_type_requested"),
        "market_data_type_observed": market.get("market_data_type_observed"),
        # Carried into the manifest rather than left in the bundle because it
        # is the line that decides how much the prices in this snapshot are
        # worth: a book priced from histDailyClose is priced from session
        # closes, and the manifest is what a later reader opens first.
        "price_fields": market.get("price_fields"),
        "n_requests": market.get("n_requests"),
        "n_series": market.get("n_series"),
        "bars_rows": market.get("bars_rows"),
        "n_errors": market.get("n_errors"),
        "error_codes": market.get("error_codes"),
        "cli_overrides": market.get("cli_overrides"),
    }
    mismatches = []
    for rel, key in (("market_bundle.json", "bundle_sha256"),
                     ("market_bars.csv", "bars_sha256")):
        claimed = market.get(key)
        path = dest / rel
        actual = (hashlib.sha256(path.read_bytes()).hexdigest()
                  if path.exists() else None)
        out[key] = actual
        if claimed and actual != claimed:
            mismatches.append(f"{rel}: weights.json claims {claimed[:12]}, "
                              f"file hashes to {(actual or '—')[:12]}")
    if mismatches:
        out["status"] = "MISMATCH"
        out["mismatches"] = mismatches
    return out


def take(tag: str | None) -> Path:
    weights_path = ROOT / "weights.json"
    if not weights_path.exists():
        raise SystemExit("No weights.json — run build_index.py first. A "
                         "snapshot of the data layer without the weights it "
                         "produced explains nothing.")
    weights = json.loads(weights_path.read_text())
    gate1_cap_path = ROOT / "gate1_cap_weights.json"
    if not gate1_cap_path.exists():
        raise SystemExit("No gate1_cap_weights.json — run build_index.py with the "
                         "current engine before freezing both index variants.")
    gate1_cap = json.loads(gate1_cap_path.read_text())
    if gate1_cap.get("generated_utc") != weights.get("generated_utc"):
        raise SystemExit(
            "weights.json and gate1_cap_weights.json came from different builds; "
            "run build_index.py again before snapshotting.")

    # The build's own timestamp, not the wall clock. A snapshot taken an hour
    # after the build belongs to the build.
    stamp = (weights.get("generated_utc") or
             datetime.now(timezone.utc).isoformat())[:10]
    name = f"{stamp}-{tag}" if tag else stamp
    dest = SNAPSHOTS / name
    if dest.exists():
        raise SystemExit(f"{dest.relative_to(ROOT)} already exists. Snapshots are "
                         f"immutable — pass --tag to distinguish this one, or "
                         f"delete the old directory deliberately.")
    dest.mkdir(parents=True)

    copied = []
    for rel in ARTEFACTS:
        src = ROOT / rel
        if src.exists():
            shutil.copy2(src, dest / Path(rel).name)
            copied.append(rel)

    rows = weights.get("weights") or []
    market = weights.get("market_input") or {}
    gate1_cap_rows = gate1_cap.get("weights") or []
    manifest = {
        "snapshot": name,
        "tag": tag,
        "taken_utc": datetime.now(timezone.utc).isoformat(),
        "build_generated_utc": weights.get("generated_utc"),
        "git_commit": git_commit(),
        # The commit the BUILD ran from, which is the one that produced these
        # numbers. git_commit above is the tree at snapshot time; they differ
        # the moment anything is edited between the run and the freeze, and
        # then only this one identifies the engine.
        "engine_commit_at_build": market.get("engine_commit"),
        "market_input": market_integrity(dest, market),
        "methodology": weights.get("methodology"),
        "data_sourced": weights.get("data_sourced"),
        "gold_aud_oz": weights.get("gold_aud_oz"),
        "euraud": weights.get("euraud"),
        "gold_reference_aud": (
            weights.get("gold_reference") or weights.get("gate2_anchor") or {}
        ).get("anchor_aud"),
        "n_constituents": len(rows),
        "effective_n": (weights.get("stats") or {}).get("effective_n"),
        "portfolio_beta_gold": (weights.get("stats") or {}).get("portfolio_beta_gold"),
        "weights": {r["ticker"]: round(r["weight"], 6) for r in rows},
        "variants": {
            "gate1_cap": {
                "methodology": gate1_cap.get("methodology"),
                "n_constituents": len(gate1_cap_rows),
                "weights": {
                    r["ticker"]: round(r["weight"], 6)
                    for r in gate1_cap_rows
                },
            }
        },
        "artefacts": copied,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return dest


def load(name: str) -> dict:
    path = SNAPSHOTS / name / "manifest.json"
    if not path.exists():
        matches = sorted(p for p in SNAPSHOTS.glob(f"{name}*") if p.is_dir())
        if len(matches) != 1:
            raise SystemExit(f"No snapshot {name!r}"
                             + (f"; did you mean one of "
                                f"{', '.join(p.name for p in matches)}?"
                                if matches else ""))
        path = matches[0] / "manifest.json"
    return json.loads(path.read_text())


def field_changes(a: str, b: str) -> list[str]:
    """Which company fields moved between two snapshots.

    A weight change with no field change behind it came from the market or from
    a parameter, and knowing which is the difference between a rebalance you can
    explain and one you cannot.
    """
    def fields(name: str) -> dict[tuple[str, str], object]:
        path = SNAPSHOTS / name / "companies.json"
        if not path.exists():
            return {}
        return {(c["ticker"], f): spec.get("v")
                for c in json.loads(path.read_text())["companies"]
                for f, spec in c.get("fields", {}).items()}

    fa, fb = fields(a), fields(b)
    out = []
    for key in sorted(set(fa) | set(fb)):
        va, vb = fa.get(key), fb.get(key)
        if va == vb:
            continue
        tick, field = key
        out.append(f"{tick}.{field}: "
                   f"{'—' if va is None else va} → {'—' if vb is None else vb}")
    return out


def diff(a: str, b: str) -> None:
    ma, mb = load(a), load(b)
    wa, wb = ma["weights"], mb["weights"]
    tickers = sorted(set(wa) | set(wb))
    turnover = 0.5 * sum(abs(wb.get(t, 0.0) - wa.get(t, 0.0)) for t in tickers)

    print(f"\n{ma['snapshot']} → {mb['snapshot']}")
    print(f"  gold A${ma['gold_aud_oz']:,.0f} → A${mb['gold_aud_oz']:,.0f}"
          f"   Eff N {ma['effective_n']:.1f} → {mb['effective_n']:.1f}"
          f"   β {ma['portfolio_beta_gold']:.2f} → {mb['portfolio_beta_gold']:.2f}")
    if ma["git_commit"] != mb["git_commit"]:
        print(f"  ENGINE CHANGED: {short(ma['git_commit'])} → "
              f"{short(mb['git_commit'])} — some of this is code, not market.")

    # A quote that arrived delayed on one date and frozen on the next is a
    # different measurement of the same thing, and it moves prices, spreads and
    # therefore weights without a single field or parameter changing.
    ta = (ma.get("market_input") or {}).get("market_data_type_observed")
    tb = (mb.get("market_input") or {}).get("market_data_type_observed")
    if ta and tb and ta != tb:
        print(f"  MARKET-DATA TYPE CHANGED: {'/'.join(ta)} → {'/'.join(tb)} — "
              f"the quotes are not the same kind of quote.")

    print(f"\n  {'TICK':<6}{'FROM':>9}{'TO':>9}{'Δpp':>8}")
    print("  " + "─" * 32)
    for t in sorted(tickers, key=lambda k: -abs(wb.get(k, 0.0) - wa.get(k, 0.0))):
        d = (wb.get(t, 0.0) - wa.get(t, 0.0)) * 100
        if abs(d) < 0.005:
            continue
        mark = "  NEW" if t not in wa else ("  EXIT" if t not in wb else "")
        print(f"  {t:<6}{wa.get(t, 0.0)*100:>8.2f}%{wb.get(t, 0.0)*100:>8.2f}%"
              f"{d:>+8.2f}{mark}")
    print(f"\n  one-way turnover {turnover*100:.2f}%   "
          f"entries {len(set(wb) - set(wa))}   exits {len(set(wa) - set(wb))}")

    changes = field_changes(ma["snapshot"], mb["snapshot"])
    if changes:
        print(f"\n  {len(changes)} data-layer field(s) moved:")
        for line in changes[:40]:
            print(f"    {line}")
        if len(changes) > 40:
            print(f"    … and {len(changes) - 40} more")
    else:
        print("\n  No data-layer field changed — this is price and parameters only.")


def chronological() -> list:
    """Snapshot directories in the order they were TAKEN, not the order they sort.

    Directory names are `<date>[-<tag>]`, so a lexical sort puts
    2026-08-17-funded-ev before 2026-08-17-final regardless of which was taken
    first, and --diff-latest then reports the change backwards. Two snapshots on
    one date is the normal case while a methodology is being worked on, so this
    is not a corner. Sort on manifest.taken_utc, which is recorded for exactly
    this purpose, and fall back to the name only if it is missing.
    """
    out = []
    for p in SNAPSHOTS.glob("*"):
        mf = p / "manifest.json"
        if not mf.exists():
            continue
        try:
            taken = json.loads(mf.read_text()).get("taken_utc") or p.name
        except (json.JSONDecodeError, OSError):
            taken = p.name
        out.append((taken, p))
    return [p for _, p in sorted(out)]


def listing() -> None:
    dirs = chronological()
    if not dirs:
        print("No snapshots yet. Run build_index.py, then tools/snapshot.py.")
        return
    print(f"\n{'SNAPSHOT':<26}{'N':>4}{'EFF N':>7}{'β':>6}{'GOLD A$':>10}  COMMIT")
    print("─" * 74)
    for d in dirs:
        m = json.loads((d / "manifest.json").read_text())
        print(f"{m['snapshot']:<26}{m['n_constituents']:>4}"
              f"{m['effective_n']:>7.1f}{m['portfolio_beta_gold']:>6.2f}"
              f"{m['gold_aud_oz']:>10,.0f}  {short(m['git_commit'])}")
    if len(dirs) == 1:
        print("\nOne snapshot: no turnover, no transition, no realised cost yet. "
              "The series starts at the second one.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", help="label this snapshot (e.g. deep-2026H2)")
    ap.add_argument("--list", action="store_true", help="list snapshots")
    ap.add_argument("--diff", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--diff-latest", action="store_true",
                    help="diff the two most recent snapshots")
    args = ap.parse_args()

    SNAPSHOTS.mkdir(exist_ok=True)

    if args.list:
        listing()
        return 0
    if args.diff:
        diff(*args.diff)
        return 0
    if args.diff_latest:
        dirs = [p.name for p in chronological()]
        if len(dirs) < 2:
            print(f"Need two snapshots to diff; there {'is' if dirs else 'are'} "
                  f"{len(dirs)}.")
            return 1
        diff(dirs[-2], dirs[-1])
        return 0

    dest = take(args.tag)
    m = json.loads((dest / "manifest.json").read_text())
    print(f"Snapshot → {dest.relative_to(ROOT)}")
    print(f"  {m['n_constituents']} constituents, Eff N {m['effective_n']:.1f}, "
          f"gold A${m['gold_aud_oz']:,.0f}, commit {short(m['git_commit'])}")
    print(f"  {len(m['artefacts'])} artefact(s): {', '.join(m['artefacts'])}")

    mi = m["market_input"]
    if mi["status"] == "unrecorded":
        print("  Market session: NOT FROZEN — this build predates the bundle.")
    else:
        print(f"  Market session {(mi['session_started_utc'] or '')[:19]}Z, "
              f"{mi['n_requests']} requests over {mi['n_series']} series, "
              f"{mi['bars_rows']:,} bars, data "
              f"{'/'.join(mi['market_data_type_observed'] or []) or '—'}")
        print("  Prices from "
              + (", ".join(f"{k}×{v}"
                           for k, v in (mi.get("price_fields") or {}).items())
                 or "—"))
        print(f"  Engine at build {short(mi['engine_commit'])}"
              + ("" if mi["engine_commit"] == m["git_commit"]
                 else f" — DIFFERS from the tree at snapshot time; the build's "
                      f"commit is the one that made these numbers."))
        if mi["status"] != "ok":
            print("  MARKET BUNDLE MISMATCH — these weights were not produced by "
                  "the session frozen beside them:")
            for line in mi.get("mismatches", []):
                print(f"    {line}")
    n = len([p for p in SNAPSHOTS.glob("*") if (p / "manifest.json").exists()])
    if n < 2:
        print("  First snapshot. Turnover and transition cost begin at the second.")
    else:
        print(f"  {n} snapshots on file — tools/snapshot.py --diff-latest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
