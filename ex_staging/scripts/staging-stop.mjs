import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pidFile = path.join(root, ".staging-pid");
const urlFile = path.join(root, ".staging-url");

if (!fs.existsSync(pidFile)) {
  console.log("no staging process recorded");
  process.exit(0);
}
const pid = Number(fs.readFileSync(pidFile, "utf8").trim());
try {
  process.kill(pid);
  console.log(`stopped staging pid ${pid}`);
} catch {
  console.log(`pid ${pid} already stopped`);
}
fs.rmSync(pidFile, { force: true });
fs.rmSync(urlFile, { force: true });
