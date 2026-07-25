# Decision Doc Style

## Core Standard

Decision docs preserve judgment that code cannot show. They should answer:

- What did we decide?
- Why was this decision necessary?
- What constraints made the decision reasonable?
- What did we reject?
- What compatibility or operational risk remains?
- What should future maintainers avoid re-litigating?

## Good Patterns

- `このAPIでは、既存クライアントがフィールド欠落を未設定として扱っているため、値なしは null ではなく省略を維持する。`
- `保存済み設定にも同じ読み取り経路を使うため、欠落フィールドを補完せず、読み取り時に未設定として扱う。`
- `案Bは実装量は少ないが、外部連携用データ生成の責務をAPIレスポンス整形に漏らすため採用しない。`
- `この判断では、DB schema ではなく読み取り時の解釈に閉じる。既存データの再書き込みを避け、移行失敗時の復旧手順を増やさないため。`

## Bad Patterns

- `X.ts を修正し、Y.ts に helper を追加した。`
- `テストを追加した。`
- `互換性のため fallback する。`
- `既存実装に合わせる。`
- `メタ情報を追加する。`
- `詳細は実装で対応する。`

## Rewrite Rules

- `実装した` -> `この判断では`
- `修正した` -> `この方針では`
- `追加した` -> `扱う` / `返す` / `保存する` / `維持する`
- `互換性のため` -> `どの既存データ、API、クライアント、テスト、運用を壊さないためか`
- `既存に合わせる` -> `既存のどの契約を維持するか`
- `影響する` -> `誰が、どの操作で、何を期待し、何が変わるか`
- `考慮する` -> `採用する` / `採用しない` / `未決事項として残す`

## Section Guidance

### 要約

2-4文で、決めたことと、その判断がなぜ重要かを書く。実装ファイル名から始めない。

### 背景

既存仕様、既存データ、既存運用、API契約、ドメイン制約を書く。作業ログは書かない。

### 問題

実装タスクではなく、未決だった判断を書く。`何を作るか` ではなく `何を決める必要があるか` を書く。

### 判断

採用する方針を、振る舞い、契約、責務分担、移行方針として書く。

### 判断理由

守りたい契約、運用上の制約、保守性、リスク、検証容易性を書く。

### 検討した代替案

現実的だった案だけを書く。各案に「なぜ採用しないか」を必ず書く。

### 互換性

既存データ、保存済みJSON、API response、クライアント、テスト、運用手順、migration のどれに関係するかを具体的に書く。不要な backward compatibility は負債として扱い、必要性を説明する。

### 影響と残るリスク

採用により良くなる点、残る制約、将来の変更で注意する点を書く。

### 検証観点

再現可能な確認を書く。ローカル作業ログ、失敗した試行、setup や retry の履歴は書かない。

### 対象外

今回決めないことを書く。`やってないこと` の羅列ではなく、判断範囲の境界を書く。

### 未決事項

追加判断が必要なことだけを書く。実装中に解けるTODOをここに逃がさない。

## Self-Review Checklist

- 本文の中心が実装差分ではなく判断になっているか。
- コードを読めば分かる情報を本文に並べていないか。
- 代替案に rejected reason があるか。
- 互換性の主張が対象を具体的に名指ししているか。
- fallback / backward compatibility を必要性なしに入れていないか。
- repo にないドメイン語を作っていないか。
- 日本語が内部思考の直訳や圧縮論理になっていないか。

## Reader-First Structure

Design docs are read by people who need to recover the decision later. Structure the document from the reader's flow, not from the agent's internal decomposition.

- Explain the business or operational flow before naming implementation parts.
- Define unfamiliar implementation terms before using them as headings.
- Prefer headings that name concrete flows or responsibilities, such as `依頼`, `結果照会`, `結果保存`, `既存レスポンスへの変換`.
- Avoid headings that only describe the document mechanics, such as `論点`, `判断すること`, `後続仕様`, `対応方針`, or `影響範囲`, unless they are part of the project template.
- If the whole document is a change/delta document, do not add another repeated `変更点` or `増えること` axis inside every section.
- Use a table only when multiple subjects are compared with the same columns. If each row needs different explanation, use short subsections instead.

## Simplicity Review

Before writing a decision as final, check whether the proposed design is adding machinery because it is possible rather than because it is needed.

- Prefer idempotency or existing-state reuse before adding rate limits or cooldowns.
- Prefer one lifecycle before adding separate TTL or artifact-retention windows.
- Prefer preserving the existing observable contract before adding fallback fields, alias fields, or compatibility paths.
- Treat unnecessary fallback and backward compatibility as future maintenance cost, not as automatic safety.
- If extra machinery is still needed, name the concrete user operation, external system, persistence contract, billing rule, or operational failure it protects.
