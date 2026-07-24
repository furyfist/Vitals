export function formatNumber(val: number | null | undefined): string {
  if (val === null || val === undefined) {
    return "—";
  }
  return val.toLocaleString("en-US");
}
