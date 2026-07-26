import type React from "react";
import styles from "./ProgressBar.module.css";

export interface ProgressBarProps {
  value?: number; // 0..100 for determinate
  max?: number;
  variant?: "determinate" | "indeterminate";
  label?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value = 0,
  max = 100,
  variant = "determinate",
  label = "Progress",
  className = "",
}) => {
  const isIndeterminate = variant === "indeterminate";
  const percentage = Math.min(Math.max(0, (value / max) * 100), 100);

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={isIndeterminate ? undefined : Math.round(percentage)}
      aria-valuemin={isIndeterminate ? undefined : 0}
      aria-valuemax={isIndeterminate ? undefined : 100}
      className={`${styles.track} ${className}`}
    >
      {isIndeterminate ? (
        <div className={`${styles.fill} ${styles.indeterminate}`} />
      ) : (
        <div className={styles.fill} style={{ width: `${percentage}%` }} />
      )}
    </div>
  );
};

export default ProgressBar;
