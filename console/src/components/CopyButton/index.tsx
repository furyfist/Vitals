import { Check, Copy } from "lucide-react";
import React, { useState } from "react";
import Button, { type ButtonSize, type ButtonVariant } from "../Button";
import IconButton from "../IconButton";

export interface CopyButtonProps {
  value: string;
  variant?: "icon" | "inline";
  label?: string;
  size?: ButtonSize;
  buttonVariant?: ButtonVariant;
  className?: string;
}

export const CopyButton: React.FC<CopyButtonProps> = ({
  value,
  variant = "icon",
  label = "Copy",
  size = "sm",
  buttonVariant = "ghost",
  className = "",
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(value);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = value;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch (err) {
      console.warn("Copy failed:", err);
    }
  };

  const iconNode = copied ? (
    <Check size={14} color="var(--color-steady-dot)" aria-hidden="true" />
  ) : (
    <Copy size={14} aria-hidden="true" />
  );

  if (variant === "inline") {
    return (
      <Button
        variant={buttonVariant}
        size={size}
        leftIcon={iconNode}
        onClick={handleCopy}
        className={className}
      >
        {copied ? "Copied" : label}
      </Button>
    );
  }

  return (
    <IconButton
      icon={iconNode}
      aria-label={copied ? "Copied" : label}
      variant={buttonVariant}
      size={size}
      onClick={handleCopy}
      className={className}
    />
  );
};

export default CopyButton;
