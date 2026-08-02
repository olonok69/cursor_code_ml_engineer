#!/usr/bin/env node
/**
 * PostToolUse hook (matcher: Write|Edit|MultiEdit) — GATE DE CALIDAD (tipos).
 *
 * Ejecuta el type-check de TypeScript tras cada edición. Si hay errores de
 * tipo, BLOQUEA (exit 2) y devuelve los diagnósticos a Claude para que los
 * corrija en el mismo turno. Este es el patrón "el hook mantiene al agente
 * dentro de las líneas": el modelo no puede seguir dejando el árbol roto.
 */
import ts from "typescript";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

function runTypeCheck(configPath) {
  const cfg = ts.readConfigFile(configPath, ts.sys.readFile);
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

const payload = JSON.parse(await readStdin());
const file = payload.tool_response?.filePath || payload.tool_input?.file_path;

// Solo actuar sobre ficheros .ts/.tsx.
if (!file || !/\.(ts|tsx)$/.test(file)) process.exit(0);

const errors = runTypeCheck("./tsconfig.json");
if (errors) {
  console.error(errors); // <-- vuelve a Claude
  process.exit(2); // <-- bloquea hasta que compile
}

process.exit(0);
