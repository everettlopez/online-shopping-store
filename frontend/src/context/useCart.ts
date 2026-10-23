// The cart context and its hook, kept apart from CartProvider so that file exports
// only a component (which React Fast Refresh needs)
import { createContext, useContext } from "react";
import type { CartLine, CartProduct, StoredCartLine } from "../api/cart";

export interface CartContextType {
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

export const CartContext = createContext<CartContextType | undefined>(undefined);

export const useCart = () => {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be inside CartProvider");
  return ctx;
};
