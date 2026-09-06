---
name: claude-strategic-review
description: Get a bounded Claude architecture or maintainability second opinion through the configured wrapper; Codex retains repo work and decisions.
---

# Claude Strategic Review

Use for a broader architecture, migration or maintainability opinion when requested or useful. Codex owns implementation, debugging, prose and final judgment.

Read [reviewer contract](references/reviewer-contract.md) for prompt scope, standing authorization and adoption rules. Use this default Claude route unless Fable is explicitly requested.

## Execution

Write the review prompt to a UTF-8 file under `/private/tmp`, then pass only its path:

```sh
${CLAUDE_STRATEGIC_REVIEW_WRAPPER:-$HOME/.local/bin/claude-strategic-review} --prompt-file "$prompt_file"
```

Use escalated sandbox permissions for the configured wrapper, which accesses its own Keychain credential. Configure an absolute `CLAUDE_STRATEGIC_CLI` path. If that CLI lacks `--safe-mode`, stop this advisor route; do not substitute another installation.

The wrapper uses `claude-opus-5`, safe mode, no tools, one turn and no session persistence. Those controls, not prompt wording, enforce execution scope. Its default timeout is 600 seconds; poll while heartbeat diagnostics arrive. On timeout or non-zero exit, report advisor unavailability and continue the Codex task without automatic retries or fabricated feedback.
