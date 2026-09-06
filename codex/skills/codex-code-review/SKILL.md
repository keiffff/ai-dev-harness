---
name: codex-code-review
description: Review changes against accepted behavior, prioritizing actionable regressions, test scope, and a complete copyable review body.
---

# Codex Code Review

Main owns the review judgment. This skill supplies review criteria; it does not require a separate agent for each criterion.

## Review Baseline

Read the accepted behavior, relevant diff, tests, and any explicitly rejected alternatives. Judge correctness, authorization/data handling, ownership, failure paths and performance where the change creates a concrete risk.

A finding needs an affected operation, a violated contract or evidenced failure, and a relevant location. Separate implementation defects from an accepted design decision worth revisiting. Reopen a rejected fallback, abstraction, compatibility path or test only with new evidence. Avoid speculative hardening and unrelated cleanup.

For changed API/schema/state/persistence contracts, use `codex-interface-review` for those criteria rather than duplicating them here.

## Test Scope

Check whether new tests protect observable behavior or a known regression. Prefer the boundary that owns the behavior. Internal helper calls, mock choreography, unused defensive paths and duplicate coverage are not independent reasons for tests.

Keep mock interactions or negative assertions when the interaction or absence is itself an accepted contract, such as no unauthorized write, duplicate charge, repeated external call, or stale user-visible state. Tests for an intentionally removed implementation concept may go with that concept; preserve tests of behavior still promised to consumers.

## Uncertain Boundary ANDON

When a consequential decision relies on indirect evidence such as time, ordering, status, existence or naming, inspect the smallest producer, representation, decision point, failure state and recovery path. If the contract remains unresolved, do not invent an identifier, fallback, retry, compatibility path or extra test as the presumed fix. Report the facts, missing decision and impact.

For a consequential repo-local change, use one bounded `codex-doubt-review` cycle when independent review can test the unresolved assumption. Include relevant interface criteria in that same review. Main reconciles findings and owns the ANDON decision.

## Copyable Review Output

Return findings in severity order with priority, file/line reference, trigger and impact. Distinguish required fixes from optional suggestions. Include the overall assessment and residual verification gaps; say explicitly when there are no findings.

Put the complete review body inside an outer four-backtick `markdown` fence. Inline comments and review cards may supplement it, but never replace or shorten the copyable review body.

For OpenSpec-governed work, also identify missing, spec-external, insufficiently tested or unverified behavior against the accepted artifacts. Apply any repository-required sidecar review and reconcile its findings.
