/** App source — built into dist/ for the staging deploy demo. */
export function healthPayload() {
  return { ok: true, service: "ex-staging", env: "local" };
}

export function createHandler() {
  return (req, res) => {
    if (req.url === "/health" || req.url?.startsWith("/health?")) {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify(healthPayload()));
      return;
    }
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: false, error: "not_found" }));
  };
}
