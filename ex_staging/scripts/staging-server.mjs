/**
 * Local staging server — started detached by deploy.mjs.
 * Serves dist/ health endpoint until staging-stop.mjs kills it.
 */
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const distApp = path.join(root, "dist", "app.js");
if (!fs.existsSync(distApp)) {
  console.error("dist/ missing — run npm run build first");
  process.exit(1);
}

const { createHandler } = await import(pathToFileURL(distApp).href);

const env = process.argv[2] || "staging";
const server = http.createServer((req, res) => {
  if (req.url === "/health" || req.url?.startsWith("/health?")) {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true, service: "ex-staging", env }));
    return;
  }
  createHandler()(req, res);
});

server.listen(0, "127.0.0.1", () => {
  const { port } = server.address();
  const url = `http://127.0.0.1:${port}`;
  fs.writeFileSync(path.join(root, ".staging-url"), url + "\n");
  fs.writeFileSync(path.join(root, ".staging-pid"), String(process.pid) + "\n");
  console.log(`staging-server listening ${url} (pid ${process.pid})`);
});
