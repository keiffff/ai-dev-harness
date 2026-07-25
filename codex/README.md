# Codex Configuration

Codex で AI agent を実務開発に組み込むための設定例と運用部品を置く場所です。

`~/.codex` は実行時の配布先です。このディレクトリは、プロジェクト固有の事情を外した正本として管理します。

## Role

Codex には、repo 文脈を読んで実装、検証、差分確認、最終判断を担う main agent の役割を持たせます。判断をすべてモデルの自律性に任せるのではなく、常時読むルール、必要なときだけ読む skill、外側で止める hook/wrapper を分けて、期待する振る舞いを実行環境に埋め込みます。

## Policy

- 常時読むルールは短く保つ
- 重い知識や作業手順は skill や reference に切り出す
- 文章、review、debug、OpenSpec、cloud/CDK などは用途別の skill に分ける
- subagent は bounded scout として使い、最終判断と Git 操作は main agent に残す
- project 固有事情は各 project repo に置き、このリポジトリには抽象化した運用だけを戻す

## Contents

- `AGENTS.generic.md`: 汎用化した Codex ルールの断片
- `config.example.toml`: approval、sandbox、model、tool 境界の設定例
- `skills/`: 作業手順、review、debug、writing、advisor 呼び出しを管理する skill 群
