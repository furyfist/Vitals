import { fetchJson } from "@/lib/api/client";
import { ENDPOINTS } from "@/lib/api/endpoints";
import type { Scope } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";
import { useQuery } from "@tanstack/react-query";

export interface UseScopesOptions {
  enabled?: boolean;
  paused?: boolean;
}

export function useScopes(options: UseScopesOptions = {}) {
  const { enabled = true, paused = false } = options;

  return useQuery({
    queryKey: queryKeys.scopes(),
    queryFn: async () => {
      const res = await fetchJson<{ scopes: Scope[] }>(ENDPOINTS.scopes());
      return res.scopes;
    },
    staleTime: 4000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: paused ? false : 5000,
    enabled,
  });
}
