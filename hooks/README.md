# Hooks

Codexによる誤操作を早い段階で止めるためのlocal safety policyを管理します。

hook は sandbox を置き換えるものではありません。PreToolUse hook は、agent が raw CLI の直接実行、secret の表示、破壊的な操作、あるいは危険な shell 構文の実行へ進もうとした際、会話と実行の境界でそれを阻止します。PermissionRequest hook は、Codex が承認を要求する操作を Jev で事前に判定し、確信を持って判断できない場合に限って通常の approval に差し戻します。

## Runtime Contract

`runtime-contract-context.py` は、既に開いているtaskにも現在の短い運用規則を届けます。`SessionStart` の startup、resume、clear、compact では必ず注入し、`UserPromptSubmit` では同じtaskへ最後に届けた内容から `runtime-contract.md` が変わった場合だけ再注入します。これにより、AGENTS.mdを更新した後に既存taskが古い要約や開始時の文脈だけで動き続ける状態を避けます。

`runtime-contract.md` はAGENTS.mdの代替ではありません。全体の規則はAGENTS.mdに置き、そのうち既存taskへ即時に反映する必要がある短い規則だけをこのファイルにも記載します。hookは契約本文のSHA-256だけをtaskごとに `~/.codex/hook-state/runtime-contract/` へ保存し、会話や入力文は保存しません。ファイルの欠落、入力形式の不一致、状態ファイルへの書き込み失敗は実行を止めません。

## Role In The Harness

AIエージェントに期待する振る舞いは、プロンプトの指定だけでは固定できません。hookは、その期待を実行前に検査するための層です。

- Git の commit/push は approved wrapper に集約する
- AWS / GCP / GitHub CLI は raw command ではなく read-only wrapper に集約する
- `.env` や credential file を直接出力・表示する代表的な shell command を阻止する
- `rm -rf`、`git clean`、recursive chmod/chown などの破壊的操作を阻止する
- shell interpreter、command substitution、process substitution、multiline shell、shell grouping、xargs、sudo を保守的に拒否する
- Browser / CUA runtime では `iab` を明示した in-app 操作のみを許可し、ユーザーのブラウザ操作や接続先が不明な操作を制限する

`shell-policy.py` は、Git、AWS、GCP、GitHub CLI、local safety に関する各検査を 1 回の PreToolUse hook からまとめて呼び出します。各 policy は単体テストの実施と責務分離のために個別のファイルとして維持しますが、1 つの shell 呼び出しに対して 5 本の hook を重複して登録することはありません。

## Jev Permission Review

`jev-agent-review` は、承認要求が発生した Bash、`apply_patch`、MCP などの tool 呼び出しを `@jev-kit/hook-adapters` で共通形式へ変換し、`@jev-kit/agent-review` の版管理された契約で Jev に渡して判定します。プロンプトへ注入された policy message を除外した直近のユーザー依頼、承認理由、tool 名および入力を 1 回の API 呼び出しで評価し、policy 整合度と指示一致度がそれぞれ 0.70 以上、かつ高リスク度が 0.15 以下の場合にのみ `allow` を返します。指示一致度の評価では、対象プロジェクトや操作の取り違え、単なる質問を操作許可と取り違える誤認、部分的な修正依頼を全体再生成へ拡大させていないかも検査します。この判定基準は `hooks/codex/jev-permission-review-policy.json` に置き、通常の閲覧・編集・テスト、明示された commit/push、外部モデル向け資料生成と、secret の読み取り、クラウド環境の変更、意図しない外部操作とを切り分けた実測例に基づいています。Jev 自身が `deny` を返すことはありません。

secret の候補となる文字列は Jev へ送信しません。API key が設定されていない場合、実ユーザー文脈を取得できない場合、通信失敗、不正な応答、あるいは score が基準に満たない場合は何も返さず、既存の OpenAI auto-review またはユーザー自身による承認へと差し戻します。SDKの自動再試行は無効で、1回のhookにつきJevの試行も1回です。tool の入力に対して独自に長さの上限を設けたり、途中で切り詰めたりすることはありません。また、PreToolUse の各 policy や sandbox も引き続き有効であり、Jev の判定がこれらを迂回することはありません。

Jev による実際の許可状況を確認できるよう、生（raw）の入力内容は残さず、判定理由ごとの件数および直近の tool 名、契約、score のみを `~/.codex/hook-state/jev-permission-review/status.json` に記録します。状態記録の失敗は、算出済みの承認判定を変更しません。

Jev CLI 自体は環境変数 `TYPESAFE_API_KEY` のみを読み取り、Keychain に直接アクセスしません。PermissionRequest の実行コマンドは汎用の `keychain-env-exec` を経由し、macOS Keychain の service `JEV_PERMISSION_REVIEW_API_KEY` から取得した値を子プロセスの `TYPESAFE_API_KEY` へ注入します。key の値がコマンド引数、stdout、stderr、あるいは Jev の状態記録に出力されることはありません。実行環境には `keychain-env-exec`、`jev-agent-review`、および `jev-permission-review-policy.json` を配置します。

`jev-keychain-store.example`を`jev-keychain-store`として配置すれば、コマンド名を実行したあとにAPI keyを非表示で貼り付けられます。クリップボード上でkeyと保存用コマンドを切り替える必要はありません。

## Browser Permission Gate

`browser-policy.py` は、Browser runtime を利用する Node REPL および CUA REPL の呼び出しを検査します。`cua.createBrowserTab("iab", ...)`、`cua.getTab(id, { browser: "iab" })`、`agent.browsers.get("iab")`、`cua.getBrowser({ id: "iab" })`、`cua.listTabs({ browser: "iab" })` と、当該 REPL セッション内で取得されたタブの操作に対しては許可行を要求しません。Browser SDK の初期化も許可対象です。REPL を reset した後は、再度 `iab` を明示的に指定して選択する必要があります。

接続先の省略や動的な指定、全ブラウザの一覧取得、既存ブラウザの選択は原則として許可しません。外部ブラウザの操作は、AGENTS.md の定めに従ってユーザーが対象を明示的に指定して依頼した場合にのみ扱い、その際にも従来どおり現行ターンにおける許可行の提示が必要です。通常の in-app 操作ではこの許可行を求めません。

本 hook は、仕様化された API 呼び出し先と同一 REPL 内の実行履歴を確認する補助的な仕組みであり、任意の JavaScript コードの意味解析や、タブ変数の厳密な出自の検証までを行うものではありません。ユーザー自身のブラウザを勝手に操作しないという規律は、引き続き AGENTS.md 側の責務としても担保します。実行環境には `browser-policy.py` と、依存する `hook_utils.py` の双方を配置します。

`local-safety-policy.py` は、Python、Node.js、Ruby などの任意のソースコードを精査する DLP（情報漏洩防止）ツールではありません。開発用 interpreter を一律に禁止してしまうと通常のテスト、コード生成、動作検証に支障をきたすため、既知の shell コマンドを経由した不用意な内容出力のみを阻止します。secret は Codex が参照可能な workspace 内には配置せず、sandbox や OS のアクセス権限、secret manager を実質的な読み取り境界として運用してください。

## Local Database Work

ローカルデータベースに対する CLI 操作、マイグレーション、シードデータの投入、および DB を利用するテストは、追加承認なしで実行できます。DB CLI 向けの hook は、接続先として `localhost`、`127.0.0.1`、`::1` が明示されている場合に接続を許可します。接続先ホストの省略や未対応の接続形式は拒否されるため、確認済みのローカル接続先を host 引数または URI の形式で明示してください。

クライアントの設定ファイルや環境変数で決まる接続先、およびポートフォワーディング先はhookだけでは判別できないため、agentが実際の接続先を確認します。リモートDBの直接操作は引き続きAGENTS.mdで禁止します。package scriptは、名前にDB、migration、seed、ORM名が含まれていることだけを理由に拒否しません。agentは、scriptから呼び出される内部処理やテストの準備・後片付けまで追跡し、設定や環境変数によって決まる実際のDB接続先がすべてローカルであると確認できた場合に限って実行します。script名や入口の設定だけで判断せず、接続先を確認できない処理が含まれる場合は実行しません。deploy、release、publish、IaC、prodなどを含むscript名に対するブロックは引き続き維持します。

## Japanese Output

日本語の品質基準については、常時参照される `AGENTS.md` と文章作成時に適用される `codex-writing` が管理します。Stop hook による continuation prompt は、会話上でフィードバックとして表示されてユーザーへの回答を途中で遮ったような挙動に見えるため、日本語の推敲用途には使用しません。

## Parse Failure Policy

Codex hooks are a policy reminder and local guardrail, not a complete security boundary.

Execution policy hooks fail open only for empty input. Non-empty malformed JSON is rejected so hook API drift does not silently disable the policy.

These hooks are intentionally conservative because they are not full shell parsers. Keep sandbox and approval settings as the real execution boundary.
