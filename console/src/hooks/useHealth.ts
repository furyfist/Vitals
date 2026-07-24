import { fetchJson } from "@/lib/api/client";
import { ENDPOINTS } from "@/lib/api/endpoints";
import type { HealthSnapshot } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";
import { useQuery } from "@tanstack/react-query";

export interface UseHealthOptions {
  enabled?: boolean;
  paused?: boolean;
}

export function useHealth(options: UseHealthOptions = {}) {
  const { enabled = true, paused = false } = options;

  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: async () => {
      return fetchJson<HealthSnapshot>(ENDPOINTS.health());
    },
    staleTime: 8000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: paused ? false : 10000,
    enabled,
  });
}
