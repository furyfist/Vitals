import { QueryClient } from "@tanstack/react-query";

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: 3,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 8000),
        refetchOnWindowFocus: true,
        refetchIntervalInBackground: false,
        structuralSharing: true,
      },
    },
  });
}

export const queryClient = createQueryClient();
