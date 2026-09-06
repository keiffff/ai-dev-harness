---
name: codex-interface-review
description: Check API, schema, persisted-data and state contracts before design or implementation review, including omission, compatibility and ownership.
---

# Codex Interface Review

Use these criteria for an interface decision or a changed contract. Main can apply them directly; an independent reviewer uses the same criteria when `codex-doubt-review` is warranted. A second agent solely for I/F review is not required.

## Contract Criteria

- Inputs and outputs: allowed values, validation, errors, defaults, and the distinct meanings of missing, null, empty and unknown values.
- Consumers: who can send/read each shape, and what they can observe after an operation.
- State: allowed transitions, ordering, duplicate handling, idempotency and recovery where relevant.
- Ownership: which layer validates, normalizes, persists and exposes the value; check the producer as well as the consumer.
- Compatibility: name affected existing records, readers and released clients. Add compatibility only for an established need, not an unreleased intermediate design.
- Naming: use repository vocabulary and a concrete referent; flag ambiguity when it changes behavior or consumer interpretation.
- Synchronization: generated schemas/artifacts and contract tests reflect the accepted shape.

When OpenSpec applies, compare these contracts across proposal, design, spec and implementation. Surface an unapproved change or missing contract decision under AGENTS.md. Routine implementation choices within the accepted contract stay with main.

For findings, use `codex-code-review`'s reporting contract when producing a code review. A design-only answer should state the proposed contract, evidence and unresolved decisions without forcing a diff-review format.
