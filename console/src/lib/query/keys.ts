export const queryKeys = {
  all: ["vitals"] as const,
  verdicts: () => [...queryKeys.all, "verdicts"] as const,
  verdict: (id: string) => [...queryKeys.all, "verdict", id] as const,
  scopes: () => [...queryKeys.all, "scopes"] as const,
  health: () => [...queryKeys.all, "health"] as const,
};
