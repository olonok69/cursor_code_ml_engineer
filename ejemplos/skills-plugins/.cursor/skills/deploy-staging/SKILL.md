---
name: deploy-staging
description: >-
  Deploy the current branch to staging — runs tests, builds, and pushes to the
  staging remote with a smoke check. Use when the user wants to deploy to staging.
---

# Deploy a staging

Flujo repetible para desplegar la rama actual a staging de forma segura.

## Pasos

1. Verifica que el árbol de git está limpio (`git status`). Si hay cambios sin commitear, PARA y avisa.
2. Ejecuta la suite de tests: `npm test`. Si falla, PARA y muestra el output.
3. Construye: `npm run build`.
4. **Pide confirmación humana** antes de desplegar (acción externa).
5. Despliega: `./scripts/deploy.sh staging` (solo tras OK).
6. Smoke check: `curl -fsS https://staging.example.com/health` y confirma HTTP 200.
7. Resume: commit desplegado, URL, y resultado del smoke check.

## Reglas

- **Nunca** despliegues con tests en rojo o el árbol sucio.
- **Nunca** despliegues sin petición/confirmación humana explícita (gate de handoff).
- Muestra siempre el output real de cada comando.
