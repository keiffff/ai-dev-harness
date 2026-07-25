# AGENTS Generic Harness

このファイルは、特定プロジェクトへ持ち込む前の汎用 Codex harness 断片です。プロジェクト固有のパス、顧客名、issue/PR番号、社内用語、secret はここに置かない。

## Conversation

- 日本語で応答する。
- optional commentary を送らない。必要な coordination update は、不可逆操作、承認、blocker、ANDON 条件、長時間処理の節目に限定する。
- 通常の短い質問や技術説明では skill を過剰に読まない。

## Workflow Routing

- 実装、debug、review、writing、OpenSpec、advisor 相談のどれに当たるか曖昧な場合だけ `codex-loop-router` を使う。
- 文章成果物は `codex-writing`、意思決定文脈を残す design doc は `codex-decision-doc` を使う。
- 設計方針や長期保守性の副査は strategic review skill を使ってよいが、採否は Codex 本体が判断する。
- subagent は bounded scout として使い、最終判断、I/F 判断、Git 操作、互換性判断は main agent に残す。

## Contract Safety

- 既存テスト、既存 API、既存 domain 変換、既存 null/undefined/省略挙動は契約候補として扱う。
- テストが落ちても、削除・緩和・期待値変更で通さない。まず何を保証しているか、今回変更してよい契約かを確認する。
- 規制対象、金銭、認証、権限、永続化、外部連携では、明示仕様にない fallback、default、合成データ、空オブジェクト補完を追加しない。
- 不要になった中間実装を「xxx しないこと」テストとして残さない。public contract、incident recurrence、security/cost risk を守らない negative test は増やさない。

## Abstraction Discipline

- helper、wrapper、adapter、facade、mapper、policy 関数を追加する前に、その抽象が所有する責務を確認する。
- 差分を小さく見せるため、既存構造へ踏み込むのを避けるため、テストを通すため、将来使うかもしれないため、という理由では追加しない。
- 追加してよいのは、既存 repo の同責務パターンに合う、実質重複を減らす、境界を閉じ込める、または構造整理なしに安全な変更ができない場合に限る。

## OpenSpec

- OpenSpec 実装では artifact-driven workflow を使い、CLI が返す status/instructions を正とする。
- legacy fallback に落ちる場合は、CLI 更新や workflow 整備を優先し、proposal/design/tasks/spec の直接読みだけで進めない。
- 既存データ互換が必要に見える場合、いきなり fallback を実装せず、既存データ形、影響範囲、互換が必要な理由、互換を持たせない選択肢を整理して相談する。
- 同一セッション内で捨てた案や未リリースの中間状態には、明示がない限り backward compatibility を持たせない。

## Git

- commit、push、PR branch 更新、submodule sync は、最新のユーザー依頼で明示された場合だけ実行する。
- raw `git commit` / `git push` / `git rebase` / `git submodule update` を使わず、承認 wrapper を使う。
- `git add -f` で ignored/excluded files を stage しない。ignore/exclude は repo の意図として扱う。
- commit message は英語にする。
- 禁止 fallback: `git commit -a`、`git commit --amend`、temp clone commit/push、remote-only commit、別 worktree へのコピー検証。

## Cloud / External CLIs

- raw `aws` / `gcloud` / `gsutil` / `bq` / `gh` を使わない。読み取りは readonly wrapper に寄せる。
- cloud write、deploy、IAM 変更、secret 参照、DB CLI は Codex から実行しない。必要ならユーザーが実行できるコマンドとして提示する。
- package manager scripts は中身を確認する。`test` / `lint` / `typecheck` / `build` / `format` は許容し、`deploy` / `release` / `publish` / `migrate` / `seed` / `db` / `terraform` / `cdk` / `prod` 系は勝手に実行しない。
