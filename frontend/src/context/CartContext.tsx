import { createContext, useCallback, useContext, useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "./AuthContext";
import { apiErrorMessage } from "../api/errors";
import {
  addCartItem, getCart, getProduct, mergeCart, removeCartItem, updateCartItem,
  type CartLine, type CartProduct, type StoredCartLine,
} from "../api/cart";

// Match MAX_CART_QUANTITY and MAX_CART_LINES on the server
export const MAX_CART_QUANTITY = 99;
const MAX_CART_LINES = 100;

const GUEST_CART_KEY = "guest_cart";

// The guest cart lives in the browser. Storage can be missing or blocked (private
// windows, cleared site data), in which case the cart just starts empty
function readGuestCart(): StoredCartLine[] {
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

function writeGuestCart(lines: StoredCartLine[]) {
  try {
    if (lines.length) localStorage.setItem(GUEST_CART_KEY, JSON.stringify(lines));
    else localStorage.removeItem(GUEST_CART_KEY);
  } catch {
    // Not saved; the cart still works until the page is reloaded
  }
}

async function loadGuestProducts(lines: StoredCartLine[]): Promise<CartLine[]> {
  const products = await Promise.all(
    lines.map((line) => getProduct(line.product_id).catch(() => null))
  );
  // Products deleted since they were added are dropped from the cart
  return lines
    .map((line, i) => ({ product_id: line.product_id, quantity: line.quantity, product: products[i] }))
    .filter((line) => line.product !== null);
}

interface CartContextType {
  items: CartLine[];
  count: number;
  loading: boolean;
  add: (product: CartProduct) => Promise<void>;
  updateQuantity: (productId: number, quantity: number) => Promise<void>;
  remove: (productId: number) => Promise<void>;
  // What a guest checks out; the server prices it again
  guestItems: () => StoredCartLine[];
  reload: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [items, setItems] = useState<CartLine[]>([]);
  const [loading, setLoading] = useState(true);

  // Reloading re-runs the load below, which also drops any load still in flight, so an
  // older answer can't land after a newer one
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion((v) => v + 1), []);

  // Load the cart once we know who's shopping. Logging in brings the guest cart along
  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        if (isAuthenticated) {
          const guestLines = readGuestCart();
          let lines: CartLine[];
          try {
            lines = guestLines.length ? await mergeCart(guestLines) : await getCart();
            writeGuestCart([]);
          } catch (err) {
            // Keep the guest cart to merge next time, and still show the account cart
            console.error("Failed to merge the guest cart:", err);
            lines = await getCart();
          }
          if (!cancelled) setItems(lines);
        } else {
          const lines = await loadGuestProducts(readGuestCart());
          if (!cancelled) setItems(lines);
        }
      } catch (err) {
        console.error("Failed to load cart:", err);
        if (!cancelled) setItems([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [authLoading, isAuthenticated, version]);

  const saveGuestLines = (lines: CartLine[]) => {
    writeGuestCart(lines.map(({ product_id, quantity }) => ({ product_id, quantity })));
    setItems(lines);
  };

  // Same limits the server applies to an account cart
  const checkQuantity = (product: CartProduct, quantity: number) => {
    if (quantity > MAX_CART_QUANTITY) throw new Error(`You can buy at most ${MAX_CART_QUANTITY} of one product`);
    if (quantity > product.stock_quantity) throw new Error(`Not enough stock for ${product.title}`);
  };

  const add = async (product: CartProduct) => {
    if (isAuthenticated) {
      await addCartItem(product.product_id);
      setItems(await getCart());
      return;
    }

    if (!product.is_active) throw new Error("Product is not available");
    const existing = items.find((line) => line.product_id === product.product_id);
    const quantity = (existing?.quantity ?? 0) + 1;
    checkQuantity(product, quantity);
    saveGuestLines(existing
      ? items.map((line) => (line.product_id === product.product_id ? { ...line, quantity, product } : line))
      : [...items, { product_id: product.product_id, quantity, product }]);
  };

  const updateQuantity = async (productId: number, quantity: number) => {
    const line = items.find((l) => l.product_id === productId);
    if (!line) return;

    if (isAuthenticated && line.cart_item_id !== undefined) {
      await updateCartItem(line.cart_item_id, quantity);
      setItems(await getCart());
      return;
    }

    if (quantity < 1) throw new Error("Quantity must be at least 1");
    // Stock can drop below what's in the cart, so lowering a quantity is always allowed
    if (line.product && quantity > line.quantity) checkQuantity(line.product, quantity);
    saveGuestLines(items.map((l) => (l.product_id === productId ? { ...l, quantity } : l)));
  };

  const remove = async (productId: number) => {
    const line = items.find((l) => l.product_id === productId);
    if (!line) return;

    if (isAuthenticated && line.cart_item_id !== undefined) {
      await removeCartItem(line.cart_item_id);
      setItems((prev) => prev.filter((l) => l.product_id !== productId));
      return;
    }

    saveGuestLines(items.filter((l) => l.product_id !== productId));
  };

  const guestItems = () => items.map(({ product_id, quantity }) => ({ product_id, quantity }));

  return (
    <CartContext.Provider value={{
      items,
      count: items.reduce((sum, line) => sum + line.quantity, 0),
      loading: loading || authLoading,
      add,
      updateQuantity,
      remove,
      guestItems,
      reload,
    }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be inside CartProvider");
  return ctx;
};

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
