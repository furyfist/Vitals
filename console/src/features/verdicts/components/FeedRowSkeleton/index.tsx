import type React from "react";
import Skeleton from "@/components/Skeleton";

export const FeedRowSkeleton: React.FC = () => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        height: "44px",
        padding: "0 16px",
        borderBottom: "1px solid var(--color-border-subtle)",
      }}
    >
      <Skeleton variant="text" width={60} height={16} />
      <Skeleton variant="circle" width={8} height={8} />
      <Skeleton variant="text" width={80} height={16} />
      <Skeleton variant="text" style={{ flex: 1 }} height={16} />
      <Skeleton variant="text" width={90} height={16} />
    </div>
  );
};

export default FeedRowSkeleton;
