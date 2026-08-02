/**
 * Cursor SDK — ejecutar un agente de forma programática (headless).
 *
 *   npm i @cursor/sdk
 *   export CURSOR_API_KEY=...
 *   npx tsx sdk.ts
 *
 * Docs: https://cursor.com/docs/sdk/typescript
 *
 * Nota: esto sustituye el ejemplo Claude Agent SDK
 * (`@anthropic-ai/claude-agent-sdk` + query()). La API no es idéntica.
 */
import { Agent } from "@cursor/sdk";

const prompt =
  "Busca queries duplicadas en el directorio ./src/queries. Solo reporta; no edites.";

const result = await Agent.prompt(prompt, {
  apiKey: process.env.CURSOR_API_KEY!,
  model: { id: "composer-2.5" },
  local: { cwd: process.cwd() },
});

console.log("status:", result.status);
console.log("\n=== RESULTADO ===\n" + (result.result ?? ""));
