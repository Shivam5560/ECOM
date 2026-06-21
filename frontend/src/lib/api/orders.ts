import { getJson, postJson, type ApiOptions } from "./client";
import type { CartItem } from "../../types";
import type { GridResponse } from "./products";

const defaultApiUrl = import.meta.env.VITE_API_BASE_URL ?? "";

export type Order = {
  id: string;
  user_id: string;
  status: string;
  total: number;
  lines: Array<{ product_id: string; quantity: number; unit_price: number }>;
  created_at?: string;
};

export async function createOrder(
  { items, paymentMethod, options = {} }: {
  items: CartItem[];
  paymentMethod: "cod";
  options?: ApiOptions;
}): Promise<Order> {
  return postJson<
    Order,
    { lines: Array<{ product_id: string; quantity: number }>; correlation_id: string; payment_method: "cod" }
  >(
    "/api/v1/orders",
    {
      lines: items.map((item) => ({
        product_id: item.product.id,
        quantity: item.quantity,
      })),
      correlation_id: `ui-${Date.now()}`,
      payment_method: paymentMethod,
    },
    { baseUrl: options.baseUrl ?? defaultApiUrl, fetcher: options.fetcher, token: options.token },
  );
}

export async function listOrders(options: ApiOptions = {}): Promise<GridResponse<Order>> {
  return getJson<GridResponse<Order>>("/api/v1/orders", {
    baseUrl: options.baseUrl ?? defaultApiUrl,
    fetcher: options.fetcher,
    token: options.token,
  });
}
