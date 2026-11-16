# Claude Reviewer Contract

This contract is shared by the default Claude and explicit Fable routes. Each skill owns its wrapper invocation.

## Prompt And Privacy

Send the smallest self-contained original evidence that preserves the user's objective: relevant requests, accepted constraints, observations and the actual proposed artifact. For code changes include the diff and relevant base/head context. Keep Codex's review findings, adoption decisions and preferred direction out of the initial independent input. Competing mechanisms and public research may be supplied as candidates without a selected winner. Identify author claims and inferred constraints so Claude can challenge unsupported scope. Ordinary user-, repository- and workspace-derived project facts are covered by the existing standing authorization for the user-managed Claude CLI; no per-request approval or placeholder substitution is needed. Honor a narrower user instruction.

Never include credentials, tokens, private keys, raw environment dumps, `.env`, auth config or other secret-bearing content. If secrets would be required, omit that part rather than requesting permission to send them. Pass content through the prompt file, not command arguments.

Require reasoning from the supplied prompt only: no repository inspection, tools, delegation, edits, shell commands, deployment or credential actions. If a material conclusion needs missing evidence, identify the specific gap and which judgment depends on it; do not fill the gap with Codex's assertions or speculative facts. Codex can investigate that gap within the existing task authority; it does not authorize an automatic retry.

## Strategic Challenge

Within the same review response, ask Claude to frame the problem from the original requests, constraints and observations, then assess the proposal as a hypothesis. Keep agent-added work and completion conditions separate from those originals, with the observations said to require them. Challenge whether those additions change the requested purpose or cost more than the consequence they address. Use an existing strategic review at a consequential direction or scope decision; do not add a mandatory call for routine steps or wait until implementation to question the framing.

Assess whether the proposal solves the right problem or shifts its cost elsewhere. For consequential mechanisms, compare repair, reduced responsibility and an existing supported alternative. Examine overdefense, duplicated ownership and future-proofing against present requirements; recurring maintenance or operating cost can matter without a runtime failure. A required change needs evidence and a feasible alternative preserving purpose, authority, compatibility and recovery.

New tests are part of the candidate, not proof that its added requirements are valid. Trace unchanged code taking a new role; distinguish new regressions, incomplete fixes and unrelated old defects. Preserve complexity justified by a contract or evidenced safety boundary. Do not force criticism or invent objectives. Name the missing fact when it would change the recommendation.

Return the recommended direction, material alternatives and trade-offs, consequential objections, and evidence that would change the recommendation. Distinguish supported findings from uncertainty.

## Adoption

Treat the answer as independent review material, not execution authority. Codex reconciles each material objection against repository facts, accepted contracts and user constraints: adopt an evidenced defect, resolve an objection with counterevidence or an established inapplicable premise, or retain it as unresolved. Absence of a documented prohibition and tests that do not exercise the disputed boundary do not resolve it. An objection to the problem framing is not resolved by restating the plan. Keep justified complexity, and distinguish uncertainty from a required change. Use `codex-decision-integrity` before reversing an existing material judgment. Changes beyond accepted scope still follow the existing authorization rules.

## User-Visible Report

In the final response, distinguish Claude's assessment from Codex's decision. Briefly report the recommended direction, significant objections, their disposition and the supporting or contradicting evidence. Name an unresolved objection in the overall assessment when it could invalidate the purpose, deployment or promised behavior; do not give an unconditional clean conclusion and leave that objection only in verification limits. Include significant objections even when resolved or rejected. Attribute a paraphrase as a summary, not a verbatim quote. If Claude supports the direction without material objections, say so without inventing a finding. If the review was unavailable, report that state rather than implying endorsement. Keep the report concise; the whole exchange is unnecessary unless requested.
