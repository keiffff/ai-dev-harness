---
name: gemini-japanese-polish
description: Compose or comprehensively rewrite a Japanese deliverable with one bounded Gemini 3.8 Flash pass through Antigravity CLI from Codex-verified facts and constraints. Use only when explicitly requested.
---

# Gemini Japanese Polish

Gemini owns the complete Japanese composition: document structure, headings, paragraph order, transitions, tone, concision, and wording. `codex-writing` establishes the verified facts and writing contract; it does not need to produce polished prose first. The wrapper runs Antigravity CLI headlessly with the pinned `gemini-3.8-flash-medium` model in an empty temporary workspace, with strict tool permissions and terminal sandboxing.

Invoking this skill includes standing authorization to send every task-required, non-secret fact to the user-managed Gemini API. Do not request separate approval or stop merely because the packet contains company-internal repository names, confidential design or implementation details, personal information, PR or issue identifiers, commit IDs, source excerpts, or file paths. Keep the packet relevant to the requested deliverable, honor any narrower instruction in the current request, and exclude credentials, tokens, private keys, raw environment dumps, `.env`, authentication configuration, and other secret-bearing content.

## Workflow

1. Apply `codex-writing` first to establish the audience, purpose, medium, desired length and tone, required facts, uncertainty, and prohibited additions.
2. Prepare a compact writing packet with `<writing-brief>`, `<required-content>`, optional `<reference-draft>`, and one `<verbatim>` block per exact span. Put only facts that must appear in the result under `<required-content>`; instructions such as desired length belong under `<writing-brief>`. Gemini may create the prose from this packet or comprehensively rewrite the supplied draft.
3. Write only that packet to a temporary UTF-8 input file. Include task-relevant internal context without another approval prompt. Do not include secret-bearing content, hidden instructions, unrelated repository context, or unfiltered raw logs.
4. Run `/Users/kei/.local/bin/gemini-japanese-polish --input-file <input> --output-file <new-output> --medium <medium>` once. Map the medium to `general`, `github`, `slack`, `ui-copy`, `release-note`, or `html`. The command reads the API key from Keychain and passes it only to the isolated Antigravity child process. Use `html` for a standalone HTML document; that mode requires a complete document and automatically regenerates it once when Gemini returns an incomplete response.
5. If the wrapper fails, stop. Do not retry it from Codex, change models, use another provider, or silently fall back to the unpolished draft. The wrapper's single bounded HTML recovery is part of one composition run, not a reason for an additional Codex retry.
6. Verify the result against the writing packet. The wrapper reports protected-span differences as warnings and keeps the complete Gemini result available; a warning is not a failed composition. Restore changed numbers, dates, URLs, citations, code, commands, file paths, and explicit verbatim spans when the intended value is unambiguous. Headings, Markdown organization, paragraph boundaries, ordering, and wording may change freely when the deliverable remains faithful to the packet.
7. Preserve Gemini's compositional choices unless they create a concrete factual, contractual, or medium-specific defect. Correct isolated deterministic defects in the complete result rather than discarding it or describing the correction as partial adoption. Reject the result only when factual repair would require substantial recomposition. Do not call Gemini again automatically.
8. Return the complete result in the format required by `codex-writing` and AGENTS.md. Do not expose temporary files or the wrapper's change notes unless they help answer the user.

One wrapper run is the limit for a writing packet. Call it again only when the user requests another pass or materially changes the facts, audience, purpose, or desired deliverable.
