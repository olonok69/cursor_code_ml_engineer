#!/usr/bin/env python3
"""
Demo mínima de prompt caching con la API de Anthropic.

Hace DOS llamadas con el mismo system prompt largo (estable, con cache_control) y
distinta pregunta (variable, fuera del cache). La 1ª ESCRIBE el cache; la 2ª LEE.

    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python cache_demo.py

Salida esperada (números orientativos):
    Llamada 1: cache_creation=~2100  cache_read=0      input=12
    Llamada 2: cache_creation=0      cache_read=~2100  input=11
    -> la 2ª llamada procesó el prefijo a 0.1x del precio de input.

Claude Code hace exactamente esto por ti en cada turno de una sesión.
"""
import os
import anthropic
from dotenv import load_dotenv
load_dotenv() 
client = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY

# --- Prefijo ESTABLE: instrucciones largas (>1024 tokens para ser cacheable). ---
# En Claude Code, este papel lo juegan el system prompt + tools + tu CLAUDE.md.
STABLE_SYSTEM = (
    "Eres un revisor de código senior de un equipo de plataforma. Sigue estas convenciones:\n"
    + "\n".join(
        f"{i}. Regla de estilo número {i}: los módulos del dominio {i} exponen una fachada única, "
        f"prohibido importar sus internals; los errores se propagan tipados y los logs no llevan PII."
        for i in range(1, 61)
    )
)

MODEL = os.environ.get("CACHE_DEMO_MODEL", "claude-sonnet-4-5")


def ask(question: str) -> None:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=200,
        system=[
            {
                "type": "text",
                "text": STABLE_SYSTEM,
                # el breakpoint va AL FINAL del bloque estable:
                "cache_control": {"type": "ephemeral"},  # TTL 5 min (usa {"ttl": "1h"} para 1 hora)
            }
        ],
        # lo variable (la pregunta) va DESPUÉS del breakpoint -> no invalida el cache
        messages=[{"role": "user", "content": question}],
    )
    u = resp.usage
    print(
        f"cache_creation={getattr(u, 'cache_creation_input_tokens', 0):>6}  "
        f"cache_read={getattr(u, 'cache_read_input_tokens', 0):>6}  "
        f"input={u.input_tokens:>4}  output={u.output_tokens:>4}"
    )


if __name__ == "__main__":
    print("Llamada 1 (escribe el cache):")
    ask("¿Puede un módulo del dominio 3 importar internals del dominio 7? Responde en una frase.")
    print("Llamada 2 (lee el cache):")
    ask("¿Los logs pueden llevar el email del usuario? Responde en una frase.")
