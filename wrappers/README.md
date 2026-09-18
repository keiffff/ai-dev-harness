# Wrappers

Wrappers are narrow execution entrypoints for tools that can mutate shared state or expose sensitive data.

The goal is not to make the agent think harder about dangerous commands. The goal is to remove unnecessary choices from the agent. Git, GitHub, AWS, and Google Cloud operations should enter through small commands whose allowed behavior is already encoded.

## Role In The Harness

wrapper は、AI agent に期待する実行境界を command level で表現します。

- Git は explicit path staging、user-requested push、force-with-lease などの運用に寄せる
- GitHub CLI は read-only lookup に寄せ、作成・更新・削除は直接実行させない
- AWS/GCP は read-only allowlist に寄せ、secret/token 取得や mutation を拒否する
- project 固有の profile、branch protection、cloud account policy は local adaptation として分離する

## Included Examples

- `bin/git-user-approved.example`: explicit-path add, explicitly requested branch creation from current HEAD or an explicit start point, branch switching and single-upstream merge, no implicit push, no amend/commit-a fallback
- `bin/gh-readonly.example`: read-only GitHub CLI commands plus generic REST API `GET`/`HEAD`; mutation methods and HTTP method-override headers are blocked
- `bin/aws-readonly.example`: read-only AWS CLI commands with secret/token and broad data-plane reads blocked by default
- `bin/gcloud-readonly.example`: explicit read-only Google Cloud CLI allowlist with secret/token access blocked
- `bin/grok-x-research.example`: one bounded xAI X Search request with date limits, no Web Search, normalized citation annotations, and explicit cost reporting
- `bin/claude-strategic-review.example`: one bounded Claude Opus review with a 600-second default timeout, heartbeat diagnostics, and tools, project customizations, session persistence, and extra agent turns disabled
- `bin/claude-html-report.example`: one bounded Claude Opus or explicitly requested Fable whole-HTML composition with a 600-second default timeout, safe mode, no tools, no session persistence, complete-document validation, bounded redacted failure diagnostics, and a new-file-only output boundary
- `bin/gemini-japanese-polish.example`: one stateless Gemini 3.8 Flash whole-document Japanese composition run with low thinking, structured output, no tools, protected fact-span difference reporting, complete-HTML validation with one bounded regeneration, token usage reporting, Keychain lookup, and a new-file-only output boundary

## Local Adaptation

Copy examples to a local bin directory and adapt:

- local secret manager lookup
- allowed read operations
- cloud profiles and accounts
- repository-specific history protection
- organization-specific approval requirements
- xAI API key lookup from the local environment or macOS Keychain
- Gemini API key lookup from the `GEMINI_JAPANESE_POLISH_API_KEY` macOS Keychain item
- an absolute `CLAUDE_STRATEGIC_CLI` path so escalated execution cannot select a different Claude CLI from `PATH`

Keep project-specific rules out of this repository unless they are rewritten as reusable patterns.
