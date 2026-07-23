import type React from "react";
import styles from "./Badge.module.css";

export type BadgeVariant =
  | "neutral"
  | "success"
  | "warning"
  | "info"
  | "error"
  | "accent"
  | "outline";

export type BadgeSize = "sm" | "md";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "neutral",
  size = "md",
  icon,
  children,
  className = "",
  ...props
}) => {
  const sizeClass = size === "sm" ? styles.sizeSm : styles.sizeMd;
  const variantClass =
    variant === "success"
      ? styles.variantSuccess
      : variant === "warning"
      ? styles.variantWarning
      : variant === "info"
      ? styles.variantInfo
      : variant === "error"
      ? styles.variantError
      : variant === "accent"
      ? styles.variantAccent
      : variant === "outline"
      ? styles.variantOutline
      : styles.variantNeutral;

  return (
    <span
      className={`${styles.badge} ${sizeClass} ${variantClass} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </span>
  );
};

export default Badge;
