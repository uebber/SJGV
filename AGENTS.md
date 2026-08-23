# Repository guidance

## Project

SJGV is a rules-based ASX gold-equity index. The production engine is
`build_index.py`; `nav_model.py` is reporting-only. Inputs and their provenance
live under `data/`, while `tools/` contains audits, sourcing helpers,
sensitivity analysis, and snapshot management.

Read the relevant source of truth before changing behavior:

- `index-methodology.md` is the binding index methodology and amendment record.
- `source-knowledge-base.md` is the binding design for source retention,
  authority tiers, factual claims, and conflict resolution.
- `data/README.md` defines the data schema and sourcing protocol.
- `README.md` explains the investment objective, construction, and repository.
- `docs/` records supporting research and accepted or pending design decisions.

Do not infer current weights or statistics from narrative prose. Generated
outputs and the latest dated snapshot are authoritative for a particular build.

## Non-negotiable rules

1. **Derive or fail.** Never invent or silently default a sourceable input. A
   value may be sourced, arithmetically derived from sourced values with the
   formula recorded, or entered as a conservative bound that is explicitly
   labelled. Otherwise omit it and let the engine report, degrade, or reject it.
2. Every field in `data/companies.json` must cite a document key. Use a
   publisher-provided range only; do not turn analyst judgment into a range.
3. Preserve category definitions, attribution, units, reporting dates, and the
   distinction between P&P, M&I non-reserve, and Inferred ounces. Read the
   field-specific rules in `data/README.md` before editing company data.
4. Every `data/config.json` parameter must name its consumer in
   `build_index.CONFIG_PARAMS`. A documented but unread parameter is a defect.
5. Reporting models and risk statistics must not affect index weights unless
   the binding methodology is deliberately amended as part of the same change.
6. `tools/extract.py` proposes candidates only. It must never write accepted
   values into `data/companies.json` automatically.
7. Do not fabricate market inputs when IBKR TWS/Gateway is unavailable. Keep
   fallback provenance and degraded/untested states explicit.

## Fetching regulatory and issuer information

Apply `source-knowledge-base.md` before discovery or network access. The store
is `knowledge/` and `tools/kb.py` is its only write path — never hand-edit a
registry or a generated view. A claim you establish by reading a source is
registered with `kb.py register-claim`, which demands the complete §6.2 record
(archived artifact, exact locator, verbatim excerpt, as-of kept apart from the
publication date), runs the §5.1 precedence sequence for the claim key, and
refuses rather than guesses. The legacy migration exceptions grandfather the
unchanged projection only; they do not apply to anything you register. Look up the retained artifact there first
(`kb.py plan` lists what is missing in tier order; `views/by_ticker.json`,
`views/url_aliases.json`, `views/source_ids.json` and `views/asx_lodgements.json`
answer most questions without a request), then during migration search
`data/companies.json`, `data/SOURCES.md`, `tools/sources.json`, and `.cache/`.
`docs/knowledge-store-initialization-2026-08-23.md` records what the store
already holds, the corrections applied to it, and its open gaps. The objects are
gitignored by decision, so a fresh clone holds every record but no bytes.
Re-fetch only for a missing admissible source, an expired field-specific
freshness rule, a relevant event, a failed integrity check, or an explicit
refresh request. A URL is an access route, not a document identity.

Seven rules the store enforces, which also govern how you write about a source:

- **A filename is not provenance.** What a local file is called records what
  somebody believed they were saving. Never turn it into a URL, an alias, or a
  verified identifier; archive with `kb.py ingest-file` and let
  `kb.py verify-inferred` test the address it implies.
- **A file with no tested route is unclassified.** A ticker read out of a
  document says what it is about, not who served it, so it earns no tier.
  `kb.py route-local` tests a bare artifact against the archived exchange index
  and records what came back; until then the record stays T4 and says so.
- **An index proves a negative only over the interval it swept.** A sweep taken
  today cannot show that nothing will be lodged in December. Quote the
  `coverage` block, not the calendar year.
- **A URL can serve different bytes later.** Each set is its own artifact
  version, kept and ordered; `latest` in a view means most recently retrieved,
  not correct.
- **A title is the publisher's name for the document.** Your reading of it goes
  in a note, a claim, or a field's source note — never in `title`. Not even a
  short tail after a dash: "— Note 17 Borrowings" is where you looked, not what
  the document is called.
- **A market session is primary for its own observations and nothing else.** It
  can never be re-fetched, so it carries its provenance in `market_session`;
  the tickers it quotes are its subject, not its publisher.
- **A refusal books a retry date.** `plan` and `acquire` honour it; do not work
  around a booked date by fetching by hand. `acquire --retry-now` is the
  override and records itself in the fetch reason.

The authority tiers and conflict barrier in `source-knowledge-base.md` are
binding. A lower-tier assertion that conflicts with an applicable higher-tier
claim must not enter `data/companies.json`, a derivation, or an accepted
summary. Retain the raw artifact for audit, quarantine the candidate, and seek
a correction or newer source at the controlling tier. An exact verified mirror
inherits the original document's tier; its host does not determine authority.

Codex CLI has no interactive browser. Use its hosted live search for discovery,
then download and inspect the exact primary document before accepting a value:

```sh
codex --search "Find the latest primary ASX/issuer filing for <company and field>"
curl -L --fail --show-error --user-agent 'Mozilla/5.0' '<document-url>' -o /tmp/<document>.pdf
pdftotext -layout /tmp/<document>.pdf -
```

Hosted search and shell networking are separate. `--search` may work while
`curl` is sandboxed; approve the narrowly scoped download when prompted, or
download the filing outside Codex and provide its local path. Keep temporary
downloads under `/tmp`, not in the repository. Browser access is not required.

Treat search results, snippets, aggregators, and news reports as discovery aids,
not evidence. Prefer, in order:

1. the issuer's lodged ASX/AIM/TSX announcement or annual/interim report;
2. an official regulator, exchange, government, or statutory publication;
3. an issuer-hosted investor-relations copy of the same document;
4. an identical filing mirror when the issuer link is dead or bot-protected;
5. a secondary source only when no primary source is available, explicitly
   labelled as secondary with the primary-source gap recorded.

For every fetched document, verify the issuer, title, publication date,
reporting/as-of date, units, currency, attribution basis, and relevant table or
note in the document itself. Do not source a field from a search snippet or an
AI summary. For PDFs, use `pdftotext -layout`; if tables are scanned or published
as images, inspect the rendered pages or images rather than treating missing
extracted text as a zero. If a site blocks automated retrieval, use an official
exchange copy or an identical document mirror; do not bypass access controls.

Record the document in the company's `documents` map and cite its key from each
accepted field. Preserve the direct URL and document date, state any arithmetic
derivation in the field note, and label bounds or unresolved evidence
explicitly. Reconcile extracted figures to the source totals where possible and
run `tools/provenance.py` and `tools/gaps.py` after company-data changes. An
unavailable or ambiguous load-bearing amount stays absent; it is never inferred
from a spend rate, search result, or narrative description.

## Working and validation

Use the repository interpreter (`.venv/bin/python`, currently Python 3.12).
There is no dependency manifest, and the tests are plain `unittest` with no
runner dependency. `build_index.py` requires `ib_insync` and normally a local
TWS/IB Gateway session.

Useful checks:

```sh
.venv/bin/python -m compileall -q build_index.py nav_model.py tools
.venv/bin/python -m unittest discover -s tests -t .
.venv/bin/python tools/gaps.py
.venv/bin/python tools/provenance.py
.venv/bin/python tools/config_audit.py --strict
.venv/bin/python tools/kb.py audit --strict        # evidence plane; --deep re-hashes
```

Run `tools/config_audit.py --strict` after any configuration change and after a
fresh build so it can compare declared consumers with observed reads. A normal
build is:

```sh
.venv/bin/python build_index.py
.venv/bin/python build_index.py 1000000 --commission 0.1
```

Builds rewrite ignored root artifacts: `weights.csv`, `weights.json`,
`basket.csv`, `basket.json`, `market_bundle.json`, and `market_bars.csv`. The
ignore patterns for these files must remain root-anchored because copies inside
`snapshots/` are tracked. After an actual rebalance, freeze the successful build
with `tools/snapshot.py`; do not create a snapshot for an ordinary code check.

Keep changes narrow and preserve source notes and historical rationale unless
the underlying methodology decision is explicitly superseded.
