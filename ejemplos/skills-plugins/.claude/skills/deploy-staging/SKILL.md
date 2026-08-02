---
name: deploy-staging
description: Use when the user wants to deploy the current branch to the staging environment - runs tests, builds, and pushes to the staging remote with a smoke check.
---

# Deploy a staging

Flujo repetible para desplegar la rama actual a staging de forma segura.

## Pasos

1. Verifica que el árbol de git está limpio (`git status`). Si hay cambios sin commitear, PARA y avisa.
2. Ejecuta la suite de tests: `npm test`. Si falla, PARA y muestra el output.
3. Construye: `npm run build`.
4. Despliega: `./scripts/deploy.sh staging`.
5. Smoke check: `curl -fsS https://staging.example.com/health` y confirma HTTP 200.
6. Resume: commit desplegado, URL, y resultado del smoke check.

## Reglas

- **Nunca** despliegues con tests en rojo o el árbol sucio.
- Muestra siempre el output real de cada comando (evidencia antes que afirmaciones).
