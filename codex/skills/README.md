# Skills

AI agent に作業ごとの期待を渡すための Codex skills を管理します。

skillには、証拠の探し先、レビュー基準、成果物の形式、外部ツールの操作契約など、作業ごとに必要な指示を置きます。一般的な探索・実装・推敲はmain agentに任せます。

## Skill Map

| Skill | 使う場面 | 主な役割 | しないこと |
| --- | --- | --- | --- |
| `codex-openspec-workflow` | OpenSpec の作成、適用、照合、archive | current CLI、artifact、互換性gate、spec照合を管理する | 通常実装や未承認proposalの実装には使わない |
| `codex-git-publish` | 明示依頼されたbranch作成・切替、commit、push、PR branch更新、submodule sync | wrapper経由のGit mutation手順を管理する | skill自体からmutation権限を推定しない |
| `codex-context-engineering` | repo の既存パターン、関連テスト、仕様、PR 状況を読む必要があるとき | 問いに合う証拠の探し先と、既存の所有者・実行経路を確認する | 無関係なファイルを広く読み込まない |
| `codex-incremental-implementation` | 複数ファイルの実装、OpenSpec tasks、refactor、feature work | 既存経路、観測可能な契約、適切なテスト範囲を保つ | 大きな speculative edit を一気に入れない |
| `codex-debugging-loop` | test、build、CI、API、browser、runtime log が失敗したとき | 直接観測と原因仮説を分け、再現、原因特定、修正、再確認の loop に戻す | エラー表示だけから原因や対処を決めない |
| `codex-code-review` | diff review、完了前 review、AI 生成コードの確認 | bug、regression、missing test、構造、残リスクを見る | 変更内容の要約だけで終わらない |
| `codex-interface-review` | API、schema、state、persisted data、module boundary を変えるとき | I/F 契約、互換性、境界条件を確認する | 実装都合で契約変更を通さない |
| `codex-doubt-review` | 非自明な判断、移行、順序、idempotency、production risk があるとき | 採用案を敵対的に見直し、弱い前提を探す | 何でも否定するために使わない |
| `codex-decision-integrity` | 既存判断への反論、競合情報、方針転換が出たとき | 新情報を分類し、根拠のある維持・変更・保留を選ぶ | ユーザーの圧力やreviewerの断言だけで判断を変えない |
| `codex-frontend-ui` | UI 方針、HTML/mock/report、review visualization、既存デザインシステム準拠、visual QA | 既存デザインへの準拠、見た目、元資料との整合、視覚検証を確認する | canonical source を生成 HTML へ置き換えたり、full app browser 検証を勝手に始めたりしない |
| `codex-artifact-integrity` | HTML、SVG、図、資料、長文の生成・大幅修正後 | 明示要件と候補成果物をJevで照合し、勝手な構成変更、情報削除、誤解を招く比較、不要な言い訳、役割や流れの誤記を採用前に検出する | pixel単位の重なりや余白を判定せず、API不通を新しいblockerにしない |
| `claude-html-report` | 複数章、比較図、画像、密な情報設計が必要な standalone HTML 資料 | Codexが証拠契約を作り、Claudeが資料全体を構成し、Codexが事実と表示を検証する | Claudeへrepo調査、事実判断、直接のファイル編集を任せない |
| `codex-writing` | PR説明、README、チーム共有、release note、返信案などの文章成果物 | 読者、目的、事実、書かないことを整理して本文を書く | `claude-html-report`のstandalone HTMLを除き、Claudeに文章草稿を外注しない |
| `gemini-japanese-polish` | 検証済みの事実や素材から日本語成果物全体をGeminiに構成させたいとき | Codexが事実と執筆条件を確定し、隔離したAntigravity CLI上のGemini 3.8 Flash Mediumが構成・見出し・文章を全面的に作り、Codexが事実を検証する。HTMLは完了を検証し、不完全なら1回だけ再生成する | 事実調査、暗黙実行、モデル切替、無制限の再試行を任せない |
| `codex-decision-doc` | design doc、ADR/RFC、移行方針、判断の記録 | 判断、理由、代替案、互換性、残リスクを残す | 実装ファイル一覧や作業ログを書かない |
| `codex-cdk-design-review` | CDK、CloudFormation、stack、shared environment、cross-stack reference を触るとき | resource ownership、依存方向、物理名、quota、region を事前に見る | isolated 環境で通るだけの設計を安全扱いしない |
| `claude-strategic-review` | 方針、設計、移行、長期保守性を広く見たいとき | Claude Opus に sidecar review を依頼する | 最終判断や repo 編集を Claude に渡さない |
| `claude-fable-strategic-review` | Fable 5 を明示的に試す深い戦略レビュー | より重い long-horizon advisor として使う | 通常 review や実装には使わない |
| `chrome-devtools-on-demand` | network、console、performance、page inspection が必要な browser debug | 必要な時だけ DevTools MCP を起動する | 常時 browser automation を前提にしない |
| `codex-thread-time-audit` | Codex thread の作業時間や日次稼働を集計したいとき | thread turn から開始・終了時刻を抽出して集計する | thread-level created/updated だけで雑に集計しない |
| `codex-thread-handoff` | 長期化と複数の劣化兆候によりfresh taskへの移行が有効なとき | 自動提案はtask中1回まで。handoff先は`gpt-5.6-sol` / `high`を明示し、同一host・checkoutなら待機しない高速経路、artifact転送時は30秒以内の同期検証を使う | compaction単独で提案しない。ID未確定時にworktreeから推測したりtaskを再作成したりしない |
| `grok-x-research` | X の最新投稿、特定アカウントの発言、障害初動、実務者の反応を調べるとき | X 専用 scout としてURL、対立意見、citation、費用を返す | 通常Web調査、最終検証、設計判断、repo変更を任せない |

## How To Choose

依頼に合うskillを直接選びます。通常のcode reviewとI/F確認はmain agentが担当し、重大な未確認の前提には`codex-doubt-review`で独立レビューを1回行います。その同じreviewerへ必要なI/F観点も渡します。Astraを指定した副査にはnative subagentを使います。

- 実装前に既存文脈が足りないなら `codex-context-engineering`
- 失敗が出ているなら `codex-debugging-loop`
- UI の見せ方や画面品質が関係するなら `codex-frontend-ui`
- standalone HTML 全体の情報設計と構成をClaudeへ任せるなら `claude-html-report`
- API や保存形式が変わるなら `codex-interface-review`
- 判断が後から読み返されるなら `codex-decision-doc`
- 人間向けの文章成果物なら `codex-writing`
- 方針を外から疑いたいなら strategic review 系
- 既存判断を維持・変更・保留するなら `codex-decision-integrity`
- X 固有の最新情報が必要なら `grok-x-research`
- 長期taskをfresh contextへ移すなら `codex-thread-handoff`

## Principle

すべてを AGENTS.md に書くと、常時コンテキストが重くなり、agent が重要度を判断しづらくなります。常時必要なルールだけを AGENTS.md に残し、作業ごとの詳しい期待は skill と reference に分けます。

実際の `~/.codex/skills` へ同期する方法は、利用環境に合わせて決めます。
