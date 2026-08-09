#!/usr/bin/env node
/**
 * Observabilidad — vuelca el payload STDIN a un JSON (Cursor o Claude-shaped).
 *   node log_hook.js pre-log.json
 *   node log_hook.js post-log.json
 */
import fs from "node:fs";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

const outputPath = process.argv[2] || "hook-log.json";
const raw = await readStdin();
let parsed;
try {
  parsed = JSON.parse(raw || "{}");
} catch {
  parsed = { raw };
}
fs.writeFileSync(outputPath, `${JSON.stringify(parsed, null, 2)}\n`, "utf8");
process.exit(0);
