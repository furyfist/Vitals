export const ENDPOINTS = {
  verdicts: (limit = 50) => `/api/verdicts?limit=${limit}`,
  verdict: (id: string) => `/api/verdicts/${encodeURIComponent(id)}`,
  scopes: () => "/api/scopes",
  health: () => "/api/health",
} as const;
