# Skills

AI agent に作業ごとの期待を渡すための Codex skills を管理します。

skill は、プロンプトを長くするための文章ではありません。main agent が毎回同じ判断で迷わないように、調査、実装、debug、review、文章作成、設計判断の手順と停止条件を分けて持たせるための部品です。

## Skill Map

| Skill | 使う場面 | 主な役割 | しないこと |
| --- | --- | --- | --- |
| `codex-loop-router` | 依頼の種類が実装、調査、review、文章、UI、OpenSpec などに分かれそうなとき | 最小 workflow を選び、必要な skill だけを読む | 実装や判断を router 自体で進めない |
| `codex-openspec-workflow` | OpenSpec の作成、適用、照合、archive | current CLI、artifact、互換性gate、spec照合を管理する | 通常実装や未承認proposalの実装には使わない |
| `codex-git-publish` | 明示依頼されたbranch作成・切替、commit、push、PR branch更新、submodule sync | wrapper経由のGit mutation手順を管理する | skill自体からmutation権限を推定しない |
| `codex-context-engineering` | repo の既存パターン、関連テスト、仕様、PR 状況を読む必要があるとき | 必要な evidence を集め、読みすぎを防ぐ | 無関係なファイルを広く読み込まない |
| `codex-incremental-implementation` | 複数ファイルの実装、OpenSpec tasks、refactor、feature work | 変更を検証可能な単位に分けて進める | 大きな speculative edit を一気に入れない |
| `codex-debugging-loop` | test、build、CI、API、browser、runtime log が失敗したとき | 再現、原因特定、修正、再確認の loop に戻す | 推測だけで修正しない |
| `codex-code-review` | diff review、完了前 review、AI 生成コードの確認 | bug、regression、missing test、構造、残リスクを見る | 変更内容の要約だけで終わらない |
| `codex-interface-review` | API、schema、state、persisted data、module boundary を変えるとき | I/F 契約、互換性、境界条件を確認する | 実装都合で契約変更を通さない |
| `codex-doubt-review` | 非自明な判断、移行、順序、idempotency、production risk があるとき | 採用案を敵対的に見直し、弱い前提を探す | 何でも否定するために使わない |
| `codex-decision-integrity` | 既存判断への反論、競合情報、方針転換が出たとき | 新情報を分類し、根拠のある維持・変更・保留を選ぶ | ユーザーの圧力やreviewerの断言だけで判断を変えない |
| `codex-frontend-ui` | UI 方針、HTML/mock/report、review visualization、既存デザインシステム準拠、visual QA | strategy/freeform/adherence/qa mode を選び、見た目とUI判断を制御する | canonical source を生成 HTML へ置き換えたり、full app browser 検証を勝手に始めたりしない |
| `codex-writing` | PR説明、README、チーム共有、release note、返信案などの文章成果物 | 読者、目的、事実、書かないことを整理して本文を書く | Claude に文章草稿を外注しない |
| `codex-decision-doc` | design doc、ADR/RFC、移行方針、判断の記録 | 判断、理由、代替案、互換性、残リスクを残す | 実装ファイル一覧や作業ログを書かない |
| `codex-cdk-design-review` | CDK、CloudFormation、stack、shared environment、cross-stack reference を触るとき | resource ownership、依存方向、物理名、quota、region を事前に見る | isolated 環境で通るだけの設計を安全扱いしない |
| `claude-strategic-review` | 方針、設計、移行、長期保守性を広く見たいとき | Claude Opus に sidecar review を依頼する | 最終判断や repo 編集を Claude に渡さない |
| `claude-fable-strategic-review` | Fable 5 を明示的に試す深い戦略レビュー | より重い long-horizon advisor として使う | 通常 review や実装には使わない |
| `gpt-sol-strategic-review` | Sol を明示的に使う高リスク・高価値の second opinion | OpenAI 側の強い advisor として使う | 普段の実装や文章生成に使わない |
| `chrome-devtools-on-demand` | network、console、performance、page inspection が必要な browser debug | 必要な時だけ DevTools MCP を起動する | 常時 browser automation を前提にしない |
| `codex-thread-time-audit` | Codex thread の作業時間や日次稼働を集計したいとき | thread turn から開始・終了時刻を抽出して集計する | thread-level created/updated だけで雑に集計しない |
| `codex-thread-handoff` | 長期化、compaction、工程境界、反復修正でfresh taskへの移行が有効なとき | 移行を一度だけ提案し、明示承認後にexact commitとcompactなcontinuation packetで新規taskへ引き継ぐ | 提案だけでtaskを作成したり、全履歴をforkしたりしない。source taskのarchiveは明示された設定・依頼がある場合のみ行う |
| `grok-x-research` | X の最新投稿、特定アカウントの発言、障害初動、実務者の反応を調べるとき | X 専用 scout としてURL、対立意見、citation、費用を返す | 通常Web調査、最終検証、設計判断、repo変更を任せない |

## How To Choose

まず `codex-loop-router` が入口になる。依頼内容が明らかな場合は、該当 skill を直接読む。

- 実装前に既存文脈が足りないなら `codex-context-engineering`
- 失敗が出ているなら `codex-debugging-loop`
- UI の見せ方や画面品質が関係するなら `codex-frontend-ui`
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
