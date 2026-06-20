import { getJson, type ApiOptions } from "./client";
import type { Product } from "../../types";

const defaultProductUrl = import.meta.env.VITE_PRODUCT_API_URL ?? "";

export type GridResponse<T> = {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
  columns: Array<{ key: string; label: string; kind?: string; sortable?: boolean; filterable?: boolean }>;
  actions: Array<{ key: string; label: string }>;
};

export async function listProducts(options: ApiOptions = {}): Promise<GridResponse<Product>> {
  return getJson<GridResponse<Product>>("/products", {
    baseUrl: options.baseUrl ?? defaultProductUrl,
    fetcher: options.fetcher,
  });
}
