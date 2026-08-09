# `permissions.json` (Cursor IDE)

Allowlist de tools MCP y comandos de terminal para el agente en el editor.

| Scope | Fichero |
|---|---|
| Usuario | `~/.cursor/permissions.json` |
| Proyecto | `.cursor/permissions.json` |

Si existen ambos, Cursor **concatena** los arrays de cada campo. Campos reales:

- `mcpAllowlist` — formato `server:tool` (glob: `server:*`, `*:tool`)
- `terminalAllowlist` — nombres de binario (`git`, `npm`, …)
- `autoRun` (opcional) — steering del clasificador Auto-review

Copia [`permissions.json.example`](./permissions.json.example) → `.cursor/permissions.json` y ajústalo.

> **No** uses un campo inventado `"allow"`. La CLI tiene un modelo distinto en `cli-config.json`
> (`permissions.allow` / `deny` con `Mcp(server:tool)`, `Shell(…)`).

**Run Mode** en el producto debe permitir que estos allowlists tengan efecto (según versión/UI).
Docs de producto + [`GUIA_TECNICA.md`](../../GUIA_TECNICA.md) §3.
