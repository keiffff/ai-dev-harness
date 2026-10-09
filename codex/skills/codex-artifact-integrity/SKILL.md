---
name: codex-artifact-integrity
description: Check generated or substantially revised reader-facing artifacts against explicit requirements before adoption.
---

# Codex Artifact Integrity

Use after creating or substantially revising a reader-facing artifact when the request contains preservation constraints, comparison rules, required roles or flows, or a bounded change scope. Do not use for ordinary short replies, source code changes, or pixel-level visual inspection.

This skill verifies artifacts; it grants no editing authority. The producing skill determines who may make corrections. Codex validates findings against the original user request, sources and baseline before accepting them; do not automatically forward reviewer suggestions, rewrite the artifact or add requirements merely because Jev proposed them. A finding needs an evidenced mismatch, not a preference for Codex's wording or structure.

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
- `review`: keep the candidate unadopted while Codex checks the findings against the original requirements, sources and baseline. Reject unsupported findings with a reason; a rejected finding does not require an edit or another model call. Route confirmed defects to the authorized editor under the producing skill, preserving the requested change scope. Review the corrected candidate again if it materially changed. If no findings remain supported, continue the normal acceptance checks without inventing a correction.
- `unavailable`: do not retry automatically and do not discard the candidate. Continue the existing factual, deterministic and visual checks; Jev availability is not a new blocker.

When `--route-checks` is present, use `required_checks` to select the checks that the observed change needs:

- `fact_and_comparison_check`: verify changed claims, metric definitions and comparison conditions against their sources.
- `changed_region_visual`: render and inspect the changed visual region.
- `full_page_visual`: render and inspect the complete artifact because its structure or composition changed broadly.
- `browser_smoke`: open runtime-bearing HTML in its supported environment and confirm that it loads.
- `interaction_journey`: exercise the changed embed, media, control or script-driven path.

The wrapper derives runtime checks from the candidate and baseline before asking Jev. Jev may add checks, but it cannot remove an inherited runtime check. If Jev is unavailable, the deterministic runtime checks remain in `required_checks`; do not add a retry or broaden them merely because routing confidence is unavailable. A selected check still has to be performed with the appropriate source, renderer or browser. The Jev score is routing evidence, not proof that the artifact passed that check.

Jev checks semantic and presentation intent: requested scope, preserved information, comparable metrics, reader-facing copy, and faithful roles or flows. It does not establish pixel overlap, whitespace, clipping, responsive layout or visual hierarchy. Rendered inspection under `codex-frontend-ui` remains authoritative for those properties.

For `claude-html-report`, return confirmed defects to Claude; Codex does not patch the report. For `gemini-japanese-polish`, retain only the factual, explicit-preservation and other concrete repairs authorized by that skill; do not use integrity findings to restore Codex-preferred composition. Inspection instructions in this skill or a visual-review skill do not override either production workflow's editing boundary.
