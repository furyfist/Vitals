import type { HealthSnapshot } from "@/lib/api/types";

export const mockHealth: HealthSnapshot = {
  spans_received: 12450,
  spans_scored: 11800,
  spans_skipped: 650,
  scopes_active: 2,
  verdicts_emitted: 18,
  emit_errors: 0,
  uptime_seconds: 86400,
  version: "0.2.0",
  receiver_port: 4327,
};
