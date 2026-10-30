---
name: codex-thread-handoff
description: Hand off a whole task or explicitly split parallel work into a fresh task, preserving scope and isolating parallel edits in app-managed worktrees.
---

# Codex Thread Handoff

Separate read-only advice from task creation. A migration suggestion does not authorize a migration.

## Require Explicit Authority

Do not proactively suggest a handoff. Create a destination only when the latest user message explicitly asks to move, transfer, hand off, or continue in a fresh task. Remarks such as "this is getting long" are not authority. Never use a transcript-preserving fork for context relief, and do not delete, compact, rename, or otherwise mutate the source task.

Record whether the latest request is a plain handoff or explicitly asks the destination to continue, resume, or finish the owned task. A plain handoff stops after verification. An explicit handoff-and-resume request authorizes the destination to continue the already-owned local task after successful verification, without another confirmation message. Do not infer resume authority from the existence of a proposed resume point.

For a parallel split, retain the source task and its checkout; a standing preference to archive migrated tasks does not apply to work retained in the source. Archive the source only after destination verification and only when the user explicitly requested source archival for this handoff or has a verified standing preference to archive successfully handed-off tasks. Otherwise leave it unchanged. Archival is cleanup after success, never a substitute for verification.

## Select Checkout Ownership

Distinguish an exclusive move of the whole task from a parallel split before creation. If the source or another destination will continue editing, or the user asks to split a workstream or hand off multiple independent workstreams, use a separate Codex app-managed worktree for each destination. A parallel split request authorizes this isolation without another worktree question. Never share the source checkout or reuse another active destination's worktree for parallel work. Only an exclusive whole-task move may use the same-checkout fast path.

Record the source checkout, the exact base commit, the approved split scope, and the checkout ownership in the packet. Start parallel worktrees from the immutable commit and transfer only the split's task-required artifacts from a frozen snapshot. Do not clone the source's whole dirty state with `startingState: working-tree`, copy unrelated changes, or keep using absolute source paths for destination edits. If one changed file contains work owned by several tasks, separate the requested change using the scope evidence; stop before creation if ownership cannot be established.

Require the Codex app's managed-worktree creation capability as part of destination creation. If it is unavailable, report the blocker; do not fall back to a shared checkout, raw Git worktree, or temporary clone. Before destination work, verify its resolved checkout path and Git index differ from the source and all other active destinations; a shared Git common directory is normal. Source changes after the snapshot belong to the source and must not be synchronized into the destination implicitly.

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

The destination must verify transferred state before substantive work. Only for an exclusive whole-task move, on a same-host destination that shares the exact checkout and needs no post-creation artifact transfer, use the fast verification path: create the destination, take at most one immediate status snapshot, report the created task without waiting for its verification turn, and stop. The destination verifies before either resuming authorized work or responding. Use synchronous source-side verification only when checkout setup, host transfer, or post-creation artifact delivery makes it necessary.

Verification gates only task-bearing state: semantic scope, the exact recovery commit, task-required state outside that commit, and active contract artifacts such as OpenSpec. A known environment-generated file that is unrelated to the task and intentionally excluded from the required-artifact manifest does not become a blocker merely because it is present in only one checkout. Do not surface such excluded state in the user-facing verification result unless it affects the proposed resume point.

OpenSpec continuity is owned by this handoff, not by a SessionStart setup hook or a shared cache. When the destination shares the exact checkout, preserve its existing files in place. Otherwise transfer the task-required OpenSpec state under the required-artifact manifest; do not regenerate it with `openspec init` or `openspec update` as a substitute for transfer.

## Load Execution Detail Progressively

- For explaining handoff behavior, use only this file.
- After explicit acceptance and a successful task-coordination preflight, read [references/prepare-transfer.md](references/prepare-transfer.md) to inspect workspace state and build the continuation packet.
- Before creating or verifying the destination, also read [references/verify-destination.md](references/verify-destination.md).

Do not load the execution references merely to decide whether to suggest a handoff.
