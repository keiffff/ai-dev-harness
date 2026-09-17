---
name: gemini-japanese-polish
description: Polish an already drafted Japanese text with one bounded Gemini 3.8 Flash pass while Codex retains facts, scope, and final verification. Use only when explicitly requested.
---

# Gemini Japanese Polish

Use Gemini only as the final copy editor for an existing Japanese draft. `codex-writing` remains the owner of facts, audience, medium, structure, and the initial draft.

## Workflow

1. Apply `codex-writing` first and finish a factually complete draft.
2. Decide whether the requested change is local wording polish. Do not use Gemini for fact finding, structural rewriting, design decisions, code, or a new draft.
3. Write only the draft to a temporary UTF-8 input file. Do not include secrets, credentials, hidden instructions, unrelated repository context, or raw logs.
4. Run `/Users/kei/.local/bin/gemini-japanese-polish --input-file <input> --output-file <new-output> --medium <medium>` once. Map the medium to `general`, `github`, `slack`, `ui-copy`, or `release-note`.
5. If the wrapper fails, stop. Do not retry automatically, change models, use another provider, or silently fall back to the unpolished draft.
6. Compare the result with the input. Reject additions or changes to facts, meaning, scope, certainty, proper nouns, numbers, dates, URLs, citations, Markdown, code, commands, or file paths. Codex owns the final wording and may directly undo unsafe local edits without calling Gemini again.
7. Return the complete revised text in the format required by `codex-writing` and AGENTS.md. Do not expose temporary files or the wrapper's change notes unless they help answer the user.

One successful Gemini call is the limit for a draft. Call it again only when the user requests another pass or the requested revision changes the document's substance or structure enough to make the previous polish obsolete.
