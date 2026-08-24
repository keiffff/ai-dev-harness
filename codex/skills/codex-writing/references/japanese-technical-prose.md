# Japanese Technical Prose

Use this reference for Japanese technical documents, explanatory Markdown, technical articles, design notes, and substantive prose editing.

This is not a generic humanizer. The goal is to make the document read like a concrete technical explanation written by someone who understands the system.

## Core Rules

- Write from the reader's problem, not from the agent's work log.
- Keep one paragraph focused on one claim or one operation.
- When saying a change matters, name what changes for the user, reviewer, API caller, test, or operation.
- Do not collapse different things into `同じ`, `一貫`, `影響`, `問題`, or `改善` unless the sentence explains the exact mechanism.
- Do not introduce filenames, function names, enum names, schema names, or identifiers unless the reader must refer to that exact name later.
- Prefer behavior, contract, state, and decision over implementation touchpoints.
- Use concrete nouns and verbs. Avoid vague wrappers such as `対応`, `反映`, `調整`, `考慮`, `形`, `周り`, `側`, `観点`, `担保`, and `整理` when they hide the actual behavior.
- Do not translate an English concept into a compact Japanese noun and assume the relation is clear. Prefer a sentence that names the actor, action, target, and condition. Treat terms such as `正本`, `契約`, `投影`, `測定境界`, `比較終端`, `外部契約`, and `実効値` as suspect unless the intended reader already uses them with that meaning.
- Avoid AI-like balance: do not add both-sides framing, generic caveats, or summary sentences unless they change the reader's decision.
- Avoid decorative structure: do not force three bullets, paired contrasts, dramatic conclusion lines, or repeated `重要なのは...`.
- Delete sentences that only restate section titles.

## Causality

When explaining cause and effect, write the mechanism.

Weak:
- この変更により独立性が改善されます。

Better:
- 公開状態の更新をファイル作成の後に移すため、公開済みのレコードだけが残り、再生に必要なファイルが存在しない状態を避けられます。

If there are multiple causes, keep them separate. Do not force them into one root cause unless the evidence supports it.

## Reader Load

- Do not make the reader remember names that never appear again.
- Put definitions before the place where the reader needs them.
- If a term is project-specific, define it once in operational terms.
- If a detail is only evidence for Codex, keep it out of the final prose.
- Prefer a short explanation with one exact example over a broad abstract paragraph.

## AI-Smell Checks

Before returning the prose, remove or rewrite:

- Generic endings such as `今後の展開が注目されます`, `重要です`, `不可欠です`, `多角的に`, `深掘り`, `本質的に`.
- Mechanical `AではなくB` contrasts where no real contrast is needed.
- Uniform sentence rhythm and repeated paragraph shapes.
- Excessive politeness that weakens technical claims.
- Bold labels, colon-heavy bullets, or decorative emphasis unless the target medium expects them.
- Claims that could fit any repository or any PR.

## Output Discipline

- For Markdown-native deliverables, use headings only when they help navigation.
- For short PR bodies and team updates, do not apply book/article-specific rules such as one-sentence-per-line, footnotes, or long definitions.
- If the source material is noisy, compress it into reader-visible behavior, decision, risk, and next action.
