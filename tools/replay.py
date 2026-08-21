#!/usr/bin/env python3
"""Rebuild weights from a recorded TWS market session without contacting TWS.

This is the activation-control replay: it holds prices, daily histories, gold,
FX and spread observations fixed while applying the current data and engine.
It is deliberately separate from ``build_index.py``.  It may prove a code/data
change against identical inputs, but it can never be described as a fresh
market-data build.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_index as B  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _series(rows: dict[str, list[dict]], key: str) -> list[tuple[str, float]]:
    return [(row["date"], float(row["close"])) for row in rows.get(key, [])
            if float(row["close"]) > 0]


def _spreads(rows: dict[str, list[dict]], key: str) -> dict | None:
    points = []
    for row in rows.get(key, []):
        bid, ask = float(row["open"]), float(row["close"])
        if bid > 0 and ask >= bid:
            points.append({"date": row["date"], "bid": bid, "ask": ask,
                           "spread_pct": (ask - bid) / ((ask + bid) / 2) * 100})
    return B.spread_stats(points)


def _market(bundle_path: Path, bars_path: Path) -> tuple[dict, dict]:
    bundle = json.loads(bundle_path.read_text())
    rows: dict[str, list[dict]] = {}
    with bars_path.open(newline="") as src:
        for row in csv.DictReader(src):
            rows.setdefault(row["series"], []).append(row)

    prices = bundle["prices"]
    history = {ticker: _series(rows, f"{ticker}:TRADES:2Y")
               for ticker in prices}
    spreads = {ticker: _spreads(rows, f"{ticker}:BID_ASK:3M")
               for ticker in prices}
    return bundle, {"prices": prices, "history": history, "spreads": spreads,
                    "gold_history": _series(rows, "XAUUSD:MIDPOINT:5Y"),
                    "audusd_history": _series(rows, "AUD.USD:MIDPOINT:5Y")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market-bundle", type=Path, default=ROOT / "market_bundle.json")
    ap.add_argument("--market-bars", type=Path, default=ROOT / "market_bars.csv")
    ap.add_argument("--reference", type=Path, default=ROOT / "weights.json",
                    help="prior build supplying the fixed gold/FX observations")
    ap.add_argument("--output", type=Path, required=True,
                    help="write replay weights JSON here; never writes root outputs")
    args = ap.parse_args()

    bundle, md = _market(args.market_bundle, args.market_bars)
    reference = json.loads(args.reference.read_text())
    meta, constituents, excluded, market, impute_notes = B.load_data()
    gold_aud = reference["gold_aud_oz"]
    aud_gold = [(d, gold / fx) for d, gold, fx in
                B._join(md["gold_history"], md["audusd_history"]) if fx > 0]
    anchor = B.gold_anchor(aud_gold, gold_aud, meta)
    risk = B.compute_risk_stats(md["history"], md["gold_history"],
                                md["audusd_history"], meta)
    rows, rejected = B.compute_raw_weights(
        constituents, md["prices"], risk, gold_aud, meta,
        anchor_gold=anchor["anchor_aud"], spreads=md["spreads"],
        as_of=market["_ledger_sourced"])
    if not rows:
        raise SystemExit("replay produced no constituents")
    constraints = B.apply_constraints(rows, meta)

    output = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "methodology": meta["methodology"], "data_sourced": market["_ledger_sourced"],
        "gold_aud_oz": gold_aud, "gold_source": "recorded build input",
        "euraud": reference.get("euraud"), "fx_source": "recorded build input",
        "market_input": {
            "bundle": str(args.market_bundle), "bundle_sha256": _sha256(args.market_bundle),
            "bars": str(args.market_bars), "bars_sha256": _sha256(args.market_bars),
            "replay": True, "replay_note": "Recorded TWS inputs; not a fresh session.",
            "session_started_utc": bundle["session"]["started_utc"],
            "session_finished_utc": bundle["session"]["finished_utc"],
        },
        "gold_reference": anchor, "constraints": constraints, "weights": rows,
        "rejected": rejected, "pre_excluded": excluded,
        "resource_reconciliation": impute_notes,
        "config_reads_observed": sorted(B.CONFIG_READS),
        "config_keys_missing": sorted(B.CONFIG_MISSES),
    }
    args.output.write_text(json.dumps(output, indent=2, default=str) + "\n")
    print(f"Replayed {len(rows)} constituents from recorded TWS inputs → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
