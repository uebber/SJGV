# Documentation register

SJGV keeps current rules, rationale, evidence and operations separate. Earlier
proposals, replays and remediation journals remain recoverable from Git but are
not part of the active documentation set.

| Document | Authority | Purpose |
|---|---|---|
| [`../index-methodology.md`](../index-methodology.md) | Binding | Complete current v2.0 construction |
| [`../data/README.md`](../data/README.md) | Binding schema | Company-data fields and sourcing rules |
| [`../source-knowledge-base.md`](../source-knowledge-base.md) | Binding evidence design | Authority, retention, conflicts and claim workflow |
| [`../README.md`](../README.md) | Orientation | Objective, construction summary and repository map |
| [`investment-case.md`](investment-case.md) | Current rationale | Why v2.0 fits the investment mandate; evidence and limits |
| [`capital-resilience.md`](capital-resilience.md) | Current rationale | Gate 2 economic logic and limitations |
| [`guidance-delivery.md`](guidance-delivery.md) | Current rationale | Delivery evidence and treatment logic |
| [`validation.md`](validation.md) | Release evidence | Frozen v2.0 checks, metrics and reproduction boundary |
| [`primary-source-operations.md`](primary-source-operations.md) | Operations | Current primary-document retrieval mechanics |
| [`knowledge-store-status.md`](knowledge-store-status.md) | Operations | Implemented evidence controls and live limitations |

Machine-readable evidence remains outside narrative documentation:

- `data/guidance_delivery.json` — active delivery ratings;
- `knowledge/` — document and claim ledgers;
- `snapshots/2026-08-24-v2.0/` — frozen release inputs and outputs; and
- generated root outputs — latest build only, not historical authority.
