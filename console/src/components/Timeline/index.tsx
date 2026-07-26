import type React from "react";
import styles from "./Timeline.module.css";

export interface TimelineItem {
  id: string;
  label: string;
  value: React.ReactNode;
  dotColor?: string;
}

export interface TimelineProps {
  items: TimelineItem[];
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ items, className = "" }) => {
  return (
    <div className={`${styles.timeline} ${className}`}>
      {items.map((item) => (
        <div key={item.id} className={styles.item}>
          <span
            className={styles.dot}
            style={item.dotColor ? { backgroundColor: item.dotColor } : undefined}
          />
          <span className={styles.label}>{item.label}</span>
          <span className={styles.value}>{item.value}</span>
        </div>
      ))}
    </div>
  );
};

export default Timeline;
