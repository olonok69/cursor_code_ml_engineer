# El flujo real de trabajo con Claude Code

> Esto **no es una plantilla ideal**: es el flujo que usamos de verdad en un proyecto en producción,
> sujeto a revisión constante. Está sanitizado (sin nombres de cliente, IDs de ticket ni secretos), pero
> las herramientas, los gates y la organización son los reales.
>
> El principio de fondo (ver la guía de presentación §8; [`../gsd/`](../gsd/) es su versión
> productizada): **el agente es un colaborador disciplinado, no un autopilot. La autonomía se gana
> por-decisión.** El agente hace el
> trabajo de anchura (investigar, planificar, implementar, testear, documentar); el humano es dueño de
> las **decisiones** y de **toda acción externa** (push, PR, deploy, hablar con QA/cliente).

## El proyecto (contexto sanitizado)

- Un **servicio de extracción de documentos** (AWS Lambda, Python 3.12): saca campos estructurados de
  DOCX/DOC/PDF con parsing asistido por LLM. Se dispara por SQS y responde por RPC + S3.
- **Repo propio** (donde trabajamos) + varios **repos de contexto solo-lectura** (el frontend que
  consume la salida, el backend que la almacena, la infra Terraform, los Helm values). Regla:
  *leer libremente, no editar/commitear salvo petición explícita; si hace falta un fix ahí, se propone.*
- **El contrato de salida** es un endpoint de estado (`status endpoint`) cuyo JSON es lo que ven QA,
  producto y el backend. **Todo lo de dentro del repo es detalle de implementación.** Este contrato es
  la unidad de verdad: los bugs se reproducen *ahí*, no en una función interna.

## Las 11 etapas

![Flujo de trabajo con Claude Code — 11 etapas](./flow.png)

> Diagrama: [`flow.png`](./flow.png) (renderizado). Fuente editable: [`flow.mmd`](./flow.mmd) (Mermaid) —
> re-genera el PNG con `python render_flow.py` si cambias el flujo.

> **Antes de las etapas — dónde está el coste y qué hace el agente.** El **agente es el orquestador**, y **es
> donde vive la inferencia** (el coste caro y no determinista): en cada etapa **elige** qué herramienta llamar,
> **lee** su salida al contexto y **razona/decide** el siguiente paso. Las **herramientas** (`/kg`, `git`/`gh`,
> parsers, `pytest`, `grep`) producen **hechos sin inferencia** — mantienen barato el *fact-finding*; el agente
> gasta su inferencia en **decidir y crear**, no en buscar por fuerza bruta. Por eso el método no elimina el
> coste: lo **concentra** (etapas 5–6–7). La tabla tras las etapas lo hace explícito una a una.

1. **Orientar — history-first Y status-first.** Antes de tocar nada, el agente lee el registro durable
   (`data/changes/STATUS.md`, ledgers por-ticket) **y** el estado vivo (`git branch -a`, `gh pr list`).
   Saltarse esto es la causa #1 de retrabajo: ramificar de la base equivocada o duplicar trabajo en curso.
   El *primer paso* history-first es **`/kg <ticket|tema>`** —un grafo de tickets/lecciones construido con
   **graphify** ("CodeGraph pero para tickets"), determinista— que saca los tickets relacionados + la **zona de peligro** a leer antes de
   hacer grep (ver [`herramientas.md`](./herramientas.md) y [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md)).
2. **Triaje inbound — ¿el síntoma es real en el contrato?** Se abre el JSON del `status endpoint` del
   documento afectado (lo aporta QA, o se reproduce con Playwright/F12 en el navegador). Si el síntoma no
   está ahí → el bug es aguas abajo → **push back con evidencia, no escribir código.**
3. **Regresión vs. pre-existente.** Reproducir sobre el estado *previo* al cambio. No asumir la culpa de
   un bug viejo ni descartar una regresión real sin prueba.
4. **Investigar — barato antes que caro.** Diagnosticar con un **oráculo determinista barato** (sin inferencia; un
   parser, un validador de esquema, un script `_diag_*.py`) que da la misma respuesta siempre. La llamada
   al LLM (metered, probabilística) se reserva **solo para verificar el fix acabado**, no para diagnosticar.
5. **Plan — proponer, no proceder.** Opciones + trade-offs; acuerdo humano explícito. Las decisiones
   (y las rechazadas) se escriben para no re-litigarlas.
6. **Implementar — TDD, mínimo.** Test que falla → confirmar RED por el motivo correcto → el código
   mínimo que pasa. Sin features especulativas.
7. **Verificar — contra el contrato, con evidencia.** Suite unit + scoped del defecto + batería de
   regresión canónica. Luego el **gate outbound**, **tres comprobaciones obligatorias**: (1) reproducir en
   la **etapa real de salida** —a través del **wrapper** que reconstruye el contrato, no de la función
   interna `extract()` (un fix en la interna lo puede descartar en silencio el rebuild del wrapper y verse
   "correcto" en local mientras lo enviado está mal)—; (2) ese JSON local coincide con la forma del contrato,
   con el síntoma resuelto; (3) verificarlo **dentro de la imagen desplegada** (la misma que corre el
   runtime): descargarla o construirla, montar el `src` arreglado y re-correr el repro → byte por byte igual
   que en local. *"Los tests en verde no prueban lo que se despliega; sin repro local del contrato Y en la
   imagen, no está hecho."*
8. **Documentar — el porqué, el qué, el handover.** Writeup por-ticket (causa raíz → fix → evidencia),
   update del ledger de estado, criterios de aceptación para QA, nota de handover. Cada cosa **una vez**,
   en su sitio canónico.
9. **Sanitizar — antes de que salga del banco de trabajo.** Escaneo mecánico de las líneas **añadidas**
   del diff staged: nombres de cliente, IDs de ticket en código, secretos, auto-atribución del agente.
   (Footgun real: un diff naive también matchea líneas *borradas* → filtrar solo añadidas.)
10. **Handoff — el humano hace lo externo.** El agente deja la rama lista; **no** hace push, PR ni deploy.
    Eso lo hace el humano (o un tool conducido por el humano, p. ej. Cursor). Los artefactos entregados
    leen como trabajo del autor humano, sin atribución del agente.
11. **Revisión automática + Persistir.** Los hallazgos de un review-bot se triagean como los de un humano
    (confirmar reales, follow-up; descartar falsos *con motivo*). Al cerrar: actualizar registros y
    memoria lean; codificar lecciones reutilizables en el `PLAYBOOK.md`; y cuando aterrizan tickets nuevos,
    reconstruir el grafo con **`/kg-refresh`** para que la orientación de la siguiente tarea (etapa 1) lo vea.

## Coste y rol del agente, etapa a etapa

No hay etapa "gratis", pero el coste **caro** (la inferencia del modelo) no está repartido por igual. La
regla: *"sin inferencia"* = la herramienta **no dispara la tirada del modelo** (el agente sí lee su salida —
coste de un `grep`); *"inferencia"* = el agente **razona o escribe**, que es el gasto real.

| # | Etapa | Herramienta determinista (**sin inferencia**) | Rol del agente = **dónde está la inferencia** |
|---|---|---|---|
| 1 | Orientar | `/kg` (query al grafo) · `STATUS.md` · `git`/`gh` | lee las 3 señales y **sintetiza** base + qué leer — *ligera* |
| 2 | Triaje inbound | JSON del contrato (Playwright/F12) | **decide** Lambda vs aguas-abajo — *barata* |
| 3 | Regresión vs pre-existente | re-ejecutar en la base previa · `git` | **compara** dos salidas y **clasifica** — *barata* |
| 4 | Investigar | parser / validador / `_diag_*.py` | **escribe** el diag (inferencia) → lee su output → causa — *moderada* |
| 5 | **Plan** | — (ningún oráculo da la respuesta) | **razona** opciones + trade-offs — **alta, concentrada** |
| 6 | **Implementar** | `pytest` (RED/GREEN) | **escribe** test + código — **alta** |
| 7 | **Verificar** | `pytest` · repro por wrapper · Docker · byte-diff | orquesta y **lee** resultados; la **tirada LLM final** (confirmar el contrato) **sí cuesta** |
| 8 | Documentar | — | **escribe** los writeups — *moderada (escritura)* |
| 9 | Sanitizar | `grep`/regex sobre el diff staged | corre el escaneo y **revisa** los hits — *barata* |
| 10 | Handoff | — | deja la rama + **escribe** el handover; push/PR = **humano** — *baja-moderada* |
| 11 | Revisión bot + persistir | review-bot (externo) · tests · `/kg-refresh` (build, **amortizado**) | **triagea** hallazgos + **codifica** lecciones — *moderada* |

> El gasto caro se concentra en **5–6–7** (plan, código, verify); 1–3 y 9 son lectura de hechos + decisión
> ligera. Es la regla *barato → caro* en la práctica: la inferencia va donde **aporta** (decidir y crear), no
> en buscar/diagnosticar por fuerza bruta.

## Cómo está organizado el trabajo (la memoria de dos niveles)

**Nivel 1 — siempre cargado (`CLAUDE.md`, pequeño):** orientación, mapa de repos + permisos, reglas de
trabajo, decisiones bloqueadas, y **punteros** de una línea. Es la onboarding de 30s del agente.

**Nivel 2 — bajo demanda (`data/changes/`, todo el detalle):**

| Fichero | Rol |
|---|---|
| `STATUS.md` | Ledger vivo, newest-first: causa raíz, fix, tests, PR por ticket. |
| `TICKETS.md` | One-liners de tickets enviados + estado de promoción dev↔stage. |
| `FOLLOWUPS.md` | Follow-ups abiertos por ticket de origen. |
| `SHARP_EDGES.md` | Invariantes "no tocar" con el ticket que las estableció y el fallo que evita. |
| `PLAYBOOK.md` | Lecciones de investigación reutilizables. |
| `CONVENTIONS.md` | Política de confidencialidad / sanitización. |
| `_HANDOVER_TEMPLATE.md` | Plantilla de handover al humano/tool que hace el push. |
| `extractors/<variante>/process.md` | El *qué* (estado actual de cada componente). |
| `<TICKET>/<TICKET>.md` | El *porqué* (historia y decisiones por ticket). |

> `extractors/` = el *qué*; `<TICKET>/` = el *porqué*. Todo `data/` está gitignored.
> Regla write-once: cada dato en un único ledger canónico; el `CLAUDE.md` apunta, no copia.
> (Cuando se hinchó, lo recortamos **~73% sin pérdida de información**.)
> Sobre estos ledgers se construye el **grafo de tickets** (`/kg`, [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md)):
> un índice navegable —tickets, sharp-edges, lecciones— que la etapa 1 consulta *antes* de grep.

Ver [`herramientas.md`](./herramientas.md) para la prevalencia de tools y [`EJEMPLO_REAL.md`](./EJEMPLO_REAL.md)
para un caso concreto de principio a fin.
