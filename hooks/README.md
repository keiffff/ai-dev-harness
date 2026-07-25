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

## Parse Failure Policy

Codex hooks are a policy reminder and local guardrail, not a complete security boundary.

They fail open only for empty input. Non-empty malformed JSON is rejected so hook API drift does not silently disable the policy.

These hooks are intentionally conservative because they are not full shell parsers. Keep sandbox and approval settings as the real execution boundary.
