# knowledge/ — source-priority knowledge base

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
