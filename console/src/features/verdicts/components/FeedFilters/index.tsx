import type React from "react";
import StatusDot from "@/components/StatusDot";
import ToggleChip from "@/components/ToggleChip";
import { STATE_META } from "@/constants/states";
import type { VerdictState } from "@/lib/api/types";

export interface FeedFiltersProps {
  selectedStates: VerdictState[];
  counts: Record<VerdictState, number>;
  onToggleState: (state: VerdictState) => void;
  className?: string;
}

const ALL_STATES: VerdictState[] = ["STEADY", "CHANGED", "INCONCLUSIVE", "WARMING"];

export const FeedFilters: React.FC<FeedFiltersProps> = ({
  selectedStates,
  counts,
  onToggleState,
  className = "",
}) => {
  return (
    <div
      className={className}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        flexWrap: "wrap",
      }}
    >
      {ALL_STATES.map((st) => {
        const isPressed = selectedStates.includes(st);
        const meta = STATE_META[st];
        const count = counts[st] || 0;

        return (
          <ToggleChip
            key={st}
            pressed={isPressed}
            onPressedChange={() => onToggleState(st)}
            icon={<StatusDot state={st} size={6} />}
          >
            <span>{meta.label}</span>
            <span style={{ opacity: 0.7, fontSize: "11px" }}>({count})</span>
          </ToggleChip>
        );
      })}
    </div>
  );
};

export default FeedFilters;
