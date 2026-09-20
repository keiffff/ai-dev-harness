# Hooks

Codex の誤操作を早い段階で止めるための local safety policy を管理します。

hook は sandbox を置き換えるものではありません。PreToolUse hook は、agent が raw CLI、secret 表示、破壊的操作、危険な shell 構文に進もうとしたときに、会話と実行の境界で止めます。PermissionRequest hook は、Codexが承認を求める操作をJevで先に判定し、確信を持って判断できない場合だけ通常のapprovalへ戻します。

## Role In The Harness

AI agent に期待する振る舞いは、プロンプトだけでは固定できません。hook は、その期待を実行前の検査として置くための層です。

- Git の commit/push は approved wrapper に寄せる
- AWS/GCP/GitHub CLI は raw command ではなく read-only wrapper に寄せる
- `.env` や credential file を直接表示する代表的なshell commandを止める
- `rm -rf`、`git clean`、recursive chmod/chown などの破壊的操作を止める
- shell interpreter、command substitution、process substitution、multiline shell、shell grouping、xargs、sudo を保守的に拒否する
- Browser / CUA runtime は `iab` を明示したin-app操作を許可し、ユーザーのブラウザや接続先が不明な操作を制限する

`shell-policy.py` は、Git、AWS、GCP、GitHub CLI、local safety の各検査を1回のPreToolUse hookから呼び出します。個別policyは単体testと責務分離のため残しますが、同じshell呼び出しへ5本のhookを登録しません。

## Jev Permission Review

`jev-permission-review.py` は、承認要求が発生したBash、`apply_patch`、MCPなどのtool呼び出しをJevへ渡します。注入されたpolicy messageを除いた直近のユーザー依頼、承認理由、tool名と入力を1回のAPI呼び出しで評価し、policy整合度と指示一致度がそれぞれ0.70以上かつ高リスク度が0.15以下の場合だけ`allow`を返します。指示一致度では、対象projectや操作の取り違え、質問を操作許可として扱う誤読、部分修正から全体再生成への拡大も検査します。この境界は、通常のread・edit・test・明示されたcommit/push・外部model資料生成と、secret読取・cloud変更・無関係な外部操作を分けた実測ケースに基づきます。Jev自身は`deny`を返しません。

secret候補はJevへ送信しません。API key未設定、通信失敗、2秒のtimeout、不正応答、またはscore不足の場合は何も返さず、既存のOpenAI auto-reviewまたはユーザー承認へ戻します。tool入力へ独自の長さ上限や切り詰めは加えません。PreToolUseの各policyとsandboxも引き続き適用され、Jevの判断がそれらを迂回することはありません。

Jevが実際に許可しているか確認できるよう、raw入力を残さず、結果別件数と直近のtool名・scoreだけを`~/.codex/hook-state/jev-permission-review/status.json`へ記録します。

Jev hook自身は`TYPESAFE_API_KEY`だけを読み、Keychainへアクセスしません。PermissionRequestのcommandは汎用`keychain-env-exec`を経由し、macOS Keychainのservice `JEV_PERMISSION_REVIEW_API_KEY`を子processの`TYPESAFE_API_KEY`へ注入します。keyの値は引数、stdout、stderr、Jev stateへ出しません。実行時には`keychain-env-exec`、`jev-permission-review.py`、依存する`hook_utils.py`を配置します。

`jev-keychain-store.example`を`jev-keychain-store`として配置すると、コマンド名を入力してからAPI keyを非表示で貼り付けられます。クリップボードにあるkeyと保存用commandを持ち替える必要はありません。

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

## Parse Failure Policy

Codex hooks are a policy reminder and local guardrail, not a complete security boundary.

Execution policy hooks fail open only for empty input. Non-empty malformed JSON is rejected so hook API drift does not silently disable the policy.

These hooks are intentionally conservative because they are not full shell parsers. Keep sandbox and approval settings as the real execution boundary.
