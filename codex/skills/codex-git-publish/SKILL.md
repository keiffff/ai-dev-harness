---
name: codex-git-publish
description: Perform explicitly requested Git publication and GitHub PR/issue operations through approved wrappers; never infer write authority from review or drafting requests.
---

# Codex Git Publish

Use the current user-visible worktree. This skill defines the publication procedure; it never grants permission by itself.

## Authorization

- Perform branch creation or switching, commit, merge, push, PR branch update, or submodule sync only when the latest user request explicitly asks for that operation. An explicit PR creation request also authorizes the working-branch creation or switching, commit of the requested changes, and push to the PR head branch needed to create that PR, without separate confirmation. Honor an explicit no-commit or no-push instruction. This does not authorize unrelated changes, direct pushes to shared branches such as main, merge, or deployment. A request to incorporate the latest base/default branch authorizes merging that named branch into the current branch.
- Rebase only when explicitly requested or as the necessary integration within an authorized push or PR branch update. An explicitly requested push or PR branch update, including the push needed for explicitly requested PR creation, authorizes rebasing unpublished local commits onto the confirmed latest upstream without separate confirmation, even when both sides have new commits. Honor explicit no-rebase instructions. For this push integration, stop on conflicts, a required rewrite of published history or unclear remote history ownership; divergence alone is not a reason to stop. This does not authorize an unrequested merge or force-push.
- Read-only Git commands are allowed when relevant.
- Perform PR/issue operations only when the latest user request explicitly asks for the affected operation and target. Review, advice and drafting alone do not authorize posting or editing a PR or issue. Do not infer PR/issue creation from a commit/push request. Only an explicit PR creation request includes its necessary branch preparation, commit and push; other PR/issue requests, review and drafting do not. A PR request does not authorize an issue write, or vice versa.
- Do not carry Git or PR/issue mutation authorization into a later user turn.
- Use English commit messages.

## Wrapper Boundary

Use `/Users/kei/.local/bin/git-user-approved` for `add`, `commit`, `merge`, `rebase`, `switch`, `submodule update`, and `push`. Do not use raw mutation commands.

Use `/Users/kei/.local/bin/gh-user-approved --confirm-user-requested pr|issue <command> [args...]` for explicitly requested PR/issue operations. It accepts the entire `gh pr` and `gh issue` command families and passes subcommands and options unchanged; do not add per-operation or per-field allowlists. The confirmation flag records Codex's authority check, not independent proof of user consent. Match the requested operation and target before invoking it, without asking for redundant confirmation of an explicit request.

If the wrapper is blocked by the sandbox, rerun the same wrapper command through the approval flow. Do not switch to another Git path.

When the Git directory is already known to sit outside the writable sandbox, use the required approval flow on the first wrapper call. Do not run an identical sandboxed attempt merely to reproduce the known permission failure.

## Branch Creation And Switching

1. Confirm the latest user message explicitly names or authorizes the target branch, or requests PR creation that requires a working branch. For PR creation, use the user-specified base and head when supplied; otherwise choose a task-appropriate working branch using the repository's existing conventions.
2. Inspect the current branch, HEAD, and worktree state.
3. Create a branch from the current HEAD with `git-user-approved switch --confirm-user-requested --create <branch>`. When the user names a fetched base ref or commit as the starting point, use `git-user-approved switch --confirm-user-requested --create <branch> <start-point>`.
4. Switch to an existing branch with `git-user-approved switch --confirm-user-requested <branch>`.

The wrapper does not support `checkout`, forced recreation, detaching HEAD, or discarding changes. Do not fall back to raw `git switch`, `git checkout`, or `git branch`.

## Commit

1. Run `git status --short --branch` and inspect the relevant diff.
2. Stage only intended explicit paths with `git-user-approved add <path...>`.
3. Do not force-add ignored or excluded files. Treat them as local context.
4. Inspect `git diff --cached --stat` and `git diff --cached --check`.
5. Commit with `git-user-approved commit -m "<English subject>"`.

Do not use `git commit -a`, implicit all-file staging, or a temporary clone to create the commit. Amend only when the latest user request explicitly authorizes rewriting the affected commit: stage only its intended corrections, then use `git-user-approved commit --confirm-user-requested --amend --no-edit`. An ordinary commit/push request does not authorize amend. For a requested rewrite of published history, verify the remote head and push with an explicit `--force-with-lease=refs/heads/<branch>:<confirmed-remote-sha>`; do not use a plain force-push.

## Merge

1. Fetch and verify the named base/default branch, current branch, and worktree state.
2. Use `git-user-approved merge --confirm-user-requested --no-edit <upstream>` for an explicitly requested non-rewriting integration.
3. If the merge conflicts, inspect and resolve only in-scope conflicts, then use `git-user-approved merge --continue`. Use `git-user-approved merge --abort` when the requested integration cannot be completed safely.
4. Run relevant verification after a successful merge.

A merge request authorizes the merge commit created by that integration. It does not authorize unrelated commits, a push, a rebase, or force-updating remote history.

## Push

1. Run `git fetch --prune` after the commit and before relying on remote refs.
2. Compare the current branch, upstream, local HEAD, and remote HEAD.
3. When integration is needed, inspect the local-only commits against the fetched remote refs. If rebasing rewrites only unpublished local commits onto the confirmed upstream, use `git-user-approved rebase <upstream>` without separate confirmation, including when both sides have new commits. Honor an explicit no-rebase instruction.
4. Stop on conflicts, a required rewrite of published history or unclear remote history ownership. Divergence alone is not a reason to stop. Do not substitute an unrequested merge or force-push.
5. Push only with `git-user-approved push --confirm-user-requested ...`.

Do not create remote-only commits, update Git objects through a connector, or copy changes into another worktree for publication.

## Submodules

Use `git-user-approved submodule update --remote <path>` only when the latest user request explicitly asks to synchronize the submodule. Run subsequent generation commands only after confirming they are verification rather than deployment or publication.

## GitHub PR And Issue Operations

Use `gh-readonly` for PR/issue reads and PR diffs. Use the GitHub wrapper for requested writes, including creation, metadata edits, comments, review submission, state changes and merge; these are examples, not an operation whitelist. Use the installed CLI help for the requested command rather than treating an unfamiliar option as prohibited. Specify the confirmed repository with `--repo` and an existing PR or issue by its confirmed number or URL.

For explicitly requested PR creation, complete its necessary working-branch preparation, commit and push through `git-user-approved` without asking for separate approval. Keep the commit limited to the requested changes and push only to the PR head branch; honor explicit user exclusions. Then use `--head` with the confirmed head branch to skip the CLI's implicit push/fork behavior. A requested PR checkout or merge authorizes the CLI's Git effects inherent to that operation, not unrelated commits, pushes, branch deletion or automatic future merge. Use those options only when the request includes them.

For a body update, preserve unrequested content and use `--body-file` for the complete revised body. PR/issue publication does not authorize deployment, workflow dispatch, secret access or unrelated GitHub writes. Do not use a connector, raw `gh`, generic API writes or GitHub blob/tree/commit APIs to bypass the approved wrappers. Authentication failures follow AGENTS.md; do not change accounts or credentials.

After creating a PR, attach its URL to the current task. Also attach an existing PR when asked to review, update or continue it. Verify the requested change using `gh-readonly` and report the PR URL and completed operation.

## Completion

For Git publication, report the resulting HEAD, completed operation, pushed branch when applicable, and clean or remaining worktree state. For PR/issue operations, report the PR or issue URL and requested change. Keep normal execution commentary minimal.
