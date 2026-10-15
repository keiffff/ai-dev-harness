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

For requested fresh-task behavioral verification, identify the currently installed agent runtime and reuse its supported entrypoint and existing configuration. A broken PATH launcher does not establish that the runtime is unavailable: inspect existing installation sources, including the running desktop app's bundled executable, before introducing another CLI. Do not substitute a new installation or an unauthenticated isolated configuration for the working environment. A missing prerequisite created by the verification setup is a setup fault to diagnose, not evidence that the original work is blocked. Preserve the prohibition on bypassing actual authentication or permission failures.

## Telemetry Ownership

Identify the existing emission owner before adding logging, exception capture or metrics. Lower layers may attach unique context and rethrow; avoid capturing the same exception twice. Local telemetry needs an operator-visible event or information unavailable to the owner.

## Completion

Keep a short current-task note of the original requested outcomes, required unfinished work, observed evidence and authority boundaries, rather than only the completed implementation steps. Bind it to the current task with `python3 ~/.codex/hooks/runtime-contract-context.py --task-note <actual-note-path>` and update and rebind it when those facts change, including completion, stop, cancellation or replacement. Do not carry closed-task unfinished work into a later request. The existing runtime hook restores this task's own note after resume or compaction and when it changes; it is context, not a permission grant or a Stop gate. Return to the maintained outcomes after an intervening question and before finalizing. Contract-delivery checks do not satisfy a requested fresh-task behavioral check.

Before the final response, reconcile the original requested outcomes with actual results, including unfinished work from before an intervening question or correction. Answer that question without treating it as cancellation. If relevant authorized work remains executable, perform it in the same turn; listing it as unverified or future work does not complete the request. A failed improvement check is evidence for the next diagnosis and change, not a reason to end at the comparison report. Respect an explicit user stop or scope replacement, and do not infer new Git, cloud or messaging authority from task continuity.

Report the implemented behavior, checks that passed or remain blocked, review result and material residual risk. Distinguish which parts of the original problem are verified as resolved from those still unresolved or unverified. Passing tests or removing an unsound implementation alone does not establish that the original problem is resolved. For consequential unresolved assumptions, use `codex-doubt-review`; ordinary implementation choices stay with main.
