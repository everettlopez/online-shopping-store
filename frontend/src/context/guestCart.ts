// The guest cart in the browser's storage, and helpers pages use with the cart
import axios from "axios";
import { apiErrorMessage } from "../api/errors";
import type { StoredCartLine } from "../api/cart";

// Match MAX_CART_QUANTITY and MAX_CART_LINES on the server
export const MAX_CART_QUANTITY = 99;
const MAX_CART_LINES = 100;

const GUEST_CART_KEY = "guest_cart";

// The guest cart lives in the browser. Storage can be missing or blocked (private
// windows, cleared site data), in which case the cart just starts empty
export function readGuestCart(): StoredCartLine[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(GUEST_CART_KEY) ?? "[]");
    if (!Array.isArray(parsed)) return [];
    // Keep it within what the server accepts, so old or edited data can't make checkout
    // or the login merge fail every time
    return parsed
      .filter((line) => Number.isInteger(line?.product_id) && Number.isInteger(line?.quantity) && line.quantity > 0)
      .slice(0, MAX_CART_LINES)
      .map((line) => ({ product_id: line.product_id, quantity: Math.min(line.quantity, MAX_CART_QUANTITY) }));
  } catch {
    return [];
  }
}

export function writeGuestCart(lines: StoredCartLine[]) {
  try {
    if (lines.length) localStorage.setItem(GUEST_CART_KEY, JSON.stringify(lines));
    else localStorage.removeItem(GUEST_CART_KEY);
  } catch {
    // Not saved; the cart still works until the page is reloaded
  }
}

// Cart changes fail with the server's message (account cart) or our own (browser cart)
export function cartErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) return apiErrorMessage(err, fallback);
  return err instanceof Error ? err.message : fallback;
}

// After a guest pays, take what was bought out of the browser cart. Like the account
// cart on the server, anything added after checkout started stays
export function removePurchasedFromGuestCart(purchased: StoredCartLine[]) {
  const bought = new Map<number, number>();
  for (const line of purchased) bought.set(line.product_id, (bought.get(line.product_id) ?? 0) + line.quantity);

  writeGuestCart(readGuestCart()
    .map((line) => ({ ...line, quantity: line.quantity - (bought.get(line.product_id) ?? 0) }))
    .filter((line) => line.quantity > 0));
}
