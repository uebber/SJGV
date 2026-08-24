# Knowledge-store status

The store under `knowledge/` is the evidence plane for source artifacts and
claim records. Its binding design and operating rules are in
[`../source-knowledge-base.md`](../source-knowledge-base.md); this note records
only the present implementation boundary.

## Implemented controls

- content-addressed document identity and version retention;
- separate document, claim and availability records;
- authority tiers scoped by factual domain;
- exact locators, verbatim excerpts and distinct publication/as-of dates;
- deterministic precedence and conflict barriers;
- explicit accepted, quarantined, stale and superseded states;
- market-session provenance;
- refusal retry dates honoured by planning and acquisition;
- generated views by ticker, URL alias, source ID and ASX lodgement; and
- strict audit, with optional deep object re-hashing.

The only supported write path is `tools/kb.py`. Registry files and generated
views must not be hand-edited. Content-addressed objects are intentionally
gitignored; a fresh clone therefore contains the records but may need the bytes
re-acquired through their recorded routes.

## Current limitations

Some retained objects may be unavailable locally, some mirrors remain
unverified, and some legacy records are non-projectable. These are evidence
states, not permission to promote a lower-tier claim. `kb.py plan` is the live
source for current gaps and retry eligibility; this note does not freeze counts
that change with every ingestion.

Projection from the knowledge plane into `data/companies.json` remains a
reviewed action. A newly registered claim does not silently update a live index
input, especially when it could change a gate, denominator or weight.

## Checks

```sh
.venv/bin/python tools/kb.py audit --strict
.venv/bin/python tools/kb.py audit --strict --deep
.venv/bin/python tools/kb.py plan
```

Use the deep audit when object integrity itself is in question. Use the normal
strict audit for routine repository validation.
