---
name: codex-incremental-implementation
description: Implement multi-file changes through existing owners, choose focused checks from changed behavior, then complete the requested delivery.
---

# Codex Incremental Implementation

Restore the existing task note and results before selecting the next unfinished step below. Completed implementation and checks for unchanged code remain complete; resume at delivery when they are satisfied. Keep scope and results in that same note. AGENTS.md owns authority and continuity.

## 1. Bound The Change And Delivery

Read the original request and relevant entrypoint. Identify the behavior to add or repair, the existing behavior to preserve, and the requested final delivery. A request to preserve performance or user operations constrains the implementation; it does not by itself request a benchmark, performance guarantee or new test suite.

Trace the existing owner through data access, transformation, output and relevant tests. Start with the smallest change there. Add a helper, state, option or shared interface only when the requested behavior needs a responsibility that the existing owner cannot handle. Reuse existing lifecycle and error handling.

## 2. Choose Verification Before Adding Tests

For each changed operation, identify the concrete failure the change could introduce and the existing check that can expose it. Use the existing check first. Add a test only when the change introduces observable behavior or a concrete regression that existing coverage cannot check. Locate it at the owning boundary.

Decide this from the actual diff and accepted contracts. New log fields, helper branches and mocks do not independently require tests. Preserve accepted contract tests; inspect a failure before changing its expectation.

For an additive observation, inspect whether it adds awaited work, repeated processing, additional I/O, sensitive output, or an exception that could interrupt the primary operation. Keep any needed check focused on the changed boundary. Existing decoding, storage or UI behavior does not become new test work solely because its result is now logged.

## 3. Implement And Run The Selected Checks

Keep the patch tied to the requested behavior and the identified failure paths. Omit adjacent cleanup, speculative defenses and hypothetical compatibility. A reproduction example does not establish a general contract.

For telemetry, use the existing emission boundary and already available values. Lower layers may attach unique context and rethrow; the owner captures the event. Keep collection out of repeated or critical processing unless the requested observation requires it. Protect the primary operation and sensitive data at that boundary.

Run selected checks whose results are missing or invalidated by the current change. Carry forward recorded successful checks on unchanged code. If a check fails, localize the failure and repair its cause, then repeat the affected check. Broaden checks only for a changed operation, an observed failure, or a concrete unresolved risk shown by the patch. Record that reason before starting the extra work. A caution in the request or an imaginable failure alone does not supply it.

## 4. Finish The Requested Delivery

Once the requested behavior and its selected checks are satisfied, advance to the remaining delivery in the task note. For an authorized PR request, continue with codex-git-publish through its saved-body check and the necessary commit, push and PR creation. A draft-only delivery reaches that same body check. Preparing that delivery does not restart implementation or verification.

A later observed defect or changed scope can reopen the affected work. Extra tests, benchmarks, comparison pages and measurement fixtures need the same concrete reason as other scope changes. Keep an optional improvement outside the completion conditions.

Report the resulting behavior and the verification that supports it. State a missing observation when it changes the requested decision or next action. A production claim needs matching evidence; do not turn an unrequested production claim into additional work.
