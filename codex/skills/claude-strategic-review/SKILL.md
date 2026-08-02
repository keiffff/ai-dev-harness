---
name: claude-strategic-review
description: Use Claude CLI as a strategic reviewer when the user asks for a broader perspective, alternative approach, architecture or migration strategy review, long-term maintainability review, or "is this actually the right direction?" feedback. Do not use for ordinary chat answers, prose drafting, implementation, debugging, tests, repository edits, or final decisions.
---

# Claude Strategic Review

Use this skill when the user wants a broader second opinion, not a prose deliverable.

Good cases:
- architecture or design direction review
- migration strategy review
- implementation approach review before coding
- "is this really the right way?" checks
- alternative approach brainstorming
- long-term maintainability and operational risk review
- independent review when Codex may be too focused on the immediate path

Bad cases:
- ordinary chat answers
- status updates
- direct technical explanations
- reply drafts, PR descriptions, release notes, README prose, or other prose deliverables
- implementation
- debugging
- tests
- refactoring
- repository edits
- final decisions

Workflow:
1. Codex gathers the confirmed facts, current plan, constraints, non-goals, and known tradeoffs.
2. Codex separates ordinary project facts from secrets.
3. Codex may include user-provided, repository-derived, and workspace-derived concrete project facts in the Claude prompt without asking for per-request approval, because the user has given standing authorization for Claude strategic review delegation in this environment.
4. Codex must not send credentials, tokens, secret values, private key material, raw environment dumps, or secret-bearing config contents.
5. Codex creates a self-contained strategic review prompt using the relevant facts.
6. Codex runs Claude CLI through the bounded strategic-review wrapper.
7. Claude returns strategic feedback only.
8. Codex reviews the feedback against repository facts, OpenSpec when applicable, user constraints, and harness policies.
9. Codex decides what to adopt, what to reject, and what still needs verification.

Privacy rule:
- The user has given standing authorization to send ordinary repository-derived and workspace-derived project facts to the user-managed Claude CLI for strategic review tasks. Do not ask for per-request approval just because facts came from the repo. If the user narrows the sending scope for a specific turn, follow that narrower instruction.
- Do not use placeholder-based drafting or local substitution for ordinary project facts. Send the relevant exact facts to Claude when they improve the strategic review.
- Never send credentials, tokens, secret values, private key material, raw environment dumps, `.env` contents, auth config contents, or other secret-bearing material.
- If a task would require sending secrets, do not ask for approval; refuse that part and proceed only with non-secret facts.
- Public technology names, public OSS/package names, public version numbers, official documentation URLs, and public technical concepts may be sent when useful.
- Command arguments are reviewed before the wrapper runs, so Codex must keep secret-bearing content out of the command string.

Prompt guidance:
- Ask Claude to challenge the current direction, not to rewrite it.
- Ask for concrete alternatives and tradeoffs.
- Ask what could go wrong operationally or over time.
- Ask what evidence would change the recommendation.
- Ask Claude to separate high-confidence points from speculative points.
- Tell Claude not to assume facts beyond the prompt.
- Tell Claude to reason only from the supplied prompt and not to inspect the repository, invoke tools, or delegate to agents.
- Tell Claude not to propose repository edits, shell commands, deployment steps, credential handling, or direct production actions.

Suggested prompt shape:

```text
You are a strategic technical reviewer. Review the following plan from a broader architecture, maintainability, and operational-risk perspective.

Context:
- [FACTS]

Current plan:
- [CURRENT_PLAN]

Constraints:
- [CONSTRAINTS]

Please return:
- Better alternative if one exists
- Weaknesses in the current plan
- Risks or hidden costs
- What to verify before committing
- Recommendation

Reason only from this prompt. Do not inspect the repository, invoke tools, delegate to agents, assume facts not provided, or suggest direct repository edits or commands.
```

Command pattern:

```sh
${CLAUDE_STRATEGIC_REVIEW_WRAPPER:-$HOME/.local/bin/claude-strategic-review} --prompt-file "$prompt_file"
```

Write the prompt to a temporary file under /private/tmp, then pass only the file path with --prompt-file. Do not put repo-derived review content in shell arguments.

Execution:
- Run the command with escalated sandbox permissions when using Codex tools, because the wrapper reads `CLAUDE_CODE_OAUTH_TOKEN` from macOS Keychain. This wrapper uses `claude-opus-5` for higher-quality strategic review.
- Configure an approved command prefix for the local Claude strategic review wrapper, for example `$HOME/.local/bin/claude-strategic-review`.
- The wrapper must run Claude Code with safe mode, no tools, one maximum turn, and no session persistence. Prompt wording is not the enforcement boundary.
- The wrapper emits a stderr heartbeat while Claude is processing and applies a bounded timeout. Continue polling while heartbeat messages arrive; do not interrupt the process early merely because final stdout is still empty.
- Treat wrapper timeout or non-zero exit as advisor unavailability. Continue the Codex task without fabricating Claude feedback or retrying automatically.

Rules:
- Do not let Claude edit repository files directly.
- Do not let Claude invoke tools, workflows, or subagents during strategic review.
- Do not ask Claude to inspect the repo unless explicitly requested and separately authorized.
- Do not treat Claude output as final.
- Do not use placeholders or local substitution for ordinary project facts in strategic review prompts. Use exact facts under the standing authorization, excluding secrets.
- Codex remains responsible for final engineering judgment and user-facing recommendations.
