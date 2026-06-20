import { beforeEach, describe, expect, it } from "vitest";

import { useCartStore } from "./cart";
import { products } from "../data/catalog";

describe("cart store", () => {
  beforeEach(() => {
    useCartStore.getState().clearCart();
  });

  it("adds products and increases quantity for repeated items", () => {
    const product = products[0];

    useCartStore.getState().addItem(product);
    useCartStore.getState().addItem(product);

    expect(useCartStore.getState().items).toEqual([
      { product, quantity: 2 },
    ]);
    expect(useCartStore.getState().itemCount()).toBe(2);
  });

  it("updates totals when item quantities change", () => {
    const product = products[1];

    useCartStore.getState().addItem(product);
    useCartStore.getState().setQuantity(product.id, 3);

    expect(useCartStore.getState().subtotal()).toBe(product.price * 3);
  });

  it("removes an item when quantity is set to zero", () => {
    const product = products[2];

    useCartStore.getState().addItem(product);
    useCartStore.getState().setQuantity(product.id, 0);

    expect(useCartStore.getState().items).toEqual([]);
  });
});
