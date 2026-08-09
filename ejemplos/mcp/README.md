# MCP — Model Context Protocol (Cursor)

**MCP** conecta Cursor a fuentes de datos y herramientas externas. El servidor expone *tools* que el
agente puede llamar (CodeGraph, Serena, Playwright, Context7, tu propio tooling…).

## Dónde vive la config en Cursor

| Scope | Fichero típico | Alcance |
|---|---|---|
| **project** | `.cursor/mcp.json` | Compartido con el equipo (versiona con cuidado; sin secretos). Ver [`mcp.json.example`](./mcp.json.example). |
| **user / global** | `~/.cursor/mcp.json` (también Settings → MCP) | Todos tus proyectos en esa máquina. |

> Claude Code usaba `.mcp.json` en la raíz, `settings.local.json` y `~/.claude.json`.
> En Cursor el sitio canónico de proyecto es **`.cursor/mcp.json`**.

## Añadir un server

1. Edita `.cursor/mcp.json` (o `~/.cursor/mcp.json` / UI de Cursor → MCP).
2. **Recarga la ventana** de Cursor (recomendado; a veces hace falta reiniciar del todo).
3. Comprueba en la UI de MCP que el server está verde y lista tools.
4. Opcional CLI: `agent mcp list` · `agent mcp enable <name>` · `agent mcp disable <name>`.

No hay `agent mcp add` / `claude mcp add`. El equivalente es editar el JSON (o la UI) + reload.

Interpolación soportada: `${env:NAME}`, `${workspaceFolder}`, `${userHome}`, `${pathSeparator}`.

Ejemplo stdio (Serena):

```json
"serena": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"]
}
```

Ejemplo HTTP (Context7):

```json
"context7": {
  "url": "https://mcp.context7.com/mcp"
}
```

Ejemplo secreto (opcional — demo):

```json
"supabase": {
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server-supabase@latest"],
  "env": { "SUPABASE_ACCESS_TOKEN": "${env:SUPABASE_ACCESS_TOKEN}" }
}
```

## Buenas prácticas

- **Secretos por `${env:…}`**, nunca hardcodeados en JSON versionado (ver `supabase` en el ejemplo).
- **Permisos:** Cursor usa `permissions.json` con `mcpAllowlist` / `terminalAllowlist`
  (`server:tool`), no el allowlist `mcp__server__tool` de Claude. Compensa además con:
  - rules que digan *qué* tool usar y cuándo,
  - hooks `beforeMCPExecution` si necesitas vetar llamadas,
  - approvals de la UI según tu Run Mode.
- **Elige el scope correcto:** lo del equipo → `.cursor/mcp.json`; lo personal → `~/.cursor/mcp.json`.
- Tras cambiar `--path` de CodeGraph: reload + verifica que `codegraph_explore` responde.

## Servers del día a día (metodología)

`serena` · `context7` · `playwright` · `codegraph` (ver [`../codegraph/`](../codegraph/)) · opcional `supabase`.

Pack listo: [`../../docs/ai-agents-code-methodology/cursor/mcp.json.example`](../../docs/ai-agents-code-methodology/cursor/mcp.json.example).
