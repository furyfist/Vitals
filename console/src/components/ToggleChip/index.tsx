import type React from "react";
import styles from "./ToggleChip.module.css";

export interface ToggleChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  pressed: boolean;
  onPressedChange?: (pressed: boolean) => void;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const ToggleChip: React.FC<ToggleChipProps> = ({
  pressed,
  onPressedChange,
  icon,
  children,
  className = "",
  onClick,
  ...props
}) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    onPressedChange?.(!pressed);
    onClick?.(e);
  };

  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={handleClick}
      className={`${styles.chip} ${pressed ? styles.chipOn : ""} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
};

export default ToggleChip;
