export function formatPrice(priceInUSD: number): string {
  return `$${(Math.round(priceInUSD * 100) / 100).toFixed(2)}`;
}
