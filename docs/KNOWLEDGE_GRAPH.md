# Grafo de conocimiento de tickets — "CodeGraph, pero para tickets y lecciones"

> Patrón real (sanitizado) construido sobre un proyecto vivo. La idea: igual que **CodeGraph** indexa el
> *código*, este skill indexa la **memoria del proyecto** — los writeups por ticket, las "sharp edges", los
> runbooks y las notas de memoria — en un **grafo navegable** que Claude consulta *antes* de tocar nada.
> Se invoca con el skill **`/kg`**; se reconstruye con **`/kg-refresh`**. Todo vive bajo `data/` (gitignored):
> los nodos llevan nombres internos, así que **nunca sale del repo**.

Complementa a CodeGraph, no lo sustituye: **CodeGraph = el *qué/cómo* del código** (símbolos, llamadas,
blast radius); **este grafo = el *por qué* y el *qué se rompió antes*** (qué tickets se tocan, qué zona de
peligro rodea un área, cómo se conecta un ticket con otro).

---

## 1. El problema que resuelve

En un repo con cientos de writeups por ticket (`data/changes/sst-*/`), un bug "nuevo" casi siempre tiene
**contexto previo que restringe el fix**: un invariante que no debes romper, un ticket que ya arregló algo
parecido, una regresión documentada. Encontrarlo a mano = recordar que existe y hacer `grep`. El grafo lo
**hace explícito**: una consulta devuelve los tickets relacionados + el clúster de la zona de peligro.

Ejemplo real: para un fix de "fin de carta", `/kg get_letter_end` devuelve al instante la zona de peligro
completa (los 5-6 tickets que comparten ese código) — justo lo que de otro modo tendrías que *recordar*
para no regresar.

## 2. El corpus (qué entra al grafo)

Un **manifest reproducible y diffeable** (`manifest.txt`) enumera exactamente qué ficheros entran, en vez de
un glob que cambia en silencio. Reglas de pertenencia:

| Grupo | Regla |
|---|---|
| Primario por ticket | `data/changes/sst-*/sst-*.md` |
| Fallback por ticket | para carpetas sin `sst-NNNN.md`, el `.md` más grande (determinista) |
| Estado de extractores | `data/changes/extractors/*/process.md` |
| Hubs | `STATUS.md`, `SHARP_EDGES.md`, `FOLLOWUPS.md`, `PLAYBOOK.md`, … |
| Orientación | `CLAUDE.md`, `CODE_NAVIGATION.md` |
| Ops | los runbooks de `machine-sync` |
| Memoria | `~/.claude/…/memory/*.md` |

Exclusiones duras: binarios (`.png`/`.json`/`.docx`), copias-stale de un tarball de viaje (`payload/`),
handovers que solo repiten el ticket. **Densidad sin conocimiento nuevo = ruido.**

## 3. El pipeline de construcción (`/kg-refresh`)

Envoltorio determinista alrededor de una pasada de extracción semántica con subagentes:

```
kg_refresh.sh prepare   # build_manifest -> stage _corpus/ -> copiar a un scratch fuera del repo
/graphify <scratch>     # detect -> extracción por subagentes (general-purpose) -> clustering -> HTML/JSON
kg_refresh.sh finalize  # copiar artefactos a output/ + sincronizar la copia in-place + leak-check
```

- **Gotcha que sostiene todo:** `graphify` respeta `.gitignore`, y **todo `data/` está gitignored** →
  correr el detector *in situ* encuentra **0 ficheros**. Solución: montar el corpus en un **scratch fuera del
  repo** (`~/.cache/…`), correr allí, copiar los 3 artefactos de vuelta a `data/knowledge-graph/output/`.
- **Reconstrucción completa** cada vez; ~5 subagentes `general-purpose` en paralelo (por eso `/kg-refresh` es
  un skill, no un script: el paso semántico es un paso de Claude).
- **Leak-check** en `finalize`: aborta si algún artefacto del grafo aterrizó fuera de `data/`.

Salida: `output/graph.json` (NetworkX node-link, **aristas tipadas** con `relation` + `confidence`),
`output/graph.html` (interactivo), `output/GRAPH_REPORT.md` (god-nodes, conexiones sorprendentes, preguntas).

## 4. La superficie de consulta (`/kg`) — determinista, sin LLM

El motor ya existe en `graphify`: `explain` (vecinos) y `path` (camino más corto) leen `graph.json`
**directamente, sin LLM** — eso *es* el análogo de CodeGraph. El skill `/kg` es un envoltorio fino
(`kg_query.sh`) que fija el intérprete + la ruta del grafo y normaliza el token:

```bash
/kg <ticket-o-tema>     # vecinos de un nodo    (graphify explain)  ← el uso más común
/kg <A> <B>             # camino más corto A<->B (graphify path)
/kg find <substr>       # descubrir el nombre exacto de un nodo
```

Los tokens se emparejan de forma difusa: `SST-1234`, `sst-1234`, `get_letter_end`, `"fin de carta"` resuelven.
Si un tema no resuelve, `find <substr>` da el id exacto para reintentar.

> **"Sin LLM" no es "gratis" — es coste menor y amortizado.** La inferencia cara (la extracción con
> subagentes) se paga **una vez** en `/kg-refresh`; cada consulta `explain`/`path`/`find` es luego un
> algoritmo determinista que lee `graph.json` → **cero inferencia**. El único coste por consulta es que el
> agente lee un output pequeño (como un `grep`): menor y dirigido, no cero. Visto así, construir el grafo es
> una **inversión** — sin inferencia por consulta, resultados **deterministas y reproducibles**, y
> razonamiento caro sustituido por lookup barato → mejor rendimiento y ahorro de tiempo/dinero por tarea.

## 5. Enganchado al flujo de trabajo (el objetivo real)

Un grafo que nadie consulta no vale. La regla **history-first** del `CLAUDE.md` ahora dice: **antes de diseñar
un fix cerca de un área conocida, corre `/kg <ticket-o-tema>`** — *antes* de hacer `grep` en `data/changes/`.
Una llamada determinista te pone delante la lista de lectura (tickets relacionados + zona de peligro); luego
lees el writeup del ticket y la entrada de "sharp edges" antes de escribir. El grafo apunta a *qué leer*, no
lo sustituye.

Honestidad sobre lo que aporta: la ganancia es **recall en zonas densas** (fin-de-carta, limpieza de títulos,
numeración de subsecciones) — ahí ahorra grep y captura 1 ticket relevante que se te habría escapado. En un
área aislada aporta poco. Aristas `EXTRACTED` = fiables; `INFERRED`/`semantically_similar_to` = pistas a
verificar, no hechos.

## 6. Viaje entre máquinas (main ⇄ portátil)

El grafo es un **artefacto derivado** (función pura del corpus) → **nunca viaja de vuelta**: la máquina que
tenga el corpus actual lo reconstruye. Dos subcomandos cierran el círculo (la memoria no viaja en el delta
por defecto):

```bash
# Bare metal (portátil nuevo): instala tooling + fija intérprete + verifica /kg
bash data/knowledge-graph/kg_refresh.sh bootstrap
# Antes de volver: la memoria no va en el delta -> parquearla bajo data/ para que viaje
bash data/knowledge-graph/kg_refresh.sh snapshot-memory
# En la principal, al aterrizar el delta: fusionar memoria de vuelta (con backup) y reconstruir
bash data/knowledge-graph/kg_refresh.sh restore-memory  &&  /kg-refresh
```

Detalle completo del kit de viaje en [`../ejemplos/metodologia/machine-sync.md`](../ejemplos/metodologia/machine-sync.md).

## 7. Confidencialidad

Los nodos llevan nombres internos → **solo interno**; todo el árbol vive bajo `data/` (gitignored) y **nunca
se commitea**. Una versión sanitizada (nombre→rol) para compartir fuera sería un entregable aparte, con su
propia pasada de anonimización.

---

## Mapa de piezas

| Pieza | Qué es |
|---|---|
| `/kg` (skill) | consulta: `explain` / `path` / `find` — determinista |
| `/kg-refresh` (skill) | reconstruye el grafo (prepare → `/graphify` → finalize) |
| `kg_query.sh` | envoltorio de `graphify explain`/`path` + `find` en python |
| `kg_refresh.sh` | bookends deterministas + `snapshot-memory` / `restore-memory` / `bootstrap` |
| `build_manifest.py` / `stage_corpus.py` | enumera y monta el corpus |
| `data/knowledge-graph/output/` | `graph.json` + `graph.html` + `GRAPH_REPORT.md` |

> En una frase: **el grafo es el mapa; el trabajo del agente tras el pipeline es ser el guía.**
> Reconstruible, consultable en 1 llamada, enganchado a la regla "primero la historia".
