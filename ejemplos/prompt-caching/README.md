# Prompt caching — por qué las sesiones largas no arruinan

Cada turno de una sesión reenvía **todo** el contexto al modelo. Sin caching, una sesión de 50 turnos
re-procesaría el system prompt + CLAUDE.md + historial 50 veces. El **prompt caching** hace que el prefijo
estable se procese una vez y se relea barato. Material de la sección **Contexto** de la Parte 1
(ver [`GUIA_PRESENTACION.md`](../../GUIA_PRESENTACION.md)).

## 1. El mecanismo (API)

La API cachea un **prefijo contiguo** del prompt hasta un *cache breakpoint* (`cache_control`), con un
TTL. Dentro del TTL, ese prefijo se lee de cache en vez de re-procesarse:

| | Escritura de cache | Lectura de cache |
|---|---|---|
| TTL 5 min (por defecto) | 1.25× el precio de input | **0.1×** el precio de input |
| TTL 1 hora | 2× el precio de input | **0.1×** el precio de input |

```python
system=[{
    "type": "text",
    "text": LONG_STABLE_INSTRUCTIONS,          # lo estable, primero
    "cache_control": {"type": "ephemeral"},    # el breakpoint va AL FINAL de lo estable
}]
# lo que cambia por turno (query del usuario, timestamps) va DESPUÉS, fuera del cache
```

La jerarquía se cachea **en orden estricto**: `[Tools] → [System] → [Messages]`. Un cambio en cualquier
nivel invalida ese nivel **y todos los siguientes**. De ahí las dos reglas: lo estable primero, y el
breakpoint sobre lo estable — nunca sobre contenido que cambia por request (el error clásico es meter un
timestamp antes del breakpoint: 0 cache hits y nadie sabe por qué).

Demo ejecutable: [`cache_demo.py`](./cache_demo.py) — dos llamadas idénticas; la segunda imprime
`cache_read_input_tokens > 0` y compara el coste.

## 2. Qué significa esto en Claude Code

Claude Code no te expone `cache_control` — **lo aplica solo** en cada request: system prompt + tools +
historial forman el prefijo estable, y cada turno nuevo lee de cache lo anterior. Tú no configuras nada,
pero tus decisiones **determinan si el cache acierta**:

| Decisión tuya | Efecto en el cache |
|---|---|
| CLAUDE.md pequeño y **estable** (dos niveles) | Prefijo corto, se escribe barato, no cambia → hits |
| Editar CLAUDE.md / settings a mitad de sesión | Cambia el prefijo → invalida **todo** desde ahí |
| Muchos servers MCP activos | Bloque de tools mayor y más propenso a cambiar → escrituras más caras |
| Sesión larga con turnos frecuentes | Cada turno relee el historial a 0.1× — el caso ideal |
| `/compact` o auto-compact | **Reescribe el historial** → rompe el cache a nivel de mensajes (se re-escribe una vez y sigue) |
| `/clear` / sesión nueva | Cache nuevo desde cero (el prefijo de sistema se re-escribe) |

La moraleja que conecta con [`../context/`](../context/): **contexto lean y estable no solo rinde mejor —
también cuesta menos.** El patrón de dos niveles del CLAUDE.md optimiza los dos ejes a la vez: menos
tokens fijos (context) y un prefijo que nunca cambia (cache).

### El TTL que usa Claude Code — y cómo cambiarlo

El TTL por defecto **depende de cómo estés autenticado**:

| Autenticación | TTL por defecto | Por qué |
|---|---|---|
| **Suscripción Claude** (login normal) | **1 hora** | Incluido en el plan, sin coste extra |
| **API key** / Bedrock / Vertex / Foundry | **5 minutos** | Minimiza el coste de las escrituras (write 1.25× vs 2× a 1h) |

Se cambia por variable de entorno (en la shell, o en el bloque `env` de `settings.json`):

```bash
ENABLE_PROMPT_CACHING_1H=1     # optar al TTL de 1h con API key / providers terceros
FORCE_PROMPT_CACHING_5M=1      # forzar 5 min aunque tengas suscripción
DISABLE_PROMPT_CACHING=1       # desactivar el caching por completo
# por modelo: DISABLE_PROMPT_CACHING_SONNET / _OPUS / _HAIKU
```

El matiz práctico: como cada **lectura** renueva la ventana, con suscripción una sesión interactiva con
pausas de hasta una hora entre turnos sigue acertando cache; con API key, una pausa de más de 5 minutos
implica re-escribir el prefijo en el siguiente turno.
Doc: [code.claude.com/docs/en/prompt-caching](https://code.claude.com/docs/en/prompt-caching).

## 3. Detalles finos (para la audiencia técnica)

- Mínimo cacheable: ~1.024 tokens en los modelos grandes (4.096 en Haiku); por debajo, no se cachea (sin error).
- Máx. 4 breakpoints explícitos + 1 automático; el lookup mira los últimos 20 bloques.
- Diagnóstico en la respuesta de la API: `usage.cache_read_input_tokens`,
  `usage.cache_creation_input_tokens` (y desglose por TTL en `cache_creation`).
- El refresh dentro del TTL no cuesta un write nuevo: cada lectura (0.1×) renueva la ventana.
- En el Agent SDK aplican las mismas reglas que en la API — si construyes tooling propio
  (ver [`../automation/sdk.ts`](../automation/sdk.ts)), pon lo estable primero.

Docs: [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) ·
[pricing](https://platform.claude.com/docs/en/about-claude/pricing).
