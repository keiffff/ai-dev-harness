---
name: codex-context-engineering
description: Find evidence for repository and operational questions, including existing owners, execution paths, direct measurements, and bounded log investigation.
---

# Codex Context Engineering

Use this when evidence sources or existing ownership need investigation. Let the request set the output: facts, interpretation, or recommendations.

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

Use `rg` / `rg --files`, relevant local Git reads, and the approved remote-read tools. Refresh remote refs when freshness matters and the task permits fetching; otherwise label the comparison as local-ref evidence. Authentication failures follow AGENTS.md; do not switch access paths.

For ambiguous conversation references, try one direct lookup; if the target is still unclear, ask before starting a broad log search.

## Existing Owner And Execution Path

Before proposing a new owner or saying a mechanism is absent or broken, trace the current owner, trigger, target discovery, inclusion/exclusion boundary, and execution evidence. Include schedules, events, implicit creation write, and downstream actions before calling an operational procedure safe.

Report the inspected scope when something is not found. A missing search result does not establish absence. If an existing owner excludes the target, describe that boundary before proposing another mechanism.

## Evidence Quality

Prefer observed records, then reproducible calculations, then labeled estimates or extrapolations. Align period, workload, denominator, population and exclusions before claiming an effect. State the observation window and continuation assumption for projections.

Distinguish pre-release checks from production outcomes. Resolve conflicting evidence by source, specificity and contract fit. Missing product requirements need a decision; missing implementation precedent alone does not.

## Bounded Scouts

Use a read-only subagent when an independent scan would reduce main-context noise. Give it one question and a bounded source area. Request file/line evidence, strong and weak candidates, search limits, and the smallest useful follow-up reads. Main owns interpretation, design, I/F, compatibility, permissions and Git actions.
