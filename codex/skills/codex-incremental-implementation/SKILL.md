---
name: codex-incremental-implementation
description: Implement multi-file changes while preserving existing owners, observable contracts, focused tests, and completion evidence.
---

# Codex Incremental Implementation

Implement complete, reviewable behavior increments. AGENTS.md owns authority and contract-change gates; OpenSpec owns accepted artifacts when applicable.

Identify the faulty behavior, intended observable outcome, and what must remain unchanged from the request and existing contracts. Keep each change tied to that outcome; omit changes whose necessity cannot be explained. These are implementation decision criteria, not a requirement for a separate document, checklist, or approval step.

## Preserve Existing Owners

Before adding a parallel CLI, parser, mapper, data path, output convention or abstraction, trace the existing entrypoint through data access, transformation, output and tests. Reuse its owner unless the requested behavior requires a distinct responsibility, invariant or external boundary.

Keep adjacent cleanup and hypothetical compatibility out of the change. Prefer existing state and idempotency for repeated requests; use one lifecycle unless a concrete operation, billing rule or contract requires different retention. New flags, artifacts, exit codes, dependencies and shared-code changes need an accepted requirement or established repository pattern.

## Verification And Test Scope

Tests should protect an accepted observable contract or a known regression, at the boundary that owns it. Use response shapes, persisted state, UI behavior, messages, artifacts or operator-visible results as evidence.

A concrete incident is reproduction evidence, not automatically a general contract. Do not promote incidental log formatting or example-specific steps into assumed interfaces. Tests built on the same unverified assumption as the implementation do not establish that assumption's correctness; ground expected behavior in the requested outcome and independently established contracts or observations.

- Add coverage where a distinct transformation or failure mode needs it; avoid duplicating a contract already covered above that layer.
- Mock interactions and negative assertions are appropriate when the interaction or absence is itself the contract: idempotency, authorization, chargeable calls, queue publish, metrics or a known regression.
- Remove tests of concepts deliberately removed by the accepted design. Preserve existing contract tests unless the user has authorized changing that behavior; investigate failures before changing expectations.
- An unnecessary test, helper or defensive branch is a reason to revise the implementation, not a new user approval gate.

Run checks that can reveal new information after the current increment. Broaden or repeat successful checks only after changes, failures or an unresolved risk justify it. Report environment blockers without borrowing another worktree to fake verification. A production outcome needs production evidence.

When fresh-task behavioral verification is requested, run actual work in a new task; hook delivery and unit tests are not substitutes. Use the existing installed runtime and normal configuration. Diagnose setup faults separately from target faults; do not bypass actual authentication or permission errors.

## Telemetry Ownership

Identify the existing emission owner before adding logging, exception capture or metrics. Lower layers may attach unique context and rethrow; avoid capturing the same exception twice. Local telemetry needs an operator-visible event or information unavailable to the owner.

## Completion

AGENTS.md owns task continuity and the task-note entrypoint; the runtime hook owns storage and restoration. Check the original requested outcomes against actual artifacts and execution evidence. Continue executable required work after questions or failed checks, and respect explicit stops. Report resolved behavior and remaining uncertainty; passing a subtest or delivering instructions does not establish the whole outcome.
