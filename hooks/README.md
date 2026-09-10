# Hooks

Codex の誤操作を早い段階で止めるための local safety policy を管理します。

hook は sandbox や approval を置き換えるものではありません。役割は、agent が raw CLI、secret 表示、破壊的操作、危険な shell 構文に進もうとしたときに、会話と実行の境界で止めることです。

## Role In The Harness

AI agent に期待する振る舞いは、プロンプトだけでは固定できません。hook は、その期待を実行前の検査として置くための層です。

- Git の commit/push は approved wrapper に寄せる
- AWS/GCP/GitHub CLI は raw command ではなく read-only wrapper に寄せる
- `.env` や credential file を直接表示する代表的なshell commandを止める
- `rm -rf`、`git clean`、recursive chmod/chown などの破壊的操作を止める
- shell interpreter、command substitution、process substitution、multiline shell、shell grouping、xargs、sudo を保守的に拒否する
- Browser / CUA runtime は `iab` を明示したin-app操作を許可し、ユーザーのブラウザや接続先が不明な操作を制限する

`shell-policy.py` は、Git、AWS、GCP、GitHub CLI、local safety の各検査を1回のPreToolUse hookから呼び出します。個別policyは単体testと責務分離のため残しますが、同じshell呼び出しへ5本のhookを登録しません。

`decision-integrity-policy.py` は、書き込みを伴うshellまたは`apply_patch`の前に、現在のユーザーturnで`decision-checkpoint.py`が有効な判断状態を記録したか検査します。成功したcheckpoint commandの実行結果だけを受け付け、文書や一般tool出力に同じ文字列が含まれていてもcheckpointとは扱いません。`NEW`、`HOLD`、`REVISE`、`SUSPEND`の遷移と許可された根拠種別を機械的に確認し、checkpointなしの変更を拒否します。自然言語の意味や判断の正しさをhookだけで推測するものではありません。

## Browser Permission Gate

`browser-policy.py` は Browser runtime を使う Node REPL と CUA REPL の呼び出しを検査します。`cua.createBrowserTab("iab", ...)`、`cua.getTab(id, { browser: "iab" })`、`agent.browsers.get("iab")`、`cua.getBrowser({ id: "iab" })`、`cua.listTabs({ browser: "iab" })`と、そのREPLで取得したタブの操作には許可行を求めません。Browser SDKの初期化も許可します。REPLをresetした後は、再び`iab`を明示して選択します。

接続先の省略・動的指定、全ブラウザの一覧取得、既存ブラウザの選択は通常許可しません。外部ブラウザはAGENTS.mdに従ってユーザーが対象を明示的に依頼した場合だけ扱い、従来の現在turnの許可行も必要です。通常のin-app操作のためにこの許可行を求めません。

hookは文書化されたAPIの選択先と同じREPLの履歴を確認する補助で、任意のJavaScriptの意味やタブ変数の由来を完全に検証するものではありません。ユーザーのブラウザを操作しない責務はAGENTS.mdにも残します。実行時には`browser-policy.py`と依存する`hook_utils.py`の両方を配置します。

`local-safety-policy.py` は任意のPython、Node.js、Rubyなどのソースコードを解析するDLPではありません。開発用interpreterを一律に禁止すると通常のtest、生成、検証を妨げるため、既知のshell経由の誤表示だけを止めます。secretはCodexから読めるworkspaceへ置かず、sandbox、OSの権限、secret managerを実際の読み取り境界として使います。

## Local Database Work

ローカルDBのCLI操作、migration、seed、DBを使うテストは追加承認なしで実行できます。DB CLIのhookは、明示された`localhost`、`127.0.0.1`、`::1`への接続を許可します。接続先の省略や未対応の接続形式は拒否するため、確認したローカル接続先をhost引数またはURIで明示します。

client設定や環境変数による接続先、port forwardingの先はhookでは確定できないため、agentが実際の接続先を確認します。リモートDBの操作は引き続きAGENTS.mdで禁止します。DB、migration、seed、ORM名を含むことだけではpackage scriptを拒否しません。agentがscriptから呼び出される内部処理とテストの準備・後片付けまで追い、設定や環境変数によって決まる実際のDB接続先がすべてローカルであると確認できた場合だけ実行します。script名や入口の接続設定だけでは判断せず、接続先を確認できない処理があれば実行しません。deploy、release、publish、IaC、prod系のscript名に対するブロックは維持します。

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
