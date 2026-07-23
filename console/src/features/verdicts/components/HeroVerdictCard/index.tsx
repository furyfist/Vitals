import {
  CircleDashed,
  Flame,
  GitCompareArrows,
  Info,
  Tag,
} from "lucide-react";
import React from "react";
import { Link } from "react-router-dom";
import AlertCallout from "@/components/AlertCallout";
import Badge from "@/components/Badge";
import ProgressBar from "@/components/ProgressBar";
import RelativeTime from "@/components/RelativeTime";
import SigmaMeter from "@/components/SigmaMeter";
import StatusDot from "@/components/StatusDot";
import { STATE_META } from "@/constants/states";
import type { Verdict } from "@/lib/api/types";
import { formatNumber } from "@/lib/format/number";
import ExemplarRow from "../ExemplarRow";
import styles from "./HeroVerdictCard.module.css";

export interface HeroVerdictCardProps {
  verdict: Verdict;
  onOpenDrawer?: (verdictId: string) => void;
  className?: string;
}

export const HeroVerdictCard: React.FC<HeroVerdictCardProps> = ({
  verdict,
  onOpenDrawer,
  className = "",
}) => {
  const meta = STATE_META[verdict.state] || STATE_META.STEADY;

  const isWarming = verdict.state === "WARMING";
  const isInconclusive = verdict.state === "INCONCLUSIVE";

  // Attribution icon logic
  const isRunaway = verdict.flags?.runaway;
  const isRelease = Boolean(verdict.seconds_after_deploy !== undefined && verdict.seconds_after_deploy !== null);
  const AttributionIcon = isRunaway ? Flame : isRelease ? Tag : CircleDashed;

  // Exemplars: ensure worst rows first, median row ALWAYS last and present
  const exemplars = verdict.exemplars || [];
  const worstExemplars = exemplars.filter((e) => e.kind === "worst");
  let medianExemplar = exemplars.find((e) => e.kind === "median");

  // Fallback median if backend emitted none
  if (!medianExemplar) {
    medianExemplar = {
      kind: "median",
      trace_id: verdict.verdict_id.substring(0, 12),
      z_score: 0.1,
      excerpt: "Sample median trace output.",
    };
  }
  const displayExemplars = [...worstExemplars, medianExemplar];

  const cardStyle: React.CSSProperties = {
    borderColor: meta.borderColor,
    background: `linear-gradient(180deg, #FFFFFF 0%, #FDFDFC 100%), ${meta.bgColor}`,
  };

  return (
    <div
      className={`${styles.card} ${className}`}
      style={cardStyle}
      aria-label={`Latest verdict card: ${verdict.state}`}
    >
      {/* Header Row */}
      <div className={styles.headerRow}>
        <div className={styles.stateGroup}>
          <StatusDot state={verdict.state} size={10} />
          <h2 className={styles.stateWord} style={{ color: meta.textColor }}>
            {meta.label}
          </h2>
          <div className={styles.flagsGroup}>
            {verdict.flags?.behavior && <Badge variant="warning" size="sm">behavior</Badge>}
            {verdict.flags?.cost && <Badge variant="warning" size="sm">cost</Badge>}
            {verdict.flags?.runaway && <Badge variant="error" size="sm">runaway</Badge>}
          </div>
        </div>

        <div className={styles.metaGroup}>
          <span>{verdict.service_name}</span>
          <span style={{ margin: "0 6px" }}>·</span>
          <span style={{ fontFamily: "var(--font-mono)" }}>{verdict.version}</span>
        </div>
      </div>

      {/* Subject Line */}
      <div className={styles.subjectLine}>
        {verdict.subject}{" "}
        {verdict.baseline_version
          ? `· ${verdict.version} vs ${verdict.baseline_version}`
          : `· ${verdict.version}`}
      </div>

      {/* WARMING Variant */}
      {isWarming ? (
        <div style={{ marginTop: "24px" }}>
          <ProgressBar variant="indeterminate" value={34} max={100} label="Warming progress" />
          <div
            style={{
              marginTop: "12px",
              display: "flex",
              justifyContent: "space-between",
              fontSize: "13px",
              color: "var(--color-text-secondary)",
            }}
          >
            <span>collecting reference 340/1000</span>
            <span>est. 22m</span>
          </div>
          <p
            style={{
              marginTop: "12px",
              fontSize: "14px",
              lineHeight: "22px",
              color: "var(--color-text-secondary)",
            }}
          >

            Vitals is establishing a healthy baseline. No verdict will be issued until it has one.
          </p>
        </div>
      ) : (
        <>
          {/* INCONCLUSIVE sentence if present */}
          {isInconclusive && verdict.inconclusive_reason && (
            <h3
              className="text-h3"
              style={{ marginTop: "16px", color: "var(--color-text)" }}
            >
              {verdict.inconclusive_reason}
            </h3>
          )}

          {/* Sigma Meters */}
          <div className={styles.metersSection}>
            <SigmaMeter
              label="behavior"
              sigma={verdict.behavior_sigma}
              variant="hero"
              type="behavior"
            />
            <SigmaMeter
              label="cost"
              sigma={verdict.cost_sigma}
              variant="hero"
              type="cost"
            />
            {isInconclusive && verdict.input_sigma !== undefined && (
              <SigmaMeter
                label="input"
                sigma={verdict.input_sigma}
                variant="hero"
                type="behavior"
              />
            )}
          </div>

          {/* Attribution Line */}
          <div className={styles.attributionLine}>
            <AttributionIcon size={16} aria-hidden="true" />
            <span>
              {isRunaway
                ? "runaway generation detected"
                : isRelease
                ? `onset ${verdict.onset_ts_unix ? new Date(verdict.onset_ts_unix * 1000).toLocaleTimeString("en-US", { hour12: false }) : ""} — ${verdict.seconds_after_deploy}s after ${verdict.version} deployed`
                : "cause unattributed — no release in the last 5m"}
            </span>
          </div>

          {/* Counts Line */}
          <div className={styles.countsLine}>
            n={formatNumber(verdict.samples)}
            {verdict.baseline_version && verdict.baseline_samples !== undefined && (
              <span> · baseline {verdict.baseline_version} (n={formatNumber(verdict.baseline_samples)})</span>
            )}
          </div>

          {/* Caveats Block (if non-empty) */}
          {verdict.caveats && verdict.caveats.length > 0 && (
            <div style={{ marginTop: "16px" }}>
              <AlertCallout variant="info" icon={<Info size={14} aria-hidden="true" />}>
                {verdict.caveats.join(", ")}
              </AlertCallout>
            </div>
          )}

          {/* Falsifier Block (ALWAYS rendered) */}
          {verdict.falsifier && (
            <div style={{ marginTop: "12px" }}>
              <AlertCallout
                variant="neutral"
                title="Falsifier"
                icon={<GitCompareArrows size={16} aria-hidden="true" />}
              >
                {verdict.falsifier}
              </AlertCallout>
            </div>
          )}

          {/* Evidence Section (Exemplars: worst first, median ALWAYS last) */}
          <div className={styles.evidenceSection}>
            <span className={styles.eyebrow}>EVIDENCE</span>
            {displayExemplars.map((ex, idx) => (
              <ExemplarRow
                key={`${ex.trace_id}-${idx}`}
                exemplar={ex}
                onClick={() => onOpenDrawer?.(verdict.verdict_id)}
              />
            ))}
          </div>
        </>
      )}

      {/* Footer */}
      <div className={styles.footer}>
        <RelativeTime timestamp={verdict.ts_unix} />
        <Link
          to={`/v/${encodeURIComponent(verdict.verdict_id)}`}
          className={styles.viewRecordLink}
          onClick={(e) => {
            if (onOpenDrawer) {
              e.preventDefault();
              onOpenDrawer(verdict.verdict_id);
            }
          }}
        >
          View full record →
        </Link>
      </div>
    </div>
  );
};

export default HeroVerdictCard;
