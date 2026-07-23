import { describe, expect, it } from "vitest";
import { fetchJson } from "./client";

describe("api client", () => {
  it("fetches json successfully from MSW handlers", async () => {
    const data = await fetchJson<{ verdicts: unknown[] }>("/api/verdicts");
    expect(data.verdicts).toBeDefined();
    expect(Array.isArray(data.verdicts)).toBe(true);
  });
});
