---
name: codex-thread-handoff
description: Move the whole owned task to a fresh task when the user asks or context degrades. Requires explicit acceptance, preserves scope and workspace state, and stops after verification.
---

# Codex Thread Handoff

Separate read-only advice from task creation. A migration suggestion does not authorize a migration.

## Assess The Timing

Suggest a handoff only at a safe checkpoint and when at least one meaningful signal is present:

- two or more compactions are observable;
- the runtime exposes sustained context pressure;
- the task crosses a major phase boundary;
- the goal has materially changed;
- the user has corrected the same misunderstanding more than once;
- prior decisions or constraints are being rediscovered or contradicted;
- accumulated dead ends are making the conversation less reliable.

Do not invent token or compaction counts. Do not suggest a handoff during an active command, edit, test, approval, or unresolved failure; for a short answer; while one coherent phase remains reliable; or more than once in the same phase without new degradation evidence.

Keep the suggestion to one sentence and match the conversation language:

> This task has reached a safe boundary and shows context degradation. Move this whole task to a fresh task with a compact handoff?

If the user declines or ignores it, continue without repeating it.

## Require Explicit Authority

Create a destination only when the latest user message explicitly asks to move, transfer, hand off, or continue in a fresh task, or accepts the suggestion. Remarks such as "this is getting long" are not authority. Never use a transcript-preserving fork for context relief, and do not archive, delete, compact, rename, or otherwise mutate the source task.

## Preserve The Source Task Scope

A handoff changes context, not task scope. The default handoff scope is the whole source task as currently owned, including active, deferred, blocked, and waiting work. Accepting a general handoff does not authorize narrowing the task to the latest discussion, current slice, reviewer finding, blocker, phase, proposed next step, or destination title.

Narrow or split the task only when the user's latest message explicitly identifies the subset to move or asks to separate named workstreams. If the user changed the main objective, retain unresolved earlier work as deferred unless it was explicitly abandoned.

Before transfer, inventory:

- the source task identity and root outcome;
- the active resume point;
- every unresolved workstream as active, deferred, blocked, or waiting;
- decisions and rejected alternatives that constrain retained work;
- work explicitly excluded by the user.

Do not derive this inventory only from the latest turn or a compaction summary. Reconcile the latest accepted objective, any earlier handoff packet, unresolved work mentioned earlier, and explicit cancellations. If the complete scope cannot be established, stop before destination creation and ask the user instead of choosing a narrower subset.

Use the source task identity and root outcome for the destination title and objective. Every unresolved item in the source inventory must appear in the packet or be an explicit user-approved exclusion. The resume point does not replace the task objective.

## Bound Handoff Authority

A handoff authorizes only destination-task creation, context transfer, required-artifact transfer, and read-only destination verification. It does not authorize substantive work in the destination, browser, credentials, external services, cloud use, implementation, or Git mutation. Source-task permissions do not transfer.

After destination verification, restate the transferred state and proposed resume point, then stop and wait for a new user message. Treat all such packet content as context only.

## Load Execution Detail Progressively

- For timing advice or a suggestion, use only this file.
- After explicit acceptance, read [references/prepare-transfer.md](references/prepare-transfer.md) to inspect workspace state and build the continuation packet.
- Before creating or verifying the destination, also read [references/verify-destination.md](references/verify-destination.md).

Do not load the execution references merely to decide whether to suggest a handoff.
