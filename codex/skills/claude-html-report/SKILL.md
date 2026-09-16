---
name: claude-html-report
description: Create a coherent standalone HTML report through bounded Claude composition while Codex retains facts, provenance checks and final artifact verification.
---

# Claude HTML Report

Use for a standalone HTML report whose quality depends on cross-section narrative, coordinated comparisons, annotated assets or dense information architecture. Keep ordinary product UI in `codex-frontend-ui`, and use Markdown, a table or one diagram when it expresses the review task clearly.

Claude owns the complete report composition. Codex owns evidence collection, the factual packet, acceptance checks, deterministic asset embedding and the final file. Do not use the strategic-review skills as an artifact authoring substitute.

## Prepare The Contract

Read [report contract](references/report-contract.md). Build its packet from verified sources before invoking Claude. Treat fact weight as a display contract, not only a confidence label: load-bearing facts belong in the visible narrative, supporting facts earn space only when they change understanding, and context belongs in progressive disclosure, a reference section or the source rather than the main flow. Describe comprehension dependencies rather than prescribing an outline unless the user explicitly requires an order. Give each asset a job in the argument; a path or screenshot alone is insufficient.

Use Opus by default. Pass `--model fable` only when the user's current request explicitly asks for Fable. Model choice does not change the evidence or verification contract.

## Generate One Whole Artifact

Write the packet to a UTF-8 file under `/private/tmp`. Select a new candidate path that does not already exist, then run:

```sh
${CLAUDE_HTML_REPORT_WRAPPER:-$HOME/.local/bin/claude-html-report} \
  --prompt-file "$packet_file" \
  --output-file "$candidate_file"
```

Use escalated sandbox permissions because the wrapper reads its own Keychain credential. If a Claude CLI override is needed, configure `CLAUDE_HTML_REPORT_CLI` with an absolute path. The wrapper enforces safe mode, no tools, one turn and no session persistence; Claude cannot read the repository, inspect assets or write files directly. The wrapper writes only its complete response to a new `.html` candidate.

For images, charts or screenshots, include dimensions, a faithful description and what each asset must demonstrate in the packet. Require `{{ASSET:A1}}` placeholders in Claude's HTML, then have Codex replace them mechanically with local or embedded sources after validating every placeholder. Do not ask Claude to infer unseen image content.

## Accept Or Restart

Validate the entire candidate against the packet before visual polish:

- every load-bearing fact ID appears in `data-fact` and every used ID exists;
- every visible fact has the correct `data-weight`; the main flow is dominated by load-bearing facts rather than source completeness;
- the first viewport communicates the conclusion, current state and reader decision or action;
- supporting and context detail is compressed, deferred or omitted with a recorded reason, without hiding a prerequisite;
- uncertainty remains open and rejected claims are not asserted or implied;
- every inference in the report metadata is accepted, removed or weakened;
- every information-weighting decision in the report metadata matches the visible main flow, deferred detail and intentional omissions;
- prerequisites precede dependent claims;
- asset placeholders are complete, intentional and attached to the promised explanation;
- the result is one self-contained document without remote executable assets.

Run desktop and mobile visual QA under `codex-frontend-ui`. Inspect hierarchy, density, wrapping, overflow, contrast, whether the reader can distinguish the decision from reference material, and whether diagrams or comparisons explain the consequence rather than merely label components. A factually complete page that requires the reader to extract the hierarchy from long prose is not accepted.

Send one bounded revision packet containing reader-level symptoms, factual corrections and visual evidence. Claude must return the whole HTML again, not a section or diff. If a third composition pass would be needed, fix the source packet and restart instead of accumulating local patches. Codex may make deterministic embedding or syntax repairs, but not redesign the report piecemeal.

On wrapper timeout, invalid HTML or non-zero exit, report the route as unavailable together with the wrapper's bounded, redacted diagnostics. Do not retry automatically, switch models or fabricate Claude output.
