import { ExternalLink } from "lucide-react";
import type React from "react";
import Badge from "@/components/Badge";
import CodeBlock from "@/components/CodeBlock";
import CopyButton from "@/components/CopyButton";
import type { Exemplar } from "@/lib/api/types";
import { formatSigma } from "@/lib/format/sigma";

export interface ExemplarCardProps {
  exemplar: Exemplar;
}

export const ExemplarCard: React.FC<ExemplarCardProps> = ({ exemplar }) => {
  const isWorst = exemplar.kind === "worst";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        padding: "12px 14px",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
        backgroundColor: "var(--color-surface)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Badge variant={isWorst ? "warning" : "neutral"} size="sm">
            {exemplar.kind}
          </Badge>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--color-text)" }}>
            {exemplar.trace_id}
          </span>
          <CopyButton value={exemplar.trace_id} variant="icon" size="sm" />
        </div>

        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "13px",
            fontWeight: 600,
            color: "var(--color-text)",
          }}
        >
          {formatSigma(exemplar.z_score)}
        </span>
      </div>

      <CodeBlock code={exemplar.excerpt} />

      {exemplar.signoz_url && (
        <a
          href={exemplar.signoz_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            alignSelf: "flex-end",
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "12px",
            color: "var(--color-accent)",
            fontWeight: 500,
            marginTop: "4px",
          }}
        >
          <span>Open trace in SigNoz</span>
          <ExternalLink size={12} aria-hidden="true" />
        </a>
      )}
    </div>
  );
};

export default ExemplarCard;
