# Decision Phrasing Examples

- State the decision and its constraint: `既存クライアントがフィールド欠落を未設定として扱うため、このAPIでも省略を維持する。`
- Explain the rejected alternative: `案Bは実装量が少ないが、外部連携用の変換をAPIレスポンスの層へ持ち込むため採用しない。`
- Identify compatibility precisely: name the existing saved data, client or operation being preserved, rather than writing only `互換性のため`.
- Keep inherited constraints separate from current choices: existing storage ownership belongs in background unless this change actually moves it.

Implementation filenames matter only when the decision depends on ownership or a boundary. Keep exact behavior in the document even when a diagram summarizes it.
