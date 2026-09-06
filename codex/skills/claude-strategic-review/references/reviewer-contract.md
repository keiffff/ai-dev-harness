# Claude Reviewer Contract

This contract is shared by the default Claude and explicit Fable routes. Each skill owns its wrapper invocation.

## Prompt And Privacy

Send the smallest self-contained set of confirmed facts, current proposal, constraints, non-goals and relevant rejected alternatives. Ordinary user-, repository- and workspace-derived project facts are covered by the existing standing authorization for the user-managed Claude CLI; no per-request approval or placeholder substitution is needed. Honor a narrower user instruction.

Never include credentials, tokens, private keys, raw environment dumps, `.env`, auth config or other secret-bearing content. If secrets would be required, omit that part rather than requesting permission to send them. Pass content through the prompt file, not command arguments.

Ask for concrete alternatives, hidden operational costs, evidence that would change the recommendation, and confidence versus speculation. Require reasoning from the supplied prompt only: no repository inspection, tools, delegation, edits, shell commands, deployment or credential actions.

## Adoption

Treat the answer as review material. Codex checks it against repository facts, accepted contracts and user constraints, then adopts, rejects or identifies evidence still needed. Use `codex-decision-integrity` before reversing an existing material judgment. Report significant findings and residual uncertainty, not the whole debate.
