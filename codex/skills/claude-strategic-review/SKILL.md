---
name: claude-strategic-review
description: Challenge problem framing and strategic direction with Claude against user goals and evidence; Codex owns execution and judgment.
---

# Claude Strategic Review

Use when the problem framing or overall direction needs an external challenge, not merely an implementation-conformance review. Claude examines whether the proposed work addresses the user's actual objective before evaluating how to implement it. Codex owns implementation, debugging and evidence-based adoption; the producing skill owns reader-facing prose.

Read [reviewer contract](references/reviewer-contract.md) for independent framing, prompt scope, standing authorization, adoption and user-visible reporting. Use this default Claude route unless Fable is explicitly requested.

## Execution

For code reviews, use `codex-code-review`'s `run-advisor` to assemble the originals, call this wrapper and bind every returned objection automatically. Do not transcribe the request or extract a separate objection list. For other strategic questions, pass an existing original prompt with the raw evidence and distinguish any proposed approach from those originals:

```sh
${CLAUDE_STRATEGIC_REVIEW_WRAPPER:-$HOME/.local/bin/claude-strategic-review} --prompt-file "$prompt_file"
```

Use escalated sandbox permissions for the configured wrapper. When the token is absent from its environment, the wrapper re-enters through the shared Keychain credential launcher. Configure an absolute `CLAUDE_STRATEGIC_CLI` path. If that CLI lacks `--safe-mode`, stop this advisor route; do not substitute another installation.

The wrapper uses `claude-opus-5-5`, safe mode, no tools, one turn and no session persistence. It authenticates with OAuth; do not add `--bare`, which disables OAuth authentication. Those controls, not prompt wording, enforce execution scope. Its default timeout is 600 seconds; poll while heartbeat diagnostics arrive. On timeout or non-zero exit, report advisor unavailability and continue the Codex task without automatic retries or fabricated feedback.
