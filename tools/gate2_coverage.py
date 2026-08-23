#!/usr/bin/env python3
"""Audit readiness for the Gate 2 capital-resilience data pack.

This is deliberately a read-only Phase 1 tool.  It does not infer stress inputs
from issuer-defined net debt or the legacy project ledger: those are different
quantities and using either as a substitute would make a missing adverse input
look like zero.  Once the v1.8 schema is populated, the same audit identifies
which producer-path candidates have a complete, common-basis core pack.

Usage:
    .venv/bin/python tools/gate2_coverage.py
    .venv/bin/python tools/gate2_coverage.py --markdown
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPANIES = ROOT / "data" / "companies.json"
PRODUCER_PATH = frozenset({"producer", "near_producer"})

# These names are the proposed §8 company-data schema.  Schedules are required
# rather than scalar totals because the candidate score tests the minimum path.
CORE_FIELDS = (
    "gate2_balance_sheet_as_of",
    "unrestricted_cash_and_bullion_aud_m",
    "debt_cash_outflows_schedule",
    "contractual_capital_commitments_schedule",
)
OPERATING_FIELDS = ("production_koz_yr", "aisc_aud_oz")
OPTIONAL_FIELDS = ("gate2_balance_sheet_rollforward_adjustments",
                   "undrawn_facilities_aud_m")


def value_present(field: dict | None) -> bool:
    """A field shell with UNRESOLVED evidence is not a usable source value."""
    if not isinstance(field, dict):
        return False
    return field.get("evidence_state") != "UNRESOLVED" and field.get("v") is not None


def schedule_present(field: dict | None) -> bool:
    """A usable path schedule has at least one sourced entry (a sourced zero
    is represented by an explicit record, never an omitted list)."""
    if not isinstance(field, dict) or field.get("evidence_state") == "UNRESOLVED":
        return False
    value = field.get("v")
    return isinstance(value, list) and bool(value)


def field_status(fields: dict, name: str) -> str:
    field = fields.get(name)
    if name.endswith("_schedule"):
        return "READY" if schedule_present(field) else "MISSING"
    return "READY" if value_present(field) else "MISSING"


def audit() -> list[dict]:
    payload = json.loads(COMPANIES.read_text())
    rows = []
    for company in payload["companies"]:
        if company.get("sleeve") not in PRODUCER_PATH:
            continue
        fields = company.get("fields") or {}
        statuses = {name: field_status(fields, name) for name in CORE_FIELDS}
        operating = {name: field_status(fields, name) for name in OPERATING_FIELDS}
        optional = {name: field_status(fields, name) for name in OPTIONAL_FIELDS}
        # Existing records do not have machine-readable period / produced-vs-sold
        # metadata.  Notes can inform the migration, but cannot establish the
        # compatibility test required by §5.6(4).
        basis_ready = all(
            isinstance(fields.get(name), dict)
            and fields[name].get("period_start")
            and fields[name].get("period_end")
            and fields[name].get("ounce_basis") in {"produced", "sold"}
            and fields[name].get("attribution_basis")
            for name in OPERATING_FIELDS
        )
        admitted = (all(v == "READY" for v in statuses.values())
                    and all(v == "READY" for v in operating.values())
                    and basis_ready)
        rows.append({
            "ticker": company["ticker"],
            "sleeve": company["sleeve"],
            "operating_volume": operating["production_koz_yr"],
            "aisc": operating["aisc_aud_oz"],
            "operating_basis": "READY" if basis_ready else "MISSING",
            "balance_sheet_date": statuses["gate2_balance_sheet_as_of"],
            "cash": statuses["unrestricted_cash_and_bullion_aud_m"],
            "debt_schedule": statuses["debt_cash_outflows_schedule"],
            "commitment_schedule": statuses[
                "contractual_capital_commitments_schedule"],
            "rollforward": optional["gate2_balance_sheet_rollforward_adjustments"],
            "facility_diagnostic": optional["undrawn_facilities_aud_m"],
            "admitted": admitted,
        })
    return rows


def render(rows: list[dict], markdown: bool) -> str:
    headers = ("Ticker", "Sleeve", "Volume", "AISC", "Operating basis",
               "Common balance-sheet date", "Cash", "Debt-outflow schedule",
               "Commitment schedule", "Roll-forward", "Facility diagnostic",
               "Core-pack result")
    values = [
        (r["ticker"], r["sleeve"], r["operating_volume"], r["aisc"],
         r["operating_basis"], r["balance_sheet_date"], r["cash"],
         r["debt_schedule"], r["commitment_schedule"], r["rollforward"],
         r["facility_diagnostic"], "ADMITTED" if r["admitted"] else "UNTESTED")
        for r in rows
    ]
    if markdown:
        lines = ["| " + " | ".join(headers) + " |",
                 "|" + "|".join("---" for _ in headers) + "|"]
        lines.extend("| " + " | ".join(row) + " |" for row in values)
    else:
        widths = [max(len(headers[i]), *(len(row[i]) for row in values))
                  for i in range(len(headers))]
        fmt = "  ".join("{" + f":<{width}" + "}" for width in widths)
        lines = [fmt.format(*headers), fmt.format(*("-" * width for width in widths))]
        lines.extend(fmt.format(*row) for row in values)
    admitted = sum(r["admitted"] for r in rows)
    lines.extend(("", f"{admitted}/{len(rows)} producer-path candidates have the "
                   "complete v1.8 core data pack."))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true",
                        help="render a Markdown table for the dated coverage audit")
    args = parser.parse_args()
    print(render(audit(), args.markdown))


if __name__ == "__main__":
    main()
