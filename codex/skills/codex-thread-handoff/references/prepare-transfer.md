# Prepare A Thread Handoff

Read this only after the user explicitly accepts a handoff.

## Gate On Workspace State

Conversation context and filesystem state are separate handoff surfaces. A complete packet does not preserve uncommitted files.

Inspect the source checkout read-only and record:

- exact checkout path and `HEAD`;
- tracked, staged, and untracked changes;
- required ignored artifacts, including repository-local specifications;
- whether each required artifact is available from a durable commit or another verified checkpoint.

Classify differences as task-required artifacts, user-owned or unknown changes, or known environment-generated files. Block on missing task artifacts and user-owned or unknown differences. A destination-only environment-generated file does not block the handoff when its owner and trigger are known, it is unrelated to the task, and the base commit plus manifest still match. Record it as excluded environment state; do not transfer, edit, or delete it.

Do not rely on ordinary `git status` for ignored artifacts. Search the active contract, conversation references, and repository instructions for artifact roots. For OpenSpec, enumerate candidates directly under `openspec/changes/`, establish the active change from source evidence, and inspect the complete selected tree. If multiple candidates remain, stop before destination creation instead of choosing one. Do not sweep unrelated ignored areas such as dependency caches or secrets.

## Build The Required-Artifact Manifest

For every required file:

- classify it as committed, staged, tracked-dirty, untracked, or ignored;
- record its recovery source and hash;
- verify committed claims with `git ls-tree`, `git cat-file`, or `git show`;
- record the transfer method for non-committed artifacts;
- later record and compare the destination hash.

When OpenSpec is active, include the whole change tree, relevant config and instructions, directly referenced specs, current task status, and latest apply or validation result.

A worktree is isolation, not a checkpoint. Do not assume `startingState: working-tree`, a source path, or task creation transferred dirty state. A temporary worktree is not durable.

If required state is not committed and the destination will not share the exact checkout, establish one recoverable transfer before creation:

- an existing commit containing all required state;
- a user-authorized Git checkpoint;
- a bounded local snapshot covering required tracked, untracked, and ignored files; or
- a documented host transfer that covers those files and retains or rolls back the source until verification succeeds.

Handoff authority permits a non-destructive local snapshot or exact transfer of task-required files. It does not permit commit, stash, branch creation, conflict overwrite, or unrelated file copying. Keep the source and snapshot until destination verification succeeds. If no recoverable transfer can be prepared, stop before creation and report the blocking condition.

## Build The Continuation Packet

Use this structure:

```markdown
# Continuation: <source task identity>

## Objective
<Root outcome of the source task.>

## Scope continuity
- Handoff scope: <whole source task, or explicitly requested subset>
- Active resume point: <where work should resume>
- Retained deferred, blocked, or waiting work: <complete inventory>
- Explicit exclusions: <only user-approved exclusions or named split work>

## Current state
<Complete, in progress, and safe checkpoint.>

## Workspace checkpoint
- Source checkout: `<path>`
- Source HEAD: `<commit>`
- Expected changes: <tracked, staged, untracked, required ignored inventory>
- Recovery source: <commit, approved snapshot, or verified transfer>
- Required-artifact manifest: <path, classification, recovery source and hash, destination hash, transfer method>

## Decisions and rejected alternatives
- <Decision, rationale, and reopening condition.>

## Active constraints and preferences
- <Only verified user, repository, and environment constraints.>

## Open work
- Active: <current unresolved work>
- Deferred: <retained work not immediately active>
- Blocked or waiting: <work awaiting authority, evidence, or external state>

## Relevant artifacts
- `<path, commit, issue, URL, or source task id>` - <why it matters>

## Contract checkpoint
- Active OpenSpec/change/spec/task identifiers and counts
- User-approved decisions and rejected alternatives
- Latest successful and failed verification commands
- Known blockers and disputed completion claims

## Proposed resume point
<One concrete action for the user to authorize. It is not a new objective.>
```

Prefer references over copied diffs, logs, specs, or source code. Include failed approaches only when needed to prevent repetition. Redact secrets and irrelevant private data. Mark uncertain reconstruction as uncertain.

Do not collapse the `Open work` inventory into the proposed resume point. For an explicit split, record work retained elsewhere under `Explicit exclusions`.

Packet prose is not proof that an artifact is committed or transferred. Complete the handoff only after recovery-source and destination hashes match for every manifest entry.

Keep the initial packet operational rather than historical. If a fuller transcript backup is useful, keep it separate instead of injecting it into the destination.
