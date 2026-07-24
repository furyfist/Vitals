import type React from "react";
import AlertCallout from "@/components/AlertCallout";
import CodeBlock from "@/components/CodeBlock";
import PageHeader from "@/components/PageHeader";
import { useHealth } from "@/hooks/useHealth";

export const AboutScreen: React.FC = () => {
  const { data: health } = useHealth();

  const blindSpots = [
    {
      title: "1. Subtle Factual Degradation",
      body: "Vitals measures behavioral and output length shift via CUSUM and ResponseDrift. Small, gradual factual hallucinatory drifts without embedding changes are not flagged instantly.",
    },
    {
      title: "2. Uniform System-Wide Degradation",
      body: "When all traffic across all model releases degrades uniformly simultaneously, baseline reference windows will re-calibrate to the new lower norm over time.",
    },
    {
      title: "3. Baseline Poisoning",
      body: "If a bad release runs for extended periods during warming or initial calibration, bad samples form part of the reference window for future comparison.",
    },
    {
      title: "4. Deploying During Warming Phase",
      body: "Re-deploying or releasing a new model while a scope is actively establishing reference data resets warming baseline collection.",
    },
  ];

  return (
    <div
      style={{
        padding: "32px var(--layout-gutter) 80px",
        maxWidth: "720px",
        margin: "0 auto",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "32px",
      }}
    >
      <PageHeader
        title="About Vitals & Blind Spots"
        subtitle="Honest monitoring contracts and engineering limitations."
      />

      {/* Section 1: What Vitals claims */}
      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <h2 className="text-h2">What Vitals claims</h2>
        <p className="text-body" style={{ color: "var(--color-text-secondary)" }}>
          Vitals is a lightweight, real-time GenAI model release verdict engine. It monitors output behavior, token length, and cost drift across model versions, issuing definitive verdicts: STEADY, CHANGED, INCONCLUSIVE, or WARMING.
        </p>
      </section>

      {/* Section 2: What Vitals does not claim */}
      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <h2 className="text-h2">What Vitals does not claim</h2>
        <p className="text-body" style={{ color: "var(--color-text-secondary)" }}>
          Vitals does not guarantee 100% detection of semantic intent errors or judge subjectively optimal response style. It evaluates statistical variance against established baseline windows.
        </p>
      </section>

      {/* Section 3: Known Blind Spots */}
      <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <h2 className="text-h2">Known blind spots</h2>
        {blindSpots.map((bs) => (
          <AlertCallout key={bs.title} variant="info" title={bs.title}>
            {bs.body}
          </AlertCallout>
        ))}
      </section>

      {/* Section 4: How to read a verdict */}
      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <h2 className="text-h2">How to read a verdict</h2>
        <p className="text-body" style={{ color: "var(--color-text-secondary)" }}>
          Verdicts follow a strict grammar emitted directly by the backend:
        </p>
        <CodeBlock code='Behavior shifted +4.2σ in customer-support after v2 release.' />
      </section>

      {/* Section 5: Version & Build */}
      <section style={{ display: "flex", flexDirection: "column", gap: "12px", borderTop: "1px solid var(--color-border-subtle)", paddingTop: "24px" }}>
        <h2 className="text-h2">Version & Build</h2>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--color-text-secondary)", display: "flex", flexDirection: "column", gap: "6px" }}>
          <div>Version: {health?.version || "0.2.0"}</div>
          <div>Receiver Port: {health?.receiver_port || 4327}</div>
          <div>Uptime: {health?.uptime_seconds ? `${Math.round(health.uptime_seconds)}s` : "—"}</div>
        </div>
      </section>
    </div>
  );
};

export default AboutScreen;
