const INR_PER_USD = 84;

export function formatMoney(usd: number): { primary: string; secondary: string } {
  const inr = Math.round(usd * INR_PER_USD);
  const usdLabel = `$${usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const inrLabel = `₹${inr.toLocaleString("en-IN")}`;
  // Domestic carton quotes are small USD amounts — show rupees first
  if (usd < 80) {
    return { primary: inrLabel, secondary: usdLabel };
  }
  return { primary: usdLabel, secondary: `≈ ${inrLabel}` };
}
