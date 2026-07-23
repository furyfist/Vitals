import { ListFilter } from "lucide-react";
import React, { useRef } from "react";
import Badge from "@/components/Badge";
import EmptyState from "@/components/EmptyState";
import type { Verdict } from "@/lib/api/types";
import FeedRow from "../FeedRow";
import FeedRowSkeleton from "../FeedRowSkeleton";

export interface VerdictFeedProps {
  verdicts: Verdict[];
  isLoading: boolean;
  density?: "comfortable" | "compact";
  focusedIndex?: number;
  onOpenDrawer: (verdictId: string) => void;
  onClearFilters?: () => void;
  hasActiveFilters?: boolean;
  className?: string;
  headerSlot?: React.ReactNode;
}

export const VerdictFeed: React.FC<VerdictFeedProps> = ({
  verdicts,
  isLoading,
  density = "comfortable",
  focusedIndex = -1,
  onOpenDrawer,
  onClearFilters,
  hasActiveFilters = false,
  className = "",
  headerSlot,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);


  if (isLoading) {
    return (
      <div className={className}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
          <h2 className="text-h2">Verdicts</h2>
        </div>
        {[...Array(6)].map((_, i) => (
          <FeedRowSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (verdicts.length === 0) {
    if (hasActiveFilters) {
      return (
        <div className={className}>
          {headerSlot}
          <EmptyState
            variant="inline"
            icon={<ListFilter size={24} aria-hidden="true" />}
            title="No verdicts match these filters"
            body="Try adjusting or clearing your filters to see results."
            action={
              onClearFilters && (
                <button
                  type="button"
                  onClick={onClearFilters}
                  style={{
                    color: "var(--color-accent)",
                    fontWeight: 500,
                    fontSize: "13px",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  Clear filters
                </button>
              )
            }
          />
        </div>
      );
    }
    return null; // Empty feed when no data at all is handled by hero card empty state
  }

  return (
    <section aria-label="Verdict feed" className={className} ref={containerRef}>
      {headerSlot || (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <h2 className="text-h2">Verdicts</h2>
            <Badge variant="neutral" size="sm">
              {verdicts.length}
            </Badge>
          </div>
        </div>
      )}

      <div role="list">
        {verdicts.map((verdict, idx) => (
          <div key={verdict.verdict_id} role="listitem">
            <FeedRow
              verdict={verdict}
              density={density}
              isFocused={idx === focusedIndex}
              onOpenDrawer={onOpenDrawer}
            />
          </div>
        ))}
      </div>
    </section>
  );
};

export default VerdictFeed;
