#!/usr/bin/env node
/**
 * PostToolUse hook (matcher: Write|Edit|MultiEdit) — GATE DE CALIDAD (formato).
 *
 * Formatea con prettier el fichero que Claude acaba de editar.
 * Es NO-BLOQUEANTE a propósito: el formateo nunca debe frenar la edición.
 *
 * Nota importante sobre el payload:
 *   - En PostToolUse el resultado real está en tool_response (p. ej. filePath).
 *   - En PreToolUse solo tienes la intención en tool_input.file_path.
 */
import { execFileSync } from "node:child_process";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

const payload = JSON.parse(await readStdin());
const filePath =
  payload.tool_response?.filePath || payload.tool_input?.file_path;

if (filePath) {
  try {
    execFileSync("npx", ["--yes", "prettier", "--write", filePath], {
      stdio: "ignore",
    });
  } catch {
    // No-bloqueante por diseño: si prettier falla, no rompemos la operación.
  }
}

process.exit(0);
