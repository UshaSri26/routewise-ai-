const INR_PER_USD = 84;

export function formatMoney(usd: number): { primary: string; secondary: string } {
  const inr = Math.round(usd * INR_PER_USD);
  const usdLabel = `$${usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const inrLabel = `₹${inr.toLocaleString("en-IN")}`;
  // Parcel / sample quotes — always lead with rupees so amounts feel real
  return { primary: inrLabel, secondary: usdLabel };
}
