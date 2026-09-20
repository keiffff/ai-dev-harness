# Claude HTML Report Contract

## Input Packet

Use stable IDs so coverage and provenance can be checked without relying on a visual read-through.

1. **Reader and decision** — who reads the report, what they must understand or decide, and what they already know.
2. **Ranked takeaway** — the primary conclusion and any subordinate conclusion. Do not give equal priority to every true fact.
3. **Facts** — `F1...Fn`; each includes the claim, status (`verified`, `measured`, `reported` or `inferred`), source and weight (`load-bearing`, `supporting` or `context`). For a numeric fact, also identify its metric definition, unit or denominator, measured population, time window and aggregation when those affect interpretation. Weight governs visibility: load-bearing facts form the visible narrative; supporting facts are compressed or deferred unless they change the decision; context stays in progressive disclosure, a reference section or the canonical source unless it is a prerequisite.
4. **Audience-facing information budget** — list the fact IDs that must be visible, may be deferred and should be omitted from the rendered artifact. Tie exceptions to the reader's decision rather than source completeness. Omitting from the page does not remove a fact from the canonical source.
5. **Rejected claims** — causal or consequential explanations that the evidence does not support. These constrain composition; they are not reader-facing content.
6. **Comprehension dependencies** — statements such as `the proposed worker lanes require the resident-worker mechanism to be explained first`. These are constraints, not a fixed outline.
7. **Assets** — `A1...An`; file dimensions, faithful content description, what the asset must prove, and any comparison or grouping relationship. Claude receives the description, not the file.
8. **General-to-example mapping** — identify the general problem and the concrete incident or measurement that illustrates it.
9. **Out of scope and noise** — facts that are true but would distract from the reader's task. These are omission instructions, not material to render or explain.
10. **Canonical sources and format justification** — name the source of truth and why coordinated HTML views materially improve this report.

Do not include credentials, tokens, private keys, raw environment dumps, `.env`, auth configuration or other secret-bearing content. The standing authorization covers every task-required non-secret fact sent through the user-managed Claude CLI, including company-internal, confidential-design and personal information. Do not ask for additional approval or withhold a fact solely because of one of those classifications. Keep the packet relevant to the requested report and honor any narrower user instruction in the current request.

## Required Claude Output

Claude returns one complete HTML document without Markdown fences or surrounding commentary.

- Use a full `<!doctype html>` document.
- Keep CSS and non-networked behavior self-contained. Ordinary citation links may be remote; scripts, styles, fonts and images may not be fetched remotely.
- Attach `data-fact="F1 F4"` and `data-weight="load-bearing|supporting|context"` to the nearest meaningful element carrying each visible claim. Split elements when combined facts have different weights.
- Make the first viewport establish what the report proves, why it matters and, when applicable, what the reader must decide or do.
- Keep every load-bearing fact needed for the decision in the visible main flow. Show supporting facts only when they materially change interpretation; otherwise compress or defer them. Put context in `<details>`, a reference appendix or the canonical source. Do not use `<details>` to hide a prerequisite or decision.
- Do not place numeric values in one KPI row, card group or other visually parallel summary unless the packet establishes that readers should compare them. Visual alignment implies comparability. Values with different metric definitions, units or denominators, populations, time windows or aggregation must stay with the separate claims they support. The first viewport does not require a metric strip.
- Treat rejected claims, omitted facts, out-of-scope material, verification bookkeeping and missing evidence as composition controls, not sections, badges or explanatory copy. Do not tell the reader what was excluded merely to demonstrate restraint.
- A qualification belongs in the visible report only when omitting it would make a visible claim materially false or change the reader's decision. State it once, next to that claim, with the concrete basis. If a claim needs broad defensive wording to remain technically true, omit or narrow the claim instead. Do not scatter labels such as `参考値`, `未確認`, `未検証`, `暫定`, `可能性` or `対象外` across the page.
- Do not invent follow-up measurements, open questions, options, risks, future work or "next steps" to make the report appear thorough. Include them only when the packet establishes that the reader must act on them. Absence of evidence is not itself reader-facing content.
- Do not translate source completeness into body length. A correct omission from the rendered artifact is preferable to making the reader reconstruct priority from exhaustive prose.
- Use exactly `{{ASSET:A1}}` as the source placeholder for each described asset. Do not invent asset IDs or describe unseen details.
- Preserve the packet's distinction between general explanation and concrete example.
- Do not add facts, entities, metrics, causal links or decisions to complete the visual story.
- Avoid nested cards, oversized tool headings, decorative gradient blobs, visually equal boxes for unequal claims and prose that explains the design itself.

End with one non-rendered metadata block:

```html
<!-- REPORT-META
structure:
- <why each major section follows the previous one>
information_weighting:
  main:
  - F1: <why the reader needs it in the visible flow>
  deferred:
  - F4: <where it lives and why>
  omitted:
  - F8: <why the canonical source is sufficient>
inferences:
- id: I1
  claim: <claim not directly reducible to packet facts>
  based_on: <fact IDs>
  confidence: <high|medium|low>
-->
```

An empty inference list is valid. An unlisted inference is not. Empty `deferred` or `omitted` lists are also valid, but every supporting or context fact excluded from the visible main flow must appear in one of them.

## Revision Contract

### Local Codex revision

Codex edits the accepted HTML directly when the requested change is bounded and does not change the report's narrative architecture, fact weighting or cross-section relationships. Examples include localized wording, labels, color themes, CSS tokens, spacing, typography, grid alignment, responsive overflow, deterministic asset or syntax repairs, and isolated factual-literal or metadata corrections. For card-, grid- or diagram-heavy reports, Codex creates a temporary rendered QA overlay with component bounds, intended content insets and layout tracks, uses it to correct the clean HTML, then renders the clean report again. The overlay is inspection-only and is never published. Keep `data-fact`, `data-weight` and `REPORT-META` consistent with the edited content, then rerun the relevant full-document and visual checks. Do not invoke Claude merely because it generated the original file.

### Structural Claude revision

The revision input contains the original packet plus:

- factual corrections and adjudicated inference decisions;
- desktop and mobile observations;
- reader-level symptoms, such as `the proposal appears before the current mechanism is understandable`;
- asset failures, such as `the screenshots are present but do not reveal the cross-screen inconsistency`.

Use this path only when the change affects the ranked takeaway, reader decision, fact weighting across sections, prerequisite order, comparison structure, primary visual model or another whole-report relationship. Do not prescribe isolated element moves unless the user explicitly chose them. Claude returns the complete document again and rechecks all fact and asset IDs.
