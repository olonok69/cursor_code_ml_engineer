# Diseño — Presentación y guía sobre Claude Code

> Documento de diseño (spec) del repositorio. Define qué se entrega, para quién y con qué estructura.
> Fecha: 2026-07-05.

## Objetivo

Preparar una **presentación (.pptx)** y una **guía escrita** para una charla + vídeo sobre **Claude Code**,
cubriendo las cinco secciones pedidas y la metodología/herramientas reales de trabajo del autor.

## Decisiones tomadas

| Decisión | Elección |
|---|---|
| Idioma | **Español** (términos técnicos —hooks, skills, MCP, CLAUDE.md— en inglés) |
| Construcción del deck | **Generador python-pptx a medida** que reproduce el estilo del ejemplo `Super_Resolucion_Presentacion.pptx` (eyebrow + título + tarjetas numeradas + agenda + franja de conclusión + footer) |
| Uso del proyecto ILS | **Sanitizado y generalizado** — sin nombres de cliente/empresa, secretos ni rutas internas; presentado como un setup profesional representativo |
| Nivel/audiencia | **Técnico / practitioner** — dirigido a desarrolladores; config y código en las slides, ritmo ágil |

## Secciones (contenido)

1. **Instalación y uso básico** — métodos de instalación (native/Homebrew/WinGet/apt), `claude`, modo interactivo vs `-p` (headless), piping estilo Unix, plan mode, superficies (terminal/IDE/desktop/web).
2. **Memoria, instrucciones y sesiones** — `CLAUDE.md` (jerarquía), auto-memory, `settings.json` (permissions), sesiones entre superficies (teleport/remote/desktop handoff), patrón de contexto de dos niveles.
3. **MCP** — qué es el Model Context Protocol, `.mcp.json`, scopes (local/project/user), servidores reales (serena, context7, playwright, codegraph…), permisos `mcp__*`.
4. **Plugins, tools & skills** — skills, slash commands custom, subagents/agent types, plugins/marketplace, herramientas.
5. **Automatización** — hooks (eventos, matchers, exit codes), GitHub Actions/CI, routines & `/schedule` & `/loop`, Agent SDK.
6. **Metodología real** — GSD (ciclo de fases), CodeGraph (índice de código), y el `ai-agent-methodology` (agente como colaborador disciplinado, 11 etapas, gates de evidencia).

## Fuentes

- Documentación oficial: https://code.claude.com/docs/en/overview
- Curso de hooks/SDK de Anthropic: `/mnt/d/repos3/claude_code_hooks` (configs y scripts reales).
- Proyecto profesional `ILS` + `ai-agent-methodology` (sanitizado).
- GSD: https://github.com/tomascortereal/claude-code-setup
- CodeGraph: https://github.com/colbymchenry/codegraph · https://colbymchenry.github.io/codegraph/

## Estructura del repositorio

```
claude_code/
├── README.md                      # intro + cómo abrir/regenerar el deck
├── GUIA_PRESENTACION.md           # guía narrativa (para el/la ponente y el vídeo)
├── GUIA_TECNICA.md                # referencia de implementación (copy-paste)
├── presentacion/
│   ├── build_pptx.py              # generador python-pptx (estilo del ejemplo)
│   └── Claude_Code_Presentacion.pptx
├── ejemplos/
│   ├── hooks/                     # settings + scripts de hooks (del curso)
│   ├── claude-md/                 # CLAUDE.md de ejemplo (dos niveles, sanitizado)
│   ├── mcp/                       # .mcp.json de ejemplo
│   ├── skills-plugins/            # slash command + skill de ejemplo
│   ├── gsd/                       # notas de uso de GSD
│   ├── codegraph/                 # notas de uso de CodeGraph
│   └── automation/                # CI, /schedule, SDK
├── assets/                        # imágenes/logos para el deck
└── docs/DISENO.md                 # este documento
```

## Criterios de aceptación

- Dos guías en Markdown (presentación / técnica) que cubren las 5 secciones + metodología.
- Un `.pptx` de ~18–20 slides que abre correctamente y sigue el estilo del ejemplo.
- El generador `build_pptx.py` regenera el deck de forma idempotente.
- `ejemplos/` contiene artefactos reales y ejecutables (o casi), sanitizados.
- Nada confidencial de ILS (nombres de cliente, tickets, secretos).
