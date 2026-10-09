---
name: claude-html-report
description: Create a coherent standalone HTML report through bounded Claude composition while Codex retains facts, provenance checks and final artifact verification.
---

# Claude HTML Report

Use for a standalone HTML report whose quality depends on cross-section narrative, coordinated comparisons, annotated assets or dense information architecture. Keep ordinary product UI in `codex-frontend-ui`, and use Markdown, a table or one diagram when it expresses the review task clearly.

Claude owns the initial complete report composition and every editorial revision, including information hierarchy, explanation order, wording, diagrams, HTML and CSS. Codex owns evidence collection, faithful transfer of the user's request, source verification and final artifact inspection, not report editing. Codex must not draft the report for Claude or edit its content, layout or metadata after generation, even for a typo, factual literal or responsive fix. Mechanical asset substitution and unchanged file adoption are the only production-file operations Codex performs. Do not use the strategic-review skills as an artifact authoring substitute.

## Prepare The Contract

Read [report contract](references/report-contract.md). Build its packet from verified sources and the relevant original user request and feedback. Preserve the requested purpose, audience, known background and constraints; keep Codex interpretations distinguishable from user requirements. Explaining what remains to be decided does not authorize asking the reader to approve it or assigning them decision ownership. Separate information required to answer the reader's questions from research available to support those answers. Technical feasibility may require extensive investigation without requiring its implementation details in the main explanation. Do not mark an entire research bundle as load-bearing because it contains one essential conclusion. Supply evidence and comprehension dependencies, not a finished outline, component inventory or prescribed visual format unless the user chose one. Claude selects the main explanation and develops its hierarchy, order and visual system. This is preparation for the existing composition call, not a separate model call, deliverable or approval step. Give each asset an evidenced explanation role; a path or screenshot alone is insufficient.

Do not replace the user's request or feedback with a Codex summary, proposed answer, ranked conclusion or detailed design. Label factual deductions separately from established user decisions. For a structural restart, carry forward verified evidence and still-applicable user constraints, not the superseded artifact as a composition template. Distinguish user-approved reference material from rejected or superseded content; do not append successive old reports and instructions as if all remained current.

When the user supplies a strong reference, analyze its reader questions, explanation units, visual semantics and default reading path, not just its colors or section names. Include transferable observations in the packet as design references, not mandatory structure, without copying organization-specific content. Use the reader-path guidance in the report contract to connect evidence to meaning and, only when requested or established, a reader decision or action.

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

Before adopting Claude's candidate, run `codex-artifact-integrity` with the packet, including the original user request and feedback, as the requirements file and the complete HTML as the candidate. A `review` result keeps the candidate unadopted while Codex verifies the finding and returns any established defect to Claude for correction. An `unavailable` result does not discard the candidate or trigger another Claude call; continue the checks below.

Validate the entire candidate against the original user request and feedback as well as the factual packet before visual polish. Correct a packet that changes the assignment; agreement between Codex's packet and Claude's HTML is not evidence of fidelity to the user:

- every user-required fact and comprehension prerequisite appears in `data-fact`, all final load-bearing facts are visible, and every used ID exists;
- every visible fact has a justified `data-weight`; Claude's weighting serves the user's task and preserves required information rather than merely matching Codex's suggested emphasis or source completeness;
- the first viewport communicates what the report establishes, why it matters and any decision or action that actually exists;
- any visually parallel metrics are intended for comparison and share the relevant definition, unit or denominator, population, time window and aggregation; unrelated numbers remain with the claims they support rather than forming a headline KPI strip;
- unsupported rejected claims, intentionally omitted material and verification bookkeeping have not leaked into defensive copy; actual evaluated alternatives and unresolved requirements appear only where the reader's task needs them;
- visible qualifications are necessary to keep a specific claim true or to change the reader's decision, appear once beside that claim, and use a concrete basis rather than generic labels;
- no follow-up test, open issue, option, risk or next step was invented beyond the packet and reader's task;
- supporting and context detail is compressed, deferred or omitted with a recorded reason, without hiding a prerequisite;
- claims not established by the packet are not rendered as settled, and rejected claims are not asserted or implied;
- every inference in the report metadata is accepted, removed or weakened;
- every information-weighting decision in the report metadata matches the visible main flow, deferred detail and intentional omissions;
- prerequisites precede dependent claims;
- asset placeholders are complete, intentional and attached to the promised explanation;
- the result is one self-contained document without remote executable assets.

Walk through the actual candidate using the original reader questions: identify the main answer and why it matters without opening implementation detail. If every section appears equally important, or the answer requires collecting fragments from technical prose, the hierarchy is not working. Technical detail belongs in the main flow when it changes that answer or is needed to perform the reader's task, not merely because it was investigated. For a reader who needs to understand rather than implement, distinguish the mechanism and its material feasibility boundary from implementation inventories and detailed alternative analyses. Check the visible explanation rather than accepting `REPORT-META` as proof. For a comparison, verify the same criteria and scenario across alternatives; for a workflow, follow an actual case through waiting, action and outcome; for results, verify the stated meaning of the observations. In a diagram, point to the visual distinction that explains the claimed difference or behavior: naming it inside a box is insufficient. Check narrow-width versions for the same relationships, not merely fitting text.

Run desktop and mobile visual QA under `codex-frontend-ui`. Inspect hierarchy, density, wrapping, overflow, contrast, whether the reader can distinguish the decision from reference material, and whether diagrams or comparisons explain the consequence rather than merely label components. A factually complete page that requires the reader to extract the hierarchy from long prose is not accepted.

Claude owns the final spacing and alignment corrections; Codex only inspects them. For reports that use cards, grids, diagrams or repeated layout tracks, preserve Claude's clean candidate and create a temporary QA copy or screenshot overlay that exposes component bounds, intended content insets, row and column tracks, and any baseline guides needed for multi-line labels. Render the overlay at desktop and relevant narrow widths and inspect the complete page and enlarged dense regions. Do not ask Claude to produce the QA overlay, and never publish or adopt it. Send observed defects to Claude, then inspect the corrected candidate again. The generic UI skill's instruction to correct a clean candidate does not grant Codex report-editing authority here.

For feedback affecting purpose, information hierarchy, comparison basis, explanation order, primary visual model, density or several sections, inspect the complete artifact for the affected relationships; this does not itself require whole-report regeneration. Preserve the original purpose, known reader background and effective explanations unless the requested correction changes them. A request for more concrete content is not a request to replace diagrams with prose or tables. Verify consistency across the affected title, first viewport, narrative, diagrams and conclusion, and reconcile source status when the feedback concerns outdated content.

All editorial revisions return to Claude. Keep a bounded correction bounded: supply the current artifact, the user's exact feedback, any verified error and the unaffected content to preserve. Claude returns a complete HTML document because the wrapper writes complete documents; that output format does not authorize redesigning unaffected sections. For a structural restart, use a refreshed source packet rather than treating the rejected artifact as the required baseline. Describe reader-level defects with evidence, not a Codex-authored replacement outline or preferred wording. Check the returned changes against the requested correction and the original purpose. Do not restore Codex-preferred sentences or layouts after inspection.

On wrapper timeout, invalid HTML or non-zero exit, report the route as unavailable together with the wrapper's bounded, redacted diagnostics. Do not retry automatically, switch models or fabricate Claude output.
