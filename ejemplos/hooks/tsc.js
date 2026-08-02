#!/usr/bin/env node
/**
 * afterFileEdit — GATE DE CALIDAD (tipos) — Cursor.
 * Type-check tras editar .ts/.tsx. Si falla → permission deny + diagnostics.
 */
import ts from "typescript";

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

function runTypeCheck(configPath) {
  const cfg = ts.readConfigFile(configPath, ts.sys.readFile);
  if (cfg.error) return "No se pudo leer tsconfig.json";
  const parsed = ts.parseJsonConfigFileContent(cfg.config, ts.sys, process.cwd());
  const program = ts.createProgram(parsed.fileNames, {
    ...parsed.options,
    noEmit: true,
  });
  const diagnostics = ts.getPreEmitDiagnostics(program);
  if (diagnostics.length === 0) return null;
  return ts.formatDiagnosticsWithColorAndContext(diagnostics, {
    getCanonicalFileName: (f) => f,
    getCurrentDirectory: process.cwd,
    getNewLine: () => "\n",
  });
}

const payload = JSON.parse((await readStdin()) || "{}");
const file = extractPath(payload);

if (!file || !/\.(ts|tsx)$/.test(file)) process.exit(0);

const errors = runTypeCheck("./tsconfig.json");
if (errors) {
  process.stdout.write(
    JSON.stringify({
      permission: "deny",
      agent_message: `TypeScript errors — fix before continuing:\n${errors}`,
      user_message: "Typecheck failed after edit; agent must fix diagnostics.",
    }),
  );
  process.exit(0);
}

process.exit(0);
