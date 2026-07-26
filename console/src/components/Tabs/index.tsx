import { motion } from "motion/react";
import React, { useRef } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import styles from "./Tabs.module.css";

export interface TabItem {
  id: string;
  label: React.ReactNode;
}

export interface TabsProps {
  items: TabItem[];
  selectedId: string;
  onChange: (id: string) => void;
  ariaLabel?: string;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  selectedId,
  onChange,
  ariaLabel = "Tabs",
  className = "",
}) => {
  const reducedMotion = useReducedMotion();
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex = index;
    if (e.key === "ArrowRight") {
      nextIndex = (index + 1) % items.length;
    } else if (e.key === "ArrowLeft") {
      nextIndex = (index - 1 + items.length) % items.length;
    } else if (e.key === "Home") {
      nextIndex = 0;
    } else if (e.key === "End") {
      nextIndex = items.length - 1;
    } else {
      return;
    }

    e.preventDefault();
    const nextItem = items[nextIndex];
    if (nextItem) {
      onChange(nextItem.id);
      tabRefs.current.get(nextItem.id)?.focus();
    }
  };

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={`${styles.tabList} ${className}`}
    >
      {items.map((item, index) => {
        const isSelected = item.id === selectedId;
        return (
          <button
            key={item.id}
            ref={(node) => {
              if (node) tabRefs.current.set(item.id, node);
              else tabRefs.current.delete(item.id);
            }}
            role="tab"
            aria-selected={isSelected}
            tabIndex={isSelected ? 0 : -1}
            onClick={() => onChange(item.id)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            className={`${styles.tab} ${isSelected ? styles.selectedTab : ""}`}
          >
            {item.label}
            {isSelected && (
              <motion.div
                layoutId={reducedMotion ? undefined : "activeTabIndicator"}
                className={styles.indicator}
                transition={{
                  duration: reducedMotion ? 0 : 0.22,
                  ease: [0.65, 0, 0.35, 1],
                }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
};

export default Tabs;
