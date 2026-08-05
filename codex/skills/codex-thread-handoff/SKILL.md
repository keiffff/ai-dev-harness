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

## Build The Continuation Packet

Write a compact operational packet for the destination. Preserve only information that changes what the next task should do:

```markdown
# Continuation: <current objective>

## Objective
<The outcome the user is currently pursuing.>

## Current state
<What is complete, what is in progress, and the safe checkpoint reached.>

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
2. Create a genuinely new task with the continuation packet in its initial prompt.
3. Keep it on the same project and current user-visible checkout when the host supports that. Do not create a branch, commit, switch checkout, or manufacture a worktree solely for migration.
4. Instruct the destination to restate the objective, current state, unresolved points, and proposed first action, then wait without tools or edits.
5. Verify that creation and initial delivery succeeded before reporting success.
6. Leave the source task intact as the recoverable record.

If direct creation is unavailable or fails, do not claim success. Return the complete continuation packet and, when useful, save a temporary Markdown backup outside the repository. Give one concise instruction for starting the destination manually.

## Destination First Response

Use this instruction at the end of the initial prompt:

```text
Before continuing, restate the objective, current state, unresolved points, and proposed first action. Do not call tools or edit files yet. Wait for the user to confirm or correct your understanding.
```
