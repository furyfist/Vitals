import { act, renderHook } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { useVerdictFilters } from "../useVerdictFilters";

describe("useVerdictFilters Hook", () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={["/?state=changed&q=checkout"]}>{children}</MemoryRouter>
  );

  it("reads initial filter state from URL search params", () => {
    const { result } = renderHook(() => useVerdictFilters(), { wrapper });

    expect(result.current.filters.state).toEqual(["CHANGED"]);
    expect(result.current.filters.q).toBe("checkout");
    expect(result.current.hasActiveFilters).toBe(true);
  });

  it("toggles state filter and clears active filters", () => {
    const { result } = renderHook(() => useVerdictFilters(), { wrapper });

    act(() => {
      result.current.toggleStateFilter("STEADY");
    });
    expect(result.current.filters.state).toContain("STEADY");

    act(() => {
      result.current.clearFilters();
    });
    expect(result.current.filters.state).toEqual([]);
    expect(result.current.filters.q).toBeUndefined();
    expect(result.current.hasActiveFilters).toBe(false);
  });
});
