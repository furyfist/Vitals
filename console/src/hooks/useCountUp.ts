import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "./useReducedMotion";

export function useCountUp(targetValue: number, durationMs = 460): number {
  const reducedMotion = useReducedMotion();
  const [displayValue, setDisplayValue] = useState(targetValue);
  const isFirstMount = useRef(true);

  useEffect(() => {
    if (isFirstMount.current || reducedMotion || Math.abs(targetValue) > 999) {
      isFirstMount.current = false;
      setDisplayValue(targetValue);
      return;
    }

    const startValue = displayValue;
    const diff = targetValue - startValue;
    if (diff === 0) return;

    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / durationMs, 1);
      // cubic-bezier(0.22, 1, 0.36, 1) approx easing for count up
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startValue + diff * ease);

      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setDisplayValue(targetValue);
      }
    };

    const animFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animFrame);
  }, [targetValue, durationMs, reducedMotion]);

  return displayValue;
}
