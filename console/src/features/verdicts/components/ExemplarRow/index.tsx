import { ExternalLink } from "lucide-react";
import type React from "react";
import Badge from "@/components/Badge";
import TruncatedId from "@/components/TruncatedId";
import type { Exemplar } from "@/lib/api/types";
import { formatSigma } from "@/lib/format/sigma";
import { formatExcerpt } from "@/lib/format/truncate";
import styles from "./ExemplarRow.module.css";

export interface ExemplarRowProps {
  exemplar: Exemplar;
  onClick?: () => void;
  className?: string;
}

export const ExemplarRow: React.FC<ExemplarRowProps> = ({
  exemplar,
  onClick,
  className = "",
}) => {
  const isWorst = exemplar.kind === "worst";
  const badgeVariant = isWorst ? "warning" : "neutral";

  const formattedExcerpt = formatExcerpt(exemplar.excerpt);

  return (
    <div className={`${styles.row} ${className}`} onClick={onClick}>
      <Badge variant={badgeVariant} size="sm">
        {exemplar.kind}
      </Badge>
      <TruncatedId id={exemplar.trace_id} />
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          color: "var(--color-text)",
          fontVariantNumeric: "tabular-nums",
          minWidth: "48px",
        }}
      >
        {formatSigma(exemplar.z_score)}
      </span>
      <span className={styles.excerpt} title={exemplar.excerpt}>
        {formattedExcerpt}
      </span>
      {exemplar.signoz_url && (
        <a
          href={exemplar.signoz_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className={styles.linkIcon}
          title="Open trace in SigNoz"
        >
          <ExternalLink size={14} aria-hidden="true" />
        </a>
      )}
    </div>
  );
};

export default ExemplarRow;
