---
name: codex-frontend-ui
description: Build or review UI using existing design constraints, concrete visual preferences and proportionate visual verification.
---

# Codex Frontend UI

For an existing product, follow its components, tokens, density, icons and interaction patterns. For a standalone artifact, choose a visual direction suited to the primary user task. When a standalone HTML report depends on cross-section narrative, coordinated comparisons, annotated assets or dense information architecture, use `claude-html-report` for whole-artifact composition and keep factual verification here. A strategy-only request returns a proposal; an implementation request authorizes routine UI choices within its scope.

## Design And Review Criteria

Preserve information hierarchy, readable density, responsive wrapping and relevant loading/empty/error/focus states. Use existing design examples and component previews to establish conventions. Resolve a material conflict between the requested design and product workflow before changing that workflow; an ordinary new component alone is not an approval gate.

Treat visual alignment as a comparison claim. Do not create a headline KPI row, equally weighted statistic cards or a shared chart scale for numbers that differ in metric definition, unit or denominator, population, time window or aggregation unless the source explicitly defines a meaningful comparison. Keep unrelated numbers beside the specific claims they support; a first viewport does not need a metric strip.

Do not turn evidence hygiene into visible UI. Warning cards, caveat badges, unresolved-item blocks, scope disclaimers and repeated footnotes earn space only when they prevent a materially false reading or change the user's decision. Otherwise omit the unsupported claim or irrelevant material instead of displaying an explanation that it was excluded. Keep a necessary qualification adjacent to its claim and state it once.

For freeform work, prefer restrained typography and color, useful visual assets and direct access to the task. Avoid nested cards, oversized tool headings, decorative gradient blobs, padding that hides weak structure and copy explaining how the UI was designed.

For a visual representation of a plan/spec/schema, read [review visualization](references/review-visualization.md). Check source fidelity before visual polish; retain exact contracts and open decisions in the source document.

## Verification Boundary

For a new or substantially revised HTML report, SVG, diagram or other reader-facing artifact with explicit preservation or comparison constraints, run `codex-artifact-integrity` before adoption. Supply the user requirements, the complete candidate and, for an existing artifact, its pre-edit baseline. Keep this semantic check separate from rendered inspection.

Start with isolated component, static artifact or screenshot checks when sufficient. Inspect overflow, long labels, mobile layout, keyboard focus, labels, contrast and relevant interaction states.

After changing an SVG, diagram or report layout, render the final artifact and inspect both the changed region and the complete canvas. Check text against icons and shapes, every arrow along its full path, nearby whitespace, clipping and density. Source validity, successful generation or non-overlapping bounding boxes alone do not establish visual completion.

For SVGs, diagrams and card- or grid-based static artifacts, a clean render alone is insufficient. Preserve the clean candidate, then create a temporary QA copy with visible component bounds, intended content insets and the main row or column guides overlaid. Render that QA copy and inspect the complete canvas plus enlarged crops of each dense region. Text, icons and arrowheads must stay inside the intended inset unless the composition explicitly places them outside it; multi-line labels must retain visible line spacing; repeated cards must align to the declared tracks. Correct the clean candidate, regenerate the overlay and inspect again. Never ship or adopt the QA overlay itself, and do not claim completion from source coordinates without inspecting the rendered overlay and the final clean render.

Use the in-app browser with an explicit `iab` selector for Browser/CUA verification; no approval line is needed. Do not select the user's browser or enumerate their tabs. External browser exceptions follow AGENTS.md. Local rendering without Browser/CUA is a separate verification path. Heavy verification requiring a full app server, login, external services or deep navigation needs the user's authorization for that setup; use existing authorization without asking again. Report the specific blocked visual check when unavailable.

Use `codex-code-review` for behavioral defects and `codex-interface-review` for changed public contracts as needed. Report the user-visible result, visual evidence and material gaps; no mandatory mode labels or file-by-file report.
