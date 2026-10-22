# Wrappers

ラッパー（wrapper）は、共有状態を変更したり機密情報を露出したりする可能性があるツールに対して、狭く限定した実行経路です。

目的は、危険なコマンドをエージェントに慎重に判断させることではなく、不要な選択肢をなくすことです。Git、GitHub、AWS、Google Cloudの操作は、許可された動作だけを実装した小さな専用コマンドへ集約します。

## ハーネスにおける役割

ラッパーは、AI エージェントに求める実行境界をコマンドレベルで規定します。

- Gitは、明示的なパスのステージング、ユーザーが明示したプッシュ、force-with-leaseなどの運用に限定する
- GitHubの参照は`gh-readonly`、明示依頼されたPR・issue操作は`gh-user-approved`へ分ける。PR・issue操作はサブコマンドやオプションの許可リストではなく、依頼された対象と操作に限定する
- AWS/Google Cloud は読み取り専用の許可リスト（allowlist）に限定し、シークレットやトークンの取得、および状態変更操作（mutation）を拒否する
- プロジェクト固有のプロファイル、ブランチ保護ルール、クラウドポリシーはローカル適応（Local Adaptation）として切り離す

## 含まれるサンプル（Included Examples）

- `bin/git-user-approved.example`: パス明示による `git add`、現在の HEAD または明示された開始点からのユーザー指示に基づくブランチ作成、ブランチ切り替え、単一アップストリームのマージに限定。暗黙的なプッシュや、amend / `commit -a` へのフォールバックは禁止。
- `bin/gh-readonly.example`: 読み取り専用の GitHub CLI コマンドおよび汎用 REST API の `GET` / `HEAD` リクエストのみを許可。変更を伴う HTTP メソッドや、HTTP メソッド上書きヘッダー（method-override headers）はブロック。
- `bin/gh-user-approved.example`: 最新の明示依頼を確認したCodexが、`--confirm-user-requested pr|issue <command>`でPR・issue操作を実行する経路。`gh pr`・`gh issue`のサブコマンドとオプションはそのまま渡す。汎用API、workflow、認証操作などは対象外。フラグ自体はユーザーの依頼を検証せず、依頼との対応は共通AGENTSとskillで判断する。
- `bin/aws-readonly.example`: 読み取り専用の AWS CLI コマンドに限定する。DynamoDBの取得・一括取得・query・scan・トランザクション取得は許可し、書き込み・削除・構成変更、読み書き兼用API、secret・tokenの取得や他の広範なデータプレーンの読み取りはブロック。
- `bin/gcloud-readonly.example`: Google Cloud CLI の明示的な読み取り専用許可リストを適用し、シークレットやトークンへのアクセスはブロック。
- `bin/grok-x-research.example`: 日付範囲を制限した 1 回限りの xAI X Search リクエストを実行。Web Search は無効化し、正規化された引用注記の付与と明示的なコスト報告を実施。
- `bin/claude-strategic-review.example`: デフォルトのタイムアウトを 600 秒に設定した 1 回限りの Claude Opus レビューを実行。ハートビート診断を備え、ツール、プロジェクトのカスタマイズ、セッションの永続化、および追加のエージェントターンは無効化。
- `bin/claude-fable-strategic-review.example`: 共有 Keychain 認証情報ランチャーを使用する Fable レビュー実行用エントリポイント。
- `bin/claude-html-report.example`: デフォルトのタイムアウトを 600 秒に設定した、Claude Opus または明示的に要求された Fable による HTML 新規作成と既存ファイルの直接編集。`--output-file` はツールなしで新規ファイルを作成し、`--edit-file` は指定ファイルへの Read/Edit だけを許可して局所修正する。空の作業ディレクトリと `dontAsk` で対象外操作を拒否し、全文返答で上書きしない。両モードでセーフモード、セッション永続化の無効化、完全なドキュメント検証、秘匿化済み失敗診断を適用。編集時は `--trace-file` に実差分とツール操作を保存できる。
- `bin/gemini-japanese-polish.example`: 隔離された Antigravity CLI ワークスペース経由で実行される、ステートレスな Gemini 3.8 Flash Medium による 1 回限りのドキュメント全体の日本語推敲。構造化出力、厳格なツール権限、サンドボックス環境、保護対象事実スパンの差分報告、最大 1 回の再生成を含む完全 HTML 検証、トークン使用量報告、Keychain 参照、新規ファイル限定の出力境界を適用。
- `bin/jev-artifact-review.example`: `@jev-kit/cli`のsemantic diffで成果物を検査する。`--request-file`の元依頼を`--requirements-file`の作成者メモと分けて扱い、作成者の解釈を許可へ昇格させない。`review`時だけ既存のtool-free Claude wrapperを1回呼び、元依頼・baselineと候補の引用を含む`concrete_review.findings`を返す。引用は入力と照合するが、その意味の妥当性と採否は呼出し元が判断する。Claude実行失敗は`concrete_review.status=unavailable`とし、再試行・別経路への切替や自動passは行わない。`--request-file`なしの既存呼出しは従来のscore出力を保つ。`--route-checks`は事実・目視・ブラウザ・操作確認を振り分け、HTMLのscript/iframe/media/control由来の実行時確認はJev不通でも保持する。点数や引用は画像比較・実操作の成功証拠ではない。
- `bin/jev-evidence-check.example`: `@jev-kit/cli`のevidence checkを使い、観測された障害の証拠が特定の原因または対処法の主張を直接裏付けているかを評価する。ハーネス側は採用基準を持ち、Jevへの送信、応答検証、単一試行は`jev-kit-evidence-check`へ委ねる。
- `bin/keychain-env-exec.example`: macOS Keychain を用いた汎用的な認証情報注入スクリプト。コマンド引数や標準出力・標準エラー出力にシークレットを露出させることなく、単一のシークレットを子プロセスの環境変数に設定。

## CLIの互換性

OAuth認証を使うClaudeのツールなし単発wrapper（HTMLの新規作成を含む）は`--safe-mode --tools "" --max-turns 1 --no-session-persistence`を併用します。HTMLの直接編集では Read/Edit と対象ファイルの絶対パスだけを許可し、空の作業ディレクトリと `dontAsk` を使います。複数のツール操作が必要なため、直接編集に `--max-turns 1` は付けません。OAuthを無効にする`--bare`は付けません。Python wrapperはsafe modeの対応を確認し、既存の外側のtimeoutとプロセスグループ終了処理を維持します。

Antigravityの一時的なrate limitの再試行はCLIに任せます。wrapperは失敗したCLI呼び出しを再実行せず、既存の構造化出力検証と秘匿化した診断を維持します。成功応答のHTMLが未完了の場合に限る1回の再生成は、API失敗の再試行とは別です。

公開更新の採用理由と検証範囲は[release compatibility](../docs/release-compatibility.md)を参照してください。

## ローカル環境への適応（Local Adaptation）

サンプルファイルをローカルの `bin` ディレクトリにコピーし、以下の項目を環境に合わせて調整してください。

- ローカルのシークレットマネージャー参照処理
- 許可する読み取り操作の定義
- 使用するクラウドプロファイルおよびアカウント
- リポジトリ固有の履歴保護設定
- 組織固有の承認要件
- 共有 Keychain ランチャー経由で注入する前の、xAI API キーのサービス／アカウント選択
- 共有ランチャーを経由した、Keychain 項目 `GEMINI_JAPANESE_POLISH_API_KEY` からの Gemini API キー注入
- 権限昇格を伴う実行時に `PATH` 上の別の Claude CLI が選択されないようにするための、`CLAUDE_STRATEGIC_CLI` の絶対パス指定

再利用可能なパターンとして再設計されている場合を除き、プロジェクト固有のルールを本リポジトリに直接持ち込まないでください。
