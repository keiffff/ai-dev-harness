---
name: codex-doubt-review
description: Challenge non-trivial decisions when correctness depends on assumptions, boundaries, ordering, idempotency, migrations, or production risk.
---

# Codex Doubt Review

Use this skill to doubt important decisions, not every keystroke. Keep the loop bounded and lightweight.

## Trigger

Apply when a decision:
- changes branching logic or state transitions
- crosses module, service, API, or persistence boundaries
- infers causality, provenance, freshness, completion, or recovery from time, ordering, status, existence, naming, or another indirect observation
- may leave durable or user-visible state after a primary-path failure, with no confirmed retrigger or recovery path
- asserts an invariant tests/types do not fully prove
- introduces a new label, state, condition, event, boolean, or summary term that may hide an unclear referent
- affects production, data integrity, security, or migration safety
- feels "obviously fine" but would be costly if wrong

Do not use for mechanical renames, formatting, obvious one-line fixes, or pure command execution.

## Bounded Doubt Loop

1. State the claim in 1-2 sentences.
2. Extract the smallest artifact and contract to review.
   - Artifact: the concrete item under review, such as a diff hunk, function, schema, state transition, OpenSpec requirement, or prose section. Do not pass the full session story when a smaller artifact is enough.
   - Contract: the promise the artifact must satisfy, such as existing behavior, OpenSpec text, API shape, persisted data compatibility, user instruction, or test intent.
   - When the concern crosses a boundary, include only the producer representation, the decision point, the failure state, and the retrigger or recovery path needed to test the claim.
3. Ask for adversarial findings against the artifact and contract: what could violate the contract, what assumption is hidden, what edge case is missed.
   - For new labels or names, ask whether the word was chosen before the referent was fixed. Check whether it mixes condition, state, event, value, record, purpose, or means.
4. Reconcile findings against the artifact and contract before acting:
   - actionable: a real issue that should change the artifact.
   - contract gap: the contract is unclear or incomplete; stop and surface the missing decision instead of guessing.
   - trade-off: the issue is real, but accepting it may be intentional; make the trade-off explicit.
   - noise: the reviewer misread the contract or raised something outside this artifact.
   Limit the reviewer to at most three contract-breaking conditions, hidden assumptions, or non-recovering failure paths. Exclude style, naming, and general refactoring suggestions.
5. Fix actionable issues or surface the trade-off.
6. Stop after one useful cycle unless new substantive issues require another. Never loop more than three times.

## Reviewer Choice

- For broad architecture or maintainability, use `claude-strategic-review`.
- For consequential repo-local diff review, explicitly route a Codex subagent to `gpt-5.6-terra` with `high` reasoning when available. If that routing cannot be verified, keep the review in the main agent instead of silently accepting the scout default.
- For simple behavioral claims, a failing/regression test can be the doubt mechanism.

Do not require cross-model review every time. Offer it only when the cost is justified by risk or the user asks.

## Output

Keep user-facing output short:
- claim checked
- important findings adopted/rejected
- remaining risk or verification gap

If the available evidence cannot resolve a contract-bearing assumption, recommend an ANDON. Do not fill the gap with an unrequested identifier, fallback, retry, compatibility path, or test.

Do not include internal debate in PR body unless it matters to reviewer risk.
