# Subagents (Task) en Cursor — y qué pasa con Agent Teams

Cómo escalar de *un* agente a *varios* en Cursor: subagents con contexto aislado. El diagrama original
del curso sigue siendo útil conceptualmente:

![Subagents vs Agent Teams](./agents.png)

> **Agent Teams de Claude Code (lead + teammates + inbox compartido) NO existen en Cursor.**
> Usa subagents en paralelo + `.cursor/agents/` para roles. No intentes portar
> `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.

---

## 1. Subagentes built-in

| Tipo (docs actuales) | Para qué |
|---|---|
| `Explore` | Búsqueda/análisis de codebase (aislamiento de ruido) |
| `Bash` | Series de comandos shell verbosos |
| `Browser` | Interacciones de navegador vía MCP |
| Otros (Task / entorno) | `generalPurpose`, `shell`, `ci-investigator`, … según producto |

La razón de ser es la misma: **aislamiento de contexto**. Un side-quest que lee 15 ficheros no debe
inundar tu hilo; el subagente muere y te deja un resumen.

Pídeselo en natural language (*"lanza un explore agent para localizar dónde se valida el token"*) o el
orquestador lo hará cuando encaje. Varios en **paralelo** si el trabajo es independiente.

## 2. Subagentes custom — `.cursor/agents/`

Sí hay fichero de definición (docs: `docs.cursor.com/subagents`):

| Scope | Ruta |
|---|---|
| Proyecto | `.cursor/agents/<nombre>.md` |
| Usuario | `~/.cursor/agents/<nombre>.md` |
| Compat | `.claude/agents/`, `.codex/agents/` (Cursor también los carga) |

Frontmatter: `name`, `description`, opcional `model` (`inherit` / slug), `readonly`, `is_background`.

Ejemplo en este pack: [`.cursor/agents/refactor-scout.md`](./.cursor/agents/refactor-scout.md).

Opciones adicionales:

| Enfoque | Dónde | Cuándo |
|---|---|---|
| **Skill** con el procedimiento | `.cursor/skills/<rol>/SKILL.md` | Auto-selección por `description` |
| **Plantilla de prompt** | [`prompts/`](./prompts/) | Pegar al lanzar si no quieres fichero de agent |
| **Rule** | `.cursor/rules/` | Forzar el hábito (“antes de rename, usa refactor-scout”) |

Plantillas portadas: [`prompts/security-reviewer.md`](./prompts/security-reviewer.md) ·
[`prompts/refactor-scout.md`](./prompts/refactor-scout.md).

**Gotcha:** el subagent **no hereda** tu conversación — dale contexto en el prompt de lanzamiento.

## 3. Agent Teams — no disponible

Todo lo de `teams/<team>/config.json`, inboxes, `teammateMode: tmux|iterm2` es **solo Claude Code**.

Sustituto razonable en Cursor:

1. Varios subagents en paralelo con ficheros particionados (evita que dos editen el mismo file).
2. Varios **Background/Cloud Agents** en ramas distintas (sin inbox compartido).
3. Un humano (o el agente principal) integra resultados.
4. Para greenfield multi-fase: Plan mode + skills de metodología (no GSD plugin).

## 4. ¿Subagent o “equipo”?

| | **Subagent** | **Agent team (Claude only)** |
|---|---|---|
| En Cursor | Sí (built-in + `.cursor/agents/`) | No |
| Contexto | Resumen al principal | Sesiones completas + mensajería |
| Coste | Menor | Alto |
| Ideal | Side-quests, scout, review | Trabajo paralelo con debate entre agents |

**Conexión metodología:** el `refactor-scout` codifica CodeGraph → Serena. GSD en Claude Code empaquetaba
roles similares como plugin; en Cursor los roles viven como agents/skills/prompts ([`../gsd/`](../gsd/)).

El diagrama `agents.png` se regenera con `python render_agents.py` (fuente: `agents.mmd`).
