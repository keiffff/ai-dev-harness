# Wrappers

ラッパー（wrapper）は、共有状態を変更したり機密情報を露出したりする可能性があるツールに対して、狭く限定した実行経路です。

目的は、危険なコマンドをエージェントに慎重に判断させることではなく、不要な選択肢をなくすことです。Git、GitHub、AWS、Google Cloudの操作は、許可された動作だけを実装した小さな専用コマンドへ集約します。

## ハーネスにおける役割

ラッパーは、AI エージェントに求める実行境界をコマンドレベルで規定します。

- Gitは、明示的なパスのステージング、ユーザーが明示したプッシュ、force-with-leaseなどの運用に限定する
- GitHub CLI は読み取り専用（read-only）の参照に限定し、作成・更新・削除を直接実行させない
- AWS/Google Cloud は読み取り専用の許可リスト（allowlist）に限定し、シークレットやトークンの取得、および状態変更操作（mutation）を拒否する
- プロジェクト固有のプロファイル、ブランチ保護ルール、クラウドポリシーはローカル適応（Local Adaptation）として切り離す

## 含まれるサンプル（Included Examples）

- `bin/git-user-approved.example`: パス明示による `git add`、現在の HEAD または明示された開始点からのユーザー指示に基づくブランチ作成、ブランチ切り替え、単一アップストリームのマージに限定。暗黙的なプッシュや、amend / `commit -a` へのフォールバックは禁止。
- `bin/gh-readonly.example`: 読み取り専用の GitHub CLI コマンドおよび汎用 REST API の `GET` / `HEAD` リクエストのみを許可。変更を伴う HTTP メソッドや、HTTP メソッド上書きヘッダー（method-override headers）はブロック。
- `bin/aws-readonly.example`: 読み取り専用の AWS CLI コマンドに限定し、シークレットやトークンの取得、および広範なデータプレーンの読み取りはデフォルトでブロック。
- `bin/gcloud-readonly.example`: Google Cloud CLI の明示的な読み取り専用許可リストを適用し、シークレットやトークンへのアクセスはブロック。
- `bin/grok-x-research.example`: 日付範囲を制限した 1 回限りの xAI X Search リクエストを実行。Web Search は無効化し、正規化された引用注記の付与と明示的なコスト報告を実施。
- `bin/claude-strategic-review.example`: デフォルトのタイムアウトを 600 秒に設定した 1 回限りの Claude Opus レビューを実行。ハートビート診断を備え、ツール、プロジェクトのカスタマイズ、セッションの永続化、および追加のエージェントターンは無効化。
- `bin/claude-fable-strategic-review.example`: 共有 Keychain 認証情報ランチャーを使用する Fable レビュー実行用エントリポイント。
- `bin/claude-html-report.example`: デフォルトのタイムアウトを 600 秒に設定した、Claude Opus または明示的に要求された Fable による 1 回限りの HTML 全体生成。セーフモードを適用し、ツール、セッション永続化は無効化。完全なドキュメント検証、範囲を限定した秘匿化済み失敗診断、新規ファイル限定（new-file-only）の出力境界を適用。
- `bin/gemini-japanese-polish.example`: 隔離された Antigravity CLI ワークスペース経由で実行される、ステートレスな Gemini 3.8 Flash Medium による 1 回限りのドキュメント全体の日本語推敲。構造化出力、厳格なツール権限、サンドボックス環境、保護対象事実スパンの差分報告、最大 1 回の再生成を含む完全 HTML 検証、トークン使用量報告、Keychain 参照、新規ファイル限定の出力境界を適用。
- `bin/jev-artifact-review.example`: 完全な候補成果物および任意のベースライン成果物に対する、明示的な要件に基づく1回のJevレビュー。`--route-checks`を指定すると、意味、レイアウト、全体構成、操作経路の変更を判定し、必要な事実確認、部分・全体の目視確認、ブラウザ確認だけを返す。HTMLのscript、iframe、media、controlはローカルでも検出するため、APIが不通でも既存の実行時確認は失われない。確度の高い重大な違反には`review`を返すが、APIが不通であること自体は作業を止める理由にしない。
- `bin/jev-evidence-check.example`: 観測された障害の証拠が、特定の原因または対処法の主張を直接裏付けているかを評価する1回のJevチェック。裏付けのない主張には対処法を作らず、レビューシグナルを返す。
- `bin/keychain-env-exec.example`: macOS Keychain を用いた汎用的な認証情報注入スクリプト。コマンド引数や標準出力・標準エラー出力にシークレットを露出させることなく、単一のシークレットを子プロセスの環境変数に設定。

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
