import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { useCartStore } from "./store/cart";

describe("premium storefront", () => {
  beforeEach(() => {
    useCartStore.getState().clearCart();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  function mockCatalog() {
    const checkoutBodies: Array<Record<string, unknown>> = [];
    const initResponse = {
      resource: "products",
      links: { list: "/api/v1/products", create: "/api/v1/products", bulk_delete: "/api/v1/products" },
      actions: {},
      bulkActions: ["bulk_delete"],
    };
    const productResponse = {
      items: [
        {
          id: "aurora-speaker",
          name: "Aurora Speaker",
          category: "Audio",
          description: "Portable room speaker",
          price: 249,
          accent: "#0e5d4e",
          image: "https://example.test/speaker.jpg",
          rating: 4.8,
          stock: 8,
        },
      ],
      total: 1,
      page: 1,
      size: 20,
      pages: 1,
    };

    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request, init?: RequestInit) => {
        const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        const method = init?.method ?? "GET";
        if (url.includes("/api/v1/auth/login")) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                access_token: `header.${btoa(JSON.stringify({ sub: "buyer-1", email: "buyer@ecom.dev", roles: ["customer"] })).replaceAll("=", "")}.sig`,
                token_type: "bearer",
              }),
              { status: 200, headers: { "Content-Type": "application/json" } },
            ),
          );
        }
        if (url.includes("/api/v1/orders") && method === "POST") {
          const body = JSON.parse(String(init?.body ?? "{}"));
          checkoutBodies.push(body);
          expect(body.payment_method).toBe("cod");
          return Promise.resolve(
            new Response(
              JSON.stringify({ id: "order-1", user_id: "buyer-1", status: "pending", total: 249, lines: [] }),
              { status: 200, headers: { "Content-Type": "application/json" } },
            ),
          );
        }
        const body = url.includes("/api/v1/products/init")
          ? initResponse
          : url.includes("/api/v1/products")
            ? productResponse
            : [];

        return Promise.resolve(
          new Response(JSON.stringify(body), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );
    return { checkoutBodies };
  }

  it("renders catalog, orders, and support as separate shopper screens", async () => {
    mockCatalog();

    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: /gateway storefront/i,
      }),
    ).toBeInTheDocument();
    expect((await screen.findAllByText("Aurora Speaker")).length).toBeGreaterThan(0);
    expect(screen.queryByText(/order workflow/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/checkout is designed around/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: /^orders$/i }));

    expect(screen.getByRole("heading", { name: /orders/i })).toBeInTheDocument();
    expect(screen.getByText(/select an order to inspect/i)).toBeInTheDocument();
    expect(screen.queryByText(/inventory reservation/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: /^support$/i }));

    expect(screen.getByRole("heading", { name: /support/i })).toBeInTheDocument();
    expect(screen.getByText(/gateway-backed help/i)).toBeInTheDocument();
  });

  it("asks for gateway sign in at checkout and lets users back out of sheets", async () => {
    mockCatalog();

    render(<App />);

    expect(await screen.findByRole("heading", { name: /gateway storefront/i })).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: /add to cart/i })[0]);

    expect(screen.getByRole("dialog", { name: /shopping cart/i })).toBeInTheDocument();
    expect(screen.getByText(/subtotal/i)).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /cash on delivery/i })).toBeChecked();
    expect(screen.getByRole("radio", { name: /card/i })).toBeDisabled();
    expect(screen.getByRole("radio", { name: /upi/i })).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: /checkout cod/i }));

    expect(screen.getByRole("dialog", { name: /gateway sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/calls the gateway auth endpoints/i)).toBeInTheDocument();
    expect(screen.getByText(/sign in to continue checkout/i)).toBeInTheDocument();

    await userEvent.click(within(screen.getByRole("dialog", { name: /gateway sign in/i })).getByRole("button", { name: /back/i }));
    expect(screen.queryByRole("dialog", { name: /gateway sign in/i })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /continue shopping/i }));
    expect(screen.queryByRole("dialog", { name: /shopping cart/i })).not.toBeInTheDocument();
  });

  it("submits checkout after password sign in", async () => {
    const api = mockCatalog();

    render(<App />);

    expect(await screen.findByRole("heading", { name: /gateway storefront/i })).toBeInTheDocument();
    expect((await screen.findAllByText("Aurora Speaker")).length).toBeGreaterThan(0);
    await userEvent.click(screen.getAllByRole("button", { name: /add to cart/i })[0]);
    await userEvent.click(screen.getByRole("button", { name: /checkout cod/i }));
    await userEvent.type(screen.getByLabelText(/email/i), "buyer@ecom.dev");
    await userEvent.type(screen.getByLabelText(/password/i), "secret");
    await userEvent.click(within(screen.getByRole("dialog", { name: /gateway sign in/i })).getByRole("button", { name: /^sign in$/i }));
    await userEvent.click(screen.getByRole("button", { name: /checkout cod/i }));

    expect(api.checkoutBodies).toHaveLength(1);
    expect(api.checkoutBodies[0].payment_method).toBe("cod");
    expect(screen.getByRole("button", { name: /^cart0$/i })).toHaveTextContent("0");
  });
});
