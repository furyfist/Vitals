import { motion } from "motion/react";
import type React from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { formatSigma } from "@/lib/format/sigma";
import styles from "./SigmaMeter.module.css";

export interface SigmaMeterProps {
  label: string; // e.g. "behavior" or "cost"
  sigma: number | null | undefined;
  variant?: "hero" | "compact";
  type?: "behavior" | "cost";
  className?: string;
}

export const SigmaMeter: React.FC<SigmaMeterProps> = ({
  label,
  sigma,
  variant = "hero",
  type = "behavior",
  className = "",
}) => {
  const reducedMotion = useReducedMotion();
  const formattedValue = formatSigma(sigma);

  const isNull = sigma === null || sigma === undefined;
  const absSigma = isNull ? 0 : Math.abs(sigma);
  const isFlat = !isNull && absSigma < 1.0;
  const isClamped = absSigma > 6.0;

  // Domain fixed 0..6σ
  const percentage = Math.min(100, (absSigma / 6.0) * 100);

  const fillColor = isFlat
    ? "var(--color-text-tertiary)"
    : type === "behavior"
    ? "var(--chart-1)"
    : "var(--chart-2)";

  const isHero = variant === "hero";

  return (
    <div className={`${styles.wrapper} ${className}`}>
      <span className={styles.label}>{label}</span>
      <div className={styles.valueContainer}>
        <span className={isHero ? styles.valueHero : styles.valueCompact}>
          {formattedValue}
        </span>
        {isClamped && <span style={{ color: "var(--color-text-tertiary)" }}>»</span>}
      </div>

      <div
        role="meter"
        aria-label={`${label} sigma`}
        aria-valuenow={isNull ? 0 : sigma}
        aria-valuemin={0}
        aria-valuemax={6}
        aria-valuetext={formattedValue}
        className={isHero ? styles.trackHero : styles.trackCompact}
      >
        <div className={styles.thresholdTick} title="3σ threshold" />
        <motion.div
          className={styles.fill}
          style={{ backgroundColor: fillColor }}
          initial={reducedMotion ? { width: `${percentage}%` } : { width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{
            duration: reducedMotion ? 0 : 0.46,
            ease: [0.22, 1, 0.36, 1],
          }}
        />
      </div>

      {isHero && <span className={styles.trailingHint}>normal ±1σ</span>}
    </div>
  );
};

export default SigmaMeter;
