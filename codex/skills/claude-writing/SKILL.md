---
name: claude-writing
description: Slack報告・確認依頼、issue・PR本文などの文章成果物の作成・推敲・訂正をClaudeに一任する。短い文面の校正も含み、通常の会話回答は除く。
---

# Claude Writing

Claude alone owns reader-facing prose: information selection, structure, composition, source checking and every editorial revision. Codex transports original requests, source files and tool records, then delivers the saved result unchanged. Ordinary conversation stays in main; HTML uses `claude-html-report`, review findings use `codex-code-review`, and decision records retain `codex-decision-doc`'s content contract.

## Transfer, Write, Deliver

1. Select existing original evidence files. Saved user requests and their completed conversation turns are attached automatically when available in the app's saved history, ending before the current request. Assistant responses remain interpretations, not user drafts or factual authority. Do not transcribe the conversation, earlier assistant explanations or a new source memo. For an issue/PR body, use the existing final diff and verification records. Preserve observations versus interpretations without writing a conclusion, required-points list, caveat policy, selected edit plan or Codex draft.
2. Invoke this skill's `scripts/compose_from_sources.py --medium <medium> --source-file <existing-source> --print-body` once. Repeat `--source-file` for other existing evidence, or omit it when the request needs none. The saved request, private work directory and output path are automatic. Claude receives the writer contract in the script; Codex need not reread it or the detailed workflow to make a normal call. For a user-requested revision, add `--draft-file <existing-draft>`; every change is required by the requested delta. Do not trade an unwanted rewrite for over-compression. If the app has no saved request, supply an existing verbatim `--request-file`; do not write a briefing document. See [source workflow](references/source-workflow.md) only for explicit output paths, legacy callers or execution diagnostics.
3. Present stdout directly, preserving its complete text. Sender notes are returned separately on stderr, and execution records are saved automatically. Do not read the body or notes back from files, generate a separate writing-completion memo, or run a second review before delivery. Keep any necessary broader task-state update brief and tied to its actual change. Codex does not approve, reject, add, delete, summarize, fact-correct or reformat passages. Add only AGENTS.md's outer presentation fence where required, outside the body. A new user correction goes back to Claude with the original draft and sources; it does not reopen Codex editing.

If Claude needs evidence, transport its specific question and retrieve an authorized original source when available. Return the raw evidence to Claude; do not decide a substitute conclusion or turn an observation into an editorial instruction. On a CLI/authentication failure, report that execution failure outside the copy. No automatic retry, provider switch or fallback writer.

Do not expand a shared observation into a new writing request. Publication still requires the current explicit user request and the existing Git/cloud routes. Content ownership does not grant operational authority. A saved body is an authored artifact, not independent proof of its facts.

When changing this skill, use actual requests and compare complete outputs and time, including repairs. Keep private conversations and case identifiers out of shared instructions and fixtures.
