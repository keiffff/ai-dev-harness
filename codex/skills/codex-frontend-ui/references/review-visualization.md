# Review Visualization

Use visualization to reduce the reconstruction work required from a human reviewer. Choose the smallest representation that fits the review task; do not default to standalone HTML.

## Representation Selection

| Review task | Prefer |
| --- | --- |
| Exact values, fields, or repeated comparison axes | Table |
| Ownership, dependencies, many-to-many relationships, or cycles | Graph or Mermaid diagram |
| State transitions or processing order | Flow or sequence diagram |
| Concurrent phases, migration stages, or time-based change | Timeline |
| Containment or hierarchy | Tree or nested list |
| Rationale, constraints, uncertainty, or tradeoffs | Text |
| Several coordinated views, dense cross-references, or useful interaction | Standalone HTML |

Start with a visual representation when the reviewer would otherwise need to reconstruct relationships, order, state, comparison axes, or hierarchy mentally from prose. Markdown tables and Mermaid diagrams are sufficient when they express the review task clearly. Use standalone HTML when layout, coordinated views, density, or interaction materially improves review.

## Canonical Source

- Keep Markdown, OpenSpec, code, schema, or another explicitly named source as canonical.
- Treat standalone HTML as a review projection unless HTML itself is the requested deliverable.
- Name the canonical source in the projection.
- Do not invent entities, edges, states, values, or decisions to complete a visual.
- Preserve exact contracts as text, tables, code, or schema even when a diagram summarizes them.
- Update the canonical source before regenerating the projection. Do not hand-edit generated HTML to create a competing source of truth.

## Review Workflow

1. Identify the human review task.
2. Select the smallest fitting representation.
3. Extract only facts supported by the canonical source.
4. Build the table, diagram, timeline, tree, or HTML projection.
5. Check fidelity before visual polish:
   - every load-bearing item from the source is represented;
   - no unsupported item was introduced;
   - labels and directionality preserve the source meaning;
   - uncertainty and open decisions remain visible.
6. Run visual QA for hierarchy, readability, wrapping, overflow, density, and responsive layout.
7. Return review findings through the active agent conversation. Do not create a separate comment-state system by default.
8. Apply accepted feedback to the canonical source, then regenerate when another visual pass is useful.

## Artifact Lifecycle

- Keep generated review HTML outside the repository or in an ignored output path by default.
- Commit generated HTML only when it is an intended deliverable.
- Prefer self-contained static HTML.
- Do not add scripts, remote assets, network calls, or a local server unless the artifact genuinely requires them.
- When a local server is required, bind to `127.0.0.1`; do not expose it to the LAN or publish it without explicit user approval.
