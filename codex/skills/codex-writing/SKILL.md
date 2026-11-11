---
name: codex-writing
description: 文章の作成・送信稿の内容点検・改稿と、その作業を続けるかの判別。引用スレッド付きの「この文でよいか」、Slack報告・確認依頼、PR本文に使う。文面作業中の観測共有を追加改稿と区別する。レビュー文面はcode-reviewへ。独立した通常会話・語句だけの校正は除く。
---

# Codex Writing

Codex writes prose. Ordinary replies and wording-only edits stay outside this workflow. Decision records use `codex-decision-doc`. HTML through `claude-html-report` is the bounded exception: Claude owns composition; Codex supplies facts and verifies the final artifact. Explicit `gemini-japanese-polish` likewise owns Japanese structure and wording from verified facts.

## Build The Current Deliverable

1. Select the requested operation before selecting a medium: checking/editing supplied prose, restructuring it, or composing a new deliverable. A shared observation without a writing request receives a direct conversational response. Review-comment composition uses `codex-code-review`'s Copyable Review Output on the established findings; it does not require a new code review.
2. For source-grounded deliverables spanning a long discussion, multiple findings or quantitative/causal comparisons, and follow-up messages in that ongoing prose task, use the [executable source workflow](references/source-workflow.md). Its first phase distinguishes a current writing request from an observation before reading historical evidence; a conversation result ends without producing a draft. For writing, it selects exact source passages without seeing a candidate and generates from that selection. Existing drafts use literal replacements; unselected text is not regenerated. Supply actual source text, not an assistant's rewritten account. Use the configured main model and reasoning setting; do not choose a new provider or model.
3. For a small self-contained edit, copy the supplied draft and patch only the requested or evidenced defect. Verify every change is required by the requested delta or a concrete defect. Do not trade an unwanted rewrite for over-compression. A medium's outline does not authorize adding subjects or commitments from quoted history. An omitted detail needs correction only when it prevents the recipient from performing the requested action or understanding its result.
4. Keep the complete deliverable in one file at the requested destination or private task storage. Explain unfamiliar objects before their names. Preserve source definitions and completion state. State well-supported findings and explanations directly. If the evidence strongly favors an explanation and the remaining uncertainty would not change the recipient's takeaway, decision or action, omit the caveat. Use brief wording within the claim when uncertainty matters. Unpublished drafts contain the accepted result, not correction history. Add no unsupported cause, owner, date, commitment or verification claim.

## Slack: Choose The Reporting Job

Use the supplied voice; otherwise use plain form. For reports with multiple points, put short section names in inline backticks and organize each section as hierarchical bullets. The parent states the point; children carry its reasons, evidence and conditions. Follow the supplied section names. A short acknowledgment or a single brief answer stays plain. The source workflow applies this layout after content editing and checks that body wording, numbers and order are retained. Use no outer fence, Markdown hash headings or tables unless requested.

| Job | Build the message from |
|---|---|
| Investigation results | Overall conclusion, then the findings across the requested questions. Retain distinct result groups and the difference between observed events and estimates. End with an action only when it was requested or agreed. |
| Incident report | Event and impact, then cause and detection gap, then completed and remaining measures. Derive each measure from existing behavior, the uncovered path and the actual change; do not propose an existing mechanism as new. |
| Interim findings | What was observed and what it supports. Include unresolved causes or boundaries only where they change the conclusion or next action. |
| Progress update | What is complete and its visible result, then close with what remains and its actual dependency. Include a next action only if requested or agreed; no internal inventory. |
| Verification request | Intended send time and environment, the changed behavior, supplied reproduction actions and expected visible result. Include only what the recipient needs to verify; other recovery work is a separate subject. |

For a short acknowledgment or local wording edit, preserve its size and intent rather than building a report.

## PR Body

Use the final change set and accepted purpose as the source. Group changes by resulting behavior, not by edit chronology. Fill the repository template with the problem, resulting behavior, relevant rationale, verification actually performed and material residual limits. Carry the source's causal uncertainty and verification status with each claim. Make the body understandable without this conversation.

When background or detail is requested, retain why the final approach was chosen and relevant constraints or alternatives. Check each paragraph, bullet and table row of the final PR body. Select exact spans of internal notes and delete them from the saved draft. Keep the remaining wording intact. If a deletion leaves a broken sentence, repair that sentence locally and check it against the original evidence:

- **Change and rationale.** Keep the trigger, resulting behavior, adopted rationale and compatibility or rollout constraints. Leave abandoned attempts, investigation chronology, agent handoffs, worktree setup and drafting steps in the work notes.
- **Verification.** Keep the relevant condition or operation, what happened and the limits of that result. Retain, for example, whether a failed save left data unchanged, or the workload and conditions needed to compare timings. Include suite names, counts, commands or fixtures when they establish relevant coverage or help reproduce that result. Leave test file inventories, worker settings and rerun history in the work notes when they add no such evidence. Keep mock conditions, environments and sample sizes attached to the specific check they describe.
- **Failures and unknowns.** Keep a failed check, gap or environment difference if it affects confidence in the changed behavior, merge readiness or deployment. State the consequence, such as an integration path still needing verification. Leave unrelated failures, local setup and troubleshooting in the work notes. If a passage mixes useful evidence and process details, remove the process details in place and preserve unaffected wording.

README follows the same reader-first ordering; release notes give user-visible changes; UI copy explains the event and the next available action.

## Check And Deliver The Actual Draft

Read the saved draft against the request and outline: every requested subject still has its result; numbers retain their group and basis; conditions explain the consequence; proposals and completion states match sources. Compare revised spans with the accepted draft and remove unrelated additions. Correct the same file, then deliver its absolute link without regenerating or shortening the text in chat. Keep required fixes in the artifact, not as unapplied suggestions.

Prefer the user's accepted example. When a new structure needs a model, read only the matching section of [Japanese prose examples](references/japanese-technical-prose.md); follow its information order, not its incidental facts. PR and review Markdown follow AGENTS.md's complete copyable-body contract.

This editing check is not independent proof. When changing the skill, compare actual old/new artifacts on the same requests and corrections; do not make that evaluation a step in every writing task.
