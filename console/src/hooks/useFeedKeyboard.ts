import { useEffect, useState } from "react";
import type { Verdict, VerdictState } from "@/lib/api/types";

export interface UseFeedKeyboardOptions {
  verdicts: Verdict[];
  onOpenDrawer: (verdictId: string) => void;
  onToggleStateFilter: (state: VerdictState) => void;
  onTogglePaused: () => void;
}

export function useFeedKeyboard({
  verdicts,
  onOpenDrawer,
  onToggleStateFilter,
  onTogglePaused,
}: UseFeedKeyboardOptions) {
  const [focusedIndex, setFocusedIndex] = useState(-1);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input, textarea, or contenteditable
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        setFocusedIndex((prev) => (prev < verdicts.length - 1 ? prev + 1 : prev));
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0));
      } else if (e.key === "o" && focusedIndex >= 0 && verdicts[focusedIndex]) {
        e.preventDefault();
        onOpenDrawer(verdicts[focusedIndex].verdict_id);
      } else if (e.key === " " && !e.repeat) {
        e.preventDefault();
        onTogglePaused();
      } else if (e.key === "1") {
        e.preventDefault();
        onToggleStateFilter("STEADY");
      } else if (e.key === "2") {
        e.preventDefault();
        onToggleStateFilter("CHANGED");
      } else if (e.key === "3") {
        e.preventDefault();
        onToggleStateFilter("INCONCLUSIVE");
      } else if (e.key === "4") {
        e.preventDefault();
        onToggleStateFilter("WARMING");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [verdicts, focusedIndex, onOpenDrawer, onToggleStateFilter, onTogglePaused]);

  return { focusedIndex, setFocusedIndex };
}
