---
name: chrome-devtools-on-demand
description: Use isolated Chrome DevTools MCP for network, console, performance, or page debugging while keeping its registration enabled across investigations.
---

# Chrome DevTools On Demand

Use this skill when DevTools-level browser data is needed, especially Network, Console, Performance, page targets, screenshots from Chrome DevTools MCP, or debugging that the in-app browser cannot provide.

## Default Policy

- In-app browser use with an explicit `iab` selector needs no additional approval. Use it for ordinary browser work. This skill starts an external Chrome instance, so use it only when the user explicitly requests that browser and supplies the current-turn `browser-control: allow` under AGENTS.md; do not make ordinary in-app work depend on that permission.
- Keep `chrome@openai-bundled` disabled unless the user explicitly asks to control their logged-in main Chrome.
- Prefer `chrome-devtools-mcp` with `--isolated=true` so debugging uses a separate browser/profile.
- Do not use `--autoConnect` for the user's main Chrome unless explicitly requested.
- Keep the DevTools MCP registration enabled across investigations. Registration does not grant browser-control permission; actual browser use remains task-scoped.

## Workflow

1. Use the available DevTools MCP tools when the task needs them and browser permission is present. Do not rewrite config or request a restart for routine use.
2. If tools are missing, run `scripts/codex-devtools status`. Run `on` only if registration is disabled and enabling it is in scope. An enabled config does not prove that the current thread has loaded the tools.
3. For missing tools, inspect the available MCP connection/startup status and use the host's supported configuration reload if exposed. Do not launch a separate app-server to refresh the current app. Request a restart only when a concrete configuration or connection problem requires it and no supported in-session recovery is available; do not issue a speculative restart instruction.
4. Perform the DevTools investigation in the isolated browser/profile.
5. When done, close only the investigation's own tabs or isolated browser through the available browser tools. Leave MCP registration enabled; do not run `off` as routine cleanup or close the user's other browsers or tabs.

## Decision Rules

Use DevTools MCP for:

- Network request/response inspection that the in-app browser cannot expose.
- Console logs, performance traces, or page target inspection.
- Browser behavior that must be verified in Chrome DevTools.

Do not use DevTools MCP for:

- Normal page navigation, screenshots, or simple UI checks where the in-app browser is enough.
- Tasks that require the user's logged-in main Chrome unless the user explicitly asks for main Chrome control.
- Background browsing unrelated to the current debugging task.

## Script

Use the bundled script from the skill directory:

```bash
./scripts/codex-devtools status
./scripts/codex-devtools on
./scripts/codex-devtools off
```

Use `status` for diagnosis, `on` for setup when disabled, and `off` only when the user requests disabling the registration. The script edits `~/.codex/config.toml` and creates a timestamped backup before changes. It only manages:

- `[mcp_servers.chrome-devtools] enabled`
- `BROWSER_USE_AVAILABLE_BACKENDS`
- `[plugins."chrome@openai-bundled"] enabled`

Expected steady state (configuration state, not permission to use a browser):

- `chrome-devtools` MCP enabled
- browser backends set to `chrome,iab`; ordinary browser work still selects `iab`
- `chrome@openai-bundled` disabled
- `browser@openai-bundled` left unchanged
