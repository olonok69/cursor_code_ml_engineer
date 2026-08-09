/**
 * Tiny Express health app — target for the `/audit` skill demo.
 */
import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";

export function createApp() {
  const app = express();
  app.get("/health", (_req, res) => {
    res.status(200).json({ ok: true, service: "ex-npm" });
  });
  return app;
}

const isMain =
  process.argv[1] &&
  path.resolve(fileURLToPath(import.meta.url)) === path.resolve(process.argv[1]);

if (isMain) {
  const port = Number(process.env.PORT || 0);
  const app = createApp();
  const server = app.listen(port, () => {
    const addr = server.address();
    const p = typeof addr === "object" && addr ? addr.port : port;
    console.log(`ex-npm listening on http://127.0.0.1:${p}`);
  });
}
