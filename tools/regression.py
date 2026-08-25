#!/usr/bin/env python3
"""Freeze and compare the pre-capital-migration construction evidence.

The default invocation compares the latest ``weights.json`` and current data
layer with the fixture captured from the 21 August 2026 TWS build::

    .venv/bin/python tools/regression.py
    .venv/bin/python tools/regression.py --strict
    .venv/bin/python tools/regression.py --json

The comparison is deliberately staged.  A later capital-model replay can show
whether a name moved at source data, the economic-capital denominator, Gate 2,
normalisation, or the caps instead of presenting only an unexplained final
weight delta.

``--capture`` exists for an explicitly approved future baseline.  It refuses to
overwrite a fixture unless ``--force`` is supplied.  A normal code check must
never refresh the fixture merely to make a regression pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_index as B  # noqa: E402


DEFAULT_ACTUAL = ROOT / "weights.json"
DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "2026-08-21-capital-baseline.json"

# Every current field that can affect the capital denominator or Gate 2.  The
# fixture keeps value-bearing provenance metadata, but hashes long notes rather
# than copying a second, inevitably stale source narrative out of companies.json.
CAPITAL_FIELDS = (
    "net_debt_aud_m",
    "undrawn_facilities_aud_m",
    "committed_capex_aud_m",
    "remaining_capex_aud_m",
    # Approved migration target.  These are absent in the before-state on
    # purpose: their first appearance must register as source-data drift.
    "execution_capital_projects",
    "remaining_execution_capex_aud_m",
    "available_project_funding_aud_m",
    "residual_funding_gap_aud_m",
    "production_koz_yr",
    "aisc_aud_oz",
    "study_stage",
    "approvals_land_secured",
)
SPEC_KEYS = ("v", "range", "horizon_years", "annual_leg_aud_m", "term_date",
             "evidence_state", "as_of", "cost_base_date", "accuracy_range",
             "contingency_included")
ABS_TOL = 1e-12


def _read(path: Path) -> dict:
    return json.loads(path.read_text())


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _note_sha256(note: str | None) -> str | None:
    if note is None:
        return None
    return hashlib.sha256(note.encode()).hexdigest()


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and not isinstance(left, bool):
        if not isinstance(right, (int, float)) or isinstance(right, bool):
            return False
        return math.isclose(float(left), float(right), rel_tol=1e-10,
                            abs_tol=ABS_TOL)
    return left == right


def _capital_inputs(payload: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for company in payload["companies"]:
        documents = company.get("documents", {})
        fields = company.get("fields", {})
        captured = {}
        for field in CAPITAL_FIELDS:
            spec = fields.get(field)
            if not isinstance(spec, dict):
                captured[field] = None
                continue
            doc_key = spec.get("doc")
            doc = documents.get(doc_key, {})
            item = {key: spec[key] for key in SPEC_KEYS if key in spec}
            item.update({
                "doc": doc_key,
                "source_type": doc.get("type"),
                "document_date": doc.get("date"),
                "note_sha256": _note_sha256(spec.get("note")),
            })
            captured[field] = item
        captured[B.EXECUTION_CAPITAL_PROJECTS_KEY] = company.get(
            B.EXECUTION_CAPITAL_PROJECTS_KEY)
        out[company["ticker"]] = captured
    return out


def _bundle_path(actual_path: Path, actual: dict) -> Path | None:
    raw = (actual.get("market_input") or {}).get("bundle")
    if not raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    local = actual_path.parent / candidate
    return local if local.exists() else ROOT / candidate


def _market_prices(actual_path: Path, actual: dict) -> dict[str, dict]:
    path = _bundle_path(actual_path, actual)
    if path and path.exists():
        return (_read(path).get("prices") or {})
    # Accepted rows still carry their exact construction price.  This fallback
    # cannot reconstruct rejected-name bridges, so validation reports the gap.
    return {row["ticker"]: {"price": row.get("price_aud")}
            for row in actual.get("weights", [])}


def _market_inputs(prices: dict[str, dict]) -> dict[str, dict]:
    """The exact per-name market observations that feed EV and Gate 2 D3."""
    keys = ("price", "field", "market_data_type", "con_id")
    return {ticker: {key: record.get(key) for key in keys}
            for ticker, record in prices.items()}


def _evaluate_gate2(companies: list[dict], cfg: dict, prices: dict[str, dict],
                    actual: dict) -> dict[str, dict]:
    """Replay Gate 2 for every modelled name, including rejected names.

    ``weights.json`` carries complete bridges only for names that survive the
    pipeline.  Replaying against its frozen price and anchor is therefore what
    captures BGL/OBM/PNR/BC8/AAR/AUC rather than preserving only their final
    prose reason.
    """
    stress_reference = actual.get("gold_aud_oz")
    if stress_reference is None:
        return {}
    try:
        as_of = date.fromisoformat(actual["data_sourced"])
    except (KeyError, TypeError, ValueError):
        return {}

    accepted = {row["ticker"] for row in actual.get("weights", [])}
    rejected = {row["ticker"]: row["reason"]
                for row in actual.get("rejected", [])}
    bridges = {}

    for original in companies:
        company = dict(original)
        ticker = company["ticker"]
        px = (prices.get(ticker) or {}).get("price")
        shares = company.get("shares_out_m")
        mcap = shares * px if shares and px else None

        reported_undrawn = company.get("undrawn_facilities_aud_m") or 0.0
        creditable, facility_note = B.creditable_undrawn(company, cfg, as_of)
        if facility_note:
            company["undrawn_facilities_aud_m"] = creditable

        gate = B.gate2_survival(company, stress_reference, mcap, cfg)
        gate["facility_note"] = facility_note
        stopped_at = "base"

        if gate.get("pass") is True:
            gate["range_invariance"] = B.gate2_range_invariance(
                company, B.disclosed_ranges(company), stress_reference, mcap, cfg)
            stopped_at = ("passed_gate2" if gate["range_invariance"]["ok"]
                          else "range_invariance")
        elif gate.get("pass") is None and gate.get("capital_interval"):
            stopped_at = "capital_interval"

        pipeline = ({"state": "included", "reason": None} if ticker in accepted
                    else {"state": "rejected", "reason": rejected.get(ticker)})
        bridges[ticker] = {
            "market_cap_aud_m": mcap,
            "reported_undrawn_aud_m": reported_undrawn,
            "creditable_undrawn_aud_m": creditable,
            "stopped_at": stopped_at,
            "evaluation": gate,
            "pipeline": pipeline,
        }
    return bridges


def _weight_stages(actual: dict, cfg: dict) -> dict[str, dict]:
    rows = actual.get("weights", [])
    precap = (actual.get("constraints") or {}).get("unconstrained_weights") or {}
    out = {}
    for row in rows:
        ticker = row["ticker"]
        raw = row.get("raw")
        # The fixture predates v2.1 and calls this stage
        # ``normalised_raw_weight``. Preserve the key for longitudinal diffs,
        # but populate it with v2.2's effective-N-only optimiser weight.
        normalised = precap.get(ticker, row.get("weight", 0.0))
        before_name_caps = precap.get(ticker, normalised)
        final = row.get("weight", 0.0)
        ceiling = 1.0
        if row.get("sleeve") == "developer":
            ceiling = min(ceiling, cfg["constraints"]["max_developer_single_name"])
        elif row.get("single_asset") is True:
            ceiling = min(ceiling, cfg["constraints"]["max_single_asset_name"])
        if (row.get("guidance_delivery") or {}).get("portfolio_treatment") == "CAP":
            ceiling = min(ceiling, cfg["constraints"]["max_guidance_delivery_name"])
        if ceiling == 1.0:
            ceiling = None
        out[ticker] = {
            "sleeve": row.get("sleeve"),
            "single_asset": row.get("single_asset"),
            "claimed_moz": row.get("claimed_moz"),
            "price_aud": row.get("price_aud"),
            "market_cap_aud_m": row.get("mcap_aud_m"),
            "ev_aud_m": row.get("ev_aud_m"),
            "capital_denominator_input_aud_m": row.get(
                "execution_capital_in_denominator_aud_m",
                row.get("remaining_execution_capex_aud_m",
                        row.get("funding_gap_aud_m"))),
            "residual_funding_gap_aud_m": row.get(
                "residual_funding_gap_aud_m", row.get("funding_gap_aud_m")),
            "funded_ev_aud_m": row.get("all_in_ev_aud_m",
                                         row.get("funded_ev_aud_m")),
            "aud_per_oz": row.get("aud_per_oz"),
            "raw_score": raw,
            "value_rank": row.get("value_rank"),
            "rank_points": row.get("rank_points"),
            "normalised_raw_weight": normalised,
            "pre_name_cap_weight": before_name_caps,
            "sleeve_cap_effect": before_name_caps - normalised,
            "name_cap_effect": final - before_name_caps,
            "total_cap_effect": final - normalised,
            "final_weight": final,
            "cap_ceiling": ceiling,
            "cap_bound": (ceiling is not None
                          and abs(final - ceiling) <= 1e-9),
        }
    return out


def build_facts(actual_path: Path) -> dict:
    actual = _read(actual_path)
    payload = _read(ROOT / "data" / "companies.json")
    plain_cfg = _read(ROOT / "data" / "config.json")
    cfg, companies, _, _, _ = B.load_data()
    prices = _market_prices(actual_path, actual)

    single_asset = {}
    threshold = plain_cfg["constraints"]["single_asset_pp_share_threshold"]
    for company in companies:
        single_asset[company["ticker"]] = {
            "largest_asset_pp_share": company.get("largest_asset_pp_share"),
            "threshold": threshold,
            "classification": B.derive_single_asset(company, cfg),
        }

    return {
        "market_inputs": _market_inputs(prices),
        "capital_inputs": _capital_inputs(payload),
        "gate2_bridges": _evaluate_gate2(companies, cfg, prices, actual),
        "weight_stages": _weight_stages(actual, plain_cfg),
        "single_asset_classifications": single_asset,
        "rejected": actual.get("rejected", []),
        "pre_excluded": actual.get("pre_excluded", []),
    }


def capture(actual_path: Path) -> dict:
    actual = _read(actual_path)
    bundle = _bundle_path(actual_path, actual)
    bars_raw = (actual.get("market_input") or {}).get("bars")
    bars = None
    if bars_raw:
        bars = Path(bars_raw)
        if not bars.is_absolute():
            local = actual_path.parent / bars
            bars = local if local.exists() else ROOT / bars

    facts = build_facts(actual_path)
    return {
        "fixture_version": 1,
        "purpose": "Issue 1 before-state for the execution-capital and Gate 2 migration",
        "baseline": {
            "generated_utc": actual.get("generated_utc"),
            "data_sourced": actual.get("data_sourced"),
            "methodology": actual.get("methodology"),
            "engine_commit": (actual.get("market_input") or {}).get("engine_commit"),
            "constituents": len(actual.get("weights", [])),
            "gate2_anchor": (
                actual.get("gate2_anchor") or actual.get("gold_reference")
            ),
            "gold_aud_oz": actual.get("gold_aud_oz"),
        },
        "source_hashes": {
            "weights.json": _sha256(actual_path),
            "data/companies.json": _sha256(ROOT / "data" / "companies.json"),
            "data/config.json": _sha256(ROOT / "data" / "config.json"),
            "market_bundle.json": _sha256(bundle) if bundle else None,
            "market_bars.csv": _sha256(bars) if bars else None,
        },
        **facts,
    }


def _diff_values(before: Any, after: Any, prefix: str = "") -> list[dict]:
    if isinstance(before, dict) and isinstance(after, dict):
        changes = []
        for key in sorted(set(before) | set(after)):
            path = f"{prefix}.{key}" if prefix else key
            if key not in before:
                changes.append({"field": path, "before": None, "after": after[key]})
            elif key not in after:
                changes.append({"field": path, "before": before[key], "after": None})
            else:
                changes.extend(_diff_values(before[key], after[key], path))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        if before == after:
            return []
        return [{"field": prefix, "before": before, "after": after}]
    if _same(before, after):
        return []
    return [{"field": prefix, "before": before, "after": after}]


def _ticker_diffs(before: dict, after: dict, fields: tuple[str, ...] | None = None
                  ) -> list[dict]:
    changes = []
    for ticker in sorted(set(before) | set(after)):
        left, right = before.get(ticker), after.get(ticker)
        if fields and isinstance(left, dict) and isinstance(right, dict):
            left = {field: left.get(field) for field in fields}
            right = {field: right.get(field) for field in fields}
        for change in _diff_values(left, right):
            changes.append({"ticker": ticker, **change})
    return changes


def compare(fixture: dict, actual_path: Path) -> dict:
    current = build_facts(actual_path)
    baseline_stages = fixture["weight_stages"]
    current_stages = current["weight_stages"]

    changes = {
        "source_data": (
            _ticker_diffs(fixture["market_inputs"], current["market_inputs"])
            + _ticker_diffs(fixture["capital_inputs"], current["capital_inputs"])
            + _ticker_diffs(baseline_stages, current_stages,
                            ("claimed_moz", "price_aud"))
        ),
        "capital_model": _ticker_diffs(
            baseline_stages, current_stages,
            ("market_cap_aud_m", "ev_aud_m", "capital_denominator_input_aud_m",
             "residual_funding_gap_aud_m", "funded_ev_aud_m", "aud_per_oz")),
        "gate2": _ticker_diffs(fixture["gate2_bridges"],
                               current["gate2_bridges"]),
        "normalisation": _ticker_diffs(
            baseline_stages, current_stages,
            ("raw_score", "normalised_raw_weight")),
        "cap_effect": (
            _ticker_diffs(fixture["single_asset_classifications"],
                          current["single_asset_classifications"])
            + _ticker_diffs(
                baseline_stages, current_stages,
                ("single_asset", "pre_name_cap_weight", "sleeve_cap_effect",
                 "name_cap_effect", "total_cap_effect", "cap_ceiling", "cap_bound",
                 "final_weight"))
        ),
    }

    expected_rejected = {row["ticker"]: row["reason"] for row in fixture["rejected"]}
    actual_rejected = {row["ticker"]: row["reason"] for row in current["rejected"]}
    expected_single = {ticker: row["classification"] for ticker, row in
                       fixture["single_asset_classifications"].items()}
    actual_single = {ticker: row["classification"] for ticker, row in
                     current["single_asset_classifications"].items()}

    checks = {
        "rejected_name_reasons": {
            "ok": expected_rejected == actual_rejected,
            "expected": expected_rejected,
            "actual": actual_rejected,
        },
        "single_asset_classifications": {
            "ok": expected_single == actual_single,
            "expected": expected_single,
            "actual": actual_single,
        },
    }
    return {
        "baseline_generated_utc": fixture["baseline"]["generated_utc"],
        "actual_generated_utc": _read(actual_path).get("generated_utc"),
        "checks": checks,
        "changes": changes,
        "n_changes": sum(len(items) for items in changes.values()),
    }


def validate_fixture(fixture: dict) -> list[str]:
    errors = []
    expected_names = set(fixture.get("capital_inputs", {}))
    if fixture.get("fixture_version") != 1:
        errors.append("unsupported fixture_version")
    if len(expected_names) != 17:
        errors.append(f"expected 17 modelled names, found {len(expected_names)}")
    if set(fixture.get("market_inputs", {})) != expected_names:
        errors.append("market inputs do not cover every modelled name")
    if set(fixture.get("gate2_bridges", {})) != expected_names:
        errors.append("Gate 2 bridges do not cover every modelled name")
    if set(fixture.get("single_asset_classifications", {})) != expected_names:
        errors.append("single-asset classifications do not cover every modelled name")
    if len(fixture.get("weight_stages", {})) != 11:
        errors.append("expected 11 weighted names in the baseline")
    if len(fixture.get("rejected", [])) != 6:
        errors.append("expected 6 build-time rejected names in the baseline")

    for ticker, row in fixture.get("weight_stages", {}).items():
        raw = row.get("raw_score")
        normalised = row.get("normalised_raw_weight")
        final = row.get("final_weight")
        if raw is None or normalised is None or final is None:
            errors.append(f"{ticker}: incomplete weight stages")
            continue
        if not _same(row["total_cap_effect"], final - normalised):
            errors.append(f"{ticker}: total cap effect does not bridge to final weight")
        parts = row["sleeve_cap_effect"] + row["name_cap_effect"]
        if not _same(row["total_cap_effect"], parts):
            errors.append(f"{ticker}: sleeve and name-cap effects do not add up")
    if fixture.get("weight_stages"):
        total = sum(row["normalised_raw_weight"]
                    for row in fixture["weight_stages"].values())
        if not math.isclose(total, 1.0, abs_tol=ABS_TOL):
            errors.append(f"normalised raw weights sum to {total}, not 1")
        final_total = sum(row["final_weight"]
                          for row in fixture["weight_stages"].values())
        if not math.isclose(final_total, 1.0, abs_tol=ABS_TOL):
            errors.append(f"final weights sum to {final_total}, not 1")
    return errors


def _short(value: Any) -> str:
    text = json.dumps(value, sort_keys=True)
    return text if len(text) <= 100 else text[:97] + "..."


def print_report(report: dict, fixture_errors: list[str]) -> None:
    print("SJGV capital migration regression")
    print(f"  baseline  {report['baseline_generated_utc']}")
    print(f"  actual    {report['actual_generated_utc']}")
    if fixture_errors:
        print(f"\nFIXTURE INVALID ({len(fixture_errors)})")
        for error in fixture_errors:
            print(f"  {error}")

    for name, check in report["checks"].items():
        label = name.replace("_", " ")
        print(f"  {label:<36} {'PASS' if check['ok'] else 'FAIL'}")

    if report["n_changes"] == 0:
        print("\nClean: no drift across source data, capital model, Gate 2, "
              "normalisation, or cap effects.")
        return

    print(f"\n{report['n_changes']} staged change(s)")
    for category, changes in report["changes"].items():
        if not changes:
            continue
        print(f"\n{category.upper().replace('_', ' ')} ({len(changes)})")
        for change in changes:
            print(f"  {change['ticker']:<6} {change['field']}: "
                  f"{_short(change['before'])} -> {_short(change['after'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--actual", type=Path, default=DEFAULT_ACTUAL,
                        help="build output to compare or capture")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE,
                        help="frozen baseline fixture")
    parser.add_argument("--capture", action="store_true",
                        help="capture --actual as the fixture and exit")
    parser.add_argument("--force", action="store_true",
                        help="allow --capture to replace an existing fixture")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 on fixture error, check failure, or drift")
    args = parser.parse_args()

    if not args.actual.exists():
        parser.error(f"actual build output not found: {args.actual}")

    if args.capture:
        if args.fixture.exists() and not args.force:
            parser.error(f"fixture exists: {args.fixture}; pass --force to replace it")
        result = capture(args.actual)
        rendered = json.dumps(result, indent=2, sort_keys=False) + "\n"
        if str(args.fixture) == "-":
            print(rendered, end="")
        else:
            args.fixture.parent.mkdir(parents=True, exist_ok=True)
            args.fixture.write_text(rendered)
            print(f"Captured {args.fixture}")
        return 0

    if not args.fixture.exists():
        parser.error(f"fixture not found: {args.fixture}")
    fixture = _read(args.fixture)
    fixture_errors = validate_fixture(fixture)
    report = compare(fixture, args.actual)
    if args.json:
        print(json.dumps({"fixture_errors": fixture_errors, **report}, indent=2))
    else:
        print_report(report, fixture_errors)

    failed_checks = any(not check["ok"] for check in report["checks"].values())
    drift = report["n_changes"] > 0
    return 1 if args.strict and (fixture_errors or failed_checks or drift) else 0


if __name__ == "__main__":
    sys.exit(main())
