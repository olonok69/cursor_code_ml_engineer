# Prevalencia de herramientas — qué usa Claude y cuándo

El `CLAUDE.md` del proyecto no solo dice *qué* hacer; dice **con qué herramienta** y en qué orden. Esta es
la parte que convierte "tengo MCP instalado" en "el agente tira de la tool correcta automáticamente".

## La regla de oro: navegación por grafo antes que leer ficheros

> **"Para 'qué es esto / quién depende / qué toco', un `codegraph_explore` **primero** — fuente + rutas de
> llamada + blast radius + flags de cobertura de tests en una llamada (trata la fuente que devuelve como YA
> leída, no la re-abras). Serena `find_referencing_symbols` para el chequeo **preciso** antes de renombrar o
> eliminar un helper (desambigua por clase). grep/Read solo para literales."** — regla real del `CLAUDE.md`.

Por qué es una *regla* y no una sugerencia: los ficheros clave tienen 4.000–6.000 líneas. Leerlos enteros
es caro (tokens) e impreciso. CodeGraph devuelve el símbolo, sus callers, sus tests y **qué se rompe al
cambiarlo** en un solo round-trip; Serena desambigua un símbolo homónimo por clase antes de un rename —
donde el `impact` plano de CodeGraph los mezclaría.

> **Dos grafos, dos dominios, dos tecnologías.** CodeGraph indexa el *código* (símbolos, llamadas, blast
> radius); el skill **`/kg`** — construido sobre **graphify**, no sobre CodeGraph — indexa la *memoria del
> proyecto* —tickets, "sharp edges", lecciones— para el paso *history-first*:
> qué se rompió antes en esta zona, qué invariantes no tocar. Los dos son deterministas y "primero, antes de
> grep". Detalle del segundo: [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md).

## Tabla de prevalencia

| Necesito… | Herramienta preferida | Por qué / regla |
|---|---|---|
| Survey: "qué es / quién depende / qué se rompe / ¿está testeado?" | **CodeGraph** `codegraph_explore` | Fuente + rutas de llamada + blast radius + cobertura en 1 consulta (incluye dispatch dinámico que grep no sigue). Trátala como YA leída. |
| Chequeo preciso antes de un rename/borrado | **Serena** `find_referencing_symbols` | **Obligatorio**; desambigua homónimos por clase (el `impact` de CodeGraph los mezcla). |
| Cuerpo de un símbolo / overview de un fichero de 5k líneas | **Serena** `find_symbol body=true` / `get_symbols_overview` | O la fuente que ya imprimió `codegraph_explore`. |
| Verificar el **contrato de salida** (lo que ve el consumidor) | **Playwright** / F12 en el navegador | Subir un doc → "Review & Import" → inspeccionar el JSON del `status endpoint`. El bug se reproduce ahí. |
| Verificar **dentro de lo que se despliega** | **Docker** (descargar/construir la imagen del runtime, montar el `src`, re-correr el repro) | Los tests en verde ≠ prueba de lo enviado. El deliverable se verifica en la **misma imagen** que corre en producción, y en la **etapa real de salida** (el *wrapper*, no una función interna `extract()`). |
| Diagnosticar causa raíz **barato** | **Oráculo determinista** (parser, validador, `_diag_*.py`) | Misma respuesta siempre, **sin inferencia** (coste menor, no cero — Claude lee la salida). Antes de gastar la tirada del LLM. |
| Diagnosticar entorno (logs, config de Lambda, colas) | **AWS CLI** (CloudWatch, `aws lambda get-function`, SQS/DLQ) | Herramienta de debugging de primera clase, no último recurso. |
| Docs de una librería externa | **Context7** | En vez de fiarse del corte de entrenamiento del modelo. |
| Estado de git / PRs para orientarse | **`gh` CLI**, `git branch -a`, `git log` | "status-first": no ramificar de la base equivocada. |
| "¿Qué tickets/lecciones rodean este área?" | **`/kg`** (grafo de tickets — [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md)) | "history-first": `/kg <ticket\|tema>` saca, **sin LLM**, los tickets relacionados + la zona de peligro a leer, ANTES de hacer grep en `data/changes/`. Es el análogo de CodeGraph para tickets — construido con **graphify**. |
| Trabajo genuinamente independiente en paralelo | **Subagentes** (`Task`: Explore/Plan/…) | Sin ensuciar el contexto principal. |

## El orden importa (barato → caro, determinista → probabilístico)

1. **Orientación:** markdown local (`STATUS.md`, ledgers) + `git`/`gh` + **`/kg`** (grafo de tickets: los tickets y la zona de peligro relacionados, sin LLM, antes de grep) — **sin inferencia** (coste menor, no cero).
2. **Navegación:** CodeGraph `codegraph_explore` (survey, 1 llamada) → Serena `find_referencing_symbols` (chequeo preciso antes de renombrar) — coste bajo, determinista.
3. **Diagnóstico:** oráculo determinista (parser/validador) — sin inferencia, reproducible.
4. **Verificación de entorno:** AWS CLI — read-only, determinista.
5. **Verificación del contrato:** Playwright/F12 — reproducir el síntoma en la salida real.
6. **Gate outbound:** reproducir en la **etapa real de salida** (el *wrapper*, no una función interna) y
   **dentro de la imagen desplegada** (Docker) — no basta con "los tests pasan".
7. **Solo al final:** la tirada del LLM (metered, probabilística) para verificar el fix acabado.

> La inversión clásica —"tirar del modelo para diagnosticar"— es justo lo que este orden evita: el modelo
> es caro y no determinista; úsalo para *verificar*, no para *diagnosticar*.

> **"Sin inferencia" ≠ "gratis" — y el coste se amortiza.** Las etapas deterministas (orientar, navegar,
> diagnosticar) no disparan la **tirada del modelo** (el recurso caro y no determinista), pero Claude sí lee
> su output: coste **menor y dirigido**, como un `grep`, no cero. El razonamiento caro se paga **una vez** al
> construir el grafo / el oráculo / la skill y se **amortiza** en cada uso — hay que entenderlo como
> **inversión**: sin inferencia por consulta, respuestas **deterministas y reproducibles** (mejor resultado),
> y razonamiento caro sustituido por lookup barato → **ahorro de tiempo y dinero** por tarea. Se paga una vez,
> se cobra en cada uso.

## Los oráculos deterministas (parser / validador / `_diag_*.py`) — qué son y dónde viven

Ojo con una confusión frecuente: **no todo lo determinista es una "skill".** Hay que separar dos naturalezas:

| | **Skills / tools MCP / slash commands** | **Oráculos** (parser · validador · `_diag`) |
|---|---|---|
| Qué es | Una **capacidad registrada** — Claude la auto-selecciona por su `description`, o la invocas con `/comando` | **Código normal** que el agente **escribe y corre con Bash** |
| Dónde vive | `~/.claude/skills/` · `.claude/commands/` · un servidor MCP | En el repo (`src/`, `tests/`) **o** gitignored bajo `data/changes/<ticket>/` |
| Ejemplos | `/kg`, `/kg-refresh`, Serena, CodeGraph, Playwright, Context7 | `_diag_pdf.py`, un check de esquema, correr el parser OOXML aislado |
| Naturaleza | Reutilizable, versionada, distribuible | Normalmente **de un solo uso**, por ticket, *throwaway* |

- **parser** — o las **funciones de parseo que ya viven en el extractor** (leer el OOXML / `ListText`, o el
  layout del PDF) invocadas **en aislamiento**, o una librería estándar (python-docx, pdfplumber). "Parser"
  es genérico: extraer **estructura** de forma determinista.
- **validador** — un check de **contrato/esquema**: un test de contrato (p. ej. identidad byte a byte de los
  prompts), o comprobar que el JSON tiene la forma del `status endpoint`. Vive en `tests/` o dentro de un `_diag`.
- **`_diag_*.py`** — la **convención del repo**: scripts de diagnóstico **gitignored** bajo
  `data/changes/<ticket>/`, de un solo uso, que **importan el código real** del extractor y corren **una sola
  etapa** para volcar el estado intermedio. El prefijo `_diag_` es la convención de nombre; no se registran en
  ningún sitio — se corren con `python data/changes/<ticket>/_diag_x.py`.

**El contraste, en una frase:** `/kg` **sí** es una skill registrada (por eso es un `/comando`); los oráculos
**no** — son código a medida que el agente teclea sobre la marcha y ejecuta con Bash. Los dos son
"deterministas", pero uno es una **capacidad instalada** y el otro un **artefacto del proyecto**.

## Permisos: el allowlist refleja esta prevalencia

El `settings.local.json` del proyecto es un allowlist **hand-curated** (cientos de reglas específicas, no
comodines): invocaciones exactas de pytest, operaciones git acotadas, `aws lambda/sts/configure`, y las
tools MCP concretas de Serena (`find_symbol`, `search_for_pattern`, `activate_project`, `find_file`),
CodeGraph (`codegraph_explore`) y Playwright (`browser_navigate`, `browser_console_messages`,
`browser_take_screenshot`, `browser_evaluate`).
`deny` y `ask` van vacíos porque el allowlist ya es la barrera — y el humano es dueño de las acciones
externas (push/PR/deploy no están en la lista).
