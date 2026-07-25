---
name: codex-decision-doc
description: Use when drafting or revising design docs that should capture decisions, rationale, tradeoffs, compatibility, risks, non-goals, and open questions rather than implementation details. Prefer user-provided or repository-local design doc formats when present, and use the fallback structure only when no project format exists. Use for decision-oriented design docs, ADR-like docs, RFC-like docs, architecture notes, migration rationale, and docs under docs/designDocs. Do not use for PR bodies, release notes, README prose, Slack/team drafts, detailed implementation specs, OpenSpec artifacts, or ordinary chat answers.
---

# Codex Decision Doc

Use this skill for design docs whose main value is decision context, not code-level detail.

## Purpose

A decision doc records:
- why a change is needed;
- what decision was made;
- what constraints shaped the decision;
- what alternatives were rejected;
- what compatibility and risk tradeoffs remain;
- what future readers should not have to rediscover from code or chat history.

It is not a detailed design spec, implementation log, PR body, file-by-file explanation, or OpenSpec artifact.

## Workflow

1. Gather the target path, audience, existing docs in the same directory, user-provided facts, relevant repo facts, and any explicit template.
2. Check whether the repository or target directory already has a design doc template or recurring structure.
3. Preserve the project format when one exists, but fill it with decision-oriented content.
4. If no project format exists, use the fallback Japanese structure below.
5. Draft in Japanese by default.
6. Self-review against `references/style.md` before returning or editing the file.

## Output Structure

Prefer structure in this order:
1. User-provided template or headings.
2. Existing design docs in the same directory.
3. Repository-level design doc convention.
4. This skill's fallback structure.

Do not override a project-specific format just to use this skill's fallback headings.

When using an existing format, preserve its headings and order where reasonable, but fill each section with decision-oriented content rather than implementation inventory.

## Fallback Structure

Use this only when no project format exists:

```md
# <判断を表すタイトル>

## 要約
## 背景
## 問題
## 判断
## 判断理由
## 検討した代替案
## 互換性
## 影響と残るリスク
## 検証観点
## 対象外
## 未決事項
```

## Language

Write the final document in Japanese by default.

Use English only when:
- the user explicitly asks for English;
- the repository template/headings are already English and preserving them is more important than translating;
- a technical identifier, API field, command, file path, or quoted source text is English.

Even when headings are preserved in English, write the body text in Japanese unless the user asks otherwise.

## Hard Rules

- Write about decisions, not implementation inventory.
- Do not list changed files, functions, classes, schemas, or tests unless needed to explain ownership, contract, or boundary.
- Do not turn the document into a detailed design document.
- Do not write work logs, failed attempts, local setup issues, or chat history.
- Do not invent domain terminology. Use repository terms or literal field names.
- Before introducing a new label, state name, condition name, or summary heading, write the concrete referent first. Keep condition, state, event, value, record, purpose, and means separate; if one label would cover multiple roles, split it or write the concrete description instead.
- Do not include fallback or backward compatibility just because it is possible. Explain whether compatibility is required and why.
- If source facts are insufficient to explain a decision, ask for the missing decision context instead of filling with generic prose.
- Every alternative must include a reason it was rejected.
- Every compatibility claim must name the affected existing data, API, client, test, or workflow.
- Do not lead with internal component names, abbreviations, or implementation role names before explaining the user-visible or operational flow they belong to.
- Do not add abstract organizer sections such as `論点`, `判断すること`, `後続仕様`, or `対応方針` unless the repository template requires them. Use headings that name the actual flow, contract, state, or responsibility the reader needs to understand.
- Use tables only when comparing multiple subjects on the same axes. Do not use a table to repeat that every row is part of the same change.

## Reference

Read `references/style.md` before drafting or revising a decision doc.
