# Prevalencia de herramientas — qué usa Cursor y cuándo

Las **rules** (`.cursor/rules/`) y `AGENTS.md` no solo dicen *qué* hacer; dicen **con qué herramienta**
y en qué orden. Eso convierte "tengo MCP instalado" en "el agente tira de la tool correcta".

## La regla de oro: navegación por grafo antes que leer ficheros

> **"Para 'qué es esto / quién depende / qué toco', un `codegraph_explore` **primero** — fuente + rutas de
> llamada + blast radius + flags de cobertura de tests en una llamada (trata la fuente que devuelve como YA
> leída, no la re-abras). Serena `find_referencing_symbols` para el chequeo **preciso** antes de renombrar o
> eliminar un helper (desambigua por clase). grep/Read solo para literales."** — regla en
> `.cursor/rules/01-tool-prevalence.mdc`.

> **Dos grafos, dos dominios.** CodeGraph indexa el *código*; la skill **`kg`** (graphify) indexa la
> *memoria del proyecto* (tickets, sharp edges). Detalle: [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md).

## Tabla de prevalencia

| Necesito… | Herramienta preferida | Por qué / regla |
|---|---|---|
| Survey: qué es / quién depende / blast / ¿testeado? | **CodeGraph** `codegraph_explore` | 1 consulta; trátala como YA leída |
| Chequeo preciso antes de rename/borrado | **Serena** `find_referencing_symbols` | Obligatorio; desambigua por clase |
| Cuerpo / overview de fichero grande | Serena `find_symbol` / `get_symbols_overview` | O la fuente de `explore` |
| Contrato de salida | **Playwright** / F12 | Lo que ve el consumidor |
| Runtime desplegado | **Docker** (misma imagen) | Tests en verde ≠ lo enviado |
| Causa raíz barata | **Oráculo** (`_diag_*.py` / parser) | Sin tirada de modelo para diagnosticar |
| Logs / config cloud | **AWS CLI** (read-only) | Debugging de primera clase |
| Docs de librería | **Context7** | Vs corte de entrenamiento |
| git / PRs | `gh`, `git` | status-first |
| Tickets / lecciones del área | **Skill `kg`** (o STATUS fallback) | history-first antes de grep |
| Trabajo paralelo independiente | **Task** (explore / generalPurpose) | Sin ensuciar el hilo principal |

## El orden (barato → caro)

1. Orientación: `STATUS.md` + `git`/`gh` + skill **`kg`**
2. Navegación: CodeGraph → Serena
3. Diagnóstico: oráculo determinista
4. Entorno: AWS CLI
5. Contrato: Playwright
6. Outbound: wrapper + Docker
7. Solo al final: tirada del modelo para verificar el fix

## Skills vs oráculos

| | **Skills / MCP** | **Oráculos** (`_diag`, parser) |
|---|---|---|
| Qué es | Capacidad registrada (auto-select por `description`) | Código que el agente escribe y corre en Shell |
| Dónde (Cursor) | `.cursor/skills/` · `~/.cursor/skills/` · MCP | `data/changes/<ticket>/` (gitignored) o `src/`/`tests/` |
| Ejemplos | `kg`, `sanitise-diff`, Serena, CodeGraph, Playwright | `_diag_pdf.py` |

En Claude Code `/kg` vivía en `~/.claude/skills/`. En Cursor: skill de proyecto (pack metodología) o usuario.

## Permisos (distinto a Claude)

Claude Code: allowlist hand-curated en `settings.local.json` (`mcp__serena__…`, etc.).

Cursor:

1. **Rules** — prevalencia y “no push sin pedir”.
2. **Approvals** de la UI / settings del producto.
3. **Hooks** — p. ej. `beforeShellExecution` para push/PR/deploy ([`../hooks/`](../hooks/)).

No copies el JSON de allow de Claude; re-implementa la *política* con rules + hooks.
