import { create } from "zustand";

import type { CartItem, Product } from "../types";

type CartState = {
  items: CartItem[];
  isOpen: boolean;
  addItem: (product: Product) => void;
  removeItem: (productId: string) => void;
  setQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  openCart: () => void;
  closeCart: () => void;
  itemCount: () => number;
  subtotal: () => number;
};

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  isOpen: false,
  addItem: (product) => {
    const items = get().items;
    const existing = items.find((item) => item.product.id === product.id);

    if (existing) {
      set({
        items: items.map((item) =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        ),
        isOpen: true,
      });
      return;
    }

    set({ items: [...items, { product, quantity: 1 }], isOpen: true });
  },
  removeItem: (productId) => {
    set({ items: get().items.filter((item) => item.product.id !== productId) });
  },
  setQuantity: (productId, quantity) => {
    if (quantity <= 0) {
      get().removeItem(productId);
      return;
    }

    set({
      items: get().items.map((item) =>
        item.product.id === productId ? { ...item, quantity } : item,
      ),
    });
  },
  clearCart: () => set({ items: [], isOpen: false }),
  openCart: () => set({ isOpen: true }),
  closeCart: () => set({ isOpen: false }),
  itemCount: () => get().items.reduce((sum, item) => sum + item.quantity, 0),
  subtotal: () =>
    get().items.reduce(
      (sum, item) => sum + item.product.price * item.quantity,
      0,
    ),
}));
