import type React from "react";
import styles from "./EmptyState.module.css";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  body?: string;
  hint?: string;
  action?: React.ReactNode;
  variant?: "default" | "inline";
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  body,
  hint,
  action,
  variant = "default",
  className = "",
}) => {
  const isInline = variant === "inline";

  return (
    <div
      className={`${isInline ? styles.inlineContainer : styles.container} ${className}`}
    >
      {!isInline && icon && <div className={styles.iconCircle}>{icon}</div>}
      <h3 className={styles.title}>{title}</h3>
      {body && <p className={styles.body}>{body}</p>}
      {hint && <p className={styles.hint}>{hint}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
};

export default EmptyState;
