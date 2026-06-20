import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import App from "./App";
import { useCartStore } from "./store/cart";

describe("premium storefront", () => {
  beforeEach(() => {
    useCartStore.getState().clearCart();
  });

  it("renders the customer storefront and opens the cart after quick add", async () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: /curated essentials, delivered fast/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /shop new arrivals/i })).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: /add to cart/i })[0]);

    expect(screen.getByRole("dialog", { name: /shopping cart/i })).toBeInTheDocument();
    expect(screen.getByText(/subtotal/i)).toBeInTheDocument();
  });
});
