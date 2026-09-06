---
name: codex-writing
description: Draft or revise prose with the requested facts, Japanese style and medium-specific format; preserve unrequested wording and structure.
---

# Codex Writing

Codex writes prose deliverables directly. Ordinary Q&A needs no writing workflow; decision records use `codex-decision-doc`.

## Editing Contract

Use the supplied facts, audience, medium and tone. Add no unsupported cause, owner, date, commitment or verification claim.

For supplied prose, verify that every change is required by the requested delta or a concrete defect. Preserve unrequested structure, reasoning and tone, and return the complete revised text unless a diff is requested. Do not trade an unwanted rewrite for over-compression. Reorganize the whole document only when the requested change concerns its structure or requires that scope.

Write concrete Japanese with a clear subject, action and consequence. Avoid chained nouns, invented labels, literal English phrasing, stock AI expressions and unnecessary preventive contrasts. Prefer one exact example over repeated abstract advice. Keep implementation details only when the reader needs them.

## Medium

- PR/README: lead with the reader-visible behavior and reason. Follow the repository template; include reproducible verification and material residual risk. Omit file-by-file work logs and session history.
- Slack/team drafts: plain text and short labels; preserve requested bullet nesting. Use no outer fence, Markdown heading, table, blockquote or decorative formatting unless requested.
- Release notes: user-visible changes, briefly.
- UI copy: what happened and what the user can do next; name the affected object and irreversibility for destructive actions.
- Markdown-native copy and review bodies: follow AGENTS.md's copyable-format contract.

Review once for factual support, requested scope, natural Japanese and the target medium. Use [examples](references/japanese-technical-prose.md) only when a phrasing problem needs clarification.
