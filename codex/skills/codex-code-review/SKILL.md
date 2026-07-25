---
name: codex-code-review
description: Review code changes with a bug-first stance. Use for "review" requests, before reporting implementation complete, after AI-generated code, or when checking a diff for correctness, tests, architecture, security, performance, and scope control.
---

# Codex Code Review

Use a code-review stance: findings first, ordered by severity, grounded in file/line references when possible.

## Review Order

1. Understand the intended behavior and contract.
2. Review tests first: do they cover behavior and regressions?
3. Review implementation for correctness, edge cases, state, and error paths.
4. Check architecture: ownership boundaries, shared modules, duplicate helpers, unnecessary abstraction.
5. Check security and data handling: input validation, secrets, auth, untrusted external data.
6. Check performance only where relevant: N+1, unbounded loops, render churn, large payloads.
7. Compare verification run against risk.

## Finding Style

- Lead with real bugs and regressions.
- Avoid long nit lists.
- Distinguish required fixes from optional suggestions.
- If no issues are found, say so and name residual test/risk gaps.
- For structural issues, propose the move: extract helper, remove branch, use existing policy, split module, make boundary explicit.

## Scope Guard

- Do not ask for unrelated cleanup in a review.
- Do not accept "we can fix later" when the current change introduces the issue.
- Do not rubber-stamp AI-generated code because tests pass.
- Do not include implementation journey or local setup noise in PR prose.

## Test Scope Review

When reviewing AI-generated tests, check whether each new test protects an accepted observable contract. Flag tests that mainly:

- assert internal helper calls, mock choreography, private fields, or intermediate status names without proving user/API/worker behavior;
- rely only on interactions between mocks, with no response, persisted state, rendered UI, queue message, output artifact, external boundary, billing event, or metrics event as the asserted contract;
- lock in speculative defensive branches, unused fallback paths, sweepers, limiters, retry paths, or compatibility paths that the design did not accept;
- keep removed behavior alive through negative assertions such as "does not call X", "does not create Y", or "does not use Z" when X/Y/Z is no longer part of the design;
- duplicate coverage already provided by a higher-level behavior test;
- preserve tests for concepts removed by the current design;
- make future refactors harder while failing to catch a real regression.

Prefer keeping tests that cover response contracts, persisted state transitions, idempotency, authorization, external message/artifact boundaries, UI states, and known failure modes. If a test is redundant, recommend removing or merging it rather than weakening production code to satisfy it.

Negative assertions are useful only when the absence is itself the contract: no duplicate external call, no unauthorized write, no extra chargeable operation, no user-visible stale state, or no regression from a known incident. Otherwise, prefer a positive test for the remaining behavior.

Mock-interaction tests are useful only when the interaction is the boundary contract: queue publish, external API call count for idempotency, forbidden write prevention, billing/metrics emission, or another observable side effect. Otherwise, prefer asserting the behavior after the interaction rather than the mock choreography itself.

## OpenSpec Review

When OpenSpec artifacts exist, compare implementation against design/spec:
- implemented
- missing
- spec-outside behavior added
- tests missing
- unverified residual risk

Use `claude-strategic-review` as a sidecar when AGENTS.md calls for post-implementation OpenSpec review.
