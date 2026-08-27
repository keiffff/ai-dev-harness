---
name: codex-thread-time-audit
description: Report Codex work times by project, task, and day from turn-level start and completion intervals.
---

# Codex Thread Time Audit

## Core Rule

Report Codex activity at the individual turn interval level. Do not collapse a whole day or thread into one min/max range unless the user explicitly asks for a coarse summary.

The user's goal is usually to see gaps within the same day, so preserve each `startedAt` to `completedAt` interval.

## Deterministic collection

Prefer the local extractor script when local Codex session JSONL files are available:

   ```bash
   python3 scripts/extract_codex_thread_times.py --start 2026-06-09 --end 2026-06-15 --output /path/to/output.html --markdown-output /path/to/output.md
   ```

   This reads `$CODEX_HOME/sessions/**/*.jsonl` and `$CODEX_HOME/archived_sessions/*.jsonl`. Its deterministic responsibility is limited to recording every recognized `task_started` interval and its provenance. It must not drop a turn because a user-message marker is absent or has moved to a new JSONL representation. The default report scope is top-level sessions. Structural subagent files are counted in diagnostics instead of silently disappearing. Use `--session-scope all` only for diagnostic inspection: subagent logs can contain inherited parent history, so Codex must review provenance and duplicates before treating those rows as report activity. Do not classify from `thread_source: subagent` alone because directly operated Desktop/VS Code sessions can carry that stale flag. The script renders a browser-friendly daily HTML report. Keep Markdown only as an optional secondary artifact. Date-only ranges use an 08:00 local-time day boundary by default, so `--start 2026-07-14 --end 2026-07-14` covers `2026-07-14 08:00` through `2026-07-15 08:00`.

   When `--json-output` is used, the extractor also writes a sibling `.diagnostics.json`. Treat that file as evidence, not as an automatic verdict.

## Collection and interpretation boundary

Keep deterministic collection separate from Codex interpretation:

1. The extractor records every recognized task start, completion/abort, session kind, parent thread, and known user-message evidence within the selected scope. A known marker may be `event_msg.user_message`, `response_item.message.user`, both, or absent. Marker absence is diagnostic information and never an exclusion rule.
2. Before finalizing a report, Codex reads the diagnostics and reconciles `rawTaskStarts`, `outputRows`, duplicates, unknown user evidence, unmatched user signals, and completions without a task start.
3. If raw task starts are present but output rows do not reconcile, treat it as an extractor defect. Inspect representative raw event keys and update the collector before reporting.
4. If local JSONL has user/completion evidence but no recognized task start, treat it as possible schema drift. Codex inspects representative raw records and adapts the parser; do not guess a new deterministic rule from a single event name.
5. If local JSONL has no evidence for an expected active period, the extractor cannot prove whether Codex failed to persist it. Compare with `list_threads` / `read_thread` metadata when available. State clearly whether the gap is in the readable local source or in extraction.
6. A `review_required` diagnostic means Codex must inspect the evidence. It does not by itself mean that the report is wrong, and it must not silently reduce the row set.
7. When subagent activity matters, inspect the `all` scope alongside the top-level result. Separate genuine subagent turns from inherited parent history before merging coverage; do not use the raw `all` row count as work time.

## Reporting workflow

1. Use `list_threads` / `read_thread` only as a fallback or to supplement missing titles. Discover thread tools with `tool_search` when thread tools are not already callable.
2. If using `read_thread`, read enough pages to cover the requested period. If the user says "6/8 to now", interpret it in the current local timezone and use concrete dates in the answer.
   - `read_thread` may return only the newest turn by default. Always inspect `page.hasMore` and follow `page.nextCursor` until the oldest returned turn is earlier than the requested start date, or until `hasMore` is false.
   - Do not assume `turnLimit` is honored. If a limit argument is rejected or ignored, fall back to cursor pagination one page at a time.
   - For threads whose `createdAt` is earlier than the requested period but `updatedAt` is inside or after it, still page through them; they can contain relevant turns on the requested dates.
3. For every relevant thread, extract each assistant/task turn that has `startedAt`. Use `completedAt` as the end time. If `completedAt` is null, show `進行中`.
4. Convert timestamps to the user's local timezone. Prefer JST when the user is in Japan or the conversation is Japanese and the environment timezone is Asia/Tokyo. Group report dates by the configured day boundary, defaulting to 08:00 local time; turns before 08:00 belong to the previous report day.
5. Infer the project from thread metadata such as project/workspace/repository path. Use the thread title for the task label.
6. Sort rows by start time, group by report day using the local 08:00 boundary, and output an HTML report by default. Do not use CSV unless the user requests it.
7. Omit chat body content by default. The important fields are time, project, thread title, and duration.

## Output Format

Return a link to the generated HTML file. The HTML should contain one section per day with this table shape:

```markdown
### YYYY-MM-DD

| 時間帯 | プロジェクト | スレッド | 所要 |
|---|---|---|---:|
| 09:04:29 - 09:06:12 | project-a | リリース失敗原因を切り分ける | 1.7分 |
| 08:47:06 - 進行中 | codex-chat | スレッド時刻を抽出 | 進行中 |
```

Duration rules:

- Show minutes to one decimal place.
- For intervals under one minute, still show minutes, for example `0.2分`.
- If the turn is still running, show `進行中` for both end/duration.

## Completeness Notes

Be explicit about the data boundary:

- If only recent threads were listed, say the result is from the readable recent thread set.
- If a date in the requested range has no rows, mention that no matching turn was found in the readable range.
- If pagination or tool output truncation prevents full extraction, say so instead of claiming completeness.
- Distinguish source absence from extraction loss: “no local JSONL evidence was found” and “raw evidence existed but was not rendered” are different results.

## Browser Output

Prefer HTML for user-facing deliverables:

- Use a `.html` output path or `--html-output`.
- Include sticky table headers, horizontal scrolling for long rows, and readable default styling.
- Include project tabs at the top: `すべて` plus one tab per project, with counts, filtering rows client-side without reloading.
- Highlight gaps of 15 minutes or longer as `休憩候補`, computed from previous completed turn coverage to next turn start. In the `すべて` tab, show global gaps. In each project tab, show gaps within that project. Treat these as candidates only; visual review, manual testing, meetings, or non-Codex work may also happen in those gaps.
- Mark overlapping turns explicitly instead of letting them look like normal sequential rows. Use `↳ 同PJ並行` when a turn starts before the previous turn in the same project has completed, and `↳ 並行` when it overlaps only at the global cross-project level.
- Save user-facing files under the current thread's `outputs/` directory when available.
- In the final response, link the HTML first and Markdown second only if Markdown was also requested or useful as a backup.

## Optional Formatter

Use `scripts/extract_codex_thread_times.py` for the full local extraction workflow. If normalized JSON rows are already available, use `scripts/format_thread_time_rows.py` to sort and render a Markdown table.

Expected JSON input:

```json
[
  {
    "project": "project-a",
    "thread": "リリース失敗原因を切り分ける",
    "startedAt": "2026-06-09T00:04:29Z",
    "completedAt": "2026-06-09T00:06:12Z"
  }
]
```
