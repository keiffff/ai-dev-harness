---
name: chrome-devtools-on-demand
description: Enable isolated Chrome DevTools MCP only for network, console, performance, or page debugging, then disable it when finished.
---

# Chrome DevTools On Demand

Use this skill when DevTools-level browser data is needed, especially Network, Console, Performance, page targets, screenshots from Chrome DevTools MCP, or debugging that the in-app browser cannot provide.

## Default Policy

- Keep normal browsing on the in-app Browser plugin.
- Keep `chrome@openai-bundled` disabled unless the user explicitly asks to control their logged-in main Chrome.
- Prefer `chrome-devtools-mcp` with `--isolated=true` so debugging uses a separate browser/profile.
- Do not use `--autoConnect` for the user's main Chrome unless explicitly requested.
- Treat DevTools MCP as a temporary capability: enable before DevTools work, disable after DevTools work.

## Workflow

1. Run `scripts/codex-devtools status` to inspect the current config state.
2. If DevTools MCP is disabled and the current task truly needs it, run `scripts/codex-devtools on`.
3. Tell the user that Codex may need a thread/app restart before the MCP tools are available in this session.
4. Perform the DevTools investigation after the MCP tools are available.
5. When done, run `scripts/codex-devtools off` unless the user explicitly asks to keep it enabled.
6. Run `scripts/codex-devtools status` again and report the final state.

## Decision Rules

Use DevTools MCP for:

- Network request/response inspection that the in-app browser cannot expose.
- Console logs, performance traces, or page target inspection.
- Browser behavior that must be verified in Chrome DevTools.

Do not enable DevTools MCP for:

- Normal page navigation, screenshots, or simple UI checks where the in-app browser is enough.
- Tasks that require the user's logged-in main Chrome unless the user explicitly asks for main Chrome control.
- Background convenience; enabling must be tied to a current debugging need.

## Script

Use the bundled script from the skill directory:

```bash
./scripts/codex-devtools status
./scripts/codex-devtools on
./scripts/codex-devtools off
```

The script edits `~/.codex/config.toml` and creates a timestamped backup before changes. It only manages:

- `[mcp_servers.chrome-devtools] enabled`
- `BROWSER_USE_AVAILABLE_BACKENDS`
- `[plugins."chrome@openai-bundled"] enabled`

Expected steady state after `off`:

- `chrome-devtools` MCP disabled
- browser backends set to `iab`
- `chrome@openai-bundled` disabled
- `browser@openai-bundled` left unchanged
