import React, { useEffect, useRef, useState } from "react";
import styles from "./Tooltip.module.css";

let globalLastTooltipClosedTime = 0;

export interface TooltipProps {
  content: React.ReactNode;
  position?: "top" | "bottom" | "left" | "right";
  children: React.ReactElement;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  position = "top",
  children,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const openTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = () => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    const now = Date.now();
    const isRecent = now - globalLastTooltipClosedTime < 300;
    const delay = isRecent ? 0 : 400;

    openTimerRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (openTimerRef.current) clearTimeout(openTimerRef.current);
    closeTimerRef.current = setTimeout(() => {
      setIsVisible(false);
      globalLastTooltipClosedTime = Date.now();
    }, 80);
  };

  useEffect(() => {
    return () => {
      if (openTimerRef.current) clearTimeout(openTimerRef.current);
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    };
  }, []);

  const positionClass =
    position === "bottom"
      ? styles.bottom
      : position === "left"
      ? styles.left
      : position === "right"
      ? styles.right
      : styles.top;

  return (
    <div
      className={styles.triggerWrapper}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleMouseEnter}
      onBlur={handleMouseLeave}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className={`${styles.tooltip} ${positionClass} ${styles.visible}`}
        >
          {content}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
