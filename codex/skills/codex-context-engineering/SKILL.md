---
name: codex-context-engineering
description: Find repository evidence, existing owners and relevant local work history.
---

# Codex Context Engineering

Use this when evidence sources or existing ownership need investigation. Let the request set the output: facts, interpretation, or recommendations.

## Project-Specific Procedures

Before selecting project procedures or rebuilding verification, read relevant SKILL.md files from the current checkout's external project-skill index in runtime context. Only the index is automatic; load bodies as needed. To resolve it directly, use `python3 ~/.codex/hooks/project_skills.py list --cwd <verified-checkout>`; read a listed entry with `read --cwd <verified-checkout> --skill <listed-id>`. An empty or unavailable index is not permission to use another project's entries.

Private skills stay outside the checkout. Register a project's existing files once with `register --cwd <verified-checkout> --skill-file <absolute-SKILL.md>` (repeat `--skill-file` for its complete set). The private registry defaults to `~/.local/share/agent-work-memory/knowledge/project-skills/registry.json` and keys that set by the canonical Git common directory, shared across its worktrees. Registration replaces that project's set and preserves other projects. This supplements the native skill catalog; it does not install each entry globally.

## Evidence Sources

| Question | Start here | Follow only as needed |
| --- | --- | --- |
| What behavior is required? | Current user request, nearest AGENTS.md, accepted spec/design and decisions | Existing contract tests and consumers |
| Where is behavior implemented? | Entrypoint or caller, current owner, one nearby implementation and its tests | Producer/consumer types and directly related helpers |
| What changed or regressed? | Current diff and exact failing command/output | Relevant history, CI evidence, generated artifacts |
| Did an operation run or finish? | Execution record and resulting artifact/state | Trigger, discovery, failure and recovery path |
| How much time, cost, volume, or impact? | Direct billing, timing, usage or result records | Reproducible calculation; explicit estimate only when records cannot answer |
| Which earlier conversation? | One direct lookup using the named task, date or artifact | Bounded task history after identifying the target |
| What does an external tool currently support? | Available local implementation/help for local behavior; official docs for service behavior | Approved readonly wrapper or dedicated connector for account/repo state |

Use `rg` / `rg --files`, local Git reads and approved remote-read tools. Refresh remote refs when freshness matters and fetching is permitted; otherwise identify local-ref evidence. Authentication failures follow AGENTS.md.

For conversation evidence, first read the named or current task, preserving roles and time range. Follow other tasks only when requested or directly referenced. If one direct lookup cannot resolve an ambiguous reference, ask before starting a broad log search. Assistant, reviewer and hook messages do not become user intent.

## Existing Owner And Observation Boundary

Trace the owner, trigger, discovery and inclusion/exclusion boundary before proposing a new mechanism. Include schedules, events, implicit creation write and downstream effects before calling an operational procedure safe. Derive relevant paths from deployed entrypoints, callers and configuration, rather than treating one convenient query as exhaustive. In the existing investigation note, retain queried source, window, filters and outcome. A negative result, unknown source, denied read and unfinished search support different conclusions.

## Choose The Next Observation

Use the requested result to choose the question, the live alternatives that matter, and an observation that distinguishes them. Check that the source can answer that question before querying it. After the result, decide whether to investigate a remaining alternative or advance to the requested delivery. Do not repeat unchanged queries or expand coverage when the result cannot change that decision.

Prefer observed records, reproducible calculations, then labeled estimates. Align period, denominator, population and exclusions; distinguish production observations from pre-release checks. Judge sufficiency against the requested decision, not universal completeness. Perform available authorized reads before treating a fact as unknown. A genuine access failure or missing requirement differs from an unperformed read.

Use the existing task note for the question, decisive evidence and unfinished outcome. Agent-selected sources and search boundaries are revisable means, not user requirements. Hand the supported conclusion and original evidence to writing; investigation notes are not automatically reader-facing content.

## Bounded Scouts

Handle routine investigation in main. A read-only subagent needs explicit delegation or a substantial independent question whose time or quality benefit justifies its cost. Context reduction alone is insufficient.

Use `fork_turns: "none"` by default. Supply one question, bounded sources, relevant constraints and evidence; inherit only necessary history. Ask for file/line evidence, search limits and useful follow-up reads. Do not duplicate its scan or permit further delegation. Main owns interpretation, design, compatibility, permissions and Git actions.
