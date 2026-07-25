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
