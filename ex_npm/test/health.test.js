import test from "node:test";
import assert from "node:assert/strict";
import { createApp } from "../index.js";

test("GET /health returns ok", async () => {
  const app = createApp();
  const server = app.listen(0);
  await new Promise((r) => server.once("listening", r));
  const { port } = server.address();
  const res = await fetch(`http://127.0.0.1:${port}/health`);
  const body = await res.json();
  assert.equal(res.status, 200);
  assert.equal(body.ok, true);
  assert.equal(body.service, "ex-npm");
  await new Promise((r) => server.close(r));
});
