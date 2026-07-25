# Design Doc Style

Use this reference for design docs, OpenSpec design text, implementation plans, migration notes, and technical proposals.

Design docs should help a future implementer or reviewer reconstruct the intended behavior without reading the chat.

## Required Shape

- Start with the user-visible or system-visible problem.
- Define project-specific terms before using them in rules.
- Separate scope, non-scope, data shape, operation behavior, edge cases, and test expectations.
- State decisions as decisions, not as vague preferences.
- Keep unresolved items explicit and small.

## Behavior Before Plumbing

Write the contract first, then the implementation direction.

Prefer:
- When a video frame is moved, frames whose start time is inside the original video range move by the same delta.

Avoid starting with:
- Add helper X, reducer Y, and action Z.

Implementation names are useful only after the behavior is clear.

## Interfaces And State

For I/F and state decisions, include:

- Field name and allowed values.
- Default behavior for missing or old data.
- Who reads and writes the value.
- Whether IDs or relationships are persisted.
- How the behavior is derived at operation time.
- Backward compatibility and migration expectations.

Do not describe an interface only by listing touched files.

## Operation Specs

For operation-heavy features, write each operation as:

- Trigger: what user/API/system action starts it.
- Target resolution: which objects are affected and at what point in time.
- State change: what changes and what does not.
- Collision or error handling.
- Example when the rule is easy to misread.

## Precision

- Do not use `同一` without saying what equality means.
- Do not use `関連` if it could imply stored relationships; say whether it is stored or computed.
- Do not use `影響する` without saying what value, state, or behavior changes.
- Do not say `既存と同じ` unless the referenced existing behavior is named.
- If a rule depends on ordering, write the ordering.

## Implementation Direction

Implementation direction may mention reducers, actions, helpers, schemas, migrations, or tests, but keep it at the level needed to avoid ambiguity.

Do not turn the design doc into a file-by-file task report.

## Review Checklist

Before returning a design doc, check:

- Can a reviewer identify the I/F and state contract?
- Can an implementer write tests from the operation rules?
- Are target and non-target cases separated?
- Are default and backward-compatible behaviors stated?
- Are unresolved questions actually unresolved, not hidden decisions?
