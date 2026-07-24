export function formatSigma(sigma: number | null | undefined): string {
  if (sigma === null || sigma === undefined) {
    return "—"; // U+2014 em dash
  }

  const abs = Math.abs(sigma);
  const sign = sigma > 0 ? "+" : sigma < 0 ? "−" : ""; // U+2212 minus sign
  const formattedNum = `${sign}${abs.toFixed(1)}σ`;

  if (abs < 1.0) {
    return `${formattedNum} flat`;
  }

  return formattedNum;
}
