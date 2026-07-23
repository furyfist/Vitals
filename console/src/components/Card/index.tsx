import React, { forwardRef } from "react";
import styles from "./Card.module.css";

export interface CardProps extends React.HTMLAttributes<HTMLElement> {
  variant?: "default" | "interactive" | "inset";
  as?: "div" | "article" | "section" | "button" | "a";
  href?: string;
  onClick?: (e: React.MouseEvent) => void;
  children: React.ReactNode;
}

export const Card = forwardRef<HTMLElement, CardProps>(
  (
    {
      variant = "default",
      as,
      href,
      onClick,
      children,
      className = "",
      ...props
    },
    ref
  ) => {
    const isInteractive = variant === "interactive" || Boolean(onClick) || Boolean(href);
    const Component = as || (href ? "a" : isInteractive ? "button" : "div");

    const variantClass =
      variant === "inset"
        ? styles.variantInset
        : isInteractive
        ? styles.variantInteractive
        : styles.card;

    const extraProps: Record<string, unknown> = {};
    if (Component === "a" && href) {
      extraProps.href = href;
    }
    if (Component === "button" && onClick) {
      extraProps.type = props.type || "button";
      extraProps.onClick = onClick;
    }

    return (
      <Component
        ref={ref as any}
        className={`${styles.card} ${variantClass} ${className}`}
        {...extraProps}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Card.displayName = "Card";
export default Card;
