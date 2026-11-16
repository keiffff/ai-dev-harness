# Original Sources to Claude

Use the configured tool-free Claude wrapper once. Claude owns information selection, composition, checking and revision; Codex only transports the source data and the returned artifact.

Reuse existing private UTF-8 code/diffs and actual tool results. The saved request and original user context are attached automatically; do not create request files or transcribed conversation/source memos in a normal app session. Do not prepare a judgment handoff, an outline, required body points, body limits or replacement paragraphs. Do not silently treat earlier assistant claims as observations. Include an existing draft only when the user asks to revise it. Keep secrets out of every input and keep real examples out of shared fixtures.

Run relative to this skill with verified task paths:

```sh
python3 "$SKILL_DIR/scripts/compose_from_sources.py" \
  --source-file "$EXISTING_SOURCE_FILE" --medium "$MEDIUM" --print-body
```

`--source-file` may be repeated for original files, or omitted for a request needing no extra material. `--medium` is `slack`, `pr_body`, `issue_body` or `other`. For a requested revision add `--draft-file "$EXISTING_DRAFT_FILE"`. `--output` and `--work-dir` remain available for callers that need explicit new paths. Without `--print-body`, stdout retains the existing JSON receipt interface. The historical `--handoff-file` and producer/model flags are accepted but ignored; they do not read a handoff, choose another writer or add a call.

When submitted-prompt storage is available, code binds the request to its latest saved source and omits any caller-written request text from the writing packet. The existing wrapper also attaches the saved original user context. From the app's saved thread history, the script carries completed conversation turns corresponding to captured user prompts, ending before that exact request and retaining their roles. This preserves earlier explanations and corrections without a Codex recap. If capture began with the current request, it carries the preceding completed response instead. Assistant responses are not independent evidence or approved drafts. A missing history record does not trigger a retry or make a new writing gate; existing original files remain usable. Outside the app context, supply `--request-file` pointing to the original verbatim request; without either request source the script stops before calling Claude. Neither a hook event nor an earlier prompt authenticates a human author or renews one-time permission.

Claude returns only `status`, `body` and `delivery_notes`. Code copies `body` to the output and `delivery_notes` to a separate private file without changing their text. JSON parsing and separate destinations are transport, not an editorial pass. If Claude returns `needs_evidence`, the body is empty and its question is saved in the notes; code neither writes a partial draft nor starts a retry. A failed call leaves no new output. No second source check, block-edit map, note classifier or main-agent acceptance step.

With `--print-body`, stdout is the unchanged body (or the evidence question when status is `needs_evidence`); sender notes and the private execution-record path are separate stderr output. Present the returned body without another file read or editorial check. A user-requested correction runs the same single Claude call on the original draft and evidence. Codex does not construct a correction request from its own editorial or factual judgment. The existing custody hook records the writer output and rejects a direct main patch within this task, including after a new user correction. A new user request initiates a Claude revision, not main editing. No Stop continuation is registered; the app's final chat transcription is not an independently enforced byte-copy channel.

`manifest.json` records input/implementation hashes, status, call count, preparation/writer/total elapsed time and output hash. `stdout.txt` retains the raw Claude envelope, and `answer.json` retains its parsed strings. These records establish execution and output identity, not prose quality or factual truth. Publication uses the exact saved body through the existing approved route; this helper does not grant publication authority.
