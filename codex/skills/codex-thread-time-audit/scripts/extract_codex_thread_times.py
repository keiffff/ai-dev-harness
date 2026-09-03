#!/usr/bin/env python3
import argparse
import html
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo


def boundary_delta(day_boundary_hour):
    return timedelta(minutes=round(day_boundary_hour * 60))


def parse_date(value, tz, end=False, day_boundary_hour=8.0):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    if end and len(value) == 10:
        dt = dt + timedelta(days=1)
    if len(value) == 10:
        dt = dt + boundary_delta(day_boundary_hour)
    return dt


def parse_iso(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def workday_start(dt, day_boundary_hour):
    boundary = dt.replace(hour=0, minute=0, second=0, microsecond=0) + boundary_delta(day_boundary_hour)
    if dt < boundary:
        boundary = boundary - timedelta(days=1)
    return boundary


def workday_label(dt, day_boundary_hour):
    return workday_start(dt, day_boundary_hour).strftime("%Y-%m-%d")


def format_boundary_hour(day_boundary_hour):
    minutes = round(day_boundary_hour * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def format_time_for_workday(dt, date_label):
    label_date = datetime.fromisoformat(date_label).date()
    time_text = dt.strftime("%H:%M:%S")
    if dt.date() == label_date:
        return time_text
    if dt.date() == label_date + timedelta(days=1):
        return f"翌日 {time_text}"
    return dt.strftime("%m/%d %H:%M:%S")


def project_from_cwd(cwd):
    if not cwd:
        return "-"
    parts = PurePosixPath(cwd).parts
    return parts[-1] if parts else cwd


def is_subagent_source(source, parent_thread_id=None):
    # Some directly operated Desktop/VS Code sessions carry a stale
    # thread_source="subagent" flag. Require structural evidence so those
    # user-owned turns are not dropped from activity reports.
    return bool(parent_thread_id) or (isinstance(source, dict) and "subagent" in source)


def load_titles(codex_home):
    titles = {}
    index = codex_home / "session_index.jsonl"
    if not index.exists():
        return titles
    with index.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("id"):
                titles[row["id"]] = row.get("thread_name") or row["id"]
    return titles


def load_overrides(path):
    if not path:
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def iter_session_files(codex_home):
    sessions = codex_home / "sessions"
    archived = codex_home / "archived_sessions"
    if sessions.exists():
        yield from sessions.glob("**/*.jsonl")
    if archived.exists():
        yield from archived.glob("*.jsonl")


def count_task_starts_in_window(lines, start_ts, end_ts):
    count = 0
    for line in lines:
        try:
            item = json.loads(line)
        except Exception:
            continue
        payload = item.get("payload") or {}
        if item.get("type") != "event_msg" or payload.get("type") != "task_started":
            continue
        timestamp = item.get("timestamp")
        started = payload.get("started_at")
        if started is None and timestamp:
            started = parse_iso(timestamp).timestamp()
        if started is not None and start_ts <= started < end_ts:
            count += 1
    return count


def extract_rows(codex_home, start_ts, end_ts, titles, overrides, session_scope="top-level"):
    rows = []
    seen = set()
    stats = Counter()

    for path in iter_session_files(codex_home):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        meta_id = None
        cwd = None
        source = None
        parent_thread_id = None
        for line in lines[:20]:
            try:
                item = json.loads(line)
            except Exception:
                continue
            if item.get("type") == "session_meta":
                payload = item.get("payload") or {}
                meta_id = payload.get("id") or meta_id
                cwd = payload.get("cwd") or cwd
                source = payload.get("source")
                parent_thread_id = payload.get("parent_thread_id")
                break

        structural_subagent = is_subagent_source(source, parent_thread_id)
        if structural_subagent:
            subagent_task_starts = count_task_starts_in_window(lines, start_ts, end_ts)
            if subagent_task_starts:
                stats["structural_subagent_files"] += 1
                stats["structural_subagent_task_starts"] += subagent_task_starts
        if structural_subagent and session_scope == "top-level":
            if subagent_task_starts:
                stats["skipped_subagent_files"] += 1
                stats["skipped_subagent_task_starts"] += subagent_task_starts
            continue

        stats["parsed_files"] += 1
        tasks = {}
        active = []

        for line in lines:
            try:
                item = json.loads(line)
            except Exception:
                continue
            payload = item.get("payload") or {}
            timestamp = item.get("timestamp")
            ts_num = parse_iso(timestamp).timestamp() if timestamp else None

            if item.get("type") == "session_meta":
                meta_id = payload.get("id") or meta_id
                cwd = payload.get("cwd") or cwd
                continue

            if item.get("type") == "turn_context":
                turn_cwd = payload.get("cwd")
                cwd = turn_cwd or cwd
                turn_id = payload.get("turn_id")
                if turn_id in tasks and turn_cwd:
                    tasks[turn_id]["cwd"] = turn_cwd
                    tasks[turn_id]["cwd_source"] = "turn_context"
                continue

            # Newer Codex session logs record the user prompt as a
            # response_item message instead of event_msg:user_message.
            # Accept either representation so a format migration does not
            # silently drop otherwise complete top-level turns.
            if item.get("type") == "response_item":
                if payload.get("type") == "message" and payload.get("role") == "user":
                    if active and active[-1] in tasks:
                        tasks[active[-1]]["user_evidence"].add("response_item.message.user")
                    elif ts_num is not None and start_ts <= ts_num < end_ts:
                        stats["unmatched_user_signals"] += 1
                continue

            if item.get("type") != "event_msg":
                continue

            event_type = payload.get("type")
            if event_type == "task_started":
                turn_id = payload.get("turn_id") or f"{path}:{ts_num}"
                tasks[turn_id] = {
                    "turn_id": turn_id,
                    "start": payload.get("started_at") or ts_num,
                    "end": None,
                    "complete_type": None,
                    "user_evidence": set(),
                    "cwd": cwd,
                    "cwd_source": "session_meta" if cwd else "missing",
                }
                active.append(turn_id)
            elif event_type == "user_message":
                if active and active[-1] in tasks:
                    tasks[active[-1]]["user_evidence"].add("event_msg.user_message")
                elif ts_num is not None and start_ts <= ts_num < end_ts:
                    stats["unmatched_user_signals"] += 1
            elif event_type in ("task_complete", "turn_aborted"):
                turn_id = payload.get("turn_id")
                if turn_id in tasks:
                    tasks[turn_id]["end"] = payload.get("completed_at") or payload.get("aborted_at") or ts_num
                    tasks[turn_id]["complete_type"] = event_type
                elif ts_num is not None and start_ts <= ts_num < end_ts:
                    stats["completion_without_task_start"] += 1
                if turn_id in active:
                    active = [candidate for candidate in active if candidate != turn_id]

        for task in tasks.values():
            started = task["start"]
            completed = task["end"]
            if started is None or not (start_ts <= started < end_ts):
                continue
            stats["raw_task_starts"] += 1
            if not task["user_evidence"]:
                stats["tasks_without_known_user_evidence"] += 1
            elif len(task["user_evidence"]) == 1:
                evidence = next(iter(task["user_evidence"]))
                stats[f"tasks_with_{evidence}"] += 1
            else:
                stats["tasks_with_both_known_user_formats"] += 1
            key = (meta_id, task["turn_id"], round(started, 3), round(completed or 0, 3))
            if key in seen:
                stats["duplicate_task_rows"] += 1
                continue
            seen.add(key)
            title = overrides.get(meta_id) or titles.get(meta_id) or f"未題 ({meta_id or path.stem})"
            if task["cwd_source"] != "turn_context":
                stats["tasks_with_session_cwd_fallback"] += 1
            rows.append(
                {
                    "session_id": meta_id or path.stem,
                    "turnId": task["turn_id"],
                    "project": project_from_cwd(task["cwd"]),
                    "thread": title,
                    "startedAt": started,
                    "completedAt": completed,
                    "status": "進行中" if completed is None else ("中断" if task["complete_type"] == "turn_aborted" else "completed"),
                    "sessionKind": "subagent" if structural_subagent else "top-level",
                    "parentThreadId": parent_thread_id,
                    "userEvidence": sorted(task["user_evidence"]),
                }
            )

    rows.sort(key=lambda row: row["startedAt"])
    stats["rows"] = len(rows)
    return rows, stats


def build_diagnostics(stats, start, end, timezone, session_scope):
    raw_task_starts = stats["raw_task_starts"]
    accounted = stats["rows"] + stats["duplicate_task_rows"]
    unaccounted = raw_task_starts - accounted
    review_reasons = []
    if unaccounted:
        review_reasons.append("raw task starts and output rows do not reconcile")
    if stats["tasks_without_known_user_evidence"]:
        review_reasons.append("some task starts have no known user-message marker")
    if stats["unmatched_user_signals"]:
        review_reasons.append("some user-message markers were not associated with a known task start")
    if stats["completion_without_task_start"]:
        review_reasons.append("some completion events were not associated with a known task start")
    if stats["tasks_with_session_cwd_fallback"]:
        review_reasons.append("some turns used session cwd because turn_context cwd was unavailable")
    if session_scope == "all" and stats["structural_subagent_files"]:
        review_reasons.append("subagent logs may contain inherited parent history; review provenance before reporting")
    return {
        "schemaVersion": 1,
        "window": {"start": start.isoformat(), "end": end.isoformat(), "timezone": timezone},
        "sessionScope": session_scope,
        "coverage": {
            "rawTaskStarts": raw_task_starts,
            "outputRows": stats["rows"],
            "duplicateTaskRows": stats["duplicate_task_rows"],
            "unaccountedTaskStarts": unaccounted,
            "tasksWithoutKnownUserEvidence": stats["tasks_without_known_user_evidence"],
            "tasksWithEventUserEvidenceOnly": stats["tasks_with_event_msg.user_message"],
            "tasksWithResponseUserEvidenceOnly": stats["tasks_with_response_item.message.user"],
            "tasksWithBothKnownUserFormats": stats["tasks_with_both_known_user_formats"],
            "unmatchedUserSignals": stats["unmatched_user_signals"],
            "completionWithoutTaskStart": stats["completion_without_task_start"],
            "structuralSubagentFiles": stats["structural_subagent_files"],
            "structuralSubagentTaskStarts": stats["structural_subagent_task_starts"],
            "skippedSubagentFiles": stats["skipped_subagent_files"],
            "skippedSubagentTaskStarts": stats["skipped_subagent_task_starts"],
        },
        "status": "review_required" if review_reasons else "ok",
        "reviewReasons": review_reasons,
        "sourceBoundary": "This verifies extraction from readable local JSONL files; it cannot prove that upstream Codex activity was written locally.",
    }


def render_markdown(rows, tz, stats, day_boundary_hour):
    by_date = defaultdict(list)
    for row in rows:
        started = datetime.fromtimestamp(row["startedAt"], tz)
        by_date[workday_label(started, day_boundary_hour)].append(row)

    lines = []
    lines.append(f"取得件数: {stats['rows']} turn")
    lines.append("")
    for date in sorted(by_date):
        lines.append(f"### {date}")
        lines.append("")
        lines.append("| 時間帯 | プロジェクト | スレッド | 所要 |")
        lines.append("|---|---|---|---:|")
        global_covered_until = None
        project_covered_until = {}
        for row in by_date[date]:
            project = row["project"]
            label = overlap_label(global_covered_until, project_covered_until.get(project), row)
            started = datetime.fromtimestamp(row["startedAt"], tz)
            start_text = format_time_for_workday(started, date)
            if row["completedAt"]:
                completed = datetime.fromtimestamp(row["completedAt"], tz)
                end_text = format_time_for_workday(completed, date)
                duration = f"{(completed - started).total_seconds() / 60:.1f}分"
            else:
                end_text = "進行中"
                duration = "進行中"
            if label:
                start_text = f"↳ {label} {start_text}"
            lines.append(f"| {start_text} - {end_text} | {row['project']} | {row['thread']} | {duration} |")
            global_covered_until = update_covered_until(global_covered_until, row)
            project_covered_until[project] = update_covered_until(project_covered_until.get(project), row)
        lines.append("")
    return "\n".join(lines)


def break_candidate_from_covered_until(covered_until, next_row, tz, threshold_minutes, day_boundary_hour):
    if not covered_until:
        return None
    previous_end = datetime.fromtimestamp(covered_until, tz)
    next_start = datetime.fromtimestamp(next_row["startedAt"], tz)
    if workday_label(previous_end, day_boundary_hour) != workday_label(next_start, day_boundary_hour):
        return None
    gap_minutes = (next_start - previous_end).total_seconds() / 60
    if gap_minutes < threshold_minutes:
        return None
    return previous_end, next_start, gap_minutes


def update_covered_until(covered_until, row):
    completed = row.get("completedAt")
    if not completed:
        return covered_until
    if covered_until is None:
        return completed
    return max(covered_until, completed)


def overlap_label(global_covered_until, project_covered_until, row):
    started = row["startedAt"]
    if project_covered_until is not None and started < project_covered_until:
        return "同PJ並行"
    if global_covered_until is not None and started < global_covered_until:
        return "並行"
    return None


def render_html(rows, tz, stats, start_label, end_label, break_threshold_minutes, day_boundary_hour):
    by_date = defaultdict(list)
    project_counts = Counter(row["project"] for row in rows)
    for row in rows:
        started = datetime.fromtimestamp(row["startedAt"], tz)
        by_date[workday_label(started, day_boundary_hour)].append(row)

    tabs = [
        f'<button class="tab is-active" type="button" data-project-tab="__all__">すべて <span>{stats["rows"]}</span></button>'
    ]
    for project, count in sorted(project_counts.items(), key=lambda item: (-item[1], item[0])):
        tabs.append(
            f'<button class="tab" type="button" data-project-tab="{html.escape(project, quote=True)}">'
            f"{html.escape(project)} <span>{count}</span></button>"
        )

    sections = []
    for date in sorted(by_date):
        sections.append(f'<section class="date-section" data-date="{html.escape(date, quote=True)}">')
        sections.append(f"<h2>{html.escape(date)}</h2>")
        sections.append('<div class="table-wrap"><table>')
        sections.append(
            "<thead><tr>"
            "<th>時間帯</th><th>プロジェクト</th><th>スレッド</th><th>所要</th>"
            "</tr></thead><tbody>"
        )
        global_covered_until = None
        project_covered_until = {}
        for row in by_date[date]:
            global_break_candidate = break_candidate_from_covered_until(global_covered_until, row, tz, break_threshold_minutes, day_boundary_hour)
            if global_break_candidate:
                break_start, break_end, gap_minutes = global_break_candidate
                sections.append(
                    '<tr class="break-row" data-global-break-row="true">'
                    f"<td>{html.escape(format_time_for_workday(break_start, date))} - {html.escape(format_time_for_workday(break_end, date))}</td>"
                    "<td>休憩候補</td>"
                    f"<td>{break_threshold_minutes:.0f}分以上 Codex turn が空いた時間。目視確認や別作業の可能性あり。</td>"
                    f"<td>{gap_minutes:.1f}分</td>"
                    "</tr>"
                )

            project = row["project"]
            label = overlap_label(global_covered_until, project_covered_until.get(project), row)
            project_break_candidate = break_candidate_from_covered_until(project_covered_until.get(project), row, tz, break_threshold_minutes, day_boundary_hour)
            if project_break_candidate:
                break_start, break_end, gap_minutes = project_break_candidate
                sections.append(
                    f'<tr class="break-row break-row--project" data-project-break-row="{html.escape(project, quote=True)}" hidden>'
                    f"<td>{html.escape(format_time_for_workday(break_start, date))} - {html.escape(format_time_for_workday(break_end, date))}</td>"
                    f"<td>{html.escape(project)}</td>"
                    f"<td>プロジェクト内休憩候補。{break_threshold_minutes:.0f}分以上このプロジェクトのCodex turnが空いた時間。</td>"
                    f"<td>{gap_minutes:.1f}分</td>"
                    "</tr>"
                )

            started = datetime.fromtimestamp(row["startedAt"], tz)
            start_text = format_time_for_workday(started, date)
            if row["completedAt"]:
                completed = datetime.fromtimestamp(row["completedAt"], tz)
                end_text = format_time_for_workday(completed, date)
                duration = f"{(completed - started).total_seconds() / 60:.1f}分"
            else:
                end_text = "進行中"
                duration = "進行中"
            time_cell = f"{html.escape(start_text)} - {html.escape(end_text)}"
            row_class = ' class="overlap-row"' if label else ""
            if label:
                time_cell = f'<span class="overlap-mark">↳ {html.escape(label)}</span> {time_cell}'
            sections.append(
                f'<tr{row_class} data-project="{html.escape(row["project"], quote=True)}">'
                f"<td>{time_cell}</td>"
                f"<td>{html.escape(row['project'])}</td>"
                f"<td>{html.escape(row['thread'])}</td>"
                f"<td>{html.escape(duration)}</td>"
                "</tr>"
            )
            global_covered_until = update_covered_until(global_covered_until, row)
            project_covered_until[project] = update_covered_until(project_covered_until.get(project), row)
        sections.append("</tbody></table></div></section>")

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codex Thread Times {html.escape(start_label)} to {html.escape(end_label)}</title>
<style>
  :root {{
    color-scheme: light;
    --bg: #f6f7f9;
    --panel: #ffffff;
    --text: #1f2328;
    --muted: #667085;
    --border: #d7dce2;
    --head: #eef2f6;
    --accent: #0f766e;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  main {{
    max-width: 1180px;
    margin: 0 auto;
    padding: 28px 20px 48px;
  }}
  h1 {{
    margin: 0 0 8px;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 0;
  }}
  .sub {{
    margin: 0 0 22px;
    color: var(--muted);
    font-size: 14px;
  }}
  .summary {{
    display: inline-block;
    margin: 0 0 22px;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    background: var(--panel);
    border-radius: 6px;
    font-weight: 600;
  }}
  .note {{
    margin: -10px 0 22px;
    color: var(--muted);
    font-size: 13px;
  }}
  .tabs {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0 0 22px;
  }}
  .tab {{
    appearance: none;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--panel);
    color: var(--text);
    cursor: pointer;
    font: inherit;
    font-size: 13px;
    line-height: 1;
    padding: 8px 11px;
  }}
  .tab span {{
    color: var(--muted);
    margin-left: 4px;
  }}
  .tab:hover {{
    border-color: var(--accent);
  }}
  .tab.is-active {{
    background: var(--accent);
    border-color: var(--accent);
    color: #ffffff;
  }}
  .tab.is-active span {{
    color: #d7f5f0;
  }}
  h2 {{
    margin: 28px 0 10px;
    font-size: 20px;
    letter-spacing: 0;
  }}
  .table-wrap {{
    overflow-x: auto;
    border: 1px solid var(--border);
    background: var(--panel);
    border-radius: 8px;
  }}
  table {{
    width: 100%;
    min-width: 860px;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;
  }}
  th, td {{
    padding: 7px 10px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    white-space: nowrap;
    vertical-align: top;
  }}
  th {{
    position: sticky;
    top: 0;
    z-index: 1;
    background: var(--head);
    font-weight: 700;
  }}
  td:nth-child(3) {{ white-space: normal; min-width: 260px; }}
  td:nth-child(4), th:nth-child(4) {{ text-align: right; }}
  tr:last-child td {{ border-bottom: 0; }}
  tr:nth-child(even) td {{ background: #fafbfc; }}
  .overlap-row td {{
    background: #f8fafc !important;
    color: #475467;
  }}
  .overlap-row td:first-child {{
    border-left: 4px solid #94a3b8;
    padding-left: 6px;
  }}
  .overlap-mark {{
    display: inline-block;
    margin-right: 6px;
    padding: 2px 6px;
    border: 1px solid #cbd5e1;
    border-radius: 999px;
    background: #ffffff;
    color: #475467;
    font-size: 11px;
    font-weight: 700;
    line-height: 1.2;
  }}
  .break-row td {{
    background: #fff7ed !important;
    color: #8a4b12;
    font-weight: 600;
  }}
  .break-row td:nth-child(3) {{
    font-weight: 500;
  }}
  .break-row--project td {{
    background: #f0fdf4 !important;
    color: #166534;
  }}
  [hidden] {{ display: none !important; }}
</style>
</head>
<body>
<main>
  <h1>Codex Thread Times</h1>
  <p class="sub">{html.escape(start_label)} - {html.escape(end_label)} / {html.escape(str(tz))} / day boundary {html.escape(format_boundary_hour(day_boundary_hour))} / selected Codex task turns</p>
  <p class="summary">取得件数: {stats['rows']} turn</p>
  <p class="note">休憩候補は、前turn終了から次turn開始まで{break_threshold_minutes:.0f}分以上空いた箇所です。すべてタブでは全体、プロジェクトタブではそのプロジェクト内の空きを表示します。目視確認や別作業の可能性があるため、休憩確定ではありません。</p>
  <p class="note">「↳ 同PJ並行」は同じプロジェクトで前のturnが終了する前に始まったturn、「↳ 並行」は別プロジェクトを含む重なりです。</p>
  <nav class="tabs" aria-label="Project filter">{''.join(tabs)}</nav>
  {''.join(sections)}
</main>
<script>
(() => {{
  const buttons = Array.from(document.querySelectorAll("[data-project-tab]"));
  const rows = Array.from(document.querySelectorAll("tr[data-project]"));
  const globalBreakRows = Array.from(document.querySelectorAll("[data-global-break-row]"));
  const projectBreakRows = Array.from(document.querySelectorAll("[data-project-break-row]"));
  const sections = Array.from(document.querySelectorAll(".date-section"));

  const applyProject = (project) => {{
    for (const button of buttons) {{
      button.classList.toggle("is-active", button.dataset.projectTab === project);
    }}
    for (const row of rows) {{
      row.hidden = project !== "__all__" && row.dataset.project !== project;
    }}
    for (const row of globalBreakRows) {{
      row.hidden = project !== "__all__";
    }}
    for (const row of projectBreakRows) {{
      row.hidden = project === "__all__" || row.dataset.projectBreakRow !== project;
    }}
    for (const section of sections) {{
      section.hidden = !section.querySelector("tr[data-project]:not([hidden]), [data-global-break-row]:not([hidden]), [data-project-break-row]:not([hidden])");
    }}
  }};

  for (const button of buttons) {{
    button.addEventListener("click", () => applyProject(button.dataset.projectTab));
  }}
}})();
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Extract recorded Codex task turn times from local session JSONL files.")
    parser.add_argument("--start", required=True, help="Start date/datetime in output timezone, inclusive")
    parser.add_argument("--end", required=True, help="End date/datetime in output timezone, inclusive when date-only")
    parser.add_argument("--timezone", default="Asia/Tokyo")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--title-overrides", help="JSON object mapping session id to title")
    parser.add_argument("--output", help="Output path. .html writes HTML; other extensions write Markdown")
    parser.add_argument("--html-output", help="HTML output path")
    parser.add_argument("--markdown-output", help="Markdown output path")
    parser.add_argument("--json-output", help="Normalized JSON rows output path")
    parser.add_argument("--diagnostics-output", help="Coverage diagnostics JSON path. Defaults beside --json-output when omitted.")
    parser.add_argument("--session-scope", choices=("all", "top-level"), default="top-level", help="Capture top-level sessions or all session files. The all scope is diagnostic because subagent logs can inherit parent history.")
    parser.add_argument("--break-threshold-minutes", type=float, default=15.0, help="Highlight global gaps of at least this many minutes as break candidates")
    parser.add_argument("--day-boundary-hour", type=float, default=8.0, help="Hour in output timezone where a report day starts. Date-only ranges use this boundary.")
    args = parser.parse_args()

    tz = ZoneInfo(args.timezone)
    codex_home = Path(args.codex_home)
    start = parse_date(args.start, tz, end=False, day_boundary_hour=args.day_boundary_hour)
    end = parse_date(args.end, tz, end=True, day_boundary_hour=args.day_boundary_hour)
    titles = load_titles(codex_home)
    overrides = load_overrides(args.title_overrides)
    rows, stats = extract_rows(codex_home, start.timestamp(), end.timestamp(), titles, overrides, args.session_scope)
    diagnostics = build_diagnostics(stats, start, end, args.timezone, args.session_scope)

    markdown = render_markdown(rows, tz, stats, args.day_boundary_hour)
    html_output = render_html(rows, tz, stats, args.start, args.end, args.break_threshold_minutes, args.day_boundary_hour)
    if args.output:
        output_path = Path(args.output)
        content = html_output if output_path.suffix.lower() in (".html", ".htm") else markdown
        output_path.write_text(content, encoding="utf-8")
    else:
        print(html_output)
    if args.html_output:
        Path(args.html_output).write_text(html_output, encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(markdown, encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    diagnostics_output = args.diagnostics_output
    if not diagnostics_output and args.json_output:
        diagnostics_output = str(Path(args.json_output).with_suffix(".diagnostics.json"))
    if diagnostics_output:
        Path(diagnostics_output).write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    coverage = diagnostics["coverage"]
    print(
        "coverage "
        f"status={diagnostics['status']} "
        f"raw_task_starts={coverage['rawTaskStarts']} "
        f"output_rows={coverage['outputRows']} "
        f"unaccounted={coverage['unaccountedTaskStarts']} "
        f"unknown_user_evidence={coverage['tasksWithoutKnownUserEvidence']}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
