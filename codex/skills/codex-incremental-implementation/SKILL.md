---
name: codex-incremental-implementation
description: Implement multi-file changes through existing owners, choose proportionate checks, and complete the requested delivery.
---

# Codex Incremental Implementation

## Choose The Work

Restore the original request, completed work and remaining delivery from the existing task note. Separate requested outcomes and constraints from agent-selected steps. A performance or safety caution constrains the solution; it does not create a separate proof, benchmark or test-suite deliverable.

Trace the entrypoint, existing owner, consumers and accepted contracts. Prefer using or repairing an existing mechanism before adding responsibility, state, helpers or compatibility paths. Compare an alternative when it could materially simplify the solution; routine edits do not need an alternatives report.

When expanding the work, connect the addition to an observed failure or accepted requirement, the consequence of leaving it out, and the decision its result would change. Weigh that consequence against waiting time, implementation and operating cost, and reversibility. Keep optional improvements outside completion conditions. Use the task note for consequential additions, not a new planning document or approval step.

## Implement And Check

Before changing behavior, use the task note to map the ordinary affected operations: action/input and state; observed before result; requested change or preserve; original user source for each allowed difference; executable entry; before/after result. Fix allowed differences before implementing. Separate user words from assistant interpretations, including an inherited proposal. A named operation does not authorize changing every operation that shares its handler. Reuse a maintained project verification map when available; do not create another planning document or enumerate arbitrary combinations.

Trace each changed branch and shared handler back to those operations. Include its relevant taken/not-taken path and distinct callers; a helper's success does not establish that its caller starts or receives the right state. If an affected entry is missing, add that operation to the same map without changing its allowed result to match the candidate.

Run the narrow existing entry on before and candidate, recording the actual source and observations in the same rows. Add only a missing observable check needed to distinguish requested behavior from a regression. Repair differences outside the request and rerun affected rows; preserve accepted contract tests. Use component checks for component behavior and actual scheduler/run evidence for orchestration. Source inspection identifies checks but is not an executed result.

For diagnostic additions, reuse available values and the existing emission boundary. Check added I/O, awaited or repeated work, sensitive output and exceptions at that boundary; unchanged downstream behavior is not new test work merely because it is logged.

Reuse successful observations for unchanged rows; execute missing or invalidated checks only when they can change the repair or delivery decision. Let each observation choose the next action: repair the demonstrated fault, obtain the observation that distinguishes remaining explanations, or advance to delivery. Repeating a check needs changed inputs or a concrete unresolved risk. A failed check of the evaluation setup is not a product failure.

When the requested work must continue after an external job or deployment finishes, register that exact wait with `python3 ~/.codex/ci-events/bridge.py wait-run` or `wait-deploy`; launch a requested detached local command through `run-local`. Pass the owning `CODEX_THREAD_ID`, original request file and already requested next action. See [continuation commands](../../ci/README.md). End the turn instead of repeatedly polling with the model. Do not register unrelated follow-ups. Resume the original work when its event arrives, then use `finish` with the actual result; queue delivery alone does not complete it.

During execution, assess progress toward the requested result, not merely whether tools are running. If setup or verification dominates without producing usable results, inspect the dependency that is delaying delivery and change the plan where the observations justify it. Consider duplicate work, I/O and execution granularity across the whole path; do not optimize only the main operation.

## Deliver

Reconcile the same operation rows with the original outcomes and artifacts, including relevant consumers or exclusions that the work list might omit. Completion of a selected list or passing tests alone does not establish the whole request is complete. Finish the remaining authorized delivery; preparing its prose does not reopen satisfied checks.

For a code change, run `python3 ~/.codex/hooks/additions_report.py --root <verified checkout>` against the actual base. It observes added patterns, not necessity or user authority. Use observations to explain consequential additions. Report a missing observation only when it changes the requested decision or next action; do not create an unrequested stronger claim to investigate.
