# Primary-source retrieval operations

This note covers access mechanics only. Authority, conflict resolution and
claim registration are binding in [`../source-knowledge-base.md`](../source-knowledge-base.md).

## Before any request

Run `tools/kb.py plan` and inspect the knowledge-store views. Re-fetch only for
a missing admissible source, an expired field-specific freshness rule, a
relevant event, failed integrity, or an explicit refresh. A booked refusal date
must be honoured unless `acquire --retry-now` is deliberately used.

During migration, also search `data/companies.json`, `data/SOURCES.md`,
`tools/sources.json` and `.cache/`. A filename or old local path is a discovery
hint, not provenance.

## Preferred channel order

1. lodged exchange or regulator document;
2. official government or statutory publication;
3. issuer-hosted copy of the same document;
4. verified identical mirror;
5. explicitly labelled secondary source, with the primary gap recorded.

Search results and snippets discover documents but do not establish claims.
Download and inspect the exact artifact. For PDFs, use `pdftotext -layout` and
render image-based pages when extraction is incomplete.

## ASX retrieval

Use the ASX issuer announcement feed for recent lodgements and the ASX calendar-
year announcement index for older records. The index establishes only the
period it actually covers. Resolve the exchange document key to the lodged PDF;
do not infer a URL from a local filename.

Archive through `tools/kb.py` only. If a bare local artifact has no tested
route, use `kb.py route-local`; it remains unclassified until the route or exact
mirror is verified.

## Verification before acceptance

Verify inside the artifact:

- issuer and publisher;
- publisher's exact title;
- publication and reporting/as-of dates separately;
- units, currency and attribution basis;
- exact table, page, note or paragraph; and
- whether the document is the original, a lodged copy or a verified mirror.

Register every accepted claim with exact locator, verbatim excerpt and complete
§6.2 record. Never use the document title to store analysis or a locator note.

## Common failure modes

- A changing URL can serve different bytes; retain each version by hash.
- A ticker found in a document identifies subject, not publisher or tier.
- Scanned tables need visual inspection; absent extracted text is not zero.
- Bot protection is not permission to bypass access controls; use an official
  exchange copy or verified mirror.
- A market session is primary only for its own observations.
- A refusal creates a recorded retry date rather than an invitation to fetch by
  hand.

After projection changes, run `tools/provenance.py`, `tools/gaps.py` and the
strict knowledge-store audit.
