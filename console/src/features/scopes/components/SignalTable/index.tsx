import { Check } from "lucide-react";
import type React from "react";
import type { ScopeSignal } from "@/lib/api/types";

export interface SignalTableProps {
  signals?: {
    behavior?: ScopeSignal;
    input?: ScopeSignal;
    cost?: ScopeSignal;
    length?: ScopeSignal;
  };
}

export const SignalTable: React.FC<SignalTableProps> = ({ signals }) => {
  const signalKeys: Array<keyof Required<SignalTableProps>["signals"]> = [
    "behavior",
    "input",
    "cost",
    "length",
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        fontFamily: "var(--font-mono)",
        fontSize: "12px",
        lineHeight: "18px",
        fontVariantNumeric: "tabular-nums",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "100px 1fr 1fr 40px",
          color: "var(--color-text-tertiary)",
          fontSize: "11px",
          borderBottom: "1px solid var(--color-border-subtle)",
          paddingBottom: "4px",
        }}
      >
        <span>SIGNAL</span>
        <span>μ (MEAN)</span>
        <span>σ (STD)</span>
        <span style={{ textAlign: "right" }}>CAL</span>
      </div>

      {signalKeys.map((key) => {
        const sig = signals?.[key];
        return (
          <div
            key={key}
            style={{
              display: "grid",
              gridTemplateColumns: "100px 1fr 1fr 40px",
              alignItems: "center",
              padding: "2px 0",
            }}
          >
            <span style={{ textTransform: "capitalize", color: "var(--color-text-secondary)" }}>
              {key}
            </span>
            <span style={{ color: "var(--color-text)" }}>{sig ? sig.mu.toFixed(2) : "—"}</span>
            <span style={{ color: "var(--color-text)" }}>{sig ? sig.sigma.toFixed(2) : "—"}</span>
            <span style={{ textAlign: "right" }}>
              {sig?.calibrated ? (
                <Check size={14} color="var(--color-steady-dot)" aria-label="Calibrated" />
              ) : (
                <span style={{ color: "var(--color-text-tertiary)" }}>—</span>
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default SignalTable;
