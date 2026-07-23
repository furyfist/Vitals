import type React from "react";

export interface KeyHintProps {
  children: React.ReactNode;
  className?: string;
}

export const KeyHint: React.FC<KeyHintProps> = ({ children, className = "" }) => {
  return (
    <kbd
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        height: "20px",
        minWidth: "20px",
        padding: "0 4px",
        backgroundColor: "var(--color-surface-inset)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-sm)",
        fontFamily: "var(--font-mono)",
        fontSize: "11px",
        fontWeight: 500,
        color: "var(--color-text-tertiary)",
        textTransform: "uppercase",
        userSelect: "none",
      }}
    >
      {children}
    </kbd>
  );
};

export default KeyHint;
