import axiosClient from "./axiosClient";

export interface CartProduct {
  product_id: number;
  title: string;
  description?: string;
  price: number;
  size?: string;
  color?: string;
  thumbnail?: string;
  images?: string[];
  stock_quantity: number;
  is_active: boolean;
}

// One product in the cart. cart_item_id is the server row, which a guest's browser cart doesn't have
export interface CartLine {
  cart_item_id?: number;
  product_id: number;
  quantity: number;
  product: CartProduct | null;
}

// What a guest's browser cart keeps, and what guest checkout and the login merge send
export interface StoredCartLine {
  product_id: number;
  quantity: number;
}

interface ServerCart {
  items: { cart_item_id: number; product_id: number; quantity: number; product: CartProduct | null }[];
}

export async function getCart(): Promise<CartLine[]> {
  const res = await axiosClient.get<ServerCart>("/cart/");
  return res.data.items;
}

export async function addCartItem(productId: number) {
  await axiosClient.post("/cart/items", null, { params: { product_id: productId } });
}

export async function updateCartItem(cartItemId: number, quantity: number) {
  await axiosClient.put(`/cart/items/${cartItemId}`, { quantity });
}

export async function removeCartItem(cartItemId: number) {
  await axiosClient.delete(`/cart/items/${cartItemId}`);
}

// Adds a guest's browser cart to the account cart after login
export async function mergeCart(items: StoredCartLine[]): Promise<CartLine[]> {
  const res = await axiosClient.post<ServerCart>("/cart/merge", { items });
  return res.data.items;
}

export async function getProduct(productId: number): Promise<CartProduct> {
  const res = await axiosClient.get<CartProduct>(`/products/${productId}`);
  return res.data;
}
