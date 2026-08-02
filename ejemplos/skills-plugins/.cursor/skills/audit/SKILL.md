---
name: audit
description: >-
  Audit dependencies for vulnerabilities and verify tests still pass. Use when
  the user asks for npm audit, dependency CVE check, or "run audit".
---

# Audit de dependencias

1. Ejecuta `npm audit` para encontrar paquetes con vulnerabilidades.
2. Ejecuta `npm audit fix` solo para actualizaciones seguras (no force mayor sin preguntar).
3. Ejecuta los tests (`npm test` o el comando del repo) para verificar que no se ha roto nada.
4. Resume qué se actualizó y cualquier vulnerabilidad que requiera intervención manual.

Muestra siempre el output real de los comandos (evidencia > afirmaciones).
