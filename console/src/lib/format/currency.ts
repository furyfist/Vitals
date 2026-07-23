export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) {
    return "—";
  }

  if (amount < 1.0) {
    return `$${amount.toFixed(4)}`;
  }

  return `$${amount.toFixed(2)}`;
}
