---
name: codex-writing
description: Draft or revise PR text, summaries, team updates, release notes, README prose, replies, announcements, and UI copy. Use codex-decision-doc for decision records.
---

# Codex Writing

Use this skill when the user asks for a prose deliverable. Codex writes the final text directly; do not delegate drafting to Claude.

Good cases:
- reply drafts
- Markdown summaries intended as deliverables
- Slack or chat sharing drafts
- Japanese technical documents
- README prose rewrites
- PR descriptions
- release notes
- announcements
- user-facing copy
- UI copy, error messages, empty states, confirmation dialogs, and notifications
- long-form editing

Bad cases:
- ordinary chat answers
- status updates
- direct technical explanations
- quick Q&A
- implementation
- debugging
- tests
- refactoring
- security-sensitive changes
- repository edits unrelated to prose
- decision-oriented design docs, ADR/RFC-like docs, migration rationale, or docs under docs/designDocs; use `codex-decision-doc` instead

## Workflow

1. Gather the facts, diffs, constraints, audience, target medium, and desired tone.
2. Separate confirmed facts from assumptions. Do not invent dates, owners, commitments, checks, or root causes.
3. Load only the writing reference needed for the deliverable:
   - Japanese technical prose, technical articles, or explanatory Markdown: `references/japanese-technical-prose.md`
   - PR descriptions: `references/pr-body-style.md`
   - Implementation plans, OpenSpec design text, or non-decision technical notes: `references/design-doc-style.md`
   - Slack, chat, PdM, or team sharing drafts: `references/team-update-style.md`
4. Draft the text directly in Codex.
5. For supplied prose, compare the draft with the source and verify that every change is required by the requested delta. Preserve unrequested structure, tone, causal detail, and useful wording.
6. Run a self-review pass against the selected reference before returning.
7. Remove any claim not supported by the user request, repository facts, or explicitly stated assumptions.

## Core Writing Rules

- Assume the reader has not seen the implementation session.
- Put the reader-visible result first, then add necessary context.
- Do not include internal work logs, hypotheses, failed attempts, or tool execution details.
- Avoid vague words such as `対応`, `修正`, `改善`, `考慮`, `反映`, `〜側`, `〜周り`, `〜する形`, `該当箇所`, and `既存処理` unless the sentence names the concrete behavior, screen, file, or user action.
- Avoid compressed Japanese, chained nouns, literal English translations, and vague demonstratives.
- Do not replace a concrete explanation with an English-derived abstract noun. Words such as `正本`, `投影`, `測定境界`, `比較終端`, and `外部契約` are not shortcuts for explaining who does what and how. Use them only when they are established terms for the intended reader.
- Before introducing a new label, heading, or coined term, name what it refers to and whether it is a condition, state, event, value, record, purpose, or means. If the referent cannot be written plainly, do not introduce the label.
- Do not use AI-like filler, ornamental structure, or generic claims when the document needs concrete technical meaning.
- Keep only information the reader needs to understand the result or decide the next action.
- When revising supplied prose, change only the requested delta or a concrete defect. Do not trade an unwanted rewrite for over-compression that removes the user's reasoning.

## Format Rules

- PR descriptions: start with reviewer-visible behavior and the reason the PR exists. Explain implementation at the level of behavior, design choice, review-relevant scope, residual risk, and reproducible checks.
- PR descriptions: do not write a file-by-file change log unless the file itself is the reviewer-facing subject.
- PR descriptions: treat implementation touchpoints found in diffs as evidence for Codex, not as output candidates.
- PR descriptions: do not include internal chat history, discarded approaches, temporary local issues, or "did not do X" notes unless they change reviewer expectations, residual risk, or required follow-up.
- Release notes: describe only user-visible changes; omit filenames, functions, tests, architecture, and implementation strategy; keep items short and scannable.
- UI copy: say what happened and what the user can do next; avoid unnecessary technical terms; for destructive actions, name the object and clearly state that the action cannot be undone.
- Reply drafts: match the requested audience and tone; do not add commitments, dates, or facts that were not provided.
- Slack or chat sharing drafts: use plain text with short section labels and simple bullet lists. Preserve requested bullet nesting instead of flattening it. Do not wrap the draft in an outer fenced code block, and do not use Markdown headings (`#`, `##`, `###`), code formatting backticks, bold markers (`**`), tables, or blockquotes unless the user explicitly requests Markdown.
- Markdown deliverables: use Markdown only when the user explicitly asks for Markdown, PR text, GitHub issue text, README prose, or another Markdown-native output.

## Reference Use

- Use references as editing constraints, not as text to quote.
- Do not load every reference by default. Pick the smallest set that matches the deliverable.
- When a deliverable spans multiple forms, load only the relevant combination. Example: a PR description for a design-heavy change may use `pr-body-style.md` and `design-doc-style.md`.

## Final Self-Review

Before returning, check:

- Is every concrete claim supported?
- Does the text expose only the details the reader needs?
- Do new labels, headings, and coined terms have a clear referent and role before they are used?
- Are file names, identifiers, and implementation layers present only when they matter?
- Are unchanged items omitted from changed-item lists?
- Are `確認` or verification sections limited to reproducible checks?
- Does the text avoid generic AI filler and decorative structure?
- Can every abstract noun and compressed label be replaced with a clearer subject and verb? If so, replace it unless the term is established for the reader.
- Can every changed or removed part be traced to the user's requested delta or a concrete defect?
