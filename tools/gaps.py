#!/usr/bin/env python3
"""
Audit the data layer against what the engine actually needs.

Answers one question: for each candidate, which fields are missing, does that
block weighting or merely degrade a score, and what document would fix it.

    python tools/gaps.py              # work list, grouped by severity
    python tools/gaps.py --by-field   # grouped by field instead of by company
    python tools/gaps.py --json       # machine-readable, for driving the fetcher
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# What each field costs if absent, and where it is normally published.
#   blocking    — compute_raw_weights() rejects the name outright
#   provisional — a GATE still returns pass, but only because the input is
#                 missing. Absence makes the test easier, so the pass is not a
#                 real one. Worse than degrading: a degraded score understates a
#                 name, a provisional gate pass overstates its safety.
#   degrading   — the name still weights, but a score term silently scores nothing
#   disclosure  — no gate and no score reads it, so no weight can move. Reported
#                 as a one-line summary rather than per name; see SEVERITY_ORDER.
#
# The fourth entry is the SET of sleeves the field applies to, or None for all.
# Developer-only fields are not gaps for a producer and must not be reported as
# such — before this was added the audit would have shown study_stage missing
# for all ten weighted producers, which is noise that hides the real list.
#
# It must be a set, not a single sleeve. gate2_survival branches on
# sleeve == "developer" and sends EVERYTHING ELSE down the producer path, so a
# "near_producer" needs the producer inputs too. Scoping them to {"producer"}
# alone let BC8 — the one near_producer — show its missing AISC as merely
# degrading while the engine was rejecting it outright.
# gate2_survival sends every non-developer down the producer path.
PRODUCER_PATH = frozenset({"producer", "near_producer"})
DEVELOPER = frozenset({"developer"})

FIELDS = {
    "gold_nav_share":      ("blocking",  "purity gate cannot be evaluated",
                            "quarterly/annual revenue by metal", None),
    "eligible_ounce_share": ("blocking", "jurisdiction split of ounces unresolved",
                            "R&R statement, per-asset tables", None),
    "pp_moz":              ("blocking",  "no reserve base",
                            "R&R statement, Ore Reserve summary", None),
    "mi_non_reserve_moz":  ("blocking",  "resource split required for a consistent cross-section",
                            "R&R statement, Mineral Resource summary (M/I/Inf table)", None),
    # Was "runtime": sourced at build time from IBKR fundamentals alongside the
    # price, so an absence here did not block. That is no longer true. TWS API
    # 10.47 removed reqFundamentalData outright (verified 17 Aug 2026, server
    # version 176 — error 10358 for every report type and for AAPL as much as
    # for the ASX names). There is no API source, so an absence here is now a
    # hard block: no share count, no market cap, no EV, no weight.
    "shares_out_m":        ("blocking",  "no share count — market cap and EV cannot be computed",
                            "annual report / half-year notes; Appendix 2A shows "
                            "INCREMENTAL issues, not totals", None),
    "mr_total_moz":        ("degrading", "the §6 ledger cannot be reconciled against "
                                         "the disclosed resource total",
                            "R&R statement headline", None),
    "reserve_price_aud":   ("disclosure", "the booked deck is not reported beside the "
                                          "P&P tranche — no weight moves",
                            "R&R statement, material assumptions / JORC Table 1", None),
    # Blocking, not degrading, for anything on the producer Gate 2 path: absent
    # AISC makes survival untestable and the name is rejected. For a DEVELOPER it
    # would only mute Channel 3 and degrade — no developer currently lacks it, so
    # that case is not modelled; add a separate entry if one ever does.
    "aisc_aud_oz":         ("blocking",  "Gate 2 cannot be tested without a cost base — "
                                         "survival unknown, so the name is rejected",
                            "quarterly activities report", PRODUCER_PATH),
    # Blocking. The hedge book is SUBTRACTED from the ounce ledger
    # (§6.3) rather than applied as a score multiplier, and an unknown short
    # position against the claim is not a claim that can be sized. Where
    # this merely muted a factor.
    "hedge_share_fwd24m":  ("blocking",  "sold-forward ounces cannot be subtracted "
                                         "from the claim — the name is rejected",
                            "quarterly report, hedge book note", None),
    "net_debt_aud_m":      ("degrading", "EV understated (treated as zero net debt)",
                            "quarterly report, cash and debt", None),
    "ineligible_nav_share": ("degrading", "entity-level ineligible cap cannot bind",
                            "R&R statement, per-jurisdiction split", None),
    "inferred_moz":        ("degrading", "the Inferred tranche of the §6 ledger reads "
                                         "zero — the name is understated",
                            "R&R statement, Mineral Resource summary", None),

    # ── Gate 2 inputs (§3). Absent from this table until 17 Aug 2026, which is
    # why the audit read "blocked 2" while the engine was rejecting seven names
    # and flagging eight more as provisional. An auditor that under-reports is
    # worse than no auditor: it converts an open gap into a clean bill.
    "production_koz_yr":   ("blocking",  "Gate 2 cannot be tested — survival is "
                                         "unknown, so the name is rejected",
                            "quarterly activities report", PRODUCER_PATH),
    "committed_capex_aud_m": ("provisional",
                            "Gate 2 passes with contracted spend treated as zero — "
                            "absence makes a SURVIVAL test easier, not harder",
                            "annual report, capital commitments note", PRODUCER_PATH),
    "undrawn_facilities_aud_m": ("degrading",
                            "treated as zero — conservative, makes Gate 2 harder",
                            "annual report, borrowings / facilities note", PRODUCER_PATH),

    # ── Constraint inputs (§4.3, §8.1). Both constraints were declared in
    # config.json and read by no code until 17 Aug 2026; wiring them made the
    # absence of their inputs visible, which is why they appear here now and not
    # before. Degrading rather than blocking in both cases, but note what
    # "degrading" means for a CONSTRAINT: the name still weights, and the limit
    # simply cannot bind on it. A cap that cannot bind is not a cap.
    "advt_shares_m":       ("degrading", "§4.3 capacity untestable for this name — "
                                         "no ADVT, so no position can be sized "
                                         "against liquidity",
                            "tools/asx.py --write (ASX key-statistics, "
                            "volumeAverage)", None),
    # "degrading", not "disclosure". An asset-level cap
    # (20%) sat ABOVE the 15% name cap, so it could not bind on one company and
    # sourcing its input was cosmetic. max_single_asset_name (10%) sits BELOW it
    # and binds directly, so an absent share now lets a one-mine company run at
    # the full 15%. Sourced for all 17 on 18 Aug 2026; it bound on PNR and CYL.
    #
    # Note what "degrading" means for a CAP input, and why it is not the weaker
    # "disclosure": absence does not mute a score, it removes a ceiling. The
    # name weights either way, and the direction of the error is always toward
    # a LARGER position in a company one operational event can destroy.
    "largest_asset_pp_share": ("degrading",
                            "§8.1 single-asset cap cannot be applied — the name "
                            "runs at the full 15% and reports UNTESTED",
                            "R&R statement per-asset Ore Reserve table; §8.1 "
                            "defines the asset unit. Also a §11 disclosure", None),

    # ── Developer gate inputs (§3.1). Not gaps for a producer.
    "study_stage":         ("blocking",  "D1 cannot be tested — PFS minimum unproven",
                            "PFS/DFS announcement", DEVELOPER),
    "approvals_land_secured": ("blocking", "D2 cannot be tested — approvals and "
                                           "land access unproven",
                            "approvals announcements, tenure register", DEVELOPER),
    # Blocking twice over since 18 Aug 2026: it gates D3 AND it is added to EV
    # to price the claim all-in (§7). A developer without it is rejected before
    # the denominator is built, which is what stops absence reading as zero in
    # the one sleeve where zero would flatter.
    "remaining_capex_aud_m": ("blocking", "D3 cannot be tested and the claim cannot "
                                          "be priced all-in — funding gap unsized",
                            "PFS/DFS capital estimate less cash", DEVELOPER),
}

# Declared in the engine's KNOWN_FIELDS and carried for three names, but read by
# nothing. Kept as a reporting input beside reserve_price_aud: the two decks
# together say how much of the resource base is booked below spot. Excluded from
# the audit so it does not read as a gap in something that consumes it.
UNCONSUMED = {"resource_price_aud"}

# "disclosure" is deliberately outside the clean/partial/blocked classification.
# It marks a field that no gate and no score reads, so its absence cannot move a
# weight — it is missing for §11 or for a constraint that provably cannot bind.
# Counting it as a partial would put all seventeen candidates in the same bucket
# and hide the four names that have real work outstanding, which is the failure
# the sleeve-scoping above already exists to prevent.
SEVERITY_ORDER = {"blocking": 0, "provisional": 1, "runtime": 2, "degrading": 3,
                  "disclosure": 4}
SCORING = {"blocking", "provisional", "runtime", "imputed", "degrading"}


def check_coverage() -> None:
    """Fail if the engine reads a field this audit does not know about.

    The engine already validates the other direction — a field in companies.json
    that KNOWN_FIELDS does not list raises at load. Nothing checked THIS
    direction, and it drifted: seven of nineteen engine fields were invisible
    here, including committed_capex_aud_m, which is the input behind eight of ten
    weighted names passing Gate 2 only provisionally. The audit reported a clean
    bill on gaps the engine was actively complaining about.

    Imported rather than re-parsed so the two lists cannot disagree.
    """
    sys.path.insert(0, str(ROOT))
    from build_index import KNOWN_FIELDS

    unaudited = KNOWN_FIELDS - set(FIELDS) - UNCONSUMED
    if unaudited:
        raise SystemExit(
            f"tools/gaps.py is out of date: the engine reads "
            f"{', '.join(sorted(unaudited))} but this audit does not check "
            f"{'them' if len(unaudited) > 1 else 'it'}. Add to FIELDS with a "
            f"severity, or to UNCONSUMED if genuinely read by nothing.")

    stale = set(FIELDS) - KNOWN_FIELDS
    if stale:
        raise SystemExit(
            f"tools/gaps.py audits {', '.join(sorted(stale))}, which the engine "
            f"no longer reads. Remove from FIELDS.")


def load() -> tuple[dict, list[dict]]:
    check_coverage()
    cfg = json.loads((DATA / "config.json").read_text())
    companies = json.loads((DATA / "companies.json").read_text())["companies"]
    return cfg, companies


def audit(companies: list[dict]) -> list[dict]:
    rows = []
    for c in companies:
        present = set(c.get("fields", {}))
        missing = []
        for name, (sev, why, where, sleeve) in FIELDS.items():
            if name in present:
                continue
            if sleeve is not None and c["sleeve"] not in sleeve:
                continue  # not applicable to this sleeve — silence, not a gap
            # An absent M&I split used to downgrade to "imputed" when the
            # resource total was known, because the cohort-split rule could fill
            # it. That rule is deleted (config, _resource_split_imputation_
            # deleted), so a missing split is now simply blocking: the near-money
            # tranche of the §6 ledger is the option inventory, and a name
            # counted on P&P alone would compete against peers counting all
            # three. Never downgrade a gap on the strength of a rule that no
            # longer runs.
            missing.append({"field": name, "severity": sev, "why": why, "where": where})

        rows.append({
            "ticker": c["ticker"], "name": c["name"], "sleeve": c["sleeve"],
            "blocked": any(m["severity"] == "blocking" for m in missing),
            "missing": sorted(missing, key=lambda m: (SEVERITY_ORDER.get(m["severity"], 2),
                                                      m["field"])),
            "blocking_note": c.get("blocking"),
            "documents": {k: v.get("url") for k, v in c.get("documents", {}).items()},
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit the SJGV data layer for gaps.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--by-field", action="store_true", help="group by field, not company")
    args = ap.parse_args()

    _, companies = load()
    rows = audit(companies)

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    if args.by_field:
        buckets: dict[str, list[str]] = {}
        for r in rows:
            for m in r["missing"]:
                buckets.setdefault(f"{m['severity']}:{m['field']}", []).append(r["ticker"])
        print(f"\n{'FIELD':<34} {'N':>3}  TICKERS")
        print("─" * 100)
        for key in sorted(buckets, key=lambda k: (SEVERITY_ORDER.get(k.split(':')[0], 2),
                                                  -len(buckets[k]))):
            sev, field = key.split(":", 1)
            tk = ", ".join(sorted(buckets[key]))
            print(f"{sev[:4].upper():<5}{field:<29} {len(buckets[key]):>3}  {tk}")
        return 0

    def scoring(r: dict) -> list[dict]:
        return [m for m in r["missing"] if m["severity"] in SCORING]

    blocked = [r for r in rows if r["blocked"]]
    partial = [r for r in rows if not r["blocked"] and scoring(r)]
    clean = [r for r in rows if not scoring(r) and not r["blocked"]]

    print(f"\nSJGV data-layer audit — {len(rows)} candidates")
    print(f"  clean {len(clean)}   partial {len(partial)}   blocked {len(blocked)}")

    disclosure: dict[str, list[str]] = {}
    for r in rows:
        for m in r["missing"]:
            if m["severity"] == "disclosure":
                disclosure.setdefault(m["field"], []).append(r["ticker"])
    for field, tickers in sorted(disclosure.items()):
        print(f"  disclosure-only: {field} unsourced for {len(tickers)}/{len(rows)} "
              f"— no gate or score reads it, so no weight moves")

    for title, group in (("BLOCKED — cannot be weighted", blocked),
                         ("PARTIAL — weights, but a score term is silent", partial)):
        if not group:
            continue
        print(f"\n{'═' * 100}\n{title}\n{'═' * 100}")
        for r in sorted(group, key=lambda x: x["ticker"]):
            print(f"\n{r['ticker']} — {r['name']} ({r['sleeve']})")
            if r["blocking_note"]:
                print(f"   ! {r['blocking_note']}")
            for m in r["missing"]:
                if m["severity"] == "disclosure":
                    continue        # summarised above, not part of the work list
                tag = {"blocking": "BLOCK", "provisional": "PROV ", "runtime": "rt   ",
                       "imputed": "IMPUT", "degrading": "degr."}[m["severity"]]
                print(f"   [{tag}] {m['field']:<24} {m['why']}")
                print(f"           → {m['where']}")

    if clean:
        print(f"\n{'═' * 100}\nCLEAN: {', '.join(sorted(r['ticker'] for r in clean))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
