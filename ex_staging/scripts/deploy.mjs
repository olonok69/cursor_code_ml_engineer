/**
 * Demo staging deploy — no real cloud. Spawns a local health server from dist/.
 *
 *   node scripts/deploy.mjs staging
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const target = process.argv[2] || "staging";
if (target !== "staging") {
  console.error(`Only 'staging' is supported in this demo (got: ${target})`);
  process.exit(1);
}

const distApp = path.join(root, "dist", "app.js");
if (!fs.existsSync(distApp)) {
  console.error("dist/ missing — run: npm run build");
  process.exit(1);
}

// Stop previous demo staging if any
const pidFile = path.join(root, ".staging-pid");
if (fs.existsSync(pidFile)) {
  const oldPid = Number(fs.readFileSync(pidFile, "utf8").trim());
  if (oldPid) {
    try {
      process.kill(oldPid);
      console.log(`stopped previous staging pid ${oldPid}`);
    } catch {
      /* already dead */
    }
  }
}

const child = spawn(
  process.execPath,
  [path.join(root, "scripts", "staging-server.mjs"), target],
  {
    cwd: root,
    detached: true,
    stdio: ["ignore", "ignore", "ignore"],
  },
);
child.unref();

// Wait briefly for .staging-url
const urlFile = path.join(root, ".staging-url");
const deadline = Date.now() + 5000;
while (!fs.existsSync(urlFile) && Date.now() < deadline) {
  await new Promise((r) => setTimeout(r, 50));
}
if (!fs.existsSync(urlFile)) {
  console.error("staging server did not write .staging-url");
  process.exit(1);
}

const url = fs.readFileSync(urlFile, "utf8").trim();
console.log(`deployed → ${url}`);
console.log(`smoke with: curl -fsS ${url}/health`);
console.log(`stop with:  npm run staging:stop`);
