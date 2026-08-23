---
name: codex-git-publish
description: Safely stage, commit, integrate remote changes, push, or update a PR branch through the user-approved Git wrapper. Use only when the user's latest request explicitly asks for a Git mutation such as commit, push, PR branch update, or submodule synchronization. Do not infer mutation permission from implementation work or an earlier request.
---

# Codex Git Publish

Use the current user-visible worktree. This skill defines the publication procedure; it never grants permission by itself.

## Authorization

- Perform commit, merge, push, PR branch update, or submodule sync only when the latest user request explicitly asks for that operation. A request to incorporate the latest base/default branch authorizes merging that named branch into the current branch.
- Rebase only when the user explicitly requests it or when it is the necessary, safe integration step within an explicitly requested push or PR branch update.
- Read-only Git commands are allowed when relevant.
- Do not carry commit, merge, or push authorization into a later user turn.
- Use English commit messages.

## Wrapper Boundary

Use `/Users/kei/.local/bin/git-user-approved` for `add`, `commit`, `merge`, `rebase`, `submodule update`, and `push`. Do not use raw mutation commands.

If the wrapper is blocked by the sandbox, rerun the same wrapper command through the approval flow. Do not switch to another Git path.

## Commit

1. Run `git status --short --branch` and inspect the relevant diff.
2. Stage only intended explicit paths with `git-user-approved add <path...>`.
3. Do not force-add ignored or excluded files. Treat them as local context.
4. Inspect `git diff --cached --stat` and `git diff --cached --check`.
5. Commit with `git-user-approved commit -m "<English subject>"`.

Do not use `git commit -a`, `git commit --amend`, implicit all-file staging, or a temporary clone to create the commit.

## Merge

1. Fetch and verify the named base/default branch, current branch, and worktree state.
2. Use `git-user-approved merge --confirm-user-requested --no-edit <upstream>` for an explicitly requested non-rewriting integration.
3. If the merge conflicts, inspect and resolve only in-scope conflicts, then use `git-user-approved merge --continue`. Use `git-user-approved merge --abort` when the requested integration cannot be completed safely.
4. Run relevant verification after a successful merge.

A merge request authorizes the merge commit created by that integration. It does not authorize unrelated commits, a push, a rebase, or force-updating remote history.

## Push

1. Run `git fetch --prune` after the commit and before relying on remote refs.
2. Compare the current branch, upstream, local HEAD, and remote HEAD.
3. If only the remote has new commits and normal integration is appropriate, use `git-user-approved rebase <upstream>`.
4. Stop when local and remote both contain independent commits or when remote history ownership is unclear.
5. Push only with `git-user-approved push --confirm-user-requested ...`.

Do not create remote-only commits, update Git objects through a connector, or copy changes into another worktree for publication.

## Submodules

Use `git-user-approved submodule update --remote <path>` only when the latest user request explicitly asks to synchronize the submodule. Run subsequent generation commands only after confirming they are verification rather than deployment or publication.

## GitHub Boundary

Use the GitHub connector or `gh-readonly` for PR metadata and diffs. Do not use raw `gh`, `gh api`, or GitHub blob/tree/commit APIs as a Git mutation fallback.

## Completion

Report the resulting HEAD, completed operation, pushed branch when applicable, and clean or remaining worktree state. Keep normal Git execution commentary minimal.
