# Claude HTML Report Contract

## Input Packet

Use stable IDs so coverage and provenance can be checked without relying on a visual read-through.

1. **Reader and task** — include the relevant original user request and feedback verbatim, separate from Codex's interpretation. State who reads the report, the requested purpose and what they already know. Include supplied tone, viewing context and concrete reader questions. Do not turn sharing or explaining into approval, commitment or decision ownership; identify a reader action only when the request or established task includes it.
2. **Ranked takeaway** — distinguish user-established priorities and evidenced conclusions from Codex's proposed emphasis. Claude determines the central answer and which explanations establish it; a suggested ranking is not a required outline. Reader questions guide coverage, not one equally prominent chapter per question. Distinguish the main argument from the technical proof or lookup that supports it.
3. **Facts** — `F1...Fn`; each identifies a distinct claim, its status (`verified`, `measured`, `reported` or `inferred`) and source. Separate a reader-level conclusion from its implementation details instead of giving the whole bundle one mandatory weight. Claude assigns presentation weights (`load-bearing`, `supporting` or `context`) from the reader's task, not the amount of research: load-bearing claims answer the main questions or establish necessary prerequisites; supporting evidence substantiates them; context is for lookup or omission. Preserve explicit user requirements, but do not confuse information required somewhere in the document with information required in the main flow. For a numeric fact, identify its definition, unit or denominator, population, time window and aggregation when they affect interpretation, plus an evidenced baseline, target or comparison when needed for its meaning. Do not invent a comparison.
4. **Audience-facing information budget and design brief** — identify required information, known reader background, out-of-scope material and relationships the reader needs to understand, with their basis in the request or evidence. Include user-supplied design constraints and references. Claude chooses emphasis, grouping, explanation order and whether a relationship needs a diagram, comparison, table or prose; Codex suggestions are not requirements. Detail needed to perform a documented action is load-bearing even when it is not an executive takeaway. Omitting from the page does not remove a fact from the canonical source.
5. **Rejected claims** — causal or consequential explanations that the evidence does not support. These constrain composition; they are not reader-facing content.
6. **Comprehension dependencies** — statements such as `the proposed worker lanes require the resident-worker mechanism to be explained first`. These are constraints, not a fixed outline.
7. **Assets** — `A1...An`; file dimensions, faithful content description, what the asset must prove, and any comparison or grouping relationship. Claude receives the description, not the file.
8. **General-to-example mapping** — identify the general problem and the concrete incident or measurement that illustrates it.
9. **Out of scope and noise** — facts that are true but would distract from the reader's task. These are omission instructions, not material to render or explain.
10. **Canonical sources and format justification** — name the source of truth and why coordinated HTML views materially improve this report.

Do not include credentials, tokens, private keys, raw environment dumps, `.env`, auth configuration or other secret-bearing content. The standing authorization covers every task-required non-secret fact sent through the user-managed Claude CLI, including company-internal, confidential-design and personal information. Do not ask for additional approval or withhold a fact solely because of one of those classifications. Keep the packet relevant to the requested report and honor any narrower user instruction in the current request.

## Reader Path And Explanation Units

Compose around the reader's questions rather than reproducing the order of investigation. Choose the shape for the task, not a universal section template:

- **Proposal or UI comparison:** connect the current experience to the specific change, the need that change creates, and why the selected approach answers it. Compare alternatives using the same scenario and criteria. Put the actual interaction or state beside its rationale, rather than asking a feature list to explain the experience.
- **Workflow or onboarding:** show the overall route and responsibility changes, then let the reader find their current step, next action and handoff. Keep overview and detailed procedures aligned through shared step names and links; repeating them serves different tasks only when that distinction is clear.
- **Analysis or experiment results:** pair the observation with what it establishes and what it means for the original question or plan. A measurements table or completion-status list alone does not communicate the finding. Do not invent implications where evidence is insufficient.

Use a coherent explanation unit: the claim or question, its evidence or concrete example, and the supported consequence. A diagram or mock belongs with the point it explains. Choose a visual for the relationship, not the list of available components. Make the behavior or difference visible: separate paths for independently handled cases, a changed state when a condition is met, or aligned alternatives with the relevant difference highlighted. A timeline must explain what changes over time, not just display marks; a flow must let the reader follow a case to its outcome, not merely connect service names. Boxes containing prose are not an explanation when the reader must reconstruct the relationship from their labels. Use prose or a table when a diagram adds no meaning. Keep comparison frames stable and use type size, spacing, color and emphasis consistently to distinguish the main message from its supporting detail.

Support both an initial read and later lookup when the task needs both. Keep prerequisites and the current conclusion or operating path visible; use navigation, links or disclosure for detailed evidence and historical alternatives. Explain each main answer once: a repeated summary, comparison table or closing checklist earns space only if it serves a different reader task. For an explanatory brief, show how the proposal works and the material boundary of its feasibility; keep engineering inventories, detailed alternative analyses and repeated parameter lists in lookup rather than giving them the same emphasis as the explanation. A feasibility qualification can stay visible without becoming a separate warning section repeated at the beginning and end. For an implementation guide, those details may be the reader's actual task. At narrow widths, keep the relationship and its outcome readable together; fitting a scroll container while hiding the decisive part of the diagram is not responsive explanation. Reflow or provide an equivalent diagram rather than reducing the diagram to prose boxes. If variants change several sections or a mock, keep the selected variant consistent across those views. Add interaction only when it helps the reader compare or act, not to demonstrate HTML capability. Explicitly distinguish a mock's illustrative values from verified product behavior.

When learning from supplied references, carry these composition choices into the packet with their purpose. Do not copy project identifiers, people, operating rules or sample data into common instructions.

## Required Claude Output

Claude returns one complete HTML document without Markdown fences or surrounding commentary.

- Use a full `<!doctype html>` document.
- Keep CSS and non-networked behavior self-contained. Ordinary citation links may be remote; scripts, styles, fonts and images may not be fetched remotely.
- Attach `data-fact="F1 F4"` and `data-weight="load-bearing|supporting|context"` to the nearest meaningful element carrying each visible claim. Split elements when combined facts have different weights.
- Make the first viewport establish what the report proves, why it matters and, when applicable, what the reader must decide or do.
- Select the main explanation before composing the page: what the reader needs to understand and the evidence that makes it convincing. Keep those load-bearing claims in the visible main flow, distinct from supporting explanation and lookup detail. Do not render each source fact as a section or treat technical completeness as equal visual importance. Put implementation evidence in disclosure, an appendix or the canonical source unless the reader needs it to understand the conclusion or perform the task. Do not use disclosure to hide a necessary prerequisite, decision or required action.
- Do not place numeric values in one KPI row, card group or other visually parallel summary unless the packet establishes that readers should compare them. Visual alignment implies comparability. Values with different metric definitions, units or denominators, populations, time windows or aggregation must stay with the separate claims they support. Do not promote a standalone number to a headline merely because it is available: show the evidenced comparison and its meaning, or keep a needed raw value with its explanatory claim. The first viewport does not require a metric strip.
- Treat unsupported rejected claims, intentionally omitted facts and verification bookkeeping as composition controls, not sections, badges or explanatory copy. Actual evaluated alternatives, scope boundaries or missing requirements may belong in a decision or implementation document when they answer a reader question; keep current decisions distinct from historical reasoning and do not invent a risk register. Do not tell the reader what was excluded merely to demonstrate restraint.
- A qualification belongs in the visible report only when omitting it would make a visible claim materially false or change the reader's decision. State it once, next to that claim, with the concrete basis. If a claim needs broad defensive wording to remain technically true, omit or narrow the claim instead. Do not scatter labels such as `参考値`, `未確認`, `未検証`, `暫定`, `可能性` or `対象外` across the page.
- Do not invent approval requests, decision ownership, commitments, follow-up measurements, open questions, options, risks, future work or "next steps" to make the report appear thorough. The original user request and established task, not an unsupported Codex interpretation, determine whether the reader must act. Absence of evidence is not itself reader-facing content.
- Do not translate source completeness into body length. A correct omission from the rendered artifact is preferable to making the reader reconstruct priority from exhaustive prose.
- Use exactly `{{ASSET:A1}}` as the source placeholder for each described asset. Do not invent asset IDs or describe unseen details.
- Preserve the packet's distinction between general explanation and concrete example.
- Do not add facts, entities, metrics, causal links or decisions to complete the visual story.
- Avoid decorative card nesting, oversized tool headings, decorative gradient blobs, visually equal boxes for unequal claims and prose that explains the design itself. A faithful UI mock or a meaningful group may need nested containers; do not flatten those relationships merely to avoid cards.

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

An empty inference list is valid. An unlisted inference is not. Empty `deferred` or `omitted` lists are also valid; excluded source facts may be grouped by ID with a shared reason. These are provenance notes, not a requirement to render the whole evidence collection.

## Revision Contract

### Local Codex revision

Codex edits the accepted HTML directly when the requested change is bounded and does not change the report's narrative architecture, fact weighting or cross-section relationships. Examples include requested local wording, labels, color themes, CSS tokens, spacing, typography, grid alignment, responsive overflow, deterministic asset or syntax repairs, and isolated factual-literal or metadata corrections. Do not use the final polish pass to rewrite the narrative, restore deferred research to the main flow, or replace a diagram's relationships with prose boxes on mobile. For card-, grid- or diagram-heavy reports, Codex creates a temporary rendered QA overlay with component bounds, intended content insets and layout tracks, uses it to correct the clean HTML, then renders the clean report again. The overlay is inspection-only and is never published. Keep `data-fact`, `data-weight` and `REPORT-META` consistent with the edited content, then rerun the relevant full-document and visual checks. Do not invoke Claude merely because it generated the original file.

### Structural Claude revision

The revision input contains the original request and factual packet plus:

- the requested correction and what must remain intact, including purpose, known reader background and effective visual explanations;
- factual corrections and adjudicated inference decisions;
- desktop and mobile observations;
- reader-level symptoms, such as `the proposal appears before the current mechanism is understandable`;
- asset failures, such as `the screenshots are present but do not reveal the cross-screen inconsistency`.

Use this path only when the change affects the ranked takeaway, reader decision, fact weighting across sections, prerequisite order, comparison structure, primary visual model or another whole-report relationship. Give Claude the observed deficiency rather than prescribing a replacement format or isolated element moves unless the user explicitly chose them. More specific content does not by itself justify discarding a working visual explanation. Claude returns the complete document again and rechecks all fact and asset IDs.
