import React, { forwardRef } from "react";
import styles from "./Button.module.css";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "secondary",
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      children,
      className = "",
      disabled,
      ...props
    },
    ref
  ) => {
    const sizeClass =
      size === "sm" ? styles.sizeSm : size === "lg" ? styles.sizeLg : styles.sizeMd;
    const variantClass =
      variant === "primary"
        ? styles.variantPrimary
        : variant === "ghost"
        ? styles.variantGhost
        : variant === "danger"
        ? styles.variantDanger
        : styles.variantSecondary;

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${styles.button} ${sizeClass} ${variantClass} ${className}`}
        {...props}
      >
        {loading ? (
          <span className={styles.spinner} role="status" aria-label="Loading" />
        ) : (
          <>
            {leftIcon}
            {children}
            {rightIcon}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
export default Button;
