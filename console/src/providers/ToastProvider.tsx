import { CircleCheck, Info, TriangleAlert, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import React, { createContext, useCallback, useContext, useState } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import styles from "../components/Toast/Toast.module.css";

export type ToastType = "success" | "error" | "info";

export interface ToastItem {
  id: string;
  title: string;
  message?: string;
  type?: ToastType;
  duration?: number;
}

interface ToastContextValue {
  addToast: (toast: Omit<ToastItem, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const reducedMotion = useReducedMotion();

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (toast: Omit<ToastItem, "id">) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastItem = { ...toast, id };

      setToasts((prev) => [...prev.slice(-2), newToast]); // Stack max 3

      const duration = toast.duration || (toast.type === "error" ? 8000 : 4000);
      setTimeout(() => {
        removeToast(id);
      }, duration);
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div className={styles.toastContainer}>
        <AnimatePresence>
          {toasts.map((toast) => {
            const isError = toast.type === "error";
            const icon =
              toast.type === "success" ? (
                <CircleCheck size={16} color="var(--color-steady-dot)" aria-hidden="true" />
              ) : isError ? (
                <TriangleAlert size={16} color="var(--color-error-dot)" aria-hidden="true" />
              ) : (
                <Info size={16} color="var(--color-accent)" aria-hidden="true" />
              );

            return (
              <motion.div
                key={toast.id}
                role={isError ? "alert" : "status"}
                className={styles.toast}
                initial={
                  reducedMotion
                    ? { opacity: 0 }
                    : { y: 16, opacity: 0, scale: 0.96 }
                }
                animate={
                  reducedMotion
                    ? { opacity: 1 }
                    : { y: 0, opacity: 1, scale: 1 }
                }
                exit={
                  reducedMotion
                    ? { opacity: 0 }
                    : { opacity: 0, x: 16 }
                }
                transition={{
                  type: reducedMotion ? "tween" : "spring",
                  stiffness: 400,
                  damping: 30,
                  duration: reducedMotion ? 0.1 : undefined,
                }}
              >
                <span className={styles.icon}>{icon}</span>
                <div className={styles.content}>
                  <h4 className={styles.title}>{toast.title}</h4>
                  {toast.message && <p className={styles.message}>{toast.message}</p>}
                </div>
                <button
                  type="button"
                  className={styles.closeButton}
                  onClick={() => removeToast(toast.id)}
                  aria-label="Close notification"
                >
                  <X size={14} aria-hidden="true" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};
