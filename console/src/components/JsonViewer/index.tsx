import { ChevronDown } from "lucide-react";
import React, { useState } from "react";
import styles from "./JsonViewer.module.css";

export interface JsonViewerProps {
  data: unknown;
  initialDepth?: number;
  className?: string;
}

const JsonNode: React.FC<{
  keyName?: string;
  value: unknown;
  depth: number;
  initialDepth: number;
  isLast?: boolean;
}> = ({ keyName, value, depth, initialDepth, isLast = true }) => {
  const [isExpanded, setIsExpanded] = useState(depth < initialDepth);

  const comma = isLast ? "" : ",";

  if (value === null) {
    return (
      <div className={styles.line}>
        {keyName && <span className={styles.key}>"{keyName}": </span>}
        <span className={styles.null}>null</span>
        {comma}
      </div>
    );
  }

  if (typeof value === "boolean") {
    return (
      <div className={styles.line}>
        {keyName && <span className={styles.key}>"{keyName}": </span>}
        <span className={styles.boolean}>{String(value)}</span>
        {comma}
      </div>
    );
  }

  if (typeof value === "number") {
    return (
      <div className={styles.line}>
        {keyName && <span className={styles.key}>"{keyName}": </span>}
        <span className={styles.number}>{value}</span>
        {comma}
      </div>
    );
  }

  if (typeof value === "string") {
    return (
      <div className={styles.line}>
        {keyName && <span className={styles.key}>"{keyName}": </span>}
        <span className={styles.string}>"{value}"</span>
        {comma}
      </div>
    );
  }

  if (typeof value === "object") {
    const isArray = Array.isArray(value);
    const keys = Object.keys(value as Record<string, unknown>);
    const openBrack = isArray ? "[" : "{";
    const closeBrack = isArray ? "]" : "}";

    if (keys.length === 0) {
      return (
        <div className={styles.line}>
          {keyName && <span className={styles.key}>"{keyName}": </span>}
          <span>{openBrack}{closeBrack}</span>
          {comma}
        </div>
      );
    }

    return (
      <div className={depth === 0 ? styles.rootNode : styles.node}>
        <div className={styles.line}>
          <button
            type="button"
            className={`${styles.toggle} ${!isExpanded ? styles.toggleCollapsed : ""}`}
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? "Collapse node" : "Expand node"}
          >
            <ChevronDown size={12} aria-hidden="true" />
          </button>
          {keyName && <span className={styles.key}>"{keyName}": </span>}
          <span>{openBrack}</span>
          {!isExpanded && (
            <span>
              {" "}… {closeBrack}
              {comma}
            </span>
          )}
        </div>

        {isExpanded && (
          <>
            {keys.map((k, idx) => (
              <JsonNode
                key={k}
                keyName={isArray ? undefined : k}
                value={(value as Record<string, unknown>)[k]}
                depth={depth + 1}
                initialDepth={initialDepth}
                isLast={idx === keys.length - 1}
              />
            ))}
            <div className={styles.line}>
              <span>{closeBrack}</span>
              {comma}
            </div>
          </>
        )}
      </div>
    );
  }

  return null;
};

export const JsonViewer: React.FC<JsonViewerProps> = ({
  data,
  initialDepth = 1,
  className = "",
}) => {
  return (
    <div className={`${styles.container} ${className}`}>
      <JsonNode value={data} depth={0} initialDepth={initialDepth} />
    </div>
  );
};

export default JsonViewer;
