export type VerdictState = "STEADY" | "CHANGED" | "INCONCLUSIVE" | "WARMING";

export interface Exemplar {
  kind: "worst" | "median";
  trace_id: string;
  z_score: number | null;
  excerpt: string;
  signoz_url?: string;
}

export interface Verdict {
  verdict_id: string;
  state: VerdictState;
  sentence: string;
  service_name: string;
  version: string;
  baseline_version?: string | null;
  subject: string;
  cause: string;
  flags: {
    behavior: boolean;
    cost: boolean;
    runaway: boolean;
  };
  behavior_sigma: number | null;
  cost_sigma: number | null;
  input_sigma?: number | null;
  length_sigma?: number | null;
  cost_usd_per_req?: number | null;
  baseline_cost_usd_per_req?: number | null;
  velocity_ratio?: number | null;
  ts_unix: number;
  onset_ts_unix?: number | null;
  seconds_after_deploy?: number | null;
  samples: number;
  baseline_samples?: number | null;
  falsifier: string;
  caveats: string[];
  inconclusive_reason?: string | null;
  exemplars: Exemplar[];
}

export interface ScopeSignal {
  mu: number;
  sigma: number;
  calibrated: boolean;
}

export interface Scope {
  service_name: string;
  gen_ai_system: string;
  model: string;
  live: boolean;
  phase: string;
  warming_progress: [number, number]; // [have, need]
  versions: string[];
  signals?: {
    behavior?: ScopeSignal;
    input?: ScopeSignal;
    cost?: ScopeSignal;
    length?: ScopeSignal;
  };
}

export interface HealthSnapshot {
  spans_received: number;
  spans_scored: number;
  spans_skipped: number;
  scopes_active: number;
  verdicts_emitted: number;
  emit_errors: number;
  uptime_seconds: number;
  version: string;
  receiver_port?: number;
}

export interface ApiError {
  status: number;
  message: string;
  endpoint: string;
}
