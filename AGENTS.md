# Repository guidance

## Project

SJGV is a rules-based ASX gold-equity index. The production engine is
`build_index.py`; `nav_model.py` is reporting-only. Inputs and their provenance
live under `data/`, while `tools/` contains audits, sourcing helpers,
sensitivity analysis, and snapshot management.

Read the relevant source of truth before changing behavior:

- `index-methodology.md` is the binding index methodology and amendment record.
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
There is no dependency manifest or automated test suite. `build_index.py`
requires `ib_insync` and normally a local TWS/IB Gateway session.

Useful checks:

```sh
.venv/bin/python -m compileall -q build_index.py nav_model.py tools
.venv/bin/python tools/gaps.py
.venv/bin/python tools/provenance.py
.venv/bin/python tools/config_audit.py --strict
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
