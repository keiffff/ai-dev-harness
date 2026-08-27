---
name: codex-interface-review
description: Review changes to APIs, schemas, persisted data, public types, state contracts, and module or cross-layer boundaries.
---

# Codex Interface Review

Use this skill before committing to an interface shape. Good interfaces are explicit, additive where possible, and hard to misuse.

## Review Axes

- Contract: typed input/output, allowed values, defaults, nullability, errors.
- Boundary: validation at system edges, trust internal typed data, parse external responses.
- Compatibility: additive changes preferred; breaking behavior must be intentional.
- Observability: every observable behavior can become a contract.
- State: transitions, ordering, idempotency, duplicate handling, rollback behavior.
- Naming: match existing repo vocabulary and avoid ambiguous terms.
- Referent before label: every new field, enum value, state, condition, event, and boolean name must have a concrete referent and one role. If a name mixes condition/state/event/value/record/purpose/means, request a rename or split.
- Tests: contract tests or reducer/usecase tests cover the new observable behavior.

## Questions To Answer

- What exactly is the consumer allowed to send or call?
- What exactly can the consumer observe afterward?
- What happens for empty, invalid, duplicate, old, missing, or unknown values?
- Which layer owns validation and normalization?
- Is this a new concept or an extension of an existing one?
- What concrete thing does each new name point to, and is it a condition, state, event, value, record, purpose, or means?
- Does a generated artifact need to stay in sync?

## OpenSpec Fit

For OpenSpec work, check that proposal/design/spec agree on:
- I/F names and enum values
- operation-specific behavior
- target and non-target objects
- persistence and migration behavior
- unresolved questions

If implementation pressure requires changing the contract, stop and ask before editing.

## Claude Sidecar

Use `claude-strategic-review` when the interface has long-term maintenance risk, affects multiple teams, or could be hard to migrate later. Claude provides review material only; Codex makes the final decision.
