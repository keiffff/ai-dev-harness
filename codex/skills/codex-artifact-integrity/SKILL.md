---
name: codex-artifact-integrity
description: Check generated or substantially revised reader-facing artifacts against explicit requirements before adoption.
---

# Codex Artifact Integrity

Use after creating or substantially revising a reader-facing artifact when the request contains preservation constraints, comparison rules, required roles or flows, or a bounded change scope. Do not use for ordinary short replies, source code changes, or pixel-level visual inspection.

Keep the user's explicit requirements in a UTF-8 file. Keep generated output at a candidate path until review completes. For an edit to an existing artifact, also preserve the pre-edit file as the baseline. Run:

```sh
${JEV_ARTIFACT_REVIEW_WRAPPER:-$HOME/.local/bin/jev-artifact-review} \
  --requirements-file "$requirements_file" \
  --candidate-file "$candidate_file" \
  --baseline-file "$baseline_file" \
  --route-checks
```

Omit `--baseline-file` for a new artifact. The wrapper sends the non-secret requirements and artifact to the user-managed Jev API under the same standing authorization as Jev permission review. Do not send credentials, tokens, private keys, raw environment dumps, `.env` values or authentication configuration.

The wrapper returns one of three decisions:

- `pass`: adopt the candidate after the normal factual, deterministic and visual checks.
- `review`: do not adopt the candidate as-is. Compare it with the requirements and baseline, then correct only the concrete offending changes. Review the corrected candidate again if it materially changed.
- `unavailable`: do not retry automatically and do not discard the candidate. Continue the existing factual, deterministic and visual checks; Jev availability is not a new blocker.

When `--route-checks` is present, use `required_checks` to select the checks that the observed change needs:

- `fact_and_comparison_check`: verify changed claims, metric definitions and comparison conditions against their sources.
- `changed_region_visual`: render and inspect the changed visual region.
- `full_page_visual`: render and inspect the complete artifact because its structure or composition changed broadly.
- `browser_smoke`: open runtime-bearing HTML in its supported environment and confirm that it loads.
- `interaction_journey`: exercise the changed embed, media, control or script-driven path.

The wrapper derives runtime checks from the candidate and baseline before asking Jev. Jev may add checks, but it cannot remove an inherited runtime check. If Jev is unavailable, the deterministic runtime checks remain in `required_checks`; do not add a retry or broaden them merely because routing confidence is unavailable. A selected check still has to be performed with the appropriate source, renderer or browser. The Jev score is routing evidence, not proof that the artifact passed that check.

Jev checks semantic and presentation intent: requested scope, preserved information, comparable metrics, reader-facing copy, and faithful roles or flows. It does not establish pixel overlap, whitespace, clipping, responsive layout or visual hierarchy. Rendered inspection under `codex-frontend-ui` remains authoritative for those properties.
