# Automatización

Cuatro niveles, del más ligero al más autónomo.

## 1. Hooks (determinista, dentro de la sesión)

Comandos que se disparan antes/después de las acciones del agente. Ver [`../hooks/`](../hooks/).
Es la base: formateo, type-check, seguridad, observabilidad — sin depender de que el modelo "se acuerde".

## 2. Headless / Unix piping (`claude -p`)

Claude Code es componible. En modo `-p` (print/headless) lee de stdin y escribe a stdout, así que
encaja en cualquier pipeline:

```bash
# Analizar logs
tail -200 app.log | claude -p "Avísame si ves alguna anomalía"

# Operaciones masivas sobre ficheros cambiados
git diff main --name-only | claude -p "Revisa estos ficheros por problemas de seguridad"

# Traducciones en CI y abrir un PR
claude -p "Traduce las cadenas nuevas al francés y abre un PR para revisión"
```

## 3. CI/CD (GitHub Actions / GitLab)

Revisión de PRs y triaje de issues automáticos. Ver [`github-action-claude.yml`](./github-action-claude.yml).
Anthropic ofrece integraciones dedicadas: **GitHub Actions**, **GitLab CI/CD** y **GitHub Code Review**.

## 4. Tareas programadas (recurrentes)

| Mecanismo | Dónde corre | Uso |
|---|---|---|
| **Routines** (`/schedule`) | Infra de Anthropic (aunque tu equipo esté apagado); puede dispararse por API o eventos de GitHub. | Reviews de PR por la mañana, auditoría semanal de dependencias. |
| **Desktop scheduled tasks** | Tu máquina, con acceso a ficheros locales. | Tareas que necesitan tu entorno local. |
| **`/loop`** | Dentro de una sesión CLI. | Polling rápido: repetir un prompt cada N minutos. |

## 5. Agent SDK (programático)

Para workflows totalmente a medida: construye tus propios agentes con las tools de Claude Code.
Ver [`sdk.ts`](./sdk.ts) — `query({ prompt, options: { allowedTools } })`.
El propio `query_hook.js` de la sección de hooks es un SDK-dentro-de-un-hook: "IA revisando IA".
