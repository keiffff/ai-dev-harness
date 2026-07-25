#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo


def parse_time(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=ZoneInfo("UTC"))
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def minutes_between(start, end):
    return (end - start).total_seconds() / 60


def main():
    parser = argparse.ArgumentParser(description="Render Codex thread turn times as daily Markdown tables.")
    parser.add_argument("json_file", help="JSON file containing normalized rows")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="IANA timezone for output")
    args = parser.parse_args()

    tz = ZoneInfo(args.timezone)
    with open(args.json_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    normalized = []
    for row in rows:
        started = parse_time(row.get("startedAt"))
        if not started:
            continue
        completed = parse_time(row.get("completedAt"))
        started_local = started.astimezone(tz)
        completed_local = completed.astimezone(tz) if completed else None
        normalized.append(
            {
                "date": started_local.strftime("%Y-%m-%d"),
                "start": started_local,
                "end": completed_local,
                "project": row.get("project") or "-",
                "thread": row.get("thread") or row.get("title") or "-",
            }
        )

    normalized.sort(key=lambda r: r["start"])
    by_date = defaultdict(list)
    for row in normalized:
        by_date[row["date"]].append(row)

    for date in sorted(by_date):
        print(f"### {date}\n")
        print("| 時間帯 | プロジェクト | スレッド | 所要 |")
        print("|---|---|---|---:|")
        for row in by_date[date]:
            start_text = row["start"].strftime("%H:%M:%S")
            if row["end"]:
                end_text = row["end"].strftime("%H:%M:%S")
                duration = f"{minutes_between(row['start'], row['end']):.1f}分"
            else:
                end_text = "進行中"
                duration = "進行中"
            print(f"| {start_text} - {end_text} | {row['project']} | {row['thread']} | {duration} |")
        print()


if __name__ == "__main__":
    main()
