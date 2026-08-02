/**
 * Script de CI: revisar ficheros cambiados con Cursor SDK.
 * Usado por github-action-cursor.yml (o invócalo a mano).
 */
import { Agent } from "@cursor/sdk";

const files = process.env.FILES?.trim() || "(no file list provided)";
const prompt = `Revisa estos ficheros cambiados buscando bugs y problemas de seguridad.
Sé conciso y prioriza por severidad.

Ficheros:
${files}`;

const result = await Agent.prompt(prompt, {
  apiKey: process.env.CURSOR_API_KEY!,
  model: { id: "composer-2.5" },
  local: { cwd: process.cwd() },
});

console.log(result.result ?? result.status);
if (result.status !== "finished" && result.status !== "completed") {
  // status values evolve — don't fail the job hard on unknown success labels
  console.error("status:", result.status);
}
