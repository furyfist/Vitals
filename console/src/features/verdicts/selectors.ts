import type { Scope, Verdict, VerdictState } from "@/lib/api/types";

export interface VerdictFiltersState {
  state: VerdictState[];
  service?: string;
  version?: string;
  q?: string;
  sort: "newest" | "oldest" | "sigma";
}

export function selectLatestVerdict(verdicts: Verdict[]): Verdict | null {
  if (!verdicts || verdicts.length === 0) return null;
  return verdicts[0] || null;
}

export function selectFilteredVerdicts(
  verdicts: Verdict[],
  filters: VerdictFiltersState
): Verdict[] {
  if (!verdicts) return [];

  return verdicts.filter((v) => {
    // State filter (comma-joined multi)
    if (filters.state.length > 0 && !filters.state.includes(v.state)) {
      return false;
    }
    // Service filter
    if (filters.service && v.service_name !== filters.service) {
      return false;
    }
    // Version filter
    if (filters.version && v.version !== filters.version) {
      return false;
    }
    // Free text query search over sentence, version, service_name, verdict_id, trace_id
    if (filters.q && filters.q.trim()) {
      const q = filters.q.toLowerCase().trim();
      const matchSentence = v.sentence.toLowerCase().includes(q);
      const matchVersion = v.version.toLowerCase().includes(q);
      const matchService = v.service_name.toLowerCase().includes(q);
      const matchId = v.verdict_id.toLowerCase().includes(q);
      const matchTrace = v.exemplars?.some((ex) =>
        ex.trace_id.toLowerCase().includes(q)
      );

      if (
        !matchSentence &&
        !matchVersion &&
        !matchService &&
        !matchId &&
        !matchTrace
      ) {
        return false;
      }
    }

    return true;
  });
}

export function selectSortedVerdicts(
  verdicts: Verdict[],
  sort: "newest" | "oldest" | "sigma"
): Verdict[] {
  const copy = [...verdicts];

  if (sort === "oldest") {
    return copy.sort((a, b) => a.ts_unix - b.ts_unix);
  }

  if (sort === "sigma") {
    return copy.sort((a, b) => {
      const maxA = Math.max(
        Math.abs(a.behavior_sigma ?? 0),
        Math.abs(a.cost_sigma ?? 0)
      );
      const maxB = Math.max(
        Math.abs(b.behavior_sigma ?? 0),
        Math.abs(b.cost_sigma ?? 0)
      );
      return maxB - maxA;
    });
  }

  // Default newest
  return copy.sort((a, b) => b.ts_unix - a.ts_unix);
}

export function selectVerdictCounts(
  verdicts: Verdict[]
): Record<VerdictState, number> {
  const counts: Record<VerdictState, number> = {
    STEADY: 0,
    CHANGED: 0,
    INCONCLUSIVE: 0,
    WARMING: 0,
  };

  if (!verdicts) return counts;

  for (const v of verdicts) {
    if (counts[v.state] !== undefined) {
      counts[v.state] += 1;
    }
  }

  return counts;
}

export function selectMostSevereScopeState(scopes: Scope[]): VerdictState {
  if (!scopes || scopes.length === 0) return "STEADY";

  const states = scopes.map((s) => (s.live ? "STEADY" : "WARMING"));

  if (states.includes("CHANGED" as VerdictState)) return "CHANGED";
  if (states.includes("INCONCLUSIVE" as VerdictState)) return "INCONCLUSIVE";
  if (states.includes("WARMING" as VerdictState)) return "WARMING";
  return "STEADY";
}
