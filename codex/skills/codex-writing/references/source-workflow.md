# Source-grounded prose workflow

Use for source-grounded prose that must combine findings or preserve comparisons from a long discussion. Ordinary replies and wording-only edits do not need an extra model workflow. Main retains factual judgment and authority; this procedure changes prose production, not Git/cloud permissions.

Keep the actual current user request in a UTF-8 file and relevant original source text in a separate file, with speakers/provenance where needed. Prefer existing source files or captured evidence. Do not replace them with a new assistant summary, mine unrelated conversations, include later corrections or send secret/credential material. Private conversations and source maps stay in private task storage, not a shared harness or public fixture.

Run the script resolved relative to this skill, using the verified existing Codex binary and the main agent's configured model/reasoning. Set the paths from this task's actual files; the work directory must be new and private.

```sh
python3 "$SKILL_DIR/scripts/compose_from_sources.py" \
  --request-file "$REQUEST_FILE" --source-file "$SOURCE_FILE" \
  --output "$DRAFT_FILE" --work-dir "$PRIVATE_WORK_DIR" \
  --codex-bin "$CODEX_BIN" --model "$MAIN_MODEL" --reasoning "$MAIN_REASONING"
```

The execution path separates three responsibilities:

1. Interpret only the current request, without old assistant drafts. A conversational observation returns a conversational response. A draft supplied now is fixed as the editing baseline.
2. Read sources without seeing a generated candidate. Select exact quotes and an ordered, reader-oriented outline for composition. Before composing, independently compare that outline with the requested scope and sources, and add evidenced material omissions. For editing, select only grounded corrections to the fixed draft; quoted history cannot substitute an older draft.
3. Compose from the selected evidence, without the old conversation. For an edit, apply replacements in code and retain all other text. PR/review composition renders one complete copyable Markdown body.

Read the actual output against the request and original evidence. The source map proves quote location and the patcher preserves unselected text; neither proves the semantic interpretation is correct. Keep numeric components, estimated/observed outcomes, causal qualifications, action/result and completed/pending status in this check. If explicit preservation needs independent review, use the existing artifact-integrity owner with the original sources rather than inventing another reviewer.

The script does not retry, fall back to another model, alter shared settings or publish anything. On a failure inspect the recorded phase and existing runtime. Diagnose source/interpretation faults separately from setup faults; fix their cause before continuing. If sandbox permissions prevent the native client from initializing, use the execution tool's normal permission request for this same producer; do not disable sandboxing, change credentials or replace the failed production step with an unrestricted rewrite. Deliver the saved result rather than regenerating another version in chat.

Workflow basis: [Attribute First, then Generate](https://research.google/pubs/attribute-first-then-generate-locally-attributable-grounded-text-generation/), [source-grounded command editing](https://aclanthology.org/2021.naacl-main.414/), and [separate coverage diagnosis](https://aclanthology.org/2026.eacl-long.167/). This adapts those principles; local evaluation, not their reported scores, determines adoption. Coverage checking is for composition, not an extra stage for every edit or reply.
