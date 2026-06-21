import { deleteJson, getJson, patchJson, postJson, type ApiOptions } from "./client";
import type { Product } from "../../types";

const defaultApiUrl = import.meta.env.VITE_API_BASE_URL ?? "";

export type GridResponse<T> = {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
  columns: Array<{ key: string; label: string; kind?: string; sortable?: boolean; filterable?: boolean }>;
  actions: Array<{ key: string; label: string }>;
};

export type ResourceInit = {
  resource: string;
  title?: string;
  columns?: GridResponse<Product>["columns"];
  filters?: Array<{ key: string; label: string }>;
  links: Record<string, string>;
  actions: Record<string, string>;
  bulkActions: string[];
};

export type ProductPayload = Product & {
  stock?: number;
};

export type BulkDeleteResult = {
  deleted: string[];
  missing: string[];
};

export async function initProducts(options: ApiOptions = {}): Promise<ResourceInit> {
  return getJson<ResourceInit>("/api/v1/products/init", {
    baseUrl: options.baseUrl ?? defaultApiUrl,
    fetcher: options.fetcher,
    token: options.token,
  });
}

export async function listProducts({
  path = "/api/v1/products",
  ...options
}: ApiOptions & { path?: string } = {}): Promise<GridResponse<Product>> {
  return getJson<GridResponse<Product>>(path, {
    baseUrl: options.baseUrl ?? defaultApiUrl,
    fetcher: options.fetcher,
    token: options.token,
  });
}

export async function createProducts({
  payload,
  path = "/api/v1/products",
  options = {},
}: {
  payload: ProductPayload | ProductPayload[];
  path?: string;
  options?: ApiOptions;
}): Promise<{ items: Product[]; total: number }> {
  return postJson<{ items: Product[]; total: number }, ProductPayload | ProductPayload[]>(path, payload, {
    baseUrl: options.baseUrl ?? defaultApiUrl,
    fetcher: options.fetcher,
    token: options.token,
  });
}

export async function updateProduct({
  id,
  payload,
  path = "/api/v1/products/{id}",
  options = {},
}: {
  id: string;
  payload: Partial<ProductPayload>;
  path?: string;
  options?: ApiOptions;
}): Promise<Product> {
  return patchJson<Product, Partial<ProductPayload>>(path.replace("{id}", id), payload, {
    baseUrl: options.baseUrl ?? defaultApiUrl,
    fetcher: options.fetcher,
    token: options.token,
  });
}

export async function bulkDeleteProducts({
  ids,
  path = "/api/v1/products",
  options = {},
}: {
  ids: string[];
  path?: string;
  options?: ApiOptions;
}): Promise<BulkDeleteResult> {
  return deleteJson<BulkDeleteResult, { ids: string[] }>(path, { ids }, {
    baseUrl: options.baseUrl ?? defaultApiUrl,
    fetcher: options.fetcher,
    token: options.token,
  });
}
