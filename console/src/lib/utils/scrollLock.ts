let activeLocksCount = 0;
let originalOverflow = "";

export function lockScroll() {
  if (typeof document === "undefined") return;
  if (activeLocksCount === 0) {
    originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  }
  activeLocksCount += 1;
}

export function unlockScroll() {
  if (typeof document === "undefined") return;
  activeLocksCount = Math.max(0, activeLocksCount - 1);
  if (activeLocksCount === 0) {
    document.body.style.overflow = originalOverflow;
  }
}
