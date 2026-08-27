---
name: codex-openspec-workflow
description: Create, apply, review, or archive OpenSpec changes. Use only when OpenSpec artifacts are requested or already govern the work.
---

# Codex OpenSpec Workflow

Treat repository-local `openspec/AGENTS.md` and current OpenSpec prompts as the authority for artifact format and CLI syntax. This skill adds user gates, context loading, implementation control, and post-implementation review.

## Route

- Create artifacts when the user asks to put a change into OpenSpec. Create the required proposal, design, tasks, and spec delta, then validate. Do not implement in the same step.
- Apply artifacts when the user explicitly asks to implement an approved change or follow its tasks. Load `codex-incremental-implementation` after obtaining current apply instructions.
- Review artifacts when the user asks whether implementation matches the accepted change. Compare contracts before proposing improvements.
- Archive only after the user explicitly asks and the repository workflow permits it. Treat archive commands as mutation.

## Create

1. Read the nearest `openspec/AGENTS.md` and repository conventions.
2. Check existing specs and active changes before creating a new capability or change ID.
3. Separate proposal, design decisions, tasks, and spec deltas according to the repository format.
4. Run the repository's current OpenSpec validation command.
5. Stop before implementation.
6. Report only the human Gate 2 decisions: I/F, state, operation-specific behavior, in/out of scope, existing-feature boundaries, compatibility, and unresolved questions.

## Apply

1. Run `openspec status --change <id> --json` and inspect the schema, artifact paths, progress, and apply conditions.
2. Run `openspec instructions apply --change <id> --json` and read the returned context and dependency files.
3. If either command is unavailable, update the global OpenSpec CLI through the required approval flow and retry. Do not silently fall back to a legacy direct-file workflow.
4. Read proposal, design, tasks, or spec files directly only when the CLI output lacks required detail.
5. Use `codex-incremental-implementation` and follow the accepted tasks autonomously.
6. Stop before changing I/F names, spec meaning, persistence format, external behavior, or accepted scope.

## Compatibility Gate

- When existing DB records, saved JSON, API responses, localStorage, or another persisted shape may be affected, identify the current shape, affected readers, reason compatibility may be needed, and the option of not supporting it before implementing a fallback.
- Do not add backward compatibility for discarded ideas, incorrect implementations, or unreleased intermediate states from the same session unless the user explicitly requires it.
- After the user decides compatibility, record that decision in the relevant design, spec, and tasks before implementation.

## Review

1. Compare the implementation with design and spec contracts.
2. Classify implementation as complete, missing, spec-external, insufficiently tested, or unverified.
3. Fix accepted implementation gaps without broadening the spec.
4. When required by repository guidance, use `claude-strategic-review` for bounded sidecar review of I/F, state transitions, boundaries, spec-external behavior, and missing tests.
5. Classify each sidecar finding as implemented, added to artifacts, or rejected with a reason. Codex owns the final decision.

## Final Report

Report spec coverage, adopted or rejected sidecar findings, verification, and residual risk. Do not return a file-by-file work log.
