import { describe, expect, it } from "vitest";
import type { Verdict } from "@/lib/api/types";
import {
  selectFilteredVerdicts,
  selectLatestVerdict,
  selectMostSevereScopeState,
  selectSortedVerdicts,
  selectVerdictCounts,
} from "../selectors";

const mockVerdicts: Verdict[] = [
  {
    verdict_id: "v1",
    ts_unix: 1700000000,
    state: "CHANGED",
    subject: "checkout-flow",
    cause: "release",
    sentence: "Behavior shifted in v2",
    service_name: "checkout",
    version: "v2",
    baseline_version: "v1",
    flags: { behavior: true, cost: false, runaway: false },
    behavior_sigma: 4.2,
    cost_sigma: 1.1,
    samples: 100,
    falsifier: "No falsifier",
    caveats: [],
    exemplars: [{ kind: "worst", trace_id: "tr-123", z_score: 4.2, excerpt: "error log" }],
  },
  {
    verdict_id: "v2",
    ts_unix: 1700000100,
    state: "STEADY",
    subject: "search-service",
    cause: "none",
    sentence: "All parameters steady",
    service_name: "search",
    version: "v1",
    flags: { behavior: false, cost: false, runaway: false },
    behavior_sigma: 0.2,
    cost_sigma: 0.1,
    samples: 50,
    falsifier: "No falsifier",
    caveats: [],
    exemplars: [],
  },
  {
    verdict_id: "v3",
    ts_unix: 1700000200,
    state: "INCONCLUSIVE",
    subject: "payment-gw",
    cause: "traffic",
    sentence: "Traffic anomaly",
    service_name: "payment",
    version: "v3",
    flags: { behavior: false, cost: false, runaway: false },
    behavior_sigma: null,
    cost_sigma: 2.5,
    samples: 20,
    falsifier: "No falsifier",
    caveats: [],
    exemplars: [],
  },
];

describe("Verdict Selectors", () => {
  it("selectLatestVerdict returns the first verdict or null", () => {
    expect(selectLatestVerdict(mockVerdicts)).toEqual(mockVerdicts[0]);
    expect(selectLatestVerdict([])).toBeNull();
  });

  it("selectFilteredVerdicts filters by state, service, version, and text query", () => {
    // State filter
    const changedOnly = selectFilteredVerdicts(mockVerdicts, {
      state: ["CHANGED"],
      sort: "newest",
    });
    expect(changedOnly).toHaveLength(1);
    expect(changedOnly[0]?.verdict_id).toBe("v1");

    // Service filter
    const searchOnly = selectFilteredVerdicts(mockVerdicts, {
      state: [],
      service: "search",
      sort: "newest",
    });
    expect(searchOnly).toHaveLength(1);
    expect(searchOnly[0]?.verdict_id).toBe("v2");

    // Query filter matching trace ID
    const traceMatch = selectFilteredVerdicts(mockVerdicts, {
      state: [],
      q: "tr-123",
      sort: "newest",
    });
    expect(traceMatch).toHaveLength(1);
    expect(traceMatch[0]?.verdict_id).toBe("v1");
  });

  it("selectSortedVerdicts sorts by newest, oldest, and max sigma", () => {
    const oldest = selectSortedVerdicts(mockVerdicts, "oldest");
    expect(oldest[0]?.verdict_id).toBe("v1");
    expect(oldest[2]?.verdict_id).toBe("v3");

    const newest = selectSortedVerdicts(mockVerdicts, "newest");
    expect(newest[0]?.verdict_id).toBe("v3");

    const sigmaSort = selectSortedVerdicts(mockVerdicts, "sigma");
    expect(sigmaSort[0]?.verdict_id).toBe("v1"); // 4.2 behavior sigma
  });

  it("selectVerdictCounts accurately tallies states", () => {
    const counts = selectVerdictCounts(mockVerdicts);
    expect(counts).toEqual({
      STEADY: 1,
      CHANGED: 1,
      INCONCLUSIVE: 1,
      WARMING: 0,
    });
  });

  it("selectMostSevereScopeState derives highest severity", () => {
    expect(
      selectMostSevereScopeState([
        { service_name: "s1", gen_ai_system: "openai", model: "gpt-4", live: true, phase: "live", warming_progress: [10, 10], versions: ["v1"] },
        { service_name: "s2", gen_ai_system: "openai", model: "gpt-4", live: false, phase: "warming", warming_progress: [5, 10], versions: ["v1"] },
      ])
    ).toBe("WARMING");
  });
});
