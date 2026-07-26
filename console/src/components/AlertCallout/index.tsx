import { Info, TriangleAlert } from "lucide-react";
import type React from "react";
import styles from "./AlertCallout.module.css";

export interface AlertCalloutProps {
  variant?: "info" | "warning" | "error" | "neutral";
  title?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export const AlertCallout: React.FC<AlertCalloutProps> = ({
  variant = "info",
  title,
  children,
  icon,
  className = "",
}) => {
  const variantClass =
    variant === "warning"
      ? styles.variantWarning
      : variant === "error"
      ? styles.variantError
      : variant === "neutral"
      ? styles.variantNeutral
      : styles.variantInfo;

  const defaultIcon =
    variant === "warning" || variant === "error" ? (
      <TriangleAlert size={16} aria-hidden="true" />
    ) : (
      <Info size={16} aria-hidden="true" />
    );

  return (
    <div className={`${styles.callout} ${variantClass} ${className}`}>
      <span className={styles.icon}>{icon || defaultIcon}</span>
      <div className={styles.content}>
        {title && <h4 className={styles.title}>{title}</h4>}
        <div className={styles.body}>{children}</div>
      </div>
    </div>
  );
};

export default AlertCallout;
