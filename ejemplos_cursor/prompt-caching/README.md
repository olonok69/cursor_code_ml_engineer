# Prompt caching — qué viaja a Cursor y qué no

Cada turno reenvía contexto al modelo. El **prompt caching** (API Anthropic) hace que un prefijo
estable se procese una vez y se relea barato. La demo ejecutable
[`cache_demo.py`](./cache_demo.py) sigue siendo válida: habla con la **API de Anthropic**, no con el
producto Cursor.

## 1. El mecanismo (API Anthropic) — sin cambios

La API cachea un **prefijo contiguo** hasta un *cache breakpoint* (`cache_control`), con TTL.

| | Escritura de cache | Lectura de cache |
|---|---|---|
| TTL 5 min (por defecto) | 1.25× input | **0.1×** input |
| TTL 1 hora | 2× input | **0.1×** input |

```python
system=[{
    "type": "text",
    "text": LONG_STABLE_INSTRUCTIONS,
    "cache_control": {"type": "ephemeral"},
}]
```

Jerarquía: `[Tools] → [System] → [Messages]`. Un cambio invalida ese nivel y los siguientes.
Demo: dos llamadas idénticas; la segunda debe mostrar `cache_read_input_tokens > 0`.

## 2. Qué significa en Claude Code vs Cursor

| | Claude Code | Cursor |
|---|---|---|
| ¿Te expone `cache_control`? | No — lo aplica el producto | No (producto distinto; el modelo/provider puede cachear por su cuenta) |
| Variables `ENABLE_PROMPT_CACHING_1H`, etc. | Sí (Claude Code / providers) | **No aplican** a Cursor IDE |
| Qué sí controlas | Tamaño/estabilidad de `CLAUDE.md` + tools MCP | Tamaño/estabilidad de **rules + AGENTS.md + MCP tools** |
| `/compact` rompe cache de historial | Documentado en Claude | No copies esa historia; en Cursor usa chats nuevos / disciplina de contexto |

**Moraleja portable:** contexto lean y estable → menos tokens fijos y mejor comportamiento
(y, si hablas con la API Anthropic tú mismo, mejor cache). El patrón de dos niveles
([`../agents-md/`](../agents-md/)) optimiza eso en Cursor igual que `CLAUDE.md` en Claude Code.

## 3. Cuándo usar `cache_demo.py` en un curso Cursor

- Para enseñar **cómo funciona el caching en la API** (audiencia técnica).
- **No** como “así configura Cursor el cache” — eso es interno / provider-dependent.
- Si automatizas con **Cursor SDK** contra modelos Anthropic u otros, lee la docs de pricing/caching
  de ese provider; no asumas las env vars de Claude Code.

Docs API: [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
