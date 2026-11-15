---
name: codex-artifact-integrity
description: Check interactive HTML for lost behavior or broken comparison operations, without editing the artifact.
---

# Codex Artifact Integrity

Use for interactive HTML with controls, media or embeds when the request requires preserving existing behavior or comparing alternatives. Ordinary prose, static reports, SVGs and diagrams do not enter this semantic review. Their existing factual and rendered checks remain with the producing skill. An explicit user request to inspect a static artifact may use `--all-artifacts`; do not add that option to bypass ordinary routing.

This skill verifies artifacts; it grants no editing authority. The producing skill determines who may make corrections. Codex validates findings against the original user request, sources and baseline before accepting them; do not automatically forward reviewer suggestions, rewrite the artifact or add requirements merely because Jev proposed them. For a product mockup, follow the affected control through its actual runtime owner instead of judging it by other prose in the report. Read a missing owner/source before selecting a correction; an unverified connection is not a confirmed defect. A finding needs an evidenced mismatch, not a preference for Codex's wording or structure.

Keep the relevant original user request in a UTF-8 file, separate from producer notes or a requirements summary. An assistant proposal is not a user requirement. Keep generated output at a candidate path until review completes. For an existing artifact or product mockup, use the actual pre-change artifact or relevant UI source as the baseline, not merely an earlier assistant-generated alternative. Run:

```sh
${JEV_ARTIFACT_REVIEW_WRAPPER:-$HOME/.local/bin/jev-artifact-review} \
  --request-file "$request_file" \
  --requirements-file "$requirements_file" \
  --candidate-file "$candidate_file" \
  --baseline-file "$baseline_file" \
  --route-checks
```

Omit `--baseline-file` for a new artifact. The wrapper sends the non-secret requirements and artifact to the user-managed Jev API under the same standing authorization as Jev permission review. Do not send credentials, tokens, private keys, raw environment dumps, `.env` values or authentication configuration.

The wrapper saves a content-bound `.integrity-review.json` receipt beside the candidate. Identical request, evidence, baseline and candidate reuse that result, including empty findings or unavailability; do not delete the receipt or change inputs merely to obtain another review. An actual requested change or repaired defect invalidates the affected result.

The wrapper returns:

- `pass`: the detector did not flag a violation; adopt only after the normal source, factual and visual/runtime checks. The score does not establish fidelity to the original request.
- `review`: the wrapper uses the existing tool-free Claude reviewer once to return `concrete_review.findings`, with exact request/baseline and candidate quotes. Check those mismatches against the original sources. Reject unsupported findings with a reason; a rejected finding does not require an edit or another model call. If concrete findings are empty or unavailable, no correction call is needed. Do not invent a defect from the score. For a Claude-owned artifact, pass the unedited receipt via `claude-html-report --integrity-review-file <receipt> --confirmed-finding-index <zero-based index> --edit-file <candidate>`, the same original request and raw evidence. Select only findings whose mismatch you verified; never select the whole list merely because it scored `review`. Without selected findings the editor does not start. The wrapper verifies and transfers the unchanged requirements and baseline automatically. Claude makes the bounded correction; Codex supplies no patch, replacement copy or added requirements. Do not present a candidate while a confirmed defect remains unresolved.
- `unavailable`: do not retry automatically and do not discard the candidate. Continue the existing factual, deterministic and visual checks; Jev availability is not a new blocker.
- `skipped`: this is not interactive HTML. Continue the producing skill without a semantic-review call or correction.

When `--route-checks` is present, use `required_checks` to select the checks that the observed change needs:

- `fact_and_comparison_check`: verify changed claims, metric definitions and comparison conditions against their sources.
- `changed_region_visual`: render and inspect the changed visual region.
- `full_page_visual`: render and inspect the complete artifact because its structure or composition changed broadly.
- `browser_smoke`: open runtime-bearing HTML in its supported environment and confirm that it loads.
- `interaction_journey`: exercise the changed embed, media, control or script-driven path.

The wrapper derives runtime checks from the candidate and baseline before asking Jev. Jev may add checks, but it cannot remove an inherited runtime check. If Jev is unavailable, the deterministic runtime checks remain in `required_checks`; do not add a retry or broaden them merely because routing confidence is unavailable. A selected check still has to be performed with the appropriate source, renderer or browser. The Jev score is routing evidence, not proof that the artifact passed that check.

Jev supplies scores for semantic risk and verification routing, not concrete findings. Claude findings supply quoted mismatches, not rendered proof. Their review evidence does not establish pixel overlap, whitespace, clipping, responsive layout or visual hierarchy. An image embedded in HTML is not a text-readable UI baseline. Rendered comparison under `codex-frontend-ui` remains authoritative for those properties.

For `claude-html-report`, return confirmed defects to Claude; Codex does not patch the report. For `gemini-japanese-polish`, retain only the factual, explicit-preservation and other concrete repairs authorized by that skill; do not use integrity findings to restore Codex-preferred composition. Inspection instructions in this skill or a visual-review skill do not override either production workflow's editing boundary.
