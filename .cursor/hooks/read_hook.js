#!/usr/bin/env node
/**
 * beforeReadFile / preToolUse — HOOK DE SEGURIDAD (Cursor).
 * Bloquea lectura de ficheros .env (secretos).
 *
 * Respuesta Cursor: JSON con permission deny|ask|allow (stdout), exit 0.
 * exit 2 también deniega.
 * ESM (import) para que top-level await sea válido en Node.
 */
import process from "node:process";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

function extractPath(payload) {
  return (
    payload.path ||
    payload.filePath ||
    payload.file_path ||
    payload.uri ||
    payload.tool_input?.file_path ||
    payload.tool_input?.path ||
    payload.args?.path ||
    ""
  );
}

const raw = await readStdin();
let payload = {};
try {
  payload = JSON.parse(raw || "{}");
} catch {
  process.stdout.write(JSON.stringify({ permission: "allow" }));
  process.exit(0);
}

const readPath = String(extractPath(payload));
if (readPath.includes(".env")) {
  process.stdout.write(
    JSON.stringify({
      permission: "deny",
      user_message: "Blocked: agent tried to read a .env file.",
      agent_message:
        "Bloqueado: no puedes leer ficheros .env (contienen secretos). Usa secretos vía env del proceso o un vault, no leas el fichero.",
    }),
  );
  process.exit(0);
}

process.stdout.write(JSON.stringify({ permission: "allow" }));
process.exit(0);
