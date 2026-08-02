#!/usr/bin/env node
/**
 * Hook de OBSERVABILIDAD (se engancha a * en PreToolUse y PostToolUse).
 *
 * Vuelca el payload que recibe por STDIN a un fichero JSON. El nombre del
 * fichero se pasa como argumento, de modo que el MISMO script sirve para
 * varios eventos:
 *   node ./hooks/log_hook.js pre-log.json    (en PreToolUse)
 *   node ./hooks/log_hook.js post-log.json   (en PostToolUse)
 *
 * Es no-bloqueante: siempre termina en exit 0.
 */
import fs from "node:fs";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

const outputPath = process.argv[2] || "hook-log.json";
const parsed = JSON.parse(await readStdin());
fs.writeFileSync(outputPath, `${JSON.stringify(parsed, null, 2)}\n`, "utf8");
process.exit(0);
