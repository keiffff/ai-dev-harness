---
name: claude-fable-strategic-review
description: Use Claude Fable 5 as an explicit experimental strategic reviewer when the user specifically asks to try Fable, Fable 5, the strongest Claude reviewer, or a deeper long-horizon strategic review. Do not use by default, for ordinary strategic review, chat answers, prose drafting, implementation, debugging, tests, repository edits, or final decisions.
---

# Claude Fable Strategic Review

Use this skill only when the user explicitly asks to try Fable 5 or a stronger-than-usual Claude strategic review. The default strategic review route remains `claude-strategic-review`.

Good cases:
- "Fable 5 で strategic review して"
- "Fable で副査して"
- "今回は強い Claude reviewer で見たい"
- architecture, migration, or long-horizon maintainability review where the user explicitly wants Fable

Escalation candidates:
- irreversible schema, migration, or persistence decisions
- design choices that cross service or team boundaries
- OpenSpec proposal/design direction when the core assumption is uncertain
- architecture decisions with high long-term maintenance cost
- repeated disagreement between Codex review and Claude strategic review
- cases where the cost of a wrong decision is materially higher than the cost of a Fable review

Bad cases:
- ordinary chat answers
- prose deliverables
- implementation
- debugging
- tests
- refactoring
- repository edits
- final decisions
- normal OpenSpec post-implementation review unless the user specifically asks for Fable

Workflow:
1. Codex gathers confirmed facts, current plan, constraints, non-goals, and tradeoffs.
2. Codex separates ordinary project facts from secrets.
3. Codex may include user-provided, repository-derived, and workspace-derived concrete project facts under the existing strategic-review authorization, excluding secrets.
4. Codex creates a self-contained strategic review prompt.
5. Codex runs the Fable wrapper.
6. Claude Fable returns strategic feedback only.
7. Codex reviews the feedback against repository facts, OpenSpec when applicable, user constraints, and harness policies.
8. Codex decides what to adopt, reject, or verify.

Privacy rule:
- Never send credentials, tokens, secret values, private key material, raw environment dumps, `.env` contents, auth config contents, or other secret-bearing material.
- If the user narrows the sending scope for a specific turn, follow that narrower instruction.
- Do not ask Claude to inspect the repo unless explicitly requested and separately authorized.

Prompt guidance:
- Ask Fable to challenge the current direction, not to rewrite it.
- Ask for concrete alternatives and tradeoffs.
- Ask what could go wrong operationally or over time.
- Ask what evidence would change the recommendation.
- Ask Fable to separate high-confidence points from speculative points.
- Tell Fable not to assume facts beyond the prompt.
- Tell Fable not to propose repository edits, shell commands, deployment steps, credential handling, or direct production actions.
- Mention that Fable 5 may be more expensive and should focus on high-value strategic issues.

Command pattern:

```sh
${CLAUDE_FABLE_STRATEGIC_REVIEW_WRAPPER:-$HOME/.local/bin/claude-fable-strategic-review} --prompt-file "$prompt_file"
```

Write the prompt to a temporary file under /private/tmp, then pass only the file path with --prompt-file. Do not put repo-derived review content in shell arguments.

Execution:
- Run the command with escalated sandbox permissions when using Codex tools, because the wrapper reads `CLAUDE_CODE_OAUTH_TOKEN` from macOS Keychain.
- Configure an approved command prefix for the local Claude Fable strategic review wrapper, for example `$HOME/.local/bin/claude-fable-strategic-review`.

Rules:
- Do not let Claude edit repository files directly.
- Do not treat Claude output as final.
- Codex remains responsible for final engineering judgment and user-facing recommendations.
