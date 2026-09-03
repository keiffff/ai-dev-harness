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
- Browser / CUA runtime は、現在のユーザーメッセージに一回限りの許可行 `browser-control: allow` がある場合だけ許可する

`shell-policy.py` は、Git、AWS、GCP、GitHub CLI、local safety の各検査を1回のPreToolUse hookから呼び出します。個別policyは単体testと責務分離のため残しますが、同じshell呼び出しへ5本のhookを登録しません。

`decision-integrity-policy.py` は、書き込みを伴うshellまたは`apply_patch`の前に、現在のユーザーturnで`decision-checkpoint.py`が有効な判断状態を記録したか検査します。`NEW`、`HOLD`、`REVISE`、`SUSPEND`の遷移と許可された根拠種別を機械的に確認し、checkpointなしの変更を拒否します。自然言語の意味や判断の正しさをhookだけで推測するものではありません。

## Browser Permission Gate

`browser-policy.py` は Browser plugin を常時有効にしたまま、Browser runtime を使う Node REPL と CUA REPL の呼び出しを実行前に検査します。現在のユーザーメッセージに独立した行として `browser-control: allow` がなければ拒否します。Browser pluginや既存タブへのmentionは参照指定として扱い、それだけでは操作を許可しません。自然文の語句や不満の表現から許可を推測せず、過去のターンの許可も持ち越しません。

このhookは `browser-client.mjs`、`setupBrowserRuntime`、標準的な Browser binding、`cua.*` の呼び出しを対象にします。一度 Browser runtime を初期化したtaskでは、binding名を変えた迂回を防ぐため、以後の対象REPL呼び出しも同じ許可対象として扱います。Browserを使っていないtaskの通常の Node REPL 利用は対象外です。Browser plugin の手動有効化・無効化を運用手順にはしません。

## Japanese Output

日本語の品質基準は、常時読む `AGENTS.md` と文章作成時の `codex-writing` が持ちます。Stop hook の continuation prompt は会話に feedback として表示され、回答を遮ったように見えるため、日本語の推敲には使用しません。

## Context Handoff Reminder

`compaction-handoff-reminder.py` は、同じ task で2回目以降の compaction が起きるたびに、次の安全な区切りで `codex-thread-handoff` を使って移行要否を確認するよう Codex へ context を渡します。通知後も task を続けるか、fresh task へ移すかは、その時点のユーザーと Codex が判断します。

hook 自体は task の作成、fork、archive を行いません。実行中の command、編集、test、approval、未解決の失敗も中断させません。提案と task 操作は、引き続き `codex-thread-handoff` の制約とユーザーの明示承認に従います。

compaction 回数は session ごとに `~/.codex/hook-state/compaction-handoff/` へ保存します。test などで保存先を分離する場合は `CODEX_HANDOFF_STATE_DIR` を指定できます。入力を解釈できない場合は、作業を妨げないよう何も通知せず終了します。

### Activation Check

command hook は、設定へ追加しただけでは実行されません。追加または command 変更後は Codex を再起動し、CLI の `/hooks` で `SessionStart` の compact hookを確認して trust します。

導入完了は次の両方で確認します。

- `/hooks` で対象hookが `Active` になり、`Review` が0である
- 実際の1回目のcompaction後に `~/.codex/hook-state/compaction-handoff/` へstateファイルが作られる
- decision integrityでは、read-only commandがcheckpointなしで通り、write-bearing commandが拒否され、有効なcheckpoint後に同じturnの書き込みが通る

スクリプトへの模擬入力やunit testだけでは、Codex lifecycleへの接続、trust、実行を確認したことにはなりません。

## Parse Failure Policy

Codex hooks are a policy reminder and local guardrail, not a complete security boundary.

Execution policy hooks fail open only for empty input. Non-empty malformed JSON is rejected so hook API drift does not silently disable the policy.

These hooks are intentionally conservative because they are not full shell parsers. Keep sandbox and approval settings as the real execution boundary.
