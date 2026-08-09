---
name: audit
description: >-
  Audit npm dependencies for vulnerabilities and verify tests still pass.
  Use for Node/JavaScript packages (package.json). For Python apps with
  requirements.txt, use the audit-python skill instead.
---

# Audit de dependencias (npm)

Target: a folder with `package.json` (e.g. `ex_npm/`).

1. `cd` into the target app (or use the path the user `@`-mentioned).
2. Ejecuta `npm audit` para encontrar paquetes con vulnerabilidades.
3. Ejecuta `npm audit fix` solo para actualizaciones seguras (no force mayor sin preguntar).
4. Ejecuta los tests (`npm test`) para verificar que no se ha roto nada.
5. Resume qué se actualizó y cualquier vulnerabilidad que requiera intervención manual.

Muestra siempre el output real de los comandos (evidencia > afirmaciones).

Si el target es Python (`requirements.txt` / no `package.json`), **no inventes npm** — di que use `/audit-python`.
