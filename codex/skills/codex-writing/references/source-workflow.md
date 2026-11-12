# Source-grounded prose workflow

Use for source-grounded prose that must combine findings or preserve comparisons from a long discussion. Ordinary replies and wording-only edits do not need an extra model workflow. Main retains factual judgment and authority; this procedure changes prose production, not Git/cloud permissions.

Keep the actual current user request in a UTF-8 file and relevant original source text in a separate file, with speakers/provenance where needed. Prefer existing source files or captured evidence. Do not replace them with a new assistant summary, mine unrelated conversations, include later corrections or send secret/credential material. Private conversations and source maps stay in private task storage, not a shared harness or public fixture.

Run the script resolved relative to this skill, using the verified existing Codex binary and the main agent's configured model/reasoning. Set the paths from this task's actual files; the work directory must be new and private.

`--codex-bin` may be omitted. The script probes the local launcher before the first model call; a missing launcher or its missing bundled executable is resolved to the installed app's verified CLI. Other failures, including permission/authentication errors, stop without changing credentials or retrying a model request. Existing-draft checks use the Claude wrapper directly and do not need a producer launcher.

```sh
python3 "$SKILL_DIR/scripts/compose_from_sources.py" \
  --request-file "$REQUEST_FILE" --source-file "$SOURCE_FILE" \
  --output "$DRAFT_FILE" --work-dir "$PRIVATE_WORK_DIR" \
  --codex-bin "$CODEX_BIN" --model "$MAIN_MODEL" --reasoning "$MAIN_REASONING"
```

The execution path separates three responsibilities:

1. Interpret only the current request, without old assistant drafts. A conversational observation returns a conversational response. A draft supplied now is fixed as the editing baseline.
2. Read sources without seeing a generated candidate. Select exact quotes and an ordered, reader-oriented outline for composition. Select the latest supported work state; an earlier investigation caveat is not a requirement for a completed change. For editing, select only grounded corrections to the fixed draft; quoted history cannot substitute an older draft. Slack output then passes through a layout-only step for backtick section labels and parent/child bullets; short replies remain plain. Code verifies that the layout retains all body wording and order.
3. Compose from the selected evidence, without the old conversation. Check the actual candidate against the original request and sources for missing results, unnecessary qualifications and the medium's writing conventions. For Japanese PR/issue bodies, check complete です・ます sentences and concrete descriptions of the component, operation, object and result, while preserving technical detail. Every retained qualification needs an original candidate claim, source evidence and a concrete reader consequence. The checker returns candidate-block and evidence IDs; code resolves the original text and offsets, rejecting unknown IDs and duplicate replacements without fuzzy matching. Apply these local replacements before layout, preserving unaffected text and the intended question. Save PR/review bodies as plain Markdown for publication; add AGENTS.md's outer copy fence only when showing that body in chat.

For an already saved issue/PR body, use the same script with `--draft-file "$DRAFT_FILE"` and a different `--output` path. This checks and patches the existing draft directly in one call; it does not regenerate its contents or run intake/selection/layout. Check the exact file that will be published after the last edit. A changed file needs this check again; an unchanged checked draft does not.

The actual-draft check uses the existing tool-free `claude-strategic-review` wrapper (or its existing `CLAUDE_STRATEGIC_REVIEW_WRAPPER` override), with the raw request, sources and candidate. Codex remains the producer and applies only exact, source-validated edits. A failed check does not publish a body or silently fall back to the producer's own assessment; inspect the existing wrapper's diagnostics without retrying or changing accounts/models.

The returned `output` is sendable copy. `delivery_notes`, when present, points to a separate file addressed to the user. Show useful supplementary uncertainty after the body; never merge it into issue/PR/Slack content.

Read the actual output against the request and original evidence. The source map proves quote location and the patcher preserves unselected text; neither proves the semantic interpretation is correct. Keep numeric components, estimated/observed outcomes, causal qualifications, action/result and completed/pending status in this check. If explicit preservation needs independent review, use the existing artifact-integrity owner with the original sources rather than inventing another reviewer.

The script does not retry, fall back to another model, alter shared settings or publish anything. On a failure inspect the recorded phase and existing runtime. Diagnose source/interpretation faults separately from setup faults; fix their cause before continuing. If sandbox permissions prevent the native client from initializing, use the execution tool's normal permission request for this same producer; do not disable sandboxing, change credentials or replace the failed production step with an unrestricted rewrite. Deliver the saved result rather than regenerating another version in chat.

Workflow basis: [Attribute First, then Generate](https://research.google/pubs/attribute-first-then-generate-locally-attributable-grounded-text-generation/), [source-grounded command editing](https://aclanthology.org/2021.naacl-main.414/), and [separate coverage diagnosis](https://aclanthology.org/2026.eacl-long.167/). This adapts those principles; local evaluation, not their reported scores, determines adoption. Coverage checking is for composition, not an extra stage for every edit or reply.
