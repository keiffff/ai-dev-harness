# Hooks

Codex の誤操作を早い段階で止めるための local safety policy を管理します。

hook は sandbox や approval を置き換えるものではありません。役割は、agent が raw CLI、secret 表示、破壊的操作、危険な shell 構文に進もうとしたときに、会話と実行の境界で止めることです。

## Role In The Harness

AI agent に期待する振る舞いは、プロンプトだけでは固定できません。hook は、その期待を実行前の検査として置くための層です。

- Git の commit/push は approved wrapper に寄せる
- AWS/GCP/GitHub CLI は raw command ではなく read-only wrapper に寄せる
- `.env` や credential file の表示を止める
- `rm -rf`、`git clean`、recursive chmod/chown などの破壊的操作を止める
- shell interpreter、command substitution、process substitution、multiline shell、shell grouping、xargs、sudo を保守的に拒否する

## Japanese Output

日本語の品質基準は、常時読む `AGENTS.md` と文章作成時の `codex-writing` が持ちます。Stop hook の continuation prompt は会話に feedback として表示され、回答を遮ったように見えるため、日本語の推敲には使用しません。

## Context Handoff Reminder

`compaction-handoff-reminder.py` は、同じ task で2回目の compaction が起きたときだけ、次の安全な区切りで `codex-thread-handoff` を使って移行要否を確認するよう Codex へ context を渡します。

hook 自体は task の作成、fork、archive を行いません。実行中の command、編集、test、approval、未解決の失敗も中断させません。提案と task 操作は、引き続き `codex-thread-handoff` の制約とユーザーの明示承認に従います。

compaction 回数は session ごとに `~/.codex/hook-state/compaction-handoff/` へ保存します。test などで保存先を分離する場合は `CODEX_HANDOFF_STATE_DIR` を指定できます。入力を解釈できない場合は、作業を妨げないよう何も通知せず終了します。

### Activation Check

command hook は、設定へ追加しただけでは実行されません。追加または command 変更後は Codex を再起動し、CLI の `/hooks` で `SessionStart` の compact hookを確認して trust します。

導入完了は次の両方で確認します。

- `/hooks` で対象hookが `Active` になり、`Review` が0である
- 実際の1回目のcompaction後に `~/.codex/hook-state/compaction-handoff/` へstateファイルが作られる

スクリプトへの模擬入力やunit testだけでは、Codex lifecycleへの接続、trust、実行を確認したことにはなりません。

## Parse Failure Policy

Codex hooks are a policy reminder and local guardrail, not a complete security boundary.

Execution policy hooks fail open only for empty input. Non-empty malformed JSON is rejected so hook API drift does not silently disable the policy.

These hooks are intentionally conservative because they are not full shell parsers. Keep sandbox and approval settings as the real execution boundary.
