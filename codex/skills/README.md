# Skills

AIエージェントへ作業ごとの期待を伝えるCodexのスキルを管理します。

各スキルには、証拠の探し先、レビュー基準、成果物の形式、外部ツールの操作ルールなど、作業ごとに必要な指示を置きます。一般的な探索・実装・推敲はmain agentが行い、最終判断、インターフェースと互換性の判断、Git操作もmain agentが担います。

## Skill Map

| Skill | 使う場面 | 主な役割 | しないこと |
| --- | --- | --- | --- |
| `codex-openspec-workflow` | ユーザーが依頼した場合、または既存のOpenSpecが作業を規定する場合 | current CLI、artifact、互換性ゲート、spec 照合を管理する | 通常の実装へ自発的に追加せず、未承認 proposal を実装しない |
| `codex-git-publish` | 明示的に依頼されたGit公開・PR・issue操作 | Git操作は`git-user-approved`、PR・issue操作は`gh-user-approved`を経由し、依頼された対象と操作だけを実行する | 読み取りや本文案の作成をPR・issue書き込みの許可と扱わず、過去の許可を持ち越さない |
| `codex-recall-work` | 過去の調査・採否・訂正を確認して作業を始める、または再開するとき | ローカル知識から関連記録と実行資産を探し、現状照合して元の作業へ使う | 全履歴を常時読み込まず、過去記録を現行仕様や操作許可と扱わない |
| `codex-learn-from-work` | 過去の知識が役立たなかった、訂正が繰り返された、検証で改善点が出たとき | 失敗した接続箇所を調べ、既存の記録・code・skillを直して次のタスクで確かめる | 比較報告だけで改善依頼を終えず、良い試行だけを採用しない |
| `codex-context-engineering` | リポジトリの既存パターン、関連テスト、仕様、PR の状況を把握する必要があるとき | 問いに対応する証拠の探索先と、既存のコード所有者や実行経路を確認する | 課題と無関係なファイルをむやみに広く読み込まない |
| `codex-incremental-implementation` | 複数ファイルにまたがる実装、OpenSpec tasks、リファクタリング、機能開発 | 既存の実行経路、観測可能な契約、適切なテスト範囲を維持して進める | 根拠のない大規模な変更（speculative edit）を一気に入れない |
| `codex-debugging-loop` | test、build、CI、API、browser、runtime log で失敗が発生したとき | 直接観測した事実と原因の仮説を切り分け、再現、原因特定、修正、再確認の流れに戻す | エラー表示の文面だけから原因や対処を決めつけない |
| `codex-code-review` | diff review、完了前レビュー、AI が生成したコードの確認 | bug、regression、テスト漏れ（missing test）、設計構造、残存リスクを検証する | 変更内容の要約だけでレビューを終わらせない |
| `codex-interface-review` | API、schema、state、永続化データ、モジュール境界を変更するとき | インターフェース契約、互換性、境界条件を精査する | 実装側の都合だけで契約の変更を通さない |
| `codex-doubt-review` | 自明でない判断、移行、処理順序、べき等性（idempotency）、本番リスクが伴うとき | 採用案をあえて批判的・敵対的に見直し、暗黙の前提や脆弱な仮定を洗い出す | 何でも否定・批判すること自体を目的に使わない |
| `codex-decision-integrity` | 既存の判断に対する異論、競合する情報、方針転換の提案が生じたとき | 新しい情報を分類し、根拠に基づいて維持・変更・保留を選択する | ユーザーからのプレッシャーや reviewer の断定だけで判断を変えない |
| `codex-frontend-ui` | UI の設計方針、HTML/mock/report の作成、レビュー用の可視化、既存デザインシステムへの準拠、visual QA | 既存デザインへの準拠、視覚的品質、元資料との整合、目視・画面検証の観点を確認する | 正本となるソース（canonical source）を生成 HTML に置き換えたり、事前の合意なくフルアプリでのブラウザ検証を始めたりしない |
| `codex-artifact-integrity` | 保持条件・比較条件・変更範囲がある成果物の作成・大幅改稿後 | 元依頼・原資料・変更前の成果物と候補を照合し、具体的な不一致を確認して作成担当へ返す | 検証を編集権限と扱わず、pixel単位の重なりや余白は別途目視し、API不通を新たなblockerとしない |
| `claude-html-report` | 複数章の構成、比較図、画像、密度の高い情報設計が必要な単体（standalone）HTML 資料を作成するとき | Codexは元依頼・原資料を渡して検証し、Claudeが構成・執筆・対象HTMLへの直接の局所編集を担当する | Codexが中間の要約・構成指示を作ったり、生成後のHTMLの文章・配置・metadataを編集したりしない |
| `codex-writing` | PR本文、README、Slack報告・確認依頼などの文章成果物と、その継続会話 | 現在の依頼を先に判定し、長い資料は根拠選択→構成の照合→生成へ進める。既存原稿は選んだ箇所だけを置換する | 観測共有を追加改稿に変えず、通常応答・語句だけの校正へ重い工程を適用しない。`claude-html-report`と明示依頼されたGemini作成の所有を守る |
| `gemini-japanese-polish` | 検証済みの事実や素材をもとに、日本語成果物全体の構成・執筆を Gemini に任せたいとき | Codex が事実と執筆条件を確定し、隔離された Antigravity CLI 上の Gemini 3.8 Flash Medium が全文の構成・見出し・文章を作成し、Codex が事実関係を検証する。HTML は完了状態を検証し、不完全なら 1 回だけ再生成する | 事実調査、暗黙の操作実行、モデルの切り替え、無制限の再試行を任せない |
| `codex-decision-doc` | design doc、ADR/RFC、移行方針、判断の記録を残すとき | 下された判断、その理由、検討した代替案、互換性への配慮、残存リスクを記録する | 実装対象ファイルの一覧や、単なる作業ログを書き連ねない |
| `codex-cdk-design-review` | CDK、CloudFormation、スタック分割、共有環境、クロススタック参照を取り扱うとき | リソースの所有権（resource ownership）、依存の向き、物理名、クォータ上限、リージョン制約を事前に確認する | 隔離された環境（isolated 環境）でのみ通るような設計を、安全な構成として扱わない |
| `claude-strategic-review` | 問題設定や全体方針を、元のユーザー目的と証拠から問い直したいとき | Claudeが独立に問題を捉えて提案を検討する。Codexは採否・理由を決め、Claudeの見解と区別して人間へ報告する | Codex案を前提とした実装適合レビューだけで済ませず、最終判断や編集権限をClaudeへ渡さない |
| `claude-fable-strategic-review` | Fable 5 の適用を明示的に試すなど、綿密な戦略レビューを行いたいとき | より思考負荷の高い長期視点のアドバイザー（long-horizon advisor）として活用する | 通常のレビューや実装作業には使用しない |
| `chrome-devtools-on-demand` | in-app browserでは取得できないDevTools情報が必要なとき | MCP登録は有効のまま維持し、必要な調査でツールを使う。外部ブラウザの操作権限はAGENTS.mdに従う | 通常の調査ごとに設定変更・再起動・offを要求せず、登録の有効化をブラウザ操作の許可と扱わない |
| `codex-thread-time-audit` | Codex thread における作業時間や日次稼働を集計したいとき | 各スレッドのターンから開始・終了時刻を抽出して実働時間を集計する | スレッド全体の作成日時・更新日時（thread-level created/updated）だけで集計しない |
| `codex-thread-handoff` | ユーザーが最新の依頼で、担当中のタスクを新しいタスクへ移すよう明示的に求めたとき | 担当中のタスク全体を引き継ぐ。引き継ぎ先には `gpt-6.1-sol` / `medium` を明示し、同一ホスト・同一チェックアウトなら待機しない高速経路を使い、成果物（artifact）を転送する場合は30秒以内に同期を検証する | 自発的にhandoffを提案しない。また、ID未確定時にworktreeから推測したりタスクを再作成したりしない |
| `grok-x-research` | X の最新投稿、特定アカウントの発言、障害発生時の初動、実務者の反応を調べるとき | X 専用のスカウト役として URL、対立意見、引用元（citation）、発生費用を報告する | 一般的な Web 調査、最終検証、設計判断、リポジトリのコード変更を任せない |

## How To Choose

依頼内容に合うスキルを直接選びます。通常のコードレビューやインターフェース確認はmain agentが担当し、重大かつ未確認の前提がある場合は`codex-doubt-review`による独立レビューを1回実施します。その際は、同じreviewerに必要なインターフェースの観点も渡します。Astraを指定した副査にはnative subagentを使います。

- 実装前に既存文脈が不足しているなら `codex-context-engineering`
- エラーやテスト失敗が出ているなら `codex-debugging-loop`
- UI の見せ方や画面品質が関係するなら `codex-frontend-ui`
- 単体 HTML 全体の情報設計と構成を Claude へ任せるなら `claude-html-report`
- API や保存形式を変更するなら `codex-interface-review`
- 判断の経緯を後から参照できるようにするなら `codex-decision-doc`
- 読者向けの文章成果物を作成するなら `codex-writing`
- 方針を外部視点から疑い直したいなら strategic review 系
- 既存の判断を維持・変更・保留するなら `codex-decision-integrity`
- X 固有の最新情報が必要なら `grok-x-research`
- ユーザーが明示的に求めたタスクの引き継ぎには `codex-thread-handoff`

## Principle

すべての規則をAGENTS.mdに記述すると、常時読み込む文脈が増え、エージェントが各指示の重要度を判断しにくくなります。そのため、常時必要な基本ルールだけをAGENTS.mdに残し、作業ごとの詳しい指示はスキルと参照資料へ分けます。

実際の `~/.codex/skills` への同期手順は、それぞれの利用環境に合わせて決定します。

## Local Work Memory

`codex-recall-work` と `codex-learn-from-work` は標準のAgent Skillsとして配置します。私的な記録は共有リポジトリへ含めず、ローカルに配置したskillの `references/library` を知識置き場へ接続します。ユーザーのskill探索先からローカルskillへリンクし、本文の読み込みは通常のskill選択に任せます。具体的な記録・検証assetは用途ごとの索引から参照し、全件を起動時に読み込ませません。
