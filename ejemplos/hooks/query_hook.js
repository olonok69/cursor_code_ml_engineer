#!/usr/bin/env node
/**
 * PreToolUse hook (matcher: Write|Edit|MultiEdit, timeout: 300) — "IA revisando IA".
 *
 * El ejemplo estrella: un hook que a su vez llama al Claude Agent SDK para
 * decidir si la edición propuesta DUPLICA una función de query ya existente.
 * Si detecta duplicación, bloquea (exit 2) y explica por qué.
 *
 * El timeout del hook está a 300s en settings.json porque este hook hace una
 * llamada a un modelo (no es instantáneo como los demás).
 */
import path from "node:path";
import { query } from "@anthropic-ai/claude-agent-sdk";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

const REVIEW_DIR = "src/queries";
const payload = JSON.parse(await readStdin());
const toolInput = payload.tool_input ?? {};
const filePath = toolInput.file_path;
if (!filePath) process.exit(0);

// Actuar solo sobre ficheros dentro de src/queries.
const normalized = path.resolve(filePath);
const queriesDir = path.resolve(process.cwd(), REVIEW_DIR);
if (!normalized.startsWith(queriesDir + path.sep)) process.exit(0);

const newContent =
  toolInput.content || toolInput.contents || toolInput.new_string || "";

const prompt = `Estás revisando un cambio propuesto a un fichero de queries de BBDD.
Fichero: ${filePath}
<new_content>
${newContent}
</new_content>
¿Este cambio DUPLICA una función de query que ya existe en ${REVIEW_DIR}?
Si sí, da feedback concreto de qué función reutilizar.
Si no, responde exactamente: "Changes look appropriate."`;

const messages = [];
for await (const message of query({ prompt })) messages.push(message);
const result = messages.find((m) => m.type === "result");

if (!result || result.result.includes("Changes look appropriate")) {
  process.exit(0);
}

console.error(`Duplicación de query detectada:\n\n${result.result}`);
process.exit(2); // <-- bloquea la edición y explica el motivo
