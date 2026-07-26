import { fetchJson } from "@/lib/api/client";
import { ENDPOINTS } from "@/lib/api/endpoints";
import type { Verdict } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";
import { useQuery } from "@tanstack/react-query";

export interface UseVerdictsOptions {
  enabled?: boolean;
  paused?: boolean;
}

export function useVerdicts(options: UseVerdictsOptions = {}) {
  const { enabled = true, paused = false } = options;

  return useQuery({
    queryKey: queryKeys.verdicts(),
    queryFn: async () => {
      const res = await fetchJson<{ verdicts: Verdict[] }>(ENDPOINTS.verdicts(50));
      return res.verdicts;
    },
    staleTime: 1500,
    gcTime: 5 * 60 * 1000,
    refetchInterval: paused ? false : 2000,
    enabled: enabled,
  });
}
