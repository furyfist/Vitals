import type React from "react";
import styles from "./Skeleton.module.css";

export interface SkeletonProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "text" | "block" | "circle";
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = "block",
  width,
  height,
  className = "",
  style,
  ...props
}) => {
  const variantClass =
    variant === "text"
      ? styles.text
      : variant === "circle"
      ? styles.circle
      : styles.block;

  const inlineStyles: React.CSSProperties = {
    ...(width !== undefined ? { width } : {}),
    ...(height !== undefined ? { height } : {}),
    ...style,
  };

  return (
    <span
      className={`${styles.skeleton} ${variantClass} ${className}`}
      style={inlineStyles}
      aria-hidden="true"
      {...props}
    />
  );
};

export default Skeleton;
