# Serena — navegación semántica de código (MCP)

[Serena](https://github.com/oraios/serena) es un server MCP que da a Claude **entendimiento simbólico**
del código vía language servers (LSP): en lugar de grep sobre texto, opera sobre símbolos — clases,
métodos, referencias — con la precisión de un IDE. Es una de las tres patas de navegación de la
metodología (Parte 2), junto a CodeGraph y `/kg` (ver [`../metodologia/herramientas.md`](../metodologia/herramientas.md)).

## Instalación

```bash
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server
# dentro de la sesión: /mcp para ver estado y tools
```

## Las tools que importan

| Tool | Qué hace | Cuándo |
|---|---|---|
| `find_symbol` | Localiza un símbolo por nombre (con `body=true` trae el cuerpo) | Leer UN método de un fichero de 5k líneas sin cargarlo entero |
| `get_symbols_overview` | Esqueleto de un fichero: clases y métodos, sin cuerpos | Primer vistazo a un fichero grande |
| `find_referencing_symbols` | **Quién referencia un símbolo, desambiguado por clase** | **Obligatorio antes de renombrar/borrar** |
| `search_for_pattern` | Búsqueda por patrón con contexto simbólico | Cuando el literal importa pero quieres el símbolo contenedor |
| `activate_project` | Cambiar de proyecto indexado | Multi-repo |

## El papel en la metodología: el chequeo preciso

La regla de prevalencia (fase **Navegar/Investigar** del flujo de 11 etapas) es:

1. **CodeGraph `codegraph_explore` primero** — survey barato: fuente + rutas de llamada + blast radius +
   cobertura en 1 llamada ([`../codegraph/`](../codegraph/)).
2. **Serena `find_referencing_symbols` para el chequeo preciso** — antes de renombrar o borrar. La razón:
   el `impact` de CodeGraph es plano y **mezcla métodos homónimos** (`Invoice.process()` vs
   `Refund.process()`); Serena, al apoyarse en el LSP, los **desambigua por clase**. Un rename basado
   solo en el grafo plano puede tocar el método equivocado.
3. **grep/Read solo para literales** — strings en templates, configs, docs: lo que ningún grafo sigue.

Complementarios, no rivales: CodeGraph responde *"¿qué es esto y qué se rompe?"* en una llamada;
Serena responde *"¿exactamente quién llama a ESTE `process()` y no al otro?"*. El subagente
[`refactor-scout`](../subagents/.claude/agents/refactor-scout.md) codifica este orden como procedimiento.

## Permisos (allowlist)

Como toda tool MCP, se gobierna en `settings.json` — reglas concretas, no comodines:

```json
"allow": [
  "mcp__serena__find_symbol",
  "mcp__serena__find_referencing_symbols",
  "mcp__serena__get_symbols_overview",
  "mcp__serena__search_for_pattern",
  "mcp__serena__activate_project"
]
```
