---
name: codex-writing
description: Create or substantially revise prose deliverables. Excludes brief proofreading and wording-only edits unless explicitly invoked.
---

# Codex Writing

Codex writes prose deliverables directly. Use this skill for new deliverables or substantial revisions, not ordinary Q&A, brief message proofreading or wording-only edits unless explicitly invoked. Handle those local edits with the common Japanese output instructions; decision records use `codex-decision-doc`. A standalone HTML report routed through `claude-html-report` is the bounded exception for composition: Claude composes the whole artifact from Codex's verified fact packet, while Codex retains factual and final-output verification. When the user explicitly invokes `gemini-japanese-polish`, Codex supplies a verified writing packet and Gemini owns the complete Japanese composition, including structure and wording. Codex retains factual constraints and final verification in both workflows.

## Editing Contract

Use the supplied facts, audience, medium and tone. Add no unsupported cause, owner, date, commitment or verification claim.

Use the conversation's established reader and purpose: what the reader needs to understand, decide or do, and whether the sender is reporting, proposing or acknowledging. Lead with that point, then give the reasons and details needed to understand it. Introduce an unfamiliar object or term before relying on it; omit explanations the intended reader already knows. Keep observations, estimates, proposals and agreed actions distinguishable without adding stock labels or generic caveats.

For supplied prose, verify that every change is required by the requested delta or a concrete defect. Preserve unrequested structure, reasoning and tone, and return the complete revised text unless a diff is requested. Do not trade an unwanted rewrite for over-compression. Reorganize the whole document only when the requested change concerns its structure or requires that scope.

Write concrete Japanese with a clear subject, action and consequence. Avoid chained nouns, invented labels, literal English phrasing, stock AI expressions and unnecessary preventive contrasts. Prefer one exact example over repeated abstract advice. Keep implementation details only when the reader needs them.

## Reference Examples

Prefer the user's supplied or explicitly accepted writing for the same purpose and medium. For a new deliverable or substantial restructuring without such a sample, read only the matching section of [Japanese prose examples](references/japanese-technical-prose.md). Follow its information order and level of detail, not its incidental facts or a fixed template. Existing conversation context is sufficient; do not start a history search or ask for another writing brief on every task.

## Medium

- PR/README: lead with the reader-visible behavior and reason. Follow the repository template; include reproducible verification and material residual risk. Omit file-by-file work logs and session history.
- Slack/team drafts: follow AGENTS.md's plain-form Japanese and nested-bullet defaults. Keep a short acknowledgment short; preserve the voice of supplied prose when editing. Use no outer fence, Markdown heading, table, blockquote or decorative formatting unless requested.
- Release notes: user-visible changes, briefly.
- UI copy: what happened and what the user can do next; name the affected object and irreversibility for destructive actions.
- Markdown-native copy and review bodies: follow AGENTS.md's copyable-format contract.

Review once against the supplied facts, requested scope and relevant example: can the reader identify the main point and understand it without unexplained terms? This is an editing pass, not independent proof of quality. When changing this skill, compare old and revised outputs on the same representative requests and user corrections; assess meaning preservation, comprehension and required rework, not the model's self-rating. Do not add this comparison as a step to every writing task.
