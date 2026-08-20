---
name: codex-thread-handoff
description: Suggest and perform a bounded handoff from a long, compacted, degraded, or phase-complete Codex task to a genuinely fresh task, transferring operational context and required workspace artifacts without carrying the full transcript. Use when context pressure, repeated corrections, rediscovered decisions, major goal changes, or a safe workflow boundary make migration useful, or when the user asks to continue in a new task/thread/session. Suggest at most once per coherent phase; never create, fork, archive, or mutate a task until the user explicitly asks for or accepts the handoff.
---

# Codex Thread Handoff

Separate read-only advice from task creation. A migration suggestion does not authorize a migration.

## Assess The Timing

Suggest a handoff only at a safe checkpoint and when at least one meaningful signal is present:

- two or more compactions are observable;
- the runtime exposes sustained context pressure, such as more than roughly 60% of the context window;
- the task crosses a major phase boundary, such as discovery to design or design to implementation;
- the goal has materially changed from the task's original purpose;
- the user has corrected the same misunderstanding more than once;
- prior decisions, constraints, or rejected approaches are being rediscovered or contradicted;
- accumulated dead ends are making the current conversation less reliable.

Do not invent token counts or compaction counts when the runtime does not expose them. Use qualitative evidence instead.

Do not suggest a handoff:

- during an active command, edit, test, approval, or unresolved failure;
- when the user only needs a short answer;
- when the work is still one coherent phase and the existing reasoning trail remains useful;
- more than once in the same coherent phase unless new degradation evidence appears.

Keep the suggestion to one sentence:

> This task has reached a safe boundary and shows context degradation. Move it to a fresh task with a compact handoff?

Match the language of the source conversation. If the user declines or ignores the suggestion, continue the task without repeating it.

## Require Explicit Authority

Create a destination task only when the user's latest message explicitly asks to move, transfer, hand off, or continue in a fresh task, or explicitly accepts a suggestion.

Do not treat remarks such as "this is getting long" as task-creation authority. Never use a transcript-preserving fork for context relief because it carries the bloated history forward. Do not archive, delete, compact, rename, or otherwise mutate the source task.

## Gate On Workspace State

Treat conversation context and filesystem state as separate handoff surfaces. A complete packet does not preserve uncommitted files.

Before creating the destination, inspect the source checkout read-only and record:

- the exact checkout path and `HEAD`;
- tracked, staged, and untracked changes;
- required ignored artifacts, such as repository-local specifications;
- whether each required artifact is available from a durable commit or another verified checkpoint.

Do not rely on ordinary `git status` to discover required ignored artifacts. Search the active task contract, conversation references, and repository-local instructions for artifact roots and change identifiers, then inspect those scoped paths with ignored-file-aware checks. For OpenSpec work, enumerate ignored and visible candidates directly under `openspec/changes/`, reconcile them with the task contract and recent OpenSpec commands, and then inspect the complete selected change tree. If multiple candidates remain and the active change cannot be established from source evidence, stop in the source before destination creation. Do not sweep unrelated ignored areas such as dependency caches or secrets.

Build a required-artifact manifest before creating the destination:

- enumerate every required file, including files inside required directories;
- classify each file as committed, staged, tracked-dirty, untracked, or ignored;
- record the recovery-source hash for every file and later record the verified destination hash;
- verify committed claims against the recovery commit with `git ls-tree`, `git cat-file`, or `git show`; existence in the source working tree is not proof that the commit contains it;
- record the destination transfer method for each non-committed artifact.

When an OpenSpec change is active, treat the artifact closure as the whole change, not a hand-picked subset. Include `openspec/changes/<change-id>/**`, relevant OpenSpec config/instructions, directly referenced capability/spec files, current task status, and the latest apply/validation result. Verify the change id and task counts from the source checkout immediately before handoff.

Worktrees are normal isolation. A destination may use a different worktree, but never assume that `working-tree` initialization, a source worktree path, or task creation has transferred dirty state. A temporary Codex worktree path is not a durable artifact.

If the source is dirty or required artifacts are ignored/untracked and the destination will not share the exact checkout, establish a recoverable transfer before creation. Accept only one of:

- an existing commit containing all required state;
- a user-authorized Git checkpoint;
- a bounded local snapshot that explicitly covers required tracked, untracked, and ignored files; or
- a documented host transfer mechanism that explicitly covers required tracked, untracked, and ignored files and retains or rolls back the source until destination verification succeeds.

Creation options such as `startingState: working-tree` are not a recoverable checkpoint by themselves.

An explicit user request to hand off authorizes a non-destructive local snapshot or exact file transfer of task-required artifacts to the fresh destination. It does not authorize commit, stash, branch creation, overwriting a conflicting destination file, or copying unrelated files. Keep the source and snapshot intact until destination verification succeeds. If no recoverable transfer can be prepared, stop in the source before destination creation and explain the single blocking condition.

## Build The Continuation Packet

Write a compact operational packet for the destination. Preserve only information that changes what the next task should do:

```markdown
# Continuation: <current objective>

## Objective
<The outcome the user is currently pursuing.>

## Current state
<What is complete, what is in progress, and the safe checkpoint reached.>

## Workspace checkpoint
- Source checkout: `<path>`
- Source HEAD: `<commit>`
- Expected changes: <tracked, staged, untracked, and required ignored-file inventory>
- Recovery source: <durable commit, approved snapshot, or verified host transfer>
- Required-artifact manifest: <path list, source classification, recovery source, recovery hash, destination hash, and transfer method>

## Decisions and rejected alternatives
- <Decision, rationale, and any condition that would justify reopening it.>

## Active constraints and preferences
- <Only constraints established by the user, repository, or verified environment.>

## Open work
- <Unresolved question, blocker, or next deliverable.>

## Relevant artifacts
- `<path, commit, issue, URL, or source task id>` - <why it matters>

## Contract checkpoint
- Active OpenSpec/change/spec/task identifiers and current completion counts
- User-approved decisions and explicitly rejected alternatives that constrain implementation
- Latest successful and failed verification commands, with relevant scope
- Known blockers and disputed completion claims

## First action
<One concrete next action.>
```

Prefer references over duplicated diffs, logs, specifications, or source code. Include failed approaches only when omission would cause the next task to repeat them. Redact secrets, credentials, private data, and irrelevant project-specific details. Mark uncertain reconstruction as uncertain.

Do not claim an artifact is committed, transferred, or recoverable from packet prose alone. Back every such claim with the source manifest and a verified recovery path. Complete the handoff only when every manifest entry has matching recovery-source and destination hashes. For an OpenSpec closure, enumerate and match every file; directory existence alone is insufficient.

Keep the initial packet operational rather than historical. If a fuller conversation record is useful, keep it as a separate temporary backup; do not inject it into the destination by default.

## Create The Fresh Task

1. Discover callable Codex thread-management capabilities.
2. Prepare and verify the required-artifact manifest and its recovery/transfer source before creating the destination.
3. When all required state is committed, create the destination from the exact verified ref/commit rather than the project default. When a bounded snapshot/file transfer is required, create the destination with the bootstrap prompt below; do not send the continuation packet yet.
4. Resolve the destination checkout, transfer only the manifested files without overwriting conflicts, and verify destination hashes against the source manifest. Transfer the whole active OpenSpec closure when applicable.
5. After checkout and artifact verification succeed, send `HANDOFF_READY` with the continuation packet. Instruct the destination to verify the repository, cwd, exact recovery/base commit recorded in the packet, dirty-state inventory, required-artifact hashes, and OpenSpec task state before work. Do not accept a different `HEAD` merely because required files exist there.
6. Instruct the destination to restate the objective, current state, unresolved points, workspace verification result, and first action, then continue with that first action automatically. Require user input only for a genuine unresolved decision, new authority, or an integrity mismatch that the source could not resolve.
7. Verify task creation, artifact transfer, packet delivery, and destination verification before reporting a complete handoff. If any stage is incomplete, report that precise stage instead of success.
8. Leave the source task, checkout, and transfer snapshot intact until destination verification succeeds. Never claim that uncommitted, untracked, or ignored changes were transferred from creation parameters alone.

Use this bootstrap prompt when transfer must occur after destination creation:

```text
Bootstrap only. Do not inspect the repository, perform substantive work, ask the user questions, or interpret task state yet. Required artifacts are being transferred by the source coordinator. Wait until a follow-up message contains both the continuation packet and `HANDOFF_READY`, then begin the packet's verification workflow.
```

The source coordinator owns recoverable transfer failures. Monitor destination verification; on a missing file, wrong hash, wrong checkout, or non-conflicting transfer omission, repair the destination from the retained source/snapshot and re-run verification without returning the problem to the user. Ask the user only when repair requires new authority, an irreversible conflict choice, or the verified recovery source itself is corrupt or unavailable.

If direct creation is unavailable or fails, do not claim success. Return the complete continuation packet and, when useful, save a temporary Markdown backup outside the repository. Give one concise instruction for starting the destination manually.

## Destination First Response

Use this instruction at the end of the initial prompt:

```text
Begin only after receiving `HANDOFF_READY`. Use read-only checks to compare the destination checkout, exact recovery/base commit recorded in the packet, expected dirty-state inventory, required-artifact hashes, and active OpenSpec task state with this packet. Do not treat a different `HEAD` as equivalent without an explicit user-approved base change recorded in the packet. If anything is missing or conflicting, stop substantive work and report the exact mismatch to the source coordinator; do not ask the user to repair it or reconstruct files. If verification succeeds, report success to the source coordinator, restate the objective, current state, unresolved points, workspace verification result, and first action, then immediately execute that first action. Do not ask the user to reconfirm information already verified and transferred. Ask the user only when the source coordinator confirms that repair requires a genuine unresolved decision, new authority, irreversible conflict choice, or unavailable/corrupt recovery source.
```
