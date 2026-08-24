# Hooks

Codex の誤操作を早い段階で止めるための local safety policy を管理します。

hook は sandbox や approval を置き換えるものではありません。役割は、agent が raw CLI、secret 表示、破壊的操作、危険な shell 構文に進もうとしたときに、会話と実行の境界で止めることです。

## Role In The Harness

AI agent に期待する振る舞いは、プロンプトだけでは固定できません。hook は、その期待を実行前の検査として置くための層です。

- Git の commit/push は approved wrapper に寄せる
- AWS/GCP/GitHub CLI は raw command ではなく read-only wrapper に寄せる
- `.env` や credential file の表示を止める
- `rm -rf`、`git clean`、recursive chmod/chown などの破壊的操作を止める
- shell interpreter、command substitution、process substitution、multiline shell、shell grouping、xargs、sudo を保守的に拒否する

## Japanese Output Review

`japanese-output-review.py` は、日本語の文章を最終回答として送る直前に一度だけ止め、同じ Codex に推敲させます。単語の禁止だけではなく、読者、目的、媒体、情報の順序、意味、余計な補足、英語を直訳したような圧縮表現まで見直すための Stop hook です。

この hook は、最初の日本語回答を原則として一度止めます。再開後は `stop_hook_active` を見て必ず通すため、推敲の繰り返しにはなりません。コードだけの回答、JSON、CSV、英語だけの回答は対象外です。ユーザーが原文どおりの出力を求めた場合も対象外にします。

`UserPromptSubmit` では、回答を変えてはいけない依頼かどうかと、明示的な除外指定だけを task ごとに保存します。文章ルールの全文を毎回追加しません。保存先は `~/.codex/hook-state/japanese-output-review/` です。test などで保存先を分ける場合は `CODEX_JAPANESE_OUTPUT_STATE_DIR` を指定できます。保存するのは turn ID と真偽値だけで、prompt 本文は保存しません。

一時的に推敲を止める必要がある場合は、ユーザーの prompt に `[ja-output-bypass]` を含めます。assistant の回答に同じ文字列があっても除外されません。

hook が単語を検出した場合は推敲時に注意を促しますが、単語だけを理由に回答を拒否し続けることはありません。たとえば `契約` は API の仕様を指す場合には必要ですが、英語の contract を文脈なしに置き換えただけなら、具体的な挙動へ書き直します。読者に定着した用語かどうかは Codex が文脈から判断します。

### Japanese Output Activation Check

設定へ `UserPromptSubmit` と `Stop` の両方を追加した後、Codex を再起動し、CLI の `/hooks` で2つの hook を確認して trust します。短い日本語の質問を試し、最終回答が1回だけ推敲されることも確認します。unit testだけでは Codex lifecycle への接続、trust、実行を確認したことにはなりません。

## Context Handoff Reminder

`compaction-handoff-reminder.py` は、同じ task で2回目の compaction が起きたときだけ、次の安全な区切りで `codex-thread-handoff` を使って移行要否を確認するよう Codex へ context を渡します。

hook 自体は task の作成、fork、archive を行いません。実行中の command、編集、test、approval、未解決の失敗も中断させません。提案と task 操作は、引き続き `codex-thread-handoff` の制約とユーザーの明示承認に従います。

compaction 回数は session ごとに `~/.codex/hook-state/compaction-handoff/` へ保存します。test などで保存先を分離する場合は `CODEX_HANDOFF_STATE_DIR` を指定できます。入力を解釈できない場合は、作業を妨げないよう何も通知せず終了します。

### Activation Check

command hook は、設定へ追加しただけでは実行されません。追加または command 変更後は Codex を再起動し、CLI の `/hooks` で `SessionStart` の compact hookを確認して trust します。

導入完了は次の両方で確認します。

- `/hooks` で対象hookが `Active` になり、`Review` が0である
- 実際の1回目のcompaction後に `~/.codex/hook-state/compaction-handoff/` へstateファイルが作られる

スクリプトへの模擬入力やunit testだけでは、Codex lifecycleへの接続、trust、実行を確認したことにはなりません。

## Parse Failure Policy

Codex hooks are a policy reminder and local guardrail, not a complete security boundary.

Execution policy hooks fail open only for empty input. Non-empty malformed JSON is rejected so hook API drift does not silently disable the policy. Japanese output review is not an execution safety boundary, so invalid input or unavailable state fails open instead of preventing the answer indefinitely.

These hooks are intentionally conservative because they are not full shell parsers. Keep sandbox and approval settings as the real execution boundary.
