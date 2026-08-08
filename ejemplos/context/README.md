# Context window — el recurso que gobierna todo (Cursor)

El context window sigue siendo **el recurso más importante**: rules, MCP, subagents/Task y skills
existen para no desperdiciarlo. Material paralelo a la sección **Contexto** del curso Claude Code.

## 1. Anatomía: qué llena el contexto en Cursor

Antes de que escribas una palabra, la sesión ya carga (órdenes de magnitud; varían por modelo/UI):

| Bloque | Notas |
|---|---|
| System / agent prompt de Cursor | Oculto; siempre primero |
| Rules `alwaysApply` + `AGENTS.md` | **Tú lo controlas** — por eso el patrón de dos niveles |
| Memories (si las hay) | Distinto de la auto-memory `MEMORY.md` de Claude Code |
| Info de entorno / workspace | SO, git, ficheros abiertos |
| Tools MCP | Schemas de tools habilitadas; desactiva servers que no uses |
| Skills relevantes | Cursor puede inyectar skills según `description` |

Después, cada turno suma: conversación, ficheros leídos, output de comandos, resultados de tools.
Un contexto lleno de ruido produce peores decisiones **antes** de llegar al límite duro.

## 2. Controles — qué hay y qué no

### Disponible / práctico en Cursor

- **Plan mode** — explorar y diseñar sin ensuciar la sesión de implementación.
- **Task / subagents** — side-quests con contexto aislado; solo vuelve el resumen ([`../subagents/`](../subagents/)).
- **Rules lean + punteros** — no pegues `STATUS.md` entero en una rule always-on.
- **MCP con moderación** — cada server suma tools; apaga lo que no uses ([`../mcp/`](../mcp/)).
- **`/summarize`** (alias `/compress`) — resumir y liberar contexto en CLI / Agent.
- **`/rewind`** — volver a un mensaje previo (CLI; según config).
- **Nueva chat / nueva invocación de `agent`** — cuando la tarea no está relacionada.

### No hay equivalente 1:1 a Claude Code

| Claude Code | Cursor |
|---|---|
| `/context` (desglose por bloque) | Anillo de contexto en la UI del editor; no el mismo comando |
| `/compact [foco]` / auto-compact | `/summarize` + resumen automático del producto — **no** asumas parity con `/compact` |
| Checkpoints de edición del agente | Usa **git** como fuente de verdad de rollback |
| `@import` en `CLAUDE.md` | Ver [`AGENTS.pointers-example.md`](./AGENTS.pointers-example.md) — solo punteros lazy |

## 3. Buenas prácticas (las que aplicamos de verdad)

1. **`AGENTS.md` + rules mínimos** — si puedes borrarlo sin que el agente se equivoque, bórralo. Patrón de dos niveles: [`../agents-md/`](../agents-md/).
2. **Punteros, no copias** — detalle en `data/changes/` on-demand.
3. **MCP con moderación** — menos tools = menos ruido (y a menudo mejor comportamiento).
4. **Task para investigar** — la exploración sucia no vive en el hilo principal.
5. **Plan → Agent** — no implementes en la misma sesión larga y ruidosa en la que exploraste sin necesidad.
6. **Lecturas con puntería** — CodeGraph primero ([`../codegraph/`](../codegraph/)): 1 llamada con señal > 10 ficheros enteros.
7. **Mide con evidencia** — si la sesión “se pone tonta”, empieza chat nuevo o recorta rules; no acumules transcript infinito.

**Conexión con la Parte 2:** la prevalencia CodeGraph → Serena → grep es una política de gestión de contexto.

Pack: [`../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md`](../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md).
