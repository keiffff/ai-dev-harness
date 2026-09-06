---
name: codex-doubt-review
description: Independently challenge consequential assumptions or failure/recovery paths using a bounded artifact and contract; main owns adoption.
---

# Codex Doubt Review

Use independent review when an unresolved assumption could materially affect data integrity, authorization, external behavior or recoverability. Mechanical edits and routine branches do not trigger it by themselves.

## Review Packet

Give the reviewer a concrete claim, the smallest relevant artifact and its governing contract. For boundary concerns, include producer representation, decision point, failure state and retrigger/recovery path. Include accepted constraints and relevant rejected alternatives, without the full session narrative.

Ask for at most three contract-breaking conditions, hidden assumptions or non-recovering failure paths, with evidence. Exclude stylistic naming and general refactoring; semantic ambiguity matters only when it can violate the contract.

## Reviewer

- For repo-local review, use a native subagent with the main agent's configured model and reasoning effort. Honor an explicit reviewer model request; Astra review uses the native subagent rather than a separate advisor wrapper.
- Apply `codex-code-review` and, where relevant, `codex-interface-review` within that one independent pass.
- For a broad external architecture/maintainability opinion, use `claude-strategic-review` when requested or useful; Fable remains explicit-only.
- Give reviewers read-only scope. Main retains I/F, compatibility, permissions, Git and final decisions.
- If independent review is unavailable, report that gap. Main review or a regression test can provide evidence, but must not be reported as an independent pass.

## Reconcile And Stop

Classify each finding as actionable, a missing contract decision, an intentional trade-off or noise. Adopt only findings supported by the artifact and contract. Use `codex-decision-integrity` before reversing an existing material judgment.

Stop after one useful cycle unless new substantive evidence requires another; never exceed three cycles. If a contract-bearing assumption cannot be resolved, recommend an ANDON instead of inventing a fallback, identifier or recovery mechanism.

Report the checked claim, significant adopted/rejected findings and remaining verification gap. Keep internal debate out of PR prose unless needed to explain risk.
