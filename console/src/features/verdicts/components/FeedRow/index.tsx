import { ChevronDown } from "lucide-react";
import React, { useState } from "react";
import StatusDot from "@/components/StatusDot";
import { STATE_META } from "@/constants/states";
import type { Verdict } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/format/relativeTime";
import { formatSigma } from "@/lib/format/sigma";
import ExemplarRow from "../ExemplarRow";
import styles from "./FeedRow.module.css";

export interface FeedRowProps {
  verdict: Verdict;
  density?: "comfortable" | "compact";
  isFocused?: boolean;
  onOpenDrawer: (verdictId: string) => void;
  className?: string;
}

export const FeedRow: React.FC<FeedRowProps> = ({
  verdict,
  density = "comfortable",
  isFocused = false,
  onOpenDrawer,
  className = "",
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const meta = STATE_META[verdict.state] || STATE_META.STEADY;

  const handleClick = (e: React.MouseEvent) => {
    if (e.metaKey || e.ctrlKey) {
      onOpenDrawer(verdict.verdict_id);
    } else {
      setIsExpanded((prev) => !prev);
    }
  };

  const formattedTime = formatRelativeTime(verdict.ts_unix);

  const behaviorStr = formatSigma(verdict.behavior_sigma);
  const costStr = formatSigma(verdict.cost_sigma);
  const sigmaPair = `${behaviorStr} / ${costStr}`;

  const exemplars = (verdict.exemplars || []).slice(0, 2);

  return (
    <div
      className={`${styles.rowContainer} ${
        isFocused ? styles.focusedRow : ""
      } ${className}`}
    >
      <div
        className={`${styles.rowHeader} ${
          density === "compact" ? styles.compact : styles.comfortable
        }`}
        onClick={handleClick}
      >
        <span className={styles.timeCol}>{formattedTime}</span>
        <StatusDot state={verdict.state} size={8} />
        <span className={styles.stateWordCol} style={{ color: meta.textColor }}>
          {meta.label}
        </span>
        <span className={styles.sentenceCol}>{verdict.sentence}</span>
        <span className={styles.sigmaCol}>{sigmaPair}</span>
        <ChevronDown
          size={16}
          className={`${styles.chevronIcon} ${
            isExpanded ? styles.chevronRotated : ""
          }`}
          aria-hidden="true"
        />
      </div>

      {isExpanded && (
        <div className={styles.expandedReceipt}>
          <div className={styles.receiptRow}>
            <span className={styles.receiptLabel}>Subject:</span>
            <span className={styles.receiptValue}>{verdict.subject}</span>
          </div>
          <div className={styles.receiptRow}>
            <span className={styles.receiptLabel}>Cause:</span>
            <span className={styles.receiptValue}>{verdict.cause}</span>
          </div>
          {verdict.falsifier && (
            <div className={styles.receiptRow}>
              <span className={styles.receiptLabel}>Falsifier:</span>
              <span className={styles.receiptValue}>{verdict.falsifier}</span>
            </div>
          )}
          {verdict.caveats && verdict.caveats.length > 0 && (
            <div className={styles.receiptRow}>
              <span className={styles.receiptLabel}>Caveats:</span>
              <span className={styles.receiptValue}>
                {verdict.caveats.join(", ")}
              </span>
            </div>
          )}
          {exemplars.length > 0 && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                marginTop: "4px",
              }}
            >
              {exemplars.map((ex, idx) => (
                <ExemplarRow
                  key={`${ex.trace_id}-${idx}`}
                  exemplar={ex}
                  onClick={() => onOpenDrawer(verdict.verdict_id)}
                />
              ))}
            </div>
          )}
          <div style={{ marginTop: "4px" }}>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onOpenDrawer(verdict.verdict_id);
              }}
              style={{
                color: "var(--color-accent)",
                fontSize: "13px",
                fontWeight: 500,
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: 0,
              }}
            >
              View full record →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedRow;
