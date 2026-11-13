# Investigation handoff to composition

Main investigates and decides what the evidence supports. Claude composes the reader-facing document, including its information hierarchy and medium-specific layout. Short conversation and local wording edits stay in main.

Reuse existing private UTF-8 request and evidence files when available; do not retype the conversation or read the helper source to discover its documented arguments. Otherwise save the original request and evidence once, retaining measurements, source locations and relevant prior decisions. Do not pass only main's summary. Save a JSON handoff with these fields:

- `purpose`: what the recipient needs to understand or do.
- `conclusion`: the supported answer for that reader, not a mixed investigation summary.
- `required_points`: the requested result groups as strings.
- `pending_checks`: decision-relevant reads still to perform; otherwise an empty array.
- `body_limits`: an empty array unless uncertainty changes the recipient's concrete next action. Each entry has `claim`, `action_if_true` and `action_if_false`. If both answers lead to the same action, this is not a body limit. A change in the analyst's confidence is not itself a different recipient action. This does not remove unknowns explicitly requested as results or explaining an actual next action.
- `sender_notes`: useful secondary uncertainty or execution notes as a string, otherwise empty. Keep these out of `conclusion` and `required_points`. Code saves them separately without passing them to the writer.

These are content decisions, not a prewritten draft. Do not embed secrets or move actual conversations into common fixtures.

Before handoff, investigate available facts whose answers could change the requested conclusion or action. Leave only those genuinely pending checks in `pending_checks`, each with its question, consequence and next available read or actual blocker. The script returns `needs_investigation` without calling a model or writing a body when this array is nonempty. This is not a requirement to prove everything: unrelated unperformed checks do not belong in it. Material unavoidable limits can be part of the supported conclusion; secondary sender notes remain outside the copy.

Run relative to this skill, substituting verified task paths:

```sh
python3 "$SKILL_DIR/scripts/compose_from_sources.py" \
  --request-file "$REQUEST_FILE" --source-file "$SOURCE_FILE" \
  --handoff-file "$HANDOFF_FILE" --medium "$MEDIUM" \
  --output "$BODY_FILE" --work-dir "$PRIVATE_WORK_DIR"
```

`--medium` is `slack`, `pr_body`, `issue_body` or `other`. Inputs remain unchanged; the output path and private work directory are new. A new output path prevents an earlier body being mistaken for this run's result when questions are returned. No publication is authorized by this workflow.

The configured tool-free `claude-strategic-review` wrapper receives the request, evidence and handoff once. It returns either `ready` with ordered Markdown blocks, or `needs_evidence` with specific questions and their consequences. Code assembles body blocks without rewriting them. Qualification blocks enter the body only when they reference a handoff `body_limits` entry; other qualifications and sender-note blocks go to `delivery-notes.md`. Questions stay in `questions.json`. On a return for evidence, main continues the investigation, updates the handoff and calls again only after obtaining a relevant change. No automatic retry, provider change or fallback writer.

For a ready document, one smaller check receives only the actual body, current request and approved limits. It selects existing lines containing mixed-in sender notes. Code may only delete those exact lines and records them in `removed-notes.json`; it cannot regenerate prose, insert cautions or alter the conclusion. Removed notes stay outside the copy. This second call exists because composition sometimes mislabeled work notes as body content in actual replays. Its cost is included in the manifest; do not add another general review or formatting pass.

For existing scoped saved-draft callers, `--draft-file` without a handoff retains literal block editing, followed by the same deletion-only final note filter. It does not regenerate the document. Factual corrections to a source-grounded artifact use this path; wording-only local edits stay in main. A substantial rewrite instead uses a handoff and may include the original draft as `--draft-file` to preserve its requested scope and voice. Older producer/model arguments do not launch a producer.

Read and deliver the saved body without rewriting it. `manifest.json` records status, input and implementation hashes, call count, elapsed time and, on completion, output hash. These records prove execution and file identity, not the truth or usefulness of the prose. A helper cannot force its own selection: evaluate normal requests with actual tool traces, source checks and end-to-end time including repairs. Do not count a manually invoked helper test as proof of natural routing.
