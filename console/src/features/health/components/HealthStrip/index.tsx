import type React from "react";
import { Link } from "react-router-dom";
import MetricChip from "@/components/MetricChip";
import { useHealth } from "@/hooks/useHealth";
import { usePolling } from "@/hooks/usePolling";
import { formatDuration } from "@/lib/format/duration";
import LivePulseDot from "../LivePulseDot";
import styles from "./HealthStrip.module.css";

export interface HealthStripProps {
  isPausedManual?: boolean;
  className?: string;
}

export const HealthStrip: React.FC<HealthStripProps> = ({
  isPausedManual = false,
  className = "",
}) => {
  const { data: health, isError } = useHealth({ paused: isPausedManual });
  const { isPolling, isTabHidden, isOffline } = usePolling(isPausedManual);

  const isReconnecting = isError;

  const statusLabel = isOffline
    ? "Offline"
    : isReconnecting
    ? "Reconnecting…"
    : isPausedManual || isTabHidden
    ? "Paused"
    : "Live";

  return (
    <div className={`${styles.container} ${className}`}>
      <div className={styles.mainRow}>
        {/* Left Status */}
        <div className={styles.statusGroup}>
          <LivePulseDot
            isPolling={isPolling}
            isPaused={isPausedManual}
            isOffline={isOffline}
            isReconnecting={isReconnecting}
          />
          <span>{statusLabel}</span>
        </div>

        {/* Center 6 MetricChips */}
        <div className={styles.metricsGroup}>
          <MetricChip
            label="spans received"
            value={health?.spans_received ?? 0}
          />
          <MetricChip label="scored" value={health?.spans_scored ?? 0} />
          <MetricChip
            label="skipped"
            value={health?.spans_skipped ?? 0}
            tooltip="Spans that weren't GenAI or couldn't be mapped. A non-zero value is normal."
          />
          <MetricChip label="scopes" value={health?.scopes_active ?? 0} />
          <MetricChip label="verdicts" value={health?.verdicts_emitted ?? 0} />
          <MetricChip
            label="emit errors"
            value={health?.emit_errors ?? 0}
            variant={(health?.emit_errors ?? 0) > 0 ? "error" : "default"}
          />
        </div>

        {/* Right Uptime & Version */}
        <div className={styles.metaGroup}>
          <span>uptime {formatDuration(health?.uptime_seconds)}</span>
          <span>·</span>
          <span>vitals v{health?.version || "0.2.0"}</span>
        </div>
      </div>

      {/* Footer Line (§7.1 Zone 3 & Backend §20.8) */}
      <div className={styles.footerRow}>
        <Link to="/about" className={styles.blindSpotsLink}>
          Known blind spots →
        </Link>
      </div>
    </div>
  );
};

export default HealthStrip;
