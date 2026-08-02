# Context window — el recurso que gobierna todo

El context window es **el recurso más importante que gestionas** en Claude Code: todo lo demás (CLAUDE.md,
MCP, subagentes, caching) son técnicas para no desperdiciarlo. Material de la sección **Contexto** de la
Parte 1 (ver [`GUIA_PRESENTACION.md`](../../GUIA_PRESENTACION.md)).

## 1. Anatomía: qué llena el contexto

Antes de que escribas una palabra, la sesión ya carga (~cifras de la doc oficial):

| Bloque | Coste aproximado |
|---|---|
| System prompt de Claude Code | ~4.200 tokens (oculto, siempre primero) |
| Auto-memory (`MEMORY.md`) | primeras 200 líneas / 25 KB, ~680 tokens |
| Info de entorno (SO, shell, git status) | ~280 tokens |
| Tools MCP (modo deferred, por defecto) | ~120 tokens de índice; el schema completo se carga al usarla |
| Tu `CLAUDE.md` (jerarquía completa) | lo que tú decidas — **por eso el patrón de dos niveles** |

Después, cada turno suma: conversación, ficheros leídos, output de comandos, resultados de tools. Los
modelos actuales dan 200K tokens de ventana (1M en beta vía API) — y el rendimiento **degrada antes de
llenarla**: un contexto lleno de ruido produce peores decisiones.

## 2. Los comandos

```text
/context                      # visualiza el uso: desglose por bloque, dónde se van los tokens
/compact [instrucciones]      # compacta YA, guiando qué debe sobrevivir:
/compact céntrate en los cambios de la API y la lista de ficheros modificados
/clear                        # reset total entre tareas NO relacionadas
/rewind   (o Esc+Esc)         # volver a un checkpoint: conversación, código, o ambos;
                              # también "summarize from here" para condensar un tramo
```

- **Auto-compact:** al acercarte al límite, Claude Code compacta solo, resumiendo lo importante. Mejor
  anticiparse con un `/compact <foco>` manual: la compactación es **lossy** y tú sabes qué importa.
- **`/clear` vs `/compact`:** tarea nueva no relacionada → `/clear` (contexto fresco > resumen de ruido).
  Misma tarea, sesión larga → `/compact` con instrucciones.
- **Checkpoints:** `/rewind` restaura ediciones de Claude, **no** cambios hechos por Bash o externos
  (no sustituye a git).

## 3. Buenas prácticas (las que aplicamos de verdad)

1. **CLAUDE.md mínimo** — regla de oro de la doc: *si puedes borrarlo sin que Claude se equivoque,
   bórralo.* Nuestro patrón de dos niveles ([`../claude-md/`](../claude-md/)) es exactamente esto: nivel 1
   siempre cargado con punteros; nivel 2 bajo demanda. El recorte real fue ~73%.
2. **Imports bajo demanda** — `@ruta/fichero` dentro de CLAUDE.md incorpora otro doc; los CLAUDE.md de
   subcarpetas solo se cargan al entrar en ellas. Ver [`CLAUDE.import-example.md`](./CLAUDE.import-example.md).
3. **MCP con moderación** — cada server suma su bloque de tools. El modo deferred (por defecto) mitiga,
   pero desactiva los servers que no uses en el proyecto. Menos tools = menos contexto **y** mejor caching
   (ver [`../prompt-caching/`](../prompt-caching/)).
4. **Subagentes para investigar** — la exploración sucia (leer 15 ficheros, probar hipótesis) va a un
   subagente; a tu sesión vuelve el resumen ([`../subagents/`](../subagents/)).
5. **Explore → Plan → Code** — separa la exploración (plan mode, read-only) de la implementación; los
   artefactos de exploración no se quedan a vivir en el contexto de implementación.
6. **Lecturas con puntería** — "lee `config/auth.js`" mejor que "entiende cómo funciona el auth". En la
   metodología (Parte 2) esto es la regla CodeGraph-primero: 1 llamada con señal > 10 ficheros enteros.
7. **`/context` regularmente** — mide antes de optimizar; te dice exactamente qué bloque engorda.

**Conexión con la Parte 2:** la prevalencia de tools de la metodología (CodeGraph → Serena → grep) es,
en el fondo, una política de gestión de contexto: máxima señal por token.

Docs: [context-window](https://code.claude.com/docs/en/context-window) ·
[best practices](https://code.claude.com/docs/en/best-practices).
