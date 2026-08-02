/**
 * Claude Agent SDK — ejecutar a Claude Code de forma programática (headless).
 *
 * El paquete "@anthropic-ai/claude-code" se renombró a "@anthropic-ai/claude-agent-sdk".
 * Ejecutar con:  npx tsx sdk.ts
 *
 * `query()` devuelve un async iterator de mensajes. `options.allowedTools`
 * restringe qué puede hacer el agente: aquí solo se le permite `Edit`.
 */
import { query } from "@anthropic-ai/claude-agent-sdk";

const prompt = "Busca queries duplicadas en el directorio ./src/queries";

for await (const message of query({
  prompt,
  options: {
    allowedTools: ["Edit"], // acceso mínimo: principio de menor privilegio
  },
})) {
  console.log(JSON.stringify(message, null, 2));

  if (message.type === "result") {
    console.log("\n=== RESULTADO ===\n" + message.result);
  }
}
