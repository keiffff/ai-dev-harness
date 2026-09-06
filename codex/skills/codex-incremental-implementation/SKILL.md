---
name: codex-incremental-implementation
description: Implement multi-file changes while preserving existing owners, observable contracts, focused tests, and completion evidence.
---

# Codex Incremental Implementation

Implement complete, reviewable behavior increments. AGENTS.md owns authority and contract-change gates; OpenSpec owns accepted artifacts when applicable.

## Preserve Existing Owners

Before adding a parallel CLI, parser, mapper, data path, output convention or abstraction, trace the existing entrypoint through data access, transformation, output and tests. Reuse its owner unless the requested behavior requires a distinct responsibility, invariant or external boundary.

Keep adjacent cleanup and hypothetical compatibility out of the change. Prefer existing state and idempotency for repeated requests; use one lifecycle unless a concrete operation, billing rule or contract requires different retention. New flags, artifacts, exit codes, dependencies and shared-code changes need an accepted requirement or established repository pattern.

## Verification And Test Scope

Tests should protect an accepted observable contract or a known regression, at the boundary that owns it. Use response shapes, persisted state, UI behavior, messages, artifacts or operator-visible results as evidence.

- Add coverage where a distinct transformation or failure mode needs it; avoid duplicating a contract already covered above that layer.
- Mock interactions and negative assertions are appropriate when the interaction or absence is itself the contract: idempotency, authorization, chargeable calls, queue publish, metrics or a known regression.
- Remove tests of concepts deliberately removed by the accepted design. Preserve existing contract tests unless the user has authorized changing that behavior; investigate failures before changing expectations.
- An unnecessary test, helper or defensive branch is a reason to revise the implementation, not a new user approval gate.

Run checks that can reveal new information after the current increment. Broaden or repeat successful checks only after changes, failures or an unresolved risk justify it. Report environment blockers without borrowing another worktree to fake verification. A production outcome needs production evidence.

## Telemetry Ownership

Identify the existing emission owner before adding logging, exception capture or metrics. Lower layers may attach unique context and rethrow; avoid capturing the same exception twice. Local telemetry needs an operator-visible event or information unavailable to the owner.

## Completion

Report the implemented behavior, checks that passed or remain blocked, review result and material residual risk. For consequential unresolved assumptions, use `codex-doubt-review`; ordinary implementation choices stay with main.
