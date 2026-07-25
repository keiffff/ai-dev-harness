---
name: codex-thread-time-audit
description: Extract and report Codex thread work times by project, thread, and day. Use when the user asks for Codex chat/thread history times, work activity by project, start/end times, daily work logs, or wants to know when they were operating across Codex projects. Prefer turn-level startedAt/completedAt intervals instead of thread-level createdAt/updatedAt summaries.
---

# Codex Thread Time Audit

## Core Rule

Report Codex activity at the individual turn interval level. Do not collapse a whole day or thread into one min/max range unless the user explicitly asks for a coarse summary.

The user's goal is usually to see gaps within the same day, so preserve each `startedAt` to `completedAt` interval.

## Workflow

1. Prefer the local extractor script when local Codex session JSONL files are available:

   ```bash
   python3 scripts/extract_codex_thread_times.py --start 2026-06-09 --end 2026-06-15 --output /path/to/output.html --markdown-output /path/to/output.md
   ```

   This reads `$CODEX_HOME/sessions/**/*.jsonl` and `$CODEX_HOME/archived_sessions/*.jsonl`, extracts only user-owned top-level turns, excludes `thread_source: subagent`, and renders a browser-friendly daily HTML report. Keep Markdown only as an optional secondary artifact. Date-only ranges use an 08:00 local-time day boundary by default, so `--start 2026-07-14 --end 2026-07-14` covers `2026-07-14 08:00` through `2026-07-15 08:00`.

2. Use `list_threads` / `read_thread` only as a fallback or to supplement missing titles. Discover thread tools with `tool_search` when thread tools are not already callable.
3. If using `read_thread`, read enough pages to cover the requested period. If the user says "6/8 to now", interpret it in the current local timezone and use concrete dates in the answer.
   - `read_thread` may return only the newest turn by default. Always inspect `page.hasMore` and follow `page.nextCursor` until the oldest returned turn is earlier than the requested start date, or until `hasMore` is false.
   - Do not assume `turnLimit` is honored. If a limit argument is rejected or ignored, fall back to cursor pagination one page at a time.
   - For threads whose `createdAt` is earlier than the requested period but `updatedAt` is inside or after it, still page through them; they can contain relevant turns on the requested dates.
4. For every relevant thread, extract each assistant/task turn that has `startedAt`. Use `completedAt` as the end time. If `completedAt` is null, show `進行中`.
5. Convert timestamps to the user's local timezone. Prefer JST when the user is in Japan or the conversation is Japanese and the environment timezone is Asia/Tokyo. Group report dates by the configured day boundary, defaulting to 08:00 local time; turns before 08:00 belong to the previous report day.
6. Infer the project from thread metadata such as project/workspace/repository path. Use the thread title for the task label.
7. Sort rows by start time, group by report day using the local 08:00 boundary, and output an HTML report by default. Do not use CSV unless the user requests it.
8. Omit chat body content by default. The important fields are time, project, thread title, and duration.

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
