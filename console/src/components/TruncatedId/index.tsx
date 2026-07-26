import React, { useState } from "react";
import { truncateId } from "@/lib/format/truncate";
import Tooltip from "../Tooltip";

export interface TruncatedIdProps {
  id: string;
  length?: number;
  className?: string;
}

export const TruncatedId: React.FC<TruncatedIdProps> = ({
  id,
  length = 6,
  className = "",
}) => {
  const [copied, setCopied] = useState(false);
  const truncated = truncateId(id, length);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  };

  const tooltipText = copied ? "Copied!" : `Full ID: ${id} (click to copy)`;

  return (
    <Tooltip content={tooltipText}>
      <button
        type="button"
        onClick={handleCopy}
        className={className}
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          color: "var(--color-text-secondary)",
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: 0,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {truncated}
      </button>
    </Tooltip>
  );
};

export default TruncatedId;
