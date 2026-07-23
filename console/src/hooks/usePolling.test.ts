import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { usePolling } from "./usePolling";

describe("usePolling hook", () => {
  it("returns isPolling true when not paused, online and tab visible", () => {
    const { result } = renderHook(() => usePolling(false));
    expect(result.current.isPolling).toBe(true);
    expect(result.current.isPausedManual).toBe(false);
  });

  it("returns isPolling false when manually paused", () => {
    const { result } = renderHook(() => usePolling(true));
    expect(result.current.isPolling).toBe(false);
    expect(result.current.isPausedManual).toBe(true);
  });
});
