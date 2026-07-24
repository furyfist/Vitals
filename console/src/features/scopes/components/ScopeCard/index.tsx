import type React from "react";
import { useNavigate } from "react-router-dom";
import Badge from "@/components/Badge";
import ProgressBar from "@/components/ProgressBar";
import StateBadge from "@/components/StateBadge";
import type { Scope } from "@/lib/api/types";
import SignalTable from "../SignalTable";
import styles from "./ScopeCard.module.css";

export interface ScopeCardProps {
  scope: Scope;
}

export const ScopeCard: React.FC<ScopeCardProps> = ({ scope }) => {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/?service=${encodeURIComponent(scope.service_name)}`);
  };

  const isLive = scope.live;
  const [have, need] = scope.warming_progress || [0, 1000];

  return (
    <div
      className={styles.card}
      onClick={handleCardClick}
      aria-label={`Scope card for ${scope.service_name}`}
    >
      <div className={styles.header}>
        <h3 className={styles.serviceName}>{scope.service_name}</h3>
        <StateBadge state={isLive ? "STEADY" : "WARMING"} showDot />
      </div>

      <div className={styles.metaRow}>
        <span>{scope.gen_ai_system}</span>
        <span>·</span>
        <span>{scope.model}</span>
      </div>

      {!isLive ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <ProgressBar value={have} max={need} label="Scope warming" />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "12px",
              color: "var(--color-text-secondary)",
            }}
          >
            <span>{scope.phase}</span>
            <span style={{ fontFamily: "var(--font-mono)" }}>
              {have}/{need}
            </span>
          </div>
        </div>
      ) : (
        <SignalTable signals={scope.signals} />
      )}

      <div className={styles.versionsRow}>
        <span
          style={{
            fontSize: "11px",
            color: "var(--color-text-tertiary)",
            fontFamily: "var(--font-mono)",
            marginRight: "4px",
          }}
        >
          VERSIONS:
        </span>
        {scope.versions.map((ver, idx) => {
          const isLatest = idx === scope.versions.length - 1;
          return (
            <Badge
              key={ver}
              variant={isLatest ? "neutral" : "outline"}
              size="sm"
            >
              {ver}
            </Badge>
          );
        })}
      </div>
    </div>
  );
};

export default ScopeCard;
