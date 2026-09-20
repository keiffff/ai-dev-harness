# Skills

AIエージェントへ作業ごとの期待を伝えるCodexのスキルを管理します。

各スキルには、証拠の探し先、レビュー基準、成果物の形式、外部ツールの操作ルールなど、作業ごとに必要な指示を置きます。一般的な探索・実装・推敲はmain agentが行い、最終判断、インターフェースと互換性の判断、Git操作もmain agentが担います。

## Skill Map

| Skill | 使う場面 | 主な役割 | しないこと |
| --- | --- | --- | --- |
| `codex-openspec-workflow` | OpenSpec の作成、適用、照合、archive | current CLI、artifact、互換性ゲート、spec 照合を管理する | 通常の実装や、未承認 proposal の実装には使用しない |
| `codex-git-publish` | 明示的に依頼されたブランチの作成・切り替え、commit、push、PR ブランチの更新、submodule sync | wrapper を経由した Git mutation 手順を管理する | skill 自体に Git の mutation 権限があると勝手に判断しない |
| `codex-context-engineering` | リポジトリの既存パターン、関連テスト、仕様、PR の状況を把握する必要があるとき | 問いに対応する証拠の探索先と、既存のコード所有者や実行経路を確認する | 課題と無関係なファイルをむやみに広く読み込まない |
| `codex-incremental-implementation` | 複数ファイルにまたがる実装、OpenSpec tasks、リファクタリング、機能開発 | 既存の実行経路、観測可能な契約、適切なテスト範囲を維持して進める | 根拠のない大規模な変更（speculative edit）を一気に入れない |
| `codex-debugging-loop` | test、build、CI、API、browser、runtime log で失敗が発生したとき | 直接観測した事実と原因の仮説を切り分け、再現、原因特定、修正、再確認の流れに戻す | エラー表示の文面だけから原因や対処を決めつけない |
| `codex-code-review` | diff review、完了前レビュー、AI が生成したコードの確認 | bug、regression、テスト漏れ（missing test）、設計構造、残存リスクを検証する | 変更内容の要約だけでレビューを終わらせない |
| `codex-interface-review` | API、schema、state、永続化データ、モジュール境界を変更するとき | インターフェース契約、互換性、境界条件を精査する | 実装側の都合だけで契約の変更を通さない |
| `codex-doubt-review` | 自明でない判断、移行、処理順序、べき等性（idempotency）、本番リスクが伴うとき | 採用案をあえて批判的・敵対的に見直し、暗黙の前提や脆弱な仮定を洗い出す | 何でも否定・批判すること自体を目的に使わない |
| `codex-decision-integrity` | 既存の判断に対する異論、競合する情報、方針転換の提案が生じたとき | 新しい情報を分類し、根拠に基づいて維持・変更・保留を選択する | ユーザーからのプレッシャーや reviewer の断定だけで判断を変えない |
| `codex-frontend-ui` | UI の設計方針、HTML/mock/report の作成、レビュー用の可視化、既存デザインシステムへの準拠、visual QA | 既存デザインへの準拠、視覚的品質、元資料との整合、目視・画面検証の観点を確認する | 正本となるソース（canonical source）を生成 HTML に置き換えたり、事前の合意なくフルアプリでのブラウザ検証を始めたりしない |
| `codex-artifact-integrity` | HTML、SVG、図、資料、長文の生成や大幅修正を行った直後 | 明示された要件や提示意図と成果物候補の意味内容を照合し、独断による構成変更、情報の削除、誤解を招く比較、不要な言い訳、役割やフローの誤記を採用前に検出する | pixel単位の重なりや余白は判定せず、API不通を新たなblockerとしない |
| `claude-html-report` | 複数章の構成、比較図、画像、密度の高い情報設計が必要な単体（standalone）HTML 資料を作成するとき | Codex が証拠契約をまとめ、Claude が資料全体の構成・執筆を行い、Codex が事実関係と表示を検証する | Claude にリポジトリ調査、事実認定、直接のファイル編集を任せない |
| `codex-writing` | PR の説明文、README、チーム共有資料、リリースノート、返信案などの文章成果物を作成するとき | 読者、目的、確定した事実、書かない範囲を整理した上で本文を執筆する | `claude-html-report` の単体 HTML を除き、Claude に文章の草稿作成を外注しない |
| `gemini-japanese-polish` | 検証済みの事実や素材をもとに、日本語成果物全体の構成・執筆を Gemini に任せたいとき | Codex が事実と執筆条件を確定し、隔離された Antigravity CLI 上の Gemini 3.8 Flash Medium が全文の構成・見出し・文章を作成し、Codex が事実関係を検証する。HTML は完了状態を検証し、不完全なら 1 回だけ再生成する | 事実調査、暗黙の操作実行、モデルの切り替え、無制限の再試行を任せない |
| `codex-decision-doc` | design doc、ADR/RFC、移行方針、判断の記録を残すとき | 下された判断、その理由、検討した代替案、互換性への配慮、残存リスクを記録する | 実装対象ファイルの一覧や、単なる作業ログを書き連ねない |
| `codex-cdk-design-review` | CDK、CloudFormation、スタック分割、共有環境、クロススタック参照を取り扱うとき | リソースの所有権（resource ownership）、依存の向き、物理名、クォータ上限、リージョン制約を事前に確認する | 隔離された環境（isolated 環境）でのみ通るような設計を、安全な構成として扱わない |
| `claude-strategic-review` | 全体方針、アーキテクチャ設計、移行計画、長期的な保守性を広く評価したいとき | Claude Opus にサイドカーとしてのレビューを依頼する | 最終判断の権限やリポジトリの編集権限を Claude に渡さない |
| `claude-fable-strategic-review` | Fable 5 の適用を明示的に試すなど、綿密な戦略レビューを行いたいとき | より思考負荷の高い長期視点のアドバイザー（long-horizon advisor）として活用する | 通常のレビューや実装作業には使用しない |
| `chrome-devtools-on-demand` | ネットワーク、コンソール、パフォーマンス、ページ要素の検証が必要なブラウザデバッグを行うとき | 必要なタイミングに限定して DevTools MCP を起動し、解析を行う | 常時ブラウザ自動操作が動いている前提の運用をしない |
| `codex-thread-time-audit` | Codex thread における作業時間や日次稼働を集計したいとき | 各スレッドのターンから開始・終了時刻を抽出して実働時間を集計する | スレッド全体の作成日時・更新日時（thread-level created/updated）だけで集計しない |
| `codex-thread-handoff` | タスクの長期化と複数の劣化兆候により、クリーンな新コンテキスト（fresh task）への移行が有効なとき | 自動提案はタスク中1回まで。引き継ぎ先には `gpt-5.6-sol` / `high` を明示し、同一ホスト・同一チェックアウトなら待機しない高速経路を使い、成果物（artifact）を転送する場合は30秒以内に同期を検証する | コンテキスト圧縮（compaction）だけを理由に提案しない。また、ID未確定時にworktreeから推測したりタスクを再作成したりしない |
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
- 長期化したタスクを新たなコンテキストへ引き継ぐなら `codex-thread-handoff`

## Principle

すべての規則をAGENTS.mdに記述すると、常時読み込む文脈が増え、エージェントが各指示の重要度を判断しにくくなります。そのため、常時必要な基本ルールだけをAGENTS.mdに残し、作業ごとの詳しい指示はスキルと参照資料へ分けます。

実際の `~/.codex/skills` への同期手順は、それぞれの利用環境に合わせて決定します。
