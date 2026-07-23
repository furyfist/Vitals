import { X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import React, { useEffect, useRef } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { trapFocus } from "@/lib/utils/focusTrap";
import { lockScroll, unlockScroll } from "@/lib/utils/scrollLock";
import IconButton from "../IconButton";
import styles from "./Modal.module.css";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
  footer?: React.ReactNode;
  ariaLabel?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = "md",
  children,
  footer,
  ariaLabel,
}) => {
  const reducedMotion = useReducedMotion();
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      lockScroll();
      modalRef.current?.focus();
    } else {
      unlockScroll();
      previousFocusRef.current?.focus();
    }
    return () => {
      if (isOpen) unlockScroll();
    };
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      onClose();
    } else if (modalRef.current) {
      trapFocus(modalRef.current, e.nativeEvent);
    }
  };

  const sizeClass =
    size === "sm" ? styles.sizeSm : size === "lg" ? styles.sizeLg : styles.sizeMd;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className={styles.scrim} onClick={onClose} onKeyDown={handleKeyDown}>
          <motion.div
            ref={modalRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-label={title || ariaLabel || "Modal"}
            onClick={(e) => e.stopPropagation()}
            className={`${styles.modal} ${sizeClass}`}
            initial={
              reducedMotion
                ? { opacity: 0 }
                : { opacity: 0, scale: 0.97, y: 8 }
            }
            animate={
              reducedMotion
                ? { opacity: 1 }
                : { opacity: 1, scale: 1, y: 0 }
            }
            exit={
              reducedMotion
                ? { opacity: 0 }
                : { opacity: 0, scale: 0.97 }
            }
            transition={{
              duration: reducedMotion ? 0.1 : 0.2,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            {title && (
              <div className={styles.header}>
                <h3 className={styles.title}>{title}</h3>
                <IconButton
                  icon={<X size={16} aria-hidden="true" />}
                  aria-label="Close modal"
                  onClick={onClose}
                />
              </div>
            )}
            <div className={styles.body}>{children}</div>
            {footer && <div className={styles.footer}>{footer}</div>}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default Modal;
