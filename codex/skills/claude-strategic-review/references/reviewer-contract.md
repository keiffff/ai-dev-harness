# Claude Reviewer Contract

This contract is shared by the default Claude and explicit Fable routes. Each skill owns its wrapper invocation.

## Prompt And Privacy

Send the smallest self-contained evidence that preserves the user's objective: relevant original user requests and corrections, user-approved constraints and decisions, and observations or source excerpts needed to judge the problem. Keep Codex's interpretation, current proposal, inferred non-goals and rejected alternatives separate and attributable; do not present them as user requirements or established facts. Include the basis for relevant exclusions so Claude can challenge an unsupported narrowing of scope. Ordinary user-, repository- and workspace-derived project facts are covered by the existing standing authorization for the user-managed Claude CLI; no per-request approval or placeholder substitution is needed. Honor a narrower user instruction.

Never include credentials, tokens, private keys, raw environment dumps, `.env`, auth config or other secret-bearing content. If secrets would be required, omit that part rather than requesting permission to send them. Pass content through the prompt file, not command arguments.

Require reasoning from the supplied prompt only: no repository inspection, tools, delegation, edits, shell commands, deployment or credential actions. If a material conclusion needs missing evidence, identify the specific gap and which judgment depends on it; do not fill the gap with Codex's assertions or speculative facts. Codex can investigate that gap within the existing task authority; it does not authorize an automatic retry.

## Strategic Challenge

Within the same review response, ask Claude to first frame the problem from the original requests, constraints and observations, then assess Codex's proposal against that framing. Treat the proposal as a hypothesis, not the premise of the review.

Focus on whether the work solves the right problem, whether it treats a symptom while leaving the cause or requested outcome unresolved, and whether local benefits hide wider impact or unnecessary work. Consider a different intervention or no change when supported by the evidence. Challenge unsupported assumptions and exclusions without overriding explicit user decisions or inventing new objectives, requirements or operational restrictions.

Ask for the recommended direction and its rationale, material alternatives and trade-offs, hidden operational costs, and evidence that would change the recommendation. Distinguish supported findings from uncertainty. Do not require criticism or alternatives when the existing direction is supported.

## Adoption

Treat the answer as independent review material, not execution authority. Codex checks it against repository facts, accepted contracts and user constraints, then adopts, rejects or identifies evidence still needed. An objection to the problem framing is not resolved merely by restating the current plan or its test results; address the objection with the original objective and relevant evidence. Use `codex-decision-integrity` before reversing an existing material judgment. Changes beyond accepted scope still follow the existing authorization rules.

## User-Visible Report

In the final response, distinguish Claude's assessment from Codex's decision. Briefly report Claude's recommended direction and significant objections, Codex's adoption or rejection and the reason, and any material unresolved disagreement or evidence gap. Include a significant objection even when Codex rejects it; do not collapse it into a generic "review passed." Attribute a paraphrase as a summary, not a verbatim quote. If Claude supports the current direction without material objections, say so without inventing a finding. If the review was unavailable, report that state rather than implying Claude endorsed the result. Keep the report concise; the whole exchange is unnecessary unless requested.
