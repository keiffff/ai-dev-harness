---
name: codex-frontend-ui
description: Build or review UI using existing design constraints, concrete visual preferences and proportionate visual verification.
---

# Codex Frontend UI

For an existing product, follow its components, tokens, density, icons and interaction patterns. For a standalone artifact, choose a visual direction suited to the primary user task. A strategy-only request returns a proposal; an implementation request authorizes routine UI choices within its scope.

## Design And Review Criteria

Preserve information hierarchy, readable density, responsive wrapping and relevant loading/empty/error/focus states. Use existing design examples and component previews to establish conventions. Resolve a material conflict between the requested design and product workflow before changing that workflow; an ordinary new component alone is not an approval gate.

For freeform work, prefer restrained typography and color, useful visual assets and direct access to the task. Avoid nested cards, oversized tool headings, decorative gradient blobs, padding that hides weak structure and copy explaining how the UI was designed.

For a visual representation of a plan/spec/schema, read [review visualization](references/review-visualization.md). Check source fidelity before visual polish; retain exact contracts and open decisions in the source document.

## Verification Boundary

Start with isolated component, static artifact or screenshot checks when sufficient. Inspect overflow, long labels, mobile layout, keyboard focus, labels, contrast and relevant interaction states.

Browser/CUA use requires the current-turn `browser-control: allow` under AGENTS.md, including isolated pages. Local rendering without Browser/CUA is a separate verification path. Heavy verification requiring a full app server, login, external services or deep navigation needs the user's authorization for that setup; use existing authorization without asking again. Report the specific blocked visual check when unavailable.

Use `codex-code-review` for behavioral defects and `codex-interface-review` for changed public contracts as needed. Report the user-visible result, visual evidence and material gaps; no mandatory mode labels or file-by-file report.
