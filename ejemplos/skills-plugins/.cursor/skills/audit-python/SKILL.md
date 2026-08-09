---
name: audit-python
description: >-
  Audit Python dependencies with pip-audit and verify the app still works.
  Use when the user asks for pip-audit, Python CVE check, or audit on a
  requirements.txt project (e.g. ex_app). For Node/npm, use the audit skill.
---

# Audit de dependencias (Python)

Target: a folder with `requirements.txt` (e.g. `ex_app/`).

1. `cd` into the target app (or use the path the user `@`-mentioned).
2. Asegura `pip-audit`: `python -m pip install pip-audit` si hace falta.
3. Ejecuta `python -m pip_audit -r requirements.txt` (o el requirements que indique el usuario).
4. **No** apliques upgrades automáticos de majors sin preguntar. Si el usuario pide fix seguro:
   `python -m pip_audit -r requirements.txt --fix` solo tras confirmación explícita.
5. Tests:
   - Si hay `pytest` / `tests/` / `test_*.py` → corre `pytest` (o el comando del README).
   - Si no hay suite → smoke mínimo: parse AST o `python -c "import …"` de los módulos principales.
6. Resume: CVEs encontradas (si hay), fixes aplicados (si los hubo), resultado de tests/smoke.

Muestra siempre el output real de los comandos (evidencia > afirmaciones).

Si el target es Node (`package.json`), **no inventes pip** — di que use `/audit`.
