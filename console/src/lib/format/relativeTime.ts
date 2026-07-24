export function formatRelativeTime(timestampMsOrSec: number | null | undefined): string {
  if (timestampMsOrSec === null || timestampMsOrSec === undefined) {
    return "—";
  }

  // Handle seconds vs milliseconds
  const ms = timestampMsOrSec < 10000000000 ? timestampMsOrSec * 1000 : timestampMsOrSec;
  const now = Date.now();
  const diffSec = Math.floor((now - ms) / 1000);

  if (diffSec < 5) {
    return "now";
  }
  if (diffSec < 60) {
    return `${diffSec}s ago`;
  }
  if (diffSec < 3600) {
    const mins = Math.floor(diffSec / 60);
    return `${mins}m ago`;
  }
  if (diffSec < 86400) {
    const hours = Math.floor(diffSec / 3600);
    return `${hours}h ago`;
  }

  const date = new Date(ms);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const monthStr = months[date.getMonth()];
  const day = date.getDate();
  const hoursStr = String(date.getHours()).padStart(2, "0");
  const minsStr = String(date.getMinutes()).padStart(2, "0");

  return `${monthStr} ${day}, ${hoursStr}:${minsStr}`;
}
