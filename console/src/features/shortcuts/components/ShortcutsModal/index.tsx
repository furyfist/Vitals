import type React from "react";
import KeyHint from "@/components/KeyHint";
import Modal from "@/components/Modal";

export interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({
  isOpen,
  onClose,
}) => {
  const shortcutGroups = [
    {
      title: "Navigation & Global",
      shortcuts: [
        { key: "⌘K / Ctrl-K", desc: "Focus search input" },
        { key: "/", desc: "Focus search input (when un-focused)" },
        { key: "Space", desc: "Toggle live polling pause" },
        { key: "?", desc: "Open keyboard shortcuts modal" },
        { key: "Esc", desc: "Clear search → clear filters → blur" },
      ],
    },
    {
      title: "Verdict Feed",
      shortcuts: [
        { key: "j / ↓", desc: "Select next feed row" },
        { key: "k / ↑", desc: "Select previous feed row" },
        { key: "Enter", desc: "Expand/collapse focused feed row" },
        { key: "o", desc: "Open focused verdict in detail drawer" },
        { key: "1–4", desc: "Toggle state filter chips (Steady, Changed, etc.)" },
      ],
    },
    {
      title: "Verdict Drawer",
      shortcuts: [
        { key: "Esc", desc: "Close drawer / return to feed" },
        { key: "j", desc: "Navigate to next verdict detail" },
        { key: "k", desc: "Navigate to previous verdict detail" },
        { key: "c", desc: "Copy raw JSON verdict record" },
      ],
    },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Keyboard Shortcuts"
      size="md"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {shortcutGroups.map((group) => (
          <div key={group.title}>
            <h4
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: "var(--color-text-tertiary)",
                textTransform: "uppercase",
                letterSpacing: "0.02em",
                marginBottom: "12px",
              }}
            >
              {group.title}
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {group.shortcuts.map((sc) => (
                <div
                  key={sc.key}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontSize: "13px",
                  }}
                >
                  <span style={{ color: "var(--color-text-secondary)" }}>{sc.desc}</span>
                  <KeyHint>{sc.key}</KeyHint>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
};

export default ShortcutsModal;
