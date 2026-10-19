---
name: claude-html-report
description: Create and directly revise HTML reports with Claude; Codex transfers evidence and verifies facts, provenance and the artifact.
---

# Claude HTML Report

Use for a standalone HTML report whose quality depends on cross-section narrative, coordinated comparisons, annotated assets or dense information architecture. Keep ordinary product UI in `codex-frontend-ui`, and use Markdown, a table or one diagram when it expresses the review task clearly.

Claude owns the initial complete report composition and every editorial revision, including information hierarchy, explanation order, wording, diagrams, HTML and CSS. Codex owns evidence collection, faithful transfer of the user's request, source verification and final artifact inspection, not report editing. Codex must not draft the report for Claude or edit its content, layout or metadata after generation, even for a typo, factual literal or responsive fix. Mechanical asset substitution and unchanged file adoption are the only production-file operations Codex performs. Do not use the strategic-review skills as an artifact authoring substitute.

## Prepare The Contract

Read [report contract](references/report-contract.md). Supply the user's relevant request and feedback verbatim, plus the original evidence files. Do not write a task-specific packet, source summary, design brief, ranked takeaway, information budget or comprehension dependencies for Claude. Claude derives these from the original request and evidence. Codex owns collection and verification; Claude owns interpretation and composition. Do not mark an entire research bundle as load-bearing because it contains one essential conclusion; source completeness is not presentation priority.

Use primary documents, source code, raw measurements, logs and actual artifacts as evidence. Preserve their contents rather than rewriting them into a fact ledger or substituting Codex deductions. Source IDs and hashes are mechanical provenance, not editorial instructions. Do not disguise a Codex-authored brief as an evidence file. Keep the packet relevant to the user's task without selecting excerpts merely to steer Claude toward a preferred answer.

For a design reference, pass the original HTML and relevant CSS themselves through `--evidence-file`; a path alone is not the content, and a verbal description is not the design system. Claude analyzes the reference directly. For a structural restart, retain the original request and sources rather than treating a rejected artifact as the required template. Keep reference documents distinct from current-product specifications.

Use Opus by default. Pass `--model fable` only when the user's current request explicitly asks for Fable. Model choice does not change the evidence or verification contract.

## Revise By Direct File Editing

For revisions use `--edit-file`, not `--output-file`. Preserve a before copy in the task directory. Pass the user's request verbatim and raw source/candidate quotes, measurements or logs of the defect; do not prescribe replacement wording, a patch or an outline. Claude reads the artifact itself, so do not duplicate its full contents in the evidence packet.

```sh
${CLAUDE_HTML_REPORT_WRAPPER:-$HOME/.local/bin/claude-html-report} \
  --request-file "$request_file" \
  --evidence-file "$observations_file" \
  --edit-file "$candidate_file" \
  --trace-file "$new_trace_file"
```

Claude uses Read and localized Edit operations on the named file. The wrapper starts in an empty directory, permits Read/Edit for that artifact only and denies unapproved operations. Shell, network, general Write tools and permission bypass are not enabled. It validates the edited file, not the final prose response. Inspect the trace and actual diff for the requested correction, retained corrections and unaffected CSS/content. Failure can leave partial edits; retain and inspect them rather than silently regenerating. A structural rewrite needs the user's request.

## Create A New Artifact

Invoking this skill includes standing authorization to send the task-required, non-secret packet to the user-managed Claude CLI. Do not request separate approval or stop merely because the packet contains company-internal, confidential-design or personal information. Keep the packet relevant to the requested report, honor any narrower instruction in the current request, and retain the secret exclusions in the report contract.

Save the user's verbatim request and feedback to a UTF-8 file in a task-specific directory under `/private/tmp`. Select a new candidate path that does not already exist. The wrapper packages the request and complete source contents without a Codex-written intermediary:

```sh
${CLAUDE_HTML_REPORT_WRAPPER:-$HOME/.local/bin/claude-html-report} \
  --request-file "$request_file" \
  --evidence-file "$source_file" \
  --output-file "$candidate_file"
```

Run the wrapper with normal sandbox permissions. When the token is absent from its environment, the wrapper re-enters through the shared Keychain credential launcher. Mandatory escalation routes the packet through a separate approval reviewer that does not inherit this skill's standing authorization. Do not request escalated permissions solely for Keychain access, Claude/Fable transmission, or writing to the task's configured visualization directory. Escalate only after a concrete sandbox failure that requires access outside the task's existing writable roots, and do not convert that failure into a new content-sharing approval question. If a Claude CLI override is needed, configure `CLAUDE_HTML_REPORT_CLI` with an absolute path. For new-file creation, the wrapper enforces safe mode, no tools, one turn and no session persistence, and writes the complete response to a new `.html` candidate. Existing-file revisions use the scoped Read/Edit mode above instead of returning a replacement document.

Repeat `--evidence-file` for additional sources; omit it when the request needs none. The existing `--prompt-file` spelling is an alias for the verbatim request, not a route for a synthesized brief. Do not append the report contract or a Codex interpretation to that file. This wrapper transfers UTF-8 sources, not image pixels. Original image captions and mechanically measured dimensions may be evidence; do not replace the image with a Codex-authored visual summary or claim Claude saw it. Preserve the existing `{{ASSET:A1}}` substitution mechanism when a source establishes that mapping.

## Accept And Revise

Before adopting Claude's candidate, run `codex-artifact-integrity` with the original request and evidence as requirements and the complete HTML as the candidate. A `review` result keeps the candidate unadopted while Codex verifies the finding. An `unavailable` result does not discard the candidate or trigger another Claude call; continue the checks below.

Validate the entire candidate against the original user request and feedback as well as the factual packet before visual polish. Correct a packet that changes the assignment; agreement between Codex's packet and Claude's HTML is not evidence of fidelity to the user:

- every user-required fact and comprehension prerequisite appears in `data-fact`, all final load-bearing facts are visible, and every used ID maps to original evidence in Claude's fact ledger;
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

Walk through the actual candidate using the original reader questions: identify the main answer and why it matters without opening implementation detail. If every section appears equally important, or the answer requires collecting fragments from technical prose, the hierarchy is not working. Technical detail belongs in the main flow when it changes that answer or is needed to perform the reader's task, not merely because it was investigated. For a reader who needs to understand rather than implement, distinguish the mechanism and its material feasibility boundary from implementation inventories and detailed alternative analyses. Check the visible explanation rather than accepting `REPORT-META` as proof. For a comparison, verify the same criteria and scenario across alternatives; for a workflow, follow an actual case through waiting, action and outcome; for results, verify the stated meaning of the observations. In a diagram, point to the visual distinction that explains the claimed difference or behavior: naming it inside a box is insufficient. When narrow widths are in scope, check the same relationships, not merely fitting text.

Run visual QA under `codex-frontend-ui` at the intended viewing size. Add mobile layout work and narrow-width QA only when the request or established viewing context includes phone use. For desktop reading or presentation, do not add mobile checks or responsive revisions solely because the deliverable is HTML; an unspecified device does not create a mobile requirement. Inspect hierarchy, density, wrapping, overflow, contrast, whether the reader can distinguish the decision from reference material, and whether diagrams or comparisons explain the consequence rather than merely label components. A factually complete page that requires the reader to extract the hierarchy from long prose is not accepted.

Claude owns the final spacing and alignment corrections; Codex only inspects them. For reports that use cards, grids, diagrams or repeated layout tracks, preserve Claude's clean candidate and create a temporary QA copy or screenshot overlay that exposes component bounds, intended content insets, row and column tracks, and any baseline guides needed for multi-line labels. Render the overlay at the intended viewing size and any narrow widths already in scope and inspect the complete page and enlarged dense regions. Do not ask Claude to produce the QA overlay, and never publish or adopt it. Send observed defects to Claude, then inspect the corrected candidate again. The generic UI skill's instruction to correct a clean candidate does not grant Codex report-editing authority here.

For feedback affecting purpose, information hierarchy, comparison basis, explanation order, primary visual model, density or several sections, inspect the complete artifact for the affected relationships; this does not itself require whole-report regeneration. Preserve the original purpose, known reader background and effective explanations unless the requested correction changes them. A request for more concrete content is not a request to replace diagrams with prose or tables. Verify consistency across the affected title, first viewport, narrative, diagrams and conclusion, and reconcile source status when the feedback concerns outdated content.

All editorial revisions return to Claude through `--edit-file`. Keep a bounded correction bounded: supply the user's exact feedback and raw evidence of the verified error. Do not turn the observation into proposed copy, a replacement outline or a new brief. Direct file access does not authorize redesigning unaffected sections. For a user-requested structural restart, supply the original request and relevant sources rather than treating the rejected artifact as the required baseline. Check the actual diff against the correction and original purpose. Do not restore Codex-preferred sentences or layouts after inspection.

On wrapper timeout, invalid HTML or non-zero exit, report the route as unavailable together with the wrapper's bounded, redacted diagnostics. Do not retry automatically, switch models or fabricate Claude output.
