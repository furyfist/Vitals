import { CircleHelp, X } from "lucide-react";

import React, { useEffect } from "react";
import AlertCallout from "@/components/AlertCallout";
import Badge from "@/components/Badge";
import Button from "@/components/Button";
import CopyButton from "@/components/CopyButton";
import Drawer from "@/components/Drawer";

import IconButton from "@/components/IconButton";
import JsonViewer from "@/components/JsonViewer";
import SigmaMeter from "@/components/SigmaMeter";
import StatusDot from "@/components/StatusDot";
import Timeline from "@/components/Timeline";
import TruncatedId from "@/components/TruncatedId";
import { STATE_META } from "@/constants/states";
import { useVerdict } from "@/hooks/useVerdict";
import type { Verdict } from "@/lib/api/types";
import { formatCurrency } from "@/lib/format/currency";
import { formatDuration } from "@/lib/format/duration";
import { formatNumber } from "@/lib/format/number";
import { formatRelativeTime } from "@/lib/format/relativeTime";
import ExemplarCard from "../ExemplarCard";
import styles from "./VerdictDrawer.module.css";

export interface VerdictDrawerProps {
  verdictId: string | null;
  onClose: () => void;
  filteredVerdicts?: Verdict[];
  onNavigateVerdict?: (verdictId: string) => void;
}

export const VerdictDrawer: React.FC<VerdictDrawerProps> = ({
  verdictId,
  onClose,
  filteredVerdicts = [],
  onNavigateVerdict,
}) => {
  const { data: verdict, isLoading, isError } = useVerdict(verdictId || undefined);

  const meta = verdict ? STATE_META[verdict.state] : null;

  // Prev / Next calculation from filtered list order
  const currentIndex = filteredVerdicts.findIndex((v) => v.verdict_id === verdictId);
  const prevVerdict = currentIndex > 0 ? filteredVerdicts[currentIndex - 1] : null;
  const nextVerdict =
    currentIndex >= 0 && currentIndex < filteredVerdicts.length - 1
      ? filteredVerdicts[currentIndex + 1]
      : null;

  // Keyboard navigation inside drawer: Esc close, j/k prev/next, c copy json (§7.4)
  useEffect(() => {
    if (!verdictId) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "c" && (e.metaKey || e.ctrlKey || document.activeElement?.tagName !== "INPUT")) {
        if (verdict) {
          e.preventDefault();
          navigator.clipboard?.writeText(JSON.stringify(verdict, null, 2));
        }
      } else if (e.key === "j" && nextVerdict && onNavigateVerdict) {
        e.preventDefault();
        onNavigateVerdict(nextVerdict.verdict_id);
      } else if (e.key === "k" && prevVerdict && onNavigateVerdict) {
        e.preventDefault();
        onNavigateVerdict(prevVerdict.verdict_id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [verdictId, verdict, prevVerdict, nextVerdict, onNavigateVerdict]);

  return (
    <Drawer isOpen={Boolean(verdictId)} onClose={onClose} ariaLabel="Verdict details">
      {/* 404 / Not Found State */}
      {isError || (!isLoading && !verdict) ? (
        <div style={{ padding: "48px 24px", textAlign: "center", margin: "auto 0" }}>
          <CircleHelp size={32} color="var(--color-text-tertiary)" style={{ margin: "0 auto 16px auto" }} />
          <h3 className="text-h3">Verdict not found</h3>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "13px", marginTop: "8px" }}>
            It may have been pruned by retention.
          </p>
          <div style={{ marginTop: "24px" }}>
            <Button variant="secondary" onClick={onClose}>
              Back to console
            </Button>
          </div>
        </div>
      ) : verdict ? (
        <>
          {/* Header */}
          <div className={styles.header}>
            <div className={styles.headerLeft}>
              <StatusDot state={verdict.state} size={10} />
              <span className={styles.headerTitle} style={{ color: meta?.textColor }}>
                {meta?.label}
              </span>
              {verdict.flags?.behavior && <Badge variant="warning" size="sm">behavior</Badge>}
              {verdict.flags?.cost && <Badge variant="warning" size="sm">cost</Badge>}
              {verdict.flags?.runaway && <Badge variant="error" size="sm">runaway</Badge>}
            </div>
            <div className={styles.headerRight}>
              <CopyButton
                value={JSON.stringify(verdict, null, 2)}
                variant="inline"
                label="Copy JSON"
                size="sm"
              />
              <IconButton
                icon={<X size={16} aria-hidden="true" />}
                aria-label="Close drawer"
                onClick={onClose}
              />
            </div>
          </div>

          {/* Body */}
          <div className={styles.body}>
            {/* Section 1: Sentence */}
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>Sentence</h4>
              <div className={styles.sentenceBlock}>
                <code>{verdict.sentence}</code>
                <div style={{ position: "absolute", top: 6, right: 6 }}>
                  <CopyButton value={verdict.sentence} variant="icon" size="sm" />
                </div>
              </div>
            </div>

            {/* Section 2: Judgment */}
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>Judgment</h4>
              <div className={styles.gridRow}>
                <span className={styles.gridLabel}>Subject</span>
                <span className={styles.gridValue}>{verdict.subject}</span>
              </div>
              <div className={styles.gridRow}>
                <span className={styles.gridLabel}>Cause</span>
                <span className={styles.gridValue}>{verdict.cause}</span>
              </div>
              <div className={styles.gridRow}>
                <span className={styles.gridLabel}>Service</span>
                <span className={styles.gridValue}>{verdict.service_name} ({verdict.version})</span>
              </div>
              {verdict.baseline_version && (
                <div className={styles.gridRow}>
                  <span className={styles.gridLabel}>Baseline version</span>
                  <span className={styles.gridValue}>{verdict.baseline_version}</span>
                </div>
              )}
            </div>

            {/* Section 3: Evidence */}
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>Evidence</h4>
              <SigmaMeter label="behavior" sigma={verdict.behavior_sigma} type="behavior" />
              <SigmaMeter label="cost" sigma={verdict.cost_sigma} type="cost" />
              {verdict.cost_usd_per_req !== undefined && (
                <div className={styles.gridRow} style={{ marginTop: 8 }}>
                  <span className={styles.gridLabel}>Cost per req</span>
                  <span className={styles.gridValue}>
                    {formatCurrency(verdict.cost_usd_per_req)}
                    {verdict.baseline_cost_usd_per_req !== undefined && (
                      <span style={{ color: "var(--color-text-tertiary)" }}>
                        {" "}vs {formatCurrency(verdict.baseline_cost_usd_per_req)}
                      </span>
                    )}
                  </span>
                </div>
              )}
              {verdict.velocity_ratio !== undefined && verdict.velocity_ratio !== null && (
                <div className={styles.gridRow}>
                  <span className={styles.gridLabel}>Velocity ratio</span>
                  <span className={styles.gridValue}>{verdict.velocity_ratio.toFixed(1)}×</span>
                </div>
              )}
            </div>

            {/* Section 4: Timing */}
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>Timing</h4>
              <Timeline
                items={[
                  {
                    id: "ts",
                    label: "Issued timestamp",
                    value: `${formatRelativeTime(verdict.ts_unix)} (${new Date(verdict.ts_unix * 1000).toLocaleTimeString()})`,
                    dotColor: meta?.dotColor,
                  },
                  ...(verdict.onset_ts_unix
                    ? [
                        {
                          id: "onset",
                          label: "Onset timestamp",
                          value: new Date(verdict.onset_ts_unix * 1000).toLocaleTimeString(),
                          dotColor: "var(--color-changed-dot)",
                        },
                      ]
                    : []),
                  ...(verdict.seconds_after_deploy !== undefined && verdict.seconds_after_deploy !== null
                    ? [
                        {
                          id: "deploy",
                          label: "After deploy",
                          value: formatDuration(verdict.seconds_after_deploy),
                        },
                      ]
                    : []),
                  {
                    id: "samples",
                    label: "Samples evaluated",
                    value: `n=${formatNumber(verdict.samples)}${verdict.baseline_samples ? ` (baseline n=${formatNumber(verdict.baseline_samples)})` : ""}`,
                  },
                ]}
              />
            </div>

            {/* Section 5: Honesty */}
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>Honesty</h4>
              {verdict.caveats && verdict.caveats.length > 0 && (
                <AlertCallout variant="warning" title="Caveats">
                  {verdict.caveats.join(", ")}
                </AlertCallout>
              )}
              {verdict.falsifier && (
                <AlertCallout variant="neutral" title="Falsifier">
                  {verdict.falsifier}
                </AlertCallout>
              )}
            </div>

            {/* Section 6: Exemplars */}
            {verdict.exemplars && verdict.exemplars.length > 0 && (
              <div className={styles.section}>
                <h4 className={styles.sectionTitle}>Exemplars</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {verdict.exemplars.map((ex, idx) => (
                    <ExemplarCard key={`${ex.trace_id}-${idx}`} exemplar={ex} />
                  ))}
                </div>
              </div>
            )}

            {/* Section 7: Raw Record */}
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>Raw record</h4>
              <JsonViewer data={verdict} initialDepth={1} />
            </div>
          </div>

          {/* Footer */}
          <div className={styles.footer}>
            <TruncatedId id={verdict.verdict_id} length={8} />
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Button
                variant="secondary"
                size="sm"
                disabled={!prevVerdict}
                onClick={() => prevVerdict && onNavigateVerdict?.(prevVerdict.verdict_id)}
              >
                ← Prev
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={!nextVerdict}
                onClick={() => nextVerdict && onNavigateVerdict?.(nextVerdict.verdict_id)}
              >
                Next →
              </Button>
            </div>
          </div>
        </>
      ) : null}
    </Drawer>
  );
};

export default VerdictDrawer;
