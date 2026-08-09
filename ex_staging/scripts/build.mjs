/**
 * Fake "build" — copies src into dist/ (no bundler needed for the course demo).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const src = path.join(root, "src");
const dist = path.join(root, "dist");

fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist, { recursive: true });
for (const name of fs.readdirSync(src)) {
  fs.copyFileSync(path.join(src, name), path.join(dist, name));
}
fs.writeFileSync(
  path.join(dist, "build-info.json"),
  JSON.stringify(
    { builtAt: new Date().toISOString(), service: "ex-staging" },
    null,
    2,
  ) + "\n",
);
console.log("build OK → dist/");
