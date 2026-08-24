# Source-priority knowledge base — binding design

- **Status:** binding repository policy
- **Effective:** 23 August 2026
- **Applies to:** source discovery, acquisition, retention, extraction, claims,
  conflict resolution, and projection into `data/`
- **Does not change:** index construction, eligibility, weights, or the field
  definitions in the binding methodology

## 1. Authority and purpose

This document is the source-management authority for SJGV. It is subordinate to
`index-methodology.md` on index construction and to law and source documents on
external facts. Within its scope it is binding: narrative notes, retrieval
convenience, agent judgement, and lower-authority sources cannot override it.
`data/README.md` remains the field-schema authority and must be amended with
this document if a future schema change affects both layers.

The repository currently has useful evidence in four disconnected forms:

- source metadata duplicated in each company's `documents` map;
- accepted values in `data/companies.json`;
- narrative conflict history in `data/SOURCES.md` and `docs/`;
- URL-keyed raw and extracted files in the ignored `.cache/` directory.

This fragmentation causes agents to rediscover URLs, re-download documents,
lose documents when publishers move them, and resolve the same conflict more
than once. The source-priority knowledge base (KB) replaces that behavior with
one durable evidence layer, one claim ledger, and generated consumer views.

The governing flow is:

```text
immutable source artifact -> scoped claim(s) -> precedence decision -> data/ projection
```

The artifact proves what a source said. The claim ledger records what the
repository may assert. `data/companies.json` remains the production engine's
input, not an independent store of knowledge.

## 2. Non-negotiable invariants

1. **Look up before fetching.** Search the KB by subject, predicate, reporting
   date, source identifier, URL alias, and content hash before using the
   network. A fetch needs a recorded reason: no admissible source, a field's
   freshness rule has expired, a relevant corporate event occurred, the stored
   object failed integrity checking, or an explicit refresh was requested.
2. **Archive before extracting.** Accepted evidence starts with the exact raw
   bytes inspected by the researcher. Extracted text, OCR, page images, and
   summaries are reproducible derivatives, never substitutes for the artifact.
3. **Identity is content-based.** URLs are mutable access routes. A document is
   identified by its SHA-256 content hash and any publisher or exchange
   identifiers. The same bytes obtained from several URLs are one artifact
   with several aliases.
4. **Every source has an authority tier and domain.** A tier is meaningless
   without the kind of fact for which the publisher is authoritative.
5. **Every claim is scoped.** Subject, predicate, effective or as-of date,
   asset or jurisdiction, attribution basis, category, period, unit, and
   currency are part of identity where applicable. Apparent conflicts must not
   be resolved until these dimensions are reconciled.
6. **Higher authority is a hard barrier.** A lower-tier source may fill a true
   gap provisionally, but it may not replace, average with, widen, narrow, or
   otherwise alter an incompatible higher-tier claim.
7. **Conflicting lower-tier assertions are not knowledge.** Their raw source
   artifacts may be retained for audit, but their conflicting values must not
   enter the active claim ledger, derived claims, summaries, or `data/`.
   Quarantine records contain pointers and the rejection reason, not a second
   active value.
8. **Ambiguity degrades or fails.** An unresolved conflict at the highest
   applicable tier remains unresolved. It is never settled by choosing a
   convenient value or by descending to a lower tier.
9. **History is immutable.** Corrections and restatements supersede claims; they
   do not erase artifacts, old claims, or the decision trail.
10. **Derive or fail still governs.** A derived claim names every input claim
    and its formula. Its authority cannot exceed its weakest factual input, and
    it becomes stale when an input is superseded.

## 3. The three planes

| Plane | Holds | Must not do |
|---|---|---|
| Evidence | Raw artifacts, hashes, source identity, URL aliases, retrieval and availability events, reproducible extractions | Decide which factual value is active |
| Knowledge | Normalized claims, evidence locators, derivations, precedence, status, supersession, and quarantine pointers | Invent a missing value or silently change field definitions |
| Projection | The current values and provenance consumed by `build_index.py`, principally `data/companies.json` | Become a second conflict-resolution system |

An extraction is not a claim. A document mentioning a number does not make the
number applicable to a field. A claim becomes projectable only after its scope,
authority, evidence locator, and precedence status are valid.

## 4. Authority tiers

Authority is assigned by origin and domain, not by the server from which bytes
were downloaded. A verified byte-identical mirror inherits the origin's tier.
An unverified copy does not.

| Tier | Name | Admissible examples | Permitted use |
|---|---|---|---|
| T0 | Binding repository authority | `index-methodology.md`; this document; binding schema and recorded amendments | Repository rules and definitions only. T0 cannot establish an issuer, market, or jurisdictional fact. |
| T1 | Controlling or lodged primary | Enacted law and regulation; regulator or exchange records; issuer filings lodged with ASX/AIM/TSX; audited statements inside those filings; official government or statutory series in its mandate | Active factual knowledge within the authority's domain |
| T2 | Other first-party primary | Issuer-hosted presentations, releases, IR tables, and reports not verified as lodged; official agency guidance or data outside a controlling instrument | Active knowledge when no applicable T1 claim conflicts; subject to field-specific admissibility rules |
| T3 | Attributed secondary | A reputable secondary publication that identifies the primary basis and preserves the relevant scope | Provisional gap-filling only. It must be labelled and replaced by primary evidence before a live rebalance unless the methodology explicitly permits it. |
| T4 | Discovery only | Search snippets, aggregators without traceable primary evidence, unattributed news, analyst estimates, AI output, and informal commentary | Leads and search terms only; never an accepted or provisional factual claim |

`primary`, `secondary`, and `derived` in the legacy company schema are too
coarse to encode this table. During migration they remain descriptive labels;
the KB tier and domain control precedence.

### 4.1 Domain limits

A source is authoritative only for claims inside its competence:

- an issuer is primary for its issued shares, accounts, guidance, projects,
  resources, reserves, and corporate actions;
- an exchange or regulator is primary for what was lodged and when, but does
  not independently vouch for every technical estimate in a lodging;
- a legislature, regulator, or revenue authority is primary for law, licence
  status, royalties, and statutory rules within its jurisdiction;
- a market venue or the repository's approved market-data provider is primary
  for the observations it publishes under the methodology's market-data rules;
- SJGV methodology is primary for index definitions, not for external facts.

Publisher prestige outside the relevant domain confers no higher tier.

An approved provider's session is the one artifact class with no retrieval
route: it answered questions about an instant that has passed, and no address
will return those bytes again. Its origin is therefore recorded on the artifact
itself and is what its tier is recomputed from. It must not be inferred from
anything the session mentions — the instruments a session quotes are its
subject, not its publisher.

### 4.2 Mirrors and transformations

- An identical ASX filing served by an issuer CDN or filing mirror remains T1
  if equivalence is established by matching bytes, a trusted exchange document
  identifier, or a documented verification of the complete artifact.
- HTML-to-text, `pdftotext -layout`, OCR, and rendered pages inherit the
  artifact's tier but are marked as transformations. They never acquire an
  authority of their own.
- A secondary article quoting a T1 filing remains T3 until the filing itself is
  archived and the claim is verified against it.
- A direct publisher URL that later serves different bytes creates a new
  artifact version. It never overwrites the earlier object.
- An artifact held locally with no recorded retrieval route is unclassified,
  whatever its filename or its text says about who issued it. A subject read
  out of a document is what the document is ABOUT; it is not evidence of who
  served the bytes, and it cannot buy that publisher's tier. A route is earned
  by testing: fetch what the publisher serves — through the exchange index row,
  or the address a filename implies — and compare. Identical bytes make the
  address this artifact's own; the same document rendered differently is
  recorded as an equivalence, with the fetched artifact carrying the verified
  identifier; anything else refutes the proposal and the record stays where it
  is, with what was tried recorded on it.
- Equivalence between two renderings of one document is established page for
  page on the extracted text. Reading order is a property of the extractor, not
  of the document, and fragments of an exchange watermark that one distributor
  draws as text may differ; the number of pages, and the words on each of them,
  may not. The comparison and its result are recorded, never assumed.

## 5. Claim identity and conflict rules

The minimum logical claim key is:

```text
(subject, predicate, scope, as_of)
```

`scope` expands as required to include asset, geography, ownership attribution,
resource category, reserve/resource boundary, period start and end, currency,
unit, price basis, accounting basis, and methodology-specific qualifiers. Units
are normalized for comparison but the reported unit is preserved.

Two values conflict only when they resolve to the same claim key and cannot
both be true after unit conversion, rounding tolerance, and stated ranges are
applied. These are not conflicts:

- the same field at different as-of dates;
- group and attributable quantities;
- Mineral Resources inclusive of Ore Reserves and M&I non-reserve ounces;
- guidance for different periods;
- a source document and a byte-identical mirror of it.

Silence is not a claim. A higher-tier document that does not address a field
does not conflict with a lower-tier source that does. The lower-tier claim may
be admissible under its tier, but it remains labelled accordingly.

### 5.1 Precedence algorithm

For each claim key, the KB must apply this sequence mechanically:

1. Validate subject, field definition, dates, basis, units, and evidence
   locator. Incomparable candidates are split into different keys or rejected
   as under-scoped.
2. Find the highest authority tier containing an admissible candidate for that
   domain and field.
3. At that tier, an explicit correction or restatement supersedes the document
   it names. For the same as-of date, a later publication that explicitly
   updates the same fact supersedes the earlier publication.
4. Apply field-specific rules already recorded in `data/README.md` or the
   methodology, such as attribution and resource-category rules. A summary
   headline does not override its own detailed table merely because it is more
   prominent.
5. If incompatible candidates remain at the same controlling tier, set the
   claim to `UNRESOLVED`, preserve both evidence paths, and omit or reject the
   projected value according to the field policy.
6. Quarantine every incompatible lower-tier candidate with `blocked_by` and a
   reason code. Do not copy its value into active knowledge or narrative
   summaries as an alternative estimate.
7. Evaluate derived claims only after all dependencies have an active status.

Recency selects among claims only after scope and authority. A lower-tier page
with a newer publication date cannot silently revise a T1 fact for the same
claim key; it triggers a search for a new T1 document. A genuinely later as-of
date is a new claim, not an override of history.

### 5.2 Claim states

The active ledger uses these states:

- `ACCEPTED` — admissible at the controlling available tier;
- `PROVISIONAL` — admissible T3 gap-fill or an explicitly temporary primary
  claim allowed by field policy;
- `UNRESOLVED` — incompatible or incomplete evidence at the controlling tier;
- `SUPERSEDED` — formerly active, replaced by an explicit correction,
  restatement, or later applicable claim;
- `STALE` — freshness policy expired or a dependency was superseded;
- `REJECTED` — invalid scope, definition, evidence, or provenance.

Only one claim may be active for a claim key. `SUPERSEDED`, `STALE`, and
`REJECTED` records remain addressable for audit but cannot feed a projection.
`PROVISIONAL` may feed a projection only where the binding field policy allows
it and must propagate its label.

## 6. Canonical storage model

The target store lives under `knowledge/`. JSON Lines is used for appendable,
diffable registries; generated indexes and views are rebuildable.

```text
knowledge/
├── documents.jsonl          one record per immutable artifact
├── claims.jsonl             normalized claims and derivations
├── quarantine.jsonl         blocked/rejected candidate pointers; no active values
├── availability.jsonl       append-only retrieval and negative-search events
├── objects/sha256/ab/<hash> exact raw bytes, content addressed
├── extracted/<hash>/        reproducible text, OCR, and page/image derivatives
└── views/                   generated indexes by ticker, field, date, and source id
```

The physical blob backend may be Git LFS, another repository-approved durable
object store, or — as adopted on 23 August 2026 and set out in §6.4 — a
gitignored local object directory. Whichever is in use, the following are
mandatory:

- the committed document record contains the content hash, byte count, MIME
  type, object locator, and storage state;
- storage state is reported, never assumed: an object held only in the local
  directory is `local`, and the audit says so on every record that carries it;
- no claim needed for a live build may depend on an object whose only known
  state is `missing`;
- migration must consume existing `.cache/` objects before attempting network
  retrieval;
- an object is garbage-collected only when no document, claim, snapshot, or
  audit record references it and the removal is separately reviewed.

### 6.1 Document record

Every `documents.jsonl` record requires:

```jsonc
{
  "document_id": "sha256:<64 hex characters>",
  "sha256": "<64 hex characters>",
  "bytes": 123456,
  "mime_type": "application/pdf",
  "title": "...",
  "publisher": "...",
  "published_on": "2026-08-20",
  "reporting_dates": ["2026-06-30"],
  "authority_tier": "T1",
  "authority_domains": ["issuer.financials"],
  "source_ids": [{"scheme": "asx_document_key", "value": "..."}],
  "url_aliases": [{"url": "https://...", "first_seen": "...", "last_verified": "..."}],
  "object_locator": "...",
  "storage_state": "durable",
  "verified": {"issuer": true, "title": true, "dates": true, "bytes": true},
  "supersedes": []
}
```

The content hash identifies bytes, not the abstract publication. If the same
publication exists in materially different formats, link its records through a
shared publisher identifier and record the equivalence check.

### 6.2 Claim record

Every claim requires:

- a stable `claim_id` and normalized claim key;
- typed value, reported value, units, currency, range, and evidence state where
  applicable;
- source `document_id`, page/table/note or image locator, and a short verbatim
  evidence excerpt where licensing permits;
- authority tier and domain copied from the source for audit;
- publication and as-of dates kept separately;
- state, decision reason, reviewer or producing tool, and timestamps;
- for derivations, ordered dependency claim IDs, formula, rounding, and output
  unit;
- supersession links rather than in-place replacement.

A document-level citation without a page, table, note, section, or image
locator is incomplete for a new or changed claim.

### 6.3 Availability record

Availability is evidence about retrieval, not evidence for a company field.
Each attempt records the document or search target, channel, checked time,
result, HTTP/content diagnosis, and next permissible retry time. Standard
states are `AVAILABLE_LOCAL`, `AVAILABLE_DURABLE`, `LINK_DEAD`, `BLOCKED`,
`MISSING_OBJECT`, and `NOT_PUBLISHED`.

`NOT_PUBLISHED` requires an exhaustive official index over the relevant issuer
and date interval. A five-item feed, search-engine result, or failed URL cannot
establish it. A dead alias never invalidates an archived artifact.

Every negative outcome books a `next_retry_at`, and the interval is longer where
the failure looks permanent. The date is binding on the acquisition queue: a
URL whose date has not arrived is deferred whatever its tier, and only an
explicit operator override fetches it early. The override is recorded in the
fetch reason, so a run that ignored the schedule says so on every record it
produced. A later success releases the block — availability records are events,
and the most recent one for an address is what holds.

### 6.4 Local object storage

The store's objects are held in `knowledge/objects/`, which is gitignored, and
their derivatives in `knowledge/extracted/`, which is also gitignored. This is
an **accepted arrangement**, not an open defect: the repository has no LFS
remote, and the objects run to well over a gigabyte of publisher PDFs whose
licences do not invite redistribution.

What that costs must be stated wherever the store is described rather than
discovered by whoever clones it next: **the store is not portable.** A fresh
clone gets every record, every view and the entire decision trail, and can
re-run every check that does not need the bytes. It cannot re-hash an object it
does not have, so `audit --deep` and any re-extraction require re-acquiring the
objects on that machine.

What makes that re-acquisition possible is committed, and is therefore not
optional:

- the SHA-256 of every artifact, so a re-fetched copy can be checked against
  the record rather than trusted;
- the full retrieval URL for every alias, unshortened and unredacted, plus the
  channel it was reached through — for an exchange document, the index sweep,
  the `displayAnnouncement` address and the resolved PDF address;
- every publisher and exchange identifier, with the basis it was obtained on;
- the registries themselves — `documents.jsonl`, `availability.jsonl`,
  `claims.jsonl`, `quarantine.jsonl` — and the generated views.

An artifact with no committed route back to it is the one thing this
arrangement cannot tolerate, because the bytes are the only copy. Where a route
is inferred rather than tested, it is recorded as inferred and the record does
not claim the authority the route would confer (§4.2).

Promoting the store to `durable` — Git LFS or an external object store — remains
a separate, reviewed decision. Until it is taken, no record may describe itself
as `durable`, and the audit must keep reporting the gap on every one of them.

## 7. Required operating workflow

### 7.1 Before network access

1. Query active claims for the subject and predicate.
2. Check scope, as-of date, freshness rule, and projection status.
3. Resolve the cited artifact by content hash and inspect the stored extraction
   or page image.
4. Search document aliases and publisher identifiers for an already archived
   newer artifact.
5. Only then create an acquisition task with its missing claim and fetch reason.

During migration, perform the same checks across `data/companies.json`,
`data/SOURCES.md`, `tools/sources.json`, and `.cache/`. The ignored cache is a
migration source, not a canonical authority.

### 7.2 When acquiring a document

1. Discover through the highest-quality available channel described in
   `docs/primary-source-operations.md`.
2. Download once and save raw bytes before transformation.
3. Sniff content, compute the full SHA-256 hash, and deduplicate by hash.
4. Verify issuer, title, publication date, reporting date, units, currency,
   attribution basis, and relevant table or note inside the artifact.
5. Assign authority tier and domains. Record all stable publisher identifiers
   and working URL aliases.
6. Produce deterministic extraction derivatives. Render and inspect scanned or
   image-based tables.
7. Register claims separately; acquisition alone accepts no value.

### 7.3 When registering or changing a claim

1. Normalize its key and compare all existing claims at every tier.
2. Run the precedence algorithm in §5.1.
3. If accepted, link the exact evidence locator and update the generated active
   view.
4. If blocked by higher authority, create only a quarantine pointer and search
   for a correction or newer high-tier document.
5. If the controlling tier is unresolved, omit/degrade/reject according to the
   existing field rule. Never descend the hierarchy for a more convenient
   answer.
6. Recompute dependent derivations and then regenerate the `data/` projection.

### 7.4 Refresh and maintenance

Freshness is predicate-specific. Annual resource statements, quarterly
guidance, corporate actions, statutory rules, and point-in-time market data do
not share a global "latest" date. Their refresh rules belong with the consuming
field or methodology.

Refreshes are event-driven where possible. A failed refresh preserves the last
valid dated claim and changes only its availability or freshness state; it does
not create a zero, carry-forward, or invented update. Repeated failures honor
`next_retry_at` rather than causing a fetch storm.

## 8. Validation and write controls

The completed KB tooling must provide one auditable write path and a strict
audit command. Direct hand-editing of active views or generated projections is
forbidden after cutover.

The strict audit must fail on:

- a document without a valid hash, authority tier/domain, verification state,
  or resolvable required object;
- two active claims for one key;
- an active lower-tier claim incompatible with a higher-tier claim;
- an accepted claim without an exact evidence locator;
- a derivation with missing, stale, unresolved, or circular dependencies;
- a projected field whose claim is absent, non-projectable, or different from
  the projected value after declared conversion and rounding;
- a superseded document or claim remaining active;
- a URL overwrite that changed bytes without creating a new document record.

`tools/provenance.py` and `tools/gaps.py` remain required until the KB audit
subsumes their checks. The production engine continues to read only `data/`;
the KB migration must not alter weights merely by changing storage.

## 9. Migration from the current repository

The migration is additive and must not refetch material already held locally.

| Current asset | KB destination | Rule |
|---|---|---|
| `.cache/` raw files and extractions | content-addressed objects and `extracted/` | Hash and deduplicate first; never refetch just to obtain a cleaner filename |
| `data/companies.json` `documents` maps | `documents.jsonl` plus temporary compatibility keys | Merge identical artifacts and retain every URL alias |
| `data/companies.json` fields | `claims.jsonl` and generated projection | Backfill exact evidence locators; do not change values during storage-only migration |
| `data/SOURCES.md` | decision, supersession, and quarantine history | Preserve rationale; narrative alternatives do not become active claims |
| `tools/sources.json` | acquisition queue/view | A requested URL or expected field is a lead, not evidence |
| `docs/primary-source-operations.md` | retrieval operations | Retrieval order does not set factual authority |

Migration order:

1. Inventory and hash every cache object and every document URL already cited.
2. Deduplicate artifacts, attach aliases, and mark uncertain legacy metadata for
   review without demoting existing production data solely because migration is
   incomplete.
3. Backfill claims in risk order: live weight/gate inputs, rejected-name gate
   inputs, reporting-only fields, then historical research.
4. Add precedence and projection audits before allowing KB-generated writes to
   `data/companies.json`.
5. Cut over only after a replay proves identical production inputs and outputs,
   except for separately reviewed factual corrections.

Until cutover, this document is immediately binding for authority, conflicts,
lookup-before-fetch, raw-artifact retention, and amendment behavior. The target
file layout becomes mandatory as its tooling is implemented. Existing records
are grandfathered for migration; any source or claim newly added or materially
changed after this document's effective date must satisfy these rules or carry
an explicit migration exception.

## 10. Acceptance criteria

The implementation is complete only when all of these are demonstrated:

1. The same filing fetched from two URLs produces one artifact and two aliases.
2. A dead publisher URL does not prevent inspection of an accepted claim.
3. A repeated research task finds the existing claim and artifact without
   network access.
4. A T3 value conflicting with T1 is blocked from claims, derivations, summaries,
   and `data/`, with a quarantine pointer to the controlling claim.
5. A same-tier unresolved conflict produces no active value.
6. An explicit correction supersedes the prior claim while preserving both
   artifacts and the historical decision.
7. Superseding an input marks dependent derivations stale until recomputed.
8. Every projected company field resolves to one active claim and exact
   evidence location.
9. Storage migration alone reproduces the pre-migration index inputs and build
   outputs.

## 11. Amendments

This design may be changed only by an explicit amendment in this section and
corresponding updates to `AGENTS.md` and any affected schema or tooling. An
implementation shortcut, narrative research note, or agent instruction cannot
quietly weaken an invariant or authority tier.

- **23 August 2026 — initial adoption.** Established durable content-addressed
  evidence, domain-specific authority tiers, a hard higher-authority conflict
  barrier, scoped claims, quarantine, and an additive migration path from the
  existing URL cache and per-company provenance.
- **23 August 2026 — storage arrangement and route rules (§4.1, §4.2, §6, §6.3,
  §6.4).** Recorded on the second acceptance review of the first load. A
  gitignored local object directory is an explicitly permitted backend, with
  non-portability stated wherever the store is described and the material
  needed to re-acquire the bytes — hashes, full retrieval URLs and channels,
  publisher identifiers, and the registries — committed. An artifact with no
  tested retrieval route is unclassified rather than filed under a subject read
  out of its own text. Equivalence between two renderings of one document is
  decided page for page on extracted text, allowing for extraction order and
  an exchange watermark. An approved market-data provider's session carries its
  origin on the artifact, because no address can restore it. Booked
  `next_retry_at` dates bind the acquisition queue unless explicitly
  overridden, and the override is recorded.
