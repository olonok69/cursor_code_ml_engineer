import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { createHandler, healthPayload } from "../src/app.js";

test("healthPayload shape", () => {
  const p = healthPayload();
  assert.equal(p.ok, true);
  assert.equal(p.service, "ex-staging");
});

test("GET /health via handler", async () => {
  const server = http.createServer(createHandler());
  await new Promise((r) => server.listen(0, r));
  const { port } = server.address();
  const res = await fetch(`http://127.0.0.1:${port}/health`);
  const body = await res.json();
  assert.equal(res.status, 200);
  assert.equal(body.ok, true);
  await new Promise((r) => server.close(r));
});
