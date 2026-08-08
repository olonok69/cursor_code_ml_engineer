#!/usr/bin/env node
/**
 * beforeShellExecution — pide confirmación humana ante push/PR/deploy.
 * ESM (import) para que top-level await sea válido en Node.
 */
import process from "node:process";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

const raw = await readStdin();
const payload = JSON.parse(raw || "{}");
const command = String(payload.command || "");

const patterns = [
  /git\s+push/i,
  /gh\s+pr\s+create/i,
  /gh\s+pr\s+merge/i,
  /terraform\s+apply/i,
  /kubectl\s+apply/i,
  /helm\s+upgrade/i,
];

if (patterns.some((re) => re.test(command))) {
  process.stdout.write(
    JSON.stringify({
      permission: "ask",
      user_message:
        "Methodology handoff gate: outward-facing command. Approve only if you explicitly want the agent to run it.",
      agent_message:
        "External/irreversible action — wait for human confirmation. Prefer preparing the branch + handover.",
    }),
  );
  process.exit(0);
}

process.stdout.write(JSON.stringify({ permission: "allow" }));
process.exit(0);
