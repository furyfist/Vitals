import { Search, X } from "lucide-react";
import React, { forwardRef } from "react";
import styles from "./Input.module.css";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  inputSize?: "md" | "lg";
  variant?: "default" | "search" | "error";
  errorMessage?: string;
  onClear?: () => void;
  leadingIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      inputSize = "md",
      variant = "default",
      errorMessage,
      onClear,
      leadingIcon,
      value,
      onChange,
      className = "",
      disabled,
      id,
      ...props
    },
    ref
  ) => {
    const isSearch = variant === "search";
    const isError = Boolean(errorMessage) || variant === "error";

    const sizeClass = inputSize === "lg" ? styles.sizeLg : styles.sizeMd;
    const hasLeading = isSearch || Boolean(leadingIcon);
    const hasTrailing = isSearch && Boolean(value) && Boolean(onClear);

    return (
      <div className={styles.wrapper}>
        <div className={styles.inputContainer}>
          {hasLeading && (
            <span className={styles.leadingIcon}>
              {leadingIcon || <Search size={16} aria-hidden="true" />}
            </span>
          )}
          <input
            ref={ref}
            id={id}
            value={value}
            onChange={onChange}
            disabled={disabled}
            className={`${styles.input} ${sizeClass} ${hasLeading ? styles.hasLeadingIcon : ""} ${
              hasTrailing ? styles.hasTrailingButton : ""
            } ${isError ? styles.inputError : ""} ${className}`}
            {...props}
          />
          {hasTrailing && (
            <button
              type="button"
              className={styles.trailingButton}
              onClick={onClear}
              aria-label="Clear input"
            >
              <X size={14} aria-hidden="true" />
            </button>
          )}
        </div>
        {errorMessage && (
          <span className={styles.errorMessage} role="alert">
            {errorMessage}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
