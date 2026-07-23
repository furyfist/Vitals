import { Activity, TriangleAlert } from "lucide-react";
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import AlertCallout from "@/components/AlertCallout";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";

import VerdictDrawer from "@/features/drawer/components/VerdictDrawer";
import HealthStrip from "@/features/health/components/HealthStrip";
import ShortcutsModal from "@/features/shortcuts/components/ShortcutsModal";
import FeedFilters from "@/features/verdicts/components/FeedFilters";
import FeedToolbar from "@/features/verdicts/components/FeedToolbar";
import HeroCardSkeleton from "@/features/verdicts/components/HeroCardSkeleton";
import HeroVerdictCard from "@/features/verdicts/components/HeroVerdictCard";
import NewVerdictsPill from "@/features/verdicts/components/NewVerdictsPill";
import VerdictFeed from "@/features/verdicts/components/VerdictFeed";
import VerdictSparkline from "@/features/verdicts/components/VerdictSparkline";

import {
  selectFilteredVerdicts,
  selectLatestVerdict,
  selectSortedVerdicts,
  selectVerdictCounts,
} from "@/features/verdicts/selectors";
import { useLocalStorage } from "@/hooks/useLocalStorage";
import { useVerdicts } from "@/hooks/useVerdicts";
import { useVerdictFilters } from "@/hooks/useVerdictFilters";
import type { VerdictState } from "@/lib/api/types";

export const ConsoleScreen: React.FC = () => {
  const navigate = useNavigate();
  const { verdictId } = useParams<{ verdictId?: string }>();

  const { filters, isPaused, toggleStateFilter, setSort, clearFilters, hasActiveFilters } =
    useVerdictFilters();

  const [density, setDensity] = useLocalStorage<"comfortable" | "compact">("density", "comfortable");
  const [isShortcutsOpen, setIsShortcutsOpen] = useState(false);

  const { data: verdicts = [], isLoading, isError, refetch } = useVerdicts({ paused: isPaused });

  const latestVerdict = selectLatestVerdict(verdicts);
  const filtered = selectFilteredVerdicts(verdicts, filters);
  const sorted = selectSortedVerdicts(filtered, filters.sort);
  const counts = selectVerdictCounts(verdicts);

  // Extract unique service names for dropdown filter
  const services = Array.from(new Set(verdicts.map((v) => v.service_name)));

  // Open / Close drawer routing helpers (§4.1)
  const handleOpenDrawer = (id: string) => {
    navigate(`/v/${encodeURIComponent(id)}`);
  };

  const handleCloseDrawer = () => {
    navigate("/");
  };

  // Keyboard shortcut listener for '?' modal (§7.1)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "?" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        setIsShortcutsOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div
      style={{
        padding: "32px var(--layout-gutter) 80px",
        maxWidth: "var(--layout-max)",
        margin: "0 auto",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-8)",
      }}
    >
      {/* Short-circuit Network Error Banner (§5.3) */}
      {isError && (
        <AlertCallout
          variant="error"
          title="Can't reach the Vitals API"
          icon={<TriangleAlert size={16} aria-hidden="true" />}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span>API call GET /api/verdicts failed. Reconnecting…</span>
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              Retry now
            </Button>
          </div>
        </AlertCallout>
      )}

      {/* Zone 1 — Hero Verdict Card (§7.1 Zone 1) */}
      {isLoading ? (
        <HeroCardSkeleton />
      ) : verdicts.length === 0 ? (
        <div style={{ backgroundColor: "var(--color-surface)", borderRadius: "var(--radius-xl)", border: "1px solid var(--color-border)", padding: "32px" }}>
          <EmptyState
            icon={<Activity size={24} aria-hidden="true" />}
            title="No verdicts yet"
            body="Vitals is listening. Send traffic through your collector and the first verdict appears here."
            hint="Receiver default port: :4327 (OTLP)"
          />
        </div>
      ) : latestVerdict ? (
        <HeroVerdictCard
          verdict={latestVerdict}
          onOpenDrawer={handleOpenDrawer}
        />
      ) : null}

      {/* SVG Sparkline (§9.2) */}
      {verdicts.length >= 2 && (
        <VerdictSparkline
          verdicts={sorted}
          onSelectVerdict={handleOpenDrawer}
        />
      )}

      {/* New Verdicts Floating Pill */}
      <NewVerdictsPill count={0} onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} />


      {/* Zone 2 — Verdict Feed (§7.1 Zone 2) */}
      {verdicts.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
            <FeedFilters
              selectedStates={filters.state}
              counts={counts}
              onToggleState={(st: VerdictState) => toggleStateFilter(st)}
            />

            <FeedToolbar
              sort={filters.sort}
              onSortChange={setSort}
              density={density}
              onDensityChange={setDensity}
              services={services}
              selectedService={filters.service}
            />
          </div>

          <VerdictFeed
            verdicts={sorted}
            isLoading={isLoading}
            density={density}
            onOpenDrawer={handleOpenDrawer}
            onClearFilters={clearFilters}
            hasActiveFilters={hasActiveFilters}
          />
        </div>
      )}

      {/* Zone 3 — Health Strip (§7.1 Zone 3) */}
      <HealthStrip isPausedManual={isPaused} />

      {/* Verdict Drawer Route (/v/:verdictId) */}
      <VerdictDrawer
        verdictId={verdictId || null}
        onClose={handleCloseDrawer}
        filteredVerdicts={sorted}
        onNavigateVerdict={handleOpenDrawer}
      />

      {/* Keyboard Shortcuts Modal (?) */}
      <ShortcutsModal
        isOpen={isShortcutsOpen}
        onClose={() => setIsShortcutsOpen(false)}
      />
    </div>
  );
};

export default ConsoleScreen;
