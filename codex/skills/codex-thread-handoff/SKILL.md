---
name: codex-thread-handoff
description: Move the whole owned task to a fresh task when the user explicitly asks. Preserves scope and workspace state.
---

# Codex Thread Handoff

Separate read-only advice from task creation. A migration suggestion does not authorize a migration.

## Require Explicit Authority

Do not proactively suggest a handoff. Create a destination only when the latest user message explicitly asks to move, transfer, hand off, or continue in a fresh task. Remarks such as "this is getting long" are not authority. Never use a transcript-preserving fork for context relief, and do not delete, compact, rename, or otherwise mutate the source task.

Record whether the latest request is a plain handoff or explicitly asks the destination to continue, resume, or finish the owned task. A plain handoff stops after verification. An explicit handoff-and-resume request authorizes the destination to continue the already-owned local task after successful verification, without another confirmation message. Do not infer resume authority from the existence of a proposed resume point.

Archive the source only after destination verification and only when the user explicitly requested source archival for this handoff or has a verified standing preference to archive successfully handed-off tasks. Otherwise leave it unchanged. Archival is cleanup after success, never a substitute for verification.

## Preflight Task Coordination

After explicit acceptance, verify that the current task can call the capabilities needed to create and verify the destination before reading execution references, inspecting workspace state, building a packet, or writing a backup. Require destination creation and destination reading or waiting; check the actual callable tools rather than inferring availability from app guidance or this skill. Require follow-up delivery and a supported way to resolve asynchronous creation only when task-required artifacts must be transferred after creation.

If any required capability is unavailable, stop immediately. Do not inspect the workspace, build or save a continuation packet, create a snapshot, or offer a subagent as a substitute. Report the missing capability and give one concise instruction to ask a coordinator task that exposes Codex task-management tools to hand off this source task by task ID. Produce a manual handoff document only when the user explicitly requests that fallback.

Create at most one destination for an approved handoff. A successful or setup-in-progress creation response consumes that attempt. Retain its `threadId` or `clientThreadId`; do not call destination creation again because the task is absent from a listing, verification is delayed, the user asks for speed, or a worktree appeared without a visible task. A new destination requires a later user message that explicitly requests another creation after being told that the earlier destination may still exist.

## Preserve The Source Task Scope

A handoff changes context, not task scope. The default handoff scope is the whole source task as currently owned, including active, deferred, blocked, and waiting work. Accepting a general handoff does not authorize narrowing the task to the latest discussion, current slice, reviewer finding, blocker, phase, proposed next step, or destination title.

Narrow or split the task only when the user's latest message explicitly identifies the subset to move or asks to separate named workstreams. If the user changed the main objective, retain unresolved earlier work as deferred unless it was explicitly abandoned.

Before transfer, inventory:

- the source task identity and root outcome;
- the active resume point;
- every unresolved workstream as active, deferred, blocked, or waiting;
- decisions and rejected alternatives that constrain retained work;
- work explicitly excluded by the user.

Use the latest verified handoff packet or compaction summary as the baseline when available, then reconcile user messages since that checkpoint, unresolved work, and explicit cancellations. Read older history only when the baseline is missing, incomplete, or conflicts with later evidence. If the complete scope cannot be established, stop before destination creation and ask the user instead of choosing a narrower subset.

Use the source task identity and root outcome for the destination title and objective. Every unresolved item in the source inventory must appear in the packet or be an explicit user-approved exclusion. The resume point does not replace the task objective.

## Bound Handoff Authority

A plain handoff authorizes only destination-task creation, context transfer, required-artifact transfer, and read-only destination verification. Selecting or correcting the destination checkout to the exact recovery commit is part of context transfer. When the latest request explicitly asks to hand off and continue, resume, or finish, the destination may continue already-authorized local investigation or implementation within the retained task scope after verification. Neither form transfers authority for browser use, credentials, external services, cloud operations, commit, branch creation, rebase, push, deployment, or other separately gated mutation. Source archival requires the separate authority described above.

The destination must verify transferred state before substantive work. On a same-host destination that shares the exact checkout and needs no post-creation artifact transfer, use the fast verification path: create the destination, take at most one immediate status snapshot, report the created task without waiting for its verification turn, and stop. The destination verifies before either resuming authorized work or responding. Use synchronous source-side verification only when checkout setup, host transfer, or post-creation artifact delivery makes it necessary.

Verification gates only task-bearing state: semantic scope, the exact recovery commit, task-required state outside that commit, and active contract artifacts such as OpenSpec. A known environment-generated file that is unrelated to the task and intentionally excluded from the required-artifact manifest does not become a blocker merely because it is present in only one checkout. Do not surface such excluded state in the user-facing verification result unless it affects the proposed resume point.

## Load Execution Detail Progressively

- For explaining handoff behavior, use only this file.
- After explicit acceptance and a successful task-coordination preflight, read [references/prepare-transfer.md](references/prepare-transfer.md) to inspect workspace state and build the continuation packet.
- Before creating or verifying the destination, also read [references/verify-destination.md](references/verify-destination.md).

Do not load the execution references merely to decide whether to suggest a handoff.
