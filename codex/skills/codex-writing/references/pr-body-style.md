# PR Body Style

Use this reference for GitHub PR descriptions.

The PR body is for reviewers. It is not a work log, commit summary, or implementation inventory.

## What To Include

- Why the PR exists.
- What end-to-end behavior changes.
- What contract, state, or workflow the reviewer should understand.
- What review questions matter.
- What reproducible checks support confidence.
- Residual risk only when it changes review or release expectations.

## What To Omit

- File-by-file work reports.
- Internal chat history, temporary failures, setup retries, or local detours.
- Discarded approaches unless the reviewer must know why they are not present.
- "Did not do X" notes unless X is an expected follow-up or release risk.
- Routine implementation touchpoints that are obvious from the diff.
- Long lists of schema/type/OpenAPI/ORM locations when the actual point is that a value is accepted end-to-end.

## Compression Rules

Convert implementation details into reviewer-level facts before drafting.

Example source facts:
- domain type, request schema, response schema, Prisma enum, and OpenAPI enum were updated.

Reviewer-level fact:
- The API now accepts the new data source end-to-end, including validation, persistence, and response/documentation surfaces.

Example source facts:
- A pure function test was deleted and an upper-level usecase test was added.

Reviewer-level fact:
- The behavior is now covered at the usecase boundary where duplicate policy and creation behavior are exercised together.

## Sections

Prefer the repository's own PR template when it exists. Do not bake project-specific section names into this skill.

Use only sections that help the reviewer understand behavior, review focus, verification, risk, and linked work. Do not fill a template section with placeholder text. If a section has no useful content and the template allows omission, omit it. If the repository template requires it, keep it terse.

## Confirmation

In the verification or confirmation section, list reproducible checks only:

- typecheck
- lint/format check
- targeted tests
- schema validation
- generated artifact check

Do not mention failed attempts, environment repairs, command retries, or manual inspection unless the reviewer needs that limitation.

## Final Review

Before returning a PR body, check:

- Does it start from reviewer-visible behavior?
- Are file names and internal identifiers included only when necessary?
- Does every bullet change the reviewer's understanding?
- Are unchanged items kept out of changed-item lists?
- Are residual risks real release/review risks rather than chat leftovers?
