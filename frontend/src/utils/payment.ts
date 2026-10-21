// Checkout offers several payment methods (card, Link, Klarna, Cash App, ...).
// Only card-backed methods have a brand and last 4.

interface OrderPayment {
  payment_method_type: string | null;
  card_brand: string | null;
  card_last4: string | null;
}

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  card: "Card",
  link: "Link",
  klarna: "Klarna",
  affirm: "Affirm",
  cashapp: "Cash App Pay",
  amazon_pay: "Amazon Pay",
  apple_pay: "Apple Pay",
  google_pay: "Google Pay",
};

// e.g. "klarna" -> "Klarna", "us_bank_account" -> "Us Bank Account"
export function paymentMethodLabel(type: string | null): string {
  if (!type) return "Unknown";

  return PAYMENT_METHOD_LABELS[type] ??
    type.split("_").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}

// e.g. "VISA ending in 4242", or null when the method has no card
export function paymentCardSummary(order: OrderPayment): string | null {
  if (!order.card_brand || !order.card_last4) return null;

  return `${order.card_brand.toUpperCase()} ending in ${order.card_last4}`;
}
