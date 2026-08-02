# GSD — "Get Stuff Done"

Setup de Claude Code para **gestión de proyectos por fases**, instalado como plugin.
Repo: https://github.com/tomascortereal/claude-code-setup

## La idea

En vez de "chatear" con el agente, GSD impone un **ciclo de vida** con estado persistente en `.planning/`.
Es la [metodología de "agente disciplinado"](../metodologia/) **hecha tooling**: separa *discutir* de
*planificar* de *ejecutar* de *verificar*, y en cada frontera hay un gate. Cada fase deja artefactos
versionados y commits atómicos, de modo que una sesión nueva **reanuda** en vez de re-onboarding.

## El ciclo de vida (y sus artefactos en `.planning/`)

```
/gsd-new-project     ->  PROJECT.md      (contexto profundo: qué, por qué, restricciones)
        │                ROADMAP.md      (fases + criterios de éxito por fase)
        ▼
/gsd-discuss-phase   ->  recoge contexto de la fase con preguntas adaptativas
        ▼
/gsd-plan-phase      ->  PLAN.md         (tareas, dependencias, verificación) + gate de plan-checker
        ▼
/gsd-execute-phase   ->  ejecuta las tareas en olas (waves) paralelas, commits atómicos
        ▼
/gsd-verify-work     ->  VERIFICATION.md (UAT conversacional: ¿entrega lo prometido?)
```

- **`/gsd-progress`** — el comando "situacional": mira el estado y te dice qué toca (planificar o ejecutar).
- **`/gsd-autonomous`** — corre todas las fases restantes (discuss→plan→execute) de forma autónoma.
- **`/gsd-quick` / `/gsd-fast`** — tareas pequeñas con las garantías (commits atómicos, estado) pero sin
  la maquinaria completa.

## Subagentes especializados (lo que lo hace potente)

GSD no es un prompt: orquesta una batería de **subagentes** con roles concretos, cada uno con su propio
contexto y presupuesto. Algunos:

| Subagente | Rol |
|---|---|
| `gsd-planner` | Crea el `PLAN.md` con desglose de tareas y análisis de dependencias. |
| `gsd-plan-checker` | Verifica que el plan logrará el objetivo **antes** de ejecutar (goal-backward). |
| `gsd-executor` | Ejecuta con commits atómicos, protocolos de checkpoint y manejo de desviaciones. |
| `gsd-code-reviewer` | Revisa los ficheros cambiados → `REVIEW.md` clasificado por severidad. |
| `gsd-verifier` | Verifica el **objetivo** de la fase, no solo que las tareas se completaron. |
| `gsd-phase-researcher` | Investiga cómo implementar antes de planificar → `RESEARCH.md`. |

## Por qué encaja con la metodología

GSD encarna los gates que en [`../metodologia/WORKFLOW.md`](../metodologia/WORKFLOW.md) se aplican a mano:
**plan → acuerdo → implementar** (el gate de `/gsd-plan-phase` + plan-checker), **verificar contra el
objetivo con evidencia** (`gsd-verifier`), **rastro durable** (`.planning/` versionado). La diferencia:
GSD lo automatiza y paraleliza con subagentes.

> **¿Se usa en el proyecto de la Parte 2? No.** GSD está instalado y encarna la misma disciplina, pero ese
> proyecto corre el flujo de 11 etapas + `data/changes/`, **más depurado y afinado** a fixes por ticket
> sobre un servicio en producción. GSD tiene más sentido en un **greenfield multi-componente** (diseñar una
> aplicación entera: roadmap → fases). Aquí se muestra como el método **productizado** — y como ejemplo
> vivo de la Parte 1: subagentes custom + skills, distribuidos como plugin.

> Instala **muchas** skills `gsd-*`. Empieza por `/gsd-help` y `/gsd-progress`. Configurable con
> `/gsd-settings` (toggles de workflow, perfil de modelo por agente).
