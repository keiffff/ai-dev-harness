# Team Update Style

Use this reference for Slack, chat, PdM updates, incident notes, and short team-facing summaries.

The output should be ready to paste unless the user explicitly asks for Markdown.

## Default Format

- No Markdown headings.
- No backticks unless the exact identifier is necessary.
- No bold markers.
- No tables.
- No fenced code blocks.
- No blockquotes unless the user asks for a quoted passage.
- Use short labels and plain bullets.
- When the user asks for hierarchical bullets, keep the nesting visible and do not flatten the items into one level.

Example labels:

- 状況
- 確認できたこと
- 見立て
- 対応案
- 確認したいこと

## Content Rules

- Lead with the current state and requested action.
- Separate confirmed facts from interpretation.
- Do not overstate probability. Use `可能性が高い` only when evidence supports it.
- If a customer, PdM, or non-engineer is the reader, explain system terms by outcome, not internal component names.
- Include IDs only when the recipient can use them.
- Do not include internal trial-and-error, command details, or failed local attempts.

## Tone

- Keep it calm and concrete.
- Do not apologize on behalf of a system unless the user asks for a customer-facing apology.
- Do not add commitments, dates, owners, or next actions that were not provided.
- Prefer `確認したいです` over vague requests like `ご確認お願いします` when a specific decision is needed.

## Final Review

Before returning the update, check:

- Can the reader tell what happened?
- Can the reader tell what is confirmed and what is a hypothesis?
- Is the requested next action explicit?
- Is there any engineering detail that does not help the recipient decide?
