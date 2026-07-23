import { fetchJson } from "@/lib/api/client";
import { ENDPOINTS } from "@/lib/api/endpoints";
import type { Verdict } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";
import { useQuery, useQueryClient } from "@tanstack/react-query";

export function useVerdict(verdictId?: string) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: queryKeys.verdict(verdictId ?? ""),
    queryFn: async () => {
      if (!verdictId) throw new Error("verdictId is required");
      return fetchJson<Verdict>(ENDPOINTS.verdict(verdictId));
    },
    enabled: Boolean(verdictId),
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: 30 * 60 * 1000,
    initialData: () => {
      if (!verdictId) return undefined;
      const listData = queryClient.getQueryData<Verdict[]>(queryKeys.verdicts());
      return listData?.find((v) => v.verdict_id === verdictId);
    },
  });
}
