---
name: codex-code-review
description: Review behavior, interfaces and risk; use Claude for an independent challenge of substantive approaches and unnecessary complexity, then reconcile a complete review.
---

# Codex Code Review

Main owns the review judgment. This skill supplies review criteria; it does not require a separate agent for each criterion.

## Review Judgment

Establish intended behavior and constraints from requirements, callers and existing contracts before accepting the PR's explanation. Respect accepted decisions and rejected alternatives unless new evidence warrants reopening them. On re-review, check whether the original problem is resolved, not just whether the named handler exists. A missing diff limits regression attribution, not assessment of evidenced behavior.

### Review the approach with Claude

For a substantive full change review, use `claude-strategic-review` to independently challenge whether the approach serves the user's purpose, assigns responsibilities well and justifies its complexity. Codex retains concrete behavior/I/F tracing, likelihood/impact assessment and the final judgment. A wording edit or verification of an already established finding does not reopen this full review.

Give Claude the relevant user request, constraints and source evidence under its existing reviewer contract. Keep the proposed implementation separate from those requirements; do not make Codex's findings or approval the premise. Use the same bounded pass for overdefense, overengineering and viable existing mechanisms, rather than separate reviewers for each criterion.

Reconcile Claude's material claims against the actual contracts and code. Keep justified complexity; adopt a design finding only with concrete operating/maintenance cost and a feasible alternative preserving the purpose. Missing evidence stays a question. Report Claude's significant assessment separately from Codex's adoption or rejection and its reason, including material disagreements. Follow the strategic-review skill's existing execution and failure handling.

### Trace affected operations before deciding severity

Follow each affected operation from its actual entry through validation, state changes, persistence and the consumer that observes the result. Use `codex-interface-review` for changed API/schema/state/persistence contracts within this pass.

- At mutable-state boundaries, compare what was read or authorized with what the final write actually predicates on. Follow the values, identities and versions across awaits and transactions. Exercise the competing transitions already supported by the system: a state can return to its previous label with different contents or permissions. A transaction or a status check alone does not prove that the originally authorized operation is still valid. A supported concurrent transition is a system condition, not an invented user gesture sequence; do not require a production incident to recognize a demonstrated contract violation.
- At alternate entry/commit paths, check that accepted validation and authorization survive to stored values and readers. Where the change resolves references or filters a requested selection, trace the missing-reference and zero-result cases through persistence to the consumer. An intentionally empty selection and a nonempty selection whose references all disappeared need not mean the same thing; inspect what the reader does with the resulting empty value. Follow failures and actual recovery before claiming loss, disclosure or irrecoverable state.
- Check ownership and the solution itself: can an existing capability or supported standard mechanism satisfy the established contract with less conflicting state or custom machinery? A design finding needs a concrete failure or maintenance consequence and an evidenced feasible alternative, not a style preference.

Keep discovered defects separate from their disposition. Do not silently discard an evidenced contract failure because its exact frequency is unknown; decide how to report it below.

### Weigh likelihood and consequence

For each candidate, establish the actor's goal or exposed system condition, the route to the trigger, the violated contract and the actual consequence. Technically possible user actions do not establish a realistic combined workflow: explain why the goal leads to that order or timing, rather than restating a feature as a goal. A nearby defensive comment/check establishes mechanics, not a universal product requirement. Bypassing the PR's own guard alone does not establish harm.

Weigh occurrence likelihood/frequency together with affected scope, recurrence, harm and recoverability. Frequent small failures can accumulate; rare failures can have severe consequences. Use numbers only when supported; do not invent user counts, probabilities or urgency. Apply the repository's priority scale; a security or data-loss label alone does not imply its highest priority. Deliberate abuse, concurrent updates, network failures and retries are judged by their actual exposure and contract, not whether they resemble ordinary UI use.

Adopt a required finding when the supported path and consequence justify correction. Keep contrived or unexplained action combinations with unestablished harm as investigation candidates, not required fixes. Keep material unresolved contracts visible as questions without claiming a defect. Separate findings, optional improvements and questions. Retain the operation, evidence, consequence, location and reason for priority with adopted findings; no mandatory numeric scorecard. Avoid speculative hardening and unrelated cleanup.

## Test Scope

Use relevant tests as evidence of intended observable behavior. Before requiring a change, inspect tests encoding the exact disputed condition. If accepted artifacts or tests give competing contracts, establish which requirement controls; unresolved disagreement is a question, not a mandatory correction. Do not claim missing coverage without checking those conditions. Prefer tests at the owning boundary; helper calls, mock choreography, unused defensive paths and duplicate coverage are not independent reasons for tests.

Keep mock interactions or negative assertions when the interaction or absence is itself an accepted contract, such as no unauthorized write, duplicate charge, repeated external call, or stale user-visible state. Tests for an intentionally removed implementation concept may go with that concept; preserve tests of behavior still promised to consumers.

## Uncertain Boundary ANDON

When a consequential decision relies on indirect evidence such as time, ordering, status, existence or naming, inspect the smallest producer, representation, decision point, failure state and recovery path. If the contract remains unresolved, do not invent an identifier, fallback, retry, compatibility path or extra test as the presumed fix. Report the facts, missing decision and impact.

For a consequential repo-local change, use one bounded `codex-doubt-review` cycle when independent review can test the unresolved assumption. Include relevant interface criteria in that same review. Main reconciles findings and owns the ANDON decision.

## Copyable Review Output

Build each comment from the established finding or the user's accepted plain explanation, rather than reconstructing it from implementation names:

1. For behavior, state the actor’s purpose, evidenced trigger and resulting failure. For approach, state the requirement, unnecessary responsibility, concrete cost and feasible simplification. Explain why likelihood and impact justify the priority; introduce internal terms only when they explain the issue.
2. Copy the code location from the current established finding and attach its evidence, priority and required correction. Do not substitute a location from an older draft or claim it was rechecked. Keep an unverified reproduction unverified. A short title does not replace the explanation.
3. Order findings by severity and retain all requested findings. When changing the format, carry the accepted explanation into the comment; do not revert to an earlier technical draft. Separate optional suggestions and include the overall assessment, Claude’s significant assessment and Codex’s disposition, and residual verification gaps. Say explicitly when there are no findings.

Put the complete review body inside an outer four-backtick `markdown` fence. Inline comments and review cards may supplement it, but never replace or shorten the copyable review body. When composing from a long findings discussion, use the [source-grounded prose execution](../codex-writing/references/source-workflow.md) on those established findings. Deliver the saved file's absolute link without a second rendition in chat. Review judgment remains here and does not authorize posting.

For OpenSpec-governed work, also identify missing, spec-external, insufficiently tested or unverified behavior against the accepted artifacts. Apply any repository-required sidecar review and reconcile its findings.
