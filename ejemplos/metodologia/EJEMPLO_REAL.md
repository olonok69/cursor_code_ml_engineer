# Un ejemplo real, de principio a fin

> Un caso concreto (sanitizado) de cómo se trabaja un bug con Claude Code siguiendo el flujo de 11 etapas
> y las herramientas de [`herramientas.md`](./herramientas.md). Los detalles de cliente/ticket están
> generalizados; la mecánica es la real.

## El síntoma

QA reporta: *"En un documento, el campo **'ley aplicable'** aparece vacío en la UI, pero en el PDF está
claramente escrito."* Adjunta el documento y el JSON del `status endpoint` (el contrato de salida).

---

### 1 · Orientar (history-first Y status-first)

**Claude, primero, sin tocar código:**
- **`/kg "fin de provisión"`** (grafo de tickets, determinista, sin LLM) → devuelve al instante la **zona de
  peligro**: los tickets que comparten ese código (el corte de fin de provisión, el look-ahead) + el
  `SHARP_EDGES.md` entry *"el corte se aplica en 3 sitios; no unificar."* Eso es lo que **restringe** el fix
  — y lo que, sin el grafo, tendrías que *acordarte* de buscar a mano. Es el paso *history-first* antes de grep.
- Lee el writeup del ticket que `/kg` señaló (`data/changes/<ticket>/<ticket>.md`) para el *porqué* completo,
  y `STATUS.md` para el estado en vuelo.
- `git branch -a` + `gh pr list` → confirma que no hay un PR abierto tocando este extractor y cuál es la
  base correcta para ramificar.

> Sin este paso, el error típico es ramificar de la base equivocada o duplicar trabajo en vuelo.

### 2 · Triaje inbound — ¿el síntoma es real en el contrato?

Abre el JSON del `status endpoint` que aportó QA y busca el campo. **Está vacío en el JSON** → el Lambda
es responsable → seguimos. (Si hubiera estado *presente* en el JSON, el bug sería aguas abajo —backend o
frontend— y la respuesta correcta sería **push back con evidencia, no escribir código**.)

Para reproducirlo en vivo, con **Playwright**: navegar a la UI, subir el documento, "Review & Import
Information", e inspeccionar la respuesta (`browser_evaluate` / consola F12). El campo vacío se confirma
**en la salida real**, no en una función interna.

### 3 · Regresión vs. pre-existente

Reproduce sobre el estado *previo*: re-extrae el fixture en la base sin el cambio en curso. El campo ya
salía vacío antes → **es pre-existente**, no lo causamos nosotros. Eso cambia la historia que se cuenta a
QA y el scope, pero sigue mereciendo el fix.

### 4 · Investigar — oráculo determinista barato primero

Los extractores tienen ~5.000 líneas. **No** se abren enteros:
- **Serena** `get_symbols_overview` sobre el extractor de PDF → lista de símbolos.
- **Serena** `find_symbol body=true` sobre la función que detecta el fin de la provisión "ley aplicable".
- **CodeGraph** `codegraph_explore "detección fin de provisión ley aplicable"` → devuelve la fuente + las
  **rutas de llamada** hasta ella + el blast radius (qué más depende de ese helper).

Ahora el **oráculo determinista**: un pequeño `_diag_pdf.py` que corre solo el parser de layout (sin LLM)
sobre el documento e imprime los bloques de texto y sus coordenadas. Revela la causa raíz: la provisión
desborda a una segunda columna y el detector de "fin" corta antes de tiempo. **Misma respuesta cada vez,
coste bajo y determinista (sin inferencia), y ni una llamada al LLM todavía.**

### 5 · Plan — proponer, no proceder

Claude presenta el plan: *"Causa: el look-ahead de fin de provisión asume una sola columna. Fix: detectar
el régimen multi-columna por una propiedad estructural (no por el texto 'ley aplicable') y extender el
look-ahead. Alternativa descartada: keying en el string del cliente (viola 'soluciones genéricas')."*
El humano **aprueba** antes de que se escriba código. La opción rechazada queda escrita.

### 6 · Implementar — TDD, mínimo

- Test **RED** primero: `tests/test_tck_1234_governing_law_overflow.py` con el fixture → falla por el
  motivo correcto (el campo sale vacío).
- El código **mínimo** que lo pone en verde, keyed en la propiedad estructural (multi-columna), no en el
  valor reportado.

### 7 · Verificar — contra el contrato, con evidencia

- Suite scoped del defecto → GREEN.
- Batería de regresión canónica → los documentos de referencia salen **byte-idénticos** (prueba **no-op**:
  el fix no toca lo que no debe).
- **Gate outbound — tres comprobaciones:**
  1. **Reproducir en la etapa real de salida:** a través del **wrapper** que reconstruye el contrato, no de
     `extract()`. (Un fix en la función interna lo puede descartar el rebuild del wrapper y verse "correcto"
     en local mientras la salida enviada sigue mal.)
  2. **Coincidencia local:** el JSON de esa etapa tiene la forma del `status endpoint` con "ley aplicable"
     **ya relleno**. *Sin este JSON local, no hay handover.*
  3. **Dentro de la imagen desplegada:** descargar (o construir) la **misma imagen** que corre el runtime,
     montar el `src` arreglado y re-correr el repro → byte por byte igual que en local. *Los tests en verde
     no son prueba de lo que se despliega.*

### 8 · Documentar

- `data/changes/tck-1234/tck-1234.md` — causa raíz → fix → evidencia (los comandos y su salida).
- Update de `STATUS.md` (una línea, newest-first).
- `qa_acceptance_criteria.md` — checks PASS/FAIL con los strings exactos que mirará QA, lista de documentos
  a probar y un "NO en scope de verificación".
- Nota de handover. Cada cosa escrita **una vez**, en su sitio.

### 9 · Sanitizar

Escaneo de las líneas **añadidas** del diff staged: sin nombre de cliente, sin el ID de ticket dentro del
código, sin secretos, sin "generado por el agente". (Filtrando solo añadidas: un diff naive matchea
también las borradas.)

### 10 · Handoff — el humano hace lo externo

Claude deja la rama `fix/tck-1234-governing-law-overflow` lista y el handover escrito. **No** hace push ni
abre el PR: eso lo hace el humano (o un tool conducido por él, p. ej. Cursor), que aplica el naming
convenido (`fix: TCK-1234 — …`, PR title `TCK-1234 …`, squash merge). El artefacto entregado lee como
trabajo del autor humano.

### 11 · Revisión automática + persistir

Un review-bot comenta que el nuevo look-ahead asume que la 2ª columna empieza a la derecha. Se **triagea
como un hallazgo humano**: se reproduce, se añade el test de regresión que faltaba (columna a la
izquierda), se arregla, se re-verifica. Al cerrar: `FOLLOWUPS.md` actualizado y la lección
("fin-de-provisión debe detectar el régimen de columnas, no asumir una") va al `PLAYBOOK.md` para no
re-caer en el mismo agujero.

---

## Qué herramienta entró en cada etapa

| Etapa | Herramienta |
|---|---|
| Orientar | **`/kg`** (grafo de tickets → zona de peligro) · `STATUS.md`/ledgers · `git` · `gh` |
| Triaje / contrato | **Playwright** / F12 sobre el `status endpoint` |
| Investigar | **Serena** (símbolos) · **CodeGraph** (rutas + blast radius) · **oráculo determinista** (`_diag_*.py`) |
| Implementar/verificar | pytest (RED→GREEN, scoped + regresión) · re-extracción local del contrato (vía **wrapper**) · **Docker** (repro dentro de la imagen desplegada) |
| Handoff | el humano / Cursor (push, PR, deploy) — **nunca el agente** |

## La moraleja

Ninguna etapa dice "pídele al LLM que lo arregle". La potencia del modelo se canaliza a través de **gates
deterministas** (contrato vía wrapper, oráculo, batería de tests, prueba no-op, verificación en la imagen
desplegada, escaneo de sanitización) y el humano conserva las decisiones y las acciones externas. Eso es lo
que convierte capacidad bruta en salida fiable.
