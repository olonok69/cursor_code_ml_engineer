# Plugins, tools y skills

Los tres mecanismos de extensibilidad de Claude Code, de más simple a más potente.

## 1. Tools (herramientas)

Lo que Claude puede *hacer*: `Read`, `Edit`, `Write`, `Bash`, `Grep`, `Glob`, `WebFetch`, `Task`
(subagentes), más las tools `mcp__*` que añaden los servidores MCP. Controlas el acceso con el
**allowlist de permisos** en `settings.json` (`allow` / `deny` / `ask`).

## 2. Slash commands (comandos custom)

Un fichero Markdown en `.claude/commands/<nombre>.md` = un comando `/<nombre>`. El cuerpo es el prompt
que se ejecuta. Ideal para tareas repetibles cortas. Ver [`audit.md`](./.claude/commands/audit.md) → `/audit`.

## 3. Skills

Una **skill** empaqueta un flujo de trabajo repetible con instrucciones más ricas. Vive en
`.claude/skills/<nombre>/SKILL.md` con frontmatter (`name`, `description`). La `description` es lo que
Claude usa para **decidir cuándo invocarla** automáticamente. Ver
[`deploy-staging/SKILL.md`](./.claude/skills/deploy-staging/SKILL.md).

Diferencia clave frente a un slash command: la skill puede llevar ficheros de apoyo (scripts, plantillas,
referencias) en su carpeta y Claude la **auto-selecciona** por su `description`; el slash command lo
invocas tú explícitamente con `/`.

## 4. Plugins y marketplaces

Un **plugin** agrupa y distribuye skills + comandos + agentes + servidores MCP + hooks como una unidad
instalable desde un *marketplace*.

```bash
/plugin marketplace add <owner/repo>   # añadir un marketplace
/plugin install <plugin>               # instalar
/plugin                                 # gestionar los instalados
```

Así se distribuyen setups completos: p. ej. GSD (ver `../gsd/`) instala decenas de skills `gsd-*`,
agentes y comandos de una vez.

## 5. Subagents (agent types)

Con la tool `Task` lanzas **subagentes** con su propio contexto y presupuesto: `Explore` (búsqueda
read-only), `Plan` (arquitectura), `general-purpose`, o agentes especializados de un plugin. Sirven para
paralelizar trabajo independiente sin ensuciar tu contexto principal.
