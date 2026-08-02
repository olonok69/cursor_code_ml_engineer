# Runbook — Instalar CodeGraph y actualizar GSD (máquina de trabajo, WSL2)

> Guía de cambios para la máquina principal donde trabajas el proyecto **ILS**. Ejecuta **todo en el shell
> de WSL** (no PowerShell), que es donde vive tu `node` y tu `claude`.
>
> Convención: `$ILS` = raíz del workspace ILS (en tu máquina principal suele ser `/mnt/d/ILS`; en otras
> puede ser `/mnt/d/repos3/ILS`). Ajústalo:
> ```bash
> export ILS=/mnt/d/ILS        # <-- pon aquí tu ruta real
> ```

---

## 0. Estado de partida y verificación previa

Verificado en una máquina equivalente (la tuya puede variar — **confírmalo primero**):

```bash
node -v          # necesitas >= 22.5  (aquí: v26.1.0  ✓ para el node:sqlite de CodeGraph)
npm -v
claude --version # aquí: 2.1.201
cat ~/.claude/get-shit-done/VERSION   # GSD instalado (aquí: 1.42.3)
```

- **GSD** está instalado por **git clone** en `~/claude-code-setup` (remote `tomascortereal/claude-code-setup`,
  rama `main`), con motor en `~/.claude/get-shit-done/` y skills en `~/.claude/skills/gsd-*`. **No** es un
  plugin de marketplace, así que el update **no** es `/plugin update`.
- **CodeGraph** aún no está instalado.

> Haz un punto de retorno rápido antes de tocar nada:
> ```bash
> cp -r ~/.claude/skills ~/.claude/skills.bak-$(date +%Y%m%d) 2>/dev/null || true
> ```
> (GSD además mantiene su propio journal de migraciones y backups automáticos — ver Parte A.)

---

## Parte A — Actualizar GSD

### Opción 1 (recomendada): el comando integrado

Dentro de una sesión de Claude Code (en cualquier proyecto, p. ej. `cd $ILS/document-parser-lambda && claude`):

```
/gsd-update
```
Comprueba la última versión, muestra el changelog y aplica la actualización (con migraciones y backup
automáticos en `~/.claude/gsd-migration-journal/` + `~/.claude/gsd-user-files-backup/`). Luego, para
alinear las skills en todos los runtime roots:

```
/gsd-sync-skills
```

Si tienes parches locales sobre GSD que la actualización pudo pisar:

```
/gsd-reapply-patches
```

### Opción 2 (manual, equivalente): git + installer

```bash
cd ~/claude-code-setup
git stash            # solo si tienes cambios locales sin commitear
git pull origin main
./install.sh         # re-aplica skills/agents/hooks al ~/.claude
git stash pop        # si hiciste stash
```

### Verificar GSD

```bash
cat ~/.claude/get-shit-done/VERSION      # debe subir respecto a 1.42.3
```
En una sesión de Claude:
```
/gsd-help            # lista de comandos (confirma que responde)
/gsd-progress        # en $ILS/document-parser-lambda: te sitúa en el proyecto
```

> Nota: el update no toca tu `data/.planning/` ni tus ledgers de ILS — solo el motor/skills de GSD bajo
> `~/.claude`. Tu trabajo del proyecto queda intacto.

---

## Parte B — Instalar CodeGraph

### B1. Instalar el CLI

Elige **uno**:

```bash
# a) npm global (necesita Node >= 22.5, que ya tienes)
npm i -g @colbymchenry/codegraph

# b) instalador self-contained (trae su propio Node; no depende de tu npm)
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
```

Verifica:
```bash
codegraph --version
```

### B2. Conectar CodeGraph a Claude Code (MCP)

CodeGraph trae un instalador que **auto-detecta Claude Code y escribe la config MCP** por ti:

```bash
codegraph install            # detecta agentes y escribe su config MCP
# o explícito y no-interactivo (--location es global|local, NO "user"):
codegraph install --target=claude --location=global --yes
```

**Proyecto por defecto (recomendado):** el server MCP **no tiene proyecto por defecto** — en modo MCP usa el
`rootUri` del cliente (= la raíz del workspace, p. ej. `/mnt/d/ILS`, que no tiene `.codegraph/`). Fija el
repo con `--path` para que `codegraph_explore` **no** pida `projectPath` en cada llamada:

```jsonc
{
  "mcpServers": {
    "codegraph": {
      "type": "stdio",
      "command": "codegraph",
      "args": ["serve", "--path", "/mnt/d/ILS/document-parser-lambda", "--mcp"]
    }
  }
}
```
(Sin `--path`, pásale `projectPath` en cada llamada; con `--path` fijado, va sin él y solo lo pasas para
consultar **otro** repo indexado. Cualquier cambio de config MCP requiere **reiniciar** Claude Code.)

### B3. Indexar los repos de ILS

`codegraph init` crea el directorio local `.codegraph/` **y construye el grafo** en un solo paso, por repo.
Empieza por el repo **propio** (donde editas extractores de 4–6k líneas):

```bash
cd $ILS/document-parser-lambda
codegraph init
```

Opcional — indexar también repos de contexto solo-lectura que consultas a menudo (uno por uno; cada uno
tendrá su `.codegraph/`):

```bash
cd $ILS/monolith   && codegraph init      # backend consumidor del contrato
cd $ILS/frontend   && codegraph init      # SPA que renderiza la salida
```

Para re-indexar en vivo mientras trabajas (opcional, deja en background):
```bash
cd $ILS/document-parser-lambda
codegraph watch
```

### B4. Ignorar el índice en git (cambio necesario)

`.codegraph/` es un índice local — **no debe commitearse**. Añádelo al `.gitignore` de cada repo indexado
que sea propio/editable:

```bash
cd $ILS/document-parser-lambda
grep -qxF '.codegraph/' .gitignore || echo '.codegraph/' >> .gitignore
```
(En los repos solo-lectura no commiteas de todos modos, pero puedes hacer lo mismo o usar tu
`core.excludesfile` global.)

### B5. Permitir la tool MCP en el allowlist de ILS (cambio necesario)

Tu `document-parser-lambda/.claude/settings.local.json` es un allowlist **hand-curated** (reglas
específicas, sin comodines). Para que `codegraph_explore` no dispare prompts de permiso cada vez, añade la
regla. Edita ese fichero y añade a `permissions.allow`:

```jsonc
"mcp__codegraph__codegraph_explore"
```

(O el comodín del server si prefieres habilitar todas sus tools: `"mcp__codegraph"`.) Mantén `deny`/`ask`
como estén. No añadas acciones externas al allowlist — esa postura no cambia.

### B6. Verificar CodeGraph

1. **Reinicia Claude Code** (cierra y reabre la sesión) para que cargue el server MCP.
2. En la sesión:
   ```
   /mcp
   ```
   Debe aparecer **codegraph** como conectado, con su tool.
3. Prueba real en el repo propio (con `--path` fijado va **sin** `projectPath`; si no, pásalo):
   ```
   codegraph_explore "detección de fin de provisión en el extractor de PDF"
   ```
   Debe devolver fuente + rutas de llamada + blast radius + flags de cobertura, sin que hayas leído el
   fichero entero. Si responde *"No CodeGraph project is loaded"*, falta el `--path` (o el `projectPath`).

---

## Parte C — Que el agente lo use (ajuste recomendado)

Tu **`~/.claude/CLAUDE.md` global ya tiene una sección de CodeGraph** ("en repos con `.codegraph/`, usa
`codegraph_explore` antes de grep/Read"), así que en cuanto un repo esté indexado, el agente lo preferirá.

Para reforzarlo en el proyecto, añade **una línea** al `document-parser-lambda/CLAUDE.md`, junto a la regla
de Serena que ya existe (regla 9 / § navegación), por ejemplo:

> *"Para impacto y callers a escala (blast radius, rutas de llamada) usa `codegraph_explore` antes de
> rastrear imports a mano; sigue usando Serena `find_symbol`/`get_symbols_overview` para overview y cuerpos,
> y `find_referencing_symbols` antes de renombrar/borrar."*

Es un cambio de una línea en el fichero always-loaded — mantenlo corto (disciplina lean del CLAUDE.md).

---

## Rollback / desinstalar

```bash
# CodeGraph (por repo o global)
codegraph uninstall
rm -rf $ILS/document-parser-lambda/.codegraph      # borra un índice concreto

# GSD: restaurar skills desde el backup que hiciste, o re-ejecutar el installer de la versión previa
#   (git checkout <tag-previo> en ~/claude-code-setup && ./install.sh)
```

---

## Checklist

- [ ] `node -v` ≥ 22.5, `claude --version` OK, `cat ~/.claude/get-shit-done/VERSION` anotado.
- [ ] Backup rápido de `~/.claude/skills`.
- [ ] **GSD:** `/gsd-update` → `/gsd-sync-skills` (o `git pull && ./install.sh`). VERSION subió.
- [ ] `/gsd-help` y `/gsd-progress` responden en ILS.
- [ ] **CodeGraph:** `npm i -g @colbymchenry/codegraph` → `codegraph --version` OK.
- [ ] `codegraph install --target=claude` (o config manual en `~/.claude.json`).
- [ ] `codegraph init` en `document-parser-lambda` (+ repos de contexto opcionales).
- [ ] `.codegraph/` en `.gitignore`.
- [ ] `mcp__codegraph__codegraph_explore` en el allowlist de `settings.local.json`.
- [ ] Reiniciar Claude → `/mcp` muestra codegraph → `codegraph_explore` devuelve resultado.
- [ ] (Opcional) línea de CodeGraph añadida al `CLAUDE.md` del repo propio.
