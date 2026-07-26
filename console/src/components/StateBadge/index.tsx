import type React from "react";
import { STATE_META } from "@/constants/states";
import type { VerdictState } from "@/lib/api/types";
import Badge, { type BadgeSize } from "../Badge";
import StatusDot from "../StatusDot";

export interface StateBadgeProps {
  state: VerdictState | "ERROR";
  size?: BadgeSize;
  showIcon?: boolean;
  showDot?: boolean;
  count?: number;
  className?: string;
}

export const StateBadge: React.FC<StateBadgeProps> = ({
  state,
  size = "md",
  showIcon = false,
  showDot = true,
  count,
  className = "",
}) => {
  const meta = STATE_META[state] || STATE_META.STEADY;
  const IconComponent = meta.icon;

  const variant =
    state === "STEADY"
      ? "success"
      : state === "CHANGED"
      ? "warning"
      : state === "INCONCLUSIVE"
      ? "info"
      : state === "ERROR"
      ? "error"
      : "neutral";

  const leadingIcon = showIcon ? (
    <IconComponent size={size === "sm" ? 12 : 14} aria-hidden={true} />
  ) : showDot ? (
    <StatusDot state={state} size={size === "sm" ? 6 : 8} label={meta.label} />
  ) : undefined;


  return (
    <Badge variant={variant} size={size} icon={leadingIcon} className={className}>
      <span>{meta.label}</span>
      {count !== undefined && <span style={{ opacity: 0.85 }}>({count})</span>}
    </Badge>
  );
};

export default StateBadge;
