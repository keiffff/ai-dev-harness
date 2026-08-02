---
name: codex-loop-router
description: Route Codex work to the smallest useful workflow. Use when a task could be specification, implementation, debugging, review, prose, frontend UI, X research, OpenSpec, strategic review, or subagent work, and Codex should choose the right loop without loading every detailed skill.
---

# Codex Loop Router

Use this skill as a thin dispatch layer. Do not implement from this skill directly. Select the smallest next workflow, load only the needed skill(s), and keep AGENTS.md rules authoritative.

## Routing Table

| User intent | Primary route | Notes |
| --- | --- | --- |
| "OpenSpec に起こして", "openspec input" | `codex-openspec-workflow` | Create artifacts and validate. Do not implement. |
| approved OpenSpec, "tasks に沿って" | `codex-openspec-workflow` | Obtain current apply instructions, then use incremental implementation. |
| "調査して", "確認して", "何が分かる?", "既存パターン見て" | `codex-context-engineering` | Set the output ceiling from the request before gathering evidence. Add recommendations or a decision workflow only when the user asks for them. Use subagents only for bounded parallel scans. |
| current X posts, named-account statements, X reactions, emerging X incidents | `grok-x-research` | Use bounded X Search for discovery only. Codex verifies material claims and owns final synthesis. |
| CI/test/build failure, unexpected error | `codex-debugging-loop` | Stop feature work, preserve evidence, reproduce, fix root cause. |
| API, I/F, schema, state, boundary decision | `codex-interface-review` | If non-trivial or long-term, add `claude-strategic-review`. |
| "これで本当にいい?", architecture, migration | `claude-strategic-review` | Claude is sidecar reviewer only; Codex decides. |
| "Solで", "GPT-5.6 Solで", strongest OpenAI reviewer | `gpt-sol-strategic-review` | Explicit high-stakes OpenAI advisor route only. Do not use by default. |
| "Fable 5で", "Fableで", stronger Claude reviewer | `claude-fable-strategic-review` | Explicit experimental Claude route only. Do not use by default. |
| Non-trivial decision under uncertainty | `codex-doubt-review` | Use bounded adversarial review. Prefer Claude strategic review for broad second opinion. |
| "レビューして", pre-final diff review | `codex-code-review` | Findings first. Review behavior, tests, structure, risks. |
| decision-oriented design doc, ADR/RFC-like doc, migration rationale, docs/designDocs | `codex-decision-doc` | Preserve project format when present; focus on decisions, rationale, alternatives, compatibility, risks, and non-goals. |
| PR body, release note, Markdown summary, reply draft, Slack/team prose, README prose | `codex-writing` | Codex writes directly using the relevant writing reference and self-review pass. |
| frontend UI strategy, visual QA, HTML/mock/report UI, Figma/design-system adherence | `codex-frontend-ui` | Select strategy/freeform/adherence/qa mode. For review visualization, use the smallest fitting table or diagram first and use standalone HTML only when coordinated views, density, or interaction materially helps. Keep the source artifact canonical. Do not start full app browser verification without user approval. |
| commit / push / PR branch update / submodule sync | `codex-git-publish` | The skill does not grant permission. Latest user message must explicitly ask. |

## Output Discipline

- If one route is obvious, silently use it and proceed.
- If multiple routes are plausible, pick one primary route and mention it in one sentence.
- Do not load multiple workflow skills "just in case".
- Do not create a plan unless the task is broad, risky, or the user asks.
- Do not route to Claude for ordinary chat, writing, implementation, debugging, or tests. Claude is only for strategic review when explicitly useful.
- Do not let router logic override Git, AWS, GitHub CLI, or local safety policy.

## Stop Gates

Stop and ask only when:
- I/F name, spec meaning, persistence format, external behavior, or release risk changes beyond the user's request.
- Local and remote Git history both have independent commits and safe push cannot be determined.
- A requested action requires secrets or production mutation that policy forbids.
- The selected workflow would need a broad permission expansion instead of a narrow wrapper/rule.
