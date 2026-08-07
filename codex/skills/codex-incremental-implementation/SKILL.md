---
name: codex-incremental-implementation
description: Implement changes in focused, verifiable slices. Use for multi-file changes, OpenSpec task execution, refactors, or features where Codex should avoid large speculative edits and keep verification tied to each meaningful increment.
---

# Codex Incremental Implementation

Use thin slices. Keep each slice small enough to review and verify. This skill does not grant commit or push permission.

## Slice Loop

For each slice:
1. Define the smallest complete behavior or refactor step.
2. Read the files and one local pattern needed for that step.
3. Edit only the files required for the slice.
4. Run the narrowest meaningful verification.
5. Review the diff for scope creep before continuing.

## Existing Path Reuse Gate

Before the first edit for a CLI, migration, data extraction/import/export, or another path that resembles existing behavior:

1. Trace the current path through entrypoint, argument parsing, data access, mapping, output, and tests where each exists.
2. Identify which existing owners the change will reuse and what behavior genuinely has no current owner.
3. Start from the existing path instead of creating a parallel parser, mapper, repository path, output convention, or test structure.

- Treat changes to shared product code for a one-off CLI or migration as scope expansion. Stop unless the accepted behavior requires that shared change.
- Do not add a flag, output artifact, exit code, parser, mapper, or helper unless it is required by the user, an accepted artifact, an existing contract, or a concrete boundary the current owner cannot handle.
- If the planned code duplicates an existing owner, stop and revise the slice before editing.

## Scope Rules

- Prefer existing helpers, architecture, and tests over new abstractions.
- Do not clean up adjacent code unless required for the requested behavior.
- Do not mix unrelated refactor and feature behavior in the same slice.
- Do not add dependencies unless the repo already has the pattern or the user approved.
- Do not treat "small diff" as safe if it changes shared contracts or external behavior.
- Treat existing tests, response shapes, domain conversions, and null/undefined/field-omission behavior as contract candidates until proven otherwise.
- Do not delete, weaken, or rewrite an existing test expectation just because it fails after your change. First identify the contract it protected and whether the user approved changing that contract.
- Do not add domain fallbacks, default values, synthesized data, or empty-object fills in medical, accounting, auth, permission, persistence, or external-integration logic unless an existing contract or explicit user decision requires it.
- Do not invent domain terms in code, test names, or PR prose. Use repository terminology or literal field names.
- Before adding a helper, wrapper, adapter, facade, mapper, or policy function, ask whether it owns responsibility, centralizes an invariant, or hides a real boundary. If not, inline it or change the existing owner directly.
- Do not add a new abstraction only to avoid touching the real owner, make a diff look smaller, make a test pass, rename a value, or prepare for hypothetical future reuse.
- A new abstraction should follow an existing repo pattern, remove real duplication across at least two callers, centralize a domain invariant, hide an external boundary, or be a clearly named structural tidy needed before the behavior change.
- Start from the simplest contract that satisfies the requested behavior. Do not add rate limits, cooldowns, extra TTL differences, fallback branches, backward compatibility layers, retry branches, duplicate storage, or alias fields unless a repository contract, explicit user decision, or concrete operational risk requires them.
- When duplicate requests, retries, or repeated UI actions are involved, first check whether idempotency, returning an existing in-flight result, or reusing existing state solves the case before adding a new limiter or error path.
- If retention, expiry, or cleanup is involved, prefer one lifecycle unless different lifetimes protect a concrete user-visible, operational, billing, or compliance requirement.

## Test Discipline

- Add tests for observable contracts, meaningful regressions, and risk-bearing state transitions. Do not add tests only because a new helper, wrapper, field, branch, or intermediate status exists.
- Before adding a test, name the behavior it protects and who would observe the regression: API caller, UI user, persisted data reader, worker retry path, billing/metrics consumer, or operator.
- Place the test at the boundary that owns the contract: persistence and data mapping at the repository/domain boundary, response and validation behavior at the API boundary, retry and publish behavior at the worker/external boundary, and dry-run or progress behavior at the operator-facing CLI boundary.
- Do not duplicate the same contract across layers unless each layer has a distinct transformation or failure mode that the higher-level test cannot localize.
- Do not test implementation plumbing when a higher-level behavior test already fails if that plumbing breaks.
- Do not add tests that freeze speculative defensive paths, temporary architecture, unused fields, or cleanup mechanisms that are not part of the accepted contract.
- If a new test mainly asserts that a mock method was called, check whether the same contract can be covered by a persisted state, response shape, rendered UI, queued message, or output artifact.
- Do not add tests whose only signal is interaction between mocks. A mock-interaction test is acceptable only when the interaction itself is the boundary contract, such as publishing a queue message, calling an external client once for idempotency, avoiding an unauthorized write, or emitting billing/metrics events.
- Keep tests aligned with the chosen design. When the design removes a limiter, sweeper, compatibility path, or extra API, remove or avoid tests for that removed concept instead of preserving them as safety coverage.
- Do not keep removed behavior alive as a negative test such as "does not call X", "does not create Y", or "does not use Z" unless X/Y/Z is an accepted public contract, cost guard, security boundary, or previously observed regression. A deleted implementation path should usually disappear from tests too.
- If the only reason for a test is "we removed this, so make sure it stays removed", replace it with a positive contract test for the behavior that remains.

## Telemetry Ownership

- Before adding exception capture, logging, or metrics, identify which existing layer owns emission.
- When a global handler captures an exception, lower layers should attach only the context they uniquely know and rethrow without capturing the same exception again.
- Do not add a catch-and-log block that only repeats information already emitted by the owner.
- Add local telemetry only when it exposes an operator-visible event, boundary result, billing signal, or context unavailable to the existing owner.

## ANDON Conditions

Stop and ask before editing further when a slice appears to require:
- changing optional vs nullable vs required behavior, field omission, empty string, empty array, or empty object semantics;
- adding a fallback/default/synthesized value in domain logic;
- deleting or weakening an existing test;
- changing a schema/OpenAPI contract to match a convenient implementation rather than a confirmed API contract;
- replacing an existing domain conversion with a new interpretation whose business meaning is not established in the repository.
- adding a helper/wrapper whose ownership, invariant, or boundary is unclear.
- adding a limiter, cooldown, fallback, backward compatibility path, retry branch, duplicate persistence path, or divergent retention period whose necessity has not been established.
- adding a test whose protected contract cannot be stated without referring to an internal helper, mock call, unused field, or speculative defensive path.
- adding or keeping a negative test for removed behavior instead of testing the remaining accepted behavior.
- adding a mock-interaction test where the interaction is not itself a boundary contract.

## OpenSpec Integration

When implementing from OpenSpec, load `codex-openspec-workflow` first. That skill owns artifact discovery, current CLI instructions, compatibility decisions, spec review, and sidecar review. This skill owns only the incremental implementation loop after those inputs are fixed.

## Verification

- Run only checks that can reveal new information after the current slice.
- Do not rerun the same successful command without intervening changes.
- If verification is blocked by environment setup, state the blocked check and why.
- Do not use symlink/copy hacks from another worktree to fake verification.
- When success is observable only after release, separate pre-release verification from the production signal, comparison basis, and observation window. Do not report the production outcome as verified before that observation occurs.

## Completion Evidence

Before reporting implementation complete, identify the evidence in this shape:
- Implemented: the requested behavior, task, or contract now covered by the diff.
- Verified: the narrowest meaningful checks that passed, or the exact blocked checks and why.
- Reviewed: scope creep, spec-outside behavior, and residual risk were checked.

For OpenSpec work, each sidecar review finding must land in one of three states: implemented, added to spec/tasks, or rejected with a short reason.

## Git Boundary

Do not commit during the slice loop unless the latest user message explicitly asks for commit. Do not push unless the latest user message explicitly asks for push or PR branch update.
