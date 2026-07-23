import type { LucideIcon } from "lucide-react";
import { Activity, CircleCheck, CircleHelp, LoaderCircle, TriangleAlert } from "lucide-react";
import type { VerdictState } from "@/lib/api/types";

export interface StateMeta {
  state: VerdictState | "ERROR";
  label: string;
  icon: LucideIcon;
  dotColor: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
}


export const STATE_META: Record<VerdictState | "ERROR", StateMeta> = {
  STEADY: {
    state: "STEADY",
    label: "STEADY",
    icon: CircleCheck,
    dotColor: "var(--color-steady-dot)",
    textColor: "var(--color-steady-text)",
    bgColor: "var(--color-steady-bg)",
    borderColor: "var(--color-steady-border)",
  },
  CHANGED: {
    state: "CHANGED",
    label: "CHANGED",
    icon: Activity,
    dotColor: "var(--color-changed-dot)",
    textColor: "var(--color-changed-text)",
    bgColor: "var(--color-changed-bg)",
    borderColor: "var(--color-changed-border)",
  },
  INCONCLUSIVE: {
    state: "INCONCLUSIVE",
    label: "INCONCLUSIVE",
    icon: CircleHelp,
    dotColor: "var(--color-inconclusive-dot)",
    textColor: "var(--color-inconclusive-text)",
    bgColor: "var(--color-inconclusive-bg)",
    borderColor: "var(--color-inconclusive-border)",
  },
  WARMING: {
    state: "WARMING",
    label: "WARMING",
    icon: LoaderCircle,
    dotColor: "var(--color-warming-dot)",
    textColor: "var(--color-warming-text)",
    bgColor: "var(--color-warming-bg)",
    borderColor: "var(--color-warming-border)",
  },
  ERROR: {
    state: "ERROR",
    label: "ERROR",
    icon: TriangleAlert,
    dotColor: "var(--color-error-dot)",
    textColor: "var(--color-error-text)",
    bgColor: "var(--color-error-bg)",
    borderColor: "var(--color-error-border)",
  },
};
