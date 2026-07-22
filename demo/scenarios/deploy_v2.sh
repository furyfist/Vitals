#!/usr/bin/env bash
# Scenario 2 — the quality payoff. Deploy the poisoned v2 prompt with NO model change.
# Infra stays green, tokens stay normal, but the quality-drift line bends, the CUSUM
# onset marker appears, Release Compare splits v1/v2, and the drift alert pages.
#
#   bash demo/scenarios/deploy_v2.sh
#
# Then drive traffic (runaway_loop.py or steady curls) and watch the Drift dashboard.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Deploying poisoned prompt v2 (service.version=v2, same model)"
PROMPT_VERSION=v2 docker compose -f compose.yaml up -d --no-deps --build ragapp

echo "==> ragapp now serving v2. Send traffic and watch quality drift onset:"
echo "    python scenarios/runaway_loop.py --rate 5 --duration 180"
echo "==> Compare v1 vs v2 on the Release Compare dashboard."
