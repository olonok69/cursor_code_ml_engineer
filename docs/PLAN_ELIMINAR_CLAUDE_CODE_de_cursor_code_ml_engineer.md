# Plan — dejar `cursor_code_ml_engineer` como curso solo-Cursor

> Objetivo: que este repo sea el curso **solo de Cursor** (Parte 1 Cursor + Parte 2 metodología
> agnóstica + Parte 3 grafo de tickets) y la base sobre la que se sigue trabajando el volumen Cursor.
>
> **Estado: la fase A (borrado) YA ESTÁ HECHA** — ver abajo. Lo que queda son las fases B–F, que son
> renombrados + corrección de enlaces. Este documento está verificado contra el repo real (commit
> `55b958f`), con números de línea y conteos comprobados, no estimados.

---

## Contexto que conviene saber antes de tocar nada

- Este repo tiene **un único commit** (`55b958f "initial commit"`). No hay atajo de historia: a
  diferencia del repo hermano —donde todo el contenido Cursor entró en un solo commit y bastó un
  `git revert`— aquí **todo es manual**.
- Repo hermano: `github.com/olonok69/claude_code_ml_engineer`. Ya se limpió: todo su contenido Cursor
  se eliminó de allí y vive aquí.
- **Control cruzado hecho**: los 45 ficheros Claude Code borrados en la fase A existen **byte a byte**
  en el repo hermano (45/45 idénticos). No se ha perdido nada.

---

## A. Borrado de contenido Claude Code — ✅ HECHO (staged, pendiente de commit)

45 ficheros eliminados con `git rm`:

```
ejemplos/                                  (40 ficheros)
presentacion/Claude_Code_Presentacion.pptx
presentacion/Claude_Code_Presentacion_EN.pptx
presentacion/build_pptx.py                 (986 líneas)
docs/SETUP_CODEGRAPH_GSD.md                (instala GSD, que solo existe en Claude Code)
docs/DISENO.md                             (diseño del deck de Claude Code)
```

Estado resultante:

```
presentacion/   → Cursor_Presentacion.pptx · capture_kg_graph.py · kg_graph.png
docs/           → KNOWLEDGE_GRAPH.md · ai-agents-code-methodology/ · knowledge-graph/ · synchro/
```

`GUIA_PRESENTACION.md`, `GUIA_TECNICA.md`, `README_EN.md`, `GUIA_PRESENTACION_EN.md` y
`GUIA_TECNICA_EN.md` (versiones Claude Code / inglés) nunca estuvieron en este repo.

> ⚠️ **`presentacion/build_pptx.py` se ha borrado.** Era la única plantilla local para escribir el
> generador del deck Cursor (ver fase E). Sigue disponible en el repo hermano si hace falta.

### Enlaces que el borrado ha dejado rotos (se arreglan en las fases B y D)

| Fichero | Línea | Apunta a |
|---|---|---|
| `README.md` | 4 | `presentacion/Claude_Code_Presentacion.pptx` (borrado) |
| `README.md` | 31 | `./ejemplos/` (borrado) |
| `ejemplos_cursor/README.md` | 3 | `../ejemplos/` (borrado) |
| `docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md` | 62 | `../../ejemplos/metodologia/WORKFLOW.md` (borrado) |
| `docs/KNOWLEDGE_GRAPH.md` | 114 | `../ejemplos/metodologia/machine-sync.md` (borrado) |

Los dos últimos **se arreglan solos** al renombrar `ejemplos_cursor/` → `ejemplos/` en la fase B: esos
mismos ficheros existen dentro de `ejemplos_cursor/metodologia/`. Los tres primeros necesitan edición
manual (fase D).

> Nota: un comprobador de enlaces ejecutado ahora mismo **no** marca `README.md:31` ni
> `ejemplos_cursor/README.md:3` como rotos, porque la carpeta `ejemplos/` sigue existiendo en disco con
> residuos ignorados (ver aviso de la fase B). Aparecerán en cuanto la borres.

---

## B. Renombrar — ⚠️ NO ejecutar los `git mv` sueltos

Quitar el sufijo `_CURSOR`, que aquí ya no distingue nada. **El peligro está en que los renombrados
dejan colgadas 68 referencias internas**, comprobadas una a una:

| Fichero | refs a `ejemplos_cursor` |
|---|---|
| `GUIA_TECNICA_CURSOR.md` | 31 |
| `GUIA_PRESENTACION_CURSOR.md` | 19 |
| `README.md` | 13 |
| `ejemplos_cursor/automation/github-action-cursor.yml` | 1 |
| **Total** | **64** |

Más 4 referencias cruzadas a los nombres de las guías: `README.md:27,28`,
`GUIA_PRESENTACION_CURSOR.md:20`, `GUIA_TECNICA_CURSOR.md:4`.

### Orden obligatorio

**B0 primero** — corrige las cabeceras "volumen Claude Code" de los **3 ficheros** afectados **antes**
de los seds, o el paso B3 las corromperá en silencio (ver fase D, punto 1).

> ⚠️ **`ejemplos/` sigue existiendo en disco tras la fase A** y bloqueará el `git mv`. `git rm` borró
> los 40 ficheros versionados, pero quedan 4 residuos **ignorados por `.gitignore`**:
> ```
> ejemplos/metodologia/WORKFLOW.pdf        (*.pdf)
> ejemplos/metodologia/herramientas.pdf    (*.pdf)
> ejemplos/metodologia/machine-sync.pdf    (*.pdf)
> ejemplos/prompt-caching/.env             (.env — 126 bytes)
> ```
> Los 4 son copias idénticas de los que están en el repo hermano (`claude_code_ml_engineer`, mismo
> tamaño y fecha), así que borrarlos aquí no pierde nada. Revisa el `.env` antes por si guardas algo
> real en él, y luego: `rm -rf ejemplos/`.

```bash
# B1) Renombrar. Requiere que `ejemplos/` NO exista (ver aviso de arriba),
#     o el `git mv` falla en seco con "destination already exists".
git mv GUIA_PRESENTACION_CURSOR.md GUIA_PRESENTACION.md
git mv GUIA_TECNICA_CURSOR.md GUIA_TECNICA.md
git mv ejemplos_cursor ejemplos

# B2) Barrido de las 64 referencias a la carpeta
sed -i 's#ejemplos_cursor#ejemplos#g' \
  README.md GUIA_PRESENTACION.md GUIA_TECNICA.md \
  ejemplos/automation/github-action-cursor.yml

# B3) Barrido de las 4 referencias cruzadas entre guías
sed -i 's#GUIA_PRESENTACION_CURSOR\.md#GUIA_PRESENTACION.md#g; s#GUIA_TECNICA_CURSOR\.md#GUIA_TECNICA.md#g' \
  README.md GUIA_PRESENTACION.md GUIA_TECNICA.md
```

> `sed -i` funciona en Git Bash (disponible en esta máquina). En PowerShell usa
> `(Get-Content f) -replace 'a','b' | Set-Content f -Encoding utf8`.

### Sobre `CURSOR_ADAPTATION.md` — recomendación: **no renombrarlo**

El fichero está escrito literalmente como "cómo adaptar la metodología de Claude Code a Cursor". Ese
nombre sigue siendo honesto y útil para quien llegue aquí y se pregunte de dónde viene el método.
Renombrarlo a `ADAPTATION.md` obligaría además a actualizar sus referencias en `GUIA_PRESENTACION.md`,
`GUIA_TECNICA.md`, `docs/ai-agents-code-methodology/README.md` y las 5 guías meta. Coste sin beneficio.

---

## C. Corregir las rutas `presentacion_cursor/` (carpeta que nunca existió)

Los 3 documentos Cursor asumían una carpeta `presentacion_cursor/` separada; el repo usa la carpeta
compartida `presentacion/`. Son 6 apariciones exactas:

| Fichero | Líneas |
|---|---|
| `README.md` | 29, 30, 55, 61 |
| `GUIA_PRESENTACION.md` (ex-`_CURSOR`) | 4 |
| `GUIA_TECNICA.md` (ex-`_CURSOR`) | 649 |

```bash
sed -i 's#presentacion_cursor/#presentacion/#g; s#presentacion_cursor#presentacion#g' \
  README.md GUIA_PRESENTACION.md GUIA_TECNICA.md
```

`presentacion/kg_graph.png` **se queda**: lo usaba el deck de Claude Code y lo sigue usando el deck
Cursor. `presentacion/capture_kg_graph.py` (el que lo genera) también se queda.

---

## D. Tres correcciones que ningún `sed` detecta

**1. Las cabeceras "volumen Claude Code" — la más importante, y afecta a 3 ficheros, no solo al
README.** Los tres enlazan al repo hermano con **rutas relativas locales**:

| Fichero | Línea | Enlace roto | En qué se convierte tras la fase B |
|---|---|---|---|
| `README.md` | 3, 4 | `./README.md`, `./GUIA_PRESENTACION.md`, `./GUIA_TECNICA.md` | apuntan a las guías **Cursor de este repo** |
| `GUIA_PRESENTACION_CURSOR.md` | 7 | `./GUIA_PRESENTACION.md` ("contrapartida directa … (Claude Code)") | **apunta a sí mismo** |
| `GUIA_TECNICA_CURSOR.md` | 7 | `./GUIA_TECNICA.md` ("Volumen Claude Code:") | **apunta a sí mismo** |

Hoy están rotos; tras el renombrado dejan de estarlo y pasan a estar **silenciosamente mal**, que es
peor. Sustituir en los tres por URLs absolutas al repo hermano, p. ej.:

```markdown
> **Volumen Claude Code:** el curso hermano
> [`claude_code_ml_engineer`](https://github.com/olonok69/claude_code_ml_engineer) —
> mismo curso, mismo método, otra herramienta. Este repo es el **volumen Cursor**.
```

En las dos guías el enlace es a un fichero concreto, así que la URL debe serlo también:
`https://github.com/olonok69/claude_code_ml_engineer/blob/master/GUIA_PRESENTACION.md` (resp.
`GUIA_TECNICA.md`).

**2. `README.md:31`** — "…mismo mapeo que [`ejemplos/`](./ejemplos/)" se vuelve autorreferencial tras
el rename (la fila describe `ejemplos/` y remite a `ejemplos/`). Quitar la coletilla final o cambiarla
por una referencia al repo hermano.

**3. `ejemplos/README.md:3`** (ex-`ejemplos_cursor/README.md`) — "Misma estructura que
[`ejemplos/`](../ejemplos/) (curso Claude Code), reescrita para **Cursor**". Mismo problema: apuntar al
repo hermano por URL absoluta, o reescribir la frase.

---

## E. `presentacion/build_pptx_cursor.py` — no existe

El repo tiene `Cursor_Presentacion.pptx` (36 slides) ya generado pero **sin script generador**, y
`README.md:30,61` lo referencian como si existiera. Tres salidas:

- **(a) Recomendada — 2 líneas de coste.** Quitar las referencias al script en `README.md:30` (fila de
  la tabla) y `README.md:61` (bloque "Regenerar el deck"), y dejar el `.pptx` como artefacto no
  regenerable. Es lo honesto y no deja el repo prometiendo algo que no tiene.
- **(b)** Escribirlo desde cero usando `presentacion/build_pptx.py` del repo hermano como plantilla
  (986 líneas) más el contenido del deck actual. Es trabajo real, y el deck regenerado **no será
  idéntico** al `.pptx` actual salvo que se acepte sustituirlo por la nueva salida.
- **(c)** Recuperarlo de la sesión donde se generó, si se conserva.

El bloque de `README.md:57-63` queda así con la opción (a) — los otros tres comandos sí funcionan:

```bash
pip install python-pptx pillow
python ejemplos/metodologia/render_flow.py       # -> flow.png (flujo de 11 etapas)
python ejemplos/subagents/render_agents.py       # -> agents.png (subagent vs Background/Cloud Agent)
python presentacion/capture_kg_graph.py          # -> kg_graph.png (requiere playwright)
```

---

## F. Opcional — contenido compartido con sintaxis Claude Code

Solo un fichero lo necesita de verdad:

| Fichero | Qué pasa | Qué hacer |
|---|---|---|
| `docs/KNOWLEDGE_GRAPH.md` | **17 usos de la sintaxis `/kg`, `/kg-refresh`** (slash-commands, estilo Claude Code) | Sustituir por la sintaxis Cursor (`kg` / `kg-refresh` como skills, sin barra) — **ya está redactada en `GUIA_TECNICA.md` §16, línea 592 y siguientes**: copiar de ahí. Alternativa mínima: una nota al principio aclarando la equivalencia. |
| `docs/ai-agents-code-methodology/{README,START_HERE,TRANSFER_AND_BOOTSTRAP,PACKAGE_MANIFEST,NEW_REPO_CONFIGURATION_PLAN}.md` | Describen el kit portable mencionando Cursor **y** Copilot como destinos | Dejar como están: es documentación del kit portable en sí, agnóstica por diseño, no material didáctico de Claude Code. A lo sumo, una frase al principio del README aclarando que aquí Cursor ya es la casa. |
| `COPILOT_ADAPTATION.md` + `templates/COPILOT_WORKING_AGREEMENT_TEMPLATE.md` | Adaptación a un tercer agente | Se quedan — misma decisión que en el repo hermano: es la prueba de portabilidad del método. |

No existe aquí un bloque "Fast path — Claude Code" que borrar: el kit de transferencia nunca tuvo
instrucciones de "cómo llegar a Claude Code", solo salidas hacia Cursor/Copilot.

---

## G. Verificación (ejecutar TODO antes del commit)

```bash
# 1. No debe quedar NINGUNA referencia a lo borrado en la fase A
grep -rn "Claude_Code_Presentacion\|build_pptx\.py\|DISENO\.md\|SETUP_CODEGRAPH_GSD" \
  --include="*.md" --include="*.yml" . | grep -v PLAN_ELIMINAR
# esperado: vacío

# 2. No debe quedar ningún rastro de los nombres viejos
grep -rn "ejemplos_cursor\|_CURSOR\.md\|presentacion_cursor" \
  --include="*.md" --include="*.yml" . | grep -v PLAN_ELIMINAR
# esperado: vacío

# 3. Comprobador de enlaces markdown, resolviendo cada ruta relativa contra SU propio fichero.
#    (Probado en este repo — no uses `grep -P`, falla aquí con "supports only unibyte and UTF-8 locales")
grep -rnoE '\]\(\.{1,2}/[^)#]+\)' --include="*.md" . | grep -v PLAN_ELIMINAR | \
  while IFS=: read -r f n link; do p="${link#](}"; p="${p%)}"; d=$(dirname "$f"); \
    [ -e "$d/$p" ] || echo "ROTO  $f:$n -> $p"; done

# Salida actual (11 enlaces rotos). Al terminar B–E deben quedar 0, salvo el de `examples/`,
# que es un roto preexistente ajeno a este trabajo:
#   ROTO  ./examples/Super_Resolution_Tecnicas.md:3 -> ./Zoom_Resize_Image.ipynb

# 4. Los generadores que se quedan siguen ejecutando
python ejemplos/metodologia/render_flow.py
python ejemplos/subagents/render_agents.py

# 5. Commit
git add -A
git commit -m "Quitar contenido Claude Code: este repo pasa a ser la base del curso Cursor"
git push origin master
```

---

## H. A partir de aquí

Aplicadas B–E, el repo queda con la estructura de tres partes enteramente en clave Cursor:
`README.md`, `GUIA_PRESENTACION.md`, `GUIA_TECNICA.md`, `ejemplos/` (ex-`ejemplos_cursor/`),
`presentacion/Cursor_Presentacion.pptx`, y el `docs/knowledge-graph/` + `docs/synchro/` compartidos.
Cualquier trabajo nuevo del volumen Cursor se hace directamente sobre este repo como base.

Decide también si este propio documento (`docs/PLAN_ELIMINAR_CLAUDE_CODE_…md`) debe quedarse en el
repo o excluirse del commit: hoy está **sin trackear**, así que un `git add -A` lo incluiría.
