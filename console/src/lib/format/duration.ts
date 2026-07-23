export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) {
    return "—";
  }

  const s = Math.round(seconds);
  if (s < 120) {
    return `${s}s`;
  }

  if (s < 3600) {
    const mins = Math.floor(s / 60);
    const remSecs = s % 60;
    return remSecs > 0 ? `${mins}m ${remSecs}s` : `${mins}m`;
  }

  const hours = Math.floor(s / 3600);
  const remMins = Math.floor((s % 3600) / 60);
  const formattedMins = remMins < 10 ? `0${remMins}` : `${remMins}`;
  return `${hours}h ${formattedMins}m`;
}
