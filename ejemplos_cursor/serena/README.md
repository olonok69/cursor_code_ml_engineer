# Serena — navegación semántica de código (MCP en Cursor)

[Serena](https://github.com/oraios/serena) da al agente entendimiento simbólico vía LSP.
Misma herramienta que en Claude Code; cambia solo **cómo se registra el server**.

## Instalación en Cursor

Añade a `.cursor/mcp.json` (ver [`../mcp/mcp.json.example`](../mcp/mcp.json.example)):

```json
"serena": {
  "command": "uvx",
  "args": [
    "--from",
    "git+https://github.com/oraios/serena",
    "serena",
    "start-mcp-server"
  ]
}
```

Recarga Cursor. Comprueba tools en la UI MCP.

> No uses `claude mcp add serena …` — eso escribe config de Claude Code.

## Tools que importan

| Tool | Qué hace | Cuándo |
|---|---|---|
| `find_symbol` | Localiza símbolo (`body=true` → cuerpo) | Un método de un fichero de 5k líneas |
| `get_symbols_overview` | Esqueleto del fichero | Primer vistazo |
| `find_referencing_symbols` | Refs desambiguadas por clase | **Obligatorio antes de renombrar/borrar** |
| `search_for_pattern` | Patrón con contexto simbólico | Literal + símbolo contenedor |
| `activate_project` | Cambiar proyecto indexado | Multi-repo |

## Prevalencia (igual que en Claude Code)

1. CodeGraph `codegraph_explore` primero.
2. Serena `find_referencing_symbols` antes de rename/delete.
3. grep/Read solo para literales.

Plantilla de scout: [`../subagents/prompts/refactor-scout.md`](../subagents/prompts/refactor-scout.md).

## Permisos

Claude Code usaba allowlist `mcp__serena__…` en `settings.local.json`.
Cursor: approvals de la UI + rules de prevalencia + opcional `beforeMCPExecution` hook.
No hay copia literal del JSON de allow de Claude.
