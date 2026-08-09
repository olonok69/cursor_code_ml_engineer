# AGENTS.md + rules — el patrón de "contexto de dos niveles" en Cursor

En Claude Code el fichero always-loaded es `CLAUDE.md`. En Cursor el rol lo cubren:

1. **`AGENTS.md`** en la raíz (orientación corta, punteros).
2. **`.cursor/rules/*.mdc`** con `alwaysApply: true` (gates y prevalencia de tools).

El error típico es el mismo: meter el historial entero en lo always-loaded hasta que cada turno paga un impuesto enorme.

Los ejemplos de esta carpeta muestran el patrón de producción (sanitizado):

### Nivel 1 — siempre cargado (pequeño)

[`AGENTS.md`](./AGENTS.md) + regla lean de ejemplo
[`./.cursor/rules/00-lean-memory.mdc`](./.cursor/rules/00-lean-memory.mdc)
(pack completo en
[`../../docs/ai-agents-code-methodology/cursor/rules/`](../../docs/ai-agents-code-methodology/cursor/rules/)).

Orientación mínima: qué es el proyecto, mapa de repos y permisos, comandos, convenciones y **punteros
de una línea** a todo lo demás.

### Nivel 2 — bajo demanda (todo el detalle)

Ficheros bajo `data/changes/` que el agente **lee solo cuando el ticket lo pide**:

| Fichero | Contenido |
|---|---|
| `STATUS.md` | Ledger vivo: estado por ticket (rama/commit/PR/nº de tests). |
| `PLAYBOOK.md` | Lecciones de debugging codificadas. |
| `SHARP_EDGES.md` | Invariantes "no tocar" con el ticket que las estableció. |
| `CONVENTIONS.md` | Política de confidencialidad / sanitización. |
| `<TICKET>/<TICKET>.md` | Ledgers por-ticket, cada uno autocontenido. |

### La disciplina write-once

> Cada registro se escribe en **exactamente un** ledger canónico. `AGENTS.md` / rules llevan un
> **puntero**, nunca una copia. En el proyecto Claude Code original el recorte fue **~73%** sin perder
> información — el mismo objetivo aplica aquí.

### Qué es distinto respecto a Claude Code

| Claude Code | Cursor |
|---|---|
| `CLAUDE.md` (+ jerarquía `~/.claude`, subcarpetas, `CLAUDE.local.md`) | `AGENTS.md` + `.cursor/rules/` (+ rules de usuario en settings) |
| `@ruta` import eager en CLAUDE.md | **No hay `@import` equivalente** en AGENTS.md; usa punteros + Read, o rules cortas |
| Auto-memory `MEMORY.md` | Memories de Cursor (otro producto); no copies el modelo Claude a ciegas |
| Un solo fichero "oficial" de orientación | Puedes partir gates en varios `.mdc` (recomendado: 1 concern / rule, &lt;50 líneas) |

Ver también: [`../context/`](../context/) y el pack [`CURSOR_ADAPTATION.md`](../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md).
