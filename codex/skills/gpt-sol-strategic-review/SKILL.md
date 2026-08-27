---
name: gpt-sol-strategic-review
description: Use GPT-5.6 Sol only when the user explicitly requests Sol for a high-stakes strategic review. Codex retains repo work and final judgment.
---

# GPT Sol Strategic Review

Use this skill only when the user explicitly asks to try Sol, GPT-5.6 Sol, the strongest OpenAI reviewer, or a high-stakes strategic second opinion.

Good cases:
- "Sol で見て"
- "GPT-5.6 Sol advisor に聞いて"
- architecture, migration, persistence, schema, or long-term maintainability review where the user explicitly wants Sol
- cases where Codex may be too close to the implementation path and an OpenAI-side red-team pass is useful

Bad cases:
- ordinary chat answers
- prose deliverables
- implementation
- debugging
- tests
- refactoring
- repository edits
- Git actions
- final decisions
- routine OpenSpec implementation unless the user specifically asks for Sol

Workflow:
1. Codex gathers confirmed facts, current plan, constraints, non-goals, and tradeoffs.
2. Codex separates ordinary project facts from secrets.
3. Codex creates a self-contained strategic review prompt.
4. Codex writes the prompt to a temporary file under `/private/tmp`.
5. Codex runs the Sol advisor wrapper with `--prompt-file`.
6. Sol returns strategic feedback only.
7. Codex reviews the feedback against repository facts, OpenSpec when applicable, user constraints, and harness policies.
8. Codex decides what to adopt, reject, or verify.

Privacy rule:
- Never send credentials, tokens, secret values, private key material, raw environment dumps, `.env` contents, auth config contents, or other secret-bearing material.
- If the user narrows the sending scope for a specific turn, follow that narrower instruction.
- Do not ask Sol to inspect the repo unless explicitly requested and separately authorized.

Prompt guidance:
- Ask Sol to challenge the current direction, not to rewrite it.
- Ask for concrete alternatives and tradeoffs.
- Ask what could go wrong operationally or over time.
- Ask what evidence would change the recommendation.
- Ask Sol to separate high-confidence points from speculative points.
- Tell Sol not to assume facts beyond the prompt.
- Tell Sol not to propose repository edits, shell commands, deployment steps, credential handling, or direct production actions.

Command pattern:

```sh
${GPT_SOL_STRATEGIC_REVIEW_WRAPPER:-$HOME/.local/bin/gpt-sol-strategic-review} --prompt-file "$prompt_file"
```

Write the prompt to a temporary file under `/private/tmp`, then pass only the file path with `--prompt-file`. Do not put repo-derived review content in shell arguments.

Rules:
- Do not let Sol edit repository files directly.
- Do not treat Sol output as final.
- Codex remains responsible for final engineering judgment and user-facing recommendations.
