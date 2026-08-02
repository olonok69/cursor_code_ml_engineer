# CLAUDE.md — el patrón de "contexto de dos niveles"

`CLAUDE.md` es el fichero de **memoria/instrucciones** que Claude Code lee al principio de **cada**
sesión. El error típico es meterlo todo dentro hasta que ocupa 25 KB y se carga entero, siempre,
gastando contexto en detalle que casi nunca hace falta.

El [`CLAUDE.md`](./CLAUDE.md) de esta carpeta muestra el patrón que uso en producción (sanitizado):

### Nivel 1 — siempre cargado (pequeño)
Orientación mínima: qué es el proyecto, mapa de repos y permisos, comandos, convenciones y **punteros
de una línea** a todo lo demás. Objetivo: que sea la "onboarding" de 30 segundos del agente.

### Nivel 2 — bajo demanda (todo el detalle)
Ficheros bajo `data/changes/` que el agente **lee solo cuando el ticket lo pide**:

| Fichero | Contenido |
|---|---|
| `STATUS.md` | Ledger vivo: estado por ticket (rama/commit/PR/nº de tests). |
| `PLAYBOOK.md` | Lecciones de debugging codificadas. |
| `SHARP_EDGES.md` | Invariantes "no tocar" con el ticket que las estableció. |
| `CONVENTIONS.md` | Política de confidencialidad / sanitización. |
| `<TICKET>/<TICKET>.md` | ~55 ledgers por-ticket, cada uno autocontenido. |

### La disciplina que lo sostiene (regla write-once)
> Cada registro se escribe en **exactamente un** ledger canónico. El `CLAUDE.md` lleva un **puntero**,
> nunca una copia. Cuando se hinchó, lo recortamos **~73% sin perder información**.

### Jerarquía de CLAUDE.md (de la doc oficial)
Claude Code combina varios `CLAUDE.md` por precedencia:
`~/.claude/CLAUDE.md` (global del usuario) → `CLAUDE.md` en la raíz del repo (compartido) →
`CLAUDE.md` en subcarpetas (se cargan al entrar) → `CLAUDE.local.md` (personal, no versionado).
Además existe la **auto-memory**: Claude guarda solo aprendizajes (comandos de build, pistas de debug)
entre sesiones sin que escribas nada.
