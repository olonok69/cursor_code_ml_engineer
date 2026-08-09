# Un ejemplo real, de principio a fin (Cursor)

> Mismo caso sanitizado que en el curso Claude Code; el agente orquestador es **Cursor**.
> Tools MCP y gates idénticos en rol.

## El síntoma

QA: *"El campo **'ley aplicable'** aparece vacío en la UI, pero en el PDF está escrito."*
Adjunta documento + JSON del `status endpoint`.

---

### 1 · Orientar

**Cursor, primero, sin tocar código:**
- Skill **`kg`** con tema `"fin de provisión"` (o `kg_query.sh` / STATUS fallback) → zona de peligro +
  sharp edge *"el corte se aplica en 3 sitios; no unificar."*
- Lee el writeup señalado y `STATUS.md`.
- `git branch -a` + `gh pr list` → base correcta, sin PR duplicado.

### 2 · Triaje inbound

JSON del contrato: campo **vacío** → responsabilidad del Lambda. Playwright confirma en la UI real.

### 3 · Provenance

Repro en baseline previo → **pre-existente**. Cambia el relato a QA; el fix sigue mereciendo hacerse.

### 4 · Investigar

- CodeGraph `codegraph_explore` (survey + blast radius) — no abrir el extractor de 5k líneas entero.
- Serena para símbolos / refs precisas.
- `_diag_pdf.py` (oráculo): layout sin LLM → desborde a 2ª columna. **Cero tiradas de modelo para diagnosticar.**

### 5 · Plan

**Plan mode:** opciones + trade-offs; fix keyed en propiedad estructural (multi-columna), no en el string
del cliente. Humano aprueba. Opción rechazada documentada.

### 6 · Implementar

Agent mode: test RED → código mínimo → GREEN.

### 7 · Verificar

Scoped + regresión byte-idéntica (no-op) + outbound en **cinco checks**: validar el instrumento ·
wrapper · JSON local (lista de miembros, no total) · imagen Docker · mirar la salida.

### 8 · Documentar

Write-once: ticket note, STATUS, QA acceptance, handover.

### 9 · Sanitizar

Skill `sanitise-diff` sobre líneas añadidas del staged diff.

### 10 · Handoff

Rama + handover listos. **No** push/PR salvo que el humano lo pida explícitamente
(hook `block_external` / rules). En el flujo Claude Code original, a menudo “Cursor hacía el push”;
aquí Cursor *es* el agente → el gate humano sigue siendo obligatorio.

### 11 · Review bot + persistir

Triage del bot; test extra; lección → `PLAYBOOK.md`; `kg-refresh` si el grafo debe ver el ticket nuevo.

---

## Herramienta por etapa

| Etapa | Herramienta |
|---|---|
| Orientar | Skill **`kg`** · STATUS · git · gh |
| Triaje | Playwright / F12 |
| Investigar | CodeGraph · Serena · `_diag_*.py` |
| Plan | Plan mode |
| Implementar / verificar | pytest · wrapper · Docker |
| Sanitise / handoff | `sanitise-diff` · humano (+ hook) |

## Moraleja

Ninguna etapa es “pídele al LLM que lo arregle”. Los gates deterministas canalizan al modelo.
El producto (Claude Code vs Cursor) cambia; la disciplina no.
