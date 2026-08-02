# MCP — Model Context Protocol

**MCP** es un estándar abierto para conectar Claude Code a fuentes de datos y herramientas externas:
docs de Google Drive, tickets de Jira, tu base de datos, un navegador, tu propio tooling… El servidor
MCP expone *tools* que Claude puede llamar; las tools aparecen con el prefijo `mcp__<server>__<tool>`.

## Los tres scopes (dónde vive la config)

| Scope | Fichero | Alcance |
|---|---|---|
| **local** | `.claude/settings.local.json` | Solo tú, solo esta máquina/proyecto (no versionado). |
| **project** | `.mcp.json` (raíz del repo) | Compartido con el equipo, **se versiona**. Ver [`.mcp.json`](./.mcp.json). |
| **user** | `~/.claude.json` | Todos tus proyectos. |

## Añadir un server por CLI

```bash
# stdio (proceso local)
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server

# HTTP remoto
claude mcp add --transport http context7 https://mcp.context7.com/mcp

claude mcp list          # ver servers y estado
/mcp                     # dentro de la sesión: estado, auth OAuth, herramientas
```

## Buenas prácticas

- **Secretos por variable de entorno**, nunca en el JSON versionado (ver el server `supabase`).
- **Permisos**: aunque el server esté configurado, controlas qué tools se permiten con el allowlist
  `mcp__playwright__browser_navigate`, etc. en `settings.local.json`.
- **Elige el scope correcto**: lo del equipo → `.mcp.json`; lo tuyo personal → local/user.

## Servers que uso a diario

`serena` (navegación semántica de código) · `context7` (docs de librerías) · `playwright` (verificación
de UI) · `codegraph` (grafo de conocimiento del código, ver `../codegraph/`) · `supabase`.
