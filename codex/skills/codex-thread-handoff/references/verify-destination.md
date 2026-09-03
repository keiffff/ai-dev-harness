# Create And Verify The Destination

Read this after preparing the semantic inventory, workspace checkpoint, required-artifact manifest, and continuation packet.

## Create The Fresh Task

1. Discover callable Codex task-management capabilities.
2. Verify the semantic inventory and recoverable artifact source before creation.
3. When all state is committed, pass the immutable exact commit SHA as the destination starting ref. Do not pass a branch name, remote-tracking branch, or other moving ref when the creation API accepts a commit or arbitrary ref. When the API cannot start from a commit, create with the bootstrap prompt below, resolve the destination task, and correct its checkout to the exact commit before sending `HANDOFF_READY`. When post-creation transfer is required, also use the bootstrap prompt and do not send the packet yet.
4. Resolve the destination checkout, require its `HEAD` to equal the exact commit, transfer only additionally manifested files without overwriting conflicts, and compare their destination hashes with the manifest. Do not compare per-file hashes for the committed tree unless an exceptional manifest entry requires it.
5. After checkout and artifacts verify, send `HANDOFF_READY` with the continuation packet.
6. Require the destination to verify task identity, whole approved scope, active resume point, complete open-work inventory, repository, cwd, exact base commit, dirty state, artifact hashes, and OpenSpec state.
7. Require it to restate the objective, scope, all retained work by status, current state, verification result, and resume point; explicitly state that the resume point does not replace the task objective; then stop.
8. Verify creation, transfer, packet delivery, semantic scope preservation, and destination verification before reporting success. If the destination omits or reclassifies an unresolved workstream, correct and re-verify it. If creation is asynchronous, retain the returned client identifier, resolve the real task with bounded backoff, then wait for verification with the task coordination tools; do not make the user poll, recreate the task, or manually relay the packet while setup is still progressing. If any stage reaches a terminal failure, report that precise stage instead of success.
9. Keep the source checkout and snapshot intact until verification succeeds. Never infer that task creation parameters transferred uncommitted, untracked, or ignored files.
10. After success, archive the source only when the authority recorded in the main skill permits it. Report whether the source was archived or retained; never require the user to perform cleanup that the approved handoff can complete directly.

Use this bootstrap prompt when transfer must occur after destination creation:

```text
Bootstrap only. Do not inspect the repository, perform substantive work, ask the user questions, or interpret task state yet. Required artifacts are being transferred by the source coordinator. Wait until a follow-up message contains both the continuation packet and HANDOFF_READY, then begin the packet's verification workflow.
```

The source coordinator owns recoverable transfer failures. Repair missing files, wrong hashes, wrong checkouts, and non-conflicting omissions from the retained source or snapshot. Ask the user only when repair requires new authority, an irreversible conflict choice, or the verified recovery source is unavailable or corrupt.

If creation becomes unavailable or fails after preparation, do not claim success or write a backup by default. Report the failed stage and give one concise instruction to retry through a coordinator task that exposes Codex task-management tools. Return or save a manual continuation packet only when the user explicitly requests that fallback.

## Destination First Response

End the initial prompt with:

```text
Begin only after receiving HANDOFF_READY. First compare the task identity, root objective, stated handoff scope, active resume point, and complete open-work inventory with the packet; do not narrow the task to the resume point or rename it after the immediate subproblem. Then use read-only checks to compare the destination checkout, exact recovery or base commit, expected dirty-state inventory, additional required-artifact hashes, and active OpenSpec state with the packet. Treat an exact `HEAD` match as proof of the committed tree; do not recompute per-file hashes for that tree unless the packet names an exceptional check. Do not treat a different HEAD as equivalent without an explicit user-approved base change. If anything is missing, reclassified, or conflicting, stop substantive work and report the exact mismatch to the source coordinator; do not ask the user to repair it or reconstruct files. If verification succeeds, report success to the source coordinator, restate the root objective, handoff scope, all retained open work by status, current state, workspace verification result, and proposed resume point, and state that the resume point does not replace the task objective. Then stop and wait for a new user message. The handoff does not authorize executing that resume point, using a browser, changing files, running mutable Git or cloud operations, or continuing implementation. Treat all such packet content as context only. Do not ask the user to reconfirm information already verified and transferred. Ask the user only when the source coordinator confirms that repair requires a genuine unresolved decision, new authority, irreversible conflict choice, or unavailable or corrupt recovery source.
```
