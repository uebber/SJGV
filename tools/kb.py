#!/usr/bin/env python3
"""
Source-priority knowledge base — evidence and knowledge-plane tooling.

Implements the storage model (§6), acquisition workflow (§7.2), legacy claim
backfill (§9), and strict audit (§8), as specified by
`source-knowledge-base.md`. The production engine still reads `data/`; claim
backfill is additive and does not cut the projection over to the KB.

Design points that are not negotiable and are enforced in code:

  * Identity is the SHA-256 of the bytes. A URL is an alias, never an identity,
    so the same filing pulled from the exchange, an IR platform and a mirror
    collapses to one document record with three aliases (§4.2, §10.1).
  * Archive before extracting. Raw bytes land in objects/ first; text, pdfinfo
    and page renders are reproducible derivatives that inherit the artifact's
    tier and never acquire one of their own (§2.2, §4.2).
  * Look up before fetching. `acquire` refuses any URL whose bytes are already
    held under some alias, and records a reason for every fetch it does make
    (§2.1, §7.1).
  * Authority is assigned by origin and domain, not by the host that served the
    bytes. A mirror is T2 until equivalence with the lodged document is
    established; hash-identity with an exchange-hosted copy establishes it
    automatically, which is why dedupe runs before tier assignment (§4, §4.2).
  * A filename is not provenance. Anything read off a local filename — a
    documentKey, a headline id, the URL it would resolve to — is recorded as
    INFERRED and never becomes a URL alias or a verified identifier. Only a
    retrieval URL, an exchange index row, or an equivalence check against a
    verified artifact can promote it (§4.2).
  * A URL is a route that can serve different bytes over time. Each set of
    bytes is its own artifact version; the view keeps them ordered by retrieval
    instead of choosing one (§4.2, §8).
  * The title field is publisher metadata. Analysis about a document is kept in
    `legacy.notes`, never in its title (§3: an extraction is not a claim).

  * A local file is not a document until something says where it came from. A
    ticker read out of its text is what it is ABOUT, not who served it, so an
    artifact with no tested route stays unclassified until `route-local` or
    `verify-inferred` earns it one (§4.2).
  * An approved market-data provider is primary for its own observations and
    for nothing else. A session can never be re-fetched, so that origin lives
    on the record in `market_session` and is what the tier is recomputed from
    (§4.1).
  * A refusal books a retry date. `plan` and `acquire` honour it, so a blocked
    host is asked again when the interval has elapsed and not before (§7.4).

    python tools/kb.py init
    python tools/kb.py ingest-local                 # .cache/ and /tmp/, no network
    python tools/kb.py plan                         # acquisition queue, tier order
    python tools/kb.py acquire --tier T1            # highest tier first
    python tools/kb.py route-local                  # test bare files against the index
    python tools/kb.py reverify                     # titles, tiers, equivalence
    python tools/kb.py backfill-claims              # migrate current company assertions
    python tools/kb.py views
    python tools/kb.py audit --strict
"""

from __future__ import annotations

import argparse
import decimal
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "knowledge"
OBJECTS = KB / "objects" / "sha256"
EXTRACTED = KB / "extracted"
VIEWS = KB / "views"
DOCUMENTS = KB / "documents.jsonl"
CLAIMS = KB / "claims.jsonl"
QUARANTINE = KB / "quarantine.jsonl"
AVAILABILITY = KB / "availability.jsonl"
CACHE = ROOT / ".cache"
TMP = Path("/tmp")

DATA_FILES = [
    "data/companies.json",
    "data/jurisdictions.json",
    "data/sovereign.json",
    "data/market.json",
    "tools/sources.json",
]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/pdf,application/json,image/png,*/*",
    "Accept-Language": "en-AU,en;q=0.9",
}
TIMEOUT = 90
POLITE_DELAY = 1.0

ASX_CDN = "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/"
ASX_YEAR_INDEX = ("https://www.asx.com.au/asx/v2/statistics/announcements.do"
                  "?by=asxCode&asxCode={ticker}&timeframe=Y&year={year}")
ASX_DISPLAY = ("https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do"
               "?display=pdf&idsId={ids}")
INDEX_URL_RE = re.compile(r"announcements\.do\?by=asxCode&asxCode=([A-Z0-9]+)"
                          r"&timeframe=Y&year=(\d{4})", re.I)


# ─────────────────────────────────────────────────────────────────────────────
# Authority tiers (§4). Keyed by origin host, never by the server that happened
# to serve the bytes. `kind` records WHY a tier was given so the audit can tell
# a rule-based assignment from a verified one.
# ─────────────────────────────────────────────────────────────────────────────

# (host regex, tier, domains, publisher, kind, note)
HOST_RULES: list[tuple[str, str, list[str], str, str, str]] = [
    # ── T1: exchange records of what was lodged ──────────────────────────────
    (r"^announcements\.asx\.com\.au$", "T1", ["exchange.lodgement"], "ASX Limited",
     "lodged", "exchange-hosted copy of the lodged announcement"),
    (r"^cdn-api\.markitdigital\.com$", "T1", ["exchange.lodgement"], "ASX Limited",
     "lodged", "ASX research CDN, addressed by documentKey"),
    (r"^www\.asx\.com\.au$", "T1", ["exchange.lodgement"], "ASX Limited",
     "lodged", "exchange announcement index / interstitial"),
    (r"^asx\.api\.markitdigital\.com$", "T1", ["exchange.market_data"], "ASX Limited",
     "volatile", "ASX research API — a live endpoint; bytes are a point-in-time observation"),

    # ── T1: law, regulators and revenue authorities, inside their jurisdiction ─
    (r"^www\.legislation\.gov\.au$", "T1", ["law.commonwealth"],
     "Office of Parliamentary Counsel (Cth)", "law", "enacted Commonwealth law"),
    (r"legislation\.wa\.gov\.au$", "T1", ["law.wa"],
     "Parliamentary Counsel's Office (WA)", "law", "enacted WA law"),
    (r"legislation\.qld\.gov\.au$", "T1", ["law.qld"],
     "Queensland Parliamentary Counsel", "law", "enacted Queensland law"),
    (r"legislation\.vic\.gov\.au$", "T1", ["law.vic"],
     "Chief Parliamentary Counsel (Vic)", "law", "authorised Victorian statutory rule"),
    (r"legislation\.nsw\.gov\.au$", "T1", ["law.nsw"],
     "Parliamentary Counsel's Office (NSW)", "law", "enacted NSW law"),
    (r"legislation\.tas\.gov\.au$", "T1", ["law.tas"],
     "Office of Parliamentary Counsel (Tas)", "law", "enacted Tasmanian law"),
    (r"^qro\.qld\.gov\.au$", "T1", ["royalty.qld"], "Queensland Revenue Office",
     "regulator", "revenue authority publishing statutory royalty rates in its mandate"),
    (r"^www\.revenue\.nsw\.gov\.au$", "T1", ["royalty.nsw"], "Revenue NSW",
     "regulator", "revenue authority in its mandate"),
    (r"^www\.resources\.nsw\.gov\.au$", "T1", ["royalty.nsw", "tenure.nsw"],
     "NSW Department of Regional NSW", "regulator", "state minerals regulator"),
    (r"^resources\.vic\.gov\.au$", "T1", ["royalty.vic", "tenure.vic"],
     "Earth Resources Regulation (Vic)", "regulator", "state minerals regulator"),
    (r"^www\.mrt\.tas\.gov\.au$", "T1", ["royalty.tas", "tenure.tas"],
     "Mineral Resources Tasmania", "regulator", "state minerals regulator"),
    (r"^www\.wa\.gov\.au$", "T1", ["royalty.wa", "tenure.wa"],
     "Government of Western Australia", "regulator", "state government in its mandate"),
    (r"^www\.abs\.gov\.au$", "T1", ["statistics.au"], "Australian Bureau of Statistics",
     "statutory", "official statutory series"),
    (r"^www\.rba\.gov\.au$", "T1", ["monetary.au"], "Reserve Bank of Australia",
     "statutory", "central bank series"),

    # ── T2: official agency material outside a controlling instrument ────────
    (r"^www\.pbo\.gov\.au$", "T2", ["macro.fiscal.au"], "Parliamentary Budget Office",
     "agency", "statutory analytical publication, not a controlling instrument"),
    (r"^www\.imf\.org$", "T2", ["macro.fiscal.global"], "International Monetary Fund",
     "agency", "official IGO publication"),
    (r"^budget\.gov\.au$", "T2", ["macro.fiscal.au"], "Commonwealth of Australia",
     "agency", "budget paper"),

    # ── T2: IR platforms and mirrors carrying lodged announcements ───────────
    # Tier is capped at T2 until equivalence with the lodged document is shown.
    # Hash-identity with an exchange-hosted object promotes it automatically.
    (r"sharelinktechnologies\.com$", "T2", ["issuer.announcement"],
     "ShareLink (issuer IR platform)", "mirror", "issuer IR platform copy of a lodged announcement"),
    (r"irmau\.com$", "T2", ["issuer.announcement"], "IRM (issuer IR platform)",
     "mirror", "issuer IR platform copy of a lodged announcement"),
    (r"wcsecure\.weblink\.com\.au$", "T2", ["issuer.announcement"],
     "WebLink (issuer IR platform)", "mirror", "issuer IR platform copy of a lodged announcement"),
    (r"api\.investi\.com\.au$", "T2", ["issuer.announcement"], "Investi (issuer IR platform)",
     "mirror", "issuer IR platform copy of a lodged announcement"),
    (r"yourir\.info$", "T2", ["issuer.announcement"], "YourIR",
     "mirror", "announcement mirror"),
    (r"listcorp\.com$", "T2", ["issuer.announcement"], "Listcorp",
     "mirror", "announcement mirror"),
    (r"investegate\.co\.uk$", "T2", ["issuer.announcement.rns"], "Investegate",
     "mirror", "mirror of an LSE/AIM RNS announcement"),
    (r"company-announcements\.afr\.com$", "T2", ["issuer.announcement"],
     "AFR announcements", "mirror", "announcement mirror"),
    (r"aspecthuntley\.com\.au$", "T2", ["issuer.announcement"], "Aspect Huntley",
     "mirror", "announcement mirror"),
    (r"prnewswire\.com$", "T2", ["issuer.release"], "PR Newswire",
     "mirror", "wire distribution of an issuer release"),

    # ── T3/T4: secondary and discovery ───────────────────────────────────────
    (r"^classic\.austlii\.edu\.au$", "T3", ["law.qld"], "AustLII", "secondary",
     "unofficial reproduction of legislation; replace with the official consolidated instrument"),
    (r"austlii\.edu\.au$", "T3", ["law"], "AustLII", "secondary",
     "unofficial reproduction of legislation"),
    (r"miningweekly\.com$", "T3", ["news"], "Mining Weekly", "secondary", ""),
    (r"australianresourcesandinvestment\.com\.au$", "T3", ["news"],
     "Australian Resources & Investment", "secondary", ""),
    (r"kpmg\.com$", "T3", ["macro.fiscal.au"], "KPMG", "secondary",
     "professional-services commentary on a budget"),
    (r"marketindex\.com\.au$", "T3", ["issuer.announcement"], "Market Index",
     "secondary", "aggregator; announcement copy not verified against the lodgement"),
    (r"ceo\.ca$|cdn-ceo-ca\.s3\.amazonaws\.com$", "T3", ["issuer.announcement"], "CEO.CA",
     "secondary", "aggregator; announcement copy not verified against the lodgement"),
    (r"kalkine\.com\.au$", "T4", ["news"], "Kalkine", "discovery",
     "unattributed commentary — discovery only"),
    (r"tradingeconomics\.com$", "T4", ["market.price"], "Trading Economics", "discovery",
     "aggregated market data without a traceable primary basis — discovery only"),
    (r"finance\.yahoo\.com$", "T4", ["market.price"], "Yahoo Finance", "discovery",
     "aggregated market data — discovery only"),
    (r"google\.com$|bing\.com$|duckduckgo\.com$", "T4", ["discovery"], "search engine",
     "discovery", "search result — leads and search terms only"),
]

# Issuer hosts → ticker. First-party primary (T2) unless the artifact is also
# reachable at an exchange host, which the hash merge handles.
ISSUER_HOSTS = {
    "www.nsrltd.com": "NST", "nsrltd.com": "NST",
    "evolutionmining.com": "EVN", "www.evolutionmining.com": "EVN",
    "capmetals.com.au": "CMM", "www.capmetals.com.au": "CMM",
    "www.greatland.com.au": "GGP", "greatland.com.au": "GGP",
    "genesisminerals.com.au": "GMD", "www.genesisminerals.com.au": "GMD",
    "www.rameliusresources.com.au": "RMS", "rameliusresources.com.au": "RMS",
    "regisresources.com.au": "RRL", "www.regisresources.com.au": "RRL",
    "www.westgold.com.au": "WGX", "westgold.com.au": "WGX",
    "vaultmineralsltd.com": "VAU", "www.vaultmineralsltd.com": "VAU",
    "bellevuegold.com.au": "BGL", "www.bellevuegold.com.au": "BGL",
    "orabandamining.com.au": "OBM", "www.orabandamining.com.au": "OBM",
    "catalystmetals.com.au": "CYL", "www.catalystmetals.com.au": "CYL",
    "pantoro.com.au": "PNR", "www.pantoro.com.au": "PNR",
    "bc8.com.au": "BC8", "www.bc8.com.au": "BC8",
    "roxresources.com.au": "RXL", "www.roxresources.com.au": "RXL",
    "ausgoldlimited.com": "AUC", "www.ausgoldlimited.com": "AUC",
    "astralresources.com.au": "AAR", "www.astralresources.com.au": "AAR",
}

TICKERS = sorted(set(ISSUER_HOSTS.values()))

TIER_ORDER = ["T0", "T1", "T2", "T3", "T4"]


# ─────────────────────────────────────────────────────────────────────────────
# Approved market-data providers (§4.1). A market session is primary for the
# observations it publishes and authoritative for nothing else.
#
# It is also the only artifact class in the store with no retrieval route at
# all: the session asked questions about a moment that has passed, and no URL
# will ever return those bytes again. So its origin has to travel on the record
# itself. Carrying it in `tier_basis` was not enough — `assign_tier` overwrites
# that field, and with no alias to read it fell through to the local-artifact
# branch, where the tickers the session QUOTES were mistaken for its publisher.
# `market_session` is durable provenance, like `lodgement`, and is what the
# tier, the title and the verification state are recomputed from.
# ─────────────────────────────────────────────────────────────────────────────

MARKET_PROVIDER_BASIS = "approved-market-data-provider"

APPROVED_MARKET_PROVIDERS = {
    "ibkr-tws": {
        "publisher": "Interactive Brokers — the methodology's approved market-data provider",
        "authority_tier": "T1",
        "authority_domains": ["market.observation"],
        "tier_note": ("approved provider, primary for its own observations (§4.1); "
                      "authoritative for nothing else"),
    },
}

# The acquisition notes `ingest-market-session` writes. They are how a session
# archived before the provider block existed is recognised and repaired.
MARKET_SESSION_VIA = ("IBKR/TWS market session", "bar series for TWS session")


def market_provider(doc: dict) -> dict | None:
    """The approved market-data provider behind this artifact, or None."""
    return APPROVED_MARKET_PROVIDERS.get((doc.get("market_session") or {}).get("provider"))


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def object_path(digest: str) -> Path:
    return OBJECTS / digest[:2] / digest


def sniff_mime(head: bytes, content_type: str = "", name: str = "") -> str:
    if head.startswith(b"%PDF"):
        return "application/pdf"
    # Before any filename is consulted: a failed download saved as `x.pdf` is an
    # HTML page, and calling it a PDF sends it through pdftotext, which returns
    # nothing and leaves a record describing an announcement we do not hold.
    if head.lstrip()[:15].lower().startswith((b"<html", b"<!doctype")):
        return "text/html"
    if head.startswith(b"\x89PNG"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.lstrip()[:1] in (b"{", b"["):
        return "application/json"
    ct = content_type.split(";")[0].strip().lower()
    if ct in ("application/pdf", "text/html", "application/json", "image/png", "image/jpeg"):
        return ct
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".json"):
        return "application/json"
    if name.endswith((".html", ".htm")):
        return "text/html"
    if name.endswith(".csv"):
        return "text/csv"
    if name.endswith(".txt"):
        return "text/plain"
    return "text/html"


def classify(url: str) -> dict:
    """Authority tier and domain for an origin. Rule-based, always attributed."""
    host = urllib.parse.urlparse(url).netloc.lower()
    for pattern, tier, domains, publisher, kind, note in HOST_RULES:
        if re.search(pattern, host):
            return {"authority_tier": tier, "authority_domains": list(domains),
                    "publisher": publisher, "tier_kind": kind, "tier_note": note,
                    "tier_basis": f"host-rule:{pattern}"}
    if host in ISSUER_HOSTS:
        t = ISSUER_HOSTS[host]
        return {"authority_tier": "T2",
                "authority_domains": [f"issuer.{t}"],
                "publisher": t, "tier_kind": "issuer",
                "tier_note": "issuer-hosted; not verified as the lodged document",
                "tier_basis": f"issuer-host:{host}"}
    return {"authority_tier": "T4", "authority_domains": ["unclassified"],
            "publisher": host or "unknown", "tier_kind": "discovery",
            "tier_note": "host not in the authority table — discovery only until classified",
            "tier_basis": "unclassified-host"}


def tier_rank(tier: str) -> int:
    return TIER_ORDER.index(tier) if tier in TIER_ORDER else len(TIER_ORDER)


# ─────────────────────────────────────────────────────────────────────────────
# Source identifiers (§6.1). An identifier carries the basis on which it was
# obtained and whether that basis is evidence. `verified` is true only where the
# identifier came from a route the publisher controls — the URL the bytes were
# actually fetched from, or a row in the exchange's own index. An identifier
# read off a local filename is a lead: it names a document we believe these
# bytes to be, which is not the same as having obtained them from the exchange.
# ─────────────────────────────────────────────────────────────────────────────

EXCHANGE_ID_SCHEMES = ("asx_document_key", "asx_ids_id")

# Bases that constitute evidence of the identifier, strongest first.
VERIFIED_BASES = ("exchange-index-row", "retrieval-url")

# The basis an identifier gets when the exchange's index row it came from names
# a publication these bytes were shown to be a copy of, rather than these bytes
# themselves. Settled — it is not re-derived — but never `verified`: what the
# exchange served was the other artifact (§4.2).
INDEX_ROUTE_BASIS = "exchange-index-row (names the equivalent lodged artifact, not these bytes)"


def source_id(scheme: str, value: str, basis: str, verified: bool) -> dict:
    return {"scheme": scheme, "value": value, "basis": basis, "verified": verified}


def add_source_id(doc: dict, sid: dict) -> None:
    """Merge an identifier, upgrading an inferred one when evidence arrives.

    The same documentKey can reach a record twice: once guessed from a filename
    during the local pass, once from the URL the bytes were later fetched from.
    The second occurrence is evidence and must replace the first, or the record
    would keep claiming its strongest provenance is a filename."""
    for held in doc["source_ids"]:
        if held.get("scheme") == sid["scheme"] and held.get("value") == sid["value"]:
            if sid.get("verified") and not held.get("verified"):
                held.update(basis=sid["basis"], verified=True,
                            previously_inferred_from=held.get("basis"))
            return
    doc["source_ids"].append(dict(sid))


WEBLINK_ID_RE = re.compile(r"headlineid=(\d+)", re.I)


def identifiers_in_url(url: str, basis: str, verified: bool) -> list[dict]:
    """Publisher identifiers carried in an address."""
    out = []
    m = ASX_KEY_RE.search(url)
    if m:
        out.append(source_id("asx_document_key", "-".join(m.groups()), basis, verified))
    m = WEBLINK_ID_RE.search(url)
    if m:
        out.append(source_id("weblink_headline_id", m.group(1), basis, verified))
    return out


def verified_exchange_id(doc: dict) -> dict | None:
    """The identifier that would justify T1, or None. Absence of the `verified`
    key is read as unverified: a record written before identifiers carried a
    basis has not been shown to deserve promotion, and `reverify` re-derives it."""
    for sid in doc.get("source_ids", []):
        if sid.get("scheme") in EXCHANGE_ID_SCHEMES and sid.get("verified") is True:
            return sid
    return None


def note_inferred(doc: dict, inferred: dict | None) -> None:
    """Record filename-derived metadata as a lead, outside the evidence fields."""
    if not inferred:
        return
    held = doc.setdefault("inferred_provenance", [])
    if inferred not in held:
        held.append(inferred)
    for sid in inferred.get("source_ids", []):
        add_source_id(doc, sid)


# ─────────────────────────────────────────────────────────────────────────────
# Registries
# ─────────────────────────────────────────────────────────────────────────────

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=False) + "\n")
    tmp.replace(path)


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_documents() -> dict[str, dict]:
    return {d["sha256"]: d for d in read_jsonl(DOCUMENTS)}


# §6.1 order first, then everything else alphabetically. Without a declared
# order a field lands wherever the run that first set it happened to add it, so
# two runs that agree on every value still produce different bytes — and a
# registry that churns under an idempotent command is one nobody will re-run.
RECORD_ORDER = [
    "document_id", "sha256", "bytes", "mime_type", "title", "title_source",
    "publisher", "published_on", "reporting_dates", "observation_as_of",
    "authority_tier", "authority_domains", "tier_kind", "tier_note", "tier_basis",
    "source_ids", "url_aliases", "inferred_provenance", "retrieval_route",
    "equivalence", "coverage", "lodgement", "market_session",
    "object_locator", "storage_state", "refetchable", "verified",
    "verification_basis", "evidence_note", "supersedes", "subjects", "subject_basis",
    "legacy", "local_paths", "part_of", "parts", "acquisition", "review",
]


FIELD_RANK = {name: i for i, name in enumerate(RECORD_ORDER)}


def canonical(doc: dict) -> dict:
    return {k: doc[k] for k in
            sorted(doc, key=lambda k: (FIELD_RANK.get(k, len(FIELD_RANK)), k))}


def save_documents(docs: dict[str, dict]) -> None:
    ordered = sorted(docs.values(),
                     key=lambda d: (tier_rank(d.get("authority_tier", "T4")),
                                    d.get("published_on") or "",
                                    d.get("sha256", "")))
    write_jsonl(DOCUMENTS, [canonical(d) for d in ordered])


# Repeated failure has to cost something, or every run re-requests the same
# blocked host — the fetch storm §7.4 forbids. Each negative outcome books the
# earliest date that address may be asked again; the interval is longer where
# the failure looks permanent. A recorded date is enforced by `plan` and
# `acquire`, so booking one is not advisory.
RETRY_AFTER_DAYS = {"BLOCKED": 7, "LINK_DEAD": 30, "MISSING_OBJECT": 3, "NOT_PUBLISHED": 7}


def retry_after(result: str, checked_at: str) -> str | None:
    days = RETRY_AFTER_DAYS.get(result)
    if not days:
        return None
    try:
        base = datetime.fromisoformat(checked_at)
    except ValueError:
        base = datetime.now(timezone.utc)
    return (base + timedelta(days=days)).date().isoformat()


def availability(target: str, result: str, **kw) -> None:
    rec = {"checked_at": now(), "target": target, "result": result}
    rec.update(kw)
    if rec.get("next_retry_at") is None:
        rec["next_retry_at"] = retry_after(result, rec["checked_at"])
    if rec["next_retry_at"] is None:
        rec.pop("next_retry_at")
    append_jsonl(AVAILABILITY, rec)


def availability_by_address() -> dict[str, dict]:
    """The most recent outcome recorded against each address.

    An availability record is an event, not a state, so the answer to "may this
    be fetched?" is the LAST event mentioning the address — a success recorded
    later releases an earlier block. Successes name the document as the target
    and carry the address in `url`, so both fields are read."""
    latest: dict[str, dict] = {}
    for rec in read_jsonl(AVAILABILITY):
        for addr in (rec.get("url"), rec.get("target")):
            if not addr or not str(addr).startswith("http"):
                continue
            held = latest.get(addr)
            if held is None or (rec.get("checked_at") or "") >= (held.get("checked_at") or ""):
                latest[addr] = rec
    return latest


def retry_block(url: str, latest: dict[str, dict], today: str) -> dict | None:
    """The booked retry date standing in the way of fetching this URL, if any."""
    rec = latest.get(url) or {}
    retry = rec.get("next_retry_at")
    if retry and retry > today:
        return {"next_retry_at": retry, "last_result": rec.get("result"),
                "last_checked_at": rec.get("checked_at"),
                "last_diagnosis": rec.get("diagnosis")}
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Legacy citation index — what data/ already points at (§9 migration table)
# ─────────────────────────────────────────────────────────────────────────────

def legacy_index() -> dict[str, dict]:
    """url -> {title, date, type, subjects, notes:[...], citations:[...]}.

    `title` holds only what a `title` field in `data/` actually said. The
    analytical prose that sits beside a URL — `note`, `for`, a `source`
    description — is a reading OF the document, not the publisher's name for
    it, so it is carried separately and never offered as a title."""
    index: dict[str, dict] = {}

    def add(url: str, **kw):
        entry = index.setdefault(url, {"title": None, "date": None, "legacy_type": None,
                                       "subjects": [], "notes": [], "citations": []})
        for key in ("title", "date", "legacy_type"):
            if kw.get(key) and not entry[key]:
                entry[key] = kw[key]
        note = kw.get("note")
        if note and not any(n["text"] == note for n in entry["notes"]):
            entry["notes"].append({"text": note, "where": kw.get("where")})
        subj = kw.get("subject")
        if subj and subj not in entry["subjects"]:
            entry["subjects"].append(subj)
        cite = kw.get("citation")
        if cite and cite not in entry["citations"]:
            entry["citations"].append(cite)

    companies = json.loads((ROOT / "data/companies.json").read_text())
    for rec in list(companies.get("companies", [])) + list(companies.get("excluded", [])):
        ticker = rec.get("ticker")
        docs = rec.get("documents", {}) or {}
        used: dict[str, list[str]] = {}
        for field, spec in (rec.get("fields", {}) or {}).items():
            if isinstance(spec, dict) and spec.get("doc"):
                used.setdefault(spec["doc"], []).append(field)
        for proj in rec.get("execution_capital_projects", []) or []:
            for key, val in proj.items():
                if key.endswith("_doc") and val:
                    used.setdefault(val, []).append(f"{proj.get('project_id','project')}.{key}")
        for key, doc in docs.items():
            if not isinstance(doc, dict) or not doc.get("url"):
                continue
            add(doc["url"], title=doc.get("title"), date=doc.get("date"),
                note=doc.get("note"), legacy_type=doc.get("type"), subject=ticker,
                where=f"data/companies.json {ticker}.documents.{key}",
                citation={"file": "data/companies.json", "ticker": ticker,
                          "doc_key": key, "fields": sorted(used.get(key, []))})

    for name in ("data/jurisdictions.json", "data/sovereign.json", "data/market.json",
                 "tools/sources.json"):
        blob = json.loads((ROOT / name).read_text())
        subjects = subject_paths(blob)
        for url, path, sibling in walk_urls(blob):
            add(url,
                title=sibling.get("title"),
                note=sibling.get("note") or sibling.get("for") or sibling.get("source"),
                date=sibling.get("date") or sibling.get("as_of") or sibling.get("_sourced"),
                subject=nearest_subject(path, subjects),
                where=f"{name} {path}",
                citation={"file": name, "json_path": path})
    return index


def subject_paths(blob) -> dict[str, str]:
    """Map a JSON path prefix to the subject it belongs to — a ticker, a
    jurisdiction code, a country. Without this, `$.jurisdictions[3]` ends up in
    the store as though it were a subject in its own right."""
    out: dict[str, str] = {}

    def walk(node, path):
        if isinstance(node, dict):
            subj = node.get("ticker") or node.get("code") or node.get("country_code")
            if isinstance(subj, str) and 1 < len(subj) <= 12:
                out[path] = subj
            elif isinstance(node.get("name"), str) and "B1" not in node and "tests" not in node:
                pass
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(blob, "$")
    return out


def nearest_subject(path: str, subjects: dict[str, str]) -> str | None:
    best = None
    for prefix, subj in subjects.items():
        if path.startswith(prefix) and (best is None or len(prefix) > len(best[0])):
            best = (prefix, subj)
    return best[1] if best else None


def walk_urls(node, path="$"):
    """Yield (url, json_path, enclosing_dict) for every URL-looking string."""
    if isinstance(node, dict):
        for key, val in node.items():
            if isinstance(val, str) and val.startswith("http"):
                yield val, f"{path}.{key}", node
            else:
                yield from walk_urls(val, f"{path}.{key}")
    elif isinstance(node, list):
        for i, val in enumerate(node):
            if isinstance(val, str) and val.startswith("http"):
                yield val, f"{path}[{i}]", {}
            else:
                yield from walk_urls(val, f"{path}[{i}]")


# ──────────────────────────────────────────────────────────────────────────────
# Knowledge-plane migration (§6.2, §9). The legacy projection remains the
# production source of truth until the separate replay/cutover step. This pass
# records exactly what it says, including gaps that the old schema could not
# express, rather than manufacturing certainty during a storage migration.
# ────────────────────────────────────────────────────────────────────────────

CLAIM_STATES = {"ACCEPTED", "PROVISIONAL", "UNRESOLVED", "SUPERSEDED",
                "STALE", "REJECTED"}
ACTIVE_CLAIM_STATES = {"ACCEPTED", "PROVISIONAL"}

FIELD_SCOPES = {
    "pp_moz": ("Moz", "Proven and Probable Ore Reserves"),
    "mr_total_moz": ("Moz", "Mineral Resources inclusive of Ore Reserves"),
    "mi_non_reserve_moz": ("Moz", "Measured and Indicated excluding Ore Reserves"),
    "inferred_moz": ("Moz", "Inferred Mineral Resources"),
    "reserve_price_aud": ("AUD/oz", "Ore Reserve constraining price"),
    "resource_price_aud": ("AUD/oz", "Mineral Resource constraining price"),
    "aisc_aud_oz": ("AUD/oz", "all-in sustaining cost"),
    "production_koz_yr": ("koz/year", "annual gold production"),
    "shares_out_m": ("million shares", "total issued shares"),
    "advt_shares_m": ("million shares/day", "90-session average daily volume"),
    "remaining_execution_capex_aud_m": ("AUD million", "remaining execution capital"),
    "committed_within_gate2_horizon_aud_m":
        ("AUD million", "project committed capital in Gate 2 horizon"),
    "committed_capex_range_aud_m":
        ("AUD million", "issuer-published project committed-capital range"),
    "execution_capital_range_aud_m":
        ("AUD million", "issuer-published project execution-capital range"),
    "available_project_funding_aud_m": ("AUD million", "available project funding"),
    "committed_capex_aud_m": ("AUD million", "committed capital in Gate 2 horizon"),
    "net_debt_aud_m": ("AUD million", "net debt; negative is net cash"),
    "undrawn_facilities_aud_m": ("AUD million", "committed undrawn facilities"),
    "study_stage": ("enum", "development study stage"),
    "approvals_land_secured": ("boolean", "approvals and land-access test"),
}

PROJECT_FIELDS = {
    "committed_within_gate2_horizon_aud_m":
        ("committed_capex_doc", "AUD million", "committed capital in Gate 2 horizon"),
    "committed_capex_range_aud_m":
        ("committed_capex_doc", "AUD million", "issuer-published committed-capital range"),
    "remaining_execution_capex_aud_m":
        ("execution_capital_doc", "AUD million", "remaining execution capital"),
    "execution_capital_range_aud_m":
        ("execution_capital_doc", "AUD million", "issuer-published execution-capital range"),
}

LOCATION_RE = re.compile(
    r"\b(?:pages?\s+\d+(?:\s*[-–]\s*\d+)?|p\.?\s*\d+(?:\s*[-–]\s*\d+)?|"
    r"tables?\s+(?:\d+[A-Z]?|[A-Z]\d+)(?:\s*(?:and|&)\s*(?:\d+[A-Z]?|[A-Z]\d+))?|"
    r"notes?\s+\d+(?:\([a-z]\))?|appendix\s+[0-9A-Z]+|section\s+[0-9A-Z.]+)", re.I)
HISTORICAL_ALTERNATIVE_RE = re.compile(
    r"\b(?:corrected\s+from|supersedes?|replac(?:es|ed|ing)\b|withdrawn|"
    r"former\b.{0,100}\bnot retained|previous\b.{0,100}\b(?:wrong|stale))", re.I)


def stable_record_id(prefix: str, payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode()
    return f"{prefix}:sha256:{hashlib.sha256(raw).hexdigest()}"


def claim_value(value) -> dict:
    if isinstance(value, bool):
        kind = "boolean"
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        kind = "number"
    elif isinstance(value, str):
        kind = "string"
    elif isinstance(value, list):
        kind = "array"
    elif value is None:
        kind = "null"
    else:
        kind = "object"
    return {"type": kind, "value": value}


def field_scope(predicate: str, company: dict, *, project: dict | None = None) -> dict:
    unit, category = FIELD_SCOPES.get(predicate, (None, predicate.replace("_", " ")))
    if predicate.endswith("_share"):
        unit = "ratio"
    scope = {"entity_level": "issuer", "category": category}
    if unit:
        scope["unit"] = unit
    if unit and unit.startswith("AUD"):
        scope["currency"] = "AUD"
    if project:
        scope.update({"project_id": project.get("project_id"),
                      "project_scope": project.get("scope"),
                      "gate2_horizon_start": project.get("gate2_horizon_start"),
                      "gate2_horizon_end": project.get("gate2_horizon_end")})
    return {k: v for k, v in scope.items() if v is not None}


def exact_legacy_locator(predicate: str, note: str | None) -> dict | None:
    """Return only locations the legacy field itself stated explicitly.

    A number occurring somewhere in a PDF is not enough to identify the table
    or proposition it belongs to. Automated value searches therefore do not
    promote document-level citations to exact locators.
    """
    if predicate == "shares_out_m":
        return {"type": "json-pointer", "pointer": "/data/numOfShares", "exact": True}
    if predicate == "advt_shares_m":
        return {"type": "json-pointer", "pointer": "/data/volumeAverage", "exact": True}
    refs = []
    for match in LOCATION_RE.finditer(note or ""):
        ref = match.group(0).strip()
        if ref.lower() not in {r.lower() for r in refs}:
            refs.append(ref)
    if not refs:
        return None
    return {"type": "document-location", "references": refs,
            "exact": True, "basis": "location stated in legacy field note"}


def documents_by_url(docs: dict[str, dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for doc in docs.values():
        for alias in doc.get("url_aliases", []):
            out.setdefault(alias["url"], []).append(doc)
    return out


def resolve_legacy_document(company: dict, doc_key: str, predicate: str,
                            docs: dict[str, dict], by_url: dict[str, list[dict]]) \
                            -> tuple[dict | None, dict | None]:
    legacy = (company.get("documents") or {}).get(doc_key) or {}
    matches = by_url.get(legacy.get("url"), [])
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, {"code": "AMBIGUOUS_URL_VERSION",
                      "detail": "legacy URL resolves to more than one immutable artifact"}

    # The legacy AUC secondary page was not retained, but the already archived
    # lodged June quarterly establishes the adverse boolean directly: key
    # approvals were still outstanding. Use that stronger evidence without
    # changing the pre-cutover `data/` document key.
    if company.get("ticker") == "AUC" and predicate == "approvals_land_secured":
        candidates = [d for d in docs.values()
                      if "AUC" in (d.get("subjects") or [])
                      and d.get("published_on") == "2026-07-13"
                      and "Quarterly Activities" in (d.get("title") or "")]
        if len(candidates) == 1:
            return candidates[0], {
                "code": "HIGHER_TIER_MIGRATION_SUBSTITUTE",
                "legacy_url": legacy.get("url"),
                "as_of": "2026-06-30",
                "detail": "lodged June quarterly, PDF page 6 Permitting and Approvals, "
                          "states that as of June 2026 approvals remained under assessment"}
    return None, {"code": "EVIDENCE_ARTIFACT_NOT_HELD", "legacy_url": legacy.get("url")}


def preserve_timestamps(records: list[dict], old_records: list[dict], id_key: str,
                        run_at: str) -> list[dict]:
    old = {r.get(id_key): r for r in old_records}
    for rec in records:
        prior = old.get(rec[id_key])
        rec["created_at"] = prior.get("created_at", run_at) if prior else run_at
        if prior:
            before = {k: v for k, v in prior.items() if k not in ("created_at", "updated_at")}
            after = {k: v for k, v in rec.items() if k not in ("created_at", "updated_at")}
            rec["updated_at"] = prior.get("updated_at", rec["created_at"]) \
                if before == after else run_at
        else:
            rec["updated_at"] = run_at
    return records


def build_company_claim(company: dict, predicate: str, spec: dict, path: str,
                        doc_key: str, docs: dict[str, dict], by_url: dict[str, list[dict]],
                        *, project: dict | None = None) -> tuple[dict, list[str]]:
    doc, resolution = resolve_legacy_document(company, doc_key, predicate, docs, by_url)
    legacy_doc = (company.get("documents") or {}).get(doc_key) or {}
    note = spec.get("note")
    locator = exact_legacy_locator(predicate, note)
    if resolution and resolution.get("code") == "HIGHER_TIER_MIGRATION_SUBSTITUTE":
        locator = {"type": "pdf-location", "page": 6,
                   "section": "Permitting and Approvals", "exact": True}

    exceptions = []
    if not locator:
        exceptions.append("EXACT_LOCATOR_NOT_CAPTURED")
    if spec.get("v") is None:
        value = claim_value(None)
    else:
        value = claim_value(spec["v"])
    scope = field_scope(predicate, company, project=project)
    as_of = spec.get("as_of")
    if project and not as_of:
        as_of = project.get("as_of")
    if not as_of and resolution and resolution.get("as_of"):
        as_of = resolution["as_of"]
    if not as_of:
        exceptions.append("AS_OF_NOT_SEPARATELY_CAPTURED")

    volatile_mismatch = bool(
        doc and doc.get("tier_kind") == "volatile"
        and legacy_doc.get("date")
        and (doc.get("observation_as_of") or doc.get("published_on")) != legacy_doc.get("date"))
    if volatile_mismatch:
        as_of = legacy_doc.get("date")
        state = "STALE"
        exceptions.append("POINT_IN_TIME_BYTES_NOT_ARCHIVED")
    elif spec.get("evidence_state") == "UNRESOLVED" or spec.get("v") is None:
        state = "UNRESOLVED"
    elif doc is None or doc.get("authority_tier") == "T4":
        state = "REJECTED"
    elif doc.get("authority_tier") == "T3":
        state = "PROVISIONAL"
    else:
        state = "ACCEPTED"

    key = {"subject": company["ticker"], "predicate": predicate,
           "scope": scope, "as_of": as_of}
    identity = {"claim_key": key, "value": value, "document_id":
                doc.get("document_id") if doc else None, "projection": path}
    claim = {
        "claim_id": stable_record_id("claim", identity),
        "claim_key": key,
        "value": value,
        "reported_value": None if (note or "").lstrip().upper().startswith("DERIVED")
                          else value,
        "reported_range": spec.get("range"),
        "accuracy_range": spec.get("accuracy_range"),
        "evidence_state": spec.get("evidence_state", "POINT"),
        "evidence": {
            "document_id": doc.get("document_id") if doc else None,
            "locator": locator,
            "locator_state": "EXACT" if locator else "LEGACY_DOCUMENT_LEVEL_ONLY",
            "legacy_document_key": doc_key,
            "legacy_url": legacy_doc.get("url"),
        },
        "authority_tier": doc.get("authority_tier") if doc else "T4",
        "authority_domains": doc.get("authority_domains", []) if doc else [],
        "publication_date": doc.get("published_on") if doc else legacy_doc.get("date"),
        "state": state,
        "projectable": state in ACTIVE_CLAIM_STATES,
        "decision": {"code": "LEGACY_PROJECTION_BACKFILL",
                     "reason": "value and status preserved during additive KB migration",
                     "producing_tool": "tools/kb.py backfill-claims"},
        "projection": {"file": "data/companies.json", "path": path},
        "legacy_note": note,
        "supersedes": [],
    }
    if resolution:
        claim["source_resolution"] = resolution
    if volatile_mismatch:
        claim["evidence"]["supports_claim_as_of"] = False
        claim["decision"] = {
            "code": "POINT_IN_TIME_ARTIFACT_UNRECOVERABLE",
            "reason": "the cited endpoint was archived on a later date and cannot evidence "
                      "the legacy observation; the value is retained only as stale history",
            "producing_tool": "tools/kb.py backfill-claims"}
        claim["projectable"] = False
    if exceptions:
        claim["migration"] = {"grandfathered_from": path, "exceptions": exceptions}
    if (note or "").lstrip().upper().startswith("DERIVED"):
        claim["derivation"] = {"formula": note, "dependencies": [],
                               "rounding": "as recorded in the legacy projection",
                               "output_unit": scope.get("unit")}
        claim.setdefault("migration", {"grandfathered_from": path, "exceptions": []})
        claim["migration"]["exceptions"].append("DERIVATION_DEPENDENCIES_NOT_ATOMIZED")
    return claim, exceptions


def current_key_statistics_claims(docs: dict[str, dict]) -> list[dict]:
    claims = []
    for doc in docs.values():
        aliases = [a.get("url", "") for a in doc.get("url_aliases", [])]
        if not any("/key-statistics" in url for url in aliases):
            continue
        subjects = doc.get("subjects") or []
        if len(subjects) != 1:
            continue
        try:
            payload = json.loads((ROOT / doc["object_locator"]).read_text())["data"]
        except (OSError, ValueError, KeyError):
            continue
        as_of = doc.get("observation_as_of") or doc.get("published_on")
        for predicate, source_key, unit in (
                ("shares_out_m", "numOfShares", "million shares"),
                ("advt_shares_m", "volumeAverage", "million shares/day")):
            if payload.get(source_key) is None:
                continue
            value = payload[source_key] / 1_000_000
            scope = {"entity_level": "issuer", "category": FIELD_SCOPES[predicate][1],
                     "unit": unit}
            key = {"subject": subjects[0], "predicate": predicate,
                   "scope": scope, "as_of": as_of}
            identity = {"claim_key": key, "value": value, "document_id": doc["document_id"]}
            claims.append({
                "claim_id": stable_record_id("claim", identity), "claim_key": key,
                "value": claim_value(value),
                "reported_value": claim_value(payload[source_key]),
                "normalization": {"formula": f"{source_key} / 1,000,000",
                                  "output_unit": unit},
                "reported_range": None, "accuracy_range": None,
                "evidence_state": "POINT",
                "evidence": {"document_id": doc["document_id"],
                             "locator": exact_legacy_locator(predicate, None),
                             "locator_state": "EXACT"},
                "authority_tier": doc["authority_tier"],
                "authority_domains": doc["authority_domains"],
                "publication_date": doc.get("published_on"), "state": "ACCEPTED",
                "projectable": False,
                "decision": {"code": "ARCHIVED_POINT_IN_TIME_OBSERVATION",
                             "reason": "accepted as a new dated observation; not projected "
                                       "outside a reviewed rebalance",
                             "producing_tool": "tools/kb.py backfill-claims"},
                "supersedes": [],
            })
    return claims


def quarantine_record(claim: dict, path: str, reason_code: str, detail: str) -> dict:
    candidate = {"file": "data/companies.json", "pointer": f"{path}/note"}
    payload = {"candidate": candidate, "reason_code": reason_code,
               "related_claim": claim["claim_id"]}
    rec = {"quarantine_id": stable_record_id("quarantine", payload),
           "candidate": candidate, "reason_code": reason_code,
           "reason": detail, "decision_source": "legacy field note",
           "producing_tool": "tools/kb.py backfill-claims"}
    if claim["state"] in ACTIVE_CLAIM_STATES:
        rec["blocked_by"] = claim["claim_id"]
    else:
        rec["related_claim"] = claim["claim_id"]
    return rec


def merge_backfill_claims(generated: list[dict], previous: list[dict]) -> list[dict]:
    """Re-running the migration must not undo researched knowledge.

    Backfill owns exactly what it produces from `data/`. A claim registered
    through `register-claim` is carried across untouched, and a backfilled claim
    that has since been superseded keeps its supersession — otherwise the second
    run would quietly resurrect a replaced value and leave two active claims for
    one key."""
    by_previous = {c["claim_id"]: c for c in previous}
    for claim in generated:
        prior = by_previous.get(claim["claim_id"])
        if not (prior and prior.get("superseded_by")):
            continue
        claim["state"] = prior["state"]
        claim["projectable"] = prior.get("projectable", claim["projectable"])
        claim["superseded_by"] = prior["superseded_by"]
        if prior.get("superseded"):
            claim["superseded"] = prior["superseded"]
        if "projection" in prior:
            claim["projection"] = prior["projection"]
        else:
            claim.pop("projection", None)
        if prior.get("projection_history"):
            claim["projection_history"] = prior["projection_history"]
    produced = {c["claim_id"] for c in generated}
    return generated + [c for c in previous if c["claim_id"] not in produced]


def cmd_backfill_claims(args) -> int:
    docs = load_documents()
    if not docs:
        print("cannot backfill claims: knowledge/documents.jsonl is empty", file=sys.stderr)
        return 1
    blob = json.loads((ROOT / "data/companies.json").read_text())
    by_url = documents_by_url(docs)
    claims: list[dict] = []
    quarantine: list[dict] = []
    for group in ("companies", "excluded"):
        for ci, company in enumerate(blob.get(group, [])):
            for predicate, spec in (company.get("fields") or {}).items():
                path = f"/{group}/{ci}/fields/{predicate}"
                claim, _ = build_company_claim(company, predicate, spec, path,
                                                spec["doc"], docs, by_url)
                claims.append(claim)
                note = spec.get("note") or ""
                if spec.get("evidence_state") == "UNRESOLVED":
                    quarantine.append(quarantine_record(
                        claim, path, "WITHHELD_UNRESOLVED_CANDIDATE",
                        "the legacy record explicitly withholds a candidate because the "
                        "controlling evidence does not establish a projectable value"))
                if HISTORICAL_ALTERNATIVE_RE.search(note):
                    quarantine.append(quarantine_record(
                        claim, path, "SUPERSEDED_OR_REJECTED_LEGACY_CANDIDATE",
                        "the field note records an earlier candidate as corrected, "
                        "superseded, replaced, or withdrawn; its value is deliberately "
                        "not copied into quarantine"))

            for pi, project in enumerate(company.get("execution_capital_projects") or []):
                for predicate, (doc_field, _unit, _category) in PROJECT_FIELDS.items():
                    if predicate not in project or not project.get(doc_field):
                        continue
                    path = f"/{group}/{ci}/execution_capital_projects/{pi}/{predicate}"
                    evidence_state = (project.get("committed_capex_state")
                                      if predicate.startswith("committed")
                                      else project.get("execution_capital_state"))
                    spec = {"v": project[predicate], "doc": project[doc_field],
                            "as_of": project.get("as_of"),
                            "evidence_state": evidence_state or "POINT",
                            "note": project.get("coverage_note")}
                    claim, _ = build_company_claim(company, predicate, spec, path,
                                                    spec["doc"], docs, by_url,
                                                    project=project)
                    claims.append(claim)

    observed = current_key_statistics_claims(docs)
    claims.extend(observed)
    current_by_subject_predicate = {
        (c["claim_key"]["subject"], c["claim_key"]["predicate"]): c
        for c in observed
    }
    for claim in claims:
        if "POINT_IN_TIME_BYTES_NOT_ARCHIVED" not in (claim.get("migration") or {}).get(
                "exceptions", []):
            continue
        successor = current_by_subject_predicate.get(
            (claim["claim_key"]["subject"], claim["claim_key"]["predicate"]))
        if successor:
            claim["superseded_by"] = successor["claim_id"]
            if claim["claim_id"] not in successor["supersedes"]:
                successor["supersedes"].append(claim["claim_id"])

    run_at = now()
    previous_claims = read_jsonl(CLAIMS)
    previous_quarantine = read_jsonl(QUARANTINE)
    claims = merge_backfill_claims(claims, previous_claims)
    carried_q = {q["quarantine_id"] for q in quarantine}
    quarantine.extend(q for q in previous_quarantine
                      if q["quarantine_id"] not in carried_q
                      and q.get("producing_tool") != "tools/kb.py backfill-claims")
    claims = preserve_timestamps(claims, previous_claims, "claim_id", run_at)
    quarantine = preserve_timestamps(quarantine, previous_quarantine,
                                     "quarantine_id", run_at)
    claims.sort(key=claim_sort_key)
    quarantine.sort(key=quarantine_sort_key)
    if not args.dry_run:
        write_jsonl(CLAIMS, claims)
        write_jsonl(QUARANTINE, quarantine)
    states = Counter(c["state"] for c in claims)
    exceptions = sum(bool((c.get("migration") or {}).get("exceptions")) for c in claims)
    action = "would write" if args.dry_run else "wrote"
    print(f"{action} {len(claims)} claims ({', '.join(f'{k} {v}' for k, v in sorted(states.items()))})")
    print(f"{action} {len(quarantine)} pointer-only quarantine records; "
          f"{exceptions} claims carry explicit legacy migration exceptions")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge plane: registering a researched claim (§5.1, §6.2, §7.3)
#
# `backfill-claims` migrates what `data/` already asserted. This is the other
# write path: a claim established by reading a source, which the migration
# exceptions explicitly do not grandfather. It therefore demands the complete
# §6.2 record — an archived artifact, an exact locator, a verbatim excerpt, an
# as-of date kept apart from the publication date — runs the §5.1 precedence
# sequence against every existing claim for the same key, and refuses rather
# than guesses. Supersession is a link, never an in-place edit: the predecessor
# keeps its record, its evidence and its decision, and gains a pointer forward.
# ─────────────────────────────────────────────────────────────────────────────

EVIDENCE_STATES = {"POINT", "UPPER_BOUND", "LOWER_BOUND", "CARRY_FORWARD", "UNRESOLVED"}

# An active claim is normally projectable. These decision codes are the two
# reasons a claim may be accepted and still deliberately held out of `data/`:
# an archived observation at a new as-of, and a fact whose adoption is a
# rebalance decision rather than a storage one.
HELD_FROM_PROJECTION_CODES = {"ARCHIVED_POINT_IN_TIME_OBSERVATION",
                              "HELD_FOR_REVIEWED_REBALANCE"}
SAME_TIER_CORRECTION_BASES = {"EXPLICIT_CORRECTION", "EXPLICIT_RESTATEMENT",
                              "SAME_AS_OF_UPDATE"}

REGISTER_TOOL = "tools/kb.py register-claim"


class ClaimSpecError(ValueError):
    """A registration the store refuses. The message says which rule."""


class SameTierConflict(ClaimSpecError):
    """Controlling-tier evidence conflicts and must produce UNRESOLVED state."""

    def __init__(self, where: str, conflicting_ids: list[str]):
        self.conflicting_ids = conflicting_ids
        super().__init__(f"{where}: incompatible controlling-tier evidence requires an "
                         "UNRESOLVED decision")


def claim_sort_key(claim: dict) -> tuple:
    key = claim.get("claim_key") or {}
    return (key.get("subject") or "", key.get("predicate") or "",
            key.get("as_of") or "", claim.get("claim_id") or "")


def quarantine_sort_key(rec: dict) -> tuple:
    candidate = rec.get("candidate") or {}
    return (candidate.get("pointer") or candidate.get("document_id") or "",
            rec.get("reason_code") or "", rec.get("quarantine_id") or "")


def require(spec: dict, field: str, where: str):
    value = spec.get(field)
    if value in (None, "", [], {}):
        raise ClaimSpecError(f"{where}: {field} is required")
    return value


ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def numeric(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) \
        else None


def values_conflict(a: dict, b: dict) -> bool:
    """Do two claims for one key assert things that cannot both be true?

    Only after unit conversion, rounding and stated ranges (§5). Ranges are the
    issuer's, so two candidates whose published ranges overlap are not in
    conflict; two point values are, unless they agree to the precision the
    coarser of them was reported at."""
    left, right = (a.get("value") or {}).get("value"), (b.get("value") or {}).get("value")
    if left is None or right is None:
        return False                     # silence is not a claim (§5)
    lo, ro = numeric(left), numeric(right)
    if lo is None or ro is None:
        return left != right
    for one, other in ((a, b), (b, a)):
        span = one.get("reported_range") or one.get("accuracy_range")
        point = numeric((other.get("value") or {}).get("value"))
        if span and len(span) == 2 and point is not None \
                and float(span[0]) <= point <= float(span[1]):
            return False
    # Compare at the precision of the COARSER report: A$600M and A$600.4M are
    # the same fact stated to different places, and the whole-million report is
    # what decides. `left`/`right` are used rather than the floats because a
    # float conversion invents decimal places the publisher did not print.
    one, other = decimal.Decimal(str(left)), decimal.Decimal(str(right))
    quantum = decimal.Decimal(1).scaleb(max(one.as_tuple().exponent,
                                            other.as_tuple().exponent))
    return one.quantize(quantum) != other.quantize(quantum)


def registration_scope(spec: dict, where: str) -> dict:
    """The claim's scope, stated by the researcher or built from the field
    definition. Units and currency are part of identity (§5), so a predicate the
    schema knows may not be registered under a different unit by accident."""
    project = spec.get("project")
    scope = dict(spec.get("scope") or {})
    if not scope:
        unit, category = FIELD_SCOPES.get(spec["predicate"],
                                          (None, spec["predicate"].replace("_", " ")))
        scope = {"entity_level": spec.get("entity_level", "issuer"), "category": category}
        if unit:
            scope["unit"] = unit
        if unit and unit.startswith("AUD"):
            scope["currency"] = "AUD"
        if project:
            scope.update({k: project.get(k) for k in
                          ("project_id", "project_scope",
                           "gate2_horizon_start", "gate2_horizon_end")})
        scope = {k: v for k, v in scope.items() if v is not None}
    known = FIELD_SCOPES.get(spec["predicate"])
    if known and scope.get("unit") and scope["unit"] != known[0]:
        raise ClaimSpecError(
            f"{where}: unit {scope['unit']!r} is not the {spec['predicate']} unit "
            f"{known[0]!r}; normalize the value or register a different predicate")
    if not scope.get("entity_level") or not scope.get("category"):
        raise ClaimSpecError(f"{where}: scope needs at least entity_level and category")
    if str(scope.get("unit", "")).startswith("AUD") and not scope.get("currency"):
        raise ClaimSpecError(f"{where}: an AUD-denominated scope must state its currency")
    return scope


def build_registered_claim(spec: dict, docs: dict[str, dict], run_at: str) -> dict:
    where = f"{spec.get('subject')}/{spec.get('predicate')}"
    for field in ("subject", "predicate", "as_of", "document_id", "state",
                  "evidence_state", "decision"):
        require(spec, field, where)
    state = spec["state"]
    if state not in CLAIM_STATES:
        raise ClaimSpecError(f"{where}: {state!r} is not a claim state")
    if spec["evidence_state"] not in EVIDENCE_STATES:
        raise ClaimSpecError(f"{where}: {spec['evidence_state']!r} is not an evidence state")
    as_of = str(spec["as_of"])
    if not ISO_DATE_RE.fullmatch(as_of):
        raise ClaimSpecError(f"{where}: as_of must be an ISO date, not {as_of!r}; "
                             "a new claim does not get the legacy as-of exception")

    digest = str(spec["document_id"]).removeprefix("sha256:")
    doc = docs.get(digest)
    if not doc:
        raise ClaimSpecError(
            f"{where}: evidence document sha256:{digest[:16]}… is not in the store — "
            "archive the exact bytes with ingest-file or asx-acquire before accepting it")
    if not (ROOT / doc.get("object_locator", "")).exists():
        raise ClaimSpecError(f"{where}: the evidence object is missing from the store")

    published = doc.get("published_on") or spec.get("publication_date")
    if spec.get("publication_date") and doc.get("published_on") \
            and spec["publication_date"] != doc["published_on"]:
        raise ClaimSpecError(
            f"{where}: publication_date {spec['publication_date']} contradicts the "
            f"artifact's own {doc['published_on']}")
    if not published:
        raise ClaimSpecError(f"{where}: the artifact carries no publication date and the "
                             "spec supplies none")

    locator = spec.get("locator")
    excerpt = spec.get("excerpt")
    if state in ACTIVE_CLAIM_STATES:
        if not (isinstance(locator, dict) and locator.get("exact")):
            raise ClaimSpecError(
                f"{where}: an active claim needs an exact page/table/note/section/image "
                "locator; a document-level citation is incomplete (§6.2)")
        if not (excerpt and str(excerpt).strip()):
            raise ClaimSpecError(f"{where}: an active claim needs a verbatim excerpt")
        if spec.get("value") is None:
            raise ClaimSpecError(
                f"{where}: a missing amount stays UNRESOLVED — an absent value is never "
                "accepted as a zero or a silence (§2.8)")

    scope = registration_scope(spec, where)
    key = {"subject": spec["subject"], "predicate": spec["predicate"],
           "scope": scope, "as_of": as_of}
    value = claim_value(spec.get("value"))
    reported = claim_value(spec["reported_value"]) if "reported_value" in spec else value
    identity = {"claim_key": key, "value": value, "document_id": doc["document_id"],
                "locator": locator}
    claim = {
        "claim_id": stable_record_id("claim", identity),
        "claim_key": key,
        "value": value,
        "reported_value": reported,
        "reported_range": spec.get("reported_range"),
        "accuracy_range": spec.get("accuracy_range"),
        "evidence_state": spec["evidence_state"],
        "evidence": {
            "document_id": doc["document_id"],
            "locator": locator,
            "locator_state": "EXACT" if (locator or {}).get("exact") else "PARTIAL",
            "excerpt": excerpt,
            "retrieval_url": next((a["url"] for a in doc.get("url_aliases", [])), None),
        },
        "authority_tier": doc["authority_tier"],
        "authority_domains": doc["authority_domains"],
        "publication_date": published,
        "state": state,
        "projectable": state in ACTIVE_CLAIM_STATES and not spec.get("held_from_projection"),
        "decision": {**spec["decision"], "producing_tool": REGISTER_TOOL},
        "supersedes": list(spec.get("supersedes") or []),
    }
    if spec.get("reported_unit"):
        claim["reported_unit"] = spec["reported_unit"]
    if spec.get("normalization"):
        claim["normalization"] = spec["normalization"]
    if spec.get("note"):
        claim["note"] = spec["note"]
    if spec.get("research"):
        claim["research"] = spec["research"]
    if spec.get("conflicts"):
        claim["conflicts"] = spec["conflicts"]
    if spec.get("derivation"):
        derivation = spec["derivation"]
        if not derivation.get("formula") or not derivation.get("dependencies"):
            raise ClaimSpecError(f"{where}: a derivation names its formula and every "
                                 "ordered dependency claim id (§2.10)")
        claim["derivation"] = derivation
    if spec.get("projection"):
        claim["projection"] = spec["projection"]
    if spec.get("projection_pending"):
        claim["projection_pending"] = spec["projection_pending"]
    if spec.get("held_from_projection"):
        if claim["decision"].get("code") not in HELD_FROM_PROJECTION_CODES:
            raise ClaimSpecError(
                f"{where}: a claim held out of the projection must say why with one of "
                f"{sorted(HELD_FROM_PROJECTION_CODES)}")
        if claim.get("projection"):
            raise ClaimSpecError(f"{where}: a held claim cannot also be the live "
                                 "projection basis for a field")
    if claim.get("projection") and claim["state"] not in ACTIVE_CLAIM_STATES:
        raise ClaimSpecError(f"{where}: a non-active claim cannot be a projection basis")
    return claim


def check_precedence(claim: dict, existing: list[dict], superseding: set[str],
                     *, allow_same_tier_correction: bool = False) -> None:
    """§5.1, run for this one normalized key.

    The barrier is authority, not recency: a lower-tier candidate may fill a gap
    but may never replace, average with, widen or narrow an incompatible claim
    from a higher tier. An incompatible candidate at the SAME tier does not pick
    a winner either — it leaves the key unresolved."""
    encoded = json.dumps(claim["claim_key"], sort_keys=True)
    where = f"{claim['claim_key']['subject']}/{claim['claim_key']['predicate']}"
    same_tier_conflicts = []
    for other in existing:
        if other["claim_id"] == claim["claim_id"]:
            continue
        same_key = json.dumps(other.get("claim_key"), sort_keys=True) == encoded
        if not same_key:
            continue
        mine, theirs = TIER_ORDER.index(claim["authority_tier"]), \
            TIER_ORDER.index(other.get("authority_tier", "T4"))
        conflicts = values_conflict(claim, other)
        if other["claim_id"] in superseding:
            if conflicts and mine > theirs:
                raise ClaimSpecError(
                    f"{where}: {claim['authority_tier']} evidence cannot supersede an "
                    f"incompatible {other['authority_tier']} claim "
                    f"({other['claim_id'][:24]}…) — quarantine the candidate and seek a "
                    "correction at the controlling tier (§2.6)")
            if conflicts and mine == theirs and not allow_same_tier_correction:
                same_tier_conflicts.append(other["claim_id"])
            continue
        if other.get("state") in ACTIVE_CLAIM_STATES:
            if conflicts and mine > theirs:
                raise ClaimSpecError(
                    f"{where}: blocked by higher-tier active claim "
                    f"{other['claim_id'][:24]}… ({other['authority_tier']}); register a "
                    "quarantine pointer instead of a second value (§2.7)")
            if conflicts and mine == theirs:
                same_tier_conflicts.append(other["claim_id"])
                continue
            if claim["state"] in ACTIVE_CLAIM_STATES:
                raise ClaimSpecError(
                    f"{where}: {other['claim_id'][:24]}… is already active for this key; "
                    "supersede it explicitly or register at a different as-of")
        elif other.get("state") == "UNRESOLVED" and claim["state"] in ACTIVE_CLAIM_STATES:
            raise ClaimSpecError(
                f"{where}: {other['claim_id'][:24]}… holds this key UNRESOLVED; a claim "
                "that resolves it must supersede it so the ledger keeps one answer")
    if same_tier_conflicts:
        raise SameTierConflict(where, sorted(set(same_tier_conflicts)))


def validate_supersession_relation(claim: dict, predecessor: dict) -> None:
    """A supersession may refine scope or date, but cannot jump to another fact."""
    old_key = predecessor.get("claim_key") or {}
    new_key = claim.get("claim_key") or {}
    where = f"{new_key.get('subject')}/{new_key.get('predicate')}"
    if predecessor.get("claim_id") == claim.get("claim_id"):
        raise ClaimSpecError(f"{where}: a claim cannot supersede itself")
    if (old_key.get("subject"), old_key.get("predicate")) != \
            (new_key.get("subject"), new_key.get("predicate")):
        raise ClaimSpecError(
            f"{where}: cannot supersede unrelated claim {predecessor.get('claim_id')} "
            f"for {old_key.get('subject')}/{old_key.get('predicate')}")
    old_path = (predecessor.get("projection") or {}).get("path")
    new_path = (claim.get("projection") or {}).get("path")
    if old_path and new_path and old_path != new_path:
        raise ClaimSpecError(
            f"{where}: supersession projection path {new_path!r} does not match "
            f"the predecessor path {old_path!r}")
    successor = predecessor.get("superseded_by")
    if successor and successor != claim.get("claim_id"):
        raise ClaimSpecError(
            f"{where}: predecessor is already superseded by {successor}; history is immutable")


def unresolved_conflict_claim(candidate: dict, incumbents: list[dict], run_at: str) -> dict:
    """Create one non-projectable decision that preserves both evidence paths."""
    alternatives = []
    for claim in [*incumbents, candidate]:
        alternatives.append({
            "claim_id": claim["claim_id"],
            "value": claim.get("value"),
            "document_id": (claim.get("evidence") or {}).get("document_id"),
            "locator": (claim.get("evidence") or {}).get("locator"),
            "authority_tier": claim.get("authority_tier"),
        })
    alternatives.sort(key=lambda item: item["claim_id"])
    identity = {"claim_key": candidate["claim_key"], "state": "UNRESOLVED",
                "alternatives": alternatives}
    record = {
        **candidate,
        "claim_id": stable_record_id("claim", identity),
        "value": claim_value(None),
        "reported_value": None,
        "reported_range": None,
        "accuracy_range": None,
        "evidence_state": "UNRESOLVED",
        "state": "UNRESOLVED",
        "projectable": False,
        "decision": {
            "code": "CONTROLLING_TIER_CONFLICT",
            "reason": "incompatible evidence remains at the same controlling tier; "
                      "no value is selected",
            "producing_tool": REGISTER_TOOL,
        },
        "supersedes": [c["claim_id"] for c in incumbents],
        "conflicts": alternatives,
        "created_at": run_at,
        "updated_at": run_at,
    }
    if candidate.get("projection"):
        record["projection_candidate"] = candidate["projection"]
    record.pop("projection", None)
    record.pop("projection_pending", None)
    return record


def apply_supersession(predecessor: dict, claim: dict, run_at: str,
                       reason: str, state: str = "SUPERSEDED",
                       *, retire_projection: bool = False) -> None:
    """History is immutable (§2.9): the predecessor keeps its evidence, value and
    decision, and gains a link forward. Only the projection basis moves, because
    two records cannot both be what `data/` reads."""
    if state not in ("SUPERSEDED", "STALE"):
        raise ClaimSpecError(f"{predecessor['claim_id']}: cannot supersede into {state!r}")
    predecessor["state"] = state
    predecessor["projectable"] = False
    predecessor["superseded_by"] = claim["claim_id"]
    predecessor["superseded"] = {"by": claim["claim_id"], "at": run_at, "reason": reason,
                                 "producing_tool": REGISTER_TOOL}
    if (claim.get("projection") or retire_projection) and predecessor.get("projection"):
        predecessor.setdefault("projection_history", []).append(predecessor.pop("projection"))


def build_registered_quarantine(spec: dict, by_id: dict[str, dict]) -> dict:
    candidate = spec.get("candidate") or {}
    if not (candidate.get("pointer") or candidate.get("document_id")):
        raise ClaimSpecError("quarantine: the candidate needs a pointer or a document_id")
    forbidden = {"value", "typed_value", "reported_value", "range", "reported_range"}
    if forbidden.intersection(candidate) or forbidden.intersection(spec):
        raise ClaimSpecError("quarantine holds pointers and reasons, never a second "
                             "active value (§2.7)")
    linked = spec.get("blocked_by") or spec.get("related_claim")
    if linked not in by_id:
        raise ClaimSpecError(f"quarantine: linked claim {linked} does not exist")
    if spec.get("blocked_by") and by_id[linked]["state"] not in ACTIVE_CLAIM_STATES:
        raise ClaimSpecError(f"quarantine: blocked_by must name the controlling ACTIVE "
                             f"claim; {linked[:24]}… is {by_id[linked]['state']}")
    payload = {"candidate": candidate, "reason_code": require(spec, "reason_code",
                                                              "quarantine"),
               "related_claim": linked}
    rec = {"quarantine_id": stable_record_id("quarantine", payload),
           "candidate": candidate, "reason_code": spec["reason_code"],
           "reason": require(spec, "reason", "quarantine"),
           "decision_source": spec.get("decision_source", "registered research finding"),
           "producing_tool": REGISTER_TOOL}
    rec["blocked_by" if spec.get("blocked_by") else "related_claim"] = linked
    return rec


def cmd_register_claim(args) -> int:
    """Register researched claims and their supersessions in one atomic pass."""
    spec = json.loads(Path(args.file).read_text())
    if isinstance(spec, list):
        spec = {"claims": spec}
    docs = load_documents()
    claims = read_jsonl(CLAIMS)
    by_id = {c["claim_id"]: c for c in claims}
    run_at = now()
    registered, unchanged, superseded = [], [], []

    try:
        for entry in spec.get("claims", []):
            claim = build_registered_claim(entry, docs, run_at)
            targets = list(entry.get("supersedes") or [])
            for target in targets:
                if target not in by_id:
                    raise ClaimSpecError(
                        f"{claim['claim_key']['subject']}/{claim['claim_key']['predicate']}: "
                        f"supersedes unknown claim {target}")
                validate_supersession_relation(claim, by_id[target])
            prior = by_id.get(claim["claim_id"])
            if prior and {k: v for k, v in prior.items()
                          if k not in ("created_at", "updated_at")} == claim:
                unchanged.append(claim)
                continue
            if prior:
                raise ClaimSpecError(
                    f"{claim['claim_key']['subject']}/{claim['claim_key']['predicate']}: "
                    f"claim identity {claim['claim_id']} already exists with different "
                    "content; history is immutable, so register a new claim and "
                    "supersede the old one")

            # An identical retry after a same-tier conflict finds the aggregate
            # decision, not the unstored candidate assertion.
            encoded = json.dumps(claim["claim_key"], sort_keys=True)
            settled = next((held for held in claims
                            if held.get("state") == "UNRESOLVED"
                            and json.dumps(held.get("claim_key"), sort_keys=True) == encoded
                            and any(alt.get("claim_id") == claim["claim_id"]
                                    for alt in held.get("conflicts", []))), None)
            if settled:
                unchanged.append(settled)
                continue

            conflict_mode = False
            try:
                check_precedence(
                    claim, claims, set(targets),
                    allow_same_tier_correction=(
                        entry.get("supersession_basis") in SAME_TIER_CORRECTION_BASES))
            except SameTierConflict as conflict:
                conflict_mode = True
                targets = list(dict.fromkeys([*targets, *conflict.conflicting_ids]))
                incumbents = [by_id[target] for target in targets]
                for incumbent in incumbents:
                    validate_supersession_relation(claim, incumbent)
                claim = unresolved_conflict_claim(claim, incumbents, run_at)
            for target in targets:
                apply_supersession(
                    by_id[target], claim, run_at,
                    entry.get("supersession_reason")
                    or claim["decision"].get("reason", "superseded by a registered claim"),
                    entry.get("supersession_state", "SUPERSEDED"),
                    retire_projection=conflict_mode)
                superseded.append(by_id[target])
            claims.append(claim)
            by_id[claim["claim_id"]] = claim
            registered.append(claim)

        quarantine = read_jsonl(QUARANTINE)
        existing_q = {q["quarantine_id"] for q in quarantine}
        new_q = []
        for entry in spec.get("quarantine", []):
            rec = build_registered_quarantine(entry, by_id)
            if rec["quarantine_id"] not in existing_q:
                quarantine.append(rec)
                new_q.append(rec)
    except ClaimSpecError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    claims = preserve_timestamps(claims, read_jsonl(CLAIMS), "claim_id", run_at)
    quarantine = preserve_timestamps(quarantine, read_jsonl(QUARANTINE),
                                     "quarantine_id", run_at)
    claims.sort(key=claim_sort_key)
    quarantine.sort(key=quarantine_sort_key)
    if not args.dry_run:
        write_jsonl(CLAIMS, claims)
        write_jsonl(QUARANTINE, quarantine)
    action = "would register" if args.dry_run else "registered"
    print(f"{action} {len(registered)} claims, superseded {len(superseded)}, "
          f"{len(unchanged)} already identical, {len(new_q)} quarantine pointers")
    for claim in registered:
        key = claim["claim_key"]
        print(f"  {claim['state']:11} {key['subject']:4} {key['predicate']:38} "
              f"as-of {key['as_of']}  {claim['authority_tier']}  "
              f"{(claim['value'] or {}).get('value')}")
    for old in superseded:
        print(f"  {old['state']:11} {old['claim_id'][:30]}… → "
              f"{old['superseded_by'][:30]}…")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Ingest: bytes → object → derivatives → document record
# ─────────────────────────────────────────────────────────────────────────────

DATE_PATTERNS = [
    "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%d/%m/%Y",
]


def date_variants(iso: str) -> list[str]:
    try:
        dt = datetime.strptime(iso[:10], "%Y-%m-%d")
    except Exception:
        return []
    out = []
    for fmt in DATE_PATTERNS:
        s = dt.strftime(fmt)
        out.append(s)
        out.append(s.lstrip("0").replace(" 0", " "))
    return sorted(set(out))


def extract_derivatives(digest: str, obj: Path, mime: str, force: bool = False) -> dict:
    """Reproducible transformations. They inherit the artifact's tier (§4.2)."""
    outdir = EXTRACTED / digest
    manifest = outdir / "extraction.json"
    if manifest.exists() and not force:
        return json.loads(manifest.read_text())
    outdir.mkdir(parents=True, exist_ok=True)
    rec = {"document_id": f"sha256:{digest}", "created": now(), "mime_type": mime,
           "authority": "inherits the artifact; a transformation never acquires its own tier",
           "derivatives": []}
    text_path = outdir / "text.txt"
    if mime == "application/pdf":
        subprocess.run(["pdftotext", "-layout", str(obj), str(text_path)],
                       capture_output=True, timeout=600)
        info = subprocess.run(["pdfinfo", str(obj)], capture_output=True, text=True,
                              timeout=120).stdout
        (outdir / "pdfinfo.txt").write_text(info)
        rec["derivatives"].append({"path": "pdfinfo.txt", "tool": "pdfinfo"})
        for line in info.splitlines():
            if line.startswith("Pages:"):
                rec["pages"] = int(line.split(":", 1)[1].strip() or 0)
            if line.startswith("Title:"):
                rec["pdf_title"] = line.split(":", 1)[1].strip()
            if line.startswith("CreationDate:"):
                rec["pdf_created"] = line.split(":", 1)[1].strip()
        if text_path.exists():
            rec["derivatives"].append({"path": "text.txt", "tool": "pdftotext -layout"})
            body = text_path.read_text(errors="ignore")
            rec["characters"] = len(body)
            # A born-scanned PDF extracts to almost nothing. Say so loudly rather
            # than letting a later reader treat empty text as an absent fact.
            if rec.get("pages") and len(body.strip()) < 200 * rec["pages"] / 10:
                rec["needs_visual_read"] = True
    elif mime == "text/html":
        raw = obj.read_bytes()
        text_path.write_text(strip_html(raw))
        rec["derivatives"].append({"path": "text.txt", "tool": "kb.strip_html"})
        rec["characters"] = len(text_path.read_text())
    elif mime == "application/json":
        raw = obj.read_text(errors="ignore")
        try:
            text_path.write_text(json.dumps(json.loads(raw), indent=1)[:4_000_000])
        except Exception:
            text_path.write_text(raw[:4_000_000])
        rec["derivatives"].append({"path": "text.txt", "tool": "json.dumps"})
        rec["characters"] = len(text_path.read_text())
    elif mime in ("text/csv", "text/plain"):
        text_path.write_text(obj.read_text(errors="ignore")[:4_000_000])
        rec["derivatives"].append({"path": "text.txt", "tool": "verbatim copy"})
        rec["characters"] = len(text_path.read_text())
    elif mime.startswith("image/"):
        rec["needs_visual_read"] = True
    for der in rec["derivatives"]:
        p = outdir / der["path"]
        if p.exists():
            der["sha256"] = sha256_file(p)
            der["bytes"] = p.stat().st_size
    manifest.write_text(json.dumps(rec, indent=1))
    return rec


def strip_html(raw: bytes) -> str:
    t = raw.decode("utf-8", errors="ignore")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def extracted_text(digest: str, limit: int | None = 400_000) -> str:
    """The text derivative, capped for scanning. `limit=None` for a comparison:
    two 217-page annual reports truncated at the same character count are cut in
    different places once a single word differs, and then differ everywhere
    after it — which reads as two different documents."""
    p = EXTRACTED / digest / "text.txt"
    if not p.exists():
        return ""
    body = p.read_text(errors="ignore")
    return body if limit is None else body[:limit]


ASX_KEY_RE = re.compile(r"\b(\d{4})-(\d{8})-(6A\d{7})\b")


def verify_document(doc: dict, text: str) -> dict:
    """Mechanical verification only. Anything a script cannot establish stays
    False and lands on the review list — the protocol wants a human read of the
    document, and a green flag we did not earn is worse than a red one."""
    v = {"bytes": True, "issuer": False, "title": False, "dates": False}
    # A market session is self-describing: the bundle records the provider, the
    # instruments, the clock and the engine commit that wrote it. Grepping it
    # for "ASX:NST" would only measure whether a JSON file happens to spell a
    # ticker the way an announcement does.
    session = doc.get("market_session") or {}
    if market_provider(doc):
        doc["verification_basis"] = session.get(
            "verification_basis", "self-describing market-session record")
        return {"bytes": True, "issuer": True, "title": True, "dates": True}
    # A document pulled off the exchange's own per-ticker index arrives with the
    # lodging entity, the headline and the lodgement date attested by the
    # exchange record itself. That is stronger evidence of those three than
    # grepping the document body, which is all the fallback below can do.
    if doc.get("lodgement", {}).get("index_document_id"):
        v.update(issuer=True, title=True, dates=True)
        doc["verification_basis"] = "ASX full-year announcement index (exchange record)"
        return v
    doc["verification_basis"] = "document text match"
    low = text.lower()
    subjects = doc.get("subjects") or []
    for ticker in subjects:
        if not ticker:
            continue
        if re.search(rf"asx\s*:?\s*{ticker.lower()}\b", low) or f"({ticker.lower()})" in low:
            v["issuer"] = True
            break
    title = (doc.get("title") or "")
    tokens = [w for w in re.findall(r"[A-Za-z]{4,}", title)][:12]
    if tokens:
        hits = sum(1 for w in tokens if w.lower() in low)
        v["title"] = hits >= max(2, int(0.6 * len(tokens)))
    for d in [doc.get("published_on")] + list(doc.get("reporting_dates") or []):
        if d and any(s.lower() in low for s in date_variants(d)):
            v["dates"] = True
            break
    return v


def ingest_bytes(raw: bytes, *, url: str | None, source_note: str,
                 legacy: dict | None = None, retrieved_at: str | None = None,
                 subjects: list[str] | None = None,
                 source_ids: list[dict] | None = None,
                 inferred: dict | None = None,
                 docs: dict[str, dict] | None = None,
                 mime_hint: str = "", name: str = "") -> dict:
    """Archive bytes, dedupe by hash, merge aliases, return the document record."""
    docs = load_documents() if docs is None else docs
    digest = sha256_bytes(raw)
    obj = object_path(digest)
    if not obj.exists():
        obj.parent.mkdir(parents=True, exist_ok=True)
        obj.write_bytes(raw)
    mime = sniff_mime(raw[:16], mime_hint, name)
    extract_derivatives(digest, obj, mime)

    doc = docs.get(digest)
    fresh = doc is None
    if fresh:
        doc = {
            "document_id": f"sha256:{digest}",
            "sha256": digest,
            "bytes": len(raw),
            "mime_type": mime,
            "title": None,
            "publisher": None,
            "published_on": None,
            "reporting_dates": [],
            "authority_tier": "T4",
            "authority_domains": ["unclassified"],
            "source_ids": [],
            "url_aliases": [],
            "object_locator": str(obj.relative_to(ROOT)),
            "storage_state": "local",
            "verified": {"issuer": False, "title": False, "dates": False, "bytes": True},
            "supersedes": [],
            "subjects": [],
            "acquisition": [],
            "review": [],
        }
        docs[digest] = doc
    elif doc.get("mime_type") != mime:
        # The same bytes, read better: a CSV that arrived without its name was
        # recorded as HTML, and its text derivative was produced by the HTML
        # stripper. Correct both rather than leaving the record describing the
        # artifact as something it is not.
        doc["mime_type"] = mime
        extract_derivatives(digest, obj, mime, force=True)

    stamp = retrieved_at or now()
    if url:
        alias = next((a for a in doc["url_aliases"] if a["url"] == url), None)
        if alias:
            alias["last_verified"] = stamp
        else:
            doc["url_aliases"].append({"url": url, "first_seen": stamp,
                                       "last_verified": stamp,
                                       "origin": classify(url)["tier_basis"]})
    for sid in source_ids or []:
        add_source_id(doc, sid)
    # An ASX documentKey in the URL the bytes were fetched from is a trusted
    # exchange identifier (§4.2) — it is what promotes a mirror copy to T1. The
    # same string read off a local filename is not: it says what we believe the
    # file to be, and belongs in `inferred_provenance` until something checks it.
    for sid in identifiers_in_url(url or "", "retrieval-url", True):
        add_source_id(doc, sid)
    note_inferred(doc, inferred)
    for s in subjects or []:
        if s and s not in doc["subjects"]:
            doc["subjects"].append(s)

    if legacy:
        title, analysis = publisher_title(legacy.get("title"))
        doc["title"] = doc["title"] or title
        if title and not doc.get("title_source"):
            doc["title_source"] = legacy.get("title_source") or "legacy title"
        if analysis:
            notes = doc.setdefault("legacy", {}).setdefault("notes", [])
            if not any(n.get("text") == analysis for n in notes):
                notes.append({"text": analysis, "where": legacy.get("where"),
                              "kind": "analytical note carried over from data/"})
        doc["published_on"] = doc["published_on"] or legacy.get("date")
        if legacy.get("legacy_type"):
            doc.setdefault("legacy", {})["type"] = legacy["legacy_type"]
        if legacy.get("citations"):
            doc.setdefault("legacy", {})["citations"] = legacy["citations"]

    # Tier: highest over all aliases, plus the exchange-identifier promotion.
    assign_tier(doc)

    note = {"at": stamp, "via": source_note}
    if url:
        note["url"] = url
    if note not in doc["acquisition"]:
        doc["acquisition"].append(note)

    doc["verified"] = verify_document(doc, extracted_text(digest))
    doc["review"] = review_flags(doc)
    return doc


def assign_tier(doc: dict) -> None:
    # An approved market-data provider is settled before anything derived from
    # aliases: an unrepeatable observation has none to read, and the tickers the
    # session quotes are its subject, not its origin (§4.1).
    provider = market_provider(doc)
    if provider:
        session = doc["market_session"]
        doc["authority_tier"] = provider["authority_tier"]
        doc["authority_domains"] = list(provider["authority_domains"])
        doc["publisher"] = provider["publisher"]
        doc["tier_kind"] = "market_session"
        doc["tier_note"] = (f"{provider['tier_note']} — {session.get('role', 'session')} "
                            f"of the session started {session.get('session_start', '?')}")
        doc["tier_basis"] = MARKET_PROVIDER_BASIS
        return
    best = None
    for alias in doc["url_aliases"]:
        cls = classify(alias["url"])
        if best is None or tier_rank(cls["authority_tier"]) < tier_rank(best["authority_tier"]):
            best = cls
    if best is None:
        # No alias: an artifact held locally whose retrieval route was never
        # recorded. A ticker read out of its text says what the document is
        # ABOUT; it says nothing about who served it, so it cannot buy the
        # issuer's tier. Until a route is established — `route-local` against
        # the exchange index, or `verify-inferred` against an implied address —
        # the record stays unclassified and says why (§4.2).
        best = {"authority_tier": "T4", "authority_domains": ["unclassified"],
                "publisher": None, "tier_kind": "local-artifact",
                "tier_note": "held locally with no recorded retrieval route; the subject "
                             "was inferred from the text and is not provenance",
                "tier_basis": "local-artifact-no-route"}
    sid = verified_exchange_id(doc)
    if sid and tier_rank(best["authority_tier"]) > tier_rank("T1"):
        best = {"authority_tier": "T1", "authority_domains": ["exchange.lodgement"],
                "publisher": "ASX Limited", "tier_kind": "lodged",
                "tier_note": f"carries a trusted ASX {sid['scheme']} obtained from "
                             f"{sid['basis']} (§4.2 equivalence)",
                "tier_basis": f"{sid['scheme']}:{sid['basis']}"}
    # Equivalence with a verified artifact is the other route to the origin's
    # tier: the CDN regenerates a lodged PDF per request, so two downloads of
    # one announcement differ in bytes while extracting to identical text.
    eq = doc.get("equivalence") or {}
    if eq.get("inherits_tier") and tier_rank(eq["inherits_tier"]) < tier_rank(best["authority_tier"]):
        best = {"authority_tier": eq["inherits_tier"],
                "authority_domains": eq.get("authority_domains") or ["exchange.lodgement"],
                "publisher": eq.get("publisher") or "ASX Limited", "tier_kind": "lodged",
                "tier_note": f"equivalent to {eq['verified_member']}: {eq['basis']}",
                "tier_basis": "equivalence-with-verified-artifact"}
    doc["authority_tier"] = best["authority_tier"]
    doc["authority_domains"] = best["authority_domains"]
    # The exchange's per-issuer index is a record of WHAT WAS LODGED AND WHEN,
    # not a lodged document (§4.1). Its host rule cannot see the difference, so
    # the domain is set from the URL and survives every reassignment.
    if any(INDEX_URL_RE.search(a["url"]) for a in doc.get("url_aliases", [])):
        doc["authority_domains"] = ["exchange.index"]
    doc["publisher"] = doc.get("publisher") or best.get("publisher")
    if best["tier_basis"] == "local-artifact-no-route":
        # A publisher inferred from the text is the same unsupported claim as an
        # inferred tier. A record with no route names no publisher, including
        # one the discarded rule had already written.
        doc["publisher"] = None
    doc["tier_kind"] = best["tier_kind"]
    doc["tier_note"] = best["tier_note"]
    doc["tier_basis"] = best["tier_basis"]


# ─────────────────────────────────────────────────────────────────────────────
# Versions and equivalence (§4.2, §6.1)
#
# One publication can hold several artifacts. The ASX CDN regenerates a lodged
# PDF on each request, so two downloads of one announcement differ by a few
# bytes and hash differently; an exchange index page carries a cache-buster.
# Both are genuine artifact versions and both are kept. What the store must not
# do is pick one silently — so a group is ordered by retrieval, and equivalence
# is recorded as a finding with its basis, not assumed from the shared key.
# ─────────────────────────────────────────────────────────────────────────────

MIN_TEXT_FOR_EQUIVALENCE = 200

# Two distributors of one lodged PDF do not produce one extraction. The ASX
# research CDN re-stamps the file through Markit; the announcements host serves
# it through OpenPDF; `pdftotext -layout` then reads the two layouts in
# different orders, so a paragraph and the sideways "For personal use only"
# stamp swap places and a character-by-character comparison fails on documents
# that are word for word the same. (Both copies carry the issuer's own
# CreationDate, which is the giveaway.)
#
# So the comparison is made where the difference is not: page for page, the
# same words in the same numbers. Reading order can differ — it is a property
# of the renderer, not of the document. What may not differ is the content of
# any page, the number of pages, or anything beyond fragments of the stamp
# itself, which one distributor draws as text and the other does not.
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
STAMP_PHRASE = "forpersonaluseonly"
STAMP_PER_PAGE = 4          # "For personal use only" — one stamp per page, at most


def page_tokens(text: str) -> list:
    pages = text.split("\f")
    while len(pages) > 1 and not pages[-1].strip():
        pages.pop()      # pdftotext ends the last page with a form feed
    return [Counter(w.lower() for w in TOKEN_RE.findall(page)) for page in pages]


def stamp_tokens(counter) -> int:
    """Tokens that can only be pieces of the exchange's stamp. `pdftotext`
    breaks the rotated phrase wherever the glyphs land, so "rsonal" and "al"
    turn up as often as the whole words."""
    return sum(n for t, n in counter.items() if len(t) >= 2 and t in STAMP_PHRASE)


def strip_stamp(counter):
    return Counter({t: n for t, n in counter.items()
                    if not (len(t) >= 2 and t in STAMP_PHRASE)})


def same_publication(a: str, b: str) -> tuple[bool | None, str]:
    """Are these two extractions the same document? (verdict, basis).

    True with the basis naming what was compared, False with the size of the
    disagreement, or None where there is too little text to say — two
    born-scanned PDFs both extract to nothing, which is not evidence either
    way."""
    if min(len(a.strip()), len(b.strip())) < MIN_TEXT_FOR_EQUIVALENCE:
        return None, (f"too little extracted text to compare ({len(a.strip())} and "
                      f"{len(b.strip())} characters) — equivalence needs a visual read")
    if a == b:
        return True, ("identical extracted text; the artifacts differ only in bytes the "
                      "publisher regenerates per request")
    pa, pb = page_tokens(a), page_tokens(b)
    if len(pa) != len(pb):
        return False, (f"{len(pa)} pages against {len(pb)} — a different document, not a "
                       f"re-rendering of the same one")
    if all(x == y for x, y in zip(pa, pb)):
        return True, (f"identical text page for page over {len(pa)} pages; only the order "
                      f"`pdftotext` read the layout in differs")
    stamps = sum(stamp_tokens((x - y) + (y - x)) for x, y in zip(pa, pb))
    stripped = [(strip_stamp(x), strip_stamp(y)) for x, y in zip(pa, pb)]
    residue = sum(sum(((x - y) + (y - x)).values()) for x, y in stripped)
    if residue == 0 and stamps <= STAMP_PER_PAGE * len(pa):
        return True, (f"identical text page for page over {len(pa)} pages once the "
                      f"exchange's 'For personal use only' stamp is set aside "
                      f"({stamps} fragments, at most {STAMP_PER_PAGE} a page); one "
                      f"distributor renders it as text and the other does not")
    return False, (f"text differs on {sum(1 for x, y in stripped if x != y)} of {len(pa)} "
                   f"pages ({residue} words) — a distinct version, not a re-rendering")


def first_retrieved(doc: dict) -> str:
    stamps = [a.get("first_seen") for a in doc.get("url_aliases", [])]
    stamps += [a.get("at") for a in doc.get("acquisition", [])]
    return min([s for s in stamps if s], default="")


def publication_groups(docs: dict[str, dict]) -> dict[str, list[dict]]:
    """Artifacts that claim to be the same publication: one exchange identifier,
    or one URL that served bytes more than once."""
    groups: dict[str, dict[str, dict]] = {}
    for doc in docs.values():
        keys = [f"{s['scheme']}:{s['value']}" for s in doc.get("source_ids", [])
                if s.get("scheme") in EXCHANGE_ID_SCHEMES]
        keys += [f"url:{a['url']}" for a in doc.get("url_aliases", [])]
        for key in keys:
            groups.setdefault(key, {})[doc["sha256"]] = doc
    return {k: sorted(v.values(), key=first_retrieved)
            for k, v in groups.items() if len(v) > 1}


def publication_clusters(docs: dict[str, dict]) -> list[dict]:
    """The same, merged where groups overlap.

    One announcement can be grouped twice over: by its documentKey, and by the
    CDN URL that key resolves to. The groups are not the same set — a copy saved
    from a token-bearing URL shares the key but not the URL — and treating them
    separately would give one artifact two different answers about what it is a
    version of. Overlapping groups are therefore one publication."""
    groups = publication_groups(docs)
    parent: dict[str, str] = {}

    def find(sha: str) -> str:
        while parent.setdefault(sha, sha) != sha:
            parent[sha] = parent[parent[sha]]
            sha = parent[sha]
        return sha

    for members in groups.values():
        for member in members[1:]:
            root_a, root_b = find(members[0]["sha256"]), find(member["sha256"])
            if root_a != root_b:
                parent[root_a] = root_b
    merged: dict[str, dict] = {}
    for key, members in groups.items():
        cluster = merged.setdefault(find(members[0]["sha256"]),
                                    {"keys": [], "members": {}})
        cluster["keys"].append(key)
        for member in members:
            cluster["members"][member["sha256"]] = member
    out = []
    for cluster in merged.values():
        # An exchange identifier names the publication; a URL only reaches it.
        keys = sorted(cluster["keys"], key=lambda k: (k.startswith("url:"), k))
        out.append({"keys": keys, "primary": keys[0],
                    "members": sorted(cluster["members"].values(), key=first_retrieved)})
    return sorted(out, key=lambda c: c["primary"])


def own_tier(doc: dict) -> str:
    """The tier this record earns from its own aliases and verified identifiers,
    ignoring anything inherited by equivalence — otherwise two unverified copies
    of one document could inherit T1 from each other."""
    ranks = [classify(a["url"])["authority_tier"] for a in doc.get("url_aliases", [])]
    if verified_exchange_id(doc):
        ranks.append("T1")
    return min(ranks, key=tier_rank) if ranks else "T4"


def link_equivalents(docs: dict[str, dict]) -> dict[str, int]:
    """Record, for every multi-artifact publication, whether the members are the
    same document. Identical extracted text is the documented verification §4.2
    allows; anything else stays an open question rather than a quiet merge."""
    stats = {"groups": 0, "equivalent": 0, "unproven": 0, "differing": 0}
    # An unchanged finding keeps the date it was first established. Re-stamping
    # it every run would churn a committed registry and, worse, make an old
    # check look like a fresh one.
    prior = {sha: doc.pop("equivalence", None) for sha, doc in docs.items()}

    def stamp(rec: dict, sha: str) -> dict:
        was = prior.get(sha) or {}
        unchanged = all(was.get(k) == rec.get(k) for k in
                        ("group", "keys", "members", "verified_member", "equivalent",
                         "basis"))
        rec["established_at"] = was["established_at"] if unchanged and was.get(
            "established_at") else now()
        return rec
    for cluster in publication_clusters(docs):
        stats["groups"] += 1
        key, keys, members = cluster["primary"], cluster["keys"], cluster["members"]
        anchor = min(members, key=lambda d: (tier_rank(own_tier(d)), first_retrieved(d)))
        anchor_text = extracted_text(anchor["sha256"], None)
        for doc in members:
            if doc["sha256"] == anchor["sha256"]:
                continue
            text = extracted_text(doc["sha256"], None)
            # Two born-scanned PDFs both extract to nothing. That is not evidence
            # that they are the same document, and it is not evidence that they
            # differ either — it is a document that has to be read by eye.
            same, why = same_publication(anchor_text, text)
            rec = {
                "group": key,
                "keys": keys,
                "members": [f"sha256:{m['sha256']}" for m in members],
                "verified_member": anchor["document_id"],
            }
            if same:
                stats["equivalent"] += 1
                rec.update(
                    equivalent=True, basis=why,
                    inherits_tier=own_tier(anchor),
                    authority_domains=anchor.get("authority_domains"),
                    publisher=anchor.get("publisher"))
            elif same is None:
                stats["unproven"] += 1
                rec.update(equivalent=None, basis=why)
            else:
                stats["differing"] += 1
                rec.update(equivalent=False,
                           basis=f"compared with the earliest verified artifact under this "
                                 f"key: {why}")
            doc["equivalence"] = stamp(rec, doc["sha256"])
        # The anchor records the group too, so a reader arriving at either
        # artifact sees the other versions rather than only the one they opened.
        if len(members) > 1:
            anchor["equivalence"] = stamp({
                "group": key,
                "keys": keys,
                "members": [f"sha256:{m['sha256']}" for m in members],
                "verified_member": anchor["document_id"],
                "equivalent": True,
                "basis": "earliest artifact of this publication held under its own "
                         "provenance; the other members are compared against it",
            }, anchor["sha256"])
    return stats


def review_flags(doc: dict) -> list[str]:
    flags = []
    v = doc.get("verified", {})
    if not v.get("issuer"):
        flags.append("issuer-unverified")
    if not v.get("dates"):
        flags.append("dates-unverified")
    if not doc.get("title"):
        flags.append("title-missing")
    if doc.get("storage_state") != "durable":
        flags.append("object-not-durable")
    if doc.get("tier_kind") == "mirror":
        flags.append("mirror-equivalence-unverified")
    if doc.get("tier_kind") == "volatile":
        flags.append("volatile-endpoint-observation")
    if any(i.get("state") == "unverified" for i in doc.get("inferred_provenance", [])):
        flags.append("inferred-provenance-unresolved")
    elif any(not (s.get("verified") or s.get("resolved_by"))
             for s in doc.get("source_ids", [])):
        flags.append("inferred-identifier-unverified")
    # What a reader needs from this flag is whether the route was TESTED, not
    # whether it began as an inference. An inference that was fetched and found
    # to serve an equivalent artifact is settled evidence, and labelling it
    # "not recorded" reads as an open hole in the store.
    route = doc.get("retrieval_route") or {}
    if not has_route(doc):
        # Nothing on the record says how these bytes could be obtained again.
        flags.append("retrieval-route-unresolved" if route.get("state") == "unresolved"
                     else "retrieval-route-untested")
    elif not doc.get("url_aliases") and (route.get("state") == "equivalent-regeneration"
                                         or routed_by_inference(doc)):
        flags.append("route-by-equivalence-not-these-bytes")
    eq = doc.get("equivalence") or {}
    if eq.get("equivalent") is None and "equivalence" in doc:
        flags.append("version-equivalence-unproven")
    elif eq.get("equivalent") is False:
        flags.append("distinct-version-under-one-key")
    man = EXTRACTED / doc["sha256"] / "extraction.json"
    if man.exists() and json.loads(man.read_text()).get("needs_visual_read"):
        flags.append("needs-visual-read")
    return flags


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(args) -> int:
    for d in (KB, OBJECTS, EXTRACTED, VIEWS):
        d.mkdir(parents=True, exist_ok=True)
    for f in (DOCUMENTS, CLAIMS, QUARANTINE, AVAILABILITY):
        f.touch()
    readme = KB / "README.md"
    if not readme.exists():
        readme.write_text(KB_README)
    print(f"knowledge store initialised at {KB.relative_to(ROOT)}")
    return 0


TMP_TICKER_RE = re.compile(r"^(bc8|bgl|cmm|cyl|evn|ggp|gmd|nst|obm|pnr|rms|rrl|vau|wgx|rxl|auc|aar)[-_.]",
                           re.I)
WEBLINK_RE = re.compile(r"^obm[-_](\d{8})", re.I)
PROBE_RE = re.compile(r"^probe-(\d{8})-(6A\d{7})")


def tmp_provenance(path: Path) -> tuple[list[str], str, dict | None]:
    """Read what a /tmp filename suggests about a download, as a lead.

    Whoever saved the file chose the name; the publisher did not. A documentKey
    in it says which announcement the downloader BELIEVED they were saving,
    which is not evidence that these bytes are that announcement — a
    re-download, an edit, a truncated transfer or a mis-named file all produce
    the same filename. So nothing here becomes a URL alias or a verified
    identifier: it is returned as an inferred record with the address it would
    resolve to, and `reverify`/`verify-inferred` are what can promote it."""
    name = path.name
    subjects: list[str] = []
    note = "local /tmp artifact from the 21-22 Aug 2026 sourcing pass"
    inferred: dict | None = None
    key = origin = None
    m = ASX_KEY_RE.search(name)
    if m:
        key, origin = "-".join(m.groups()), "documentKey read from the filename"
    else:
        m = PROBE_RE.match(name)
        if m:
            key = f"2924-{m.group(1)}-{m.group(2)}"
            origin = ("documentKey reconstructed from a probe filename, including a "
                      "guessed 2924 prefix")
    if key:
        inferred = {
            "basis": "local-filename", "state": "unverified", "detail": origin,
            "source_ids": [source_id("asx_document_key", key, "local-filename", False)],
            "candidate_urls": [{"url": ASX_CDN + key,
                                "why": "the ASX research CDN address this documentKey "
                                       "would resolve to, if the filename is right"}],
            "resolves_by": "fetching the candidate URL, or matching an exchange index "
                           "row, and comparing the artifact",
        }
        note += f"; {origin} — inferred, not verified"
    else:
        m = WEBLINK_RE.match(name)
        if m:
            inferred = {
                "basis": "local-filename", "state": "unverified",
                "detail": "WebLink headlineid read from the filename",
                "source_ids": [source_id("weblink_headline_id", m.group(1),
                                         "local-filename", False)],
                "candidate_urls": [{
                    "url": "https://wcsecure.weblink.com.au/clients/orabandamining/"
                           f"headline.aspx?headlineid={m.group(1)}",
                    "why": "the WebLink headline page this id would resolve to"}],
                "resolves_by": "fetching the candidate URL and comparing the artifact",
            }
            note += "; WebLink headlineid read from the filename — inferred, not verified"
    m = TMP_TICKER_RE.match(name)
    if m:
        subjects.append(m.group(1).upper())
    if name.startswith("nst-"):
        subjects.append("NST")
    if inferred:
        inferred["filename"] = name
    return sorted(set(subjects)), note, inferred


def cmd_ingest_local(args) -> int:
    """Consume everything already held on disk before any network access (§6)."""
    cmd_init(args)
    docs = load_documents()
    legacy = legacy_index()
    seen_before = set(docs)
    counts = {"cache": 0, "tmp": 0, "merged": 0, "skipped": 0}

    if args.source in ("cache", "all"):
        for meta_path in sorted(CACHE.glob("*.json")):
            try:
                meta = json.loads(meta_path.read_text())
            except Exception:
                continue
            blob = meta.get("blob")
            url = meta.get("url")
            if not blob or not url:
                if url and meta.get("error"):
                    availability(url, "LINK_DEAD" if meta.get("status") in (404, 410)
                                 else "BLOCKED" if meta.get("status") == 403 else "MISSING_OBJECT",
                                 channel="legacy .cache record", http_status=meta.get("status"),
                                 diagnosis=meta.get("error"), source="cache-migration")
                    counts["skipped"] += 1
                continue
            p = ROOT / blob
            if not p.exists():
                availability(url, "MISSING_OBJECT", channel="legacy .cache record",
                             diagnosis="cache metadata references a missing blob")
                counts["skipped"] += 1
                continue
            raw = p.read_bytes()
            leg = legacy.get(url) or legacy.get(meta.get("final_url", ""), {})
            doc = ingest_bytes(raw, url=url, source_note="migrated from .cache",
                               legacy=leg or None,
                               subjects=(leg or {}).get("subjects"),
                               docs=docs, mime_hint="", name=p.name)
            availability(doc["document_id"], "AVAILABLE_LOCAL", url=url,
                         channel="cache-migration", object=doc["object_locator"])
            counts["cache"] += 1

    if args.source in ("tmp", "all"):
        for p in sorted(TMP.glob("*.pdf")):
            subjects, note, inferred = tmp_provenance(p)
            raw = p.read_bytes()
            before = sha256_bytes(raw) in docs
            doc = ingest_bytes(raw, url=None, source_note=note, legacy=None,
                               subjects=subjects, inferred=inferred, docs=docs,
                               name=p.name)
            doc.setdefault("local_paths", [])
            if str(p) not in doc["local_paths"]:
                doc["local_paths"].append(str(p))
            availability(doc["document_id"], "AVAILABLE_LOCAL",
                         channel="tmp-migration", object=doc["object_locator"],
                         inferred=(inferred or {}).get("detail"))
            counts["merged" if before else "tmp"] += 1

    refresh_derived(docs)
    save_documents(docs)
    added = len(docs) - len(seen_before)
    print(f"ingested: {counts['cache']} from .cache, {counts['tmp']} from /tmp, "
          f"{counts['merged']} merged into an artifact already held, "
          f"{counts['skipped']} unusable cache records")
    print(f"documents: {len(docs)} ({added} new this run)")
    return 0


def cmd_ingest_file(args) -> int:
    """Archive a file obtained outside the tool — the sandbox-friendly path in
    AGENTS.md — with its retrieval URL recorded rather than lost."""
    path = Path(args.path).expanduser()
    raw = path.read_bytes()
    docs = load_documents()
    legacy = legacy_index().get(args.url or "", {}) if args.url else {}
    doc = ingest_bytes(raw, url=args.url, source_note=args.note or f"ingest-file {path.name}",
                       legacy={"title": args.title or legacy.get("title"),
                               "title_source": "operator-supplied" if args.title else None,
                               "date": args.date or legacy.get("date"),
                               "citations": legacy.get("citations")},
                       subjects=args.subject or legacy.get("subjects"),
                       docs=docs, name=path.name)
    doc.setdefault("local_paths", [])
    if str(path) not in doc["local_paths"]:
        doc["local_paths"].append(str(path))
    refresh_derived(docs)
    save_documents(docs)
    availability(doc["document_id"], "AVAILABLE_LOCAL", url=args.url,
                 channel="ingest-file", object=doc["object_locator"])
    print(f"[{doc['authority_tier']}] {doc['document_id']}  {doc['bytes']/1000:.0f} kB  "
          f"{doc.get('title') or path.name}")
    return 0


# A title is what the publisher called the document. Two sentences, or a
# shouted finding, is somebody's reading of it: analysis, and it belongs in
# `legacy.notes` where a reader can see whose reading it is.
TITLE_MAX = 200
SENTENCE_RE = re.compile(r"[.!?]\s+[A-Z(\[0-9]")
DASH_SPLIT_RE = re.compile(r"\s+[—–-]\s+")
# Titles the tool must not overwrite: nobody else can reconstruct them.
PINNED_TITLE_SOURCES = ("operator-supplied", "market session record")
# Titles the publisher wrote. Whatever punctuation they contain is theirs.
PUBLISHER_TITLE_SOURCES = ("exchange index headline", "exchange index row", "pdf metadata",
                           "html <title>", "publisher URL filename")
JUNK_PDF_TITLES = ("untitled", "microsoft word", "document", "print", "layout 1")


# A tail that quotes figures, stacks clauses, or runs long is a reading of the
# document rather than part of its name. Publisher titles do use dashes, so the
# test is what the tail SAYS, not that a dash is present.
GLOSS_RE = re.compile(r"(?:A?U?\$|\b\d[\d,.]*\s*(?:koz|oz|Moz|Mt|kt|g/t|%|bn|m\b))|;")
GLOSS_MAX_TAIL = 80

# Short tails give the length test nothing to work with, so they are read
# instead. Three things mark a tail as somebody's reading of the document:
#
#   * it points INTO the document — a note number, a table, a slide. A title
#     names the whole thing; only an analysis cites a part of it.
#   * it is a sentence fragment about the document rather than a name. A
#     publisher's continuation is a noun phrase ("Correction", "December 2025",
#     "Maiden Ore Reserve"); a gloss starts mid-thought ("the exchange's own
#     figure") or hinges on a subordinating word ("following...", "replacing...").
#   * it stacks findings, which shows up as a list of clauses.
#
# The first word's case is load-bearing: "revised" is one lower-case word and a
# real ASX headline suffix, while "the exchange's own figure" is four. Deciding
# on length alone would have to reject one to catch the other.
GLOSS_POINTER_RE = re.compile(
    r"\bnotes?\s+\d+"                                   # Note 17, notes 13
    r"|\b(?:table|slide|tables|slides|figure|appendix\s+page|section|page\s+\d+)\b"
    r"|\b(?:actuals?|balance\s+sheet|guidance\s+table|line\s+item)\b"
    r"|\b\d{1,3}\s*(?:pp|pages)\b", re.I)
GLOSS_CONNECTIVE_RE = re.compile(
    r"\b(?:which|including|showing|confirming|replacing|superseding|following"
    r"|as\s+observed|as\s+reported|noting|because|whereas|so\s+that|used\s+for"
    r"|read\s+with|per\s+the|but\s+not)\b", re.I)
GLOSS_LEAD_RE = re.compile(r"^[a-z]")


def is_narrative(s: str) -> bool:
    return len(s) > TITLE_MAX or bool(SENTENCE_RE.search(s))


def is_gloss(tail: str) -> bool:
    if len(tail) > GLOSS_MAX_TAIL or GLOSS_RE.search(tail):
        return True
    if GLOSS_POINTER_RE.search(tail) or GLOSS_CONNECTIVE_RE.search(tail):
        return True
    words = tail.split()
    if len(words) >= 3 and GLOSS_LEAD_RE.match(tail):
        return True                     # a phrase, not a name: "the only asset CMM held"
    return tail.count(",") >= 2         # stacked findings


def publisher_title(raw: str | None, from_publisher: bool = False
                    ) -> tuple[str | None, str | None]:
    """Split a title string into (publisher title, analysis).

    `data/` records many documents as "Publisher headline (date) — what we
    concluded from reading it". The headline is metadata about the artifact and
    belongs in `title`; everything after the dash is a claim about its contents
    and does not. Where no headline can be separated cleanly, this returns no
    title rather than a truncated one — the artifact's own metadata is a better
    source than a guess at where the prose stops.

    `from_publisher` marks a string the publisher itself wrote — an exchange
    headline, a PDF title, an HTML `<title>`. Those are titles by definition,
    dashes and all, and are only rejected if they run to narrative. Splitting
    them would invent an analytical note nobody wrote and truncate real
    headlines that happen to contain a dash."""
    s = re.sub(r"\s+", " ", (raw or "").strip())
    if not s:
        return None, None
    if from_publisher:
        return (None, s) if is_narrative(s) else (s, None)
    parts = DASH_SPLIT_RE.split(s, 1)
    head = parts[0].strip()
    tail = parts[1].strip() if len(parts) > 1 else ""
    if not is_narrative(s) and not (tail and is_gloss(tail)):
        return s, None
    if head and head != s and not is_narrative(head):
        return head, s
    return None, s


def artifact_title(doc: dict) -> tuple[str | None, str | None]:
    """The publisher's own title, taken from the artifact or the exchange record."""
    lodge = doc.get("lodgement") or {}
    if lodge.get("headline"):
        title, _ = publisher_title(lodge["headline"], from_publisher=True)
        if title:
            return title, "exchange index headline"
    man = EXTRACTED / doc["sha256"] / "extraction.json"
    if man.exists():
        t = re.sub(r"\s+", " ", (json.loads(man.read_text()).get("pdf_title") or "")).strip()
        if t and t.lower() not in JUNK_PDF_TITLES and not is_narrative(t):
            return t, "pdf metadata"
    if doc.get("mime_type") == "text/html":
        obj = ROOT / doc["object_locator"]
        if obj.exists():
            m = re.search(rb"<title[^>]*>(.{0,300}?)</title>", obj.read_bytes()[:200_000],
                          re.S | re.I)
            if m:
                t = re.sub(r"\s+", " ", strip_html(m.group(1))).strip()[:TITLE_MAX]
                if t:
                    return t, "html <title>"
    if lodge.get("ticker"):
        return f"{lodge['ticker']} lodgement {lodge.get('lodged_on', '')}".strip(), \
               "exchange index row"
    for alias in doc.get("url_aliases", []):
        name = url_filename_title(alias["url"])
        if name:
            return name, "publisher URL filename"
    return None, None


def url_filename_title(url: str) -> str | None:
    """The name the publisher gave the file on its own server. Weak, but it is
    the publisher's, which a description written here would not be. Rejected
    where the segment is an opaque identifier rather than a name."""
    segment = urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
    base = re.sub(r"\.(pdf|html?|json|txt)$", "", segment, flags=re.I).strip()
    tokens = [t for t in re.split(r"[-_+ ]+", base) if t]
    words = [t for t in tokens if re.fullmatch(r"[A-Za-z]{2,}", t)]
    if len(words) >= 2 and len(base) <= TITLE_MAX:
        return base
    return None


def resolve_title(doc: dict, legacy: dict[str, dict]) -> None:
    """Recompute `title` from publisher metadata, moving analysis to `legacy.notes`.

    Recomputed rather than filled-if-empty: the store already holds titles that
    were legacy analytical notes, and a fill-if-empty rule leaves them exactly
    where they are."""
    # A session bundle has no publisher metadata to read and no legacy title
    # worth trusting over the session record itself, which names the provider,
    # the instant and the role. It is restored rather than merely left alone, so
    # that a record already carrying a drifted title is corrected.
    session = doc.get("market_session") or {}
    if market_provider(doc) and session.get("title"):
        doc["title"] = session["title"]
        doc["title_source"] = "market session record"
        return
    cover = doc.get("coverage") or {}
    if cover.get("channel") == "asx_announcement_index" and cover.get("subject"):
        # An index sweep has no publisher title to take: the exchange serves
        # every ticker-year under the same page heading. What identifies this
        # artifact is what it covers, and the source says plainly that the name
        # is ours rather than passing it off as the publisher's.
        doc["title"] = (f"ASX announcement index — {cover['subject']} "
                        f"{cover.get('covered_from', '')[:4]}").strip()
        doc["title_source"] = "index sweep record"
        return
    if doc.get("title_source") in PINNED_TITLE_SOURCES:
        return
    notes = doc.setdefault("legacy", {}).setdefault("notes", [])

    def keep_note(text: str | None, where: str | None) -> None:
        if text and not any(n.get("text") == text for n in notes):
            notes.append({"text": text, "where": where,
                          "kind": "analytical note carried over from data/"})

    legacy_title, legacy_where = None, None
    for alias in doc.get("url_aliases", []):
        entry = legacy.get(alias["url"])
        if not entry:
            continue
        for note in entry.get("notes", []):
            keep_note(note.get("text"), note.get("where"))
        if entry.get("title") and not legacy_title:
            legacy_title = entry["title"]
            cite = (entry.get("citations") or [{}])[0]
            legacy_where = (f"{cite.get('file', 'data/')} "
                            f"{cite.get('doc_key') or cite.get('json_path') or ''}").strip()

    title, source = artifact_title(doc)
    clean, analysis = publisher_title(legacy_title)
    if analysis:
        keep_note(analysis, legacy_where)
    # The exchange's headline outranks a legacy title; a legacy title outranks
    # PDF metadata, which is frequently the authoring tool's default.
    if source != "exchange index headline" and clean:
        title, source = clean, f"legacy title ({legacy_where})" if legacy_where else "legacy title"
    if not title and doc.get("title"):
        # A title already on the record and reproducible from nothing else still
        # goes through the same split: the initial load wrote glosses here too.
        carried, gloss = publisher_title(doc["title"])
        if gloss:
            keep_note(gloss, "documents.jsonl title, before this correction")
        if carried:
            title, source = carried, doc.get("title_source") or "carried from ingest"
    doc["title"] = title
    doc["title_source"] = source if title else None
    if not notes:
        doc["legacy"].pop("notes", None)
    if not doc["legacy"]:
        doc.pop("legacy", None)


def valid_subject(s: str) -> bool:
    return bool(s) and (s in TICKERS or re.fullmatch(r"[A-Z]{2}(-[A-Z]{2,4})?", s) is not None
                        or re.fullmatch(r"[A-Z][a-z]+(?: [A-Z][a-z]+)*", s) is not None)


def infer_subject(text: str) -> list[str]:
    """Ticker inference for artifacts that arrived without provenance. Requires
    the exchange-code form, not a bare three-letter string, or every mention of
    'CYL' inside a word would become a subject."""
    head = text[:4000]
    hits = []
    for t in TICKERS:
        pat = rf"\bASX\s*:?\s*{t}\b|\({t}\)|\bASX\s*code\s*:?\s*{t}\b"
        if re.search(pat, head, re.I) or len(re.findall(pat, text[:200_000], re.I)) >= 3:
            hits.append(t)
    return hits


TMP_VIA = "local /tmp artifact"


def demote_inferred_aliases(doc: dict) -> list[str]:
    """Withdraw URL aliases that were constructed from a local filename.

    An alias asserts that these bytes were served at that address. Where the
    only acquisition event behind an alias is the local /tmp pass, no request
    was ever made to it: the URL was assembled from the filename. It moves to
    `inferred_provenance` as a candidate address, and the acquisition entry
    stops claiming a retrieval that did not happen."""
    withdrawn = []
    for alias in list(doc.get("url_aliases", [])):
        events = [a for a in doc.get("acquisition", []) if a.get("url") == alias["url"]]
        if not events or not all(a.get("via", "").startswith(TMP_VIA) for a in events):
            continue
        doc["url_aliases"].remove(alias)
        withdrawn.append(alias["url"])
        ids = identifiers_in_url(alias["url"], "local-filename", False)
        note_inferred(doc, {
            "basis": "local-filename", "state": "unverified",
            "detail": "URL assembled from the filename of a local /tmp artifact during "
                      "the 23 Aug 2026 load; withdrawn as an alias on review",
            "source_ids": ids,
            "candidate_urls": [{"url": alias["url"],
                                "why": "the address the filename implies; never requested"}],
            "resolves_by": "fetching the candidate URL, or matching an exchange index "
                           "row, and comparing the artifact",
            "first_recorded": alias.get("first_seen"),
        })
        for event in events:
            event["inferred_url"] = event.pop("url")
            event["correction"] = ("recorded as a retrieval URL by the initial load; it "
                                   "was derived from the filename, not requested")
    return withdrawn


def normalize_source_ids(doc: dict) -> None:
    """Give every identifier the basis it was actually obtained on. Records
    written before identifiers carried a basis are re-derived from the evidence
    still on the record: a URL that contains the identifier, or an exchange
    index row that supplied it."""
    aliases = " ".join(a["url"] for a in doc.get("url_aliases", []))
    inferred_values = {s["value"] for i in doc.get("inferred_provenance", [])
                       for s in i.get("source_ids", [])}
    # An inference the publisher settled leaves the identifier unverified for
    # these bytes but no longer open: the resolution is recorded against it so
    # the review queue stops listing finished work.
    settled = {s["value"]: i for i in doc.get("inferred_provenance", [])
               if i.get("state") == "equivalent" and i.get("fetched_artifact")
               for s in i.get("source_ids", [])}
    # A route resolved against the exchange index settles the identifier the
    # same way, and says so in the same field.
    route = doc.get("retrieval_route") or {}
    if route.get("equivalent_artifact") and route.get("ids_id"):
        settled.setdefault(route["ids_id"], {"fetched_artifact": route["equivalent_artifact"]})
    for sid in doc.get("source_ids", []):
        found = settled.get(sid.get("value"))
        if found and not sid.get("verified") and not sid.get("resolved_by"):
            sid["resolved_by"] = (f"equivalence with {found['fetched_artifact']}, fetched "
                                  f"from the address this identifier implies")
    for sid in doc.get("source_ids", []):
        # An identifier that already rests on evidence is settled. One that does
        # not is re-derived every run, so that an alias confirmed later upgrades
        # it instead of leaving it stamped with the weakest basis it ever had.
        if sid.get("verified") and sid.get("basis") in VERIFIED_BASES:
            continue
        # An identifier taken off an index row that names the publication these
        # bytes are a copy of is not a guess to be re-derived — but it is not
        # evidence about THESE bytes either, so it keeps its own basis.
        if sid.get("basis") == INDEX_ROUTE_BASIS:
            continue
        value, scheme = sid.get("value") or "", sid.get("scheme")
        if value and value in aliases:
            # The identifier is inside an address these bytes came back from.
            sid.update(basis="retrieval-url", verified=True)
        elif scheme == "asx_ids_id" and doc.get("lodgement", {}).get("index_document_id"):
            sid.update(basis="exchange-index-row", verified=True)
        elif scheme in ("tws_session_start", "engine_commit"):
            sid.update(basis="session-record", verified=True)
        elif value in inferred_values:
            sid.update(basis="local-filename", verified=False)
        else:
            sid.update(basis="legacy-record", verified=False)


def repair_index_coverage(docs: dict[str, dict]) -> int:
    """Restate what each archived exchange index actually covers.

    A sweep of the current year is an index of the year TO DATE. Recording it as
    1 Jan–31 Dec would make it evidence that nothing will be lodged in the rest
    of the year, which is the one thing an index cannot show. It also backfills
    the exchange's headline onto each lodgement, so the publisher's own title is
    available without going through `data/`."""
    store_path = VIEWS / "asx_lodgements.json"
    if not store_path.exists():
        return 0
    store = json.loads(store_path.read_text())
    register_unswept_indexes(store, docs)
    by_index: dict[str, dict] = {}
    headlines: dict[str, dict] = {}
    for key, idx in store.get("indexes", {}).items():
        ticker, _, year = key.partition(":")
        for sweep in [idx] + idx.get("previous_sweeps", []):
            sweep.update(index_coverage(ticker, int(year),
                                        sweep.get("retrieved_at") or now(),
                                        sweep.get("count", 0)))
            by_index[sweep["index_document_id"]] = sweep
        for row in idx.get("rows", []):
            row["headline"] = html.unescape(row.get("headline") or "")
            headlines[f"{ticker}:{row['ids_id']}"] = row
    fixed = 0
    for doc in docs.values():
        idx = by_index.get(doc["document_id"])
        if idx:
            doc["coverage"] = {k: idx[k] for k in
                               ("subject", "channel", "covered_from", "covered_to",
                                "complete", "retrieved_at", "completeness")}
            doc["reporting_dates"] = [idx["covered_from"], idx["covered_to"]]
            fixed += 1
        lodge = doc.get("lodgement") or {}
        if lodge.get("headline"):
            lodge["headline"] = html.unescape(lodge["headline"])
        elif lodge.get("ticker"):
            ids = next((s["value"] for s in doc["source_ids"]
                        if s.get("scheme") == "asx_ids_id"), None)
            row = headlines.get(f"{lodge['ticker']}:{ids}")
            if row:
                lodge["headline"] = row["headline"]
    store["generated"] = now()
    store_path.write_text(json.dumps(store, indent=1))
    return fixed


def register_unswept_indexes(store: dict, docs: dict[str, dict]) -> None:
    """Re-attach archived index artifacts the store had dropped.

    `indexes[ticker:year]` held one sweep, so re-sweeping a ticker overwrote the
    earlier entry and left its artifact in the store with nothing describing
    what it covered. Both sweeps are evidence — the earlier one is what a
    NOT_PUBLISHED finding made before the re-sweep actually rested on."""
    known = {sweep["index_document_id"]
             for idx in store.get("indexes", {}).values()
             for sweep in [idx] + idx.get("previous_sweeps", [])}
    for doc in docs.values():
        if doc["document_id"] in known:
            continue
        match = next((INDEX_URL_RE.search(a["url"]) for a in doc["url_aliases"]
                      if INDEX_URL_RE.search(a["url"])), None)
        if not match:
            continue
        ticker, year = match.group(1).upper(), match.group(2)
        entry = store.setdefault("indexes", {}).get(f"{ticker}:{year}")
        obj = ROOT / doc["object_locator"]
        sweep = {"index_document_id": doc["document_id"],
                 "retrieved_at": first_retrieved(doc),
                 "url": doc["url_aliases"][0]["url"],
                 "count": len(parse_asx_index(obj.read_text(errors="ignore")))
                          if obj.exists() else 0,
                 "recovered": "archived sweep not referenced by the store; re-attached "
                              "by kb.py reverify"}
        if entry is None:
            store["indexes"][f"{ticker}:{year}"] = {**sweep, "rows": []}
        elif sweep["retrieved_at"] > (entry.get("retrieved_at") or ""):
            entry.setdefault("previous_sweeps", []).append(
                {k: v for k, v in entry.items() if k not in ("rows", "previous_sweeps")})
            entry.update(sweep)
        else:
            entry.setdefault("previous_sweeps", []).append(sweep)
            entry["previous_sweeps"].sort(key=lambda s: s.get("retrieved_at") or "")


def index_coverage(ticker: str, year: int, retrieved_at: str, count: int) -> dict:
    """The interval an announcement-index sweep is evidence over."""
    covered_from = f"{year}-01-01"
    covered_to = min(f"{year}-12-31", retrieved_at[:10])
    complete = covered_to == f"{year}-12-31"
    return {
        "subject": ticker, "channel": "asx_announcement_index",
        "covered_from": covered_from, "covered_to": covered_to,
        "complete": complete, "retrieved_at": retrieved_at, "count": count,
        "completeness": (
            f"unfiltered exchange index over {ticker} from {covered_from} to "
            f"{covered_to}" + (
                " — the full calendar year; admissible for a NOT_PUBLISHED finding "
                "over that interval" if complete else
                f" — the year to date at retrieval; admissible for a NOT_PUBLISHED "
                f"finding over that interval ONLY. It says nothing about the rest of "
                f"{year}, which is not yet published; re-sweep to extend it")),
    }


def cmd_reverify(args) -> int:
    """Recompute provenance, titles, subjects, tiers and review flags over the
    whole store. Cheap, idempotent, and the only sanctioned way to change them.

    This is also the repair path for a store loaded under earlier rules: it
    withdraws filename-derived aliases, re-derives identifier bases, restates
    partial-year index coverage and moves analytical prose out of titles. Each
    step is a no-op on a store that is already correct."""
    docs = load_documents()
    legacy = legacy_index()
    sessions = repair_market_sessions(docs)
    mislabelled = repair_mislabelled_pdfs(docs)
    withdrawn = 0
    for doc in docs.values():
        for url in demote_inferred_aliases(doc):
            withdrawn += 1
            availability(doc["document_id"], "AVAILABLE_LOCAL",
                         channel="provenance-correction", url=url,
                         diagnosis="the AVAILABLE_LOCAL event recorded against this URL by "
                                   "the 23 Aug 2026 tmp migration is withdrawn: the URL was "
                                   "derived from the artifact's filename and never requested",
                         result_of="kb.py reverify")
        normalize_source_ids(doc)
    coverage_fixed = repair_index_coverage(docs)
    for doc in docs.values():
        assign_tier(doc)
    equivalence = link_equivalents(docs)
    for doc in docs.values():
        subjects = [s for s in doc.get("subjects", []) if valid_subject(s)]
        for a in doc["url_aliases"]:
            for s in (legacy.get(a["url"], {}).get("subjects") or []):
                if valid_subject(s) and s not in subjects:
                    subjects.append(s)
        if doc.get("lodgement", {}).get("ticker"):
            t = doc["lodgement"]["ticker"]
            if t not in subjects:
                subjects.insert(0, t)
        if not subjects:
            inferred = infer_subject(extracted_text(doc["sha256"]))
            if inferred:
                subjects = inferred
                doc["subject_basis"] = "inferred from the document text"
        doc["subjects"] = subjects
        resolve_title(doc, legacy)
        assign_tier(doc)
        doc["verified"] = verify_document(doc, extracted_text(doc["sha256"]))
    # An artifact established as the same publication as another takes that
    # publication's title — a title belongs to what was published, not to one
    # rendering of it. This runs after the main pass so every member's own title
    # is resolved first, and only original titles donate, so the donor does not
    # drift between runs.
    donors: dict[str, dict] = {}
    for doc in docs.values():
        group = (doc.get("equivalence") or {}).get("group")
        if not group or not doc.get("title"):
            continue
        if str(doc.get("title_source", "")).startswith("title of the equivalent"):
            continue
        if doc["document_id"] < donors.get(group, {}).get("document_id", "~"):
            donors[group] = doc
    for doc in docs.values():
        eq = doc.get("equivalence") or {}
        donor = donors.get(eq.get("group"))
        if not doc.get("title") and eq.get("equivalent") and donor:
            doc["title"] = donor["title"]
            doc["title_source"] = f"title of the equivalent artifact {donor['document_id']}"
            # The title is new evidence about the artifact, so its verification
            # state is recomputed here rather than at the next run.
            doc["verified"] = verify_document(doc, extracted_text(doc["sha256"]))
        doc["review"] = review_flags(doc)
    save_documents(docs)
    verified = sum(1 for d in docs.values() if all(d["verified"].values()))
    print(f"reverified {len(docs)} documents; {verified} fully verified, "
          f"{len(docs) - verified} carrying at least one open flag")
    if withdrawn:
        print(f"withdrew {withdrawn} filename-derived URL aliases to inferred provenance")
    if sessions:
        print(f"re-attached the approved-provider block to {sessions} market-session "
              f"artifacts loaded before it existed")
    if mislabelled:
        print(f"corrected {mislabelled} artifacts recorded as PDFs on the strength of a "
              f"filename; their derivatives were re-extracted")
    print(f"{coverage_fixed} exchange indexes restated to their retrieved coverage; "
          f"{equivalence['groups']} multi-version publications "
          f"({equivalence['equivalent']} equivalent, {equivalence['unproven']} unproven, "
          f"{equivalence['differing']} distinct)")
    return 0


def session_title(role: str, started: str) -> str:
    if role == "bar series":
        return f"IBKR TWS daily/intraday bars {started[:10]}"
    return f"IBKR TWS market session {started[:19]}Z"


def session_block(sess: dict, started: str, role: str, note: str) -> dict:
    """The durable provenance of an unrepeatable observation. Everything the
    tier, the publisher, the title and the verification state are recomputed
    from lives here, because there is no URL to recompute them from."""
    return {
        "provider": "ibkr-tws",
        "role": role,
        "session_start": started,
        "session_end": sess.get("finished_utc"),
        "engine_commit": sess.get("engine_commit"),
        "market_data_type": sess.get("market_data_type_requested_label"),
        "title": session_title(role, started),
        "verification_basis": ("self-describing session record written by build_index.py"
                               if role == "session bundle"
                               else "digest recorded in the session bundle"),
        "session_note": note,
    }


def apply_market_session(doc: dict) -> None:
    """Recompute what the provider block determines. `ingest-market-session` and
    `reverify` both come through here, so the two cannot drift apart — which is
    how the bundle and its bars ended up demoted to an issuer document after a
    reverify that the ingest path had set to T1."""
    assign_tier(doc)
    resolve_title(doc, {})
    doc["verified"] = verify_document(doc, "")
    doc["review"] = review_flags(doc)


def repair_mislabelled_pdfs(docs: dict[str, dict]) -> int:
    """A failed download saved with a `.pdf` name is not a PDF.

    The sniffer used to fall back to the extension, so an exchange interstitial
    saved as `bgl-5b-jun26.pdf` was recorded as `application/pdf` and put
    through pdftotext, which produced an empty derivative — a record describing
    an announcement, holding a web page, and extracting to nothing. The bytes
    decide; the derivative is remade from the corrected reading."""
    fixed = 0
    for doc in docs.values():
        if doc.get("mime_type") != "application/pdf":
            continue
        obj = ROOT / doc["object_locator"]
        if not obj.exists():
            continue
        with obj.open("rb") as fh:
            head = fh.read(16)
        if head.startswith(b"%PDF"):
            continue
        mime = sniff_mime(head, "", "")
        doc["mime_type"] = mime
        doc["evidence_note"] = (
            "Recorded as a PDF by the initial load because of its filename; the bytes are "
            f"{mime}. This artifact is not the document its name claims.")
        extract_derivatives(doc["sha256"], obj, mime, force=True)
        fixed += 1
    return fixed


def repair_market_sessions(docs: dict[str, dict]) -> int:
    """Re-attach the provider block to sessions archived before it existed.

    Their origin was only ever written into `tier_basis`, which `assign_tier`
    overwrites, so a reverify silently reclassified them. The acquisition note
    survived, and it names the session; that is enough to reconstruct the block
    and let the normal path recompute the rest."""
    repaired = 0
    for doc in docs.values():
        if market_provider(doc):
            continue
        via = next((a.get("via", "") for a in doc.get("acquisition", [])
                    if a.get("via", "").startswith(MARKET_SESSION_VIA)), None)
        if not via:
            continue
        started = doc.get("observation_as_of") or ""
        role = "session bundle" if via.startswith(MARKET_SESSION_VIA[0]) else "bar series"
        doc["market_session"] = {
            "provider": "ibkr-tws", "role": role, "session_start": started,
            "engine_commit": next((s["value"] for s in doc.get("source_ids", [])
                                   if s.get("scheme") == "engine_commit"), None),
            "title": session_title(role, started),
            "verification_basis": ("self-describing session record written by build_index.py"
                                   if role == "session bundle"
                                   else "digest recorded in the session bundle"),
            "session_note": via,
            "reattached_by": "kb.py reverify — archived before the provider block existed; "
                             "reconstructed from the acquisition record",
        }
        apply_market_session(doc)
        repaired += 1
    return repaired


def cmd_ingest_market_session(args) -> int:
    """Archive a TWS session as a source document.

    The methodology's approved market-data provider is primary for the
    observations it publishes (§4.1), so the bundle is T1 within
    `market.observation` and nothing else. It is also the one artifact in the
    store that can never be re-fetched: the session answered questions about a
    moment that has passed. That is precisely why it has to be archived at read
    time rather than pointed at — the failure recorded against the 17 August
    share counts in the initialization note.
    """
    bundle_path = Path(args.bundle)
    bars_path = Path(args.bars) if args.bars else bundle_path.parent / "market_bars.csv"
    bundle = json.loads(bundle_path.read_text())
    sess = bundle.get("session", {})
    started = sess.get("started_utc") or now()
    tickers = sess.get("tickers_requested") or []
    docs = load_documents()

    price_sources: dict[str, int] = {}
    for spec in (bundle.get("prices") or {}).values():
        src = spec.get("source") if isinstance(spec, dict) else None
        if src:
            price_sources[src] = price_sources.get(src, 0) + 1
    note = (f"TWS session {started} → {sess.get('finished_utc')}, "
            f"{len(bundle.get('requests', []))} requests, "
            f"{len(bundle.get('contracts', {}))} contracts, "
            f"market data requested {sess.get('market_data_type_requested_label')}"
            + (f"; prices by source {price_sources}" if price_sources else ""))

    ids = [source_id("tws_session_start", started, "session-record", True),
           source_id("engine_commit", sess.get("engine_commit", ""), "session-record", True)]
    main = ingest_bytes(
        bundle_path.read_bytes(), url=None,
        source_note=f"IBKR/TWS market session — {note}",
        legacy={"date": started[:10]},
        subjects=tickers, source_ids=ids, docs=docs, name=bundle_path.name)
    main["market_session"] = session_block(sess, started, "session bundle", note)
    main["observation_as_of"] = started
    main["reporting_dates"] = [started[:10]]
    main["refetchable"] = False
    main["evidence_note"] = (
        "Unrepeatable observation: the session cannot be reconstructed from any URL. "
        "Prices are as returned on this session — check `prices[].source` before "
        "reading a value as a live quote.")
    apply_market_session(main)

    if bars_path.exists():
        bars = ingest_bytes(bars_path.read_bytes(), url=None,
                            source_note=f"bar series for TWS session {started}",
                            legacy={"date": started[:10]},
                            subjects=tickers, docs=docs, name=bars_path.name)
        bars["market_session"] = session_block(sess, started, "bar series", note)
        bars["observation_as_of"] = started
        bars["reporting_dates"] = [started[:10]]
        bars["refetchable"] = False
        bars["part_of"] = main["document_id"]
        apply_market_session(bars)
        if bars["document_id"] not in main.setdefault("parts", []):
            main["parts"].append(bars["document_id"])
        availability(bars["document_id"], "AVAILABLE_LOCAL", channel="market-session",
                     object=bars["object_locator"])

    save_documents(docs)
    availability(main["document_id"], "AVAILABLE_LOCAL", channel="market-session",
                 object=main["object_locator"], note=note)
    print(f"[T1] {main['document_id']}  {main['bytes']/1000:.0f} kB  {main['title']}")
    if bars_path.exists():
        print(f"[T1] {main['parts'][0]}  bars series, linked to the session")
    return 0


def cmd_plan(args) -> int:
    """Acquisition queue: cited URLs whose bytes are not held, tier order."""
    docs = load_documents()
    held = {a["url"] for d in docs.values() for a in d["url_aliases"]}
    legacy = legacy_index()
    latest = availability_by_address()
    today = now()[:10]
    queue = []
    for url, meta in legacy.items():
        if url in held:
            continue
        cls = classify(url)
        item = {"url": url, **{k: cls[k] for k in ("authority_tier", "authority_domains",
                                                   "publisher", "tier_kind", "tier_note")},
                "title": meta.get("title"), "date": meta.get("date"),
                "subjects": meta.get("subjects"), "citations": meta.get("citations")}
        # A booked retry date outranks the tier: the highest-authority document
        # in the queue is still not fetched today if the host refused it and the
        # interval has not elapsed (§7.4).
        blocked = retry_block(url, latest, today)
        if blocked:
            item.update(blocked)
            item["deferred"] = (f"{blocked['last_result']} on "
                                f"{(blocked['last_checked_at'] or '')[:10]}; "
                                f"not retried before {blocked['next_retry_at']}")
        elif cls["tier_kind"] == "volatile":
            item["deferred"] = ("live endpoint — today's bytes are a new observation, "
                                "not the cited as-of artifact")
        elif cls["authority_tier"] == "T4":
            item["deferred"] = "discovery-only tier — never an accepted or provisional claim"
        queue.append(item)
    queue.sort(key=lambda i: (tier_rank(i["authority_tier"]), bool(i.get("deferred")), i["url"]))
    VIEWS.mkdir(parents=True, exist_ok=True)
    (VIEWS / "acquisition_queue.json").write_text(json.dumps(
        {"generated": now(), "held_urls": len(held), "queued": len(queue), "items": queue},
        indent=1))
    by_tier: dict[str, int] = {}
    for item in queue:
        key = item["authority_tier"] + (" (deferred)" if item.get("deferred") else "")
        by_tier[key] = by_tier.get(key, 0) + 1
    cited_held = len([u for u in legacy if u in held])
    waiting = [i for i in queue if i.get("next_retry_at")]
    print(f"{cited_held} of {len(legacy)} cited URLs held ({len(held)} aliases in the store); "
          f"{len(queue)} to acquire")
    for key in sorted(by_tier, key=lambda k: (tier_rank(k.split()[0]), k)):
        print(f"  {key:<18} {by_tier[key]}")
    if waiting:
        print(f"  {len(waiting)} held back by a booked retry date "
              f"(earliest {min(i['next_retry_at'] for i in waiting)})")
    if args.verbose:
        for item in queue:
            mark = "defer" if item.get("deferred") else "fetch"
            wait = f" until {item['next_retry_at']}" if item.get("next_retry_at") else ""
            print(f"  [{item['authority_tier']}] {mark}{wait}  {item['url'][:110]}")
    return 0


def http_get(url: str, referer: str | None = None) -> tuple[bytes, dict]:
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read(), {"status": resp.status, "final_url": resp.geturl(),
                                 "content_type": resp.headers.get("Content-Type", "")}
    except urllib.error.HTTPError:
        raise
    except Exception:
        # Not an HTTP refusal but a transport failure — several issuer IR hosts
        # (WebLink) serve an incomplete certificate chain that curl completes
        # from the system trust store and Python does not. Retry there before
        # calling the document unavailable; falling back is cheaper than
        # recording a false LINK_DEAD against a live artifact.
        return curl_get(url, referer)


CURL_MARK = b"\n__KB_TRAILER__"


def curl_get(url: str, referer: str | None = None) -> tuple[bytes, dict]:
    # The body is binary, so the status trailer needs an unambiguous marker;
    # splitting on the last tab would break on any PDF containing one.
    cmd = ["curl", "-sSL", "--fail", "--max-time", str(TIMEOUT), "-A", UA, "-o", "-",
           "-w", CURL_MARK.decode() + "%{http_code}\t%{content_type}\t%{url_effective}"]
    if referer:
        cmd += ["-e", referer]
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT + 30)
    if proc.returncode != 0:
        raise RuntimeError(f"curl exit {proc.returncode}: {proc.stderr.decode()[:160]}")
    idx = proc.stdout.rfind(CURL_MARK)
    if idx < 0:
        raise RuntimeError("curl: no status trailer in output")
    body = proc.stdout[:idx]
    status, ctype, final = (proc.stdout[idx + len(CURL_MARK):]
                            .decode(errors="ignore").split("\t") + ["", "", ""])[:3]
    return body, {"status": int(status or 0), "final_url": final or url,
                  "content_type": ctype, "via": "curl"}


def cmd_acquire(args) -> int:
    """Fetch queued documents, highest authority tier first. Every fetch records
    its reason; nothing already held by hash is fetched again (§2.1)."""
    cmd_plan(argparse.Namespace(verbose=False))
    queue = json.loads((VIEWS / "acquisition_queue.json").read_text())["items"]
    if args.retry_now:
        # The override is part of why the fetch happened, so it travels with the
        # reason onto every acquisition record it produces.
        args.reason = f"{args.reason} [--retry-now: booked retry date overridden]"
    tiers = args.tier or ["T1", "T2", "T3"]
    docs = load_documents()
    held_hashes = set(docs)
    done = failed = skipped = waiting = 0
    for item in queue:
        if item["authority_tier"] not in tiers:
            continue
        # A booked retry date is honoured even under --include-deferred: that
        # flag says "fetch the leads too", not "ignore what the host told us".
        # Only --retry-now overrides it, and it says so in the fetch reason.
        if item.get("next_retry_at") and not args.retry_now:
            waiting += 1
            continue
        if item.get("deferred") and not item.get("next_retry_at") and not args.include_deferred:
            skipped += 1
            continue
        if args.limit and done + failed >= args.limit:
            break
        url = item["url"]
        if args.dry_run:
            print(f"[{item['authority_tier']}] would fetch {url}")
            done += 1
            continue
        try:
            raw, resp = http_get(url)
        except urllib.error.HTTPError as e:
            state = {403: "BLOCKED", 404: "LINK_DEAD", 410: "LINK_DEAD"}.get(e.code, "MISSING_OBJECT")
            availability(url, state, channel="kb.acquire", http_status=e.code,
                         diagnosis=f"HTTP {e.code}", reason=args.reason)
            print(f"[{item['authority_tier']}] HTTP {e.code:<4} {url[:110]}")
            failed += 1
            time.sleep(POLITE_DELAY)
            continue
        except Exception as e:  # noqa: BLE001 — network failure modes are open-ended
            availability(url, "MISSING_OBJECT", channel="kb.acquire",
                         diagnosis=str(e)[:200], reason=args.reason)
            print(f"[{item['authority_tier']}] ERROR    {url[:110]}  {str(e)[:60]}")
            failed += 1
            time.sleep(POLITE_DELAY)
            continue
        mime = sniff_mime(raw[:16], resp["content_type"], url)
        # A 200 carrying an HTML error page where a PDF was expected is the
        # failure mode that reads as success. Catch it on the bytes.
        expected_pdf = url.lower().endswith(".pdf") or "asxpdf" in url or ASX_CDN in url
        if expected_pdf and mime != "application/pdf":
            availability(url, "LINK_DEAD", channel="kb.acquire", http_status=resp["status"],
                         diagnosis=f"expected application/pdf, received {mime} ({len(raw)} bytes)",
                         reason=args.reason)
            print(f"[{item['authority_tier']}] NOT-PDF  {url[:110]}")
            failed += 1
            time.sleep(POLITE_DELAY)
            continue
        legacy = {"title": item.get("title"), "date": item.get("date"),
                  "citations": [c for c in (item.get("citations") or [])]}
        volatile = item.get("tier_kind") == "volatile"
        if volatile:
            # A live endpoint serves today's numbers. Dating this artifact with
            # the cited as-of would forge evidence for a reading nobody took —
            # it is a NEW observation and must never be read as the old one.
            legacy = {"title": item.get("title"), "date": now()[:10]}
        doc = ingest_bytes(raw, url=url, source_note=f"kb.acquire — {args.reason}",
                           legacy=legacy, subjects=item.get("subjects"), docs=docs,
                           mime_hint=resp["content_type"], name=url)
        if volatile:
            doc["observation_as_of"] = now()
            doc["evidence_note"] = (
                "Point-in-time observation of a live endpoint. It does not evidence the "
                f"as-of date cited in data/ ({item.get('date')}); those bytes were not "
                "archived at the time and are unrecoverable.")
            doc["reporting_dates"] = [now()[:10]]
        merged = doc["sha256"] in held_hashes
        held_hashes.add(doc["sha256"])
        availability(doc["document_id"], "AVAILABLE_LOCAL", url=url, channel="kb.acquire",
                     http_status=resp["status"], object=doc["object_locator"],
                     reason=args.reason)
        print(f"[{doc['authority_tier']}] {'merged ' if merged else 'ok     '} "
              f"{len(raw)/1000:8.0f} kB  {url[:100]}")
        done += 1
        save_documents(docs)
        time.sleep(POLITE_DELAY)
    refresh_derived(docs)
    save_documents(docs)
    print(f"\nacquired {done}, failed {failed}, deferred {skipped}, "
          f"{waiting} not due for retry"
          + (" (--retry-now overrode the schedule)" if args.retry_now else ""))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# ASX exchange channel. The research API is capped at five items, so the legacy
# statistics endpoint is the only complete, unfiltered index — and completeness
# is what lets an absence be recorded as NOT_PUBLISHED instead of "not found"
# (§6.3). See docs/primary-document-fetching-strategy.md §1.1.
# ─────────────────────────────────────────────────────────────────────────────

ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)


def parse_asx_index(page: str) -> list[dict]:
    rows = []
    for block in ROW_RE.findall(page):
        m_ids = re.search(r"idsId=(\d+)", block)
        m_date = re.search(r"(\d{2})/(\d{2})/(\d{4})", block)
        if not (m_ids and m_date):
            continue
        m_head = re.search(r'idsId=\d+"[^>]*>(.*?)<br', block, re.S)
        # Unescaped, or the headline enters the store as the exchange's HTML
        # rather than as the words it published: "Appendix 4E &amp; ...".
        headline = html.unescape(
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m_head.group(1))).strip()
        ) if m_head else ""
        m_sens = re.search(r'class="pricesens".*?>(.*?)</td>', block, re.S)
        m_pages = re.search(r'class="page">\s*(\d+)', block)
        m_time = re.search(r'dates-time">([^<]+)<', block)
        rows.append({
            "ids_id": m_ids.group(1),
            "date": f"{m_date.group(3)}-{m_date.group(2)}-{m_date.group(1)}",
            "time": (m_time.group(1).strip() if m_time else None),
            "headline": headline,
            "price_sensitive": bool(m_sens and "<img" in m_sens.group(1)),
            "pages": int(m_pages.group(1)) if m_pages else None,
        })
    return rows


def resolve_asx_pdf(ids_id: str) -> str | None:
    """displayAnnouncement.do returns a terms interstitial; the real path is in
    a hidden form field."""
    raw, _ = http_get(ASX_DISPLAY.format(ids=ids_id))
    m = re.search(rb'name="pdfURL"\s+value="([^"]+)"', raw)
    return m.group(1).decode() if m else None


def cmd_asx_index(args) -> int:
    tickers = args.ticker or TICKERS
    years = args.year or [datetime.now(timezone.utc).year]
    docs = load_documents()
    store_path = VIEWS / "asx_lodgements.json"
    store = json.loads(store_path.read_text()) if store_path.exists() else {"indexes": {}}
    for ticker in tickers:
        for year in years:
            url = ASX_YEAR_INDEX.format(ticker=ticker, year=year)
            try:
                raw, resp = http_get(url)
            except Exception as e:  # noqa: BLE001
                availability(url, "MISSING_OBJECT", channel="asx-year-index",
                             diagnosis=str(e)[:200])
                print(f"{ticker} {year}: FAILED {str(e)[:60]}")
                continue
            retrieved_at = now()
            rows = parse_asx_index(raw.decode("utf-8", errors="ignore"))
            cover = index_coverage(ticker, year, retrieved_at, len(rows))
            doc = ingest_bytes(raw, url=url,
                               source_note=f"ASX announcement index, {cover['covered_from']} "
                                           f"to {cover['covered_to']}",
                               legacy={"title": f"ASX announcement index — {ticker} {year}",
                                       "date": retrieved_at[:10]},
                               subjects=[ticker], docs=docs, retrieved_at=retrieved_at,
                               mime_hint=resp["content_type"], name=f"{ticker}-{year}.html")
            doc["authority_domains"] = ["exchange.index"]
            doc["coverage"] = {k: cover[k] for k in
                               ("subject", "channel", "covered_from", "covered_to",
                                "complete", "retrieved_at", "completeness")}
            doc["reporting_dates"] = [cover["covered_from"], cover["covered_to"]]
            # A re-sweep does not erase the earlier one: a NOT_PUBLISHED finding
            # made last week rests on the index as it stood last week.
            previous = store.get("indexes", {}).get(f"{ticker}:{year}")
            history = previous.get("previous_sweeps", []) if previous else []
            if previous and previous["index_document_id"] != doc["document_id"]:
                history = history + [{k: v for k, v in previous.items()
                                      if k not in ("rows", "previous_sweeps")}]
            store["indexes"][f"{ticker}:{year}"] = {
                "index_document_id": doc["document_id"], "url": url, "rows": rows, **cover,
                **({"previous_sweeps": history} if history else {}),
            }
            availability(f"{ticker}:{year} announcement index", "AVAILABLE_LOCAL",
                         url=url, channel="asx-year-index", count=len(rows),
                         object=doc["object_locator"],
                         covers=f"{cover['covered_from']}..{cover['covered_to']}")
            print(f"{ticker} {year}: {len(rows):4} lodgements, "
                  f"{cover['covered_from']}..{cover['covered_to']}"
                  f"{'' if cover['complete'] else ' (year to date)'}")
            time.sleep(POLITE_DELAY)
    save_documents(docs)
    store["generated"] = now()
    VIEWS.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(store, indent=1))
    return 0


def cmd_asx_acquire(args) -> int:
    """Download lodged PDFs off the exchange index. Bytes that match an artifact
    already held merge into it and carry it to T1 — that is the mirror
    equivalence rule doing its work, not a second copy."""
    store_path = VIEWS / "asx_lodgements.json"
    if not store_path.exists():
        print("no index: run `kb.py asx-index` first")
        return 1
    store = json.loads(store_path.read_text())
    docs = load_documents()
    held_ids = {s["value"] for d in docs.values() for s in d["source_ids"]
                if s["scheme"] == "asx_ids_id"}
    held_hashes = set(docs)
    pattern = re.compile(args.match, re.I) if args.match else None
    done = failed = 0
    for key, idx in sorted(store.get("indexes", {}).items()):
        ticker, _, year = key.partition(":")
        if args.ticker and ticker not in args.ticker:
            continue
        for row in idx["rows"]:
            if args.since and row["date"] < args.since:
                continue
            if pattern and not pattern.search(row["headline"]):
                continue
            if row["ids_id"] in held_ids:
                continue
            if args.limit and done + failed >= args.limit:
                break
            if args.dry_run:
                print(f"{ticker} {row['date']} would fetch: {row['headline'][:90]}")
                done += 1
                continue
            try:
                pdf_url = resolve_asx_pdf(row["ids_id"])
                if not pdf_url:
                    raise RuntimeError("no pdfURL in the interstitial")
                time.sleep(POLITE_DELAY)
                raw, resp = http_get(pdf_url, referer=ASX_DISPLAY.format(ids=row["ids_id"]))
            except Exception as e:  # noqa: BLE001
                availability(f"asx:{ticker}:{row['ids_id']}", "MISSING_OBJECT",
                             channel="asx-index-pdf", diagnosis=str(e)[:200],
                             headline=row["headline"])
                print(f"{ticker} {row['date']} FAILED  {row['headline'][:70]}  {str(e)[:50]}")
                failed += 1
                continue
            if not raw.startswith(b"%PDF"):
                availability(pdf_url, "LINK_DEAD", channel="asx-index-pdf",
                             diagnosis=f"expected a PDF, received {len(raw)} bytes of "
                                       f"{resp.get('content_type')}")
                print(f"{ticker} {row['date']} NOT-PDF {row['headline'][:70]}")
                failed += 1
                continue
            doc = ingest_bytes(
                raw, url=pdf_url, source_note="ASX year index → displayAnnouncement pdfURL",
                legacy={"title": row["headline"], "date": row["date"]},
                subjects=[ticker],
                source_ids=[source_id("asx_ids_id", row["ids_id"],
                                      "exchange-index-row", True)],
                docs=docs, mime_hint=resp.get("content_type", ""), name=pdf_url)
            doc.setdefault("lodgement", {}).update({
                "ticker": ticker, "lodged_on": row["date"], "lodged_time": row["time"],
                "headline": row["headline"],
                "price_sensitive": row["price_sensitive"], "pages": row["pages"],
                "index_document_id": idx["index_document_id"]})
            doc["published_on"] = doc["published_on"] or row["date"]
            merged = doc["sha256"] in held_hashes
            held_hashes.add(doc["sha256"])
            held_ids.add(row["ids_id"])
            availability(doc["document_id"], "AVAILABLE_LOCAL", url=pdf_url,
                         channel="asx-index-pdf", object=doc["object_locator"])
            print(f"{ticker} {row['date']} {'merged→T1' if merged else 'ok       '} "
                  f"{len(raw)/1000:7.0f} kB  {row['headline'][:70]}")
            done += 1
            save_documents(docs)
            time.sleep(POLITE_DELAY)
    refresh_derived(docs)
    save_documents(docs)
    print(f"\nacquired {done}, failed {failed}")
    return 0


def refresh_derived(docs: dict[str, dict]) -> dict[str, int]:
    """Re-run the whole-store passes after new bytes arrive. A fetch can settle
    an artifact that was already held: the same publication under one exchange
    key resolves the inferred copy, which changes its tier.

    Tiers are assigned twice on purpose. The first pass settles what each record
    earns on its own, which is what an equivalence check has to compare against;
    the second lets the members of a group inherit. Without the first pass the
    result depends on how many times the command has been run."""
    for doc in docs.values():
        assign_tier(doc)
    stats = link_equivalents(docs)
    for doc in docs.values():
        assign_tier(doc)
        doc["review"] = review_flags(doc)
    return stats


def cmd_verify_inferred(args) -> int:
    """Test filename-derived provenance against the publisher.

    `reverify` settles what can be settled from bytes already held. This settles
    the rest, and it is the only way an artifact that arrived as a bare /tmp
    file earns T1: fetch the address its filename implies and see what comes
    back. Three outcomes, all recorded — the same bytes (the address is a real
    alias), a regenerated copy that extracts to the same text (equivalent, and
    the fetched artifact carries the verified provenance), or something else
    (the inference is refuted and the record stays where it is)."""
    docs = load_documents()
    pending = [d for d in docs.values()
               if any(i.get("state") == "unverified" and i.get("candidate_urls")
                      for i in d.get("inferred_provenance", []))]
    print(f"{len(pending)} documents carry unverified filename-derived provenance")
    checked = confirmed = equivalent = refuted = failed = 0
    for doc in pending:
        if args.limit and checked >= args.limit:
            break
        for inf in doc["inferred_provenance"]:
            if inf.get("state") != "unverified":
                continue
            for cand in inf.get("candidate_urls", []):
                if args.dry_run:
                    print(f"would fetch {cand['url'][:110]}")
                    checked += 1
                    continue
                checked += 1
                try:
                    raw, resp = http_get(cand["url"])
                except Exception as e:  # noqa: BLE001 — network failure modes are open-ended
                    availability(doc["document_id"], "MISSING_OBJECT", url=cand["url"],
                                 channel="verify-inferred", diagnosis=str(e)[:200])
                    print(f"FAILED    {cand['url'][:100]}  {str(e)[:50]}")
                    failed += 1
                    continue
                if sha256_bytes(raw) == doc["sha256"]:
                    doc["url_aliases"].append(
                        {"url": cand["url"], "first_seen": now(), "last_verified": now(),
                         "origin": classify(cand["url"])["tier_basis"],
                         "note": "confirmed by fetch: this address serves exactly these bytes"})
                    doc["acquisition"].append(
                        {"at": now(), "url": cand["url"],
                         "via": "kb.verify-inferred — fetched to test filename-derived "
                                "provenance; the address returned these exact bytes"})
                    for sid in inf.get("source_ids", []):
                        add_source_id(doc, {**sid, "basis": "retrieval-url", "verified": True})
                    inf.update(state="confirmed", resolved_at=now(),
                               resolution="the address serves these exact bytes")
                    confirmed += 1
                    print(f"CONFIRMED {cand['url'][:100]}")
                else:
                    fetched = ingest_bytes(
                        raw, url=cand["url"],
                        source_note=f"kb.verify-inferred — checking the filename-derived "
                                    f"provenance of {doc['document_id']}",
                        subjects=doc.get("subjects"), docs=docs,
                        mime_hint=resp.get("content_type", ""), name=cand["url"])
                    same, why = same_publication(extracted_text(fetched["sha256"], None),
                                                 extracted_text(doc["sha256"], None))
                    inf.update(state="equivalent" if same else "refuted", resolved_at=now(),
                               fetched_artifact=fetched["document_id"],
                               resolution=(f"the address serves a regenerated copy of the "
                                           f"same document — {why}" if same else
                                           f"the address does not serve these bytes: {why}"))
                    tested = {s["value"] for s in inf.get("source_ids", [])}
                    for sid in doc.get("source_ids", []):
                        if sid.get("verified") or sid.get("value") not in tested:
                            continue
                        if same:
                            # The identifier names this publication — the exchange
                            # serves the same document under it. It stays unverified
                            # FOR THESE BYTES, which came off a local disk, and the
                            # equivalence record is what carries the tier.
                            sid["resolved_by"] = (
                                f"equivalence with {fetched['document_id']}, fetched "
                                f"from the address this identifier implies")
                        else:
                            sid["basis"] = "local-filename (refuted by fetch)"
                    equivalent += same
                    refuted += not same
                    print(f"{'EQUIVALENT' if same else 'REFUTED   '} {cand['url'][:97]}")
                availability(doc["document_id"], "AVAILABLE_LOCAL", url=cand["url"],
                             channel="verify-inferred", http_status=resp.get("status"),
                             diagnosis=inf.get("resolution"))
                time.sleep(POLITE_DELAY)
    if not args.dry_run:
        refresh_derived(docs)
        save_documents(docs)
    print(f"\nchecked {checked}: {confirmed} confirmed, {equivalent} equivalent, "
          f"{refuted} refuted, {failed} unreachable")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Routing a local artifact through the exchange index (§4.2, §7.2)
#
# An artifact that arrived as a bare file has no route: nothing on the record
# says where it came from, so it is unclassified however confidently its
# filename or its text names an issuer. The exchange's own per-year index is a
# way to earn one. Every row is a lodged announcement with a headline, a date
# and a page count, so a row can be proposed as this artifact's publication and
# then TESTED — fetch what the exchange serves for that row and compare. The
# comparison decides, never the proposal.
#
# Three outcomes, all recorded: the exchange serves exactly these bytes (the
# route is this artifact's own, and the identifier is verified for it); it
# serves a regenerated copy extracting to identical text (the identifier names
# the publication, the fetched artifact carries the verified provenance, and
# this record reaches the lodged tier by equivalence); or it serves something
# else (the proposal is refuted and the next candidate is tried).
# ─────────────────────────────────────────────────────────────────────────────

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
PDF_DATE_RE = re.compile(r"\w{3}\s+(\w{3})\s+(\d{1,2})\s+[\d:]+\s+(\d{4})")
ROUTE_MIN_SCORE = 5
ROUTE_MAX_CANDIDATES = 4


def pdf_created_on(digest: str) -> str | None:
    """The creation date the PDF carries in its own metadata, as ISO."""
    man = EXTRACTED / digest / "extraction.json"
    if not man.exists():
        return None
    m = PDF_DATE_RE.search(json.loads(man.read_text()).get("pdf_created") or "")
    if not m or m.group(1) not in MONTHS:
        return None
    return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"


def days_between(a: str, b: str) -> int | None:
    try:
        return abs((datetime.strptime(a[:10], "%Y-%m-%d")
                    - datetime.strptime(b[:10], "%Y-%m-%d")).days)
    except Exception:
        return None


def index_rows_by_ticker(store: dict) -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    for key, idx in store.get("indexes", {}).items():
        ticker, _, year = key.partition(":")
        for row in idx.get("rows", []):
            rows.setdefault(ticker, []).append(
                {**row, "year": year, "index_document_id": idx.get("index_document_id"),
                 "index_url": idx.get("url")})
    return rows


def route_candidates(doc: dict, rows: list[dict]) -> list[dict]:
    """Index rows that could name this artifact's publication, best first.

    Scored on the three things an index row and a PDF can be compared on
    without fetching anything: how many pages each says it has, how close the
    lodgement date is to the date the file says it was created, and whether the
    words of the headline appear in the document. A score is a reason to go and
    check, never a finding."""
    man = EXTRACTED / doc["sha256"] / "extraction.json"
    pages = json.loads(man.read_text()).get("pages") if man.exists() else None
    created = pdf_created_on(doc["sha256"])
    text = extracted_text(doc["sha256"], 8000).lower()
    scored = []
    for row in rows:
        score, why = 0, []
        if pages and row.get("pages") == pages:
            score += 3
            why.append(f"{pages} pages")
        gap = days_between(row["date"], created) if created else None
        if gap is not None and gap <= 6:
            score += 2
            why.append(f"lodged {row['date']}, file created {created}")
        tokens = [w.lower() for w in re.findall(r"[A-Za-z0-9]{4,}", row.get("headline", ""))]
        if tokens and sum(1 for w in tokens if w in text) / len(tokens) >= 0.6:
            score += 2
            why.append("headline words appear in the document")
        if doc.get("published_on") and doc["published_on"][:10] == row["date"]:
            score += 1
        if score >= ROUTE_MIN_SCORE:
            scored.append({**row, "score": score, "why": "; ".join(why)})
    scored.sort(key=lambda r: (-r["score"], r["date"]))
    return scored[:ROUTE_MAX_CANDIDATES]


def routed_by_inference(doc: dict) -> bool:
    """Did `verify-inferred` already settle where these bytes came from?

    A filename-derived address that was fetched and compared is a tested route,
    reached by a different door. Re-testing it against the index would spend
    requests to learn what the record already says."""
    return any(i.get("state") in ("confirmed", "equivalent")
               for i in doc.get("inferred_provenance", []))


def has_route(doc: dict) -> bool:
    return bool(doc.get("url_aliases")) or bool(market_provider(doc)) \
        or bool((doc.get("retrieval_route") or {}).get("ids_id")) or routed_by_inference(doc)


def unrouted_local(docs: dict[str, dict], recheck: bool = False) -> list[dict]:
    """Artifacts held locally that nothing on the record says how to re-obtain.

    An artifact already tested and left unresolved is skipped unless `recheck`
    says otherwise: the index has not changed since, so re-running would spend
    the same requests to reach the same answer. `--recheck` is for after the
    index is re-swept, or after the comparison itself is changed."""
    return sorted((d for d in docs.values()
                   if not has_route(d)
                   and (recheck or not (d.get("retrieval_route") or {}).get("state"))),
                  key=lambda d: (d.get("subjects") or [""])[0] + d["sha256"])


def record_lodgement(doc: dict, row: dict, ticker: str) -> None:
    doc.setdefault("lodgement", {}).update({
        "ticker": ticker, "lodged_on": row["date"], "lodged_time": row.get("time"),
        "headline": html.unescape(row.get("headline") or ""),
        "price_sensitive": row.get("price_sensitive"), "pages": row.get("pages"),
        "index_document_id": row["index_document_id"]})
    doc["published_on"] = doc.get("published_on") or row["date"]


def cmd_route_local(args) -> int:
    """Give every bare local artifact a tested retrieval route, or leave it
    unclassified and say what was tried."""
    store_path = VIEWS / "asx_lodgements.json"
    if not store_path.exists():
        print("no archived index: run `kb.py asx-index` first")
        return 1
    rows_by_ticker = index_rows_by_ticker(json.loads(store_path.read_text()))
    docs = load_documents()
    by_ids: dict[str, dict] = {}
    for d in docs.values():
        for sid in d.get("source_ids", []):
            if sid.get("scheme") == "asx_ids_id" and sid.get("verified"):
                by_ids.setdefault(sid["value"], d)

    targets = unrouted_local(docs, recheck=args.recheck)
    if args.ticker:
        targets = [d for d in targets if set(d.get("subjects") or []) & set(args.ticker)]
    print(f"{len(targets)} local artifacts carry no retrieval route")
    confirmed = equivalent = unresolved = 0
    for n, doc in enumerate(targets, 1):
        if args.limit and n > args.limit:
            break
        ticker = (doc.get("subjects") or [None])[0]
        label = Path((doc.get("local_paths") or ["?"])[0]).name
        cands = route_candidates(doc, rows_by_ticker.get(ticker, [])) if ticker else []
        if not cands:
            print(f"  [{ticker}] {label:<34} no index row scores as a candidate")
            if not args.dry_run:
                record_route_attempt(doc, [], "no index row scores as a candidate")
            unresolved += 1
            continue
        if args.dry_run:
            print(f"  [{ticker}] {label:<34} {len(cands)} candidates: "
                  + ", ".join(f"{c['ids_id']} {c['headline'][:40]} ({c['score']})"
                              for c in cands))
            continue
        outcome = route_one(doc, cands, ticker, docs, by_ids, label)
        if outcome == "confirmed":
            confirmed += 1
        elif outcome == "equivalent":
            equivalent += 1
        else:
            unresolved += 1
        save_documents(docs)
    if not args.dry_run:
        refresh_derived(docs)
        save_documents(docs)
    print(f"\nrouted {confirmed + equivalent} of {len(targets)}: {confirmed} serve exactly "
          f"these bytes, {equivalent} equivalent to the lodged artifact, "
          f"{unresolved} still unrouted (T4)")
    return 0


def record_route_attempt(doc: dict, tried: list[dict], why: str) -> None:
    """What was tested against this artifact and what came back. Kept whether or
    not it worked — an unrouted artifact should say what has already been ruled
    out, so the next pass does not repeat it."""
    doc["retrieval_route"] = {"channel": "asx_announcement_index", "state": "unresolved",
                              "attempted_at": now(), "basis": why, "candidates_tested": tried}


def route_one(doc: dict, cands: list[dict], ticker: str, docs: dict[str, dict],
              by_ids: dict[str, dict], label: str) -> str:
    tried = []
    local_text = extracted_text(doc["sha256"], None)
    for cand in cands:
        ids = cand["ids_id"]
        display = ASX_DISPLAY.format(ids=ids)
        held = by_ids.get(ids)
        try:
            if held is not None:
                # The exchange copy of this row is already in the store. Nothing
                # is fetched: the comparison is the same one, against bytes the
                # exchange has already served us (§2.1).
                other, pdf_url = held, next(
                    (a["url"] for a in held["url_aliases"]), cand.get("index_url"))
                raw = None
            else:
                pdf_url = resolve_asx_pdf(ids)
                if not pdf_url:
                    raise RuntimeError("no pdfURL in the exchange interstitial")
                time.sleep(POLITE_DELAY)
                raw, resp = http_get(pdf_url, referer=display)
                if not raw.startswith(b"%PDF"):
                    raise RuntimeError(f"expected a PDF, received {len(raw)} bytes")
                other = None
        except Exception as e:  # noqa: BLE001 — network failure modes are open-ended
            availability(f"asx:{ticker}:{ids}", "MISSING_OBJECT", channel="route-local",
                         diagnosis=str(e)[:200], headline=cand.get("headline"))
            tried.append({"ids_id": ids, "headline": cand.get("headline"),
                          "outcome": f"unreachable: {str(e)[:80]}"})
            print(f"  [{ticker}] {label:<34} {ids} unreachable  {str(e)[:40]}")
            continue

        if raw is not None and sha256_bytes(raw) == doc["sha256"]:
            stamp = now()
            doc["url_aliases"].append(
                {"url": pdf_url, "first_seen": stamp, "last_verified": stamp,
                 "origin": classify(pdf_url)["tier_basis"],
                 "note": "confirmed by fetch through the exchange index: this address "
                         "serves exactly these bytes"})
            doc["acquisition"].append(
                {"at": stamp, "url": pdf_url,
                 "via": f"kb.route-local — exchange index row {ids} resolved through "
                        f"{display}; the address returned these exact bytes"})
            add_source_id(doc, source_id("asx_ids_id", ids, "exchange-index-row", True))
            record_lodgement(doc, cand, ticker)
            doc["retrieval_route"] = {
                "channel": "asx_announcement_index", "state": "identical-bytes",
                "ids_id": ids, "index_document_id": cand["index_document_id"],
                "index_url": cand.get("index_url"), "display_url": display,
                "pdf_url": pdf_url, "lodged_on": cand["date"],
                "headline": html.unescape(cand.get("headline") or ""),
                "compared": "sha256", "matched_on": cand.get("why"),
                "basis": "the exchange served exactly these bytes for this index row",
                "resolved_at": stamp, "candidates_tested": tried}
            availability(doc["document_id"], "AVAILABLE_LOCAL", url=pdf_url,
                         channel="route-local", object=doc["object_locator"],
                         diagnosis="the exchange serves exactly these bytes")
            print(f"  [{ticker}] {label:<34} {ids} SAME BYTES   {cand['headline'][:44]}")
            return "confirmed"

        if other is None:
            other = ingest_bytes(
                raw, url=pdf_url,
                source_note=f"kb.route-local — exchange index row {ids}, fetched to test "
                            f"the provenance of {doc['document_id']}",
                legacy={"title": cand.get("headline"), "date": cand["date"]},
                subjects=[ticker],
                source_ids=[source_id("asx_ids_id", ids, "exchange-index-row", True)],
                docs=docs, mime_hint="application/pdf", name=pdf_url)
            record_lodgement(other, cand, ticker)
            by_ids.setdefault(ids, other)
            availability(other["document_id"], "AVAILABLE_LOCAL", url=pdf_url,
                         channel="route-local", object=other["object_locator"])

        other_text = extracted_text(other["sha256"], None)
        same, why = same_publication(other_text, local_text)
        if same:
            add_source_id(doc, {"scheme": "asx_ids_id", "value": ids,
                                "basis": INDEX_ROUTE_BASIS, "verified": False})
            doc["retrieval_route"] = {
                "channel": "asx_announcement_index", "state": "equivalent-regeneration",
                "ids_id": ids, "index_document_id": cand["index_document_id"],
                "index_url": cand.get("index_url"), "display_url": display,
                "pdf_url": pdf_url, "lodged_on": cand["date"],
                "headline": html.unescape(cand.get("headline") or ""),
                "equivalent_artifact": other["document_id"], "compared": "extracted text",
                "matched_on": cand.get("why"),
                "basis": f"the exchange serves this publication as a different artifact; "
                         f"these bytes were not served there, and the two are the same "
                         f"document — {why}",
                "resolved_at": now(), "candidates_tested": tried}
            availability(doc["document_id"], "AVAILABLE_LOCAL", url=pdf_url,
                         channel="route-local", object=doc["object_locator"],
                         diagnosis=f"equivalent to {other['document_id']} by extracted text")
            print(f"  [{ticker}] {label:<34} {ids} EQUIVALENT   {cand['headline'][:44]}")
            return "equivalent"

        tried.append({"ids_id": ids, "headline": cand.get("headline"),
                      "compared_with": other["document_id"], "outcome": why})
        print(f"  [{ticker}] {label:<34} {ids} "
              f"{'no text' if same is None else 'differs'}      {cand['headline'][:44]}")
    record_route_attempt(doc, tried, "every candidate index row was tested and none matched")
    return "unresolved"


def version_entry(doc: dict, alias: dict | None = None) -> dict:
    eq = doc.get("equivalence") or {}
    entry = {"document_id": doc["document_id"],
             "retrieved_at": (alias or {}).get("first_seen") or first_retrieved(doc),
             "bytes": doc["bytes"], "mime": doc["mime_type"],
             "tier": doc["authority_tier"], "title": doc.get("title")}
    if alias and alias.get("last_verified"):
        entry["last_verified"] = alias["last_verified"]
    if eq:
        entry["equivalent_to_verified_member"] = eq.get("equivalent")
        entry["equivalence_basis"] = eq.get("basis")
    return entry


def cmd_views(args) -> int:
    docs = load_documents()
    VIEWS.mkdir(parents=True, exist_ok=True)
    by_ticker: dict[str, list] = {}
    by_tier: dict[str, list] = {}
    urls: dict[str, list[dict]] = {}
    ids: dict[str, list[dict]] = {}
    for d in docs.values():
        row = {"document_id": d["document_id"], "title": d.get("title"),
               "published_on": d.get("published_on"), "tier": d["authority_tier"],
               "mime": d["mime_type"], "bytes": d["bytes"],
               "object": d["object_locator"], "aliases": [a["url"] for a in d["url_aliases"]],
               "review": d.get("review", [])}
        for t in d.get("subjects") or ["_unassigned"]:
            by_ticker.setdefault(t, []).append(row)
        by_tier.setdefault(d["authority_tier"], []).append(row)
        for a in d["url_aliases"]:
            urls.setdefault(a["url"], []).append(version_entry(d, a))
        for sid in d["source_ids"]:
            ids.setdefault(f"{sid['scheme']}:{sid['value']}", []).append(
                {**version_entry(d), "identifier_verified": bool(sid.get("verified")),
                 "identifier_basis": sid.get("basis")})
    (VIEWS / "by_ticker.json").write_text(json.dumps(
        {"generated": now(), "tickers": {k: sorted(v, key=lambda r: r["published_on"] or "")
                                         for k, v in sorted(by_ticker.items())}}, indent=1))
    (VIEWS / "by_tier.json").write_text(json.dumps(
        {"generated": now(), "tiers": {k: by_tier[k] for k in sorted(by_tier, key=tier_rank)}},
        indent=1))
    # A URL is a route, and a route can serve different bytes on different days
    # (§4.2). Every version it served is listed in retrieval order; `latest` is
    # the most recent retrieval, NOT a ruling on which artifact is correct.
    def ordered(groups: dict[str, list[dict]]) -> dict[str, dict]:
        out = {}
        for key, entries in sorted(groups.items()):
            entries = sorted(entries, key=lambda e: (e["retrieved_at"], e["document_id"]))
            out[key] = {"versions": entries, "version_count": len(entries),
                        "latest": entries[-1]["document_id"]}
            if len(entries) > 1:
                out[key]["multiple_versions"] = (
                    "this key resolves to more than one artifact; each record's "
                    "`equivalence` states whether they are the same document")
        return out

    (VIEWS / "url_aliases.json").write_text(json.dumps(
        {"generated": now(),
         "note": "url -> artifact versions in retrieval order; a URL is an access "
                 "route, never an identity",
         "urls": ordered(urls)}, indent=1))
    (VIEWS / "source_ids.json").write_text(json.dumps(
        {"generated": now(),
         "note": "publisher/exchange identifier -> artifact versions in retrieval "
                 "order; `identifier_verified` is false where the identifier was "
                 "inferred (e.g. read off a local filename) and not yet checked",
         "identifiers": ordered(ids)}, indent=1))
    review = [{"document_id": d["document_id"], "title": d.get("title"),
               "tier": d["authority_tier"], "flags": d["review"],
               "aliases": [a["url"] for a in d["url_aliases"]]}
              for d in docs.values() if d.get("review")]
    (VIEWS / "review_queue.json").write_text(json.dumps(
        {"generated": now(), "count": len(review), "items": review}, indent=1))
    claims = read_jsonl(CLAIMS)
    by_subject: dict[str, list[dict]] = {}
    active_claims: dict[str, dict] = {}
    for claim in claims:
        key = claim.get("claim_key") or {}
        row = {"claim_id": claim.get("claim_id"), "predicate": key.get("predicate"),
               "scope": key.get("scope"), "as_of": key.get("as_of"),
               "state": claim.get("state"), "projectable": claim.get("projectable"),
               "document_id": (claim.get("evidence") or {}).get("document_id"),
               "projection": claim.get("projection")}
        by_subject.setdefault(key.get("subject") or "_unassigned", []).append(row)
        if claim.get("state") in ACTIVE_CLAIM_STATES:
            active_claims[json.dumps(key, sort_keys=True)] = row
    (VIEWS / "claims_by_subject.json").write_text(json.dumps(
        {"generated": now(), "subjects": {
            subject: sorted(rows, key=lambda r: (r.get("predicate") or "",
                                                  r.get("as_of") or ""))
            for subject, rows in sorted(by_subject.items())}}, indent=1))
    (VIEWS / "active_claims.json").write_text(json.dumps(
        {"generated": now(), "claims": active_claims}, indent=1))
    quarantined = read_jsonl(QUARANTINE)
    (VIEWS / "quarantine.json").write_text(json.dumps(
        {"generated": now(), "count": len(quarantined), "items": quarantined}, indent=1))
    multi = sum(1 for v in urls.values() if len(v) > 1)
    print(f"views regenerated: {len(docs)} documents, {len(urls)} URLs "
          f"({multi} with more than one version), {len(ids)} source identifiers, "
          f"{len(review)} needing review, {len(claims)} claims, "
          f"{len(quarantined)} quarantined pointers")
    return 0


def audit_promotion(doc: dict) -> str | None:
    """Is this record's tier supported by something other than its own claim?

    T1 says a controlling authority published these bytes. That has to rest on a
    URL at the authority's own host, an identifier obtained from the authority,
    or a checked equivalence with an artifact that has one. A filename does not
    qualify, and neither does an identifier whose only basis is that filename."""
    if doc.get("authority_tier") != "T1":
        return None
    # An approved provider's own observation. The support is the session record
    # on the artifact, not the string in `tier_basis` — which is why this asks
    # the provider registry rather than reading the field back.
    if market_provider(doc):
        return None
    if doc.get("tier_basis") == MARKET_PROVIDER_BASIS:
        return ("T1 claims an approved market-data provider but carries no market_session "
                "block naming one")
    unretrieved = None
    for alias in doc.get("url_aliases", []):
        if classify(alias["url"])["authority_tier"] != "T1":
            continue
        if alias_was_retrieved(doc, alias):
            return None
        unretrieved = alias["url"]
    if verified_exchange_id(doc):
        return None
    eq = doc.get("equivalence") or {}
    if eq.get("equivalent") and eq.get("inherits_tier") == "T1":
        return None
    if unretrieved:
        return ("T1 rests on an alias with no retrieval event behind it — nothing was "
                f"ever requested from {unretrieved[:80]}")
    inferred = [s for s in doc.get("source_ids", []) if not s.get("verified")]
    return ("T1 without a verified basis" + (
        f" — the only exchange identifier came from {inferred[0].get('basis')}"
        if inferred else f" (tier_basis {doc.get('tier_basis')})"))


def alias_was_retrieved(doc: dict, alias: dict) -> bool:
    """Did anything actually come back from this address?

    An alias is a claim that these bytes were served there, and the acquisition
    trail is what backs it. The nine T1 records this check exists for all had an
    exchange-host alias and no request behind it — the address had been built
    out of a filename, so classifying the host proved nothing."""
    events = [a for a in doc.get("acquisition", []) if a.get("url") == alias["url"]]
    return any(not a.get("via", "").startswith(TMP_VIA) for a in events)


def audit_coverage(doc: dict, today: str) -> list[str]:
    """No record may claim evidence over a date that has not happened. An index
    swept today cannot cover December, and a coverage interval that runs past
    its own retrieval is the same error stated a different way."""
    problems = []
    for field in ("published_on", "observation_as_of"):
        value = doc.get(field)
        if value and value[:10] > today:
            problems.append(f"{field} {value[:10]} is in the future")
    for date in doc.get("reporting_dates") or []:
        if date and date[:10] > today:
            problems.append(f"reporting date {date[:10]} is in the future")
    cover = doc.get("coverage") or {}
    if cover:
        retrieved = (cover.get("retrieved_at") or "")[:10]
        covered_to = cover.get("covered_to", "")
        # Three separate claims, reported separately: a sweep cannot cover the
        # future, cannot cover past the moment it was taken, and cannot call an
        # interval it did not observe complete.
        if covered_to > today:
            problems.append(f"coverage runs to {covered_to}, which is in the future")
        if retrieved and covered_to > retrieved:
            problems.append(f"coverage runs to {covered_to} but the index was "
                            f"retrieved on {retrieved}")
            if cover.get("complete"):
                problems.append("a partial-interval sweep is described as complete")
        if cover.get("covered_from", "") > covered_to:
            problems.append("coverage interval ends before it starts")
    return problems


def audit_title(doc: dict) -> str | None:
    """Titles hold publisher metadata. Analysis in the title field makes a
    reading of the document look like the document's own name for itself.

    Length and sentence structure catch the long ones. The short ones — a note
    reference, a table description, half a sentence after a dash — are caught by
    reading the tail, and only where the title did NOT come from the publisher:
    an exchange headline or an HTML `<title>` containing a dash is the
    publisher's own punctuation, not our commentary."""
    title = doc.get("title")
    if not title:
        return None
    if len(title) > TITLE_MAX:
        return f"title is {len(title)} characters — analytical prose, not a title"
    if SENTENCE_RE.search(title):
        return "title runs to more than one sentence — analysis, not a title"
    if doc.get("title_source") in PUBLISHER_TITLE_SOURCES:
        return None
    parts = DASH_SPLIT_RE.split(title, 1)
    if len(parts) > 1 and parts[1].strip() and is_gloss(parts[1].strip()):
        return (f"title carries an analytical suffix — {parts[1].strip()[:60]!r} is a "
                f"reading of the document and belongs in legacy.notes")
    return None


def audit_ambiguity(docs: dict[str, dict]) -> list[str]:
    """A URL or an exchange identifier resolving to several artifacts is fine —
    publishers regenerate files. Leaving it unresolved is not: each artifact
    must say, on its own record, how it relates to the others."""
    problems = []
    for key, members in sorted(publication_groups(docs).items()):
        undecided = [m for m in members
                     if key not in ((m.get("equivalence") or {}).get("keys") or [])]
        if undecided:
            problems.append(
                f"{key} resolves to {len(members)} artifacts with no recorded version "
                f"relation for {len(undecided)} of them: "
                + ", ".join(m["document_id"][:20] for m in undecided[:3]))
            continue
        distinct = [m for m in members if (m.get("equivalence") or {}).get("equivalent") is False]
        if distinct and key.startswith("asx_"):
            problems.append(
                f"{key} carries {len(distinct)} artifact(s) whose content differs from the "
                f"verified copy — one exchange identifier cannot name two documents")
    return problems


def json_pointer_get(blob, pointer: str):
    node = blob
    for raw in pointer.lstrip("/").split("/") if pointer else []:
        part = raw.replace("~1", "/").replace("~0", "~")
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def audit_claim_plane(docs: dict[str, dict], *, projection: bool = False) \
        -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    claims = read_jsonl(CLAIMS)
    all_by_id = {c.get("claim_id"): c for c in claims}
    by_id: dict[str, dict] = {}
    active: dict[str, str] = {}
    for claim in claims:
        cid = claim.get("claim_id", "?")
        if not re.fullmatch(r"claim:sha256:[0-9a-f]{64}", cid):
            errors.append(f"{cid}: invalid claim_id")
        if cid in by_id:
            errors.append(f"{cid}: duplicate claim record")
        by_id[cid] = claim
        key = claim.get("claim_key")
        if not isinstance(key, dict) or not all(k in key for k in
                                                ("subject", "predicate", "scope", "as_of")):
            errors.append(f"{cid}: incomplete normalized claim key")
            continue
        state = claim.get("state")
        if state not in CLAIM_STATES:
            errors.append(f"{cid}: invalid claim state {state!r}")
        encoded_key = json.dumps(key, sort_keys=True)
        if state in ACTIVE_CLAIM_STATES:
            if encoded_key in active:
                errors.append(f"two active claims for {encoded_key}")
            active[encoded_key] = cid
        evidence = claim.get("evidence") or {}
        did = evidence.get("document_id")
        doc = docs.get(did.removeprefix("sha256:")) if isinstance(did, str) else None
        if did and not doc:
            errors.append(f"{cid}: evidence document {did} is not registered")
        if doc:
            if claim.get("authority_tier") != doc.get("authority_tier"):
                errors.append(f"{cid}: authority tier does not match its artifact")
            if claim.get("authority_domains") != doc.get("authority_domains"):
                errors.append(f"{cid}: authority domains do not match its artifact")
        exceptions = set((claim.get("migration") or {}).get("exceptions") or [])
        if not key.get("as_of"):
            if "AS_OF_NOT_SEPARATELY_CAPTURED" in exceptions:
                warnings.append(f"{cid}: legacy claim has no separately captured as-of date")
            else:
                errors.append(f"{cid}: claim key has no as-of date")
        exact = bool((evidence.get("locator") or {}).get("exact"))
        if state in ACTIVE_CLAIM_STATES and not exact:
            if "EXACT_LOCATOR_NOT_CAPTURED" in exceptions:
                warnings.append(f"{cid}: grandfathered legacy claim has only a "
                                "document-level citation")
            else:
                errors.append(f"{cid}: active claim without an exact evidence locator")
        derivation = claim.get("derivation")
        if derivation is not None and not derivation.get("dependencies"):
            if "DERIVATION_DEPENDENCIES_NOT_ATOMIZED" in exceptions:
                warnings.append(f"{cid}: legacy derivation dependencies are not atomized")
            else:
                errors.append(f"{cid}: derivation has no dependency claim IDs")
        if claim.get("projectable") != (state in ACTIVE_CLAIM_STATES):
            # Accepted observations may deliberately be held out until the next
            # reviewed rebalance; their decision code names that state.
            held = (claim.get("decision") or {}).get("code") in HELD_FROM_PROJECTION_CODES
            if not (state in ACTIVE_CLAIM_STATES and not claim.get("projectable") and held):
                errors.append(f"{cid}: projectable flag conflicts with claim state")
        for predecessor in claim.get("supersedes") or []:
            old = all_by_id.get(predecessor)
            if not old:
                errors.append(f"{cid}: supersedes missing claim {predecessor}")
                continue
            old_key = old.get("claim_key") or {}
            if (old_key.get("subject"), old_key.get("predicate")) != \
                    (key.get("subject"), key.get("predicate")):
                errors.append(f"{cid}: supersedes unrelated claim {predecessor}")
            if old.get("superseded_by") != cid:
                errors.append(f"{cid}: predecessor {predecessor} does not link back")
            if old.get("state") not in ("SUPERSEDED", "STALE"):
                errors.append(f"{cid}: predecessor {predecessor} remains {old.get('state')}")
            old_paths = {
                item.get("path") for item in [old.get("projection") or {},
                                               *(old.get("projection_history") or [])]
                if item.get("path")
            }
            new_path = ((claim.get("projection") or
                         claim.get("projection_candidate") or {}).get("path"))
            if old_paths and new_path and new_path not in old_paths:
                errors.append(
                    f"{cid}: supersession projection path {new_path!r} does not match "
                    f"predecessor {predecessor}")

    for claim in claims:
        successor = claim.get("superseded_by")
        if not successor:
            continue
        if successor not in all_by_id:
            errors.append(f"{claim.get('claim_id')}: superseded_by missing claim {successor}")
            continue
        if claim.get("claim_id") not in (all_by_id[successor].get("supersedes") or []):
            errors.append(f"{claim.get('claim_id')}: successor {successor} does not link back")

    for claim in claims:
        if (claim.get("decision") or {}).get("code") != "CONTROLLING_TIER_CONFLICT":
            continue
        cid = claim["claim_id"]
        alternatives = claim.get("conflicts") or []
        if claim.get("state") != "UNRESOLVED" or claim.get("projectable"):
            errors.append(f"{cid}: controlling-tier conflict is not non-projectable UNRESOLVED")
        if (claim.get("value") or {}).get("value") is not None:
            errors.append(f"{cid}: controlling-tier conflict selected a value")
        if len(alternatives) < 2:
            errors.append(f"{cid}: controlling-tier conflict does not preserve both paths")
        tiers = {alt.get("authority_tier") for alt in alternatives}
        if len(tiers) != 1:
            errors.append(f"{cid}: conflict alternatives are not at one controlling tier")
        for alt in alternatives:
            did = alt.get("document_id")
            if not did or did.removeprefix("sha256:") not in docs:
                errors.append(f"{cid}: conflict alternative has no registered evidence")

    quarantine_ids = set()
    forbidden = {"value", "typed_value", "reported_value", "range", "reported_range"}
    for rec in read_jsonl(QUARANTINE):
        qid = rec.get("quarantine_id", "?")
        if not re.fullmatch(r"quarantine:sha256:[0-9a-f]{64}", qid):
            errors.append(f"{qid}: invalid quarantine_id")
        if qid in quarantine_ids:
            errors.append(f"{qid}: duplicate quarantine record")
        quarantine_ids.add(qid)
        if forbidden.intersection(rec):
            errors.append(f"{qid}: quarantine contains an active-value field")
        if not (rec.get("candidate") and rec.get("reason_code") and
                (rec.get("blocked_by") or rec.get("related_claim"))):
            errors.append(f"{qid}: quarantine pointer is incomplete")
        linked = rec.get("blocked_by") or rec.get("related_claim")
        if linked not in by_id:
            errors.append(f"{qid}: linked claim {linked} does not exist")
        if rec.get("blocked_by") and by_id.get(linked, {}).get("state") not in ACTIVE_CLAIM_STATES:
            errors.append(f"{qid}: blocked_by does not identify a controlling active claim")

    # One field, one projection basis. Supersession moves the block to
    # `projection_history` precisely so that two records cannot both claim to be
    # what `data/` reads; leaving both is the silent-choice defect (§7.3).
    basis: dict[str, str] = {}
    for claim in claims:
        path = (claim.get("projection") or {}).get("path")
        if not path:
            continue
        if path in basis:
            errors.append(f"{path}: {basis[path][:30]}… and {claim['claim_id'][:30]}… both "
                          f"record themselves as the projection basis for one field")
        basis[path] = claim["claim_id"]

    if projection:
        company_data = json.loads((ROOT / "data/companies.json").read_text())
        projected = {c.get("projection", {}).get("path"): c for c in claims
                     if c.get("projection", {}).get("file") == "data/companies.json"}
        expected = []
        for group in ("companies", "excluded"):
            for ci, company in enumerate(company_data.get(group, [])):
                for predicate in (company.get("fields") or {}):
                    expected.append(f"/{group}/{ci}/fields/{predicate}")
                for pi, project in enumerate(company.get("execution_capital_projects") or []):
                    for predicate in PROJECT_FIELDS:
                        if predicate in project:
                            expected.append(
                                f"/{group}/{ci}/execution_capital_projects/{pi}/{predicate}")
        for path in expected:
            claim = projected.get(path)
            if not claim:
                errors.append(f"{path}: projected field has no claim")
                continue
            source = json_pointer_get(company_data, path)
            field_spec = source if "/fields/" in path and isinstance(source, dict) else None
            if field_spec is not None:
                source = field_spec.get("v")
            claimed = (claim.get("value") or {}).get("value")
            if source != claimed:
                errors.append(f"{path}: projection differs from {claim.get('claim_id')}")
            if field_spec is not None:
                allows_unresolved = field_spec.get("evidence_state") == "UNRESOLVED"
            else:
                project = json_pointer_get(company_data, path.rsplit("/", 1)[0])
                allows_unresolved = (project.get("committed_capex_state") == "UNRESOLVED"
                                     or project.get("execution_capital_state") == "UNRESOLVED")
            if claim.get("state") not in ACTIVE_CLAIM_STATES and not allows_unresolved:
                errors.append(f"{path}: projected field resolves to non-projectable "
                              f"{claim.get('state')} claim")
    return errors, warnings


def cmd_audit(args) -> int:
    """Audit the evidence plane and, once populated, the knowledge plane."""
    docs = load_documents()
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, str] = {}
    today = now()[:10]
    for d in docs.values():
        did = d.get("document_id", "?")
        if not re.fullmatch(r"[0-9a-f]{64}", d.get("sha256", "")):
            errors.append(f"{did}: invalid content hash")
        if d.get("document_id") != f"sha256:{d.get('sha256')}":
            errors.append(f"{did}: document_id does not match its hash")
        obj = ROOT / d.get("object_locator", "")
        if not obj.exists():
            errors.append(f"{did}: object missing at {d.get('object_locator')}")
        elif args.deep and sha256_file(obj) != d["sha256"]:
            errors.append(f"{did}: stored object does not hash to its identity")
        if d.get("authority_tier") not in TIER_ORDER:
            errors.append(f"{did}: no authority tier")
        if not d.get("authority_domains"):
            errors.append(f"{did}: authority tier without a domain")
        if not d.get("verified"):
            errors.append(f"{did}: no verification state")
        if d["sha256"] in seen_ids:
            errors.append(f"{did}: duplicate document record")
        seen_ids[d["sha256"]] = did
        unsupported = audit_promotion(d)
        if unsupported:
            errors.append(f"{did}: {unsupported}")
        for problem in audit_coverage(d, today):
            errors.append(f"{did}: {problem}")
        polluted = audit_title(d)
        if polluted:
            errors.append(f"{did}: {polluted}")
        if d.get("storage_state") != "durable":
            warnings.append(f"{did}: object is local-only, not durable")
        for flag in d.get("review", []):
            if flag not in ("object-not-durable",):
                warnings.append(f"{did}: {flag}")
    for problem in audit_ambiguity(docs):
        errors.append(problem)
    claims = read_jsonl(CLAIMS)
    claim_errors, claim_warnings = audit_claim_plane(docs, projection=args.projection)
    errors.extend(claim_errors)
    warnings.extend(claim_warnings)
    print(f"documents {len(docs)}, claims {len(claims)}, "
          f"errors {len(errors)}, warnings {len(warnings)}")
    for e in errors:
        print(f"  ERROR   {e}")
    if args.warnings:
        for w in warnings[:args.warnings if isinstance(args.warnings, int) else len(warnings)]:
            print(f"  warn    {w}")
    else:
        counts: dict[str, int] = {}
        for w in warnings:
            counts[w.split(": ", 1)[1]] = counts.get(w.split(": ", 1)[1], 0) + 1
        for k, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  warn    {n:4}  {k}")
    if errors and args.strict:
        return 1
    return 0


KB_README = """# knowledge/ — source-priority knowledge base

Generated and maintained by `tools/kb.py`. The binding design is
`../source-knowledge-base.md`; this file only describes the physical layout.

```
documents.jsonl     one record per immutable artifact, keyed by SHA-256
claims.jsonl        normalized claims and derivations
quarantine.jsonl    blocked candidates: pointers and reasons, never a value
availability.jsonl  append-only retrieval and negative-search events
objects/sha256/..   exact raw bytes, content addressed, two-character shard
extracted/<hash>/   reproducible text/pdfinfo derivatives, tier inherited
views/              generated indexes — regenerate, never hand-edit
```

`objects/` and `extracted/` are not committed: the store holds several gigabytes
of publisher PDFs and the repository has no LFS remote. This is an explicitly
permitted arrangement (`../source-knowledge-base.md` §6.4), not an open defect —
with the consequence stated plainly: **the store is not portable.** A clone gets
the registries, the views and the full decision trail, but no bytes, and
`audit --deep` cannot re-hash what is not there. Every record therefore carries
`storage_state: "local"` and the audit reports the gap on all of them.

What makes the bytes re-obtainable IS committed, and that is the condition of
the arrangement: the SHA-256 of every artifact, every full retrieval URL and the
channel it was reached through, every publisher identifier with its basis, and
the registries and views themselves.

Fields the reader should not confuse:

* `url_aliases` — addresses these exact bytes were served at. Never a
  constructed or expected address.
* `inferred_provenance` — what a filename or a local path suggests, with the
  candidate address it implies. A lead, not evidence; `verify-inferred` is what
  settles it.
* `retrieval_route` — how a bare local artifact was matched to a publisher's
  own copy, with the index row, the full addresses, what was compared and what
  came back. `state: unresolved` means it was tested and nothing matched.
* `market_session` — the provenance of an observation that can never be
  re-fetched. It is what the tier, title and verification of a session artifact
  are recomputed from.
* `source_ids[].verified` — true only where the identifier came from the
  publisher's own route. Only a verified exchange identifier can promote a
  record to T1.
* `equivalence` — a recorded finding that two artifacts are the same
  publication, with the basis. Several artifacts under one key is normal;
  leaving their relation unstated is not.
* `coverage` — for an index sweep, the interval it is actually evidence over.
* `title` / `legacy.notes` — the publisher's name for the document, and the
  analysis carried over from `data/`, kept apart.

`claims.jsonl` and `quarantine.jsonl` have exactly two write paths.

`backfill-claims` migrates the current `data/companies.json` projection. It
preserves those values, records explicit legacy gaps rather than concealing
them, and separately registers newer archived point-in-time observations
without projecting them. It owns only what it regenerates: a researched claim
survives a re-run untouched, and a backfilled claim that has since been
superseded keeps its supersession.

`register-claim` registers a claim established by reading a source. Claims
carrying a migration exception are review work and do not relax the
requirements here: a registration needs an archived artifact, an exact
page/table/note/section locator, a verbatim excerpt, an as-of date kept apart
from the publication date, and a decision reason. Tier and domain are copied
from the artifact and cannot be asserted by the spec. It runs the §5.1
precedence sequence for the claim key and refuses rather than guesses — a
lower-tier candidate incompatible with a higher-tier claim gets a quarantine
pointer, an incompatible candidate at the same tier leaves the key unresolved,
and a claim that resolves an `UNRESOLVED` key must supersede it. Supersession
is a link forward: the predecessor keeps its value, evidence and decision, and
only the `projection` block moves, to `projection_history`, so one field never
has two records claiming to be what `data/` reads.

An accepted claim may be deliberately held out of the projection —
`projectable: false` with `ARCHIVED_POINT_IN_TIME_OBSERVATION` or
`HELD_FOR_REVIEWED_REBALANCE` — when adopting it is a rebalance decision rather
than a storage one. `projection_pending` on such a claim records what `data/`
would become, without changing it.

Do not hand-edit any file here. Writes go through `tools/kb.py`.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create the store skeleton")

    p = sub.add_parser("ingest-local", help="consume .cache/ and /tmp/ without network access")
    p.add_argument("--source", choices=["cache", "tmp", "all"], default="all")

    p = sub.add_parser("ingest-file", help="archive a file fetched outside the tool")
    p.add_argument("--path", required=True)
    p.add_argument("--url", help="retrieval URL — recorded as an alias, not an identity")
    p.add_argument("--title")
    p.add_argument("--date")
    p.add_argument("--subject", action="append")
    p.add_argument("--note")

    p = sub.add_parser("ingest-market-session",
                       help="archive a TWS session bundle as a T1 market observation")
    p.add_argument("--bundle", default="market_bundle.json")
    p.add_argument("--bars", help="defaults to market_bars.csv beside the bundle")

    p = sub.add_parser("plan", help="print and write the acquisition queue, tier order")
    p.add_argument("--verbose", action="store_true")

    p = sub.add_parser("acquire", help="fetch queued documents, highest tier first")
    p.add_argument("--tier", action="append", choices=TIER_ORDER,
                   help="restrict to these tiers (repeatable); default T1,T2,T3")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--include-deferred", action="store_true",
                   help="also fetch volatile endpoints and T4 leads")
    p.add_argument("--retry-now", action="store_true",
                   help="override booked next_retry_at dates (recorded in the fetch reason)")
    p.add_argument("--reason", default="initial KB load: cited document not held locally")

    p = sub.add_parser("asx-index", help="sweep the exchange's full-year announcement index")
    p.add_argument("--ticker", action="append")
    p.add_argument("--year", action="append", type=int)

    p = sub.add_parser("asx-acquire", help="download lodged PDFs from the swept index")
    p.add_argument("--ticker", action="append")
    p.add_argument("--match", help="headline regex")
    p.add_argument("--since", help="ISO date floor")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("route-local",
                       help="give bare local artifacts a retrieval route by testing them "
                            "against the archived exchange index")
    p.add_argument("--ticker", action="append")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--dry-run", action="store_true",
                   help="print the candidate index rows without fetching")
    p.add_argument("--recheck", action="store_true",
                   help="also re-test artifacts a previous run left unresolved")

    p = sub.add_parser("verify-inferred",
                       help="fetch the addresses filename-derived provenance implies "
                            "and record whether they hold up")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")

    sub.add_parser("reverify", help="recompute provenance, titles, tiers and review flags")

    p = sub.add_parser("backfill-claims",
                       help="backfill company claims and pointer-only quarantine records")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("register-claim",
                       help="register researched claims, supersessions and quarantine "
                            "pointers from a JSON spec, running §5.1 precedence")
    p.add_argument("--file", required=True, help="path to the registration spec")
    p.add_argument("--dry-run", action="store_true")

    sub.add_parser("views", help="regenerate generated indexes")

    p = sub.add_parser("audit", help="strict audit of the document plane")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--deep", action="store_true", help="re-hash every stored object")
    p.add_argument("--projection", action="store_true",
                   help="also require every current company projection to resolve to a "
                        "projectable, value-identical claim (cutover readiness)")
    p.add_argument("--warnings", nargs="?", const=200, type=int, default=0)

    args = ap.parse_args()
    return {
        "init": cmd_init, "ingest-local": cmd_ingest_local, "ingest-file": cmd_ingest_file,
        "ingest-market-session": cmd_ingest_market_session,
        "backfill-claims": cmd_backfill_claims, "register-claim": cmd_register_claim,
        "plan": cmd_plan, "reverify": cmd_reverify, "verify-inferred": cmd_verify_inferred,
        "route-local": cmd_route_local,
        "acquire": cmd_acquire, "asx-index": cmd_asx_index, "asx-acquire": cmd_asx_acquire,
        "views": cmd_views, "audit": cmd_audit,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
