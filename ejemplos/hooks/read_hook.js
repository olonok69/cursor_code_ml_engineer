#!/usr/bin/env node
/**
 * PreToolUse hook (matcher: Read|Grep) — HOOK DE SEGURIDAD.
 *
 * Bloquea que el agente lea ficheros de secretos (.env).
 *
 * Contrato de un hook:
 *   - Recibe el payload JSON de la tool por STDIN.
 *   - exit 0  -> permite la operación.
 *   - exit 2  -> la BLOQUEA y devuelve stderr a Claude como feedback.
 */
async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

const payload = JSON.parse(await readStdin());
const readPath =
  payload.tool_input?.file_path || payload.tool_input?.path || "";

if (readPath.includes(".env")) {
  console.error("Bloqueado: no puedes leer el fichero .env (contiene secretos).");
  process.exit(2); // <-- bloquea
}

process.exit(0); // <-- permite
