import { motion } from "motion/react";
import React, { useRef, useState } from "react";
import StateBadge from "@/components/StateBadge";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import type { Verdict } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/format/relativeTime";
import { formatSigma } from "@/lib/format/sigma";
import styles from "./VerdictSparkline.module.css";

export interface VerdictSparklineProps {
  verdicts: Verdict[];
  onSelectVerdict?: (verdictId: string) => void;
  className?: string;
}

export const VerdictSparkline: React.FC<VerdictSparklineProps> = ({
  verdicts,
  onSelectVerdict,
  className = "",
}) => {
  const reducedMotion = useReducedMotion();
  const [showBehavior, setShowBehavior] = useState(true);
  const [showCost, setShowCost] = useState(true);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Hidden if less than 2 verdicts (§9.2 empty rule)
  if (!verdicts || verdicts.length < 2) {
    return null;
  }

  // Order oldest to newest for sparkline timeline x-axis
  const timelineVerdicts = [...verdicts].reverse();
  const n = timelineVerdicts.length;

  const width = 1000;
  const height = 72;
  const paddingY = 8;
  const usableHeight = height - paddingY * 2;

  // Y domain: fixed -1 to 6 (range 7)
  const minY = -1;
  const maxY = 6;
  const getY = (val: number) => {
    const clamped = Math.min(maxY, Math.max(minY, val));
    const ratio = (clamped - minY) / (maxY - minY);
    return height - paddingY - ratio * usableHeight;
  };

  const getX = (idx: number) => {
    if (n <= 1) return width / 2;
    return (idx / (n - 1)) * width;
  };

  // Y positions for threshold lines
  const y3 = getY(3); // 3σ threshold
  const y6 = getY(6); // 6σ top

  // Build SVG path segments with null breaks
  const buildPath = (values: (number | null)[]) => {
    let path = "";
    let inSubpath = false;

    values.forEach((v, idx) => {
      if (v === null || v === undefined) {
        inSubpath = false;
      } else {
        const x = getX(idx);
        const y = getY(v);
        if (!inSubpath) {
          path += `M ${x.toFixed(1)} ${y.toFixed(1)} `;
          inSubpath = true;
        } else {
          path += `L ${x.toFixed(1)} ${y.toFixed(1)} `;
        }
      }
    });

    return path.trim();
  };

  const behaviorValues = timelineVerdicts.map((v) => v.behavior_sigma);
  const costValues = timelineVerdicts.map((v) => v.cost_sigma);

  const behaviorPath = buildPath(behaviorValues);
  const costPath = buildPath(costValues);

  const rafRef = useRef<number | null>(null);

  // Mouse hover tracking throttled via rAF (§9.2)
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!containerRef.current) return;
    const clientX = e.clientX;

    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    rafRef.current = requestAnimationFrame(() => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = clientX - rect.left;
      const ratio = Math.max(0, Math.min(1, mouseX / rect.width));
      const closestIdx = Math.round(ratio * (n - 1));
      setHoverIndex(closestIdx);
    });
  };

  const handleMouseLeave = () => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
    setHoverIndex(null);
  };

  const hoveredVerdict = hoverIndex !== null ? timelineVerdicts[hoverIndex] : null;
  const hoverXPercent = hoverIndex !== null ? (hoverIndex / (n - 1)) * 100 : 0;

  const latestVerdict = verdicts[0];
  const summaryText = `Verdict trend sparkline: ${n} samples, latest state ${latestVerdict?.state || "STEADY"}`;

  return (
    <div className={`${styles.container} ${className}`} ref={containerRef}>
      {/* Header & Legend */}
      <div className={styles.header}>
        <span className={styles.title}>Sigma Drift Trend</span>
        <div className={styles.legend}>
          <button
            type="button"
            className={styles.legendItem}
            style={{ opacity: showBehavior ? 1 : 0.15 }}
            onClick={() => setShowBehavior(!showBehavior)}
          >
            <span className={styles.legendDash} style={{ backgroundColor: "var(--chart-1)" }} />
            <span>Behavior σ</span>
          </button>
          <button
            type="button"
            className={styles.legendItem}
            style={{ opacity: showCost ? 1 : 0.15 }}
            onClick={() => setShowCost(!showCost)}
          >
            <span className={styles.legendDash} style={{ backgroundColor: "var(--chart-2)" }} />
            <span>Cost σ</span>
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className={styles.svgWrapper}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          style={{ width: "100%", height: "100%", overflow: "visible" }}
          role="img"
          aria-label={summaryText}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={() => {
            if (hoveredVerdict && onSelectVerdict) {
              onSelectVerdict(hoveredVerdict.verdict_id);
            }
          }}
        >
          {/* 3σ to 6σ Band Fill */}
          <rect
            x={0}
            y={y6}
            width={width}
            height={Math.max(0, y3 - y6)}
            fill="rgba(245, 158, 11, 0.08)"
          />

          {/* 3σ Dashed Threshold Line */}
          <line
            x1={0}
            y1={y3}
            x2={width}
            y2={y3}
            stroke="var(--chart-3)"
            strokeWidth={1}
            strokeDasharray="4 3"
          />

          {/* Behavior Series */}
          {showBehavior && behaviorPath && (
            <motion.path
              d={behaviorPath}
              fill="none"
              stroke="var(--chart-1)"
              strokeWidth={1.5}
              strokeLinecap="round"
              initial={reducedMotion ? { opacity: 1 } : { pathLength: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: reducedMotion ? 0 : 0.46, ease: [0.22, 1, 0.36, 1] }}
            />
          )}

          {/* Cost Series */}
          {showCost && costPath && (
            <motion.path
              d={costPath}
              fill="none"
              stroke="var(--chart-2)"
              strokeWidth={1.5}
              strokeLinecap="round"
              initial={reducedMotion ? { opacity: 1 } : { pathLength: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: reducedMotion ? 0 : 0.46, ease: [0.22, 1, 0.36, 1] }}
            />
          )}

          {/* Point Markers */}
          {timelineVerdicts.map((v, idx) => {
            const cx = getX(idx);
            const isChanged = v.state === "CHANGED";
            const isHovered = idx === hoverIndex;
            const r = isHovered ? 6 : isChanged ? 5 : 3;

            return (
              <g key={v.verdict_id}>
                {showBehavior && v.behavior_sigma !== null && v.behavior_sigma !== undefined && (
                  <circle
                    cx={cx}
                    cy={getY(v.behavior_sigma)}
                    r={r}
                    fill="var(--chart-1)"
                    stroke={isChanged ? "#ffffff" : "none"}
                    strokeWidth={isChanged ? 2 : 0}
                    style={{ transition: "r 100ms var(--ease-out)" }}
                  />
                )}
                {showCost && v.cost_sigma !== null && v.cost_sigma !== undefined && (
                  <rect
                    x={cx - r}
                    y={getY(v.cost_sigma) - r}
                    width={r * 2}
                    height={r * 2}
                    fill="var(--chart-2)"
                    stroke={isChanged ? "#ffffff" : "none"}
                    strokeWidth={isChanged ? 2 : 0}
                    style={{ transition: "width 100ms, height 100ms" }}
                  />
                )}
              </g>
            );
          })}

          {/* Crosshair Line */}
          {hoverIndex !== null && (
            <line
              x1={getX(hoverIndex)}
              y1={0}
              x2={getX(hoverIndex)}
              y2={height}
              stroke="var(--color-border-strong)"
              strokeWidth={1}
            />
          )}
        </svg>

        {/* Hover Tooltip */}
        {hoveredVerdict && (
          <div
            className={styles.crosshairTooltip}
            style={{ left: `${hoverXPercent}%` }}
          >
            <StateBadge state={hoveredVerdict.state} size="sm" />
            <span>{formatRelativeTime(hoveredVerdict.ts_unix)}</span>
            <span>bhv: {formatSigma(hoveredVerdict.behavior_sigma)}</span>
            <span>cost: {formatSigma(hoveredVerdict.cost_sigma)}</span>
            <span>n={hoveredVerdict.samples}</span>
          </div>
        )}
      </div>

      {/* Visually-hidden Accessible Data Table (§9.2 A11y) */}
      <table className="visually-hidden">
        <caption>Verdict trend data points</caption>
        <thead>
          <tr>
            <th scope="col">Time</th>
            <th scope="col">State</th>
            <th scope="col">Behavior σ</th>
            <th scope="col">Cost σ</th>
            <th scope="col">Samples</th>
          </tr>
        </thead>
        <tbody>
          {timelineVerdicts.map((v) => (
            <tr key={v.verdict_id}>
              <td>{formatRelativeTime(v.ts_unix)}</td>
              <td>{v.state}</td>
              <td>{formatSigma(v.behavior_sigma)}</td>
              <td>{formatSigma(v.cost_sigma)}</td>
              <td>{v.samples}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default VerdictSparkline;
