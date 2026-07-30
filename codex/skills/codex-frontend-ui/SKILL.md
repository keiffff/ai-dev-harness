---
name: codex-frontend-ui
description: Use when Codex needs frontend UI strategy, visual direction, UI implementation guidance, design-system adherence, or visual QA for web UI, React components, HTML reports, mocks, dashboards, Storybook stories, Tailwind, shadcn/ui, Base UI, MUI, Figma-derived designs, responsive layout, typography, spacing, overflow, or screenshot review. Use before or during UI work when the task could affect visual quality or existing design consistency.
---

# Codex Frontend UI

Use this skill when frontend work depends on visual quality, information architecture, or design-system consistency. This skill does not replace implementation, code review, or project-specific design rules; it controls the UI workflow before and after implementation.

## Mode Selection

Start by selecting exactly one primary mode. Switch modes only when the task clearly moves to a new phase.

| Mode | Use when | Default action |
| --- | --- | --- |
| `strategy` | The user wants to decide how a workflow, data set, or feature should be shown. | Discuss and propose. Do not implement unless the user asks. |
| `freeform` | Building standalone artifacts such as HTML reports, mocks, explainers, demos, or visualizations. | Design and build a polished self-contained UI. |
| `adherence` | Changing an existing product UI or following Figma, Tailwind, shadcn/ui, Base UI, MUI, or local components. | Read existing UI patterns first and conform to them. |
| `qa` | Reviewing an existing UI, screenshot, diff, Storybook story, or generated artifact. | Inspect visual quality, responsive behavior, and state coverage. |

If the user is asking for implementation inside an existing product, default to `adherence`. If the user is asking for a report, mock, or artifact with visual freedom, default to `freeform`. If the user is asking what UI would work best, default to `strategy`.

## Strategy Mode

Use `strategy` to decide the UI before building it.

Clarify or infer:
- primary user and main task;
- operation frequency;
- information volume and hierarchy;
- whether the screen is for input, review, comparison, monitoring, exploration, or confirmation;
- required states such as empty, loading, error, disabled, selected, and completed;
- whether an existing product UI or design system constrains the answer.

Return:
- recommended screen structure;
- primary and secondary tasks;
- UI pattern choice, such as table, form, card list, timeline, dashboard, wizard, command palette, or split pane;
- rejected alternatives and why;
- open decisions before implementation.

Use web research only when the UI problem depends on current ecosystem conventions, accessibility guidance, or unfamiliar domain patterns. When browsing, prefer primary docs and high-quality design-system references.

Do not implement in `strategy` mode unless the user explicitly asks to proceed.

## Freeform Mode

Use `freeform` for standalone UI artifacts where visual direction is open.

When the artifact visualizes an existing plan, design doc, OpenSpec change, schema, process, or other canonical source for human review, read `references/review-visualization.md`. Treat this as a review projection within `freeform`, not as another mode.

Prioritize:
- clear information hierarchy;
- readable density;
- stable responsive layout;
- restrained color and typography;
- domain-appropriate visual tone;
- direct access to the primary task.

Avoid:
- nested cards;
- oversized hero text inside tools, dashboards, sidebars, panels, or compact surfaces;
- decorative gradient blobs, orbs, bokeh, and generic abstract backgrounds;
- one-note palettes dominated by a single hue;
- padding used to hide weak information structure;
- in-app explanatory text that describes how the UI was designed;
- text buttons where a familiar icon button would be clearer.

Use visual assets when the artifact benefits from them. For websites, games, or rich visual artifacts, do not rely on plain gradient/SVG decoration when a relevant image, generated bitmap, screenshot, or real asset would better communicate the subject.

## Adherence Mode

Use `adherence` when modifying existing UI.

Before editing, read the nearest relevant examples:
- layout and page shells;
- forms, tables, modals, drawers, tabs, menus, empty states, loading states, and error states;
- token usage for spacing, color, typography, border radius, and shadows;
- icon library;
- responsive patterns;
- Storybook stories or visual tests when present;
- Figma references if provided or connected.

Rules:
- Do not invent a new visual language.
- Prefer existing components and tokens over new CSS.
- Match existing density, hierarchy, spacing, and interaction states.
- Add a new component, token, or layout rule only when existing patterns cannot express the required behavior.
- If Figma and implementation patterns conflict, stop and explain the conflict before choosing.

Stop and ask before implementation if:
- a new component or token seems necessary;
- the proposed UI changes an established product workflow;
- responsive behavior or accessibility expectations are unclear;
- existing design-system constraints cannot support the requested UI;
- a service-backed screen requires heavy setup for visual verification.

## QA Mode

Check the UI against the user-visible task, not just the code.

For a review projection, check source fidelity before visual quality. Confirm that load-bearing entities, relationships, states, ordering, values, uncertainty, and open decisions are represented without unsupported additions.

Review:
- primary task visibility;
- heading hierarchy and typography scale;
- spacing within and between sections;
- table, form, card, and list density;
- text wrapping, truncation, overflow, and long labels;
- desktop and mobile layout stability;
- hover, focus, selected, disabled, loading, empty, and error states;
- icon/button affordance;
- color, shadow, border, and radius consistency;
- accessibility basics such as keyboard focus, contrast, labels, and target size.

Do not run broad e2e flows just to inspect UI unless the user explicitly asks. Prefer isolated screenshot or component-level checks.

## Screenshot Boundary

Codex may run screenshot checks automatically only when the target is isolated and self-contained.

Allowed automatic screenshot checks:
- static HTML;
- generated reports;
- standalone mock pages;
- Storybook stories;
- isolated component previews;
- local files that can be opened without app setup.

Do not automatically start or navigate a full application for visual checks.

Ask the user before browser or dev-server based verification when the target requires:
- full app dev server;
- login;
- DB, API, Docker, or external service;
- seeded state;
- deep navigation inside an existing product;
- long browser operation.

When automatic screenshot verification is not appropriate, report the expected visual checks and ask the user to launch the app, provide a screenshot, or explicitly approve the heavier verification path.

## Relationship To Other Skills

- Use `codex-context-engineering` first if UI conventions are unknown and need repository context.
- Use `codex-incremental-implementation` for multi-file implementation after UI direction is clear.
- Use `codex-code-review` for bug-first diff review after implementation.
- Use `codex-interface-review` if UI changes affect API, schema, persisted state, or public component contracts.
- Use `codex-decision-doc` for the canonical decision record; use `freeform` only for a derived review projection when a standalone visual surface materially improves review.
- Use `codex-writing` only for prose deliverables, not UI layout decisions.
- Use strategic advisors only for UI strategy or visual direction review; do not let sidecars edit production code or make final design-system decisions.

## Final Report

Report UI work in terms of:
- selected mode;
- visual or design-system constraints used;
- user-visible behavior and layout changes;
- screenshot or QA result;
- unverified visual risks;
- decisions that still need human judgment.

Do not produce file-by-file UI change logs unless the files are the subject of the review.
