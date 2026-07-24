import React, { forwardRef } from "react";
import type { ButtonSize, ButtonVariant } from "../Button";
import styles from "./IconButton.module.css";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  "aria-label": string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  title?: string;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon, "aria-label": ariaLabel, variant = "ghost", size = "md", title, className = "", ...props }, ref) => {
    const sizeClass =
      size === "sm" ? styles.sizeSm : size === "lg" ? styles.sizeLg : styles.sizeMd;
    const variantClass =
      variant === "primary"
        ? styles.variantPrimary
        : variant === "secondary"
        ? styles.variantSecondary
        : variant === "danger"
        ? styles.variantDanger
        : styles.variantGhost;

    return (
      <button
        ref={ref}
        aria-label={ariaLabel}
        title={title || ariaLabel}
        className={`${styles.iconButton} ${sizeClass} ${variantClass} ${className}`}
        {...props}
      >
        {icon}
      </button>
    );
  }
);

IconButton.displayName = "IconButton";
export default IconButton;
