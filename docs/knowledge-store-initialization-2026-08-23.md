# Knowledge-store initialization — 23 August 2026

**Purpose:** record how `knowledge/` was populated, what it now holds, what it
deliberately does not hold, and the findings the load surfaced. The binding
design is `source-knowledge-base.md`; this is the run record for its first
load, not an amendment to it.

The first pass initialized the **evidence plane** (§3) — artifacts, hashes,
aliases, authority tiers and availability. Section 9 records the subsequent
knowledge-plane backfill. No value in `data/` was written or re-derived, so the
pre-migration index inputs remain unchanged by construction (§10.9).

## 1. What the store holds

Counts are as at the close of the corrections in §7 and §8, which are part of
this load and not a later change to it.

| | |
|---|---|
| Documents | 480 immutable artifacts, 1.43 GB (376 PDFs, 80 HTML, 23 JSON, 1 CSV) |
| Authority | T1 351 · T2 117 · T3 4 · T4 8 |
| Lodgement-attested | 194 carry an exchange record of issuer, headline and lodgement date |
| Cited-URL coverage | 133 of the 146 URLs cited across `data/` and `tools/sources.json` |
| Exchange indexes | 29 sweeps over 17 tickers (11 closed years, 17 year-to-date), 2,477 lodgement rows, 1 superseded sweep retained |
| Multi-version publications | 46 — artifacts the publisher regenerated or re-rendered, each member checked and linked, none silently dropped |
| Local artifacts routed | 34 of the 36 bare `/tmp` files matched to an exchange index row and tested against it; 4 unrouted records remain T4 |
| Availability events | 693 — 629 `AVAILABLE_LOCAL`, 35 `LINK_DEAD`, 21 `BLOCKED`, 8 `MISSING_OBJECT`; 10 addresses carry a booked `next_retry_at` |
| Claims | 402 — 355 accepted, 3 provisional, 34 stale, 10 unresolved |
| Quarantine | 57 pointer-only records; no candidate values |

Tooling is `tools/kb.py`: `init`, `ingest-local`, `ingest-file`, `backfill-claims`,
`register-claim`, `ingest-market-session`, `plan`, `acquire`, `asx-index`,
`asx-acquire`, `route-local`, `verify-inferred`, `reverify`, `views`, `audit`.
It is the only sanctioned write path; `knowledge/` must not be hand-edited.
`register-claim` was added by the first research pass over this store and is
recorded in `docs/claim-resolution-pass-2026-08-23.md`; the counts in this
section are the state at the close of the load, not after that pass.

## 2. Order of the load — local first, then by tier

1. **Local before network (§2.1, §6).** 161 `.cache/` artifacts and 66 `/tmp`
   PDFs from the 21–22 August sourcing pass were hashed and archived without a
   single request. The `/tmp` set is the FY26 reporting-season evidence base
   behind `docs/gate2-capital-resilience-source-register-2026-08-22.md`; it had
   never been retained anywhere durable and would have been lost on reboot.
2. **T1 cited documents.** Exchange-lodged PDFs, ASX CDN documents, Commonwealth
   law, and state revenue-authority material.
3. **T1 exchange indexes.** The per-year announcement index for every ticker —
   the only unfiltered channel (the research API is capped at five items).
   Archived as artifacts, so an absence is checkable evidence over the interval
   the sweep actually covers: a whole calendar year for CY2025, the year to the
   retrieval date for CY2026.
4. **T1 lodged core pack.** 150 annual reports, Appendix 4E/4D filings,
   half-years, quarterlies, Appendix 5Bs, R&R statements and guidance releases,
   taken off the index for CY2026 across all 17 names and CY2025 for the eleven
   whose latest accounts are FY25.
5. **T2 then T3.** Issuer sites, IR-platform copies, mirrors, then attributed
   secondary sources.
6. **T4 not fetched.** Search snippets and unattributed aggregators stay in the
   acquisition queue as leads, never as evidence.

## 3. The design's own acceptance criteria, exercised

- **One artifact, several aliases (§10.1).** Capricorn's 6 July release is
  byte-identical at `capmetals.com.au` and `announcements.asx.com.au`: one
  record, two aliases, T1. 74 artifacts arrived by more than one route — a
  duplicate `/tmp` filename, a cache entry, an IR-platform URL with and without
  its API key — and merged rather than duplicating.
- **Mirror promotion (§4.2).** Eight `/tmp` copies whose lodged status could not
  be established were promoted to T1 when the exchange's own file hashed
  identically — Westgold's FY25 Appendix 4E and half-year financial report,
  Greatland's FY25 4E, and Pantoro's FY25 annual report, half-year and FY26
  result among them. Equivalence was established by bytes, not by trusting the
  host.
- **A filename is not provenance (§4.2, §7.2).** Fourteen artifacts arrived as
  bare `/tmp` files whose names implied an exchange address. The name is a lead:
  it says what the downloader believed they were saving. Each was fetched from
  the address it implied and the result recorded — five served exactly those
  bytes, nine served a regenerated copy extracting to identical text, none was
  refuted. T1 now rests on those fetches, not on the filenames (§7.1).
- **A dead URL no longer blocks inspection (§10.2).** Westgold's issuer link to
  the 2025 MRE now 404s; the statement itself is archived from the exchange and
  remains readable. The dead alias is recorded, not deleted.
- **Negatives are provable (§6.3).** The 2,477 indexed rows are unfiltered, so
  "nothing was lodged" is now a checkable claim over a stated interval rather
  than an inference from a five-item window. The interval is the one that was
  actually swept: for the seventeen current-year indexes that is 1 January to
  the retrieval date, not the calendar year (§7.2).
- **Repeat research is free (§10.3).** `kb.py plan` resolves 133 of 146 cited
  URLs to held bytes with no network access.

## 4. Findings that need a decision

1. **Two share counts have moved since the cited as-of.** Against the exchange's
   own key-statistics service on 23 August: **EVN 2,041.823 m vs the 2,031.090 m
   in `data/companies.json` (+0.53%)** and **BGL 1,491.502 m vs 1,490.660 m
   (+0.06%)**. The other fifteen agree to within rounding. Both feed market
   capitalisation and the Gate 1 cap-weighted variant. Nothing was changed here:
   the cited claims carry a 17 August as-of, a new count is a new claim at a new
   as-of, and revising weights is a rebalance decision, not a storage migration.
2. **The 17 August key-statistics bytes are unrecoverable.** They were never
   archived and the endpoint is live. Today's responses are held as *new dated
   observations*, explicitly labelled as not evidencing the cited as-of. Every
   future point-in-time market observation must be archived at the moment it is
   read.
3. **The FY26 reporting gap is unchanged as of 23 August.** The exhaustive index
   shows no lodgement after 21 August for any of the fourteen producer-path
   names — 22–23 August is a weekend. CMM, GGP, WGX, BGL, OBM, CYL, PNR and BC8
   still have no FY26 accounts, exactly as the 22 August register recorded, and
   now on complete-index evidence. A re-sweep from 26 August is worth running.
4. **Two sources refuse automated retrieval and have no substitute yet.**
   `imf.org` (Fiscal Monitor, T2 macro-fiscal) returns 403; `pbo.gov.au` returns
   no bytes at all over either HTTP version. Both are recorded with
   `next_retry_at: 2026-08-30` and are not live gate inputs.
5. **Four blocked or dead sources were replaced at a higher tier**, with the
   substitution recorded in `availability.jsonl`:
   - the AustLII reproduction of the Queensland royalty regulation (T3) →
     **Mineral Resources (Royalty) Regulation 2025 (Qld), SL 2025 No. 108**, the
     official consolidated instrument (T1);
   - Earth Resources Victoria's blocked royalty information sheet → the
     **authorised Mineral Industries Regulations 2019 (Vic), SR 48/2019 v004**
     (T1), which states the 2·75% of net market value rate and the 2,500 oz
     annual exemption directly — confirming the `AU-VIC` B1 record from the
     controlling instrument rather than from agency guidance;
   - a Market Index aggregator copy of Astral's resource announcement (T3) → the
     lodged announcement of 21 April 2026 (T1);
   - Westgold's dead issuer link → the exchange-hosted 2025 MRE (T1).
6. **Four issuer "announcements" navigation pages now 404** (NST, OBM, BC8,
   PNR). They were never documents; the archived exchange index supersedes them
   as a channel.

## 5. Known gaps, stated rather than hidden

- **Objects are local-only, and this is the accepted arrangement.**
  `knowledge/objects/` and `knowledge/extracted/` hold 1.43 GB and are
  gitignored; the repository has no LFS remote. This is now written into the
  binding design as a permitted backend rather than tolerated in practice:
  `source-knowledge-base.md` §6.4 states the arrangement, its condition and its
  cost. The registries, the views and the whole decision trail are committed —
  the bytes are not. Every record carries `storage_state: "local"` and the audit
  reports the gap on all 480 rather than hiding it. The consequence, stated
  rather than discovered later: **the store is not portable.** A fresh clone can
  read every record and re-run every check that does not need the bytes, but
  `audit --deep` and any re-extraction require re-acquiring the objects on that
  machine. What makes that possible is committed and is the condition of the
  arrangement: every content hash, every full retrieval URL with the channel it
  was reached through, every publisher identifier with its basis, and the
  registries themselves. Promoting the store to `durable` — Git LFS or an
  external object store — remains a separate, reviewed decision.
- **238 documents carry at least one open review flag beyond durability**
  (194 dates, 107 issuer, 76 mirror-equivalence, 41 routed by equivalence rather
  than by their own bytes, 37 titles, 22 volatile-endpoint observations,
  4 retrieval-route-unresolved). These are honest: a
  flag is set only where a script actually established the fact. Documents taken
  off the exchange index are verified for issuer, headline and lodgement date by
  the exchange record itself; legacy `.cache` artifacts largely are not.
  `knowledge/views/review_queue.json` is the work list. The 37 missing titles
  are records whose artifact carries no title of its own; a description written
  here would be ours, not the publisher's, so the field stays empty and flagged
  (§7.4).
- **Four local artifacts still have no retrieval route** and stay T4. Two —
  `lr4.pdf` (ASX Listing Rules chapter 4) and `p3.pdf` (an Appendix 4E) — name
  no issuer, so the per-ticker index gives nothing to test them against. The
  other two, saved as `bgl-5b-jun26.pdf` and `ggp-ar-fy25.pdf`, are not PDFs at
  all: they are a `displayAnnouncement` interstitial and an issuer web page,
  captured under a `.pdf` name by a download that failed silently in the
  21–22 August pass. Their records now say so (§8.2). The documents they were
  meant to be are held from the exchange in any case.
- **The claim store is initialized but cutover has not occurred.** The backfill
  covers every current company field and execution-capital project amount, plus
  the newer archived key-statistics observations. The production engine still
  reads `data/`. Exact locators and atomized derivation dependencies that the
  legacy schema did not retain are explicit migration exceptions and remain a
  review queue, not inferred facts.
- **`tools/provenance.py` and `tools/gaps.py` remain required.** The KB audit
  covers documents and objects only; it does not yet subsume their checks.

## 6. Reproducing or extending the load

```sh
.venv/bin/python tools/kb.py ingest-local          # local artifacts, no network
.venv/bin/python tools/kb.py plan --verbose        # what is missing, tier order
.venv/bin/python tools/kb.py acquire --tier T1     # highest tier first
.venv/bin/python tools/kb.py asx-index --year 2026 # lodgement index, year to date
.venv/bin/python tools/kb.py asx-acquire --ticker CMM --match 'appendix 4e|annual'
.venv/bin/python tools/kb.py route-local           # test bare files against the index
.venv/bin/python tools/kb.py verify-inferred       # test filename-derived provenance
.venv/bin/python tools/kb.py reverify               # recompute evidence metadata
.venv/bin/python tools/kb.py backfill-claims        # claims + pointer-only quarantine
.venv/bin/python tools/kb.py views                  # evidence + knowledge views
.venv/bin/python tools/kb.py audit --strict --warnings
```

`acquire` will not re-request an address whose booked `next_retry_at` has not
arrived; `acquire --retry-now` overrides that and records the override in the
fetch reason of every artifact the run produces.

A document fetched outside the tool is archived with its retrieval URL by
`kb.py ingest-file --path <file> --url <url>`, which keeps the sandbox-friendly
workflow in `AGENTS.md` inside the one auditable write path.

`reverify` is idempotent and safe to run at any time: it recomputes provenance,
titles, subjects, tiers, equivalence and review flags from the artifacts
themselves and writes byte-identical output on a store that is already correct.
It is also the repair path — a store loaded under earlier rules is brought up to
the current ones by running it.

## 7. Corrections applied after the acceptance review

The first load was reviewed on 23 August and six defects were returned. All six
are fixed in `tools/kb.py`, so the defect cannot recur, and the existing store
was repaired through `reverify` rather than by hand. `audit --strict --deep` is
clean; run against the pre-correction registry the extended audit raises 85
errors, which is the check working.

### 7.1 A filename no longer assigns authority

`tmp_provenance()` was building an ASX CDN URL out of a `/tmp` filename and
recording it as a retrieval alias. `ingest_bytes()` then read that alias as
evidence of an exchange origin, and nine records reached T1 on the strength of
what someone had named a file.

Filename-derived metadata now lands in `inferred_provenance` — the identifier,
the address it implies, and how it could be settled — and never in
`url_aliases` or a verified identifier. `source_ids` entries carry a `basis` and
a `verified` flag; only `retrieval-url` and `exchange-index-row` count, and only
a verified exchange identifier, an alias with a retrieval event behind it, or a
recorded equivalence can support T1.

The fourteen affected artifacts were then resolved against the publisher with
`kb.py verify-inferred`: five WebLink files were served byte-identically at the
implied address (confirmed), nine ASX CDN files came back as regenerated copies
extracting to identical text (equivalent, with the fetched artifact archived and
carrying the verified identifier), and none was refuted. The inferences were
right — but they are now checked rather than assumed, which is the difference
the review was asking for.

### 7.2 Index coverage is the interval actually swept

A sweep of the current year was recorded as covering 1 January to 31 December
and described as a "full calendar-year index". A sweep taken in August cannot
evidence what will be lodged in November. Every index document and store entry
now carries a `coverage` block — `covered_from`, `covered_to` (the retrieval
date for a year in progress), `complete`, and a `completeness` sentence that
states the admissible interval for a `NOT_PUBLISHED` finding and says plainly
that the rest of the year is not covered. Seventeen of the 28 sweeps are
year-to-date; the eleven CY2025 sweeps are complete years and say so.

### 7.3 URL and identifier version history is preserved

Two URLs resolved to two artifacts each while `url_aliases.json` mapped each URL
to one document, and seven ASX document keys named two artifacts each. Nothing
was lost from the store, but the view chose a version silently.

`views/url_aliases.json` and the new `views/source_ids.json` now list every
version in retrieval order under each key, with `latest` meaning most recently
retrieved and nothing more. Where groups overlap — a documentKey group and the
CDN URL it resolves to are not the same set — they are merged into one
publication, so an artifact gets one answer about what it is a version of. Each
member records an `equivalence` finding with its basis: identical extracted text
means the publisher regenerated the file (the ASX CDN does this per request, and
the exchange index page carries a cache-buster), too little text to compare
means unproven and needs a visual read, and differing text under one exchange
identifier is an error the audit refuses. The 23 August re-sweep of NST's 2026
index, which had overwritten its predecessor in the lodgement store, is
re-attached as a superseded sweep: a `NOT_PUBLISHED` finding made before the
re-sweep rested on the earlier artifact and has to remain checkable.

### 7.4 Titles hold publisher metadata, analysis is kept separately

Fifteen records carried an analytical note in `title`, one of them 1,613
characters, because `legacy_index()` had been offering `note`, `for` and
`source` fields as titles and because `data/companies.json` records many
documents as "Publisher headline — what we concluded from reading it".

Legacy notes are no longer title candidates. A legacy title is split: the
headline stays, and a tail that quotes figures, stacks clauses or runs long goes
to `legacy.notes` with the `data/` path it came from — 108 notes were carried
over, none discarded. Titles now resolve, in order, from the exchange's own
headline, the legacy headline, PDF metadata, the HTML `<title>`, the
publisher's own filename, or the title of an artifact established as the same
publication. Where none of those exists the field stays empty and flagged;
52 records are in that state. Exchange headlines are also HTML-unescaped, so
"Appendix 4E &amp; ..." is no longer stored as the exchange's markup.

### 7.5 The audit detects all four defect classes

`audit --strict` now fails on an unsupported T1 promotion (including an
exchange-host alias with no retrieval event behind it — the exact shape of the
nine records above), a coverage interval that runs into the future or past its
own retrieval or calls a partial sweep complete, a URL or exchange identifier
resolving to several artifacts with no recorded version relation, and a title
carrying analysis. `tests/test_kb_integrity.py` holds 22 tests over these rules,
each stating the defect it exists to prevent.

### 7.6 Views and counts regenerated

`views/` was rebuilt and §1 restated: at the close of this round the store held
438 documents, 273 at T1, 607 availability events. The earlier report had said
427 / 264 / 577 against a store of 429 / 266 / 579 — the counts had been taken
before the last ingest. §1 now carries the figures after §8.

## 8. Corrections applied after the second review

The corrected load was reviewed again and six further items were returned. Each
is fixed in `tools/kb.py` so the defect cannot recur, and the existing store was
repaired by running the tool rather than by hand.

### 8.1 A market session keeps its own authority

`assign_tier()` had no branch for an approved market-data provider, and the
provider was recorded only in `tier_basis` — a field that same function
overwrites. With no URL alias to read, both session artifacts fell through to
the local-artifact branch, where the tickers the session QUOTES were taken for
its publisher: the IBKR bundle and its bar series were filed as **T2
`issuer.NST`**, an unverified Northern Star document. The ingest set them to T1
and the next `reverify` took it away.

Provenance that cannot be re-derived from an address now lives on the record.
`market_session` holds the provider, the role (session bundle or bar series),
the session clock, the engine commit and the title; `APPROVED_MARKET_PROVIDERS`
maps the provider to its tier and domain. `assign_tier()` settles it before
anything alias-derived, `resolve_title()` restores the recorded title, and
`verify_document()` reads the session record instead of grepping a JSON file for
"ASX:NST". `ingest-market-session` and `reverify` share one path
(`apply_market_session`), so they cannot drift apart again, and sessions
archived before the block existed are reconstructed from their acquisition
record. Both artifacts are T1 `market.observation` and stay there across
repeated reverifies; `audit_promotion()` asks the provider registry, so a record
that merely names the basis is refused.

The bar series was also recorded as `text/html`, because the sniffer fell back
to a filename with no extension it recognised. It is `text/csv`, and its text
derivative is no longer the output of an HTML stripper.

### 8.2 The 36 unrouted local artifacts, resolved against the exchange

The 36 `/tmp` PDFs with no retrieval route had been classified **T2** on a
ticker inferred from their own text. That is the same unsupported promotion as a
filename-derived tier, one rung lower: what a document is ABOUT is not evidence
of who served it. Two changes:

1. **The fallback is now T4.** An artifact with no tested route is
   `local-artifact-no-route`, `unclassified`, and its `publisher` is cleared —
   including where the discarded rule had already written the ticker there.
2. **`kb.py route-local` earns a route.** For each bare artifact it proposes
   index rows from the archived sweep, scored on page count, the distance
   between the lodgement date and the PDF's own creation date, and whether the
   headline's words appear in the document. A proposal is then TESTED: resolve
   the row through `displayAnnouncement.do`, fetch what the exchange serves —
   or compare against the exchange copy already held, which is where most of
   these resolved without a request — and compare.

Of the 36: **2 are byte-identical** to what the exchange serves (the address
becomes a genuine alias, the `asx_ids_id` is verified from the index row, and
the record is T1 lodged); **32 are the same document differently rendered** (the
fetched artifact carries the verified identifier and the full URL, the local
record carries the route, the equivalence and an identifier explicitly marked as
naming the equivalent artifact and not these bytes, and reaches T1 by
equivalence); **4 remain unrouted at T4**, with what was tried recorded on them.
Every routed record carries the index sweep, the `displayAnnouncement` address
and the resolved PDF address in full. 42 exchange artifacts were fetched in the
process and archived in their own right, which is where the store's growth from
438 to 480 documents comes from.

Comparing the extractions needed correcting too. Two distributors of one lodged
PDF do not produce one extraction: the CDN re-stamps through Markit, the
announcements host through OpenPDF, and `pdftotext -layout` then reads the two
layouts in different orders, so a paragraph and the sideways "For personal use
only" stamp swap places. Both copies carry the issuer's own CreationDate.
`same_publication()` therefore compares page for page — the same number of
pages, and on each page the same words in the same numbers — allowing only
fragments of that stamp to differ, and it states in the equivalence basis what
it compared. (Character equality had also been failing on long documents for a
duller reason: the comparison read a 400,000-character prefix, and two
217-page reports cut at the same offset diverge everywhere after the first
difference.)

### 8.3 Short analytical suffixes are out of titles

Long analytical titles had been moved to `legacy.notes`; short ones after a dash
had not — "— Note 17 Revolving Credit Facility, Note 6 Cash", "— the exchange's
own figure", "— FY27 Group guidance table and FY27 KCGM guidance slide". The
length test could not catch them without also rejecting real ASX headlines like
"Appendix 4E - revised".

So the tail is read rather than measured. It is analysis when it points INTO the
document (a note number, a table, a slide), when it hinges on a subordinating
word ("following...", "replacing...", "as observed"), when it opens mid-thought
in lower case with three or more words, or when it stacks clauses. It is a title
when it is a noun phrase the publisher would write: "Correction", "December
2025", "Maiden Ore Reserve". A title taken from the artifact itself — an
exchange headline, PDF metadata, an HTML `<title>` — is never split at all: its
punctuation is the publisher's, and splitting it would invent an analytical note
nobody wrote. `audit --strict` fails on an analytical suffix in any title that
did not come from the publisher, and the store now has none. The 29 index sweeps
carry `title_source: index sweep record`, which says plainly that the name is
ours.

### 8.4 A refusal now books a retry date, and the date binds

`availability()` wrote `next_retry_at=None if state == "LINK_DEAD" else None` —
always null. Nothing recorded a retry date and nothing honoured one, so every
`acquire` run re-requested the same blocked hosts: the fetch storm §7.4 exists to
prevent.

Every negative outcome now books a date (BLOCKED +7 days, MISSING_OBJECT +3,
LINK_DEAD +30). `plan` marks any queued URL whose date has not arrived as
deferred and prints how many are held back; `acquire` skips them — including
under `--include-deferred`, which means "fetch the leads too", not "ignore what
the host told us". `--retry-now` is the explicit override and is written into
the fetch reason of every record the run produces. A later success releases the
block, because availability records are events and the most recent one for an
address is what holds. Re-running the eight outstanding cited URLs confirmed all
eight still refuse; the queue now holds 10 addresses back rather than asking
again, and a second `acquire` fetched nothing.

### 8.5 The storage arrangement is in the binding design

`source-knowledge-base.md` required a durable blob backend and said a local
ignored cache "is not `durable` or `portable`", while the store ran on exactly
that. The gap was reported honestly in this note but the design still forbade
the arrangement in force.

New §6.4 permits a gitignored local object directory explicitly, states the
non-portability plainly, and makes the arrangement conditional on what has to
stay committed: content hashes, full retrieval URLs with their channel,
publisher identifiers with their basis, and the registries and views. §6 now
requires storage state to be reported rather than assumed, §4.1 and §4.2 carry
the market-session and tested-route rules, §6.3 carries the retry rule, and §11
records the amendment.

### 8.6 Checks

`tests/test_kb_integrity.py` holds 51 tests (73 across the suite), including
regressions for each item above: the bundle and the bar series each surviving
repeated tier recomputation, a ticker never becoming a publisher, an inferred
subject not buying the issuer tier, the index-route identifier never being
marked verified, every analytical suffix in the review rejected while nine real
publisher headlines pass, and `acquire` refusing a booked date under
`--include-deferred` but fetching under `--retry-now`.

`reverify` → `views` → `audit --strict --deep` returns zero errors over 480
documents, and the fixed-market replay reproduces both the primary SJGV weights
and the Gate 1 cap-weighted variant exactly.

One review flag was also renamed. Nine artifacts settled by `verify-inferred`
were carrying `retrieval-route-inferred-not-recorded`, which described how their
route STARTED rather than that it had been fetched and compared; read down a
warning list it looked like nine holes in the store. What matters is whether the
route was tested, so those records now carry the same
`route-by-equivalence-not-these-bytes` label as the artifacts `route-local`
settled — 41 in total. The name that remains for an untested route is
`retrieval-route-untested`, and for a tested one that found nothing,
`retrieval-route-unresolved`.

## 9. Knowledge-plane backfill

`kb.py backfill-claims` now migrates the current company projection through the
sanctioned write path. It wrote 402 claims: 323 top-level company fields, 45
scoped execution-capital project claims, and 34 new point-in-time ASX
key-statistics observations. The state split is 355 `ACCEPTED`, 3
`PROVISIONAL`, 34 `STALE`, and 10 `UNRESOLVED`.

The 57 quarantine records are pointers only. Five point to explicitly withheld
unresolved candidates; the remainder point to legacy field notes that expressly
describe an earlier candidate as corrected, superseded, replaced or withdrawn.
No rejected value was copied into `quarantine.jsonl`.

The migration preserves two limitations rather than hiding them:

- 242 active legacy claims have only a document-level citation because the old
  field record did not retain a page, table, note, section or image locator;
  266 do not separate the fact's as-of date from the publication date; and 68
  legacy derivations do not atomize their source facts as dependency claims.
  In total 367 claims carry one or more explicit migration exceptions. These
  exceptions grandfather the unchanged legacy projection only. A new or
  materially changed claim must satisfy the complete §6.2 record.
- The 17 August ASX key-statistics responses were not archived. The 34 projected
  share-count and average-volume assertions are therefore retained as `STALE`
  history, linked to 34 accepted observations from the archived 23 August
  responses. The new observations are deliberately not projected outside a
  reviewed rebalance. `audit --strict --projection` consequently reports those
  34 fields as the exact cutover blockers; ordinary `audit --strict` is clean.

One legacy secondary citation was unavailable: AUC's approvals boolean pointed
to a Kalkine page that was not fetched. The backfill resolves the same adverse
boolean to the held, lodged 13 July 2026 quarterly, PDF page 6, “Permitting and
Approvals”, where Ausgold says the Works Approval and EPA assessment remained in
progress. This upgrades the claim evidence without changing the projected
value or the pre-cutover company record.

The command is idempotent: a second run produced byte-identical
`claims.jsonl` and `quarantine.jsonl`. Generated views now include
`claims_by_subject.json`, `active_claims.json`, and `quarantine.json`. The full
78-test suite, compile check, `tools/gaps.py`, `tools/provenance.py`,
`tools/config_audit.py --strict`, and `tools/kb.py audit --strict` pass.
