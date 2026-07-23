import { AnimatePresence, motion } from "motion/react";
import React, { useEffect, useRef } from "react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { trapFocus } from "@/lib/utils/focusTrap";
import { lockScroll, unlockScroll } from "@/lib/utils/scrollLock";
import styles from "./Drawer.module.css";

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  ariaLabel?: string;
  ariaLabelledBy?: string;
  children: React.ReactNode;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  ariaLabel,
  ariaLabelledBy,
  children,
}) => {
  const isMobile = useMediaQuery("(max-width: 767px)");
  const reducedMotion = useReducedMotion();
  const drawerRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      lockScroll();
      drawerRef.current?.focus();
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
    } else if (drawerRef.current) {
      trapFocus(drawerRef.current, e.nativeEvent);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className={`${styles.scrim} ${isMobile ? styles.scrimMobile : ""}`}
          onClick={onClose}
          onKeyDown={handleKeyDown}
        >
          <motion.div
            ref={drawerRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-label={ariaLabel || "Drawer"}
            aria-labelledby={ariaLabelledBy}
            onClick={(e) => e.stopPropagation()}
            className={`${styles.drawer} ${isMobile ? styles.bottomSheet : ""}`}
            drag={isMobile ? "y" : false}
            dragConstraints={isMobile ? { top: 0, bottom: 0 } : undefined}
            dragElastic={isMobile ? { top: 0, bottom: 0.5 } : undefined}
            onDragEnd={(_, info) => {
              if (isMobile && info.offset.y > 120) {
                onClose();
              }
            }}
            initial={
              reducedMotion
                ? { opacity: 0 }
                : isMobile
                ? { y: "100%" }
                : { x: "100%" }
            }
            animate={
              reducedMotion
                ? { opacity: 1 }
                : isMobile
                ? { y: 0 }
                : { x: 0 }
            }
            exit={
              reducedMotion
                ? { opacity: 0 }
                : isMobile
                ? { y: "100%" }
                : { x: "100%" }
            }
            transition={{
              type: reducedMotion ? "tween" : "spring",
              stiffness: 380,
              damping: 32,
              mass: 0.9,
              duration: reducedMotion ? 0.1 : undefined,
            }}
          >
            {isMobile && <div className={styles.grabHandle} aria-hidden="true" />}
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default Drawer;
