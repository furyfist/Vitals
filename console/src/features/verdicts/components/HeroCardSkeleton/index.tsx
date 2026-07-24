import type React from "react";
import Skeleton from "@/components/Skeleton";
import styles from "../HeroVerdictCard/HeroVerdictCard.module.css";

export const HeroCardSkeleton: React.FC = () => {
  return (
    <div className={styles.card} style={{ backgroundColor: "var(--color-surface)" }}>
      <div className={styles.headerRow}>
        <div className={styles.stateGroup}>
          <Skeleton variant="circle" width={10} height={10} />
          <Skeleton variant="text" width={160} height={36} />
        </div>
        <Skeleton variant="text" width={140} height={20} />
      </div>

      <div style={{ marginTop: 12 }}>
        <Skeleton variant="text" width="60%" height={18} />
      </div>

      <div className={styles.metersSection}>
        <Skeleton variant="block" height={28} />
        <Skeleton variant="block" height={28} />
      </div>

      <div style={{ marginTop: 24 }}>
        <Skeleton variant="block" height={40} />
      </div>

      <div className={styles.evidenceSection}>
        <Skeleton variant="text" width={80} height={16} />
        <Skeleton variant="block" height={36} />
        <Skeleton variant="block" height={36} />
      </div>
    </div>
  );
};

export default HeroCardSkeleton;
