---
name: deploy-staging
description: >-
  Deploy the current app to staging — runs tests, builds, asks for human
  confirmation, then runs the staging deploy script and a health smoke check.
  Use when the user wants to deploy to staging (demo target: ex_staging).
---

# Deploy a staging

Flujo repetible para desplegar a staging de forma segura.
**Demo target:** carpeta `ex_staging/` (staging local simulado — no cloud real).

## Pasos

1. `cd` al target (`ex_staging` o la ruta `@`-mencionada).
2. Verifica el árbol de git **del target**:
   `git status --porcelain -- .` (desde esa carpeta) o `git status --porcelain -- ex_staging`.
   Si hay cambios sin commitear **en el target**, PARA y avisa. (Suciedad en otras carpetas del monorepo del curso se puede ignorar tras avisar.)
3. Ejecuta tests: `npm test`. Si falla, PARA y muestra el output.
4. Construye: `npm run build`. Si falla, PARA.
5. **Pide confirmación humana** antes de desplegar (acción externa / irreversible en producción).
   No ejecutes el deploy hasta un OK explícito del usuario en este chat.
6. Tras OK: `npm run deploy:staging` (equivale a `node scripts/deploy.mjs staging`).
   - En este demo eso levanta un servidor local y escribe `.staging-url`.
   - En un repo real sustituye por `./scripts/deploy.sh staging` o tu pipeline.
7. Smoke check: lee `.staging-url` y llama `GET {url}/health` (curl, `Invoke-WebRequest`, o `fetch`).
   Debe ser HTTP 200 y `ok: true`.
8. Resume: qué se desplegó, URL, resultado del smoke. Menciona `npm run staging:stop` para apagar el demo.

## Reglas

- **Nunca** despliegues con tests en rojo o el target sucio.
- **Nunca** despliegues sin petición/confirmación humana explícita (gate de handoff).
- Muestra siempre el output real de cada comando.
- No uses `staging.example.com` en este repo — el smoke es contra la URL local de `.staging-url`.
