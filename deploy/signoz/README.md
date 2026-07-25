# SigNoz (Foundry-managed)

SigNoz itself — ClickHouse, the metastore, the ingester, the control plane, and the
MCP server — is deployed by [Foundry](https://github.com/SigNoz/foundry), not by a
hand-maintained compose file. This directory holds Foundry's declarative input
(`casting.yaml`) and its resolved output (`casting.yaml.lock`, `pours/`), committed so
judges can reproduce the exact deployment `foundryctl` produced here.

`casting.yaml` enables the MCP server (`spec.mcp.spec.enabled: true`) alongside the
default Docker Compose flavor.

## Deploy

```bash
curl -fsSL https://signoz.io/foundry.sh | bash    # installs foundryctl, if not already present
cd deploy/signoz
foundryctl cast -f casting.yaml -p ./pours
```

`cast` runs `gauge` (checks Docker is available), `forge` (regenerates `pours/` and
`casting.yaml.lock` from `casting.yaml` — already committed here, so this step should
be a no-op unless `casting.yaml` changed), then brings the stack up. SigNoz's UI is at
`http://localhost:8080`.

**Before sending any telemetry**, open `http://localhost:8080` and complete the
signup wizard. The ingester (`signoz-ingester`, OTLP ports 4317/4318) only receives
its real pipeline config from the control plane after an org/admin account exists —
before that, every span and metric sent to it is silently dropped. See
[../../demo/README.md](../../demo/README.md) for the full demo bootstrap sequence.

This deployment is owned by Foundry; do not hand-edit `pours/` or
`casting.yaml.lock` — change `casting.yaml` and re-run `forge`.

## MCP server

Enabled via `spec.mcp.spec.enabled: true` in `casting.yaml`; forged as the `signoz-mcp`
container, HTTP transport on `http://localhost:8000/mcp`.

Two things to know:

- **`docker ps` will show it as `unhealthy`.** This is a packaging bug in Foundry's
  forged healthcheck, not a real outage: it execs `wget --spider` inside a container
  image that doesn't ship `wget` (`exec: "wget": executable file not found in $PATH`).
  The endpoint itself is live — `curl http://localhost:8000/livez` returns `200`, and
  a raw MCP `initialize` POST to `/mcp` gets a real protocol response, not a connection
  error. This lives in Foundry's generated `pours/`, not in `casting.yaml`, so there's
  no config knob to fix it from here.
- **It needs a SigNoz API key to actually answer queries** (confirmed: without one,
  `/mcp` responds `"Authorization or SIGNOZ-API-KEY header required"`). Create one
  yourself — Settings -> Service Accounts -> (existing account, or New Service Account)
  -> New Key — then either pass it per-request as the `SIGNOZ-API-KEY` header, or bake
  it into the deployment by adding to `casting.yaml`:

  ```yaml
  spec:
    mcp:
      spec:
        enabled: true
        env:
          SIGNOZ_API_KEY: "<your key>"
  ```

  and re-running `forge`. Minting the key isn't something to script or commit —
  do it once in the UI and keep it out of version control.

To point Claude Code at it: `claude mcp add --scope user --transport http signoz http://localhost:8000/mcp` (add `-e SIGNOZ-API-KEY=<key>` if your client needs the header set explicitly rather than prompting).
