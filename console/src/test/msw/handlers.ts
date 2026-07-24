import { http, HttpResponse } from "msw";
import { mockHealth } from "../fixtures/health";
import { mockScopes } from "../fixtures/scopes";
import { mockVerdicts } from "../fixtures/verdicts";

export const handlers = [
  http.get("/api/verdicts", () => {
    return HttpResponse.json({ verdicts: mockVerdicts });
  }),

  http.get("/api/verdicts/:id", ({ params }) => {
    const verdict = mockVerdicts.find((v) => v.verdict_id === params.id);
    if (!verdict) {
      return HttpResponse.json({ error: "verdict not found" }, { status: 404 });
    }
    return HttpResponse.json(verdict);
  }),

  http.get("/api/scopes", () => {
    return HttpResponse.json({ scopes: mockScopes });
  }),

  http.get("/api/health", () => {
    return HttpResponse.json(mockHealth);
  }),
];
