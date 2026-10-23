import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./useAuth";
import { CartContext } from "./useCart";
import { MAX_CART_QUANTITY, readGuestCart, writeGuestCart } from "./guestCart";
import {
  addCartItem, getCart, getProduct, mergeCart, removeCartItem, updateCartItem,
  type CartLine, type CartProduct, type StoredCartLine,
} from "../api/cart";

async function loadGuestProducts(lines: StoredCartLine[]): Promise<CartLine[]> {
  const products = await Promise.all(
    lines.map((line) => getProduct(line.product_id).catch(() => null))
  );
  // Products deleted since they were added are dropped from the cart
  return lines
    .map((line, i) => ({ product_id: line.product_id, quantity: line.quantity, product: products[i] }))
    .filter((line) => line.product !== null);
}

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
