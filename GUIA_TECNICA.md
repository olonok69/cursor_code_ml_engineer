# Cursor — Guía técnica de implementación (curso en dos partes)

> Referencia copy-paste para montar cada pieza. Complementa a
> [`GUIA_PRESENTACION.md`](./GUIA_PRESENTACION.md) (el hilo narrativo) con el **cómo**.
> Todos los artefactos ejecutables están en [`ejemplos/`](./ejemplos/);
> [`docs/`](./docs/) es referencia de una instalación real. Volumen Claude Code:
> [`GUIA_TECNICA.md`](https://github.com/olonok69/claude_code_ml_engineer/blob/HEAD/GUIA_TECNICA.md)
> (repo hermano) — misma estructura y numeración de secciones.
>
> **Nota de verificación:** el contenido específico de Cursor (Skills, Marketplace, Subagents, CLI
> headless, hooks, SDK…) se verificó contra `docs.cursor.com` en agosto de 2026. Cursor cambia rápido —
> antes de reutilizar esta guía, revisa si algo se ha vuelto a mover.

## Índice

**Parte 1 — Cursor**

1. [Instalación y CLI](#1-instalación-y-cli)
2. [Memoria: AGENTS.md, rules y Memories](#2-memoria)
3. [Permisos](#3-permisos)
4. [Sesiones entre superficies](#4-sesiones)
5. [Context window](#5-context-window)
6. [Prompt caching](#6-prompt-caching)
7. [MCP](#7-mcp)
8. [Skills y Marketplace](#8-skills-y-marketplace)
9. [Subagents](#9-subagents)
10. [Hooks](#10-hooks)
11. [Automatización: headless, CI, Automations, SDK](#11-automatización)

**Parte 2 — La metodología**

12. [El flujo y el ejemplo real](#12-metodología)
13. [Las herramientas: CodeGraph, Serena, GSD](#13-herramientas-del-método)
14. [Transferir la metodología (starter-kit / de Claude Code a Cursor)](#14-transferir-la-metodología)
15. [Sincronización de máquinas](#15-sincronización-de-máquinas)

**Parte 3 — El grafo de conocimiento de tickets (graphify)**

16. [Grafo de conocimiento de tickets](#16-grafo-de-conocimiento-de-tickets)

---

# PARTE 1 — Cursor

## 1. Instalación y CLI

```bash
# Editor: descarga desde cursor.com (macOS / Windows / Linux)

# Cursor CLI (agent) — headless-capable
curl https://cursor.com/install -fsS | bash

# Arrancar
cd tu-proyecto && agent

# Headless (un prompt, stdout)
agent -p "resume los cambios de esta rama"

# En background (equivalente conceptual a lanzar un Background Agent desde CLI)
agent -p "…" --background
```
Comandos dentro de la sesión CLI: `/clear`, `/rewind`, `/summarize`, y los propios del editor (Plan mode,
Agent mode, chat). No hay paridad 1:1 con `/help`, `/mcp`, `/plugin`, `/schedule`, `/loop`, `/desktop` de
Claude Code — la configuración de MCP/hooks/skills se edita como fichero, no por slash command.
Referencia completa: `docs.cursor.com/cli`.

---

## 2. Memoria

### `AGENTS.md` (raíz + anidado — gana el más específico)
```
AGENTS.md                    # raíz del repo, sin frontmatter, siempre cargado
<subdir>/AGENTS.md           # más específico: gana sobre el de la raíz al trabajar ahí
```
No hay sintaxis `@ruta/fichero` de import eager en `AGENTS.md` (sí existe dentro de rules `.mdc`, ver
abajo) — usa punteros + que el agente lea el fichero, o mueve ese contenido a una rule.

### `.cursor/rules/*.mdc` — gates y prevalencia
Frontmatter: `description`, `globs`, `alwaysApply`. **Cuatro modos**: Always Apply, Apply Intelligently,
Apply to Specific Files, Apply Manually. Dentro del cuerpo, `@fichero` incluye contenido de otro fichero al
cargar la rule (carga *eager* — cuenta contra el contexto siempre que la rule esté activa):
```yaml
---
description: Gates y prevalencia de tools del proyecto
globs:
alwaysApply: true
---
Antes de tocar código: orienta con la skill `kg` + STATUS.md. Para navegar, `codegraph_explore`
PRIMERO. @../data/changes/SHARP_EDGES.md
```
Recomendado: partir gates en varios `.mdc` (1 concern por regla, <50 líneas), no un único fichero enorme.

### Patrón de dos niveles (ver [`ejemplos/agents-md/`](./ejemplos/agents-md/))
- **Nivel 1** = `AGENTS.md` + rules `alwaysApply` siempre cargados: orientación + punteros de una línea.
  Pequeño.
- **Nivel 2** = ficheros bajo `data/changes/` (`STATUS.md`, `PLAYBOOK.md`, `SHARP_EDGES.md`,
  `CONVENTIONS.md`, `<TICKET>/<TICKET>.md`) que se leen bajo demanda.
- **Regla write-once:** cada dato en un único ledger canónico; el core lleva el puntero, no la copia.

### Memories — un sistema DISTINTO
Cursor genera Memories automáticamente a partir de tus chats — **no** son ficheros versionables que tú
escribes, y **no** es el mismo mecanismo que la auto-memory de Claude Code (`MEMORY.md`). No copies el
modelo mental de Claude Code a ciegas: trátalas como complemento del patrón de dos niveles, no como
sustituto.

---

## 3. Permisos

```jsonc
// ~/.cursor/permissions.json (o su equivalente de proyecto)
{
  "allow": [
    "serena:find_symbol",
    "playwright:browser_navigate",
    "codegraph:*"
  ]
}
```
Allowlist con **glob** (`server:*`, `*:tool`) — no copies el JSON de `allow` de Claude Code
(`mcp__serena__…`): re-implementa la *política* con este formato. El humano es dueño de las acciones
externas (push/PR/deploy) → esas no van en `allow`; se refuerzan con rules ("no push sin pedir") + hooks
(`beforeShellExecution`, §10).

### Las capas que gobiernan el acceso — comparado con Claude Code

1. **`permissions.json`** — el allowlist de arriba (proyecto + usuario, con glob).
2. **Approvals de la UI / settings del producto** — confirmación interactiva en el editor.
3. **Rules** — política declarada en prosa (prevalencia, "no push sin pedir"): no vetan por sí solas, pero
   dirigen el comportamiento del agente de forma consistente.
4. **Hooks** — un `beforeShellExecution`/`preToolUse` con `permission: "deny"` (o `exit 2`) veta por
   *contenido*, cosa que el allowlist estático no puede (§10).

> Regla-resumen: **Claude Code gestiona un allowlist de nombres de tool** (`mcp__servidor__tool`);
> **Cursor gestiona lo mismo con `server:tool` + glob**, reforzado por rules y hooks. La *política* — el
> humano posee lo externo — es idéntica; el mecanismo cambia.

---

## 4. Sesiones

| Necesito… | Herramienta |
|---|---|
| Trabajar en el editor con diffs inline | **Editor Cursor** (chat / Agent mode / Plan mode) |
| Terminal / SSH / servidor sin UI | **Cursor CLI** (`agent`) |
| Tarea larga en la nube, sin editor abierto | **Background / Cloud Agents** (`cursor.com/agents`) |
| Revisión automática de cada PR | **Bugbot** (GitHub/GitLab/Bitbucket) |

El mismo agente y la misma configuración (`AGENTS.md`/rules/MCP/permissions/hooks) funcionan en las tres
superficies interactivas; Bugbot corre solo, sin invocarlo.

> No hay equivalente directo de `claude --teleport` / Remote Control / `/desktop` (el handoff explícito
> entre CLI-terminal y app de escritorio de Claude Code): en Cursor, editor/CLI/nube son puntos de entrada
> independientes al mismo agente, no una sesión que se "traspasa" entre superficies con un comando.

---

## 5. Context window

Referencia completa: [`ejemplos/context/`](./ejemplos/context/). Lo que carga la sesión
antes de tu primer prompt: system/agent prompt (oculto, siempre primero) · rules `alwaysApply` +
`AGENTS.md` (lo controlas tú) · Memories si las hay (sistema distinto — revisa qué se coló) · índice de
tools MCP · luego conversación, ficheros leídos, output de comandos (crece cada turno).

```text
/clear                         # nueva sesión, reset entre tareas no relacionadas
/rewind                        # volver a un mensaje previo
/summarize                     # resumir y liberar contexto manualmente
# + anillo de contexto en el editor: uso por bloque
```

- Cursor **resume automáticamente** al acercarse al límite (además del `/summarize` manual) — no asumas
  paridad exacta con `/compact <foco>` de Claude Code; el mecanismo de resumen automático es distinto.
- MCP: cada server suma contexto → desactiva los que el proyecto no use (`.cursor/mcp.json`).
- Investigación ruidosa → subagents (§9): el ruido muere fuera; vuelve el resumen.
- `AGENTS.md`/rules: misma regla que en la doc de Claude Code — *si puedes borrarlo sin que el agente se
  equivoque, bórralo*.

---

## 6. Prompt caching

Referencia y demo ejecutable (API de Anthropic, para entender el mecanismo — no expuesto como tal en el
producto Cursor): [`ejemplos/prompt-caching/`](./ejemplos/prompt-caching/)
([`cache_demo.py`](./ejemplos/prompt-caching/cache_demo.py)).

**Mecánica (API):** se cachea un **prefijo contiguo** hasta un breakpoint `cache_control`; jerarquía
estricta `Tools → System → Messages` (un cambio invalida su nivel y los siguientes).

| | Escritura | Lectura |
|---|---|---|
| TTL 5 min (defecto) | 1.25× input | **0.1×** input |
| TTL 1 h (`"ttl": "1h"`) | 2× input | **0.1×** input |

```python
system=[{ "type": "text", "text": STABLE_INSTRUCTIONS,
          "cache_control": {"type": "ephemeral"} }]   # breakpoint AL FINAL de lo estable
messages=[{"role": "user", "content": query}]          # lo variable, DESPUÉS (fuera del cache)
```

Diagnóstico en `response.usage`: `cache_creation_input_tokens` / `cache_read_input_tokens`.
Mínimo cacheable ~1.024 tokens (4.096 en Haiku); máx. 4 breakpoints explícitos.

**En el producto Cursor** no hay mando expuesto (ni env vars como `ENABLE_PROMPT_CACHING_1H`, ni
`cache_control` visible) — aplica lo que decida el proveedor del modelo por debajo. Lo que sí controlas:
`AGENTS.md`/rules pequeños y **estables** (prefijo que no cambia); no editarlos a mitad de sesión; pocos
MCP activos (bloque de tools estable); `/clear` entre tareas no relacionadas. Si automatizas con la
**Cursor SDK** contra la API de Anthropic directamente (§11), sí aplican las reglas de arriba tal cual.

---

## 7. MCP

Ver [`ejemplos/mcp/mcp.json.example`](./ejemplos/mcp/mcp.json.example). Scopes: **project**
(`.cursor/mcp.json`, versionado) y **user** (`~/.cursor/mcp.json`, editable directamente o vía Settings →
MCP).

```jsonc
// .cursor/mcp.json — edición manual, no hay comando "agent mcp add"
{ "mcpServers": {
    "serena": { "command": "uvx", "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"] },
    "context7": { "url": "https://mcp.context7.com/mcp" },
    "supabase": {
      "command": "npx", "args": ["-y", "@supabase/mcp-server-supabase@latest"],
      "env": { "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}" } }
} }
```
Tras editar: **recarga/reinicia Cursor** — no hay hot-reload. Las tools MCP se permiten/deniegan en
`permissions.json` (§3) con `server:tool` + glob.

> **La config da la capacidad; `AGENTS.md`/rules dan el criterio.** Los MCP servers **no** se instalan en
> `AGENTS.md` — ese fichero es solo prompt, no configuración. Se instalan en `.cursor/mcp.json` /
> `~/.cursor/mcp.json` (o los trae un pack del repo). Pero instalar Serena solo hace que *exista* la tool;
> que el agente **tire de ella sin pedirlo** lo consigue una rule con un *trigger map*: "CodeGraph ANTES de
> leer ficheros enteros; `find_referencing_symbols` SIEMPRE antes de un rename". Es la regla de prevalencia
> de [`metodologia/herramientas.md`](./ejemplos/metodologia/herramientas.md) — la config convierte
> "no tengo la tool" en "la tengo"; la rule convierte "la tengo" en "se usa en el orden correcto".

---

## 8. Skills y Marketplace

**Skill** — `.cursor/skills/<n>/SKILL.md` con frontmatter `name` + `description` (la `description` guía
la auto-selección, igual que en Claude Code). Puede llevar scripts/plantillas en su carpeta.

**Interop directa:** Cursor también lee `.claude/skills/` — **el mismo `SKILL.md` sirve en los dos
productos** sin traducir nada. Es la razón por la que las skills `kg`/`kg-refresh` de la Parte 3 (creadas
originalmente para Claude Code) funcionan igual aquí.

**Marketplace** (`cursor.com/marketplace`): paquetes instalables de skills + subagents + MCP + hooks +
rules, desde la UI del producto. No hay comando `/plugin install`.

```
.cursor/skills/kg/SKILL.md
.cursor/skills/kg-refresh/SKILL.md
.cursor/skills/sanitise-diff/SKILL.md
.cursor/skills/methodology-plan/SKILL.md
```
Ejemplos reales de skills de proyecto: [`ejemplos/skills-plugins/.cursor/skills/`](./ejemplos/skills-plugins/.cursor/skills/)
(`audit`, `deploy-staging`). Pack de metodología con las cuatro skills anteriores:
[`docs/ai-agents-code-methodology/cursor/skills/`](./docs/ai-agents-code-methodology/cursor/skills/).

> **Lo que YA NO es una brecha frente a Claude Code (agosto 2026):** cuando se escribió la primera guía de
> adaptación no existían ni Skills ni Marketplace en Cursor — la tabla "qué NO está" de
> [`ejemplos/README.md`](./ejemplos/README.md) refleja ese snapshot antiguo en algunas filas.
> Revisa `docs.cursor.com` antes de asumir que algo "no tiene equivalente".

---

## 9. Subagents

Referencia completa + diagrama: [`ejemplos/subagents/`](./ejemplos/subagents/).

**Nativo (Cursor 2.4+):** delegación tipo Task, contexto **aislado** por subagent — a la sesión principal
vuelve solo el resumen. Se invoca por lenguaje natural o `/nombre`; ejecución en paralelo para trabajo
independiente. Tipos base documentados de forma laxa — no asumas nombres exactos sin comprobar la doc
actual.

**No hay `.claude/agents/*.md` equivalente.** El patrón que funciona: una **plantilla de prompt**
(opcionalmente respaldada por una skill), guardada como referencia y pegada al lanzar el subagent:
```text
# ejemplos/subagents/prompts/refactor-scout.md
Actúa como refactor-scout: usa CodeGraph `codegraph_explore` y LUEGO Serena
`find_referencing_symbols` antes de proponer el rename. Desambigua por clase.
```
Ejemplos reales: [`security-reviewer`](./ejemplos/subagents/prompts/security-reviewer.md) ·
[`refactor-scout`](./ejemplos/subagents/prompts/refactor-scout.md) (codifica la regla
CodeGraph→Serena de la Parte 2). **Gotcha:** el subagent no hereda tu conversación — contexto en el prompt
de lanzamiento.

**Lo que NO existe: Agent Teams.** Sin lead+teammates+inbox compartido. El sustituto pragmático es
paralelismo con **Background/Cloud Agents** (`cursor.com/agents` o CLI `agent -p "…" --background`): cada
uno una sesión completa, en su propia rama, **sin mensajería entre agentes**. Particiona el trabajo por
rama/fichero antes de lanzar; un humano (o el agente principal) integra resultados.

| | Subagent | Background / Cloud Agent |
|---|---|---|
| Contexto | Aislado; devuelve un resumen | Sesión completa, async, en su rama |
| Comunicación | Solo resultado → sesión principal | Ninguna entre agentes (sin inbox) |
| Coste | Bajo | Alto (N sesiones completas) |
| Config | Prompt/skill al lanzar | `cursor.com/agents` o CLI `--background` |

---

## 10. Hooks

Todo en [`ejemplos/hooks/`](./ejemplos/hooks/). Config en `.cursor/hooks.json` (proyecto) o
`~/.cursor/hooks.json` (usuario):

```jsonc
// hooks.json.example
{ "hooks": {
    "beforeReadFile": [{ "command": "node ./hooks/read_hook.js" }],
    "beforeShellExecution": [{ "command": "node ./hooks/block_external.js" }],
    "afterFileEdit": [
      { "command": "node ./hooks/format_hook.js" },
      { "command": "node ./hooks/tsc.js" }
    ]
} }
```

**Contrato:** payload del evento por **STDIN** · respuesta **JSON** por STDOUT con
`{"permission": "allow"|"deny"|"ask", "user_message"?: string}` — **`exit 2` también bloquea**.
`failClosed`: si el hook crashea, bloquea (postura más estricta que el fail-open implícito de un hook que
no responde en Claude Code).

**Eventos disponibles (más granulares que Claude Code):** `preToolUse`, `postToolUse`, `beforeReadFile`,
`afterFileEdit`, `beforeShellExecution`, `beforeMCPExecution`, `beforeSubmitPrompt`, `stop`, y más.

**Patrón de bloqueo (JS):**
```js
// beforeReadFile — bloquear .env
const p = JSON.parse(require("fs").readFileSync(0, "utf8"));
if ((p.path || "").includes(".env")) {
  console.log(JSON.stringify({ permission: "deny", user_message: "Bloqueado: no leas .env" }));
  process.exit(0);
}
console.log(JSON.stringify({ permission: "allow" }));
process.exit(0);
```
Payloads reales: [`pre-log.json`](./ejemplos/hooks/pre-log.json),
[`post-log.json`](./ejemplos/hooks/post-log.json). Ejemplo de veto de handoff:
[`block_external.js`](./ejemplos/hooks/block_external.js) (`beforeShellExecution` para vetar
push/PR/deploy salvo petición explícita) — también en
[`docs/ai-agents-code-methodology/cursor/hooks/block-external-git.ps1`](./docs/ai-agents-code-methodology/cursor/hooks/block-external-git.ps1).

---

## 11. Automatización

Ver [`ejemplos/automation/`](./ejemplos/automation/).

**Headless / piping:**
```bash
tail -200 app.log | agent -p "avísame de anomalías"
git diff main --name-only | agent -p "revisa por seguridad"
```

**CI/CD:** **Bugbot** (nativo, revisión de PR sin script propio) o Cursor SDK en tu propio GitHub Action —
ver [`github-action-cursor.yml`](./ejemplos/automation/github-action-cursor.yml).

**Automations** (distinto de Background/Cloud Agents) — cron + triggers de eventos: Slack, Linear, PR
merged, PagerDuty. Los **Background/Cloud Agents** (`cursor.com/agents`) son para trabajo async bajo
demanda, no programado.

**Cursor SDK** (`@cursor/sdk`, v1.0.26 en esta verificación):
```ts
import { Agent } from "@cursor/sdk";

const agent = await Agent.create({ apiKey: process.env.CURSOR_API_KEY, local: { cwd } });
const run = await agent.send(prompt);
for await (const ev of run.stream()) {
  // eventos de progreso / resultado
}
```
Para que el agente trabaje en la nube y abra el PR él mismo: `Agent.create({ cloud: { repos, autoCreatePR: true } })`.
Ejemplo completo: [`sdk.ts`](./ejemplos/automation/sdk.ts) ·
[`review.ts`](./ejemplos/automation/review.ts) (revisión automática de PR con la SDK).

> **Ojo con la API:** no es `Agent.prompt()` — es `Agent.create()` seguido de `agent.send()` y
> `run.stream()`. Verifica la firma exacta contra `docs.cursor.com/background-agent/api` antes de dar
> por buena esta guía si ha pasado tiempo.

---

# PARTE 2 — La metodología

## 12. Metodología

Todo el material profundo (flujo de 11 etapas, ejemplo real end-to-end, prevalencia de tools) está en
[`ejemplos/metodologia/`](./ejemplos/metodologia/). Resumen:

### El flujo real (ver [`metodologia/WORKFLOW.md`](./ejemplos/metodologia/WORKFLOW.md))
Agente = colaborador disciplinado; la autonomía se gana por-decisión. 11 etapas encadenadas por **gates
deterministas**: orientar (skill `kg` + history+status) → triaje inbound en el **contrato de salida** →
regresión vs pre-existente → investigar con **oráculo determinista** (antes de la tirada de pago) →
**Plan mode** + acuerdo → Agent mode: TDD RED→GREEN → verificar (unit+scoped+regresión+contrato vía
*wrapper* Y dentro de la imagen desplegada) → documentar → **sanitizar** (skill `sanitise-diff` sobre
líneas añadidas) → handoff (el agente **no** hace push/PR/deploy salvo petición explícita — hook
`beforeShellExecution`/rules; el humano lo hace) → revisión Bugbot + persistir (skill `kg-refresh` si
aplica).
Diagrama: [`metodologia/flow.png`](./ejemplos/metodologia/flow.png) (fuente `flow.mmd`, render
`render_flow.py`). Caso concreto de principio a fin:
[`metodologia/EJEMPLO_REAL.md`](./ejemplos/metodologia/EJEMPLO_REAL.md).

> **El gate outbound son tres checks** (no solo "los tests pasan"): (1) reproducir en la **etapa real de
> salida** —el *wrapper* que reconstruye el contrato, no una función interna `extract()`—; (2) el JSON
> local casa con el contrato; (3) verificarlo **dentro de la imagen desplegada** (descargar/construir la
> imagen del runtime, montar el `src`, re-correr). Los tests en verde no son prueba de lo que se despliega.
> Idéntico en rol al gate de Claude Code — cambia solo qué agente lo ejecuta.

### Prevalencia de tools (ver [`metodologia/herramientas.md`](./ejemplos/metodologia/herramientas.md))
Las rules `.cursor/rules/` y `AGENTS.md` no solo dicen *qué* hacer, sino **con qué tool y en qué orden**
(barato→caro, determinista→probabilístico):
```
Orientar     -> skill kg (grafo de tickets) · STATUS.md/ledgers · git · gh   (sin inferencia)
Navegar      -> CodeGraph codegraph_explore (MCP): fuente+rutas+blast radius+cobertura (1 llamada; trátala como YA leída)
Refactor-chk -> Serena find_referencing_symbols (MCP) (desambigua por clase)  OBLIGATORIO antes de renombrar/borrar
Diagnosticar -> oráculo determinista (parser/validador/_diag_*.py)  (sin inferencia, reproducible)
Entorno      -> AWS CLI (CloudWatch, lambda get-function, SQS/DLQ)   (read-only)
Contrato     -> Playwright (MCP) / F12 sobre el endpoint de salida
Desplegado   -> Docker: repro dentro de la imagen del runtime (etapa real = wrapper); tests verdes != lo enviado
Solo al final-> la tirada del agente, para VERIFICAR el fix (no para diagnosticar)
```

### Permisos del método (distinto mecanismo que Claude Code, misma política)
Claude Code: allowlist hand-curated en `settings.local.json` (`mcp__serena__…`). Cursor: (1) **Rules**
— prevalencia y "no push sin pedir"; (2) **Approvals** de la UI/settings; (3) **Hooks** — p. ej.
`beforeShellExecution` para push/PR/deploy. No copies el JSON de `allow` de Claude Code: re-implementa la
*política* con rules + hooks + `permissions.json`.

---

## 13. Herramientas del método

### CodeGraph ([`ejemplos/codegraph/`](./ejemplos/codegraph/)) — inteligencia de código local (vía MCP)
Índice tree-sitter → SQLite en `.codegraph/` (sin API keys). Devuelve símbolos + rutas de llamada +
blast radius + **flags de cobertura de tests**. Benchmarks: 58% menos tool calls, 22% más rápido.
```bash
codegraph init        # crea .codegraph/ y construye el índice   codegraph sync   # incremental tras editar
codegraph explore "<símbolo|pregunta>"       # fuente + rutas + blast radius, en 1 round-trip
codegraph impact|callers|node <símbolo>      # blast radius / callers / 1 símbolo + trail
```
```jsonc
// .cursor/mcp.json — registro manual, no hay "codegraph install --target=cursor"
{ "mcpServers": { "codegraph": { "command": "codegraph", "args": ["serve", "--path", "<repo>", "--mcp"] } } }
```
Es el **primer** tool de navegación (antes que grep/Read); trata la fuente que imprime como **ya leída**
(no re-abras ese fichero). El MCP **no tiene proyecto por defecto** salvo que fijes `--path`: hazlo y
`codegraph_explore` no necesita `projectPath`; pásalo solo para consultar **otro** repo indexado. En WSL2
`/mnt` el watcher puede perder cambios → `codegraph sync` tras editar.

### Serena ([`ejemplos/serena/`](./ejemplos/serena/)) — navegación semántica vía LSP (MCP)
```jsonc
// .cursor/mcp.json
{ "mcpServers": { "serena": { "command": "uvx", "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"] } } }
```
Tools clave: `find_symbol` (con `body=true`), `get_symbols_overview`, `search_for_pattern`, y sobre todo
**`find_referencing_symbols`** — el chequeo **preciso** antes de renombrar/borrar: desambigua métodos
homónimos por clase, donde el `impact` plano de CodeGraph los mezcla. Complementa a CodeGraph, no lo
sustituye. La plantilla [`refactor-scout`](./ejemplos/subagents/prompts/refactor-scout.md)
empaqueta el orden CodeGraph→Serena→grep como procedimiento de subagent.

### GSD ([`ejemplos/gsd/`](./ejemplos/gsd/)) — el método hecho tooling, **solo en Claude Code**
Ciclo por fases con estado versionado en `.planning/` y subagentes especializados (`gsd-planner`,
`gsd-plan-checker`, `gsd-executor`, `gsd-code-reviewer`, `gsd-verifier`, `gsd-phase-researcher`) — **no
hay port oficial a Cursor**.

**Equivalente práctico en Cursor:**
```
Plan mode                    -> gate discuss -> plan (el humano aprueba antes de tocar código)
skill methodology-plan       -> rellena la plantilla de plan antes de implementar
Task / subagents + prompt    -> sustituye a los roles gsd-* (planner/executor/verifier)
data/changes/                -> el mismo estado que en Claude Code (no .planning/ de GSD)
```
> **Honestidad — ¿lo usamos aquí?** **No.** Este proyecto no corre GSD (no existe en Cursor) ni su
> equivalente: usa el flujo de 11 etapas + `data/changes/`, más depurado y afinado a fixes por ticket sobre
> un servicio en producción. GSD (Claude Code) tiene más sentido en un **greenfield multi-componente**.

---

## 14. Transferir la metodología

Material real: [`docs/ai-agents-code-methodology/`](./docs/ai-agents-code-methodology/) —

- **Cursor:** [`CURSOR_ADAPTATION.md`](./docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md) +
  superficie [`cursor/`](./docs/ai-agents-code-methodology/cursor/) (`AGENTS.md.example`,
  `hooks.json.example`, `mcp.json.example`, `rules/00-methodology-core.mdc`,
  `rules/01-tool-prevalence.mdc`, `rules/02-gates-and-handoff.mdc`, `skills/kg/`, `skills/kg-refresh/`,
  `skills/methodology-plan/`, `skills/sanitise-diff/`, `hooks/block-external-git.ps1`) +
  [`scripts/bootstrap-cursor-repo.ps1.txt`](./docs/ai-agents-code-methodology/scripts/bootstrap-cursor-repo.ps1.txt)
- Compartido: [`TRANSFER_AND_BOOTSTRAP.md`](./docs/ai-agents-code-methodology/TRANSFER_AND_BOOTSTRAP.md),
  [`templates/CURSOR_WORKING_AGREEMENT_TEMPLATE.md`](./docs/ai-agents-code-methodology/templates/CURSOR_WORKING_AGREEMENT_TEMPLATE.md),
  [`scripts/bootstrap-new-repo.ps1.txt`](./docs/ai-agents-code-methodology/scripts/bootstrap-new-repo.ps1.txt)
- El mismo pack trae [`COPILOT_ADAPTATION.md`](./docs/ai-agents-code-methodology/COPILOT_ADAPTATION.md) —
  este repo no es un caso especial: la disciplina llega a un tercer agente.

**Qué viaja sin cambios:** plan→acuerdo→implementar · verificar en el contrato del consumidor · resolver
la clase general · rastro durable · el humano posee lo externo.

**Qué cambia — la superficie (tabla completa):**
```
CLAUDE.md (+ jerarquía)              -> AGENTS.md + .cursor/rules/*.mdc
Skills ~/.claude/skills/             -> .cursor/skills/ (o ~/.cursor/skills/) — MISMO SKILL.md
Allowlist settings.local.json        -> permissions.json (server:tool + glob)
Hooks (exit 0/2, stdin JSON)         -> .cursor/hooks.json (permission JSON, stdin/stdout, failClosed)
Plan mode                            -> Plan mode (misma disciplina, mismo nombre)
Subagents (Task) + Agent Teams       -> Cursor Subagents (nativo) — SIN Agent Teams
claude -p (headless)                 -> agent -p (Cursor CLI)
Auto-memory (MEMORY.md)              -> Memories (sistema DISTINTO, no soportar 1:1)
Agent SDK (query/allowedTools)       -> Cursor SDK (Agent.create + agent.send + run.stream)
```

**Bootstrap en el repo destino:**
```powershell
Expand-Archive ai-agent-methodology-package.zip -DestinationPath data/changes
Rename-Item …/scripts/bootstrap-new-repo.ps1.txt bootstrap-new-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1
# crea: STATUS.md · FOLLOWUPS.md · SHARP_EDGES.md · plantillas de handover y QA

# Cursor: AGENTS.md + rules + skills + MCP + hooks
Rename-Item …/scripts/bootstrap-cursor-repo.ps1.txt bootstrap-cursor-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1
```
(El script viaja como `.ps1.txt` para esquivar los bloqueos de contenido activo del correo.)

**Fallback sin grafo de tickets** (80% del valor, setup mínimo): `STATUS.md` newest-first + carpetas por
ticket · búsqueda léxica por síntoma/símbolo/campo del contrato · historia de commits (solapamiento de
ficheros) como sustituto ligero del grafo · sección corta de "danger zones".

**Checklist de primer día:** rellenar `STATUS.md` · 3-5 invariantes en `SHARP_EDGES.md` · definir el
contrato de salida · comandos de test scoped · un issue completo con RED→GREEN + verificación de contrato.

---

## 15. Sincronización de máquinas

Procedimiento real (sanitizado) que aplica los mismos principios a una tarea de ops
(ver [`metodologia/machine-sync.md`](./ejemplos/metodologia/machine-sync.md);
runbooks de la instalación real en [`docs/synchro/`](./docs/synchro/)). El runbook original nació en
Claude Code — la tabla de adaptación:
```
Claude Code                          Cursor
Puntero en CLAUDE.md                 Puntero en AGENTS.md / rule on-demand
Bundle ~/.claude (skills + memory)   Skills en .cursor/skills/ o ~/.cursor/skills/; Memories != MEMORY.md
codegraph MCP en ~/.claude.json      Re-pin --path en .cursor/mcp.json en el portátil
/kg-refresh skill Claude             Skill kg-refresh del pack Cursor + mismos scripts kg_refresh.sh
```
No copies a ciegas el tarball de `~/.claude` como "setup Cursor": lleva `data/`, repos git, y reinstala la
superficie `.cursor/` (bootstrap del pack metodología). **Asimétrico:**

```bash
# OUTBOUND (principal -> portátil): COPIA COMPLETA. -h dereferencia el symlink de .aws (crítico);
# se excluyen venvs/node_modules/caches; se omite .gnupg si no existe.
WS=$(ls -d /mnt/*/ILS 2>/dev/null | head -1)          # DERIVAR la raíz, no asumir
tar -czhf ~/ils-migration-$(date +%Y%m%d).tar.gz \
  --exclude='*/node_modules' --exclude='*/.codegraph' --exclude='*/.venv' --exclude='*/__pycache__' --exclude='*.pyc' \
  -C "$(dirname "$WS")" "$(basename "$WS")" \
  -C /home/$USER .cursor .aws .ssh
# USB: WSL no auto-monta un USB conectado tras arrancar -> sudo mount -t drvfs F: /mnt/f ; copiar, sync,
# y verificar byte a byte (stat -c %s origen destino coinciden) antes de expulsar. El bundle crece (~1.5 GB).
# En destino: bash data/machine-sync/target-setup.sh  -> reinstala el CLI de CodeGraph, actualiza GSD si va
# atrasado, corrige el --path del MCP a la raíz real del portátil (en .cursor/mcp.json), reconstruye el índice.

# INBOUND (portátil -> principal): SOLO DELTA. El código ya está en GitHub.
git fetch origin                                      # única op de red (read-only)
cp data/changes/STATUS.md data/changes/STATUS.md.mainbak   # backup ANTES
tar -xzf "$TARBALL" -C "$REPO"                         # solo los docs gitignored de data/
diff data/changes/STATUS.md.mainbak data/changes/STATUS.md # ¿solo adiciones? quedarse. ¿ediciones propias? STOP
```

**Dos huecos, dos subcomandos idempotentes** (el workspace lleva un grafo `kg` — §16): en un portátil
nuevo, `kg_refresh.sh bootstrap` instala el tooling que no va en el bundle y fija el intérprete (además
re-bootstrap `.cursor/`: MCP `--path`, skills, si esa máquina no lo tenía); y como la memoria del agente
**no** viaja igual que en Claude Code, decide explícitamente qué viaja: `snapshot-memory` la parquea bajo
`data/` (para que viaje) y `restore-memory` la fusiona de vuelta con backup en la principal, antes de
`kg-refresh` — no asumas que las Memories del editor se sincronizan solas. Punto de entrada único para el
agente del portátil: `LAPTOP_START_HERE.md` (restaurar → `bootstrap` → seguir igual → mandar delta). El
grafo es un artefacto **derivado**: nunca viaja de vuelta; se reconstruye donde esté el corpus.

Guardrails (el landing lo conduce **un agente**, con un `INSTRUCTIONS.md` escrito *para* él): solo
no-destructivo (renombrar, no borrar; nunca dos ops de movimiento a la vez en un mount Windows); sin
escrituras git a remoto (nada de push/merge/PR); STOP y preguntar ante ambigüedad; el binario del AWS CLI
**no** va en el bundle (reinstalar en destino + `aws sso login`) — igual el CLI de CodeGraph y el índice
`.codegraph/`, que repone `target-setup.sh`. El humano es dueño de las acciones
externas; el agente prepara y reporta con evidencia (conteos de ficheros, estados de PR).

---

# PARTE 3 — El grafo de conocimiento de tickets (graphify)

## 16. Grafo de conocimiento de tickets

**Tecnología: `graphify` — no CodeGraph.** CodeGraph es solo la analogía (mismo rol, otro dominio): si
CodeGraph indexa el *código*, este grafo indexa la **memoria del proyecto** — writeups por ticket, "sharp
edges", runbooks, notas de memoria. El pipeline de build se generó originalmente **en Claude Code**; hoy
la consulta y el refresco viven como skills, portables sin cambios. Todo el material real está en
[`docs/knowledge-graph/`](./docs/knowledge-graph/): [`design.md`](./docs/knowledge-graph/design.md) (diseño
de la Fase 1, un spike con decisión keep/extend/replace), scripts, tests, manifest y la salida real.
Resumen narrativo adicional: [`docs/KNOWLEDGE_GRAPH.md`](./docs/KNOWLEDGE_GRAPH.md).

### Las piezas

| Pieza | Qué es |
|---|---|
| `kg` (skill) | Consulta: `explain` / `path` / `find` — determinista, **sin LLM** |
| `kg-refresh` (skill) | Reconstruye el grafo: `prepare` → extracción semántica → `finalize` |
| [`kg_query.sh`](./docs/knowledge-graph/kg_query.sh) | Envoltorio de `graphify explain`/`path` sobre `output/graph.json` + `find` (descubrir nombres de nodo); resuelve intérprete y ruta del grafo, limpia warnings |
| [`kg_refresh.sh`](./docs/knowledge-graph/kg_refresh.sh) | Bookends deterministas: `prepare` / `finalize` / `bootstrap` / `snapshot-memory` / `restore-memory` |
| [`build_manifest.py`](./docs/knowledge-graph/build_manifest.py) / [`stage_corpus.py`](./docs/knowledge-graph/stage_corpus.py) | Enumeran y montan el corpus con nombres provenance-preserving (`sst-5468__sst-5468.md`, `hub__STATUS.md`, `memory__x.md`) |
| `test_kg_corpus.py` · `test_kg_query.py` · `test_kg_refresh.py` | Los bookends están **testeados** — el pipeline es infraestructura, no un one-off |
| [`manifest.txt`](./docs/knowledge-graph/manifest.txt) | El corpus explícito y diffeable (~116 ficheros, ~196k palabras) |

**¿`kg` es un slash command o una skill? Skill** — el mecanismo de invocación por nombre (`/kg` en Claude
Code, `kg` en Cursor) no distingue por sí solo. Lo que lo hace skill: lleva **assets** (los shell
wrappers), tiene **`description`** para que el agente se auto-seleccione en la etapa de orientar sin que
la escribas, y `kg-refresh` **orquesta un paso del propio agente** (la extracción semántica) — un slash
command es solo un prompt guardado. Las definiciones (`SKILL.md`) viven **a nivel de usuario, fuera del
repo**: `~/.cursor/skills/kg/`, `~/.cursor/skills/kg-refresh/` (o `~/.claude/skills/…` — **mismo
fichero**, ambos productos lo leen). Ubicación deliberada: (1) **confidencialidad** — nada del KG vive en
rutas committeables; (2) **alcance** — user-level la hace disponible en cualquier sesión de la máquina,
coherente con que el grafo indexa también memoria del agente. Y como la config de usuario viaja en el
tarball outbound del machine-sync (§15), las skills llegan al portátil con la copia completa; el grafo
(derivado) se reconstruye allí con `bootstrap` + `kg-refresh`.

### Construir y consultar

```bash
# construir / refrescar (el único paso con el agente es la extracción semántica, con subagentes en paralelo)
kg_refresh.sh prepare        # manifest -> stage _corpus/ -> copiar a un scratch FUERA del repo
                              # extracción de nodos/aristas + clustering -> HTML/JSON/reporte
kg_refresh.sh finalize       # copiar artefactos a output/ + leak-check (nada fuera de data/)

# consultar (cero LLM: kg_query.sh lee output/graph.json directamente)
kg explain <ticket|tema>     # vecinos de un nodo    (graphify explain)  <- el uso más común
kg path <A> <B>              # camino más corto A<->B (graphify path)
kg find <substr>             # descubrir el nombre exacto de un nodo
```

**Gotcha que sostiene el pipeline:** `graphify` respeta `.gitignore` y todo `data/` lo está → correr el
detector in situ encuentra 0 ficheros; el corpus se monta en un scratch fuera del repo y los artefactos
se copian de vuelta. **Por eso `kg-refresh` es una skill y no un script:** el paso semántico es un paso
del agente; los bookends son deterministas.

### La salida real (ver [`output/`](./docs/knowledge-graph/output/))

- [`graph.html`](./docs/knowledge-graph/output/graph.html) — visualización **vis-network interactiva**:
  búsqueda de nodos, panel de info, filtro por comunidad. La captura para el deck se regenera con
  [`presentacion/capture_kg_graph.py`](./presentacion/capture_kg_graph.py) → `presentacion/kg_graph.png`
  (mismo grafo real, reutilizado sin cambios entre los dos volúmenes del curso).
- `graph.json` — NetworkX node-link; aristas **tipadas** (`relation`) con `confidence`
  (`EXTRACTED`/`INFERRED` + score). Es lo que lee `kg_query.sh`.
- [`GRAPH_REPORT.md`](./docs/knowledge-graph/output/GRAPH_REPORT.md) — el informe de auditoría:
  **507 nodos · 672 aristas · 35 comunidades**; **92% `EXTRACTED`** · 7% `INFERRED` (confianza media 0.7);
  god-nodes (los tickets estructurales, onboarding gratis) y "surprising connections" (lecciones gemelas
  que nadie había conectado a mano). Las comunidades mapean a zonas de peligro reales
  ("Letter-End & Run-in Titles", "Title Detection Failures", "PDF Extractor Cascade"…).

### Enganche y ciclo de vida

Enganchado a la regla **history-first** de `.cursor/rules/00-methodology-core.mdc` (etapa 1, Orientar):
corre `kg explain <ticket|tema>` *antes* de hacer grep en `data/changes/`; una llamada saca los tickets
relacionados + la zona de peligro a leer (apunta a *qué leer*, no lo sustituye). Honestidad: la ganancia
real es **recall en zonas densas**; `EXTRACTED` = fiable, `INFERRED` = pista a verificar. En la instalación
real todo vive bajo `data/` gitignored (los nodos llevan nombres internos → interno; compartir fuera =
pasada de sanitización aparte). Es un artefacto **derivado**: nunca viaja entre máquinas; se reconstruye
donde esté el corpus (§15, con `bootstrap` / `snapshot-memory` / `restore-memory` cerrando el círculo).

> **Coste — honesto, y por qué compensa.** "Sin LLM en la consulta" **no** es "gratis": el razonamiento caro
> se paga **una vez** al construir el grafo (`kg-refresh`, con subagentes); cada consulta `kg` es luego un
> algoritmo determinista sobre `graph.json` → **cero inferencia**, con el único coste de que el agente lee
> un output corto (como un `grep`) — coste **menor y dirigido**, no cero. El coste de construir (grafo,
> oráculos, skills deterministas) se **amortiza**: es inversión → sin inferencia por consulta, respuestas
> **deterministas y reproducibles** (mejor resultado), razonamiento caro sustituido por lookup barato →
> **ahorro de tiempo y dinero** por tarea. Se paga una vez, se cobra en cada uso — desde cualquiera de los
> dos agentes.
