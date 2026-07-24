import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import type { VerdictFiltersState } from "@/features/verdicts/selectors";
import type { VerdictState } from "@/lib/api/types";

export function useVerdictFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters: VerdictFiltersState = useMemo(() => {
    const rawState = searchParams.get("state");
    const stateList: VerdictState[] = rawState
      ? (rawState.toUpperCase().split(",") as VerdictState[])
      : [];

    const service = searchParams.get("service") || undefined;
    const version = searchParams.get("version") || undefined;
    const q = searchParams.get("q") || undefined;
    const rawSort = searchParams.get("sort");
    const sort = rawSort === "oldest" || rawSort === "sigma" ? rawSort : "newest";

    return {
      state: stateList,
      service,
      version,
      q,
      sort,
    };
  }, [searchParams]);

  const isPaused = searchParams.get("paused") === "1";

  const setFilters = useCallback(
    (updater: (prev: VerdictFiltersState) => VerdictFiltersState) => {
      setSearchParams((prevParams) => {
        const currentFilters: VerdictFiltersState = {
          state: prevParams.get("state")
            ? (prevParams.get("state")!.toUpperCase().split(",") as VerdictState[])
            : [],
          service: prevParams.get("service") || undefined,
          version: prevParams.get("version") || undefined,
          q: prevParams.get("q") || undefined,
          sort:
            prevParams.get("sort") === "oldest" || prevParams.get("sort") === "sigma"
              ? (prevParams.get("sort") as "oldest" | "sigma")
              : "newest",
        };

        const next = updater(currentFilters);
        const newParams = new URLSearchParams(prevParams);

        if (next.state.length > 0) {
          newParams.set("state", next.state.join(",").toLowerCase());
        } else {
          newParams.delete("state");
        }

        if (next.service) {
          newParams.set("service", next.service);
        } else {
          newParams.delete("service");
        }

        if (next.version) {
          newParams.set("version", next.version);
        } else {
          newParams.delete("version");
        }

        if (next.q && next.q.trim()) {
          newParams.set("q", next.q.trim());
        } else {
          newParams.delete("q");
        }

        if (next.sort !== "newest") {
          newParams.set("sort", next.sort);
        } else {
          newParams.delete("sort");
        }

        return newParams;
      });
    },
    [setSearchParams]
  );

  const toggleStateFilter = useCallback(
    (targetState: VerdictState) => {
      setFilters((prev) => {
        const hasState = prev.state.includes(targetState);
        const nextState = hasState
          ? prev.state.filter((s) => s !== targetState)
          : [...prev.state, targetState];
        return { ...prev, state: nextState };
      });
    },
    [setFilters]
  );

  const setSearchQuery = useCallback(
    (q: string) => {
      setFilters((prev) => ({ ...prev, q }));
    },
    [setFilters]
  );

  const setSort = useCallback(
    (sort: "newest" | "oldest" | "sigma") => {
      setFilters((prev) => ({ ...prev, sort }));
    },
    [setFilters]
  );

  const togglePaused = useCallback(() => {
    setSearchParams((prevParams) => {
      const newParams = new URLSearchParams(prevParams);
      if (newParams.get("paused") === "1") {
        newParams.delete("paused");
      } else {
        newParams.set("paused", "1");
      }
      return newParams;
    });
  }, [setSearchParams]);

  const clearFilters = useCallback(() => {
    setSearchParams((prevParams) => {
      const newParams = new URLSearchParams();
      if (prevParams.get("paused") === "1") {
        newParams.set("paused", "1");
      }
      return newParams;
    });
  }, [setSearchParams]);

  const hasActiveFilters = Boolean(
    filters.state.length > 0 || filters.service || filters.version || filters.q
  );

  return {
    filters,
    isPaused,
    setFilters,
    toggleStateFilter,
    setSearchQuery,
    setSort,
    togglePaused,
    clearFilters,
    hasActiveFilters,
  };
}
