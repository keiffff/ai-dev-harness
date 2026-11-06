---
name: codex-code-review
description: Review purposes and approaches, research existing mechanisms, then reconcile Claude's objections and report proportionate corrections.
---

# Codex Code Review

Main owns the review judgment. Use one approach-review path, not a separate agent for each criterion.

## Review Judgment

Start with the user's goal and the promised behavior. Separate accepted requirements, PR-author claims and unknowns using their sources. Read a linked decision through the available authorized read path when it governs the approach; preserve an actual access blocker instead of inventing a product decision. Respect accepted decisions and rejected alternatives unless new evidence warrants reopening them. On re-review, check whether the original problem is resolved. A missing diff limits regression attribution, not assessment of evidenced behavior.

### Review the approach with Claude

For a substantive full change review, use `claude-strategic-review` to independently challenge whether the approach serves the user's purpose, assigns responsibilities well and justifies its complexity. Codex retains concrete behavior/I/F tracing, likelihood/impact assessment and the final judgment. A wording edit or verification of an already established finding does not reopen this full review.

Follow [review execution record](references/review-record.md): prepare the purpose, sourced requirements and unknowns; run its goal-only `discover` for consequential mechanisms; compare the resulting candidates with the actual code and supported environment. Then give Claude the original request, constraints, source evidence and comparison under its existing contract. Keep the implementation hypothesis and Codex's interpretation separate, rather than making approval or a defect list the premise. Reconcile objections and run `render` in private task storage. The result must show whether the approach is proportionate. A minor local change can justify no separate discovery; do not manufacture alternatives or a redesign.

Reconcile each material objection before writing the overall assessment:

1. Identify the disputed claim, its supporting evidence, the consequence if true and the observation that would settle it. Preserve Claude's stated confidence and limits; evaluate the claim rather than the reviewer's identity.
2. Adopt an evidenced defect. Resolve or reject an objection only by showing source evidence that contradicts its premise, or an established contract that makes its consequence inapplicable. For a design finding, keep justified complexity and require a concrete cost plus a feasible alternative preserving the purpose. Not finding a prohibition, not reproducing an unexercised path, and passing checks that do not cover the disputed boundary are not counterevidence.
3. Keep a material claim unresolved when neither its validity nor its rebuttal is established. State the remaining fact and its consequence; do not turn uncertainty into a confirmed defect, mandatory redesign or automatic deployment requirement. Use relevant existing code, documents, tests or observations to settle it within the task's authority.

Build the overall assessment from these dispositions. If an unresolved objection could invalidate the change's purpose, deployment or promised behavior, name it in the overall assessment and qualify the conclusion. Do not report an unconditional clean review while burying it in verification limits. "No confirmed defects" does not mean the unresolved acceptance condition is satisfied. Report Claude's significant assessment and the evidence for Codex's disposition separately. Follow the strategic-review skill's existing execution and failure handling.

### Trace behavior to test the compared approaches

Follow each affected operation from its actual entry through validation, state changes, persistence and the consumer that observes the result. Use `codex-interface-review` for changed API/schema/state/persistence contracts within this pass.

- At mutable-state boundaries, compare what was read or authorized with what the final write actually predicates on. Follow the values, identities and versions across awaits and transactions. Exercise the competing transitions already supported by the system: a state can return to its previous label with different contents or permissions. A transaction or a status check alone does not prove that the originally authorized operation is still valid. A supported concurrent transition is a system condition, not an invented user gesture sequence; do not require a production incident to recognize a demonstrated contract violation.
- At alternate entry/commit paths, check that accepted validation and authorization survive to stored values and readers. Where the change resolves references or filters a requested selection, trace the missing-reference and zero-result cases through persistence to the consumer. An intentionally empty selection and a nonempty selection whose references all disappeared need not mean the same thing; inspect what the reader does with the resulting empty value. Follow failures and actual recovery before claiming loss, disclosure or irrecoverable state.
- Compare the current approach with evidenced existing or standard mechanisms under the same requirements, supported environments, ownership and operating/maintenance cost. A technically possible remedy is not a recommendation until its added responsibilities are weighed against the actual harm. Do not require a runtime defect to explain an avoidable recurring cost. Preserve justified complexity and distinguish a behavior-changing alternative from a simplification.

Keep discovered defects separate from their disposition. Do not silently discard an evidenced contract failure because its exact frequency is unknown; decide how to report it below.

### Weigh likelihood and consequence

For each candidate, establish the actor's goal or exposed system condition, the route to the trigger, the violated contract and the actual consequence. Technically possible user actions do not establish a realistic combined workflow: explain why the goal leads to that order or timing, rather than restating a feature as a goal. A nearby defensive comment/check establishes mechanics, not a universal product requirement. Bypassing the PR's own guard alone does not establish harm.

Explain likelihood/frequency together with affected scope, recurrence, harm and recoverability in ordinary language. Frequent small failures can accumulate; rare failures can have severe consequences. Use numbers only when supported; do not invent user counts, probabilities or urgency. State whether correction is warranted now and why, without P0/P1/P2/P3 or other unexplained priority codes. Deliberate abuse, concurrent updates, network failures and retries are judged by actual exposure and contract.

Adopt a required finding when the supported path and consequence justify correction. Keep contrived or unexplained action combinations with unestablished harm as investigation candidates, not required fixes. Carry material unresolved contracts into the overall assessment using the reconciliation above. Separate findings, optional improvements and questions. Retain the operation, evidence, consequence, location and reason for correction with adopted findings. Avoid speculative hardening and unrelated cleanup.

## Test Scope

Trace disputed expectations to their source. Existing accepted contract tests can establish promised behavior; tests added in the reviewed change are part of that proposal. Inspect the exact condition, and assess a new expectation against the stated goal rather than letting its presence settle the goal's meaning. A new passing test can encode the same incomplete fix as the implementation. Reserve unresolved-contract questions for an actual gap or conflict among governing requirements. Do not claim missing coverage without checking the relevant tests. Prefer tests at the owning boundary; helper calls, mock choreography, unused defensive paths and duplicate coverage are not independent reasons for tests.

Keep mock interactions or negative assertions when the interaction or absence is itself an accepted contract, such as no unauthorized write, duplicate charge, repeated external call, or stale user-visible state. Tests for an intentionally removed implementation concept may go with that concept; preserve tests of behavior still promised to consumers.

## Uncertain Boundary ANDON

When a consequential decision relies on indirect evidence such as time, ordering, status, existence or naming, inspect the smallest producer, representation, decision point, failure state and recovery path. If the contract remains unresolved, do not invent an identifier, fallback, retry, compatibility path or extra test as the presumed fix. Report the facts, missing decision and impact.

For a consequential repo-local change, use one bounded `codex-doubt-review` cycle when independent review can test the unresolved assumption. Include relevant interface criteria in that same review. Main reconciles findings and owns the ANDON decision.

## Copyable Review Output

Build each comment from the established finding or the user's accepted plain explanation, rather than reconstructing it from implementation names:

1. Lead with a short conclusion that identifies the change, whether its approach is appropriate and what must happen next. Then give required corrections and decisions separately. Include an alternative and its trade-off where it changes a correction or decision; do not print the full candidate comparison.
2. For each adopted finding give the current code location, what appears wrong, a realistic trigger, actual consequence and proportionate correction. Use clickable Markdown links for findings' locations and decision questions' source references when the target is known; preserve verified URLs and line numbers, and use absolute paths for real local files. A backticked path is not a link; do not invent a target or imply an old location was rechecked. Distinguish newly introduced behavior, an incomplete promised fix and unrelated old behavior using the base/head evidence. Explain whether correction is warranted now without priority codes; keep unverified reproduction unverified.
3. Retain the full Claude reconciliation privately. In the review, briefly report Claude's significant assessment and Codex's adoption or disagreement; explain disputed evidence only where it affects the conclusion or reader's next action. A remaining risk accepted under an established contract is not disproved. Each material unresolved issue must appear as a concrete correction or decision, explaining the consequence and what answer changes the recommendation. Ordinary unexercised checks belong together in verification limits and do not automatically block acceptance. When editing an established comment, preserve its accepted explanation and location rather than reconstructing it from internal names.

Put the complete review directly in this chat as rendered Markdown, without an outer code fence. For a substantive review use the execution record's output directly, without a second model rewrite. Do not substitute a summary, a file link or a separate app panel for the complete chat body. Private execution records are not the deliverable. Supply a fenced copy only when the user explicitly requests copyable source. Inline comments and review cards are supplementary. Review judgment does not authorize posting.

For OpenSpec-governed work, also identify missing, spec-external, insufficiently tested or unverified behavior against the accepted artifacts. Apply any repository-required sidecar review and reconcile its findings.
