# ex_staging — mini app for `/deploy-staging`

Tiny Node app used to demo a **safe staging deploy gate** (tests → build → human OK → local “staging” → smoke).

There is **no real cloud deploy**. `scripts/deploy.mjs` starts a local health server from `dist/`.

## Install & preflight

```powershell
cd ex_staging
npm install   # no runtime deps; lock optional
npm test
npm run build
```

## Manual dry-run (after human confirmation in the skill)

```powershell
npm run deploy:staging
# read URL from .staging-url, then:
curl -fsS ((Get-Content .staging-url).Trim() + "/health")
npm run staging:stop
```

## Course usage

```text
/deploy-staging @ex_staging
```

The skill must **stop and ask** before running deploy. See [`DEMO_RUNBOOK.md`](../DEMO_RUNBOOK.md).
