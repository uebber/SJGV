#!/usr/bin/env python3
"""
Pull candidate field values out of fetched documents.

Design rule: this tool PROPOSES, it never writes to data/companies.json.

Extraction from mining filings has too many traps to automate end to end —
attributable versus 100% basis, gold-only versus gold-equivalent, group versus
single-asset totals, statements whose headline disagrees with their own table
(Genesis: headline 4.4 Moz, table sums to 4.2), and documents served from a URL
that describes a different vintage than the file behind it (Ora Banda's "2026"
URL serves the FY25 statement). Every one of those was hit in the 17 Aug 2026
pass. A tool that silently picked a number would have gotten several wrong.

So: surface the candidates with enough surrounding context to judge them, rank
by confidence, and leave the commit to a human.

    python tools/extract.py .cache/<slug>.txt
    python tools/extract.py .cache/<slug>.txt --field reserve_price
    python tools/extract.py --all                    # every cached text artifact
    python tools/extract.py --all --field shares
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"

NUM = r"[\d][\d,\.]*"


def _f(s: str) -> float | None:
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _ctx(text: str, start: int, end: int, pad: int = 130) -> str:
    return " ".join(text[max(0, start - pad):end + pad].split())


# ──────────────────────────────────────────────────────────────────────────
# Extractors. Each returns [{value, unit, confidence, context, why}]
# ──────────────────────────────────────────────────────────────────────────

def reserve_price(text: str) -> list[dict]:
    """Gold price assumption behind Ore Reserves — the Channel 2a input.

    Deliberately separates reserve decks from resource decks and from spot
    quotes. All three appear in the same document and they are not the same
    number: Vault's statement quotes A$5,546 spot as pricing *context* for
    hedged versus unhedged ounces while its actual reserve deck is A$4,500.
    Conflating them was a live error in the first pass.
    """
    out = []
    for m in re.finditer(rf"(A?\$\s?({NUM})\s*/\s*oz)", text, re.I):
        val = _f(m.group(2))
        if val is None or not (500 <= val <= 12000):
            continue
        ctx = _ctx(text, m.start(), m.end())
        low = ctx.lower()

        # Site chrome. Issuer pages render a live spot ticker in the header, and
        # it sits in exactly the same A$X/oz shape as a price deck. Evolution's
        # R&R page has no deck at all, only the ticker — without this the tool
        # would offer A$6,178 as a candidate reserve assumption.
        ticker = re.search(r"gold\s*:|asx\s*:|spot|market quote|closing price|realised|"
                           r"live price|current price", low)

        # Which subject is NEARER to the price governs. "Mineral Resources are
        # inclusive of Ore Reserves ... reported at A$2500-3500/oz" is a RESOURCE
        # guideline, but a naive reserve-first test reads the words "Ore Reserves"
        # and calls it a reserve deck. Genesis is exactly this case.
        before = low[:len(low) // 2 + 40]
        res_pos = max((before.rfind(k) for k in
                       ("mineral resource", "resources are", "resources were",
                        "pit shell", "pit optimis", "resource cut-off")), default=-1)
        rsv_pos = max((before.rfind(k) for k in
                       ("ore reserve", "reserves are", "reserves were", "reserve cut-off",
                        "establish ore reserves", "reserve estimat")), default=-1)
        # "inclusive of ore reserves" is a scope note, not an estimation basis.
        if re.search(r"inclusive of ore reserves", before):
            rsv_pos = -1

        if ticker:
            conf, why = "reject", "live site ticker or spot quote, not an estimation assumption"
        elif re.search(r"npv|irr|cash ?flow|financial evaluation|payback|\baisc\b", low):
            conf, why = "low", "study economics deck, not an estimation assumption"
        elif rsv_pos > res_pos and rsv_pos >= 0:
            conf, why = "high", "reserve is the nearer subject"
        elif res_pos >= 0:
            conf, why = "resource", "RESOURCE deck — nearer subject is resources, not reserves"
        elif re.search(r"cut-?off grade", low):
            conf, why = "medium", "cut-off grade context, subject ambiguous"
        else:
            conf, why = "medium", "price near no qualifying context"

        out.append({"value": val, "unit": "AUD/oz" if "A$" in m.group(1) else "USD/oz",
                    "confidence": conf, "why": why, "context": ctx})
    return out


def resource_split(text: str) -> list[dict]:
    """Group Measured / Indicated / Inferred and Proved / Probable totals.

    Anchors on a Total-ish row followed by a run of numbers, then reports the
    row verbatim. Column order varies too much between issuers to parse blind —
    Westgold runs Measured, Indicated, M&I, Inferred; Vault runs M&I, Inferred,
    Total. Showing the row and letting a human map the columns is correct.
    """
    out = []
    pat = re.compile(
        rf"((?:Group|Northern Star|Regis|Evolution|Total)\s*"
        rf"(?:Total|Resources?|Reserves?|Mineral Resource|Ore Reserve)?)\s*[:\s]"
        rf"((?:\s*{NUM}){{3,14}})", re.I)
    for m in re.finditer(pat, text):
        nums = [_f(x) for x in re.findall(NUM, m.group(2))]
        nums = [n for n in nums if n is not None]
        if len(nums) < 3:
            continue
        out.append({"label": " ".join(m.group(1).split()),
                    "numbers": nums[:14],
                    "confidence": "high" if len(nums) >= 6 else "medium",
                    "why": "candidate group total row — verify column order",
                    "context": _ctx(text, m.start(), m.end(), pad=60)})
    return out


def shares(text: str) -> list[dict]:
    """Ordinary shares on issue. The single biggest blocking gap."""
    out = []
    pats = [
        (rf"({NUM})\s*(?:fully paid )?ordinary shares", "high", "explicit share count"),
        (rf"shares? on issue[^\d]{{0,40}}({NUM})", "high", "'shares on issue' label"),
        (rf"issued capital[^\d]{{0,40}}({NUM})", "medium", "'issued capital' label"),
        (rf"({NUM})\s*(?:m|million)\s*shares", "medium", "shares in millions"),
    ]
    for pat, conf, why in pats:
        for m in re.finditer(pat, text, re.I):
            v = _f(m.group(1))
            if v is None:
                continue
            ctx = _ctx(text, m.start(), m.end())
            if re.search(r"quotation of|issue of|exercise|conversion|performance rights"
                         r"|placement of|vest", ctx, re.I):
                conf2, why2 = "reject", "incremental issuance, not total on issue"
            else:
                conf2, why2 = conf, why
            if "million" in m.group(0).lower() or re.search(r"\bm\b", m.group(0)):
                v_m = v
            else:
                v_m = v / 1e6
            out.append({"value_millions": round(v_m, 3), "raw": v,
                        "confidence": conf2, "why": why2, "context": ctx})
    return out


def hedges(text: str) -> list[dict]:
    """Forward sales versus bought puts.

    The distinction is load-bearing under methodology §6 P1, but NOT because the
    two score in opposite directions — they do not. Per §6.2 (decided 17 Aug
    2026) P1 is a penalty only: sold production is penalised and a bought
    position earns nothing, so a bought put scores the same as no position at
    all. The distinction matters because miscounting a bought put as a forward
    sale invents a penalty that should not exist. Greatland and Rox both hold
    options over gold and both must read as ZERO sold production.

    What belongs in the count: flat forward sales, and the sold-call leg of a
    collar. What does not: anything the company bought.
    """
    out = []
    for m in re.finditer(rf"({NUM})\s*(?:k)?oz[^.]{{0,160}}", text, re.I):
        ctx = _ctx(text, m.start(), m.end())
        low = ctx.lower()
        if re.search(r"sold call|call option|written call", low):
            kind, conf = "sold_call (COUNTS — caps upside, §6.2)", "high"
        elif re.search(r"\bput\b|put option", low):
            kind, conf = "bought_put (EXCLUDE — scores as unhedged, §6.2)", "high"
        elif re.search(r"forward sale|hedge|sold forward|delivery commitment"
                       r"|hedge book|committed ounces", low):
            kind, conf = "forward_sale (COUNTS — penalised)", "high"
        else:
            continue
        out.append({"value": _f(m.group(1)), "kind": kind,
                    "confidence": conf, "why": kind, "context": ctx})
    return out


def unhedged(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"(100% unhedged|fully unhedged|no hedging|unhedged|no forward sales)",
                         text, re.I):
        out.append({"value": 0.0, "confidence": "high",
                    "why": "explicit unhedged statement", "context": _ctx(text, m.start(), m.end())})
    return out


EXTRACTORS = {
    "reserve_price": reserve_price,
    "resource_split": resource_split,
    "shares": shares,
    "hedges": hedges,
    "unhedged": unhedged,
}

RANK = {"high": 0, "medium": 1, "resource": 2, "low": 3, "reject": 4}


def run(path: Path, fields: list[str], limit: int) -> dict:
    text = path.read_text(errors="ignore")
    return {f: sorted(EXTRACTORS[f](text),
                      key=lambda r: RANK.get(r.get("confidence"), 9))[:limit]
            for f in fields}


def main() -> int:
    ap = argparse.ArgumentParser(description="Propose field values from cached documents.")
    ap.add_argument("paths", nargs="*", help="cached .txt artifacts")
    ap.add_argument("--all", action="store_true", help="every cached .txt")
    ap.add_argument("--field", action="append", choices=list(EXTRACTORS),
                    help="restrict to one extractor (repeatable)")
    ap.add_argument("--limit", type=int, default=6, help="max candidates per field")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    paths = [Path(p) for p in args.paths]
    if args.all:
        paths = sorted(CACHE.glob("*.txt"))
    if not paths:
        ap.error("give paths or --all (nothing cached yet? run tools/fetch.py first)")

    fields = args.field or list(EXTRACTORS)
    results = {}
    for p in paths:
        if not p.exists():
            print(f"missing: {p}", file=sys.stderr)
            continue
        results[str(p)] = run(p, fields, args.limit)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    for path, byfield in results.items():
        meta_p = Path(path).with_suffix(".json")
        src = json.loads(meta_p.read_text()).get("url", "") if meta_p.exists() else ""
        print(f"\n{'═' * 100}\n{path}\n{src}\n{'═' * 100}")
        for field, cands in byfield.items():
            if not cands:
                continue
            print(f"\n  ── {field} ──")
            for c in cands:
                val = c.get("value", c.get("value_millions", c.get("numbers")))
                conf = c.get("confidence", "?")
                mark = {"high": "++", "medium": " +", "resource": " R",
                        "low": " -", "reject": "XX"}.get(conf, "  ")
                print(f"   {mark} {str(val)[:46]:<48} [{conf}] {c.get('why', '')}")
                print(f"      {c['context'][:180]}")

    print("\nCandidates only — nothing was written. Confirm against the source, "
          "then update data/companies.json with a `doc` reference.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
