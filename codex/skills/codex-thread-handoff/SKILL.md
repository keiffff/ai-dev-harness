---
name: codex-thread-handoff
description: Suggest and perform a bounded handoff from a long, compacted, degraded, or phase-complete Codex task to a genuinely fresh task without carrying the full transcript. Use when context pressure, repeated corrections, rediscovered decisions, major goal changes, or a safe workflow boundary make migration useful, or when the user asks to continue in a new task/thread/session. Suggest at most once per coherent phase; never create, fork, archive, or mutate a task until the user explicitly asks for or accepts the handoff.
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
- required ignored artifacts, such as repository-local specifications, only when already known to be part of the task;
- whether each required artifact is available from a durable commit or another verified checkpoint.

Worktrees are normal isolation. A destination may use a different worktree, but never assume that `working-tree` initialization, a source worktree path, or task creation has transferred dirty state. A temporary Codex worktree path is not a durable artifact.

If the source is dirty and the destination will not share the exact checkout, require a recoverable checkpoint before creation. Accept only one of:

- an existing commit containing all required state;
- a user-authorized Git checkpoint;
- a user-approved local snapshot that explicitly covers required tracked, untracked, and ignored files; or
- a documented host transfer mechanism that explicitly covers required tracked, untracked, and ignored files and retains or rolls back the source until destination verification succeeds.

Creation options such as `startingState: working-tree` are not a recoverable checkpoint by themselves.

Do not commit, stash, create a branch, or snapshot files without the authority required for that mutation. If no recoverable checkpoint exists, stop and explain that context can be handed off but workspace state cannot yet be transferred safely.

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

## Decisions and rejected alternatives
- <Decision, rationale, and any condition that would justify reopening it.>

## Active constraints and preferences
- <Only constraints established by the user, repository, or verified environment.>

## Open work
- <Unresolved question, blocker, or next deliverable.>

## Relevant artifacts
- `<path, commit, issue, URL, or source task id>` - <why it matters>

## First action
<One concrete next action.>
```

Prefer references over duplicated diffs, logs, specifications, or source code. Include failed approaches only when omission would cause the next task to repeat them. Redact secrets, credentials, private data, and irrelevant project-specific details. Mark uncertain reconstruction as uncertain.

Keep the initial packet operational rather than historical. If a fuller conversation record is useful, keep it as a separate temporary backup; do not inject it into the destination by default.

## Create The Fresh Task

1. Discover callable Codex thread-management capabilities.
2. Pass the workspace checkpoint, exact `HEAD`, and expected dirty-state inventory in the continuation packet when filesystem state matters.
3. Create a genuinely new task with the continuation packet in its initial prompt. Keep it on the same project and follow the host's normal worktree policy; do not create a branch, commit, or switch checkout solely for migration.
4. Instruct the destination to verify its checkout read-only before work: confirm the expected repository, report cwd, and compare `HEAD`, dirty-state inventory, and required artifacts. It must stop on any mismatch rather than reconstruct or continue.
5. Instruct the destination to restate the objective, current state, unresolved points, workspace verification, and proposed first action, then wait without edits.
6. Verify task creation, initial delivery, and workspace verification before reporting a complete handoff. If only task creation is verified, report `task created; workspace verification pending`, not success.
7. Leave the source task and its checkout intact until the destination verification succeeds. Never claim that uncommitted changes were transferred from creation parameters alone.

If direct creation is unavailable or fails, do not claim success. Return the complete continuation packet and, when useful, save a temporary Markdown backup outside the repository. Give one concise instruction for starting the destination manually.

## Destination First Response

Use this instruction at the end of the initial prompt:

```text
Before continuing, use read-only checks to compare the destination checkout, HEAD, expected dirty-state inventory, and required artifacts with this packet. If anything is missing, stop and report a workspace handoff failure; do not reconstruct files or continue implementation. Then restate the objective, current state, unresolved points, workspace verification result, and proposed first action. Do not edit files yet. Wait for the user to confirm or correct your understanding.
```
