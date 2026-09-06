---
name: codex-decision-doc
description: Write decision records that preserve rationale, inherited constraints, rejected alternatives, compatibility and open decisions in the project format.
---

# Codex Decision Doc

Use this for ADRs, RFCs and design rationale. OpenSpec owns its artifacts; PRs and ordinary prose use `codex-writing`.

## Content Contract

Separate inherited constraints, the current decision, unresolved choices and out-of-scope work. Explain the operational problem before naming implementation parts. Preserve why the decision is reasonable and what would otherwise be lost from code or chat history.

Use the user's template or nearby project format. When none exists, include only the useful parts of: summary, background/problem, decision and rationale, rejected alternatives, compatibility, risks/verification, non-goals and open questions. A short decision needs no mandatory eleven-section document.

- Every alternative needs a rejection reason; every compatibility claim needs affected existing data, clients, APIs, tests or operations.
- Add fields, IDs, artifacts, versions, fallback or recovery machinery only for an accepted requirement or concrete operational evidence.
- Describe inherited decisions as background, not as work decided in this change. A discovered adjacent issue does not become accepted scope.
- Ask for missing decision context; do not manufacture questions about states excluded by the contract.
- Use exact values and contract text where needed. Tables compare common axes; Mermaid can express relationships, state or order. Use `codex-frontend-ui` for a derived interactive view only when useful, keeping this document as the source.

Write in Japanese unless requested otherwise; preserve project headings. For a prose defect, use `codex-writing`'s editing contract. For decision phrasing examples, consult [style](references/style.md) as needed.
