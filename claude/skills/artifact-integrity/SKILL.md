---
name: artifact-integrity
description: Verify a generated or substantially revised reader-facing artifact against explicit preservation, comparison or interaction requirements.
---

# Artifact Integrity

Use for material artifacts with explicit preservation/comparison/role/flow constraints, not ordinary short replies or code changes. This check is evidence, not new editing authority or a mandatory external reviewer for every task.

Keep the original user request, producer notes and candidate in separate non-secret UTF-8 files. Do not promote assistant proposals to user requirements. For edits and product mockups, preserve the actual pre-change artifact or relevant UI source, not just an earlier generated alternative. Run the existing wrapper:

```sh
~/.local/bin/jev-artifact-review --request-file "$request_file" --requirements-file "$requirements_file" --candidate-file "$candidate_file" --route-checks
```

Add `--baseline-file "$baseline_file"` for an edit. Existing standing authorization covers task-relevant non-secret artifacts; never send credentials, auth configuration or environment values.

`pass` still needs normal source and runtime verification. For `review`, the wrapper calls the existing tool-free Claude reviewer once and returns quoted mismatches in `concrete_review.findings`. Check these against original sources; discard unsupported preferences without rewriting. Correct confirmed defects only within scope. If concrete review is unavailable or finds no evidenced defect, resolve the score through direct source comparison rather than inventing a defect or retrying. For `unavailable`, perform existing checks directly, without discarding the artifact.

Use `required_checks` to select factual/comparison checks, changed-region/full-page visual inspection, browser smoke and interaction journeys. A Jev score is not a rendered or runtime test. Deterministically required runtime checks remain necessary even if Jev is unavailable. Do not add universal extra checks merely because the reviewer suggested them.
