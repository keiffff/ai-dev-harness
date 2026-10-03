# Release compatibility

2026-10-03に公開リリースと既存の実行経路を照合した結果です。モデル名とCLIの版は別に確認し、この文書の版番号をインストール済み版や自動更新の指定として扱いません。

| 対象 | 公式の変更 | このハーネスでの対応 |
| --- | --- | --- |
| Claude Code 2.1.286 / 2.1.288 | bareの背景処理・MCP接続の制限、非対話応答のAPI timeout回復 | 単発wrapperにbareを追加し、safe mode、no-tools、1 turn、保存禁止を維持。外側のtimeoutとTERM/KILLによる終了をテストする。内部のAPI回復をwrapper側で重複実装しない |
| Codex 0.159 / 0.160 | 承認後もfilesystemの明示的denyを保持、writable root内の`.aws`を保護、開始中subagent環境と準備失敗を保持 | sandbox・approval・既存hookを維持する。許可オプションの追加やhookによるsandbox再実装は行わない。既存permission境界テストを実施し、実ランタイムのdenyとsubagent挙動は別途実環境の確認事項とする |
| OpenSpec 1.14.0 | apply JSONの各taskにsourcePathとlineを提供し、正確なcheckboxを確認 | skillでファイルと1-based lineを使用し、編集直前にcheckboxとtask textを再照合する。重複した説明文だけで選ばず、古い位置はinstructionsを取り直す。位置情報のないCLIでは実際のtask sourceを確認する |
| Antigravity CLI 1.2.12 | 日次quota・spend cap・prepaid credits枯渇を即時終了し、短期rate limitは再試行 | CLIが再試行を所有する。wrapperでquota分類や再試行を追加しない。失敗・timeoutで成果物を採用しないこと、成功したstructured outputを検証することを合成応答で確認する |

## Official sources

- [Claude Code changelog](https://code.claude.com/docs/en/changelog)と[CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Codex changelog](https://learn.chatgpt.com/docs/changelog)
- [OpenSpec 1.14.0](https://github.com/Fission-AI/OpenSpec/releases/tag/v1.14.0)
- [Antigravity changelog](https://antigravity.google/docs/changelog)のAntigravity CLI欄

## Verification

有料API、実際の認証情報、ユーザーのブラウザを使わずに検証します。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_release_compatibility.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_hooks_wrappers.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Claudeはmock CLIで既存の実行禁止フラグを確認し、合成processでtimeout時のTERMとKILLを確認します。Geminiは合成stream-jsonを使い、API失敗後にwrapperから2回目の呼び出しが起きないことを確認します。OpenSpecの位置照合はskillの手順を検査する範囲であり、CLIやagentの実編集を実行した証拠とは区別します。Codexの実sandbox、開始中環境のsubagent、各CLIの内部API再試行は、mockによるハーネステストでは証明しません。
