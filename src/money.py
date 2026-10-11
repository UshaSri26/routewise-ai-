"""Display helpers for SME-scale freight amounts (INR first, USD alongside)."""

INR_PER_USD = 84.0


def usd_from_inr(inr: float) -> float:
    return round(max(0.5, inr / INR_PER_USD), 2)


def format_money(usd: float) -> str:
    """Human label: rupees first for typical parcel quotes."""
    inr = int(round(float(usd) * INR_PER_USD))
    return f"₹{inr:,} (${float(usd):,.2f})"
