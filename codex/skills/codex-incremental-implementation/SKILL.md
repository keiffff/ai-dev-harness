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

Make the change at the existing owner. Select the existing check that can expose a concrete regression; add a test only for observable behavior not covered there. Preserve accepted contract tests and diagnose failures before changing expectations.

For diagnostic additions, reuse available values and the existing emission boundary. Check added I/O, awaited or repeated work, sensitive output and exceptions at that boundary; unchanged downstream behavior is not new test work merely because it is logged.

Run missing or invalidated checks and reuse successful results for unchanged code. Let each observation choose the next action: repair the demonstrated fault, obtain the observation that distinguishes remaining explanations, or advance to delivery. Repeating a check needs changed inputs or a concrete unresolved risk. A failed check of the evaluation setup is not a product failure.

During execution, assess progress toward the requested result, not merely whether tools are running. If setup or verification dominates without producing usable results, inspect the dependency that is delaying delivery and change the plan where the observations justify it. Consider duplicate work, I/O and execution granularity across the whole path; do not optimize only the main operation.

## Deliver

Compare the actual behavior and artifacts with the original outcomes, including relevant consumers or exclusions that the work list might omit. Completion of a selected list or passing tests alone does not establish the whole request is complete. Finish the remaining authorized delivery; preparing its prose does not reopen satisfied checks.

For a code change, run `python3 ~/.codex/hooks/additions_report.py --root <verified checkout>` against the actual base. It observes added patterns, not necessity or user authority. Use observations to explain consequential additions. Report a missing observation only when it changes the requested decision or next action; do not create an unrequested stronger claim to investigate.
