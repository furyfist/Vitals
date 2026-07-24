import { ArrowUp } from "lucide-react";
import { motion } from "motion/react";
import type React from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export interface NewVerdictsPillProps {
  count: number;
  onClick: () => void;
}

export const NewVerdictsPill: React.FC<NewVerdictsPillProps> = ({
  count,
  onClick,
}) => {
  const reducedMotion = useReducedMotion();

  if (count <= 0) return null;

  return (
    <motion.button
      type="button"
      onClick={onClick}
      style={{
        position: "sticky",
        top: "72px",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 30,
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        height: "32px",
        padding: "0 14px",
        backgroundColor: "var(--color-accent)",
        color: "#ffffff",
        borderRadius: "var(--radius-full)",
        boxShadow: "var(--shadow-md)",
        fontFamily: "var(--font-sans)",
        fontSize: "13px",
        fontWeight: 600,
        border: "none",
        cursor: "pointer",
        margin: "0 auto",
      }}
      initial={reducedMotion ? { opacity: 0 } : { y: -16, opacity: 0, scale: 0.9 }}
      animate={reducedMotion ? { opacity: 1 } : { y: 0, opacity: 1, scale: 1 }}
      exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -16 }}
      transition={{
        type: reducedMotion ? "tween" : "spring",
        stiffness: 400,
        damping: 25,
      }}
    >
      <ArrowUp size={14} aria-hidden="true" />
      <span>{count} new {count === 1 ? "verdict" : "verdicts"}</span>
    </motion.button>
  );
};

export default NewVerdictsPill;
