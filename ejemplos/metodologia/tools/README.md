# `tools/` — dos herramientas de lectura para el agente

Copias genericizadas de dos herramientas reales del proyecto. Las dos comparten una idea:
**el agente puede leer mucho más de lo que puede escribir**, y esa frontera se impone en el código,
no en una instrucción.

| Carpeta | Qué es | Skill que la usa |
|---|---|---|
| [`atlassian/`](./atlassian/) | Cliente Jira + Confluence de **solo lectura** (`atl.py`) y el único camino de escritura, a una página de Confluence, con confirmación humana (`confluence_write.py`) | [`atlassian`](../../skills-plugins/.cursor/skills/atlassian/SKILL.md) |
| [`evidence/`](./evidence/) | El núcleo reutilizable de la captura de evidencia de una ejecución: elegir la **versión de S3** que una ejecución usó de verdad, cliente AWS de solo lectura, limpieza de URLs firmadas | [`evidence`](../../skills-plugins/.cursor/skills/evidence/SKILL.md) |

```bash
cd ejemplos/metodologia/tools
uv run -q --with pytest --with boto3 python -m pytest     # offline, sin red ni credenciales
```

---

## 1. `atlassian/` — leer el tracker y la wiki, no escribirlos

`atl.py` es Python de biblioteca estándar. Tiene **una sola** función de red, `Client._get`, y solo
envía `GET`; un test falla si aparece cualquier otro método. Añadir una escritura es un cambio de
código revisable, no un flag.

```bash
python3 atlassian/atl.py jira issue PROJ-123
python3 atlassian/atl.py jira comments PROJ-123 --last 3
python3 atlassian/atl.py jira xml PROJ-123 --out data/changes/proj-123/
python3 atlassian/atl.py confluence diff docs/pagina.md <PAGE_ID>
```

Credenciales: `~/.config/<org>/jira.env` (`JIRA_BASE_URL=https://<your-site>.atlassian.net`,
`JIRA_EMAIL`, `JIRA_API_TOKEN`), `chmod 600`, **un token por persona**, escrito por la persona en su
terminal. El token nunca se imprime, ni en errores (hay test).

**Escribir en Confluence** es `confluence_write.py`, y su forma es la lección:

1. `pull <PAGE_ID>` — guarda el cuerpo vivo para editarlo.
2. `plan <PAGE_ID> nuevo.xhtml --root <ROOT_ID>` — comprueba que la página cuelga del árbol permitido
   (ancestros leídos de Confluence, no del llamante), hace **backup**, imprime el diff de texto
   visible y un **token de confirmación**.
3. El humano lee el diff y dice OK **para esa página**.
4. `apply plan.json --confirm <token>` — rechaza si el token no cuadra, si el fichero cambió desde el
   plan o si alguien editó la página en Confluence entretanto; escribe la versión N+1 (un 409 se
   reporta, nunca se reintenta) y **relee** la página para comparar.

⚠️ Lección medida en la primera escritura real: Confluence reordena los parámetros de las macros al
guardar, así que una escritura correcta se releía como "no coincide". El diff compara **texto
visible** (sin `<ac:parameter>`), pero conserva el contenido de los bloques de código — un *strip* de
etiquetas ingenuo los borraba, y un cambio dentro de un bloque de código habría pasado inadvertido.

Crear, editar, comentar o transicionar tickets de Jira: **siempre la persona**. El agente redacta.

---

## 2. `evidence/` — la evidencia de una ejecución, tal y como estaba

**Problema.** Llega "este documento falló" con una URL de la app. Reunir a mano el documento fuente,
el artefacto generado, el JSON de resultado y las líneas de log cuesta media hora, y casi siempre
se coge la versión **equivocada**: el fichero se re-subió después, o el resultado es de la ejecución
siguiente.

**Diseño (la herramienta completa vive en el proyecto; aquí está el núcleo genérico):**

- **La línea de log es el índice.** Cada ejecución escribe una línea de inicio con id de documento,
  contenedor, variante, nombre original y la clave S3 exacta de la fuente. Las líneas de error no
  llevan id, pero un *log stream* es un contenedor y un contenedor procesa una invocación a la vez: lo
  que hay entre dos líneas de inicio pertenece a la primera.
- **Versión de la fuente = la más nueva con `LastModified ≤ inicio + 60 s`**, nunca más allá de la
  siguiente ejecución sobre la misma clave. Medido: la subida que dispara la ejecución aterriza en S3
  **~1 s después** de la línea de log, así que "≤ inicio" cogía la subida *anterior*
  ([`versions.py`](./evidence/versions.py), `source_version`).
- **Artefacto y resultado = la versión escrita en `[inicio, siguiente ejecución de la misma CLAVE)`.**
  Por clave, no por documento: un fichero re-subido con otro id reutiliza las mismas claves de salida,
  y la regla "por documento" se llevaba los ficheros de la otra ejecución.
- **Depende del versionado del bucket.** `check_recovery` falla (exit 6) si el versionado no está
  `Enabled` o hay una regla de expiración: sin versiones antiguas, "la fuente tal y como estaba" deja
  de existir y la herramienta lo dice en vez de devolver la actual.
- **Solo lectura por construcción**: [`awsro.py`](./evidence/awsro.py) envuelve cada cliente boto3 y
  rechaza todo lo que no sea `get_/list_/describe_/head_/filter_log_events`; otro test escanea los
  módulos buscando métodos que escriben.
- **Las líneas de log llevan URLs pre-firmadas** con credenciales temporales:
  [`scrub.py`](./evidence/scrub.py) las limpia antes de escribir nada a disco (log, manifiesto, resumen).
- **`discover --list`** cuenta y agrupa fallos por firma (`regla:tipo:mensaje`, con ids enmascarados)
  sin descargar nada. Existe porque la primera pasada real encontró ~240 ejecuciones problemáticas en
  24 h: un `discover` que descarga habría saltado su propio límite cada mañana. Es lo que corre el
  paso 3c de `day start`.
- **La salida por defecto (`_evidence/`) no se sube al registro compartido** (`JUNK_ARGS` en
  [`../s3-sync/config.env.example`](../s3-sync/config.env.example)): puede contener documentos de
  cliente. Solo lo curado pasa a la carpeta del ticket.

⚠️⚠️ **El canario que pasó con la respuesta equivocada.** El primer `selftest` comparaba el sha256 del
fichero descargado con el de una descarga directa de "la misma" versión — y **pasaba** aunque la
herramienta elegía la versión incorrecta, porque dos subidas eran **idénticas byte a byte**. Una
comprobación calculada por la propia herramienta no puede detectar un error de selección. Ahora el
canario afirma **timestamps de versión conocidos** de antemano, y se demostró que falla con
`SOURCE_GRACE = 0`. Canary sobre una respuesta conocida, y con más de una propiedad.

Códigos de salida: 0 ok · 1 uso · 2 login (`aws sso login`, no diagnosticar) · 3 error AWS ·
4 nada encontrado · 5 guarda (estrecha `--since`) · 6 el bucket ya no garantiza versiones antiguas.
