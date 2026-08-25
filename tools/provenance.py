#!/usr/bin/env python3
"""
Audit source QUALITY, as distinct from source presence.

    python tools/provenance.py            # summary + the non-primary register
    python tools/provenance.py --field aisc_aud_oz

tools/gaps.py answers "is there a value?". This answers "is the value any good?"
— and they can disagree sharply. A field sourced to a news aggregator is not a
gap and looks clean in the gap audit, but it is a paraphrase of a filing rather
than the filing, and paraphrases drop qualifiers, mix vintages and round.

Why this matters more than it sounds: the load-bearing fields are the worst
affected. On the 2026-08-17 baseline, 67 of 228 values (29.4%) were secondary,
including AISC for eight names — and AISC is a GATE 2 input, so a health gate
was being decided on aggregator reporting. Pantoro carried nine secondary values
against one primary while sitting at the former 15% single-name cap.

The tiers are the ones data/companies.json already declares per document:

  primary    the filing, the issuer's own page, the exchange's own feed
  secondary  a report ABOUT the filing — news, aggregator, broker, transcript
  none       no document cited at all, which should never happen

Weighted names are flagged, because a secondary value on a rejected name costs
nothing and a secondary value on a large position costs a great deal.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Fields that feed a binary gate. A secondary source here is materially worse
# than a secondary source on a score input: a score degrades continuously and is
# reported, a gate flips and removes the name.
GATE_FIELDS = {
    "aisc_aud_oz", "production_koz_yr", "committed_capex_aud_m",
    "undrawn_facilities_aud_m", "net_debt_aud_m", "gold_nav_share",
    "eligible_ounce_share", "eligible_pp_share", "eligible_mi_share",
    "eligible_inferred_share", "study_stage", "approvals_land_secured",
    "remaining_execution_capex_aud_m", "available_project_funding_aud_m",
}


def _is_load_bearing(company: dict, field: str) -> bool:
    """Producer execution capital is retained evidence, not a live input."""
    return not (field == "remaining_execution_capex_aud_m"
                and company.get("sleeve") == "producer")


def load():
    companies = json.loads((ROOT / "data" / "companies.json").read_text())["companies"]
    weights = {}
    wpath = ROOT / "weights.json"
    if wpath.exists():
        weights = {r["ticker"]: r["weight"]
                   for r in json.loads(wpath.read_text())["weights"]}
    return companies, weights


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--field", help="restrict to one field")
    args = ap.parse_args()

    companies, weights = load()
    tally = collections.Counter()
    rows = []

    for c in companies:
        docs = c.get("documents", {})
        for f, v in c.get("fields", {}).items():
            if not isinstance(v, dict) or (args.field and f != args.field):
                continue
            t = docs.get(v.get("doc"), {}).get("type", "none")
            tally[t] += 1
            if t != "primary":
                rows.append({
                    "ticker": c["ticker"], "field": f, "type": t,
                    "weight": weights.get(c["ticker"]),
                    "gate": f in GATE_FIELDS and _is_load_bearing(c, f),
                    "url": docs.get(v.get("doc"), {}).get("url", ""),
                })
        for project in c.get("execution_capital_projects", []):
            if not isinstance(project, dict):
                continue
            for suffix, doc_key in (
                    ("committed", project.get("committed_capex_doc")),
                    ("coverage", project.get("coverage_doc")),
                    ("execution", project.get("execution_capital_doc"))):
                field = ("execution_capital_projects."
                         f"{project.get('project_id', '?')}.{suffix}")
                if args.field and field != args.field:
                    continue
                doc = docs.get(doc_key, {})
                source_type = doc.get("type", "none")
                tally[source_type] += 1
                if source_type != "primary":
                    rows.append({
                        "ticker": c["ticker"], "field": field,
                        "type": source_type, "weight": weights.get(c["ticker"]),
                        "gate": (suffix != "execution"
                                 or c.get("sleeve") != "producer"),
                        "url": doc.get("url", ""),
                    })

    total = sum(tally.values()) or 1
    print(f"SOURCE QUALITY — {total} field values across {len(companies)} candidates\n")
    for k in ("primary", "secondary", "none"):
        if tally.get(k):
            print(f"  {k:<11}{tally[k]:>4}  {tally[k] / total * 100:>5.1f}%")

    weighted = [r for r in rows if r["weight"]]
    gate_weighted = [r for r in weighted if r["gate"]]
    print(f"\n  non-primary on a WEIGHTED name:        {len(weighted)}")
    print(f"  non-primary on a weighted GATE input:  {len(gate_weighted)}"
          f"   <-- worst category")

    if gate_weighted:
        print("\n" + "=" * 78)
        print("GATE INPUTS ON WEIGHTED NAMES, NOT PRIMARY-SOURCED")
        print("A binary gate decided on a report ABOUT a filing rather than the filing.")
        print("=" * 78)
        print(f"  {'TICK':<6}{'WEIGHT':>8}  {'FIELD':<26}{'TYPE':<11}SOURCE")
        for r in sorted(gate_weighted, key=lambda x: -x["weight"]):
            host = r["url"].split("/")[2] if "//" in r["url"] else r["url"][:28]
            print(f"  {r['ticker']:<6}{r['weight'] * 100:>7.2f}%  "
                  f"{r['field']:<26}{r['type']:<11}{host}")

    other = [r for r in rows if not (r["weight"] and r["gate"])]
    if other:
        print("\n" + "=" * 78)
        print(f"OTHER NON-PRIMARY VALUES ({len(other)}) — score inputs, or names "
              f"not currently weighted")
        print("=" * 78)
        by = collections.defaultdict(list)
        for r in other:
            by[r["ticker"]].append(r["field"])
        for t in sorted(by):
            w = weights.get(t)
            mark = f"{w * 100:.1f}%" if w else "—"
            print(f"  {t:<6}{mark:>7}  {', '.join(sorted(by[t]))}")

    print("\nUpgrade path, in the order that has actually worked:")
    print("  1. ASX announcements feed — asx.api.markitdigital.com "
          "/companies/{T}/announcements")
    print("     then cdn-api.markitdigital.com/.../file/{documentKey} for the PDF.")
    print("     The lodged document itself. CAPPED AT 5 RECENT ITEMS per ticker,")
    print("     so it catches what is published from now on, not the back catalogue.")
    print("  2. Issuer resources-and-reserves page — full JORC table in HTML for some")
    print("     (Ausgold, Catalyst); an IMAGE or JS-rendered for others (Pantoro).")
    print("  3. Issuer annual report PDF — reliable but a year stale by August.")
    print("  4. listcorp / investegate / api.investi.com.au mirrors when the issuer")
    print("     blocks automated access.")
    print("  5. Visual read of the image, where the table is published as a PNG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
