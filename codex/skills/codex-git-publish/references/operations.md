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

For operations absent from the installed PR/issue CLI, use `gh-user-approved --confirm-user-requested api <endpoint> [args...]` for REST or `api graphql` for GraphQL. Use confirmed repository and issue/PR identifiers in the endpoint or input; API calls do not take the PR/issue CLI's `--repo` option. Verify the relevant installed help or official API schema rather than inventing an operation. Do not ask again for an already requested target and operation solely because this transport is needed. Keep every mutation in an API request within that same authorization. API reads remain on `gh-readonly` within its supported read contract.

For a body update, preserve unrequested content and use `--body-file` for the complete revised body. PR/issue publication does not authorize deployment, workflow dispatch, secret access or unrelated GitHub writes. The API route is for requested PR/issue operations, not a generic mutation exemption. Do not use a connector, raw `gh`, API writes outside the approved wrapper or GitHub blob/tree/commit APIs to bypass the approved wrappers. Authentication failures follow AGENTS.md; do not change accounts or credentials.

Apply the PR Body Delivery step in `../SKILL.md` before submitting this body. When creating a PR, supply its title explicitly with `--title` in the PR's prose language; do not let `--fill` or a commit subject choose the title's language. Japanese PR prose gets a Japanese title, while English PR prose keeps an English title. Include a supplied external ticket identifier for this change only when that ticket has no GitHub linkage; preserve its exact spelling and established format. Do not add GitHub issue/PR numbers or identifiers for tickets already linked to GitHub, and do not invent an identifier. A body-only update does not authorize changing an existing title.

After creating a PR, attach its URL to the current task. Also attach an existing PR when asked to review, update or continue it. Verify the requested change using `gh-readonly` and report the PR URL and completed operation.

### Link A Pull Request To A GitHub Issue

1. Resolve the requested PR and issue from the user's references, current task attachments and repository, and confirm their identities with `gh-readonly pr view` and `gh-readonly issue view`. Use `--json id,url` for node IDs and `--json closingIssuesReferences` on the PR to check whether the requested issue is already linked. Resolve an explicit reference from existing context before asking for its number.
2. For the requested Development link, use `gh-user-approved --confirm-user-requested api graphql` with GitHub's [`addCloseIssueReferences` mutation](https://docs.github.com/en/graphql/reference/issues#addcloseissuereferences), passing the confirmed issue node ID as `issueId` and PR node ID as an element of `pullRequestIds`. A `Refs` line in the PR body or a mention in a comment does not complete a Development link. Preserve the existing PR body for a link-only request. This relationship may close the issue when merged into the default branch. If the user asked for a mention only or explicitly excludes automatic closure, honor that scope.
3. Treat the Development link as complete only after `gh-readonly pr view --json closingIssuesReferences` returns the exact issue URL for the requested PR. If this was already true before the mutation, report the existing link without creating it again. Report the PR and issue URLs. Handle a GraphQL `errors` response as a failed or partial operation even if HTTP succeeded.

### Create Or Extend A Native Pull Request Stack

1. Resolve the repository, target base and PR layers from the request and current branch and PR state. For new layers, use the ordinary approved PR creation procedure, set the bottom PR's base to the intended target, and set each upper PR's base to the immediately lower PR's head. For existing PRs, verify the base/head chain and native stack membership before writing. A request to link an existing chain does not authorize rewriting branch history or moving members out of another stack.
2. With the PRs created and their chain verified, use `gh-user-approved --confirm-user-requested api` and the [GitHub stacks REST API](https://docs.github.com/en/rest/pulls/stacks): `POST repos/OWNER/REPO/stacks` with JSON `pull_requests` ordered bottom to top. For a requested extension, use `POST repos/OWNER/REPO/stacks/STACK_NUMBER/add` with only the new layers in order. If the requested stack already exists, reuse it. A base/head chain and links in PR descriptions do not register a stack. Use this API route through the existing wrapper without installing a CLI extension.
3. Treat the request as complete only when `gh-readonly api` on `GET repos/OWNER/REPO/stacks/STACK_NUMBER` returns a GitHub stack with the requested PRs in order. Report the stack number and member PR URLs. If a write returns an uncertain result, reread the stack before retrying. If native stacks are unavailable on the confirmed host, report the specific blocker and any PRs already created.
