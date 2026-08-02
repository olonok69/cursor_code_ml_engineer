# CodeGraph — inteligencia de código local

Herramienta *local-first* que indexa tu código con **tree-sitter** en un **grafo SQLite** de símbolos,
aristas y ficheros, y lo expone a Claude Code como servidor MCP.
Repo: https://github.com/colbymchenry/codegraph · Docs: https://colbymchenry.github.io/codegraph/

## Qué indexa (determinista, del AST — no resumido por un LLM)

- **Símbolos:** funciones, clases, métodos, tipos, rutas, componentes.
- **Aristas:** llamadas, imports, herencia, referencias, relaciones de framework.
- **Ficheros:** estructura + búsqueda full-text.

Todo vive en `.codegraph/` (una base SQLite local). **Sin servicios externos ni API keys.**

## Cómo funciona, a alto nivel (tres piezas)

1. **Indexar** (`codegraph init`) — recorre el repo y parsea cada fichero con **tree-sitter**, un parser
   sintáctico que entiende la gramática de cada lenguaje y produce el AST. No ejecuta código ni llama a
   ningún LLM: análisis puramente sintáctico. De cada AST extrae nodos (símbolos) y aristas (llamadas,
   imports, herencia, referencias).
2. **Guardar el grafo** — todo se escribe en la SQLite de `.codegraph/`. De ahí las propiedades: local,
   determinista (mismo código → mismo grafo) y barato de refrescar (`sync` re-parsea solo lo cambiado).
3. **Consultar** — `codegraph_explore` no "lee código": **camina el grafo**. Localiza el nodo, sigue las
   aristas hacia arriba (callers) y hacia abajo (callees), calcula el blast radius transitivamente, cruza
   con los tests para los flags de cobertura, y devuelve todo eso más la fuente literal en una respuesta.

La analogía: es lo que hace tu IDE por debajo en "Find usages" / "Go to definition" — un índice
precomputado — pero empaquetado para que un **agente** lo consulte por MCP. Y es el mismo patrón de ROI
del grafo de tickets (`/kg`): **parsear una vez al indexar, recuperar mil en cada consulta** — CodeGraph
sin inferencia ni siquiera en el build; graphify con inferencia solo en el build.

## "Blast radius", en palabras sencillas

Es la "onda expansiva" de tocar un símbolo: **todo lo que se puede romper si lo cambias**. CodeGraph
recorre el grafo de llamadas hacia atrás y responde: *"a esta función la llaman estos 7 sitios; esos
alimentan a estos otros 3; de todo el conjunto, estos 4 tienen tests y estos 6 no"*. Antes de editar una
línea ya sabes si tocas una pieza aislada o un pilar del que cuelga medio sistema. Sin el grafo, esa
pregunta se responde con grep — que encuentra el *texto* pero no sigue el dispatch dinámico ni te dice
quién llama a quién. Matiz: el blast radius de CodeGraph es *plano* (mezcla métodos homónimos); el
veredicto fino pre-rename lo da Serena `find_referencing_symbols` (ver tabla más abajo).

## Qué problema resuelve

El bucle habitual "grep → abrir fichero → seguir el import → volver a grepear" gasta muchísimo contexto.
CodeGraph lo reemplaza por **una consulta**: `codegraph_explore` devuelve el **código fuente verbatim y
numerado** de los símbolos relevantes, **más las rutas de llamada** entre ellos (incluidos saltos de
dispatch dinámico que grep no puede seguir) y un resumen del **blast radius** (qué se rompería al cambiar).

Según sus benchmarks, dar acceso a CodeGraph a un agente produjo **58% menos tool calls**, **22% más
rápido** y prácticamente eliminó las lecturas de fichero.

## CLI

```bash
codegraph init        # crea el índice .codegraph/ y lo construye (decisión explícita del usuario)
codegraph sync        # re-indexa incremental tras editar (en WSL2 /mnt, hazlo a mano: el watcher pierde eventos)
codegraph watch       # re-indexa en vivo en background (poco fiable en /mnt)
codegraph explore "<símbolo o pregunta>"   # fuente + rutas + blast radius + cobertura, en 1 round-trip
codegraph impact|callers|node <símbolo>    # blast radius / callers / 1 símbolo + su trail
codegraph install --target=claude --location=global   # escribe la config MCP (--location: global|local, NO user)
codegraph serve --path <repo> --mcp        # arranca el server MCP; --path fija el proyecto POR DEFECTO
codegraph status                            # estado del índice (nodos, aristas, frescura)
```
Desde Claude Code (MCP), la tool **`codegraph_explore`** hace lo mismo en un solo round-trip. El server MCP
**no tiene proyecto por defecto** salvo que lo arranques con `--path <repo>`: fíjalo y no necesitas pasar
`projectPath`; pásalo solo para consultar **otro** repo indexado (útil en un monorepo o con varios repos —
p. ej. ya indexamos `monolith` y `frontend`). Si un repo no tiene `.codegraph/`, no se usa: indexar es
decisión del usuario. Trata la fuente que imprime como **ya leída** — no re-abras ese fichero (ahí está el
ahorro real de tokens).

## CodeGraph vs. Serena vs. grep — cuándo cada uno

| Pregunta | Herramienta |
|---|---|
| **Survey (primero):** "dame fuente + callers + qué se rompe + ¿está testeado?" | **CodeGraph** `codegraph_explore` (fuente + rutas + blast radius + cobertura en 1 llamada) |
| **Chequeo preciso antes de un rename/borrado** | **Serena** `find_referencing_symbols` — desambigua homónimos por clase (el `impact` plano de CodeGraph los mezcla) |
| "Overview de símbolos" / "cuerpo de esta función" | **Serena** `get_symbols_overview` / `find_symbol` (o la fuente que ya imprimió `explore`) |
| Búsqueda textual simple de una cadena / literal | grep / `search_for_pattern` |

En el flujo real (ver [`../metodologia/EJEMPLO_REAL.md`](../metodologia/EJEMPLO_REAL.md)), CodeGraph entra
**primero** en la **etapa 4 (investigar)** para el survey (símbolos + rutas de llamada + cobertura, sin leer
los ficheros de 5k líneas enteros); Serena `find_referencing_symbols` hace el chequeo preciso justo antes de
tocar. CodeGraph responde *"qué es y cómo se conecta"*; Serena, *"quién referencia exactamente esto"*.
