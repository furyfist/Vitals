import type React from "react";
import { useCountUp } from "@/hooks/useCountUp";
import { formatNumber } from "@/lib/format/number";
import Tooltip from "../Tooltip";
import styles from "./MetricChip.module.css";

export interface MetricChipProps {
  label: string;
  value: number;
  variant?: "default" | "error";
  tooltip?: string;
  className?: string;
}

export const MetricChip: React.FC<MetricChipProps> = ({
  label,
  value,
  variant = "default",
  tooltip,
  className = "",
}) => {
  const animatedValue = useCountUp(value);
  const formattedValue = formatNumber(animatedValue);

  const content = (
    <div
      className={`${styles.chip} ${
        variant === "error" ? styles.variantError : ""
      } ${className}`}
    >
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>{formattedValue}</span>
    </div>
  );

  if (tooltip) {
    return <Tooltip content={tooltip}>{content}</Tooltip>;
  }

  return content;
};

export default MetricChip;
