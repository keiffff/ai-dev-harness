# Original Sources to Claude

Use the configured tool-free Claude wrapper once. Claude owns information selection, composition, checking and revision; Codex only transports the source data and the returned artifact.

Reuse existing private UTF-8 files containing the original request, relevant conversation, code/diffs and actual tool results. Do not prepare a judgment handoff, an outline, required body points, body limits or replacement paragraphs. Do not silently treat earlier assistant claims as observations. Include an existing draft only when the user asks to revise it. Keep secrets out of every input and keep real examples out of shared fixtures.

Run relative to this skill with verified task paths:

```sh
python3 "$SKILL_DIR/scripts/compose_from_sources.py" \
  --request-file "$REQUEST_FILE" --source-file "$SOURCE_FILE" \
  --medium "$MEDIUM" --output "$BODY_FILE" --work-dir "$PRIVATE_WORK_DIR"
```

`--source-file` may be repeated for original files, or omitted for a request needing no extra material. `--medium` is `slack`, `pr_body`, `issue_body` or `other`. For a requested revision add `--draft-file "$DRAFT_FILE"`. Output and work directory are new, preserving the original inputs. The historical `--handoff-file` and producer/model flags are accepted but ignored; they do not read a handoff, choose another writer or add a call.

When submitted-prompt storage is available, code binds the request to its latest saved source and omits the caller-written request text from the writing packet. The existing wrapper also attaches the saved original context. Without that source, the request file remains usable and is labeled unverified. Neither a hook event nor an earlier prompt authenticates a human author or renews one-time permission.

Claude returns only `status`, `body` and `delivery_notes`. Code copies `body` to the output and `delivery_notes` to a separate private file without changing their text. JSON parsing and separate destinations are transport, not an editorial pass. If Claude returns `needs_evidence`, the body is empty and its question is saved in the notes; code neither writes a partial draft nor starts a retry. A failed call leaves no new output. No second source check, block-edit map, note classifier or main-agent acceptance step.

Read and display the saved body unchanged. Include separate sender notes only outside the copy. A user-requested correction runs the same single Claude call on the original draft and evidence. Codex does not construct a correction request from its own editorial or factual judgment. The existing custody hook records the writer output and rejects a direct main patch within this task, including after a new user correction. A new user request initiates a Claude revision, not main editing. No Stop continuation is registered; the app's final chat transcription is not an independently enforced byte-copy channel.

`manifest.json` records input/implementation hashes, status, call count, elapsed time and output hash. `stdout.txt` retains the raw Claude envelope, and `answer.json` retains its parsed strings. These records establish execution and output identity, not prose quality or factual truth. Publication uses the exact saved body through the existing approved route; this helper does not grant publication authority.
