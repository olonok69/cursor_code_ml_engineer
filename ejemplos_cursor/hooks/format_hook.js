#!/usr/bin/env node
/**
 * afterFileEdit — GATE DE CALIDAD (formato) — Cursor.
 * prettier --write sobre el fichero editado. NO-BLOQUEANTE.
 */
import { execFileSync } from "node:child_process";

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
    payload.tool_response?.filePath ||
    payload.tool_input?.file_path ||
    ""
  );
}

const payload = JSON.parse((await readStdin()) || "{}");
const filePath = extractPath(payload);

if (filePath) {
  try {
    execFileSync("npx", ["--yes", "prettier", "--write", filePath], {
      stdio: "ignore",
    });
  } catch {
    // No-bloqueante por diseño
  }
}

process.exit(0);
