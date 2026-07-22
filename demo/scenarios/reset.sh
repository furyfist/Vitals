#!/usr/bin/env bash
# Reset the demo to a clean v1 (healthy) state: redeploy ragapp on v1 and restart vitals
# so baselines re-warm from scratch. SigNoz data is left intact.
#
#   bash demo/scenarios/reset.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Resetting ragapp to healthy v1"
PROMPT_VERSION=v1 docker compose -f compose.yaml up -d --no-deps --build ragapp

echo "==> Restarting vitals (baselines re-warm)"
docker compose -f compose.yaml restart vitals

echo "==> Clean state. Warm the baseline before the next demo run:"
echo "    python scenarios/runaway_loop.py --rate 3 --duration 60"
