import type React from "react";
import { STATE_META } from "@/constants/states";
import type { VerdictState } from "@/lib/api/types";
import styles from "./StatusDot.module.css";

export interface StatusDotProps {
  state?: VerdictState | "ERROR";
  size?: 6 | 8 | 10 | 12;
  pulse?: boolean;
  color?: string;
  label?: string;
  className?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({
  state = "STEADY",
  size = 8,
  pulse = false,
  color,
  label,
  className = "",
}) => {
  const meta = STATE_META[state] || STATE_META.STEADY;
  const dotColor = color || meta.dotColor;
  const ariaLabel = label || `Status: ${meta.label}`;

  const sizeClass =
    size === 6
      ? styles.size6
      : size === 10
      ? styles.size10
      : size === 12
      ? styles.size12
      : styles.size8;

  return (
    <span
      role="status"
      aria-label={ariaLabel}
      className={`${styles.dot} ${sizeClass} ${pulse ? styles.pulse : ""} ${className}`}
      style={{ backgroundColor: dotColor }}
    />
  );
};

export default StatusDot;
