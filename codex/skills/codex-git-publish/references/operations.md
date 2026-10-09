# Additional Git And GitHub Operations

Read only the section for the requested operation. Authorization and wrapper rules remain in `../SKILL.md`; this reference grants no additional authority.

## Branch Creation And Switching

1. Confirm the latest user message explicitly names or authorizes the target branch, or requests PR creation that requires a working branch. For PR creation, use the user-specified base and head when supplied; otherwise choose a task-appropriate working branch using the repository's existing conventions.
2. Inspect the current branch, HEAD, and worktree state.
3. Create a branch from the current HEAD with `git-user-approved switch --confirm-user-requested --create <branch>`. When the user names a fetched base ref or commit as the starting point, use `git-user-approved switch --confirm-user-requested --create <branch> <start-point>`.
4. Switch to an existing branch with `git-user-approved switch --confirm-user-requested <branch>`.

The wrapper does not support `checkout`, forced recreation, detaching HEAD, or discarding changes. Do not fall back to raw `git switch`, `git checkout`, or `git branch`.

## Merge

1. Fetch and verify the named base/default branch, current branch, and worktree state.
2. Use `git-user-approved merge --confirm-user-requested --no-edit <upstream>` for an explicitly requested non-rewriting integration.
3. If the merge conflicts, inspect and resolve only in-scope conflicts, then use `git-user-approved merge --continue`. Use `git-user-approved merge --abort` when the requested integration cannot be completed safely.
4. Run relevant verification after a successful merge.

A merge request authorizes the merge commit created by that integration. It does not authorize unrelated commits, a push, a rebase, or force-updating remote history.

## Submodules

Use `git-user-approved submodule update --remote <path>` only when the latest user request explicitly asks to synchronize the submodule. Run subsequent generation commands only after confirming they are verification rather than deployment or publication.

## GitHub PR And Issue Operations

Use `gh-readonly` for PR/issue reads and PR diffs. Use the GitHub wrapper for requested writes, including creation, metadata edits, comments, review submission, state changes and merge; these are examples, not an operation whitelist. Use the installed CLI help for the requested command rather than treating an unfamiliar option as prohibited. Specify the confirmed repository with `--repo` and an existing PR or issue by its confirmed number or URL.

For explicitly requested PR creation, complete its necessary working-branch preparation, commit and push through `git-user-approved` without asking for separate approval. Keep the commit limited to the requested changes and push only to the PR head branch; honor explicit user exclusions. Then use `--head` with the confirmed head branch to skip the CLI's implicit push/fork behavior. A requested PR checkout or merge authorizes the CLI's Git effects inherent to that operation, not unrelated commits, pushes, branch deletion or automatic future merge. Use those options only when the request includes them.

For a body update, preserve unrequested content and use `--body-file` for the complete revised body. PR/issue publication does not authorize deployment, workflow dispatch, secret access or unrelated GitHub writes. Do not use a connector, raw `gh`, generic API writes or GitHub blob/tree/commit APIs to bypass the approved wrappers. Authentication failures follow AGENTS.md; do not change accounts or credentials.

After creating a PR, attach its URL to the current task. Also attach an existing PR when asked to review, update or continue it. Verify the requested change using `gh-readonly` and report the PR URL and completed operation.
