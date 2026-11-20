---
name: codex-git-publish
description: Perform explicitly requested Git publication and GitHub PR/issue operations through approved wrappers; never infer write authority from review or drafting requests.
---

# Codex Git Publish

Use the current user-visible worktree. This skill defines the publication procedure; it never grants permission by itself.

## Authorization

- Perform branch creation or switching, commit, merge, push, PR branch update, or submodule sync only when the latest user request explicitly asks for that operation. An explicit PR creation request also authorizes the working-branch creation or switching, commit of the requested changes, and push to the PR head branch needed to create that PR, without separate confirmation. Honor an explicit no-commit or no-push instruction. This does not authorize unrelated changes, merge, or deployment. Direct shared-branch pushes normally need explicit permission for that operation. If the user has configured standing permission in the repository’s local AGENTS.md for a specific remote and branch, a latest commit/push request includes a normal push to that destination without another question. Verify the actual remote and branch; never extend this permission to another repository or destination. A request to incorporate the latest base/default branch authorizes merging that named branch into the current branch.
- Rebase only when explicitly requested or as the necessary integration within an authorized push or PR branch update. An explicitly requested push or PR branch update, including the push needed for explicitly requested PR creation, authorizes rebasing unpublished local commits onto the confirmed latest upstream without separate confirmation, even when both sides have new commits. Honor explicit no-rebase instructions. For this push integration, stop on conflicts, a required rewrite of published history or unclear remote history ownership; divergence alone is not a reason to stop. This does not authorize an unrequested merge or force-push.
- Read-only Git commands are allowed when relevant.
- Perform PR/issue operations only when the latest user request explicitly asks for the affected operation and target. Review, advice and drafting alone do not authorize posting or editing a PR or issue. Do not infer PR/issue creation from a commit/push request. Only an explicit PR creation request includes its necessary branch preparation, commit and push; other PR/issue requests, review and drafting do not. A PR request does not authorize an issue write, or vice versa.
- Do not carry one-off Git or PR/issue mutation authorization into a later user turn. User-configured repository standing permission remains effective until revoked or changed; it never replaces the latest commit/push request.
- Use English commit messages. This applies only to commits; PR titles follow the PR's prose language and the repository's established convention. Use Japanese for a Japanese PR and English for an English PR, unless the user specifies otherwise. Do not reuse an English commit subject as the PR title merely because it is available.

## Wrapper Boundary

Use `/Users/kei/.local/bin/git-user-approved` for `add`, `commit`, `merge`, `rebase`, `switch`, `submodule update`, and `push`. Do not use raw mutation commands.

Use `/Users/kei/.local/bin/gh-user-approved --confirm-user-requested pr|issue|api <command-or-endpoint> [args...]` for explicitly requested PR/issue operations. It accepts the entire `gh pr` and `gh issue` command families and `gh api` for those operations, passing arguments unchanged; do not add endpoint, subcommand, method or field allowlists. Use the API route for REST or GraphQL operations absent from the installed PR/issue CLI, including parent/sub-issue links. An already requested target and operation do not need another approval merely because the implementation uses the API. The confirmation flag records Codex's authority check, not independent proof of user consent. Match every API operation, including every mutation in a GraphQL request, to the latest user request. This is not permission for unrelated API writes, workflow dispatch, deployment, secrets or authentication operations.

If the wrapper is blocked by the sandbox, rerun the same wrapper command through the approval flow. Do not switch to another Git path.

When the Git directory is already known to sit outside the writable sandbox, use the required approval flow on the first wrapper call. Do not run an identical sandboxed attempt merely to reproduce the known permission failure.

## PR Body Delivery

For a new or revised issue/PR body, including a draft-only delivery, use `claude-writing`. Pass the original request, final diff and actual verification records. Claude alone composes, checks and revises the text; Codex does not provide a conclusion, selected edits or caveat requirements, and does not run another draft check after Claude returns.

Submit or deliver the saved body unchanged. Keep Claude's separate sender notes outside the issue/PR copy. A user-requested revision goes back to Claude with the existing draft and original sources. An unchanged Claude-authored body needs no duplicate call. Keep composition and the GitHub write in separate calls; publication authority still follows the explicit current request.

## Operation-Specific Guidance

For branch creation/switching, merge, submodule synchronization or PR/issue operations, read only the relevant section of [operations](references/operations.md). For PR creation, also use the branch section and the commit/push procedure below. Ordinary commit/push needs no additional reference.

## Commit

1. Run `git status --short --branch` and inspect the actual changes, including already staged hunks. For PR creation or update, also inspect the full diff from the verified PR base to the proposed head; a clean worktree or the latest commit alone cannot establish the PR contents.
2. Separate the product change from verification working files using the original request, creation history and actual consumers. For each added file or hunk, identify the continuing requested responsibility that would be lost if it were omitted. A measurement or before/after comparison created only to validate this change stays private; moving it under docs or calling it a reusable tool does not establish a delivery requirement. Keep concrete regression coverage for supported behavior, even when a test checks source text. Use a one-off comparison, rather than a permanent second copy of configuration, for assertions that an extraction preserved today's complete command/step list or lockfile versions. A general instruction to preserve behavior does not turn every internal literal into an accepted contract; keep tests of selection, failure propagation and externally required values. A test newly added during this task remains part of the candidate diff even if committed or registered in CI; compare with the base rather than treating that registration as an accepted contract. Within mixed files retain behavioral cases and remove only one-off material with its dedicated references. Preserve pre-existing accepted tests and unrelated local work. Requested diagnostic tools, maintained tests, build/configuration and required documentation remain deliverables.
3. Stage only the selected explicit paths with `git-user-approved add <path...>`. Do not force-add ignored or excluded files. Treat them as local context.
4. Inspect the full `git diff --cached`, then `git diff --cached --check`, against that selection. If a one-off artifact is already in the PR history, an authorized branch update can remove it in a follow-up commit; do not infer permission to rewrite history.
5. Commit with `git-user-approved commit -m "<English subject>"`.

Do not use `git commit -a`, implicit all-file staging, or a temporary clone to create the commit. Amend only when the latest user request explicitly authorizes rewriting the affected commit: stage only its intended corrections, then use `git-user-approved commit --confirm-user-requested --amend --no-edit`. An ordinary commit/push request does not authorize amend. For a requested rewrite of published history, verify the remote head and push with an explicit `--force-with-lease=refs/heads/<branch>:<confirmed-remote-sha>`; do not use a plain force-push.

## Push

1. Run `git fetch --prune` after the commit and before relying on remote refs.
2. Compare the current branch, upstream, local HEAD, and remote HEAD.
3. When integration is needed, inspect the local-only commits against the fetched remote refs. If rebasing rewrites only unpublished local commits onto the confirmed upstream, use `git-user-approved rebase <upstream>` without separate confirmation, including when both sides have new commits. Honor an explicit no-rebase instruction.
4. Stop on conflicts, a required rewrite of published history or unclear remote history ownership. Divergence alone is not a reason to stop. Do not substitute an unrequested merge or force-push.
5. Push only with `git-user-approved push --confirm-user-requested ...`.

Do not create remote-only commits, update Git objects through a connector, or copy changes into another worktree for publication.

## Completion

For Git publication, report the resulting HEAD, completed operation, pushed branch when applicable, and clean or remaining worktree state. For PR/issue operations, report the PR or issue URL and requested change. Keep normal execution commentary minimal.
