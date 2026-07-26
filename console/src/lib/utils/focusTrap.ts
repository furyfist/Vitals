export function trapFocus(element: HTMLElement, e: KeyboardEvent) {
  if (e.key !== "Tab") return;

  const focusables = element.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  if (focusables.length === 0) return;

  const first = focusables[0];
  const last = focusables[focusables.length - 1];

  if (e.shiftKey) {
    if (document.activeElement === first) {
      e.preventDefault();
      last?.focus();
    }
  } else {
    if (document.activeElement === last) {
      e.preventDefault();
      first?.focus();
    }
  }
}
