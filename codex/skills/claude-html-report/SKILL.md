---
name: claude-html-report
description: Create a coherent standalone HTML report through bounded Claude composition while Codex retains facts, provenance checks and final artifact verification.
---

# Claude HTML Report

Use for a standalone HTML report whose quality depends on cross-section narrative, coordinated comparisons, annotated assets or dense information architecture. Keep ordinary product UI in `codex-frontend-ui`, and use Markdown, a table or one diagram when it expresses the review task clearly.

Claude owns the initial complete report composition and any structural recomposition. Codex owns evidence collection, the factual packet, acceptance checks, bounded post-generation edits, deterministic asset embedding and the final file. Do not use the strategic-review skills as an artifact authoring substitute.

## Prepare The Contract

Read [report contract](references/report-contract.md). Build its packet from verified sources before invoking Claude. Treat fact weight as a display contract, not only a confidence label: load-bearing facts belong in the visible narrative, supporting facts earn space only when they change understanding, and context belongs in progressive disclosure, a reference section or the source rather than the main flow. Describe comprehension dependencies rather than prescribing an outline unless the user explicitly requires an order. Give each asset a job in the argument; a path or screenshot alone is insufficient.

Use Opus by default. Pass `--model fable` only when the user's current request explicitly asks for Fable. Model choice does not change the evidence or verification contract.

## Generate One Whole Artifact

Invoking this skill includes standing authorization to send the task-required, non-secret packet to the user-managed Claude CLI. Do not request separate approval or stop merely because the packet contains company-internal, confidential-design or personal information. Keep the packet relevant to the requested report, honor any narrower instruction in the current request, and retain the secret exclusions in the report contract.

Write the packet to a UTF-8 file under `/private/tmp`. Select a new candidate path that does not already exist, then run:

```sh
${CLAUDE_HTML_REPORT_WRAPPER:-$HOME/.local/bin/claude-html-report} \
  --prompt-file "$packet_file" \
  --output-file "$candidate_file"
```

Run the wrapper with normal sandbox permissions. When the token is absent from its environment, the wrapper re-enters through the shared Keychain credential launcher. Mandatory escalation routes the packet through a separate approval reviewer that does not inherit this skill's standing authorization. Do not request escalated permissions solely for Keychain access, Claude/Fable transmission, or writing to the task's configured visualization directory. Escalate only after a concrete sandbox failure that requires access outside the task's existing writable roots, and do not convert that failure into a new content-sharing approval question. If a Claude CLI override is needed, configure `CLAUDE_HTML_REPORT_CLI` with an absolute path. The wrapper enforces safe mode, no tools, one turn and no session persistence; Claude cannot read the repository, inspect assets or write files directly. The wrapper writes only its complete response to a new `.html` candidate.

For images, charts or screenshots, include dimensions, a faithful description and what each asset must demonstrate in the packet. Require `{{ASSET:A1}}` placeholders in Claude's HTML, then have Codex replace them mechanically with local or embedded sources after validating every placeholder. Do not ask Claude to infer unseen image content.

## Accept And Revise

Before adopting Claude's candidate, run `codex-artifact-integrity` with the packet as the requirements file and the complete HTML as the candidate. A `review` result keeps the candidate unadopted while Codex identifies and corrects the concrete offending change. An `unavailable` result does not discard the candidate or trigger another Claude call; continue the checks below.

Validate the entire candidate against the packet before visual polish:

- every load-bearing fact ID appears in `data-fact` and every used ID exists;
- every visible fact has the correct `data-weight`; the main flow is dominated by load-bearing facts rather than source completeness;
- the first viewport communicates what the report establishes, why it matters and any decision or action that actually exists;
- any visually parallel metrics are intended for comparison and share the relevant definition, unit or denominator, population, time window and aggregation; unrelated numbers remain with the claims they support rather than forming a headline KPI strip;
- rejected claims, omitted material, missing evidence and verification process have not leaked into reader-facing sections or defensive copy;
- visible qualifications are necessary to keep a specific claim true or to change the reader's decision, appear once beside that claim, and use a concrete basis rather than generic labels;
- no follow-up test, open issue, option, risk or next step was invented beyond the packet and reader's task;
- supporting and context detail is compressed, deferred or omitted with a recorded reason, without hiding a prerequisite;
- claims not established by the packet are not rendered as settled, and rejected claims are not asserted or implied;
- every inference in the report metadata is accepted, removed or weakened;
- every information-weighting decision in the report metadata matches the visible main flow, deferred detail and intentional omissions;
- prerequisites precede dependent claims;
- asset placeholders are complete, intentional and attached to the promised explanation;
- the result is one self-contained document without remote executable assets.

Run desktop and mobile visual QA under `codex-frontend-ui`. Inspect hierarchy, density, wrapping, overflow, contrast, whether the reader can distinguish the decision from reference material, and whether diagrams or comparisons explain the consequence rather than merely label components. A factually complete page that requires the reader to extract the hierarchy from long prose is not accepted.

Codex, not Claude, owns the final spacing and alignment pass. For reports that use cards, grids, diagrams or repeated layout tracks, preserve Claude's clean candidate and create a temporary QA copy or screenshot overlay that exposes component bounds, intended content insets, row and column tracks, and any baseline guides needed for multi-line labels. Render the overlay at desktop and relevant narrow widths, inspect the complete page and enlarged dense regions, then make bounded CSS or HTML corrections in the clean candidate. Regenerate the overlay after corrections and render the clean report once more. Do not ask Claude to produce the QA overlay, do not publish it, and do not return to Claude for padding, line spacing, overflow or alignment corrections that leave the report's narrative architecture intact.

Treat feedback about the report's purpose, information hierarchy, comparison basis, explanation order, primary visual model, density, or a problem repeated across sections as whole-report feedback. Re-read and render the complete artifact before editing; do not patch only the sentence or block named by the user. Preserve the parts that still work, but verify that the correction is consistent across the title, first viewport, narrative, diagrams and conclusion.

Classify a requested revision by its effect on the report, not by who generated the file:

- **Bounded Codex edit:** edit the accepted HTML directly when the target is specific and the report's narrative architecture, fact weighting and cross-section relationships remain intact. This includes wording, labels and typo fixes; color themes, CSS tokens, spacing, typography, grid alignment and responsive overflow; corrections found through the temporary QA overlay; deterministic asset or syntax repairs; and isolated factual-literal or metadata corrections. Preserve or consistently update fact, weight and `REPORT-META` markers, then repeat the relevant factual and visual checks.
- **Structural Claude recomposition:** return to Claude only when the change alters the ranked takeaway or reader decision, materially reweights facts across sections, changes prerequisite order or comparison structure, replaces the primary visual model, or otherwise requires coordinated redesign of the whole report. Send a refreshed packet with the new evidence, accepted decisions and observed reader-level symptoms; Claude returns one complete replacement document.

Do not send a revision to Claude solely because Claude produced the original HTML. Do not use whole-document regeneration for a color theme, localized wording, a few stale literals, metadata cleanup or a bounded responsive fix. If repeated local edits begin to change the information hierarchy or make sections inconsistent, stop patching and use structural recomposition from a corrected source packet.

On wrapper timeout, invalid HTML or non-zero exit, report the route as unavailable together with the wrapper's bounded, redacted diagnostics. Do not retry automatically, switch models or fabricate Claude output.
