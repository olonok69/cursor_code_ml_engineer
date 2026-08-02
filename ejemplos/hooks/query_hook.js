#!/usr/bin/env node
/**
 * preToolUse — "IA revisando IA" (Cursor).
 *
 * Llama al Cursor SDK para detectar si una edición en src/queries DUPLICA
 * una query existente. Si sí → permission deny.
 *
 * Requisitos:
 *   - npm i @cursor/sdk  (o npx con el paquete disponible)
 *   - CURSOR_API_KEY en el entorno del hook
 *
 * Si falta el SDK o la key, el hook hace fail-open (allow) y escribe en stderr.
 */
import path from "node:path";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

function extractPathAndContent(payload) {
  const filePath =
    payload.tool_input?.file_path ||
    payload.tool_input?.path ||
    payload.path ||
    payload.filePath ||
    payload.args?.path ||
    "";
  const newContent =
    payload.tool_input?.content ||
    payload.tool_input?.contents ||
    payload.tool_input?.new_string ||
    payload.args?.contents ||
    payload.args?.new_string ||
    "";
  return { filePath, newContent };
}

const REVIEW_DIR = "src/queries";
const payload = JSON.parse((await readStdin()) || "{}");
const { filePath, newContent } = extractPathAndContent(payload);
if (!filePath) process.exit(0);

const normalized = path.resolve(filePath);
const queriesDir = path.resolve(process.cwd(), REVIEW_DIR);
if (!normalized.startsWith(queriesDir + path.sep)) process.exit(0);

if (!process.env.CURSOR_API_KEY) {
  console.error("query_hook: CURSOR_API_KEY missing — fail-open");
  process.exit(0);
}

let Agent;
try {
  ({ Agent } = await import("@cursor/sdk"));
} catch {
  console.error("query_hook: @cursor/sdk not installed — fail-open");
  process.exit(0);
}

const prompt = `Estás revisando un cambio propuesto a un fichero de queries de BBDD.
Fichero: ${filePath}
<new_content>
${newContent}
</new_content>
¿Este cambio DUPLICA una función de query que ya existe en ${REVIEW_DIR}?
Si sí, da feedback concreto de qué función reutilizar.
Si no, responde exactamente: "Changes look appropriate."`;

try {
  const result = await Agent.prompt(prompt, {
    apiKey: process.env.CURSOR_API_KEY,
    model: { id: "composer-2.5" },
    local: { cwd: process.cwd() },
  });
  const text = String(result.result ?? "");
  if (text.includes("Changes look appropriate")) {
    process.stdout.write(JSON.stringify({ permission: "allow" }));
    process.exit(0);
  }
  process.stdout.write(
    JSON.stringify({
      permission: "deny",
      agent_message: `Duplicación de query detectada:\n\n${text}`,
      user_message: "Query duplication hook blocked the edit.",
    }),
  );
  process.exit(0);
} catch (err) {
  console.error(`query_hook error (fail-open): ${err}`);
  process.exit(0);
}
