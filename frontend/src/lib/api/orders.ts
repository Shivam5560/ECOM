import { getJson, postJson, type ApiOptions } from "./client";
import type { CartItem } from "../../types";
import type { GridResponse } from "./products";

const defaultOrderUrl = import.meta.env.VITE_ORDER_API_URL ?? "";

export type Order = {
  id: string;
  user_id: string;
  status: string;
  total: number;
  lines: Array<{ product_id: string; quantity: number; unit_price: number }>;
  created_at?: string;
};

export async function createOrder(
  { userId, items, options = {} }: {
  userId: string;
  items: CartItem[];
  options?: ApiOptions;
}): Promise<Order> {
  return postJson<Order, { user_id: string; lines: Order["lines"]; correlation_id: string }>(
    "/orders",
    {
      user_id: userId,
      lines: items.map((item) => ({
        product_id: item.product.id,
        quantity: item.quantity,
        unit_price: item.product.price,
      })),
      correlation_id: `ui-${Date.now()}`,
    },
    { baseUrl: options.baseUrl ?? defaultOrderUrl, fetcher: options.fetcher },
  );
}

export async function listOrders(options: ApiOptions = {}): Promise<GridResponse<Order>> {
  return getJson<GridResponse<Order>>("/orders", {
    baseUrl: options.baseUrl ?? defaultOrderUrl,
    fetcher: options.fetcher,
  });
}
