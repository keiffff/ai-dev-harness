---
name: claude-writing
description: Slack報告・確認依頼、issue・PR本文などの文章成果物の作成・推敲・訂正をClaudeに一任する。短い文面の校正も含み、通常の会話回答は除く。
---

# Claude Writing

Claude alone owns reader-facing prose: information selection, structure, composition, source checking and every editorial revision. Codex transports original requests, source files and tool records, then delivers the saved result unchanged. Ordinary conversation stays in main; HTML uses `claude-html-report`, review findings use `codex-code-review`, and decision records retain `codex-decision-doc`'s content contract.

## Transfer, Write, Deliver

1. Reuse the original request, relevant conversation and original evidence files. Supply the actual final diff and verification tool records for an issue/PR body. Preserve provenance between observations, user statements and earlier assistant interpretations. Do not replace those materials with a Codex summary, conclusion, required-points list, caveat policy or selected edit plan. No Codex-authored draft for Claude to preserve.
2. Run the [one-call source workflow](references/source-workflow.md). Claude receives the [writer contract](references/writer-contract.md), original request and evidence together. Claude decides what belongs in the body and what belongs in sender notes. An existing draft is supplied only for a requested revision; every change is required by the requested delta. Do not trade an unwanted rewrite for over-compression.
3. Deliver the saved body and, if useful, Claude's separate sender notes without rewriting either. Codex does not approve, reject, add, delete, summarize, fact-correct or reformat passages. No second model check, note filter or Codex final polish. Add only AGENTS.md's outer presentation fence where required, outside the saved body. A new user correction goes back to Claude with the original draft and sources; it does not reopen Codex editing.

If Claude needs evidence, transport its specific question and retrieve an authorized original source when available. Return the raw evidence to Claude; do not decide a substitute conclusion or turn an observation into an editorial instruction. On a CLI/authentication failure, report that execution failure outside the copy. No automatic retry, provider switch or fallback writer.

Do not expand a shared observation into a new writing request. Publication still requires the current explicit user request and the existing Git/cloud routes. Content ownership does not grant operational authority. A saved body is an authored artifact, not independent proof of its facts.

When changing this skill, use actual requests and compare complete outputs and time, including repairs. Keep private conversations and case identifiers out of shared instructions and fixtures.
