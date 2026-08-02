# CodeGraph — inteligencia de código local (vía MCP en Cursor)

Herramienta *local-first* que indexa tu código con **tree-sitter** en un **grafo SQLite** y lo
expone al agente como servidor MCP. En el curso Claude Code se instalaba con
`codegraph install --target=claude`. En Cursor configuras el server en **`.cursor/mcp.json`**.

Repo: https://github.com/colbymchenry/codegraph · Docs: https://colbymchenry.github.io/codegraph/

## Qué indexa (determinista, del AST — no resumido por un LLM)

- **Símbolos:** funciones, clases, métodos, tipos, rutas, componentes.
- **Aristas:** llamadas, imports, herencia, referencias, relaciones de framework.
- **Ficheros:** estructura + búsqueda full-text.

Todo vive en `.codegraph/` (SQLite local). **Sin servicios externos ni API keys.** Añade `.codegraph/`
al `.gitignore`.

## CLI (igual)

```bash
codegraph init        # crea el índice .codegraph/ y lo construye
codegraph sync        # re-indexa incremental
codegraph watch       # re-indexa en vivo (poco fiable en WSL /mnt)
codegraph explore "<símbolo o pregunta>"
codegraph serve --path <repo> --mcp
codegraph status
```

## Conectar a Cursor

En `.cursor/mcp.json`:

```json
"codegraph": {
  "command": "codegraph",
  "args": ["serve", "--path", "/absolute/path/to/repo", "--mcp"]
}
```

1. Sustituye el path por tu repo (el server **no** tiene proyecto por defecto útil si el workspace root
   no tiene `.codegraph/`).
2. Recarga Cursor.
3. Llama `codegraph_explore` desde el agente.

> `codegraph install --target=claude` **no** configura Cursor. Usa el JSON de arriba o el bootstrap
> [`bootstrap-cursor-repo.ps1`](../../docs/ai-agents-code-methodology/scripts/bootstrap-cursor-repo.ps1.txt).

Trata la fuente que imprime `codegraph_explore` como **ya leída** — no re-abras ese fichero.

## CodeGraph vs. Serena vs. grep

| Pregunta | Herramienta |
|---|---|
| Survey: fuente + callers + blast radius + ¿testeado? | **CodeGraph** `codegraph_explore` |
| Chequeo preciso antes de rename/borrado | **Serena** `find_referencing_symbols` |
| Overview / cuerpo de un símbolo | Serena o la fuente que ya dio `explore` |
| Literal / string | grep |

En la metodología (etapa 4): CodeGraph primero, Serena antes de tocar. Ver
[`../metodologia/EJEMPLO_REAL.md`](../metodologia/EJEMPLO_REAL.md).

## Blast radius

Onda expansiva de tocar un símbolo: callers transitivos + flags de cobertura. El blast de CodeGraph es
*plano* (mezcla homónimos); el veredicto fino pre-rename lo da Serena.
