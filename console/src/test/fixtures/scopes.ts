import type { Scope } from "@/lib/api/types";

export const mockScopes: Scope[] = [
  {
    service_name: "customer-support",
    gen_ai_system: "openai",
    model: "gpt-4o",
    live: true,
    phase: "calibrated",
    warming_progress: [1000, 1000],
    versions: ["v1", "v2"],
    signals: {
      behavior: { mu: 0.85, sigma: 0.12, calibrated: true },
      input: { mu: 120, sigma: 45, calibrated: true },
      cost: { mu: 0.004, sigma: 0.001, calibrated: true },
      length: { mu: 450, sigma: 120, calibrated: true },
    },
  },
  {
    service_name: "rag-summarizer",
    gen_ai_system: "anthropic",
    model: "claude-3-5-sonnet",
    live: false,
    phase: "collecting reference",
    warming_progress: [340, 1000],
    versions: ["v1"],
  },
];
