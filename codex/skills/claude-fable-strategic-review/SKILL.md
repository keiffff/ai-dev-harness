---
name: claude-fable-strategic-review
description: Use Claude Fable 5 for an explicitly requested strategic second opinion through its configured wrapper.
---

# Claude Fable Strategic Review

Use only when the user explicitly requests Fable 5 or a stronger-than-usual Claude strategic review. Keep the existing explicit-only invocation policy.

Read the shared [reviewer contract](../claude-strategic-review/references/reviewer-contract.md). It owns prompt scope, standing authorization, privacy and adoption; this skill selects the Fable wrapper.

Write the prompt under `/private/tmp`, then pass only the path:

```sh
${CLAUDE_FABLE_STRATEGIC_REVIEW_WRAPPER:-$HOME/.local/bin/claude-fable-strategic-review} --prompt-file "$prompt_file"
```

Use escalated sandbox permissions for the configured wrapper's Keychain access. Codex retains repository work and final judgment. Report wrapper failures as advisor unavailability; do not switch credentials, execute suggested actions or fabricate a review.
